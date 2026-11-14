"""Fristkalender: beregnede frister pr. kunde (rene funktioner, ingen database).

Reglerne er de almindelige frister fra Skat og Erhvervsstyrelsen. De er
bevidst enkle og skal tjekkes, når Skat ændrer kalenderen. Usikre regler er
markeret med TODO.

Forskydning:
- Moms og A-skat/AM betales via banken. Falder fristen på en lørdag, søndag,
  helligdag eller dag, hvor bankerne holder lukket (grundlovsdag, juleaftensdag,
  nytårsaftensdag, fredag efter Kristi himmelfartsdag), rykkes den til
  førstkommende bankdag.
- Årsrapport og selvangivelse: rykkes til førstkommende hverdag (ikke lørdag,
  søndag eller helligdag).
"""

from dataclasses import dataclass, field
from datetime import date, timedelta
import calendar

PERSONAL_FORMS = {"enk", "pmv", "is"}  # personligt ejede virksomheder (ikke selvstændige skattesubjekter)
COMPANY_FORMS = {"aps", "as", "ivs", "holding"}  # selskabsskattepligtige
MONTHS_DA = ["januar", "februar", "marts", "april", "maj", "juni", "juli", "august",
             "september", "oktober", "november", "december"]


# ─── Kalender ─────────────────────────────────────────────────────────────────

def easter(year):
    """Påskedag (gregoriansk, Meeus/Jones/Butcher)."""
    a = year % 19
    b, c = divmod(year, 100)
    d, e = divmod(b, 4)
    f = (b + 8) // 25
    g = (b - f + 1) // 3
    h = (19 * a + b - d - g + 15) % 30
    i, k = divmod(c, 4)
    l_ = (32 + 2 * e + 2 * i - h - k) % 7
    m = (a + 11 * h + 22 * l_) // 451
    month = (h + l_ - 7 * m + 114) // 31
    day = (h + l_ - 7 * m + 114) % 31 + 1
    return date(year, month, day)


def public_holidays(year):
    """Danske helligdage (lovbestemte)."""
    e = easter(year)
    days = {
        date(year, 1, 1),            # nytårsdag
        e - timedelta(days=3),       # skærtorsdag
        e - timedelta(days=2),       # langfredag
        e,                           # påskedag
        e + timedelta(days=1),       # 2. påskedag
        e + timedelta(days=39),      # Kristi himmelfartsdag
        e + timedelta(days=49),      # pinsedag
        e + timedelta(days=50),      # 2. pinsedag
        date(year, 12, 25), date(year, 12, 26),
    }
    if year <= 2023:
        days.add(e + timedelta(days=26))  # store bededag (afskaffet fra 2024)
    return days


def bank_holidays(year):
    """Dage uden bankdrift ud over helligdagene."""
    e = easter(year)
    return public_holidays(year) | {
        date(year, 6, 5),            # grundlovsdag
        e + timedelta(days=40),      # fredag efter Kristi himmelfartsdag
        date(year, 12, 24), date(year, 12, 31),
    }


def is_weekday(d):
    return d.weekday() < 5 and d not in public_holidays(d.year)


def is_bank_day(d):
    return d.weekday() < 5 and d not in bank_holidays(d.year)


def next_weekday(d):
    while not is_weekday(d):
        d += timedelta(days=1)
    return d


def next_bank_day(d):
    while not is_bank_day(d):
        d += timedelta(days=1)
    return d


def last_bank_day(year, month):
    d = date(year, month, calendar.monthrange(year, month)[1])
    while not is_bank_day(d):
        d -= timedelta(days=1)
    return d


def add_months(year, month, n):
    """(år, måned) + n måneder."""
    idx = year * 12 + (month - 1) + n
    return idx // 12, idx % 12 + 1


def month_end(year, month):
    return date(year, month, calendar.monthrange(year, month)[1])


# ─── Kunde og frist ───────────────────────────────────────────────────────────

@dataclass(frozen=True)
class Profile:
    vat_period: str = "quarter"          # none | month | quarter | half
    fiscal_year_start_month: int = 1
    accounting_class: str = "B"          # A | B | C | D
    legal_form: str = "aps"
    has_payroll: bool = True


