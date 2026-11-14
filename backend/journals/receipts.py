"""Incoming bank money matched to CRM invoices — the invoice is worth the MAD
that actually arrived.

Clients pay in two ways, and both are matched here:

1. Exchanged at once (all of it, or the 30 % the bank exchanges) into a MAD
   account (CIH300, BP09). The line's 34971 suspense leg becomes CR 71243
   revenue for the MAD received — the invoice (or that part of it) is
   booked right there, at what came in. For an EUR invoice the rate is simply
   MAD received ÷ euros covered.
2. Kept in euros on the EUR account (51413, the other 70 %). Those euros have
   no MAD value until they are exchanged, so the match only records them
   ("awaiting exchange"): the suspense leg moves to 34972 "Devises reçues non
   encore changées" and nothing reaches revenue. If they are exchanged later, the
   MAD that arrives is matched to the waiting part (`exchanged_from`) and that
   part is booked then, like way 1.

A MAD invoice is booked when it is issued (DR 3421 / CR 71243); its receipt
turns the suspense leg into CR 3421 and clears the receivable.
"""

import re
from decimal import Decimal, InvalidOperation

from django.db import transaction
from django.db.models import Sum
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response

from accounts import chart
from accounts.models import Account
from core.audit import log_action
from core.permissions import RoleWriteAccess

from .lettrage import auto_lettrer, undo_lettrage_of
from .models import InvoiceReceipt, JournalEntry, JournalEntryLine
from .periods import closed_period_error

CENT = Decimal("0.01")
MAD_CODES = {"MAD", "DH", "DHS", ""}
EUR_BANK_CODES = {chart.BANK_CIH600_EUR}
SUSPENSE_CODE = chart.SUSPENSE
EUR_HELD_CODE = chart.EUR_UNEXCHANGED
AR_CODE = chart.RECEIVABLE
REVENUE_CODE = chart.REVENUE


def is_mad(currency):
    return (currency or "").strip().upper() in MAD_CODES


def is_eur_line(jel):
    return jel.account.code in EUR_BANK_CODES


def _dec(v):
    try:
        return Decimal(str(v if v not in (None, "") else 0)).quantize(CENT)
    except (InvalidOperation, ValueError):
        return None


def line_unallocated(jel):
    """What of an incoming bank line is not matched yet — MAD on a MAD account,
    euros on the EUR account."""
    field = "covered_amount" if is_eur_line(jel) else "amount_mad"
    matched = jel.invoice_receipts.aggregate(s=Sum(field))["s"] or Decimal("0")
    return (jel.debit or Decimal("0")) - matched


def covered_so_far(cmr_invoice_id):
    """How much of the invoice (its own currency) has been paid, exchanged or not.
    An exchange only turns waiting euros into MAD, so it is not counted again."""
    return InvoiceReceipt.objects.filter(cmr_invoice_id=cmr_invoice_id, exchanged_from__isnull=True).aggregate(
        s=Sum("covered_amount"))["s"] or Decimal("0")


def waiting_euros(receipt):
    """Euros of a waiting receipt that have not been exchanged yet."""
    done = receipt.exchanges.aggregate(s=Sum("covered_amount"))["s"] or Decimal("0")
    return receipt.covered_amount - done


def validate_line(jel):
    """Why this line cannot take an invoice receipt, or None."""
    from purchases.models import BankTransactionCategorization

    if jel.journal_entry.source != "bank" or not (jel.account and chart.is_treasury(jel.account.code)):
        return "Not a bank transaction line"
    if not (jel.debit and jel.debit > 0):
        return "Only money coming in can be matched to an invoice"
    if BankTransactionCategorization.objects.filter(journal_entry_line=jel).exists():
        return "This transaction is already categorised"
    return None


def _take_from_suspense(jel, amount):
    """Reduce the bank entry's 34971 leg by `amount`; error text or None."""
    susp = jel.journal_entry.lines.filter(account__code=SUSPENSE_CODE, credit__gt=0).first()
    if not susp or susp.credit + CENT < amount:
        return "This transaction has no unclassified amount left to match"
    susp.credit = susp.credit - amount
    if susp.credit <= 0 and (susp.debit or 0) <= 0:
        susp.delete()
    else:
        susp.save()
    return None


def _receipt(jel, inv_like, covered, amount_mad, matched_by, exchanged_from=None):
    return InvoiceReceipt.objects.create(
        journal_entry_line=jel, cmr_invoice_id=inv_like["id"], invoice_number=inv_like["number"],
        customer_name=(inv_like.get("customer_name") or "")[:255],
        trip_reference=(inv_like.get("trip_reference") or "")[:50],
        currency=(inv_like.get("currency") or "MAD")[:3], invoice_total=inv_like["total"],
        covered_amount=covered, amount_mad=amount_mad, matched_by=matched_by, exchanged_from=exchanged_from,
    )


