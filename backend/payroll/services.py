"""Lønkørsler: oprettelse, beregning, godkendelse og bogføring i lønjournalen."""

import calendar
from collections import OrderedDict
from datetime import date, timedelta
from decimal import Decimal

from django.db import models, transaction
from django.utils import timezone

from accounts import chart
from accounts.models import Account

from .calculations_dk import (CARD_FREE, CARD_MAIN, PayInput, TaxCard, calculate_pay,
                              fortnight_deduction, free_phone_month)
from .models import Employee, PayrollLine, PayrollRun

Z = Decimal("0")


class PayrollError(Exception):
    """Fejl, der vises for brugeren (400)."""


def period_for(frequency, year, month, period_start=None):
    if frequency == "month":
        start = date(year, month, 1)
        return start, date(year, month, calendar.monthrange(year, month)[1])
    if not period_start:
        raise PayrollError("En 14-dageskørsel kræver en startdato.")
    return period_start, period_start + timedelta(days=13)


def _employees_for(frequency, start, end):
    forms = ("month", "hourly") if frequency == "month" else ("fortnight",)
    return (Employee.objects.filter(is_active=True, pay_form__in=forms)
            .filter(models.Q(start_date__isnull=True) | models.Q(start_date__lte=end))
            .exclude(end_date__lt=start))


def default_line_values(emp, run):
    """Inddata til en ny lønlinje ud fra medarbejderens stamdata."""
    months = Decimal("1") if run.frequency == "month" else Decimal("12") / Decimal("26")
    hours = (emp.hours_per_week * Decimal("52") / (12 if run.frequency == "month" else 26)).quantize(Decimal("0.01"))
    if emp.pay_form == "hourly" or (emp.pay_form == "fortnight" and emp.hourly_rate and not emp.monthly_salary):
        base = (emp.hourly_rate * hours).quantize(Decimal("0.01"))
    else:
        base = emp.monthly_salary
    phone = (free_phone_month(run.year) * months).quantize(Decimal("0.01")) if emp.free_phone else Z
    return {
        "hours": hours,
        "base_salary": base,
        "car_benefit": (emp.car_benefit_month * months).quantize(Decimal("0.01")),
        "phone_benefit": phone,
    }


@transaction.atomic
def create_run(*, frequency, year, month, pay_date=None, period_start=None, created_by=""):
    start, end = period_for(frequency, year, month, period_start)
    if PayrollRun.objects.filter(frequency=frequency, period_start=start).exists():
        raise PayrollError(f"Der findes allerede en lønkørsel for perioden {start.isoformat()}.")
    employees = list(_employees_for(frequency, start, end))
    if not employees:
        raise PayrollError("Ingen aktive medarbejdere med denne lønform i perioden.")
    run = PayrollRun.objects.create(
        frequency=frequency, year=end.year, month=end.month, period_start=start, period_end=end,
        pay_date=pay_date or end, created_by=created_by,
    )
    for emp in employees:
        PayrollLine.objects.create(payroll_run=run, employee=emp, **default_line_values(emp, run))
    return run


def _frikort_used_before(emp, run):
    return (PayrollLine.objects.filter(employee=emp, payroll_run__year=run.year,
                                       payroll_run__status__in=("approved", "posted"),
                                       payroll_run__period_start__lt=run.period_start)
            .aggregate(s=models.Sum("frikort_used"))["s"] or Z)


def tax_card_for(emp, run):
    deduction = Z
    if emp.tax_card == CARD_MAIN:
        if run.frequency == "month":
            deduction = emp.deduction_month
        else:
            deduction = (emp.deduction_fortnight if emp.deduction_fortnight is not None
                         else fortnight_deduction(emp.deduction_month))
    remaining = Z
    if emp.tax_card == CARD_FREE:
        remaining = max(emp.free_card_amount - _frikort_used_before(emp, run), Z)
    return TaxCard(card_type=emp.tax_card, rate=emp.tax_rate, deduction=deduction, free_remaining=remaining)


def pay_input_for(line):
    emp, run = line.employee, line.payroll_run
    return PayInput(
        year=run.year, frequency=run.frequency,
        base_salary=line.base_salary, supplements=line.supplements, holiday_payout=line.holiday_payout,
        a_income_no_am=line.a_income_no_am, car_benefit=line.car_benefit, phone_benefit=line.phone_benefit,
        other_benefits=line.other_benefits, b_income=line.b_income, hours=line.hours,
        atp_class=emp.atp_class, pension_employee_pct=emp.pension_employee_pct,
        pension_employer_pct=emp.pension_employer_pct,
        holiday_type="without_pay" if emp.holiday_scheme == "feriekonto" else emp.holiday_type,
        holiday_allowance_pct=emp.holiday_allowance_pct, holiday_allowance_mode=emp.holiday_allowance_mode,
        sick_pay_refund=line.sick_pay_refund, tax_card=tax_card_for(emp, run),
    )


RESULT_FIELDS = ("holiday_allowance_paid", "holiday_allowance_accrued", "holiday_pay_accrued", "gross_cash",
                 "benefits", "atp_employee", "atp_employer", "pension_employee", "pension_employer",
                 "am_base", "am_contribution", "tax_base", "deduction_used", "frikort_used", "a_tax",
                 "net_pay", "employer_cost", "warnings")


