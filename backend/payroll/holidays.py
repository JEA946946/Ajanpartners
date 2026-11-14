"""Danske helligdage, beregnet ud fra påsken.

Store bededag er afskaffet som helligdag fra og med 2024 (lov nr. 151 af 28/2/2023).
Grundlovsdag (5. juni) er ikke en officiel helligdag, men fri hel eller halv dag i
mange overenskomster; derfor kan den slås til som "half" eller "full".
"""

from datetime import date, timedelta
from decimal import Decimal

GRUNDLOVSDAG_MODES = ("none", "half", "full")


def easter_sunday(year):
    """Påskedag (gregoriansk kalender, anonym algoritme / Meeus-Jones-Butcher)."""
    a = year % 19
    b, c = divmod(year, 100)
    d, e = divmod(b, 4)
    f = (b + 8) // 25
    g = (b - f + 1) // 3
    h = (19 * a + b - d - g + 15) % 30
    i, k = divmod(c, 4)
    l = (32 + 2 * e + 2 * i - h - k) % 7
    m = (a + 11 * h + 22 * l) // 451
    month, day = divmod(h + l - 7 * m + 114, 31)
    return date(year, month, day + 1)


def danish_holidays(year, grundlovsdag="half"):
    """Liste af (dato, navn, andel af en dag) sorteret efter dato."""
    if grundlovsdag not in GRUNDLOVSDAG_MODES:
        raise ValueError("grundlovsdag skal være none, half eller full")
    e = easter_sunday(year)
    one = Decimal("1")
    days = [
        (date(year, 1, 1), "Nytårsdag", one),
        (e - timedelta(days=3), "Skærtorsdag", one),
        (e - timedelta(days=2), "Langfredag", one),
        (e, "Påskedag", one),
        (e + timedelta(days=1), "2. påskedag", one),
        (e + timedelta(days=39), "Kristi himmelfartsdag", one),
        (e + timedelta(days=49), "Pinsedag", one),
        (e + timedelta(days=50), "2. pinsedag", one),
        (date(year, 12, 25), "Juledag", one),
        (date(year, 12, 26), "2. juledag", one),
    ]
    if year < 2024:
        days.append((e + timedelta(days=26), "Store bededag", one))
    if grundlovsdag != "none":
        days.append((date(year, 6, 5), "Grundlovsdag",
                     one if grundlovsdag == "full" else Decimal("0.5")))
    return sorted(days)


def working_days(year, month, grundlovsdag="half"):
    """Arbejdsdage (man–fre) i måneden fratrukket helligdage på hverdage."""
    d = date(year, month, 1)
    holidays = {h: share for h, _, share in danish_holidays(year, grundlovsdag)}
    total = Decimal("0")
    while d.month == month:
        if d.weekday() < 5:
            total += Decimal("1") - holidays.get(d, Decimal("0"))
        d += timedelta(days=1)
    return total
