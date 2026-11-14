"""Fakturaregler: linjer og totaler, betalingsbetingelser, fortløbende nummer,
fakturakrav (momsbekendtgørelsens § 58), bogføring og FI-kort.
"""

import calendar
import re
from datetime import date, timedelta
from decimal import Decimal, InvalidOperation

from accounts import chart
from accounts.models import Account
from core.vat import EntryBuilder, add_sale, q2, vat_of
from journals.lettrage import customer_partner

from .models import PAYMENT_TERMS, Invoice

ZERO = Decimal("0")
TERMS = {code: (name, kind, days) for code, name, kind, days in PAYMENT_TERMS}

# Omsætningskonto efter momskode, når linjen ikke har en konto.
REVENUE_BY_CODE = {
    "S21": chart.REVENUE_EU_GOODS, "S22": chart.REVENUE_EU_GOODS, "S23": chart.REVENUE_EU_SERVICES,
    "S41": chart.REVENUE_NON_EU_GOODS, "S42": chart.REVENUE_NON_EU_SERVICES,
}
EU_B2B_RUBRIKS = {"B_goods", "B_goods_other", "B_services"}
# Momskoder, hvor køber skal betale momsen (fakturaen skal påføres "Omvendt betalingspligt").
REVERSE_CHARGE_SALES = {"S02", "S21", "S22", "S23"}


# ─── Betalingsbetingelser ─────────────────────────────────────────────────────

def due_date_for(invoice_date, terms_code):
    """Forfaldsdato: netto x dage, eller løbende måned + x dage."""
    name, kind, days = TERMS.get(terms_code, TERMS["net14"])
    if kind == "lm":
        last = date(invoice_date.year, invoice_date.month,
                    calendar.monthrange(invoice_date.year, invoice_date.month)[1])
        return last + timedelta(days=days)
    return invoice_date + timedelta(days=days)


def terms_text(terms_code):
    return TERMS.get(terms_code, TERMS["net14"])[0]


# ─── Nummerering ──────────────────────────────────────────────────────────────

DRAFT_PREFIX = "UDK"


def draft_number():
    from journals.numbering import next_number
    return next_number(Invoice, "invoice_number", DRAFT_PREFIX, 5)


def is_draft_number(number):
    return str(number).startswith(DRAFT_PREFIX + "-")


def next_invoice_number(model=Invoice, field="invoice_number"):
    """Næste fortløbende fakturanummer (kun tal: 1, 2, 3 …). Gives først ved
    bogføring, så slettede udkast ikke efterlader huller i nummerrækken."""
    max_num = 0
    for v in model.objects.values_list(field, flat=True):
        if v and str(v).isdigit():
            max_num = max(max_num, int(v))
    return str(max_num + 1)


# ─── Linjer ───────────────────────────────────────────────────────────────────

class LineError(ValueError):
    pass


def save_lines(parent, line_model, fk, lines_data, kind="sales"):
    """Erstat linjerne på et udkast. Returnerer (subtotal, moms) i dokumentets valuta."""
    from core.models import TaxCode

    if not lines_data:
        raise LineError("Der skal være mindst én linje")
    accounts = {str(a.id): a for a in Account.objects.filter(
        id__in=[l.get("account_id") for l in lines_data if l.get("account_id")])}
    codes = {str(t.id): t for t in TaxCode.objects.filter(
        id__in=[l.get("tax_code_id") for l in lines_data if l.get("tax_code_id")])}
    getattr(parent, "lines").all().delete()
    subtotal = tax = ZERO
    for idx, data in enumerate(lines_data):
        if data.get("is_text"):
            line_model.objects.create(**{fk: parent}, description=data.get("description", ""), quantity=0,
                                      unit_price=0, is_text=True, position=idx)
            continue
        if data.get("account_id") and str(data["account_id"]) not in accounts:
            raise LineError(f"Kontoen {data['account_id']} findes ikke")
        account = accounts.get(str(data.get("account_id") or ""))
        if account is not None and account.is_header:
            raise LineError(f"{account.code} er en overskrift og kan ikke bruges på en linje")
        tc = codes.get(str(data.get("tax_code_id") or ""))
        if data.get("tax_code_id") and tc is None:
            raise LineError("Momskoden findes ikke")
        if tc is not None and tc.type not in (kind if kind == "sales" else "purchase", "both"):
            raise LineError(f"Momskoden {tc.code} kan ikke bruges på et salg")
        try:
            quantity = Decimal(str(data.get("quantity", 1)))
            unit_price = Decimal(str(data.get("unit_price", 0)))
        except (InvalidOperation, TypeError):
            raise LineError("Ugyldigt antal eller pris")
        amount = q2(quantity * unit_price)
        subtotal += amount
        tax += vat_of(amount, tc)
        line_model.objects.create(**{fk: parent}, description=data.get("description", ""), quantity=quantity,
                                  unit=data.get("unit") or "stk.", unit_price=unit_price, tax_code=tc,
                                  account=account, position=idx)
    return subtotal, tax