def apply_receipt(jel, inv, covered, amount_mad, matched_by):
    """Match the bank line to the CRM invoice `inv`. Caller holds transaction.atomic().

    On a MAD account `amount_mad` of the line is booked (CR 71243, or CR 3421
    for a MAD invoice). On the EUR account `covered` euros are recorded as waiting
    for exchange (CR 34972) and nothing is valued. Returns (receipt, error)."""
    if covered is None or covered <= 0:
        return None, "The invoice amount covered must be positive"
    err = closed_period_error(jel.journal_entry.date)
    if err:
        return None, err
    total = _dec(inv.get("total")) or Decimal("0")
    left = total - covered_so_far(inv["id"])
    if covered > left + CENT:
        return None, f"Only {left} {inv.get('currency') or 'MAD'} of invoice {inv.get('invoice_number')} is still open"
    num = inv.get("invoice_number") or inv["id"][:8]
    inv_like = {**inv, "number": num, "total": total}
    unallocated = line_unallocated(jel)

    if is_eur_line(jel):
        if is_mad(inv.get("currency")):
            return None, "Euros on the EUR account can only pay an invoice in euros"
        if covered > unallocated + CENT:
            return None, f"Only {unallocated} EUR of this transaction is not matched yet"
        held = Account.objects.filter(code=EUR_HELD_CODE).first()
        if not held:
            return None, f"Account {EUR_HELD_CODE} (EUR i bank – ikke vekslet) not found"
        terr = _take_from_suspense(jel, covered)
        if terr:
            return None, terr
        JournalEntryLine.objects.create(
            journal_entry=jel.journal_entry, account=held, debit=Decimal("0"), credit=covered,
            currency=jel.currency,
            description=f"Invoice {num} — {inv.get('customer_name') or ''} — {covered} EUR held, not exchanged"[:500],
        )
        return _receipt(jel, inv_like, covered, None, matched_by), None

    if amount_mad is None or amount_mad <= 0:
        return None, "The MAD amount must be positive"
    if amount_mad > unallocated + CENT:
        return None, f"Only {unallocated} MAD of this transaction is not matched yet"
    mad_invoice = is_mad(inv.get("currency"))
    if mad_invoice:
        if not JournalEntry.objects.filter(source="cmr_invoice", source_id=inv["id"]).exists():
            return None, (f"Invoice {num} is not booked yet — run CMR Sync first, "
                          "so the receipt has a receivable to clear")
        if abs(covered - amount_mad) > CENT:
            return None, "For a MAD invoice the amount covered is the MAD received"
        target_code = AR_CODE
        desc = f"Payment received — Invoice {num} — {inv.get('customer_name') or ''}".strip(" —")
    else:
        target_code = REVENUE_CODE
        rate = (amount_mad / covered).quantize(Decimal("0.0001"))
        desc = (f"Invoice {num} — {inv.get('customer_name') or ''} — {covered} {inv.get('currency')} "
                f"received as {amount_mad} MAD (rate {rate})")
    target = Account.objects.filter(code=target_code).first()
    if not target:
        return None, f"Account {target_code} not found"
    terr = _take_from_suspense(jel, amount_mad)
    if terr:
        return None, terr
    tiers = {}
    if mad_invoice:
        ar_line = _invoice_ar_lines(inv["id"]).first()
        if ar_line:
            tiers = {"partner_type": ar_line.partner_type, "partner_id": ar_line.partner_id,
                     "partner_name": ar_line.partner_name}
    JournalEntryLine.objects.create(
        journal_entry=jel.journal_entry, account=target, debit=Decimal("0"), credit=amount_mad,
        currency="MAD", description=desc[:500], **tiers,
    )
    receipt = _receipt(jel, inv_like, covered, amount_mad, matched_by)
    if mad_invoice:
        auto_lettrer(_settling_lines(inv["id"], num))
    return receipt, None


def _invoice_ar_lines(cmr_invoice_id):
    return JournalEntryLine.objects.filter(
        journal_entry__source="cmr_invoice", journal_entry__source_id=cmr_invoice_id, account__code=AR_CODE,
    ).select_related("journal_entry")


