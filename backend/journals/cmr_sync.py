"""CRM → journal entries. Shared by the CMR Sync page (views.cmr_sync, the audit)
and `manage.py sync_cmr`, which used to carry two copies of this logic.

What the CRM sends (crm/api integrations): invoices marked "sent to finance",
and every supplier-payment row of the trips updated in the window, with
`amount` (the planned cost), `paid` (what has actually been paid so far),
`paid_date`, `sent_to_finance` and `entry_index`.

Rules:
- A MAD invoice is booked once when it is sent to finance (DR 3421 clients /
  CR 71243 revenue, gross TTC as the PCGM margin regime requires).
- An invoice in another currency (EUR, …) is NOT booked here: it is worth the
  MAD that actually arrived, so it is booked when its receipt is matched in Bank
  reconciliation (journals/receipts.py).
- Money in is never booked from the CRM's "paid" flag — the bank statement
  holds it, and booking both counted it twice. Old payment entries made that
  way are reported.
- A supplier payment that has been paid AND handed to finance
  (`sent_to_finance`) is booked as a purchase in AC: DR 61263x cost / CR 4411
  with the supplier as tiers. The amount is `paid`, not the planned `amount`.
  The bank line of the payment settles the 4411 (it is not booked to the bank
  here, so the bank statement stays the only source of bank movements). Payments are summed per trip, category and supplier and
  only the difference to what is already booked is posted. That makes a re-run
  idempotent, a second partial payment books just the increase, and rows can be
  reordered or added without touching other suppliers. The older entries, keyed
  by row position ("<trip>:<category>:<n>"), count as booked for their supplier
  so nothing is posted twice.
- When the CRM shows less than is booked, or an invoice total changed after it
  was booked, nothing is reversed automatically: the run reports it.

`plan()` works out what should happen without writing; `run_sync()` books it;
the audit shows the plan plus the problems with what is already booked.
"""

import hashlib
import re
from collections import OrderedDict
from datetime import date
from decimal import Decimal, InvalidOperation

from django.db import transaction
from django.db.models import Sum

from accounts import chart
from accounts.models import Account, SupplierAccountMapping

from .models import InvoiceReceipt, JournalEntry, JournalEntryLine
from .numbering import next_je_number
from .periods import closed_period_error


# CRM payment category (lower case) → cost account, when the supplier has no mapping.
CATEGORY_ACCOUNT_MAP = {
    "accommodation": chart.COST_HOTELS,
    "hotel": chart.COST_HOTELS,
    "restaurant": chart.COST_RESTAURANTS,
    "transport": chart.COST_TRANSPORT,
    "transportation": chart.COST_TRANSPORT,
    "guide": chart.COST_GUIDES,
    "entry": chart.COST_ACTIVITIES,
    "entries": chart.COST_ACTIVITIES,
    "entrees": chart.COST_ACTIVITIES,
    "package": chart.COST_OTHER,
    "packages": chart.COST_OTHER,
}
FALLBACK_ACCOUNT_CODE = chart.COST_OTHER
ACCOUNTS_RECEIVABLE_CODE = chart.RECEIVABLE
REVENUE_CODE = chart.REVENUE

CENT = Decimal("0.01")


def _dec(value):
    try:
        return Decimal(str(value if value not in (None, "") else 0)).quantize(CENT)
    except (InvalidOperation, ValueError):
        return None


def parse_paid_date(value):
    """ISO date, ISO timestamp, or the CRM Payments tab's "DD/MM/YYYY HH:MM"."""
    s = str(value or "").strip()
    if not s:
        return None
    m = re.match(r"^(\d{4})-(\d{2})-(\d{2})", s)
    if m:
        try:
            return date(int(m[1]), int(m[2]), int(m[3]))
        except ValueError:
            return None
    m = re.match(r"^(\d{1,2})/(\d{1,2})/(\d{4})", s)
    if m:
        try:
            return date(int(m[3]), int(m[2]), int(m[1]))
        except ValueError:
            return None
    return None


def _supplier_key(name):
    norm = re.sub(r"\s+", " ", (name or "").strip().lower())
    return "s" + hashlib.sha1(norm.encode("utf-8")).hexdigest()[:8]


def _legacy_pattern(opp_id, category):
    return re.compile(r"^%s:%s:\d+$" % (re.escape(opp_id), re.escape(category)))