def refresh_totals(doc):
    """Genberegn subtotal, moms og total ud fra linjerne (per linje afrundet)."""
    subtotal = tax = ZERO
    for line in doc.lines.select_related("tax_code").all():
        if line.is_text:
            continue
        amount = q2(line.amount)
        subtotal += amount
        tax += vat_of(amount, line.tax_code)
    doc.subtotal, doc.tax_amount, doc.total = subtotal, tax, subtotal + tax
    doc.save(update_fields=["subtotal", "tax_amount", "total"])


# ─── Fakturakrav (momsbekendtgørelsens § 58) ─────────────────────────────────

def is_reverse_charge(invoice):
    return any(l.tax_code and l.tax_code.code in REVERSE_CHARGE_SALES
               for l in invoice.lines.select_related("tax_code").all())


def compliance_errors(invoice):
    """Hvad mangler, før fakturaen må udstedes. Tom liste = ok."""
    from core.models import CompanySettings

    errors = []
    settings_obj = CompanySettings.objects.first()
    if not settings_obj or not (settings_obj.tax_id or "").strip():
        errors.append("Virksomhedens CVR-/SE-nummer mangler (Indstillinger)")
    if not settings_obj or not (settings_obj.company_name and settings_obj.address):
        errors.append("Virksomhedens navn og adresse mangler (Indstillinger)")
    c = invoice.customer
    if not c.name or not (c.address or "").strip():
        errors.append("Kundens navn og adresse skal stå på fakturaen")
    lines = list(invoice.lines.select_related("tax_code").all())
    real = [l for l in lines if not l.is_text]
    if not real:
        errors.append("Fakturaen har ingen linjer med beløb")
    for l in real:
        if not (l.description or "").strip():
            errors.append("Hver linje skal beskrive varens eller ydelsens art")
            break
    if any(l.tax_code is None for l in real):
        errors.append("Hver linje skal have en momskode (også momsfrie linjer)")
    rubriks = {l.tax_code.rubrik for l in real if l.tax_code}
    if rubriks & EU_B2B_RUBRIKS and not (c.tax_id or "").strip():
        errors.append("EU-salg uden moms kræver kundens momsnummer (VAT-nummer) på fakturaen")
    if c.is_public and not re.fullmatch(r"\d{13}", c.ean or ""):
        errors.append("Offentlige kunder skal have et EAN-/GLN-nummer på 13 cifre (e-faktura via NemHandel)")
    if invoice.currency != chart.BASE_CURRENCY and (invoice.exchange_rate or 0) <= 0:
        errors.append("En faktura i fremmed valuta skal have en kurs")
    return errors


# ─── FI-kort (+71) ────────────────────────────────────────────────────────────

def _mod10(digits):
    """Kontrolciffer, modulus 10 (vægt 2-1-2 … fra højre, tværsum)."""
    total = 0
    for i, ch in enumerate(reversed(digits)):
        n = int(ch) * (2 if i % 2 == 0 else 1)
        total += n // 10 + n % 10
    return str((10 - total % 10) % 10)


def fi_payment_id(invoice_number):
    """Betalingsidentifikation (15 cifre inkl. kontrolciffer) til FI-kort type 71.
    TODO(revisor/bank): bekræft kontrolcifferberegningen mod pengeinstituttets
    FI-specifikation, før kortet bruges i produktion."""
    digits = re.sub(r"\D", "", str(invoice_number))[-14:].rjust(14, "0")
    return digits + _mod10(digits)


def fi_line(invoice_number, creditor_no):
    """Kodelinjen på FI-kortet, fx +71<000000000012343+12345678<."""
    if not creditor_no or not str(creditor_no).isdigit() or len(str(creditor_no)) != 8:
        return ""
    return f"+71<{fi_payment_id(invoice_number)}+{creditor_no}<"


# ─── Bogføring ────────────────────────────────────────────────────────────────

def _fx(doc):
    if doc.currency and doc.currency != chart.BASE_CURRENCY:
        return {"currency": doc.currency, "exchange_rate": doc.exchange_rate}
    return {}


def _to_dkk(amount, doc):
    return q2(Decimal(amount) * (doc.exchange_rate if doc.currency != chart.BASE_CURRENCY else 1))


def build_invoice_entry(invoice, sign=1, ratio=Decimal("1"), label=None):
    """EntryBuilder for en faktura (sign=1) eller kreditnota (sign=-1, andel `ratio`).
    Omsætning og moms beregnes i DKK; debitorposten er summen."""
    builder = EntryBuilder(fx=_fx(invoice))
    receivable = Account.objects.get(code=chart.RECEIVABLE)
    revenue = {a.code: a for a in Account.objects.filter(code__in={chart.REVENUE, *REVENUE_BY_CODE.values()})}
    label = label or f"Faktura {invoice.invoice_number} — {invoice.customer.name}"
    total_vat = ZERO
    for line in invoice.lines.select_related("account", "tax_code").all():
        if line.is_text:
            continue
        net = _to_dkk(q2(line.amount) * ratio, invoice)
        account = line.account or revenue[REVENUE_BY_CODE.get(line.tax_code.code if line.tax_code else "",
                                                              chart.REVENUE)]
        total_vat += add_sale(builder, account, sign * net, line.tax_code, label)
    # Debitor = alt, hvad der er krediteret (fortegn modsat).
    builder.add(receivable, -builder.balance, description=label, partner=customer_partner(invoice.customer))
    return builder, sign * total_vat