def calculate_line(line):
    inp = pay_input_for(line)
    res = calculate_pay(inp)
    for f in RESULT_FIELDS:
        setattr(line, f, getattr(res, f))
    line.tax_card = inp.tax_card.card_type
    line.tax_rate = inp.tax_card.rate
    line.calculated = True
    line.save()
    return res


def recalc_totals(run):
    s = run.lines.aggregate(
        gross=models.Sum("gross_cash"), benefits=models.Sum("benefits"), am=models.Sum("am_contribution"),
        a_tax=models.Sum("a_tax"), atp_e=models.Sum("atp_employee"), atp_r=models.Sum("atp_employer"),
        pen_e=models.Sum("pension_employee"), pen_r=models.Sum("pension_employer"),
        hol_a=models.Sum("holiday_allowance_accrued"), hol_p=models.Sum("holiday_pay_accrued"),
        b=models.Sum("b_income"), a_no=models.Sum("a_income_no_am"), net=models.Sum("net_pay"),
    )
    g = {k: v or Z for k, v in s.items()}
    run.total_gross = g["gross"] + g["a_no"]
    run.total_benefits = g["benefits"]
    run.total_am = g["am"]
    run.total_a_tax = g["a_tax"]
    run.total_atp_employee = g["atp_e"]
    run.total_atp_employer = g["atp_r"]
    run.total_pension_employee = g["pen_e"]
    run.total_pension_employer = g["pen_r"]
    run.total_holiday = g["hol_a"] + g["hol_p"]
    run.total_b_income = g["b"]
    run.total_net = g["net"]
    run.save()


def _require_editable(run):
    if not run.is_editable:
        raise PayrollError("Lønkørslen er godkendt eller bogført og kan ikke ændres.")


@transaction.atomic
def calculate_run(run):
    run = PayrollRun.objects.select_for_update().get(pk=run.pk)
    _require_editable(run)
    lines = list(run.lines.select_related("employee", "payroll_run"))
    if not lines:
        raise PayrollError("Lønkørslen har ingen linjer.")
    for line in lines:
        calculate_line(line)
    recalc_totals(run)
    run.status = "calculated"
    run.save(update_fields=["status", "updated_at"])
    return run


@transaction.atomic
def update_line(run, line, data):
    """Ret inddata på en linje; kørslen går tilbage til kladde."""
    run = PayrollRun.objects.select_for_update().get(pk=run.pk)
    _require_editable(run)
    for f in PayrollLine.INPUT_FIELDS:
        if f not in data:
            continue
        if f == "note":
            line.note = str(data[f] or "")[:500]
        elif f == "b_income_am":
            line.b_income_am = bool(data[f])
        else:
            try:
                setattr(line, f, Decimal(str(data[f] or 0)))
            except Exception:
                raise PayrollError(f"Ugyldigt beløb i {f}.") from None
    line.calculated = False
    line.save()
    run.status = "draft"
    run.save(update_fields=["status", "updated_at"])
    return line


@transaction.atomic
def approve_run(run, user_label):
    run = PayrollRun.objects.select_for_update().get(pk=run.pk)
    if run.status != "calculated":
        raise PayrollError("Lønkørslen skal være beregnet, før den kan godkendes.")
    if run.lines.filter(calculated=False).exists():
        raise PayrollError("Alle linjer skal være beregnet.")
    run.status = "approved"
    run.approved_by = user_label
    run.approved_at = timezone.now()
    run.save()
    return run


@transaction.atomic
def reopen_run(run):
    run = PayrollRun.objects.select_for_update().get(pk=run.pk)
    if run.status != "approved":
        raise PayrollError("Kun en godkendt, ikke bogført lønkørsel kan genåbnes.")
    run.status = "calculated"
    run.approved_by = ""
    run.approved_at = None
    run.save()
    return run


# ─── Bogføring ────────────────────────────────────────────────────────────────

POSTING_ACCOUNTS = {
    "DK_SALARIES": "Lønninger",
    "DK_HOLIDAY_PAY_EXPENSE": "Feriepenge og ferietillæg",
    "DK_PENSION_EXPENSE": "Pension (arbejdsgiver)",
    "DK_ATP_EXPENSE": "ATP (arbejdsgiver)",
    "DK_SALARY_REFUNDS": "Lønrefusioner",
    "DK_SALARIES_PAYABLE": "Skyldig løn",
    "DK_A_TAX_PAYABLE": "Skyldig A-skat",
    "DK_AM_PAYABLE": "Skyldigt AM-bidrag",
    "DK_ATP_PAYABLE": "Skyldig ATP",
    "DK_PENSION_PAYABLE": "Skyldig pension",
    "DK_HOLIDAY_PAY_PAYABLE": "Skyldige feriepenge",
    "DK_OTHER_PAYROLL_PAYABLE": "Andre lønrelaterede poster",
}


