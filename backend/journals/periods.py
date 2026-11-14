"""Lukkede perioder.

Alle endpoints, der skriver eller sletter i bøgerne, skal afvise datoer i en
lukket måned (journals.models.Period), et afsluttet regnskabsår
(accounts.models.FiscalYear.is_closed) eller en angivet momsperiode
(core.models.VatReturn med status "filed"). Alle posteringer i en lukket måned
er validerede, så tjekket holder også validerede posteringer uændrede.
"""

from datetime import date, datetime


def _to_date(value):
    """Coerce a date/datetime/ISO-string to a date, or None if unparseable."""
    if value is None:
        return None
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    try:
        return date.fromisoformat(str(value).strip().split("T")[0])
    except (ValueError, TypeError):
        return None


def closed_period_error(entry_date):
    """Fejltekst, hvis datoen ligger i en lukket periode, ellers None.

    Tager en dato eller ISO-tekst; None → None (kalderen validerer selv).
    """
    d = _to_date(entry_date)
    if d is None:
        return None
    # Lazy import: avoid app-load ordering issues between journals and accounts.
    from accounts.models import FiscalYear
    from journals.models import Period
    fy = FiscalYear.objects.filter(
        is_closed=True, start_date__lte=d, end_date__gte=d,
    ).first()
    if fy:
        return f"{d.isoformat()} ligger i det afsluttede regnskabsår {fy.name}, som ikke kan ændres."
    if Period.objects.filter(year=d.year, month=d.month).exists():
        return (f"{d.year}-{d.month:02d} er lukket, og dens posteringer er validerede. "
                "Ret med en tilbageføring i en åben måned.")
    from core.models import VatReturn
    vr = VatReturn.objects.filter(status="filed", period_start__lte=d, period_end__gte=d).first()
    if vr:
        return (f"Momsperioden {vr.period_start.isoformat()}–{vr.period_end.isoformat()} er angivet og låst. "
                "Ret i en åben periode (og ret angivelsen hos Skat).")
    return None