def _booked_for(opp_id, category, supplier_name):
    """What is already booked for one trip/category/supplier: (amount, entries)."""
    key_prefix = f"{opp_id}:{category}:{_supplier_key(supplier_name)}:"
    new_style = list(JournalEntry.objects.filter(source="cmr_payment", source_id__startswith=key_prefix))
    legacy_re = _legacy_pattern(opp_id, category)
    needle = (supplier_name or "").strip().lower()
    legacy = [
        e for e in JournalEntry.objects.filter(source="cmr_payment", source_id__startswith=f"{opp_id}:{category}:")
        if legacy_re.match(e.source_id) and needle and f"— {needle} —" in f"{e.description.lower()} —"
    ]
    entries = new_style + legacy
    total = JournalEntryLine.objects.filter(journal_entry__in=entries).aggregate(s=Sum("debit"))["s"] or Decimal("0")
    return total.quantize(CENT), entries, len(new_style)


def _group_payments(payments):
    """Sum paid-and-handed-to-finance rows per (trip, category, supplier)."""
    groups = OrderedDict()
    for p in payments:
        opp_id = p.get("opportunity_id") or ""
        category = (p.get("category") or "").strip()
        supplier = (p.get("supplier_name") or "").strip()
        if not opp_id or not category or not supplier:
            continue
        key = (opp_id, category, supplier.lower())
        g = groups.setdefault(key, {
            "opportunity_id": opp_id, "category": category, "supplier_name": supplier,
            "supplier_id": None, "opportunity_title": p.get("opportunity_title") or "",
            "trip_reference": p.get("trip_reference") or "",
            "paid": Decimal("0"), "planned": Decimal("0"), "paid_unsent": Decimal("0"),
            "paid_date": None, "bad_amount": False,
        })
        g["supplier_id"] = g["supplier_id"] or p.get("supplier_id")
        paid = _dec(p.get("paid"))
        planned = _dec(p.get("amount"))
        if paid is None or planned is None:
            g["bad_amount"] = True
            continue
        g["planned"] += planned
        if paid <= 0:
            continue
        if not p.get("sent_to_finance"):
            g["paid_unsent"] += paid
            continue
        g["paid"] += paid
        d = parse_paid_date(p.get("paid_date"))
        if d and (g["paid_date"] is None or d > g["paid_date"]):
            g["paid_date"] = d
    return list(groups.values())


def plan(invoices, payments):
    """What a sync would book, and what is off with what is already booked."""
    actions, notes = [], []

    for inv in invoices:
        inv_id = inv.get("id") or ""
        num = inv.get("invoice_number") or inv_id[:8]
        total = _dec(inv.get("total"))
        if total is None or total <= 0:
            notes.append({"kind": "invoice_skipped", "invoice": num, "message": "No total"})
            continue
        foreign = (inv.get("currency") or "MAD").strip().upper() not in ("MAD", "DH", "DHS", "")
        existing = JournalEntry.objects.filter(source="cmr_invoice", source_id=inv_id).first()
        receipts = InvoiceReceipt.objects.filter(cmr_invoice_id=inv_id)
        if foreign:
            # Worth the MAD that arrives: booked when the receipt is matched in bank
            # reconciliation (journals/receipts.py), never at face value here.
            if existing:
                notes.append({
                    "kind": "invoice_foreign_booked", "invoice": num, "entry": existing.entry_number,
                    "message": (f"Invoice {num} ({inv.get('currency')}) was booked at face value in "
                                f"{existing.entry_number} — reverse it; it is now booked from the MAD received"),
                })
            elif not receipts.exists():
                notes.append({
                    "kind": "invoice_on_receipt", "invoice": num, "currency": inv.get("currency"),
                    "message": (f"Invoice {num}: {total} {inv.get('currency')} — booked when the money is "
                                "matched in Bank reconciliation"),
                })
            continue
        if existing:
            booked = existing.lines.aggregate(s=Sum("debit"))["s"] or Decimal("0")
            if booked.quantize(CENT) != total:
                notes.append({
                    "kind": "invoice_total_changed", "invoice": num, "entry": existing.entry_number,
                    "booked": str(booked), "crm": str(total),
                    "message": f"Invoice {num} is booked at {booked} but the CRM now says {total}",
                })
        else:
            actions.append({"type": "invoice", "inv": inv, "total": total})
        # Money in is booked from the bank statement and matched to the invoice
        # there; a payment entry from the CRM's "paid" flag counted it twice.
        old_payment = JournalEntry.objects.filter(source="cmr_invoice", source_id=f"{inv_id}:payment").first()
        if old_payment:
            notes.append({
                "kind": "invoice_payment_from_crm", "invoice": num, "entry": old_payment.entry_number,
                "message": (f"{old_payment.entry_number} books invoice {num}'s payment from the CRM — if the bank "
                            "statement holds the same receipt it is counted twice"),
            })
        elif inv.get("status") == "paid" and not receipts.exists():
            notes.append({
                "kind": "invoice_paid_unmatched", "invoice": num,
                "message": f"Invoice {num} is paid in the CRM — match its receipt in Bank reconciliation",
            })

    for g in _group_payments(payments):
        label = f"{g['supplier_name']} ({g['category']}, {g['trip_reference'] or g['opportunity_title']})"
        if g["bad_amount"]:
            notes.append({"kind": "payment_bad_amount", "supplier": label, "message": f"{label}: an amount is not a number"})
        booked, entries, new_count = _booked_for(g["opportunity_id"], g["category"], g["supplier_name"])
        diff = g["paid"] - booked
        if diff > 0:
            actions.append({"type": "supplier_payment", "group": g, "amount": diff, "seq": new_count + 1,
                            "booked_before": booked})
        elif diff < 0:
            notes.append({
                "kind": "payment_overbooked", "supplier": label,
                "entries": [e.entry_number for e in entries], "booked": str(booked), "crm_paid": str(g["paid"]),
                "message": (f"{label}: {booked} is booked but the CRM shows {g['paid']} paid and sent to "
                            f"finance — {', '.join(e.entry_number for e in entries)} should be checked"),
            })
        if g["paid_unsent"] > 0:
            notes.append({
                "kind": "payment_not_sent", "supplier": label, "amount": str(g["paid_unsent"]),
                "message": f"{label}: {g['paid_unsent']} is paid in the CRM but not sent to finance yet",
            })
    return actions, notes


