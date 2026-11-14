"""Dansk lønberegning – rene funktioner (ingen database).

Rækkefølge for én medarbejder i én lønperiode:

    kontant løn (grundløn + tillæg + udbetalt ferietillæg/feriepenge)
  + skattepligtige personalegoder (fri bil, fri telefon, andre goder)
  − ATP, lønmodtagerandel
  − eget pensionsbidrag (arbejdsgiveradministreret, AM-bidragsfrit)
  = AM-grundlag
  − AM-bidrag 8 %
  + A-indkomst uden AM-bidrag
  = skattegrundlag
  A-skat = trækprocent × (skattegrundlag − fradrag)   [hovedkort]
         = trækprocent × skattegrundlag               [bikort]
         = 55 % af det, der overstiger restfrikortet  [frikort]
         = 55 % × skattegrundlag                      [intet skattekort]
  Nettoløn = kontant løn + A-indkomst uden AM + B-indkomst − ATP − pension − AM − A-skat

Ferie (ny ferielov, samtidighedsferie fra 1/9-2020):
- Ferie med løn: lønnen fortsætter under ferien; ferietillæg 1 % af den
  ferieberettigede løn, enten udbetalt løbende med lønnen eller hensat.
- Ferie uden løn (FerieKonto eller egen ordning): feriepenge 12,5 % af den
  ferieberettigede løn hensættes og udbetales, når ferien holdes.
Ferieberettiget løn er her grundløn + tillæg (ikke personalegoder, ikke
arbejdsgiverens pensionsbidrag, ikke ferietillæg og feriepenge).
"""

from dataclasses import asdict, dataclass, field
from decimal import ROUND_HALF_UP, Decimal

from .rates import atp_amounts, rates_for

ZERO = Decimal("0")
ORE = Decimal("0.01")

CARD_MAIN = "main"
CARD_SECONDARY = "secondary"
CARD_FREE = "free"
CARD_NONE = "none"


def ore(value):
    """Afrund til øre (halvt op)."""
    return Decimal(value).quantize(ORE, ROUND_HALF_UP)


def _q(value, rule):
    step, mode = rule
    return Decimal(value).quantize(step, mode)


def pct(value):
    """Procent (fx 37,5) som brøk (0,375)."""
    return Decimal(value or 0) / Decimal("100")


def free_phone_month(year):
    """Månedsværdi af fri telefon/multimedier (årsbeløb / 12, øre)."""
    return ore(rates_for(year)["free_phone_year"] / 12)


def fortnight_deduction(month_deduction):
    """14-dagesfradrag ud fra månedsfradraget, når eSkattekortet ikke har det: × 12/26."""
    return (Decimal(month_deduction or 0) * 12 / 26).quantize(Decimal("1"), ROUND_HALF_UP)


@dataclass
class TaxCard:
    card_type: str = CARD_MAIN
    rate: Decimal = ZERO             # trækprocent, fx Decimal("37")
    deduction: Decimal = ZERO        # fradrag for perioden (hovedkort)
    free_remaining: Decimal = ZERO   # resterende frikortbeløb i året


@dataclass
class PayInput:
    year: int
    frequency: str = "month"             # month | fortnight
    base_salary: Decimal = ZERO          # grundløn (eller timer × timeløn)
    supplements: Decimal = ZERO          # tillæg, overtid (ferieberettiget)
    holiday_payout: Decimal = ZERO       # udbetaling af hensatte feriepenge/ferietillæg
    a_income_no_am: Decimal = ZERO       # A-indkomst uden AM-bidrag
    car_benefit: Decimal = ZERO          # fri bil, skattepligtig værdi for perioden
    phone_benefit: Decimal = ZERO        # fri telefon/multimedier for perioden
    other_benefits: Decimal = ZERO       # andre skattepligtige goder
    b_income: Decimal = ZERO             # B-indkomst (ingen tilbageholdelse)
    hours: Decimal = ZERO                # ATP-timer i perioden
    atp_class: str = "A"
    pension_employee_pct: Decimal = ZERO
    pension_employer_pct: Decimal = ZERO
    holiday_type: str = "with_pay"       # with_pay | without_pay
    holiday_allowance_pct: Decimal | None = None   # None → lovens 1 %
    holiday_allowance_mode: str = "monthly"        # monthly (udbetales) | accrue (hensættes)
    sick_pay_refund: Decimal = ZERO      # sygedagpengerefusion (manuel)
    tax_card: TaxCard = field(default_factory=TaxCard)


@dataclass
class PayResult:
    holiday_base: Decimal
    holiday_allowance_paid: Decimal
    holiday_allowance_accrued: Decimal
    holiday_pay_accrued: Decimal
    gross_cash: Decimal          # kontant AM-pligtig løn
    benefits: Decimal
    atp_employee: Decimal
    atp_employer: Decimal
    pension_employee: Decimal
    pension_employer: Decimal
    am_base: Decimal
    am_contribution: Decimal
    tax_base: Decimal
    deduction_used: Decimal
    frikort_used: Decimal
    a_tax: Decimal
    b_income: Decimal
    a_income_no_am: Decimal
    sick_pay_refund: Decimal
    net_pay: Decimal
    employer_cost: Decimal
    warnings: list

    def as_dict(self):
        return asdict(self)