def _settling_lines(cmr_invoice_id, number):
    """The invoice's 3421 line and the 3421 legs of the money received for it."""
    lines = list(_invoice_ar_lines(cmr_invoice_id))
    for r in InvoiceReceipt.objects.filter(cmr_invoice_id=cmr_invoice_id).select_related("journal_entry_line"):
        lines += list(r.journal_entry_line.journal_entry.lines.filter(
            account__code=AR_CODE, description__contains=f"Invoice {number}").select_related("journal_entry"))
    return list({l.id: l for l in lines}.values())


def apply_exchange(jel, waiting, euros, amount_mad, matched_by):
    """MAD that came in from exchanging waiting euros: book that part of the
    invoice at the MAD received. Caller holds transaction.atomic()."""
    if is_eur_line(jel):
        return None, "An exchange arrives on a MAD account"
    if euros is None or euros <= 0 or amount_mad is None or amount_mad <= 0:
        return None, "Euros exchanged and MAD received must be positive"
    err = closed_period_error(jel.journal_entry.date)
    if err:
        return None, err
    still = waiting_euros(waiting)
    if euros > still + CENT:
        return None, f"Only {still} EUR of invoice {waiting.invoice_number} is waiting for exchange"
    unallocated = line_unallocated(jel)
    if amount_mad > unallocated + CENT:
        return None, f"Only {unallocated} MAD of this transaction is not matched yet"
    target = Account.objects.filter(code=REVENUE_CODE).first()
    if not target:
        return None, f"Account {REVENUE_CODE} not found"
    terr = _take_from_suspense(jel, amount_mad)
    if terr:
        return None, terr
    rate = (amount_mad / euros).quantize(Decimal("0.0001"))
    JournalEntryLine.objects.create(
        journal_entry=jel.journal_entry, account=target, debit=Decimal("0"), credit=amount_mad, currency="MAD",
        description=(f"Invoice {waiting.invoice_number} — {waiting.customer_name} — {euros} EUR exchanged "
                     f"into {amount_mad} MAD (rate {rate})")[:500],
    )
    inv_like = {"id": waiting.cmr_invoice_id, "number": waiting.invoice_number,
                "customer_name": waiting.customer_name, "trip_reference": waiting.trip_reference,
                "currency": waiting.currency, "total": waiting.invoice_total}
    return _receipt(jel, inv_like, euros, amount_mad, matched_by, exchanged_from=waiting), None


def undo_receipts(jel):
    """Put the matched money back on the 34971 suspense leg and drop the receipts.
    Caller holds transaction.atomic() and has checked the period. Returns an error
    text when the euros of this line were already exchanged."""
    receipts = list(jel.invoice_receipts.all())
    if not receipts:
        return None
    if any(r.exchanges.exists() for r in receipts):
        return "Some of these euros have been exchanged — undo the exchange on the MAD account first"
    be = jel.journal_entry
    for r in receipts:
        undo_lettrage_of(_settling_lines(r.cmr_invoice_id, r.invoice_number))
        amount = r.covered_amount if r.amount_mad is None else r.amount_mad
        codes = (EUR_HELD_CODE,) if r.amount_mad is None else (AR_CODE, REVENUE_CODE)
        line = be.lines.filter(account__code__in=codes, credit=amount,
                               description__contains=f"Invoice {r.invoice_number}").first()
        if line:
            line.delete()
        susp = be.lines.filter(account__code=SUSPENSE_CODE).first()
        if susp:
            susp.credit = (susp.credit or Decimal("0")) + amount
            susp.save()
        else:
            JournalEntryLine.objects.create(
                journal_entry=be, account=Account.objects.get(code=SUSPENSE_CODE),
                debit=Decimal("0"), credit=amount, currency=jel.currency, description=be.description[:500])
        r.delete()
    return None


# ─── Suggestions ────────────────────────────────────────────────────────────

_WORD = re.compile(r"[A-Z0-9]{4,}")
_SKIP_WORDS = {"VOYAGES", "TRAVEL", "TOURS", "AGENCY", "AGENCE", "VIREMENT", "RECEPTION", "FAVEUR",
               "RAPATRIEMENT", "COMMERCIAL", "RECU", "SARL", "GMBH", "LTD"}


def _text_score(inv, haystack):
    score, why = 0, []
    for ref in (inv.get("invoice_number"), inv.get("trip_reference")):
        if ref and len(ref) >= 4 and ref.upper() in haystack:
            score += 50
            why.append(f"{ref} in the text")
            break
    words = {w for w in _WORD.findall(f"{inv.get('customer_name') or ''} {inv.get('opportunity_title') or ''}".upper())
             if w not in _SKIP_WORDS}
    hits = [w for w in words if w in haystack]
    if hits:
        score += 35
        why.append("name: " + ", ".join(sorted(hits)[:3]))
    return score, why


