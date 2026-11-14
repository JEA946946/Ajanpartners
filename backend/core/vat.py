"""Moms: hvordan en momskode bogføres, momsangivelsen og momsafregningen.

Bogføring pr. linje (EntryBuilder):
  Salg     CR omsætning (netto), CR salgsmoms (netto × sats).
  Køb      DR omkostning (netto + ikke-fradragsberettiget moms), DR købsmoms
           (moms × fradragsprocent).
  Omvendt betalingspligt (EU-varer/-ydelser, import, indenlandsk byggeri):
           leverandøren får kun nettobeløbet. Momsen beregnes af køber:
           CR moms af varekøb/ydelseskøb udland (eller salgsmoms ved indenlandsk),
           DR købsmoms for den fradragsberettigede del.
  Energiafgift (E-koder): hele beløbet bogføres på afgiftskontoen (godtgørelse).
Hver linje får momskoden i JournalEntryLine.vat_code.

Momsangivelsen (Skats felter) tages fra momskontiene (bevægelsen i perioden, uden
selve momsafregningen), og rubrik A/B/C fra nettobeløbene på linjer med en
momskode, der hører til rubrikken. Den kan derfor altid afstemmes mod
saldobalancen. Momsafregningen nulstiller momskontiene mod momsafregningskontoen
(chart.VAT_SETTLEMENT); øredifferencen mellem de præcise beløb og angivelsens
hele kroner går til øreafrunding.
"""

import calendar
from collections import OrderedDict
from datetime import date
from decimal import ROUND_HALF_UP, Decimal

from django.db import transaction
from django.db.models import Sum
from django.utils import timezone

from accounts import chart

CENT = Decimal("0.01")
ZERO = Decimal("0")


def q2(v):
    return Decimal(v).quantize(CENT, ROUND_HALF_UP)


# ─── Bogføring ────────────────────────────────────────────────────────────────

class EntryBuilder:
    """Samler linjer (konto, momskode, tekst, debitor/kreditor) som fortegnsbeløb
    (debet positiv) og skriver dem på en postering. Valuta: alle beløb er DKK;
    `fx` (currency, exchange_rate) skrives på linjerne med valutabeløbet."""

    def __init__(self, fx=None):
        self.rows = OrderedDict()
        self.fx = fx or {}

    def add(self, account, amount, vat_code="", description="", partner=None):
        amount = q2(amount)
        if not amount:
            return
        key = (account.id if hasattr(account, "id") else account, vat_code or "", description,
               tuple(sorted((partner or {}).items())))
        self.rows[key] = self.rows.get(key, ZERO) + amount

    @property
    def balance(self):
        return sum(self.rows.values(), ZERO)

    def write(self, entry):
        from journals.models import JournalEntryLine
        rate = self.fx.get("exchange_rate")
        currency = self.fx.get("currency") or chart.BASE_CURRENCY
        for (account_id, vat_code, description, partner), amount in self.rows.items():
            if not amount:
                continue
            fx = {}
            if currency != chart.BASE_CURRENCY and rate:
                fx = {"currency": currency, "exchange_rate": rate,
                      "amount_currency": q2(amount / Decimal(rate))}
            JournalEntryLine.objects.create(
                journal_entry=entry, account_id=account_id,
                debit=amount if amount > 0 else ZERO, credit=-amount if amount < 0 else ZERO,
                vat_code=vat_code, description=description[:500], **dict(partner), **fx,
            )


def vat_of(net, tax_code):
    """Momsen af et nettobeløb (0 for momsfri koder og energiafgifter)."""
    if tax_code is None or tax_code.energy_tax or not tax_code.rate:
        return ZERO
    return q2(Decimal(net) * tax_code.rate / Decimal("100"))


def supplier_vat(net, tax_code):
    """Den moms, leverandøren fakturerer (0 ved omvendt betalingspligt, energiafgift og momsfri)."""
    if tax_code is None or tax_code.reverse_charge or tax_code.energy_tax:
        return ZERO
    return vat_of(net, tax_code)


def add_sale(builder, account, net, tax_code, description=""):
    """Salgslinje: CR omsætning og CR salgsmoms. Returnerer momsen, kunden skal betale."""
    code = tax_code.code if tax_code else ""
    builder.add(account, -Decimal(net), code, description)
    vat = vat_of(net, tax_code)
    if vat:
        builder.add(tax_code.account, -vat, code, f"Moms {description}".strip())
    return vat


