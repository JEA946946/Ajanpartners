"""Closed-period enforcement.

Every endpoint that writes or removes ledger data must refuse dates that fall
inside a closed month (journals.models.Period) or a closed fiscal year
(accounts.models.FiscalYear with is_closed=True). Every entry of a closed month
is validated, so this check also keeps validated entries untouched.
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
    """Message if the date falls in a closed fiscal year, else None.

    Accepts date or ISO string; None date → None (caller validates elsewhere).
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
        return f"Date {d.isoformat()} falls in closed fiscal year '{fy.name}'. Closed years cannot be changed."
    if Period.objects.filter(year=d.year, month=d.month).exists():
        return (f"{d.year}-{d.month:02d} is closed and its entries are validated. "
                "Correct with a reversal entry in an open month.")
    return None