@dataclass(frozen=True)
class Deadline:
    date: date            # gældende frist (efter forskydning)
    due: date             # frist efter reglen (før forskydning)
    kind: str             # moms | a_skat | aarsrapport | selvangivelse | oplysningsskema | acontoskat
    title: str
    period: str           # fx "3. kvartal 2026"
    authority: str        # Skat | Erhvervsstyrelsen
    note: str = ""
    period_start: date = field(default=None)
    period_end: date = field(default=None)

    @property
    def shifted(self):
        return self.date != self.due


def fiscal_year_end(start_month, year):
    """Slutdato for regnskabsåret, der slutter i kalenderåret `year`."""
    end_month = 12 if start_month == 1 else start_month - 1
    return month_end(year, end_month)


def fiscal_year_start(start_month, end):
    y, m = add_months(end.year, end.month, -11)
    return date(y, m, 1)


# ─── Moms ─────────────────────────────────────────────────────────────────────

def vat_due(period, year, index):
    """Frist (før forskydning) for momsperioden.
    month: index 1-12, quarter: 1-4, half: 1-2."""
    if period == "month":
        if index == 6:
            # Juni har sommerfrist: 17. august (Skat). TODO: tjek hvert år i Skats momskalender.
            return date(year, 8, 17)
        y, m = add_months(year, index, 1)
        return date(y, m, 25)
    if period == "quarter":
        # Den 1. i den 3. måned efter kvartalets udløb: 1. juni, 1. sep., 1. dec., 1. marts.
        y, m = add_months(year, index * 3, 3)
        return date(y, m, 1)
    if period == "half":
        return date(year, 9, 1) if index == 1 else date(year + 1, 3, 1)
    raise ValueError(period)


def vat_periods(period, year):
    """[(index, start, slut, etiket)] for året."""
    if period == "month":
        return [(m, date(year, m, 1), month_end(year, m), f"{MONTHS_DA[m - 1]} {year}") for m in range(1, 13)]
    if period == "quarter":
        return [(q, date(year, q * 3 - 2, 1), month_end(year, q * 3), f"{q}. kvartal {year}") for q in range(1, 5)]
    if period == "half":
        return [(1, date(year, 1, 1), date(year, 6, 30), f"1. halvår {year}"),
                (2, date(year, 7, 1), date(year, 12, 31), f"2. halvår {year}")]
    return []


def vat_deadlines(profile, year):
    out = []
    for index, start, end, label in vat_periods(profile.vat_period, year):
        due = vat_due(profile.vat_period, year, index)
        out.append(Deadline(next_bank_day(due), due, "moms", "Momsangivelse og betaling", label, "Skat",
                            period_start=start, period_end=end))
    return out


# ─── A-skat og AM-bidrag (eIndkomst) ──────────────────────────────────────────

def a_tax_due(year, month):
    """Små og mellemstore virksomheder: den 10. i måneden efter lønmåneden;
    for december den 17. januar."""
    if month == 12:
        # TODO: Skat har tidligere haft 17. januar for december – tjek årets kalender.
        return date(year + 1, 1, 17)
    y, m = add_months(year, month, 1)
    return date(y, m, 10)


def a_tax_deadlines(profile, year):
    if not profile.has_payroll:
        return []
    note = ("Små og mellemstore virksomheder. Store virksomheder (A-skat og AM over 1 mio. kr. om året) "
            "har frist den sidste bankdag i lønmåneden.")
    out = []
    for m in range(1, 13):
        due = a_tax_due(year, m)
        out.append(Deadline(next_bank_day(due), due, "a_skat", "A-skat og AM-bidrag (eIndkomst)",
                            f"{MONTHS_DA[m - 1]} {year}", "Skat", note,
                            period_start=date(year, m, 1), period_end=month_end(year, m)))
    return out


# ─── Årsrapport og selvangivelse ──────────────────────────────────────────────

ANNUAL_REPORT_MONTHS = {"B": 5, "C": 4, "D": 4}


def annual_report_due(year_end, accounting_class):
    """Klasse B: 5 måneder efter regnskabsårets udløb; klasse C og D: 4 måneder.
    Slutter året den sidste i måneden, er fristen også den sidste i måneden."""
    months = ANNUAL_REPORT_MONTHS[accounting_class]
    y, m = add_months(year_end.year, year_end.month, months)
    if year_end == month_end(year_end.year, year_end.month):
        return month_end(y, m)
    return date(y, m, min(year_end.day, calendar.monthrange(y, m)[1]))