def post_invoice(invoice, created_by):
    """Giv fakturanummer (hvis udkast), bogfør (DR debitorer / CR omsætning og
    salgsmoms) og knyt posteringen. Kaldes i transaction.atomic(). Returnerer
    (entry, fejl)."""
    from journals.models import JournalEntry
    from journals.numbering import next_je_number

    errors = compliance_errors(invoice)
    if errors:
        return None, "; ".join(errors)
    if is_draft_number(invoice.invoice_number):
        invoice.invoice_number = next_invoice_number()
        invoice.save(update_fields=["invoice_number"])
    refresh_totals(invoice)
    builder, _ = build_invoice_entry(invoice)
    entry = JournalEntry.objects.create(
        entry_number=next_je_number(), date=invoice.date,
        description=f"Faktura {invoice.invoice_number} — {invoice.customer.name}",
        reference=f"FAKTURA:{invoice.invoice_number}", piece_number=invoice.invoice_number,
        source="invoice", source_id=str(invoice.id), is_posted=True, created_by=created_by)
    builder.write(entry)
    invoice.journal_entry = entry
    invoice.save(update_fields=["journal_entry"])
    return entry, None


def post_credit_note(cn, invoice, created_by):
    """Kreditnota: spejler fakturaens linjer for andelen cn.total / faktura.total
    (DR omsætning og salgsmoms / CR debitorer), med samme momskoder."""
    from journals.models import JournalEntry
    from journals.numbering import next_je_number

    if not invoice.journal_entry_id:
        return None, "Fakturaen er ikke bogført"
    ratio = (cn.total / invoice.total) if invoice.total else Decimal("1")
    label = f"Kreditnota {cn.credit_note_number} — {cn.customer.name} (faktura {invoice.invoice_number})"
    builder, _ = build_invoice_entry(invoice, sign=-1, ratio=ratio, label=label)
    entry = JournalEntry.objects.create(
        entry_number=next_je_number(), date=cn.date, description=label,
        reference=f"KREDITNOTA:{cn.credit_note_number}", piece_number=cn.credit_note_number,
        source="credit_note", source_id=str(cn.id), is_posted=True, created_by=created_by)
    builder.write(entry)
    return entry, None


def invoice_print_data(invoice):
    """Felter, en fakturaskabelon/PDF/e-faktura skal vise (§ 58)."""
    from core.models import CompanySettings

    s = CompanySettings.objects.first()
    lines = list(invoice.lines.select_related("tax_code").all())
    vat_by_rate = {}
    for l in lines:
        if l.is_text or l.tax_code is None:
            continue
        key = (str(l.tax_code.rate), l.tax_code.invoice_text)
        v = vat_by_rate.setdefault(key, {"rate": str(l.tax_code.rate), "base": ZERO, "vat": ZERO,
                                         "text": l.tax_code.invoice_text})
        v["base"] += q2(l.amount)
        v["vat"] += vat_of(q2(l.amount), l.tax_code)
    notes = sorted({l.tax_code.invoice_text for l in lines if l.tax_code and l.tax_code.invoice_text})
    fi = fi_line(invoice.invoice_number, s.fi_creditor_no if s else "") if not is_draft_number(
        invoice.invoice_number) else ""
    return {
        "seller": {"name": s.company_name if s else "", "address": s.address if s else "",
                   "city": s.city if s else "", "cvr": s.tax_id if s else "", "email": s.email if s else "",
                   "phone": s.phone if s else "", "bank_reg_no": s.bank_reg_no if s else "",
                   "bank_account_no": s.bank_account_no if s else "", "iban": s.iban if s else "",
                   "bic": s.bic if s else "", "gln": s.gln if s else ""},
        "buyer": {"name": invoice.customer.name, "address": invoice.customer.address,
                  "postal_code": invoice.customer.postal_code, "city": invoice.customer.city,
                  "country": invoice.customer.country, "vat_number": invoice.customer.tax_id,
                  "ean": invoice.customer.ean},
        "delivery_date": (invoice.delivery_date or invoice.date).isoformat(),
        "payment_terms": terms_text(invoice.payment_terms_code),
        "vat_specification": [{**v, "base": str(v["base"]), "vat": str(v["vat"])} for v in vat_by_rate.values()],
        "vat_dkk": str(_to_dkk(invoice.tax_amount, invoice)),
        "reverse_charge": is_reverse_charge(invoice),
        "legal_notes": notes,
        "fi_line": fi,
        "footer": s.invoice_footer if s else "",
    }