def run_sync(invoices, payments, created_by, dry_run=False):
    """Book the plan. Returns counts, a line per action and the notes."""
    actions, notes = plan(invoices, payments)
    accounts = {a.code: a for a in Account.objects.filter(is_active=True)}
    mappings = {m.cmr_supplier_id: m.account for m in SupplierAccountMapping.objects.select_related("account")}
    ar, cf = accounts.get(ACCOUNTS_RECEIVABLE_CODE), accounts.get(REVENUE_CODE)
    result = {"invoices_created": 0, "payments_created": 0, "skipped": 0, "details": [], "notes": notes}
    details = result["details"]

    def entry(date_, description, reference, source, source_id, lines):
        if dry_run:
            return
        je = JournalEntry.objects.create(
            entry_number=next_je_number(), date=date_, description=description, reference=reference,
            piece_number=reference, source=source, source_id=source_id, is_posted=True, created_by=created_by,
        )
        for acct, debit, credit, desc, *partner in lines:
            JournalEntryLine.objects.create(journal_entry=je, account=acct, debit=debit, credit=credit,
                                            description=desc or description, **(partner[0] if partner else {}))

    with transaction.atomic():
        for a in actions:
            if a["type"] == "invoice":
                inv, total = a["inv"], a["total"]
                num = inv.get("invoice_number", "")
                if not ar or not cf:
                    result["skipped"] += 1
                    details.append(f"SKIP invoice {num} — accounts {ACCOUNTS_RECEIVABLE_CODE}/{REVENUE_CODE} missing")
                    continue
                d = inv.get("invoice_date") or (inv.get("updated_at") or "")[:10]
                err = closed_period_error(d)
                if err:
                    result["skipped"] += 1
                    details.append(f"SKIP invoice {num} — {err}")
                    continue
                desc = f"CMR Invoice {num} — {inv.get('customer_name', '')} — {inv.get('opportunity_title', '')}"
                cats = OrderedDict()
                for li in inv.get("line_items") or []:
                    cat, amt = (li.get("category") or "").strip(), _dec(li.get("amount"))
                    if cat and amt and amt > 0:
                        cats[cat] = cats.get(cat, Decimal("0")) + amt
                lines = [(ar, total, Decimal("0"), desc, _customer_tiers(inv))]
                if cats and sum(cats.values()) <= total:
                    items = list(cats.items())
                    running = Decimal("0")
                    for i, (cat, amt) in enumerate(items):
                        if i == len(items) - 1:
                            amt = total - running  # the last line takes the rounding
                        running += amt
                        lines.append((cf, Decimal("0"), amt, f"CMR Invoice {num} — {cat}"))
                else:
                    lines.append((cf, Decimal("0"), total, desc))
                entry(d, desc, f"CMR:{num}", "cmr_invoice", inv.get("id"), lines)
                result["invoices_created"] += 1
                details.append(f"Invoice {num}: {total}")
                continue

            g, amount = a["group"], a["amount"]
            label = f"{g['supplier_name']} ({g['category']})"
            pay_date = g["paid_date"]
            if pay_date is None:
                pay_date = date.today()
                details.append(f"NOTE {label}: no payment date in the CRM, booked on {pay_date.isoformat()}")
            err = closed_period_error(pay_date)
            if err:
                result["skipped"] += 1
                details.append(f"SKIP {label} — {err}")
                continue
            expense = (mappings.get(g["supplier_id"]) if g["supplier_id"] else None) \
                or accounts.get(CATEGORY_ACCOUNT_MAP.get(g["category"].lower(), FALLBACK_ACCOUNT_CODE)) \
                or accounts.get(FALLBACK_ACCOUNT_CODE)
            payable = accounts.get(chart.PAYABLE)
            if not expense or not payable:
                result["skipped"] += 1
                details.append(f"SKIP {label} — cost account or {chart.PAYABLE} missing")
                continue
            desc = (f"Supplier payment — {g['supplier_name']} — "
                    f"Opp: {g['trip_reference'] or g['opportunity_title']}")
            source_id = f"{g['opportunity_id']}:{g['category']}:{_supplier_key(g['supplier_name'])}:{a['seq']}"
            entry(pay_date, desc, f"CMR:{g['trip_reference'] or g['opportunity_id']}:{g['category']}",
                  "cmr_payment", source_id[:100],
                  [(expense, amount, Decimal("0"), desc),
                   (payable, Decimal("0"), amount, desc, _supplier_tiers(g))])
            result["payments_created"] += 1
            extra = f" (paid {g['paid']}, {a['booked_before']} already booked)" if a["booked_before"] else ""
            details.append(f"Supplier payment {label}: {amount}{extra}")

        if dry_run:
            transaction.set_rollback(True)

    for n in notes:
        details.append(f"CHECK {n['message']}")
    return result