def posting_lines(run):
    """Konteringen af en lønkørsel som liste af (konstantnavn, debet, kredit, tekst).

    Personalegoder (fri bil, telefon) er ikke en udgift i lønkørslen – udgiften er
    allerede bogført på bil/telefon; goderne påvirker kun AM-bidrag og A-skat.
    Sygedagpengerefusion: tilgodehavende hos kommunen (DR) mod lønrefusioner (CR).
    """
    s = run.lines.aggregate(**{f: models.Sum(f) for f in (
        "base_salary", "supplements", "a_income_no_am", "b_income", "holiday_allowance_paid",
        "holiday_allowance_accrued", "holiday_pay_accrued", "holiday_payout", "pension_employee",
        "pension_employer", "atp_employee", "atp_employer", "am_contribution", "a_tax", "net_pay",
        "sick_pay_refund")})
    s = {k: v or Z for k, v in s.items()}
    lbl = run.label
    rows = [
        ("DK_SALARIES", s["base_salary"] + s["supplements"] + s["a_income_no_am"] + s["b_income"], Z,
         f"Lønninger {lbl}"),
        ("DK_HOLIDAY_PAY_EXPENSE",
         s["holiday_allowance_paid"] + s["holiday_allowance_accrued"] + s["holiday_pay_accrued"], Z,
         f"Feriepenge/ferietillæg {lbl}"),
        ("DK_HOLIDAY_PAY_PAYABLE", s["holiday_payout"], Z, f"Udbetalte feriepenge {lbl}"),
        ("DK_PENSION_EXPENSE", s["pension_employer"], Z, f"Pension, arbejdsgiver {lbl}"),
        ("DK_ATP_EXPENSE", s["atp_employer"], Z, f"ATP, arbejdsgiver {lbl}"),
        ("DK_OTHER_PAYROLL_PAYABLE", s["sick_pay_refund"], Z, f"Sygedagpengerefusion til gode {lbl}"),
        ("DK_SALARIES_PAYABLE", Z, s["net_pay"], f"Nettoløn {lbl}"),
        ("DK_A_TAX_PAYABLE", Z, s["a_tax"], f"A-skat {lbl}"),
        ("DK_AM_PAYABLE", Z, s["am_contribution"], f"AM-bidrag {lbl}"),
        ("DK_ATP_PAYABLE", Z, s["atp_employee"] + s["atp_employer"], f"ATP {lbl}"),
        ("DK_PENSION_PAYABLE", Z, s["pension_employee"] + s["pension_employer"], f"Pension {lbl}"),
        ("DK_HOLIDAY_PAY_PAYABLE", Z, s["holiday_allowance_accrued"] + s["holiday_pay_accrued"],
         f"Hensatte feriepenge {lbl}"),
        ("DK_SALARY_REFUNDS", Z, s["sick_pay_refund"], f"Sygedagpengerefusion {lbl}"),
    ]
    out = []
    for const, dr, cr, text in rows:
        amount = dr - cr
        if amount == 0:
            continue
        # Negativt beløb (fx negativ nettoløn) bogføres på modsat side.
        out.append((const, amount if amount > 0 else Z, -amount if amount < 0 else Z, text))
    return out


def resolve_accounts(names):
    codes = OrderedDict((n, getattr(chart, n)) for n in names)
    found = {a.code: a for a in Account.objects.filter(code__in=codes.values())}
    missing = [f"{codes[n]} ({POSTING_ACCOUNTS.get(n, n)})" for n in codes if codes[n] not in found]
    if missing:
        raise PayrollError("Konti mangler i kontoplanen: " + ", ".join(missing))
    return {n: found[codes[n]] for n in codes}


@transaction.atomic
def post_run(run, user_label):
    """Bogfør en godkendt lønkørsel i lønjournalen (source "payroll")."""
    from journals.models import JournalEntry, JournalEntryLine
    from journals.numbering import next_je_number
    from journals.periods import closed_period_error

    run = PayrollRun.objects.select_for_update().get(pk=run.pk)
    if run.status != "approved":
        raise PayrollError("Kun en godkendt lønkørsel kan bogføres.")
    err = closed_period_error(run.pay_date)
    if err:
        raise PayrollError(err)
    rows = posting_lines(run)
    if not rows:
        raise PayrollError("Lønkørslen har ingen beløb at bogføre.")
    total_dr = sum(r[1] for r in rows)
    total_cr = sum(r[2] for r in rows)
    if total_dr != total_cr:
        raise PayrollError(f"Konteringen balancerer ikke ({total_dr} ≠ {total_cr}).")
    accounts = resolve_accounts([r[0] for r in rows])
    currency = getattr(chart, "BASE_CURRENCY", "DKK")
    entry = JournalEntry.objects.create(
        entry_number=next_je_number(), date=run.pay_date, description=f"Løn {run.label}",
        reference=f"LØN-{run.label}", piece_number=f"LØN-{run.label}", source="payroll",
        source_id=str(run.id), is_posted=True, created_by=user_label,
    )
    for const, dr, cr, text in rows:
        JournalEntryLine.objects.create(journal_entry=entry, account=accounts[const], debit=dr, credit=cr,
                                        currency=currency, description=text)
    run.status = "posted"
    run.journal_entry = entry
    run.save()
    return run, entry