def add_purchase(builder, account, net, tax_code, description=""):
    """Købslinje. Returnerer den moms, leverandøren fakturerer (0 ved omvendt
    betalingspligt og momsfri køb)."""
    net = Decimal(net)
    code = tax_code.code if tax_code else ""
    if tax_code is not None and tax_code.energy_tax:
        builder.add(tax_code.account, net, code, description)
        return ZERO
    vat = vat_of(net, tax_code)
    deductible = q2(vat * (tax_code.deduction_rate if tax_code else 0) / Decimal("100")) if vat else ZERO
    builder.add(account, net + vat - deductible, code, description)
    if not vat:
        return ZERO
    if tax_code.reverse_charge:
        builder.add(tax_code.account, -vat, code, f"Moms (omvendt betalingspligt) {description}".strip())
        if deductible:
            builder.add(tax_code.input_account or tax_code.account, deductible, code,
                        f"Fradrag {description}".strip())
        return ZERO
    if deductible:
        builder.add(tax_code.account, deductible, code, f"Købsmoms {description}".strip())
    return vat


# ─── Perioder ─────────────────────────────────────────────────────────────────

PERIOD_MONTHS = {"month": 1, "quarter": 3, "half": 6}


def periods_for(year, vat_period):
    """[(start, slut, navn)] for året efter kundens momsperiode."""
    months = PERIOD_MONTHS.get(vat_period)
    if not months:
        return []
    out = []
    for i, m in enumerate(range(1, 13, months), start=1):
        end_month = m + months - 1
        start, end = date(year, m, 1), date(year, end_month, calendar.monthrange(year, end_month)[1])
        name = {1: f"{year}-{m:02d}", 3: f"{year} {i}. kvartal", 6: f"{year} {i}. halvår"}[months]
        out.append((start, end, name))
    return out


def deadline(period_end, vat_period):
    """Fristen for angivelse og betaling.

    Måned: den 25. i måneden efter. Kvartal og halvår: den 1. i den tredje måned
    efter periodens udløb (1. kvartal → 1. juni, 2. halvår → 1. marts).
    TODO(revisor): Skat flytter fristen, når den falder på en weekend eller
    helligdag, og har enkelte særfrister (fx juni for månedsangivere); tjek mod
    Skats momskalender for året.
    """
    y, m = period_end.year, period_end.month
    if vat_period == "month":
        y, m = (y + 1, 1) if m == 12 else (y, m + 1)
        return date(y, m, 25)
    m += 3
    if m > 12:
        y, m = y + 1, m - 12
    return date(y, m, 1)


def period_of(d, vat_period):
    for start, end, name in periods_for(d.year, vat_period):
        if start <= d <= end:
            return start, end, name
    return None


# ─── Momsangivelse ────────────────────────────────────────────────────────────

# Skats felter på momsangivelsen (TastSelv Erhverv), i formularens rækkefølge.
FIELDS = [
    ("salgsmoms", "Salgsmoms (udgående moms)"),
    ("moms_varekoeb_udland", "Moms af varekøb i udlandet (både EU og lande uden for EU)"),
    ("moms_ydelseskoeb_udland", "Moms af ydelseskøb i udlandet med omvendt betalingspligt"),
    ("koebsmoms", "Købsmoms (indgående moms)"),
    ("olie_flaskegasafgift", "Olie- og flaskegasafgift"),
    ("elafgift", "Elafgift"),
    ("naturgas_bygasafgift", "Naturgas- og bygasafgift"),
    ("kulafgift", "Kulafgift"),
    ("co2_afgift", "CO2-afgift"),
    ("vandafgift", "Vandafgift"),
    ("momstilsvar", "Momstilsvar (beløb til betaling eller tilgode)"),
    ("rubrik_a_varer", "Rubrik A – varer: værdien uden moms af varekøb i andre EU-lande (EU-erhvervelser)"),
    ("rubrik_a_ydelser", "Rubrik A – ydelser: værdien uden moms af ydelseskøb i andre EU-lande"),
    ("rubrik_b_varer_indberettes", "Rubrik B – varer: værdien af varesalg uden moms til andre EU-lande, "
                                   "der skal indberettes til EU-salg uden moms"),
    ("rubrik_b_varer_ikke", "Rubrik B – varer: værdien af varesalg uden moms til andre EU-lande, "
                            "der ikke skal indberettes til EU-salg uden moms"),
    ("rubrik_b_ydelser", "Rubrik B – ydelser: værdien af ydelsessalg uden moms til andre EU-lande"),
    ("rubrik_c", "Rubrik C – værdien af andre varer og ydelser, der leveres uden afgift"),
]
FIELD_NAMES = dict(FIELDS)