def _customer_tiers(inv):
    from sales.models import Customer
    c = Customer.objects.filter(cmr_id=inv.get("customer_id") or "-").first() if inv.get("customer_id") else None
    if c:
        return {"partner_type": "customer", "partner_id": str(c.id), "partner_name": c.name}
    return {"partner_type": "customer", "partner_name": (inv.get("customer_name") or "")[:255]}


def _supplier_tiers(g):
    from purchases.models import Supplier
    s = Supplier.objects.filter(cmr_id=g["supplier_id"]).first() if g.get("supplier_id") else None
    if s:
        return {"partner_type": "supplier", "partner_id": str(s.id), "partner_name": s.name}
    return {"partner_type": "supplier", "partner_name": (g.get("supplier_name") or "")[:255]}


def audit(invoices, payments):
    """Read-only: what the next full sync would book, and what to check."""
    actions, notes = plan(invoices, payments)
    pending = []
    for a in actions:
        if a["type"] == "supplier_payment":
            g = a["group"]
            pending.append({
                "kind": "supplier_payment", "supplier": g["supplier_name"], "category": g["category"],
                "trip": g["trip_reference"] or g["opportunity_title"], "amount": str(a["amount"]),
                "date": g["paid_date"].isoformat() if g["paid_date"] else None,
            })
        else:
            inv = a["inv"]
            pending.append({
                "kind": a["type"], "invoice": inv.get("invoice_number"), "amount": str(a["total"]),
                "date": inv.get("invoice_date"),
                "trip": inv.get("trip_reference") or inv.get("opportunity_title"),
            })
    # Old position-keyed entries that no current CRM supplier row accounts for
    # (supplier renamed or removed, or the trip deleted) — booked money with no
    # payment behind it in the CRM.
    matched = set()
    for g in _group_payments(payments):
        _, entries, _ = _booked_for(g["opportunity_id"], g["category"], g["supplier_name"])
        matched.update(e.pk for e in entries)
    legacy_re = re.compile(r"^[0-9a-f-]{36}:.+:\d+$")
    for e in JournalEntry.objects.filter(source="cmr_payment").order_by("date"):
        if e.pk in matched or not legacy_re.match(e.source_id):
            continue
        amount = e.lines.aggregate(s=Sum("debit"))["s"] or Decimal("0")
        notes.append({
            "kind": "payment_unmatched", "entries": [e.entry_number], "booked": str(amount),
            "message": f"{e.entry_number} ({e.date}, {amount}) — {e.description}: no matching supplier row in the CRM",
        })
    return {"pending": pending, "issues": notes}
