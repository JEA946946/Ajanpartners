"""Satser til dansk løn pr. indkomstår.

Årlig opdatering er kun data: kopiér det seneste år, ret beløbene og angiv kilden.
Satser, der ikke er efterprøvet mod en primærkilde, er markeret med TODO.

Kilder:
- AM-bidrag: arbejdsmarkedsbidragsloven § 1 (8 %).
- ATP: virk.dk "Gældende satser for ATP-bidrag" og borger.dk "ATP-satser for 2026 i
  privat virksomhed" (A-sats måned: 99,00 / 198,00 / 297,00 kr. ved mindst 117 timer).
- Ferie: ferieloven (lov nr. 60 af 30/1/2018), § 16 (feriepenge 12,5 %) og § 17
  (ferietillæg 1 %).
- Fri telefon/multimedier: ligningslovens § 16, stk. 12 – 3.300 kr. (2025) og
  3.500 kr. (2026) jf. Danske Erhverv / DI "Satser for beskatning af personalegoder".
- Bruttotræk 55 % uden skattekort/efter opbrugt frikort: kildeskattelovens § 48, stk. 7.
"""

from decimal import ROUND_DOWN, ROUND_HALF_UP, Decimal

D = Decimal

# ATP-tabel: (mindste antal timer i perioden, lønmodtagerandel, arbejdsgiverandel).
# Første række, hvis timetal opfyldes, vinder. Under laveste grænse: intet bidrag.
_ATP_A_2025 = {
    "month": [
        (D("117"), D("99.00"), D("198.00")),
        (D("78"), D("66.00"), D("132.00")),
        (D("39"), D("33.00"), D("66.00")),
    ],
    # TODO(kilde: virk.dk ATP-satser, 14-dages løn): beløbene er afledt af månedssatsen
    # og bør efterprøves mod tabellen for 14-dageslønnede.
    "fortnight": [
        (D("54"), D("45.70"), D("91.40")),
        (D("36"), D("30.47"), D("60.93")),
        (D("18"), D("15.23"), D("30.47")),
    ],
}

RATES = {
    2025: {
        "am_rate": D("0.08"),
        "atp": {"A": _ATP_A_2025},
        "holiday_pay_rate": D("0.125"),        # feriepenge, ferie uden løn
        "holiday_allowance_rate": D("0.01"),   # ferietillæg, ferie med løn
        "no_card_rate": D("0.55"),             # bruttotræk uden skattekort
        "frikort_excess_rate": D("0.55"),      # TODO(kilde: skat.dk "Frikort"): træk når frikortet er opbrugt
        "free_phone_year": D("3300"),          # fri telefon/multimedier pr. år
        "a_tax_rounding": (D("1"), ROUND_DOWN),       # TODO(kilde: kildeskattebekendtgørelsen): hele kr. nedad
        "am_rounding": (D("0.01"), ROUND_HALF_UP),    # øre
    },
    2026: {
        "am_rate": D("0.08"),
        # ATP 2026 uændret: 99,00 / 198,00 kr. (borger.dk, ATP-satser for 2026).
        "atp": {"A": _ATP_A_2025},
        "holiday_pay_rate": D("0.125"),
        "holiday_allowance_rate": D("0.01"),
        "no_card_rate": D("0.55"),
        "frikort_excess_rate": D("0.55"),      # TODO(kilde: skat.dk "Frikort")
        "free_phone_year": D("3500"),
        "a_tax_rounding": (D("1"), ROUND_DOWN),       # TODO(kilde: kildeskattebekendtgørelsen)
        "am_rounding": (D("0.01"), ROUND_HALF_UP),
    },
}

# Andre ATP-satser (B–F, bl.a. offentlige arbejdsgivere og særlige grupper) er ikke lagt ind.
# TODO(kilde: virk.dk ATP-satser B–F): tilføj dem under "atp" pr. år, når de skal bruges.
ATP_CLASSES = [
    ("A", "A-sats (standard, efter timer)"),
    ("B", "B-sats"),
    ("C", "C-sats"),
    ("D", "D-sats"),
    ("E", "E-sats"),
    ("F", "F-sats"),
    ("0", "Ingen ATP"),
]


class MissingRate(ValueError):
    pass


def rates_for(year):
    try:
        return RATES[int(year)]
    except KeyError:
        raise MissingRate(f"Der er ingen lønsatser for {year} i payroll/rates.py.") from None


def atp_amounts(year, frequency, hours, atp_class="A"):
    """(lønmodtagerandel, arbejdsgiverandel) for perioden."""
    if atp_class == "0":
        return D("0"), D("0")
    table = rates_for(year)["atp"].get(atp_class)
    if table is None:
        raise MissingRate(f"ATP-sats {atp_class} for {year} er ikke lagt ind i payroll/rates.py.")
    hours = D(hours or 0)
    for min_hours, employee, employer in table[frequency]:
        if hours >= min_hours:
            return employee, employer
    return D("0"), D("0")