def _score(inv, line_amount, haystack, eur_line):
    total = _dec(inv.get("total")) or Decimal("0")
    left = total - covered_so_far(inv["id"])
    if left <= CENT:
        return None
    if eur_line and is_mad(inv.get("currency")):
        return None
    score, why = _text_score(inv, haystack)
    if eur_line:
        # Usually the 70 % the bank keeps in euros, sometimes the whole amount.
        for share, label in ((Decimal("1"), "the open amount"), (Decimal("0.7"), "70 % of it")):
            if abs(left * share - line_amount) <= Decimal("1"):
                score += 40
                why.append(f"euros = {label}")
                break
    elif is_mad(inv.get("currency")):
        if abs(left - line_amount) <= Decimal("1"):
            score += 40
            why.append("amount matches")
        elif left and abs(left - line_amount) / left <= Decimal("0.05"):
            score += 15
            why.append("amount close")
    elif left:
        rate = line_amount / left
        rate30 = line_amount / (left * Decimal("0.3"))
        if Decimal("9.5") <= rate <= Decimal("12.5"):
            score += 25 if Decimal("10.3") <= rate <= Decimal("11.5") else 10
            why.append(f"≈ {rate.quantize(Decimal('0.01'))} MAD per {inv.get('currency')}")
        elif Decimal("9.5") <= rate30 <= Decimal("12.5"):
            score += 20
            why.append(f"≈ 30 % exchanged at {rate30.quantize(Decimal('0.01'))}")
    return score, why, left


def _invoice_dict(inv, left, score=None, why=None):
    return {
        "cmr_invoice_id": inv["id"], "invoice_number": inv.get("invoice_number"),
        "customer_name": inv.get("customer_name"), "trip_reference": inv.get("trip_reference"),
        "opportunity_title": inv.get("opportunity_title"), "currency": inv.get("currency") or "MAD",
        "total": str(_dec(inv.get("total"))), "open": str(left), "invoice_date": inv.get("invoice_date"),
        "status": inv.get("status"), "score": score, "why": why or [],
    }


def _receipt_dict(r):
    return {
        "id": str(r.id), "invoice_number": r.invoice_number, "customer_name": r.customer_name,
        "trip_reference": r.trip_reference, "currency": r.currency, "covered_amount": str(r.covered_amount),
        "amount_mad": str(r.amount_mad) if r.amount_mad is not None else None,
        "rate": str(r.rate.quantize(Decimal("0.0001"))) if r.rate else None,
        "awaiting_exchange": r.amount_mad is None, "exchanged_from": str(r.exchanged_from_id or "") or None,
    }


def _bank_line(jel_id):
    return JournalEntryLine.objects.select_related("journal_entry", "account").filter(id=jel_id).first()


@api_view(["GET"])
@permission_classes([RoleWriteAccess])
def invoice_suggestions(request, jel_id):
    """For an incoming line: CRM invoices with money still open (best match
    first) and, on a MAD account, the euros waiting for exchange."""
    jel = _bank_line(jel_id)
    if not jel:
        return Response({"success": False, "message": "Transaction not found"}, status=status.HTTP_404_NOT_FOUND)
    err = validate_line(jel)
    if err:
        return Response({"success": False, "message": err}, status=status.HTTP_400_BAD_REQUEST)
    try:
        from .cmr_client import CMRClient
        invoices = CMRClient().get_invoices(fetch_all=True)
    except Exception as e:  # noqa: BLE001
        return Response({"success": False, "message": f"Could not fetch CRM invoices: {e}"},
                        status=status.HTTP_502_BAD_GATEWAY)
    eur_line = is_eur_line(jel)
    unallocated = line_unallocated(jel)
    haystack = f"{jel.journal_entry.description} {jel.journal_entry.reference} {jel.description}".upper()
    rows = []
    for inv in invoices:
        scored = _score(inv, unallocated, haystack, eur_line)
        if scored is None:
            continue
        score, why, left = scored
        rows.append(_invoice_dict(inv, left, score, why))
    rows.sort(key=lambda r: (-(r["score"] or 0), r["invoice_date"] or ""))
    waiting = []
    if not eur_line:
        for r in InvoiceReceipt.objects.filter(amount_mad__isnull=True).select_related(
                "journal_entry_line__journal_entry").order_by("created_at"):
            left = waiting_euros(r)
            if left > CENT:
                waiting.append({**_receipt_dict(r), "waiting": str(left),
                                "received_on": str(r.journal_entry_line.journal_entry.date)})
    return Response({"success": True, "data": {
        "eur_account": eur_line,
        "unallocated": str(unallocated),
        "unallocated_mad": str(unallocated),  # kept for older clients
        "suggestions": rows[:40],
        "waiting_exchange": waiting,
        "matched": [_receipt_dict(r) for r in jel.invoice_receipts.all()],
    }})