def company_tax_return_due(year_end):
    """Selskabers selvangivelse: 6 måneder efter indkomstårets udløb.
    Slutter indkomståret mellem 1. februar og 31. marts: 1. august samme år."""
    if year_end.month in (2, 3):
        return date(year_end.year, 8, 1)
    y, m = add_months(year_end.year, year_end.month, 6)
    return month_end(y, m)


def annual_deadlines(profile, year):
    """Frister for regnskabsåret, der slutter i kalenderåret `year`."""
    end = fiscal_year_end(profile.fiscal_year_start_month, year)
    start = fiscal_year_start(profile.fiscal_year_start_month, end)
    label = f"{start.year}" if start.year == end.year else f"{start.year}/{str(end.year)[2:]}"
    out = []
    personal = profile.legal_form in PERSONAL_FORMS
    cls = (profile.accounting_class or "B").upper()
    if cls in ANNUAL_REPORT_MONTHS and not personal:
        due = annual_report_due(end, cls)
        out.append(Deadline(next_weekday(due), due, "aarsrapport", f"Årsrapport (klasse {cls}) til Erhvervsstyrelsen",
                            f"Regnskabsår {label}", "Erhvervsstyrelsen", period_start=start, period_end=end))
    if personal:
        # Personligt ejet virksomhed: ingen årsrapport, ejerens oplysningsskema.
        # TODO: forskudt indkomstår for personer – her bruges året efter regnskabsårets udløb.
        due = date(end.year + 1, 7, 1)
        out.append(Deadline(next_weekday(due), due, "oplysningsskema",
                            "Oplysningsskema (selvangivelse) for ejeren",
                            f"Indkomstår {label}", "Skat",
                            "Personligt ejet virksomhed uden pligt til årsrapport.",
                            period_start=start, period_end=end))
    elif profile.legal_form in COMPANY_FORMS:
        due = company_tax_return_due(end)
        out.append(Deadline(next_weekday(due), due, "selvangivelse", "Selvangivelse for selskab",
                            f"Indkomstår {label}", "Skat", period_start=start, period_end=end))
    return out


def aconto_deadlines(profile, year):
    """Acontoskat for selskaber: 20. marts og 20. november i skatteåret.
    TODO: frivillig 3. rate (20. december) og selskaber uden acontoskat (underskud) håndteres ikke."""
    if profile.legal_form not in COMPANY_FORMS:
        return []
    out = []
    for n, d in ((1, date(year, 3, 20)), (2, date(year, 11, 20))):
        out.append(Deadline(next_bank_day(d), d, "acontoskat", f"Acontoskat, {n}. rate", f"Skatteår {year}", "Skat"))
    return out


# ─── Samlet ───────────────────────────────────────────────────────────────────

def deadlines_for(profile, start, end):
    """Alle frister med gældende dato i [start, end], sorteret efter dato."""
    out = []
    # Perioder fra året før: fx 4. kvartal betales i marts, årsrapporten 5 mdr. efter.
    for year in range(start.year - 2, end.year + 1):
        if profile.vat_period in ("month", "quarter", "half"):
            out += vat_deadlines(profile, year)
        out += a_tax_deadlines(profile, year)
        out += annual_deadlines(profile, year)
        out += aconto_deadlines(profile, year)
    return sorted((d for d in out if start <= d.date <= end), key=lambda d: (d.date, d.kind))


def next_deadline(profile, today):
    items = deadlines_for(profile, today, today + timedelta(days=400))
    return items[0] if items else None


def profile_of(client, has_payroll=None):
    """Profil fra en tenancy.ClientCompany."""
    if has_payroll is None:
        # TODO: et felt "har ansatte" på kunden. Indtil da: kunder med lønmodulet.
        has_payroll = client.has_feature("payroll")
    return Profile(vat_period=client.vat_period, fiscal_year_start_month=client.fiscal_year_start_month or 1,
                   accounting_class=client.accounting_class or "B", legal_form=client.legal_form,
                   has_payroll=has_payroll)


def deadline_dict(d):
    return {"date": d.date.isoformat(), "due": d.due.isoformat(), "shifted": d.shifted, "kind": d.kind,
            "title": d.title, "period": d.period, "authority": d.authority, "note": d.note,
            "period_start": d.period_start.isoformat() if d.period_start else None,
            "period_end": d.period_end.isoformat() if d.period_end else None}