# Felt → (konto, fortegn): +1 = kreditsaldo er tilsvar (skyldig), −1 = debetsaldo er tilgode.
ACCOUNT_FIELDS = [
    ("salgsmoms", chart.VAT_OUTPUT, 1),
    ("moms_varekoeb_udland", chart.VAT_EU_GOODS, 1),
    ("moms_ydelseskoeb_udland", chart.VAT_EU_SERVICES, 1),
    ("koebsmoms", chart.VAT_INPUT, -1),
    ("olie_flaskegasafgift", chart.TAX_OIL, -1),
    ("elafgift", chart.TAX_ELECTRICITY, -1),
    ("naturgas_bygasafgift", chart.TAX_GAS, -1),
    ("kulafgift", chart.TAX_COAL, -1),
    ("co2_afgift", chart.TAX_CO2, -1),
    ("vandafgift", chart.TAX_WATER, -1),
]
RUBRIK_FIELDS = {
    "A_goods": ("rubrik_a_varer", -1), "A_services": ("rubrik_a_ydelser", -1),
    "B_goods": ("rubrik_b_varer_indberettes", 1), "B_goods_other": ("rubrik_b_varer_ikke", 1),
    "B_services": ("rubrik_b_ydelser", 1), "C": ("rubrik_c", 1),
}


def _lines(start, end):
    from journals.models import JournalEntryLine
    return (JournalEntryLine.objects
            .filter(journal_entry__is_posted=True, journal_entry__date__gte=start, journal_entry__date__lte=end)
            .exclude(journal_entry__source="vat_settlement"))


def _whole(v):
    """Hele kroner (angivelsen på TastSelv er i hele kroner)."""
    return Decimal(v).quantize(Decimal("1"), ROUND_HALF_UP)


def compute(start, end):
    """Momsangivelsens felter for perioden, og afstemningen mod momskontiene."""
    from accounts.models import Account
    from core.models import TaxCode

    lines = _lines(start, end)
    by_account = {r["account__code"]: (r["dr"] or ZERO, r["cr"] or ZERO)
                  for r in lines.filter(account__code__in=chart.VAT_ACCOUNTS)
                  .values("account__code").annotate(dr=Sum("debit"), cr=Sum("credit"))}
    coded = {r["account__code"]: (r["dr"] or ZERO, r["cr"] or ZERO)
             for r in lines.filter(account__code__in=chart.VAT_ACCOUNTS).exclude(vat_code="")
             .values("account__code").annotate(dr=Sum("debit"), cr=Sum("credit"))}

    exact = {k: ZERO for k, _ in FIELDS}
    reconciliation = []
    names = dict(Account.objects.filter(code__in=chart.VAT_ACCOUNTS).values_list("code", "name"))
    for field, code, sign in ACCOUNT_FIELDS:
        dr, cr = by_account.get(code, (ZERO, ZERO))
        value = (cr - dr) if sign > 0 else (dr - cr)
        exact[field] = value
        cdr, ccr = coded.get(code, (ZERO, ZERO))
        from_codes = (ccr - cdr) if sign > 0 else (cdr - ccr)
        reconciliation.append({
            "field": field, "account_code": code, "account_name": names.get(code, ""),
            "booked": str(value), "from_vat_codes": str(from_codes),
            # Bevægelser på momskontoen uden momskode (manuelle posteringer).
            "manual": str(value - from_codes),
        })

    rubrik_codes = {}
    for tc in TaxCode.objects.exclude(rubrik=""):
        rubrik_codes.setdefault(tc.rubrik, []).append(tc.code)
    for rubrik, (field, sign) in RUBRIK_FIELDS.items():
        codes = rubrik_codes.get(rubrik, [])
        if not codes:
            continue
        t = (lines.filter(vat_code__in=codes).exclude(account__code__in=chart.VAT_ACCOUNTS)
             .aggregate(dr=Sum("debit"), cr=Sum("credit")))
        dr, cr = t["dr"] or ZERO, t["cr"] or ZERO
        exact[field] = (cr - dr) if sign > 0 else (dr - cr)

    payable = (exact["salgsmoms"] + exact["moms_varekoeb_udland"] + exact["moms_ydelseskoeb_udland"]
               - exact["koebsmoms"] - exact["olie_flaskegasafgift"] - exact["elafgift"]
               - exact["naturgas_bygasafgift"] - exact["kulafgift"] - exact["co2_afgift"] - exact["vandafgift"])
    exact["momstilsvar"] = payable
    whole = {k: _whole(v) for k, v in exact.items()}
    whole["momstilsvar"] = (whole["salgsmoms"] + whole["moms_varekoeb_udland"] + whole["moms_ydelseskoeb_udland"]
                            - whole["koebsmoms"] - whole["olie_flaskegasafgift"] - whole["elafgift"]
                            - whole["naturgas_bygasafgift"] - whole["kulafgift"] - whole["co2_afgift"]
                            - whole["vandafgift"])
    return {
        "fields": [{"key": k, "name": n, "amount": str(exact[k]), "amount_kr": str(whole[k])} for k, n in FIELDS],
        "exact": exact, "whole": whole, "reconciliation": reconciliation,
    }