@api_view(["POST"])
@permission_classes([RoleWriteAccess])
def match_invoice(request, jel_id):
    """Match (part of) an incoming bank line.

    To an invoice — body: cmr_invoice_id; covered_amount in the invoice's currency
    (default: what is open, capped by the line on the EUR account); amount_mad on a
    MAD account (default: what is left of the line).
    To waiting euros (an exchange) — body: exchanged_from (receipt id), euros,
    amount_mad."""
    data = request.data
    jel = _bank_line(jel_id)
    if not jel:
        return Response({"success": False, "message": "Transaction not found"}, status=status.HTTP_404_NOT_FOUND)
    err = validate_line(jel)
    if err:
        return Response({"success": False, "message": err}, status=status.HTTP_400_BAD_REQUEST)
    created_by = f"{request.user.first_name} {request.user.last_name}".strip() or request.user.username

    if data.get("exchanged_from"):
        waiting = InvoiceReceipt.objects.filter(id=data["exchanged_from"], amount_mad__isnull=True).first()
        if not waiting:
            return Response({"success": False, "message": "Waiting euros not found"},
                            status=status.HTTP_404_NOT_FOUND)
        with transaction.atomic():
            jel = JournalEntryLine.objects.select_for_update().select_related("journal_entry", "account").get(id=jel.id)
            InvoiceReceipt.objects.select_for_update().filter(id=waiting.id).first()
            euros = _dec(data.get("euros")) if data.get("euros") not in (None, "") else waiting_euros(waiting)
            amount_mad = (_dec(data.get("amount_mad")) if data.get("amount_mad") not in (None, "")
                          else line_unallocated(jel))
            receipt, rerr = apply_exchange(jel, waiting, euros, amount_mad, created_by)
            if rerr:
                transaction.set_rollback(True)
                return Response({"success": False, "message": rerr}, status=status.HTTP_400_BAD_REQUEST)
    else:
        inv_id = data.get("cmr_invoice_id")
        if not inv_id:
            return Response({"success": False, "message": "cmr_invoice_id is required"},
                            status=status.HTTP_400_BAD_REQUEST)
        try:
            from .cmr_client import CMRClient
            inv = CMRClient().get_invoice(inv_id)
        except Exception as e:  # noqa: BLE001
            return Response({"success": False, "message": f"Could not fetch the CRM invoice: {e}"},
                            status=status.HTTP_502_BAD_GATEWAY)
        if not inv:
            return Response({"success": False, "message": "Invoice not found in the CRM"},
                            status=status.HTTP_404_NOT_FOUND)
        with transaction.atomic():
            jel = JournalEntryLine.objects.select_for_update().select_related("journal_entry", "account").get(id=jel.id)
            unallocated = line_unallocated(jel)
            open_amount = (_dec(inv.get("total")) or Decimal("0")) - covered_so_far(inv_id)
            if is_eur_line(jel):
                amount_mad = None
                covered = (_dec(data.get("covered_amount")) if data.get("covered_amount") not in (None, "")
                           else min(unallocated, open_amount))
            else:
                amount_mad = (_dec(data.get("amount_mad")) if data.get("amount_mad") not in (None, "")
                              else unallocated)
                if is_mad(inv.get("currency")):
                    covered = amount_mad
                elif data.get("covered_amount") not in (None, ""):
                    covered = _dec(data.get("covered_amount"))
                else:
                    covered = open_amount
            receipt, rerr = apply_receipt(jel, inv, covered, amount_mad, created_by)
            if rerr:
                transaction.set_rollback(True)
                return Response({"success": False, "message": rerr}, status=status.HTTP_400_BAD_REQUEST)

    log_action(request.user, "match", "InvoiceReceipt", receipt.id,
               {"invoice_number": receipt.invoice_number, "amount_mad": str(receipt.amount_mad),
                "covered": f"{receipt.covered_amount} {receipt.currency}",
                "exchange": bool(receipt.exchanged_from_id)})
    return Response({"success": True, "message": "Matched", "data": {
        **_receipt_dict(receipt), "unallocated": str(line_unallocated(jel)),
    }}, status=status.HTTP_201_CREATED)
