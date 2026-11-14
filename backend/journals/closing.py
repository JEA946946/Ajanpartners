"""Month closing (clôture mensuelle).

Closing a month validates every entry dated in it: in date order, each journal's
entries get the next numbers of that journal's yearly series (BQ1-2026-00001 …),
so the numbering is chronological and without gaps. After that the entries can
never change (see journals/signals.py) and the month takes no new entries.

Months close in order. A month cannot close while it has a manual draft, an
unbalanced entry, or a bank journal without a completed reconciliation at the
month's last day. Money still on 34971 (à classer) is a warning to confirm.
"""

import calendar
from datetime import date
from decimal import Decimal

from django.db import transaction
from django.db.models import Count, Min, Q, Sum
from django.utils import timezone

from accounts import chart

from .models import Journal, JournalEntry, JournalEntryLine, Period
from .numbering import validated_number


def month_bounds(year, month):
    return date(year, month, 1), date(year, month, calendar.monthrange(year, month)[1])


def open_months_before(year, month):
    """(year, month) pairs before this one that have entries but are not closed."""
    first, _ = month_bounds(year, month)
    closed = set(Period.objects.values_list("year", "month"))
    months = set()
    for d in JournalEntry.objects.filter(date__lt=first).dates("date", "month"):
        if (d.year, d.month) not in closed:
            months.add((d.year, d.month))
    return sorted(months)


def first_open_month():
    """The earliest month with entries that is not closed, or None."""
    closed = set(Period.objects.values_list("year", "month"))
    for d in JournalEntry.objects.dates("date", "month"):
        if (d.year, d.month) not in closed:
            return d.year, d.month
    return None


def check_month(year, month):
    """What stops the month from closing (blockers) and what to confirm (warnings)."""
    first, last = month_bounds(year, month)
    blockers, warnings = [], []
    if Period.objects.filter(year=year, month=month).exists():
        blockers.append(f"{year}-{month:02d} is already closed")
        return {"blockers": blockers, "warnings": warnings}

    earlier = open_months_before(year, month)
    if earlier:
        y, m = earlier[0]
        blockers.append(f"Close {y}-{m:02d} first; months close in order")

    entries = JournalEntry.objects.filter(date__gte=first, date__lte=last)
    drafts = entries.filter(is_posted=False).count()
    if drafts:
        blockers.append(f"{drafts} draft entr{'y' if drafts == 1 else 'ies'} not posted — post or delete them")

    unbalanced = [
        e.entry_number for e in entries.filter(is_posted=True).annotate(dr=Sum("lines__debit"), cr=Sum("lines__credit"))
        if (e.dr or Decimal("0")) != (e.cr or Decimal("0"))
    ]
    if unbalanced:
        blockers.append(f"Unbalanced entries: {', '.join(unbalanced[:10])}")

    for journal in Journal.objects.filter(type="bank", account__isnull=False).select_related("account"):
        has_lines = JournalEntryLine.objects.filter(
            account=journal.account, journal_entry__is_posted=True, journal_entry__date__lte=last).exists()
        if not has_lines:
            continue
        done = journal.account.reconciliations.filter(status="completed", date=last).exists()
        if not done:
            blockers.append(f"{journal.code} ({journal.account.code}) has no completed bank reconciliation "
                            f"at {last.isoformat()}")

    suspense = (JournalEntryLine.objects
                .filter(account__code=chart.SUSPENSE, journal_entry__is_posted=True, journal_entry__date__lte=last)
                .values("currency").annotate(dr=Sum("debit"), cr=Sum("credit")))
    for s in suspense:
        bal = (s["dr"] or Decimal("0")) - (s["cr"] or Decimal("0"))
        if bal:
            warnings.append(f"{chart.SUSPENSE} (à classer) still holds {bal} {s['currency']} at {last.isoformat()}")

    # Pièces justificatives: bank lines are backed by the statement; every other
    # entry should have its document attached.
    unsupported = (entries.filter(is_posted=True).exclude(journal__type="bank")
                   .filter(documents__isnull=True).count())
    if unsupported:
        warnings.append(f"{unsupported} entr{'y has' if unsupported == 1 else 'ies have'} no document attached")

    counts = entries.aggregate(n=Count("id"), first=Min("date"))
    return {"blockers": blockers, "warnings": warnings, "entries": counts["n"]}


def close_month(year, month, closed_by, confirm_warnings=False):
    """Validate and number the month's entries and lock the month. Returns
    (period, check) — period is None when the month could not close."""
    with transaction.atomic():
        # One closing at a time: lock all periods while this runs.
        list(Period.objects.select_for_update().all())
        check = check_month(year, month)
        if check["blockers"] or (check["warnings"] and not confirm_warnings):
            return None, check
        first, last = month_bounds(year, month)
        now = timezone.now()
        entries = (JournalEntry.objects.select_for_update()
                   .filter(date__gte=first, date__lte=last, is_posted=True, validated_at__isnull=True)
                   .select_related("journal").order_by("date", "created_at", "entry_number"))
        for e in entries:
            e.entry_number = validated_number(e.journal, year)
            e.validated_at = now
            e.validated_by = closed_by
            e.save(update_fields=["entry_number", "validated_at", "validated_by", "updated_at"])
        period = Period.objects.create(year=year, month=month, closed_at=now, closed_by=closed_by)
        check["validated"] = len(entries)
        return period, check


def reverse_entry(entry, on_date, created_by):
    """Contre-passation of a validated entry: same journal, debits and credits
    swapped, dated in an open month. Returns (reversal, error)."""
    from .numbering import next_je_number
    from .periods import closed_period_error

    if not entry.validated_at:
        return None, "This entry is not validated yet — edit or delete it instead"
    done = JournalEntry.objects.filter(reversal_of=entry).first()
    if done:
        return None, f"Entry {entry.entry_number} is already reversed by {done.entry_number}"
    if on_date < entry.date:
        return None, "A reversal cannot be dated before the entry it reverses"
    err = closed_period_error(on_date)
    if err:
        return None, err
    with transaction.atomic():
        rev = JournalEntry.objects.create(
            journal=entry.journal, entry_number=next_je_number(), date=on_date,
            piece_number=entry.piece_number,
            description=f"Contre-passation de {entry.entry_number} — {entry.description}"[:2000],
            reference=entry.entry_number, source="reversal", source_id=str(entry.id),
            is_posted=True, created_by=created_by, reversal_of=entry,
        )
        for line in entry.lines.all():
            JournalEntryLine.objects.create(
                journal_entry=rev, account=line.account, debit=line.credit, credit=line.debit,
                currency=line.currency, exchange_rate=line.exchange_rate,
                description=f"Contre-passation — {line.description}"[:500],
            )
    return rev, None


def period_status(year):
    """Every month of the year with its state, for the closing page."""
    closed = {(p.year, p.month): p for p in Period.objects.filter(year=year)}
    out = []
    for month in range(1, 13):
        first, last = month_bounds(year, month)
        p = closed.get((year, month))
        q = JournalEntry.objects.filter(date__gte=first, date__lte=last)
        out.append({
            "year": year, "month": month,
            "closed": p is not None,
            "closed_at": p.closed_at.isoformat() if p else None,
            "closed_by": p.closed_by if p else "",
            "entries": q.count(),
            "brouillard": q.filter(is_posted=True, validated_at__isnull=True).count(),
            "drafts": q.filter(is_posted=False).count(),
            "validated": q.filter(~Q(validated_at=None)).count(),
        })
    return out