def balances_at(d):
    """Momskontienes og momsafregningskontoens saldo pr. dag d (debet − kredit), til
    afstemning mod saldobalancen."""
    from journals.models import JournalEntryLine
    rows = (JournalEntryLine.objects.filter(journal_entry__is_posted=True, journal_entry__date__lte=d,
                                            account__code__in=(*chart.VAT_ACCOUNTS, chart.VAT_SETTLEMENT))
            .values("account__code").annotate(dr=Sum("debit"), cr=Sum("credit")))
    return {r["account__code"]: str((r["dr"] or ZERO) - (r["cr"] or ZERO)) for r in rows}


# ─── Afregning og angivelse ───────────────────────────────────────────────────

def settle(start, end, created_by, on_date=None, vat_period="quarter"):
    """Bogfør momsafregningen: momskontiene nulstilles mod momsafregningskontoen.
    Returnerer (VatReturn, fejl)."""
    from accounts.models import Account
    from core.models import VatReturn
    from journals.models import JournalEntry
    from journals.numbering import next_je_number
    from journals.periods import closed_period_error

    on_date = on_date or end
    err = closed_period_error(on_date)
    if err:
        return None, err
    with transaction.atomic():
        vr, _ = VatReturn.objects.select_for_update().get_or_create(
            period_start=start, period_end=end, defaults={"period_type": vat_period})
        if vr.status == "filed":
            return None, "Perioden er angivet og låst"
        if vr.settlement_entry_id:
            return None, f"Momsafregningen er allerede bogført ({vr.settlement_entry.entry_number})"
        result = compute(start, end)
        accounts = {a.code: a for a in Account.objects.filter(
            code__in=(*chart.VAT_ACCOUNTS, chart.VAT_SETTLEMENT, chart.ROUNDING))}
        builder = EntryBuilder()
        label = f"Momsafregning {start.isoformat()}–{end.isoformat()}"
        for field, code, sign in ACCOUNT_FIELDS:
            value = result["exact"][field]
            # Nulstil kontoen: en kreditsaldo (sign +1) debiteres, en debetsaldo krediteres.
            builder.add(accounts[code], sign * value, description=label)
        payable_whole = result["whole"]["momstilsvar"]
        builder.add(accounts[chart.VAT_SETTLEMENT], -payable_whole, description=label)
        diff = builder.balance
        if diff:
            builder.add(accounts[chart.ROUNDING], -diff, description="Øreafrunding moms")
        entry = JournalEntry.objects.create(
            entry_number=next_je_number(), date=on_date, description=label,
            reference=f"MOMS:{start.isoformat()}:{end.isoformat()}", source="vat_settlement",
            source_id=str(vr.id), is_posted=True, created_by=created_by)
        builder.write(entry)
        vr.fields = {k: str(v) for k, v in result["whole"].items()}
        vr.settlement_entry = entry
        vr.period_type = vat_period
        vr.save(update_fields=["fields", "settlement_entry", "period_type"])
    return vr, None


def unsettle(vr):
    """Fjern en bogført, ikke angivet momsafregning (fx efter en rettelse)."""
    if vr.status == "filed":
        return "Perioden er angivet og låst"
    entry = vr.settlement_entry
    if entry is None:
        return "Der er ingen momsafregning at fjerne"
    if entry.validated_at:
        return "Momsafregningen er valideret (måneden er lukket); tilbagefør den i stedet"
    with transaction.atomic():
        vr.settlement_entry = None
        vr.fields = {}
        vr.save(update_fields=["settlement_entry", "fields"])
        entry.delete()
    return None


def file_return(vr, filed_by, receipt_number=""):
    """Markér perioden som angivet hos Skat og lås den."""
    if vr.status == "filed":
        return "Perioden er allerede angivet"
    if not vr.settlement_entry_id:
        return "Bogfør momsafregningen før angivelsen"
    current = compute(vr.period_start, vr.period_end)["whole"]
    if {k: str(v) for k, v in current.items()} != vr.fields:
        return "Der er bogført i perioden efter afregningen. Fjern afregningen og bogfør den igen"
    vr.status = "filed"
    vr.filed_at = timezone.now()
    vr.filed_by = filed_by
    vr.receipt_number = receipt_number or ""
    vr.save(update_fields=["status", "filed_at", "filed_by", "receipt_number"])
    return None