def calculate_a_tax(year, tax_base, card):
    """(A-skat, brugt fradrag, brugt frikort) af skattegrundlaget (efter AM-bidrag)."""
    r = rates_for(year)
    tax_base = max(Decimal(tax_base), ZERO)
    deduction_used = frikort_used = ZERO
    if card.card_type == CARD_MAIN:
        deduction_used = min(Decimal(card.deduction or 0), tax_base)
        tax = (tax_base - deduction_used) * pct(card.rate)
    elif card.card_type == CARD_SECONDARY:
        tax = tax_base * pct(card.rate)            # bikort: ingen fradrag
    elif card.card_type == CARD_FREE:
        frikort_used = min(max(Decimal(card.free_remaining or 0), ZERO), tax_base)
        tax = (tax_base - frikort_used) * r["frikort_excess_rate"]
    elif card.card_type == CARD_NONE:
        tax = tax_base * r["no_card_rate"]
    else:
        raise ValueError(f"Ukendt skattekort: {card.card_type}")
    return _q(tax, r["a_tax_rounding"]), deduction_used, frikort_used


def calculate_pay(inp: PayInput) -> PayResult:
    r = rates_for(inp.year)
    D = Decimal
    base = ore(inp.base_salary or 0)
    supplements = ore(inp.supplements or 0)
    holiday_base = base + supplements
    warnings = []

    # Ferie
    allowance_paid = allowance_accrued = holiday_pay = ZERO
    if inp.holiday_type == "with_pay":
        rate = pct(inp.holiday_allowance_pct) if inp.holiday_allowance_pct is not None \
            else r["holiday_allowance_rate"]
        allowance = ore(holiday_base * rate)
        if inp.holiday_allowance_mode == "accrue":
            allowance_accrued = allowance
        else:
            allowance_paid = allowance
    elif inp.holiday_type == "without_pay":
        holiday_pay = ore(holiday_base * r["holiday_pay_rate"])
    else:
        raise ValueError(f"Ukendt ferietype: {inp.holiday_type}")

    # Pension af den ferieberettigede løn
    pension_employee = ore(holiday_base * pct(inp.pension_employee_pct))
    pension_employer = ore(holiday_base * pct(inp.pension_employer_pct))

    gross_cash = holiday_base + allowance_paid + ore(inp.holiday_payout or 0)
    benefits = ore(inp.car_benefit or 0) + ore(inp.phone_benefit or 0) + ore(inp.other_benefits or 0)

    # ATP – ingen løn i perioden, intet bidrag
    if gross_cash + benefits > 0:
        atp_employee, atp_employer = atp_amounts(inp.year, inp.frequency, inp.hours, inp.atp_class)
    else:
        atp_employee = atp_employer = ZERO

    am_base = gross_cash + benefits - atp_employee - pension_employee
    if am_base < 0:
        warnings.append("ATP og pension overstiger lønnen; AM-grundlaget er sat til 0.")
        am_base = ZERO
    am = _q(am_base * r["am_rate"], r["am_rounding"])

    a_no_am = ore(inp.a_income_no_am or 0)
    tax_base = am_base - am + a_no_am
    a_tax, deduction_used, frikort_used = calculate_a_tax(inp.year, tax_base, inp.tax_card)

    b_income = ore(inp.b_income or 0)
    net = gross_cash + a_no_am + b_income - atp_employee - pension_employee - am - a_tax
    if net < 0:
        warnings.append("Nettolønnen er negativ (personalegoder større end kontant løn).")

    employer_cost = (gross_cash + a_no_am + b_income + allowance_accrued + holiday_pay
                     + atp_employer + pension_employer)
    return PayResult(
        holiday_base=holiday_base, holiday_allowance_paid=allowance_paid,
        holiday_allowance_accrued=allowance_accrued, holiday_pay_accrued=holiday_pay,
        gross_cash=gross_cash, benefits=benefits,
        atp_employee=D(atp_employee), atp_employer=D(atp_employer),
        pension_employee=pension_employee, pension_employer=pension_employer,
        am_base=am_base, am_contribution=am, tax_base=max(tax_base, ZERO),
        deduction_used=deduction_used, frikort_used=frikort_used, a_tax=a_tax,
        b_income=b_income, a_income_no_am=a_no_am, sick_pay_refund=ore(inp.sick_pay_refund or 0),
        net_pay=net, employer_cost=employer_cost, warnings=warnings,
    )


def holiday_days_earned(months, days_per_month=Decimal("2.08")):
    """Samtidighedsferie: 2,08 feriedage pr. ansættelsesmåned (ferielovens § 5), højst 25 pr. år."""
    return min(Decimal(months) * days_per_month, Decimal("25"))
