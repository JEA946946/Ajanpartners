"""Månedslukning og årsafslutning.

At lukke en måned validerer alle dens posteringer: i datoorden får hver journals
posteringer de næste numre i journalens årlige serie (BANK-2026-00001 …), så
nummereringen er kronologisk og uden huller (Bogføringsloven). Derefter kan
posteringerne aldrig ændres (journals/signals.py), og måneden tager ikke nye.

Månederne lukkes i rækkefølge. En måned kan ikke lukkes med en kladde, en
postering, der ikke balancerer, eller en bankjournal uden afsluttet
bankafstemning pr. månedens sidste dag. Saldo på uafklarede poster er en advarsel.
"""

import calendar
from datetime import date, timedelta
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
        blockers.append(f"{year}-{month:02d} er allerede lukket")
        return {"blockers": blockers, "warnings": warnings}

    earlier = open_months_before(year, month)
    if earlier:
        y, m = earlier[0]
        blockers.append(f"Luk {y}-{m:02d} først; månederne lukkes i rækkefølge")

    entries = JournalEntry.objects.filter(date__gte=first, date__lte=last)
    drafts = entries.filter(is_posted=False).count()
    if drafts:
        blockers.append(f"{drafts} kladde(r) er ikke bogført – bogfør eller slet dem")

    unbalanced = [
        e.entry_number for e in entries.filter(is_posted=True).annotate(dr=Sum("lines__debit"), cr=Sum("lines__credit"))
        if (e.dr or Decimal("0")) != (e.cr or Decimal("0"))
    ]
    if unbalanced:
        blockers.append(f"Posteringer, der ikke balancerer: {', '.join(unbalanced[:10])}")

    for journal in Journal.objects.filter(type="bank", account__isnull=False).select_related("account"):
        has_lines = JournalEntryLine.objects.filter(
            account=journal.account, journal_entry__is_posted=True, journal_entry__date__lte=last).exists()
        if not has_lines:
            continue
        done = journal.account.reconciliations.filter(status="completed", date=last).exists()
        if not done:
            blockers.append(f"{journal.code} ({journal.account.code}) har ingen afsluttet bankafstemning "
                            f"pr. {last.isoformat()}")

    susp = (JournalEntryLine.objects
            .filter(account__code=chart.SUSPENSE, journal_entry__is_posted=True, journal_entry__date__lte=last)
            .aggregate(dr=Sum("debit"), cr=Sum("credit")))
    bal = (susp["dr"] or Decimal("0")) - (susp["cr"] or Decimal("0"))
    if bal:
        warnings.append(f"{chart.SUSPENSE} (uafklarede poster) har en saldo på {bal} kr. pr. {last.isoformat()}")

    # Bilag: banklinjer dokumenteres af kontoudtoget; alle andre posteringer skal
    # have et bilag vedhæftet (Bogføringsloven).
    unsupported = (entries.filter(is_posted=True).exclude(journal__type="bank")
                   .filter(documents__isnull=True).count())
    if unsupported:
        warnings.append(f"{unsupported} postering(er) har intet bilag vedhæftet")

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
    """Tilbageføring af en valideret postering: samme journal, debet og kredit
    byttet om, dateret i en åben måned. Returnerer (tilbageføring, fejl)."""
    from .numbering import next_je_number
    from .periods import closed_period_error

    if not entry.validated_at:
        return None, "Posteringen er ikke valideret endnu – ret eller slet den i stedet"
    done = JournalEntry.objects.filter(reversal_of=entry).first()
    if done:
        return None, f"Postering {entry.entry_number} er allerede tilbageført med {done.entry_number}"
    if on_date < entry.date:
        return None, "En tilbageføring kan ikke dateres før den postering, den tilbagefører"
    err = closed_period_error(on_date)
    if err:
        return None, err
    with transaction.atomic():
        rev = JournalEntry.objects.create(
            journal=entry.journal, entry_number=next_je_number(), date=on_date,
            piece_number=entry.piece_number,
            description=f"Tilbageføring af {entry.entry_number} — {entry.description}"[:2000],
            reference=entry.entry_number, source="reversal", source_id=str(entry.id),
            is_posted=True, created_by=created_by, reversal_of=entry,
        )
        for line in entry.lines.all():
            JournalEntryLine.objects.create(
                journal_entry=rev, account=line.account, debit=line.credit, credit=line.debit,
                currency=line.currency, exchange_rate=line.exchange_rate,
                amount_currency=-line.amount_currency if line.amount_currency is not None else None,
                vat_code=line.vat_code, partner_type=line.partner_type, partner_id=line.partner_id,
                partner_name=line.partner_name,
                description=f"Tilbageføring — {line.description}"[:500],
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
            "posted": q.filter(is_posted=True, validated_at__isnull=True).count(),
            "drafts": q.filter(is_posted=False).count(),
            "validated": q.filter(~Q(validated_at=None)).count(),
        })
    return out


# ─── Årsafslutning ────────────────────────────────────────────────────────────
# Når alle årets måneder er lukket: resultatkontiene nulstilles mod egenkapitalen
# (ÅA-journalen, dateret årets sidste dag), balancen overføres som primo til
# næste år (PRIMO-journalen, dateret næste års første dag), og året låses
# (FiscalYear.is_closed). Bogføringsloven kræver, at året ikke kan ændres bagefter.


def _months_in(fy):
    y, m = fy.start_date.year, fy.start_date.month
    while date(y, m, 1) <= fy.end_date:
        yield y, m
        y, m = (y + 1, 1) if m == 12 else (y, m + 1)


def result_account_code(template_hint=None):
    """Kontoen, årets resultat overføres til: overført resultat (selskaber) eller
    årets resultat for en enkeltmandsvirksomhed (konto 6916 er aktiv)."""
    from accounts.models import Account
    if template_hint == "enkeltmand":
        return chart.OWNER_RESULT
    if template_hint in ("standard", "holding"):
        return chart.RETAINED_EARNINGS
    owner = Account.objects.filter(code=chart.OWNER_RESULT, is_active=True).exists()
    company = Account.objects.filter(code=chart.RETAINED_EARNINGS, is_active=True).exists()
    return chart.OWNER_RESULT if owner and not company else chart.RETAINED_EARNINGS


def check_year(fy):
    """Hvad forhindrer årsafslutningen (blockers), og hvad skal bekræftes (warnings)."""
    from accounts.models import FiscalYear
    from core.models import VatReturn

    blockers, warnings = [], []
    if fy.is_closed:
        return {"blockers": [f"Regnskabsåret {fy.name} er allerede afsluttet"], "warnings": []}
    earlier = FiscalYear.objects.filter(end_date__lt=fy.start_date, is_closed=False).order_by("start_date").first()
    if earlier and JournalEntry.objects.filter(date__gte=earlier.start_date, date__lte=earlier.end_date).exists():
        blockers.append(f"Afslut {earlier.name} først")
    closed = set(Period.objects.values_list("year", "month"))
    with_entries = {(d.year, d.month) for d in JournalEntry.objects.filter(
        date__gte=fy.start_date, date__lte=fy.end_date).exclude(source="closing").dates("date", "month")}
    open_months = [f"{y}-{m:02d}" for y, m in _months_in(fy) if (y, m) in with_entries and (y, m) not in closed]
    if open_months:
        blockers.append(f"Disse måneder er ikke lukket: {', '.join(open_months)}")
    if JournalEntry.objects.filter(date__gte=fy.start_date, date__lte=fy.end_date, validated_at__isnull=True)\
            .exclude(source="closing").exists():
        blockers.append("Der er bogførte eller kladdeposteringer, der ikke er valideret")

    susp = JournalEntryLine.objects.filter(
        account__code=chart.SUSPENSE, journal_entry__is_posted=True,
        journal_entry__date__lte=fy.end_date).aggregate(dr=Sum("debit"), cr=Sum("credit"))
    bal = (susp["dr"] or Decimal("0")) - (susp["cr"] or Decimal("0"))
    if bal:
        warnings.append(f"Uafklarede poster ({chart.SUSPENSE}) har en saldo på {bal} kr. pr. {fy.end_date}")
    unfiled = VatReturn.objects.filter(period_start__gte=fy.start_date, period_end__lte=fy.end_date)\
        .exclude(status="filed").count()
    if unfiled:
        warnings.append(f"{unfiled} momsperiode(r) i året er ikke angivet")
    result = year_result(fy)
    return {"blockers": blockers, "warnings": warnings, "result": str(result),
            "result_account": result_account_code()}


def year_result(fy):
    """Årets resultat (kredit − debet på resultatkonti), uden årsafslutningsposteringen."""
    totals = JournalEntryLine.objects.filter(
        journal_entry__is_posted=True, journal_entry__date__gte=fy.start_date,
        journal_entry__date__lte=fy.end_date, account__arl_line__in=_result_lines(),
    ).exclude(journal_entry__source="closing").aggregate(dr=Sum("debit"), cr=Sum("credit"))
    return (totals["cr"] or Decimal("0")) - (totals["dr"] or Decimal("0"))


def _result_lines():
    from accounts.standardkontoplan import ARL_LINES
    return [k for k, _, side in ARL_LINES if side == "result"]


def _validate_now(entry, by):
    """Nummerér og valider en postering, som årsafslutningen selv laver i en lukket periode."""
    entry.entry_number = validated_number(entry.journal, entry.date.year)
    entry.validated_at = timezone.now()
    entry.validated_by = by
    entry.save(update_fields=["entry_number", "validated_at", "validated_by", "updated_at"])


def close_year(fy, closed_by, confirm_warnings=False, result_account=None):
    """Bogfør årsafslutning og primo og lås året. Returnerer (resultat, check);
    resultat er None, hvis året ikke kunne afsluttes."""
    from accounts.models import Account, FiscalYear
    from .journal_for import CLOSING, OPENING, journal_by_code
    from .lettrage import tiers_type
    from .numbering import next_je_number

    with transaction.atomic():
        FiscalYear.objects.select_for_update().filter(pk=fy.pk).first()
        check = check_year(fy)
        if check["blockers"] or (check["warnings"] and not confirm_warnings):
            return None, check
        equity = Account.objects.get(code=result_account or result_account_code())

        # 1. Resultatkonti nulstilles mod egenkapitalen (ÅA, valideret med det samme).
        result_rows = (JournalEntryLine.objects
                       .filter(journal_entry__is_posted=True, journal_entry__date__gte=fy.start_date,
                               journal_entry__date__lte=fy.end_date, account__arl_line__in=_result_lines())
                       .values("account_id").annotate(dr=Sum("debit"), cr=Sum("credit")))
        closing_entry = JournalEntry.objects.create(
            journal=journal_by_code(CLOSING), entry_number=next_je_number(), date=fy.end_date,
            description=f"Årsafslutning {fy.name}: resultat overført til egenkapitalen",
            reference=f"ÅA:{fy.name}", source="closing", source_id=str(fy.id), is_posted=True,
            created_by=closed_by)
        result = Decimal("0")
        for row in result_rows:
            bal = (row["dr"] or Decimal("0")) - (row["cr"] or Decimal("0"))
            if not bal:
                continue
            result -= bal
            JournalEntryLine.objects.create(
                journal_entry=closing_entry, account_id=row["account_id"],
                debit=-bal if bal < 0 else Decimal("0"), credit=bal if bal > 0 else Decimal("0"),
                description="Årsafslutning")
        if result:
            JournalEntryLine.objects.create(
                journal_entry=closing_entry, account=equity,
                debit=-result if result < 0 else Decimal("0"), credit=result if result > 0 else Decimal("0"),
                description=f"Årets resultat {fy.name}")
        if closing_entry.lines.exists():
            _validate_now(closing_entry, closed_by)
        else:
            closing_entry.delete()
            closing_entry = None

        # 2. Næste regnskabsår findes (oprettes ellers med samme længde).
        nxt = FiscalYear.objects.filter(start_date__gt=fy.end_date).order_by("start_date").first()
        if nxt is None:
            start = fy.end_date + timedelta(days=1)
            end = _same_length_end(fy, start)
            nxt = FiscalYear.objects.create(name=_fy_name(start, end), start_date=start, end_date=end)

        # 3. Primo: balancekontienes saldi (pr. debitor/kreditor på debitor- og
        # kreditorkonti), dateret næste års første dag. Bogført, valideres ved
        # månedslukning.
        balance_rows = (JournalEntryLine.objects
                        .filter(journal_entry__is_posted=True, journal_entry__date__lte=fy.end_date)
                        .exclude(account__arl_line__in=_result_lines())
                        .filter(_since_last_opening(fy))
                        .values("account_id", "account__code", "partner_type", "partner_id", "partner_name")
                        .annotate(dr=Sum("debit"), cr=Sum("credit")))
        opening = JournalEntry.objects.create(
            journal=journal_by_code(OPENING), entry_number=next_je_number(), date=nxt.start_date,
            description=f"Primo {nxt.name} (overført fra {fy.name})", reference=f"PRIMO:{nxt.name}",
            source="opening", source_id=str(fy.id), is_posted=True, created_by=closed_by)
        totals = {}
        for row in balance_rows:
            key = (row["account_id"], row["partner_id"] if tiers_type(row["account__code"]) else "")
            t = totals.setdefault(key, {"bal": Decimal("0"), "row": row})
            t["bal"] += (row["dr"] or Decimal("0")) - (row["cr"] or Decimal("0"))
        for (account_id, partner_id), t in sorted(totals.items(), key=lambda kv: kv[1]["row"]["account__code"]):
            bal = t["bal"]
            if not bal:
                continue
            tiers = ({"partner_type": t["row"]["partner_type"], "partner_id": partner_id,
                      "partner_name": t["row"]["partner_name"]} if partner_id else {})
            JournalEntryLine.objects.create(
                journal_entry=opening, account_id=account_id,
                debit=bal if bal > 0 else Decimal("0"), credit=-bal if bal < 0 else Decimal("0"),
                description="Primo", **tiers)
        if not opening.lines.exists():
            opening.delete()
            opening = None

        # 4. Lås året.
        fy.is_closed = True
        fy.closed_at = timezone.now()
        fy.closed_by = closed_by
        fy.save(update_fields=["is_closed", "closed_at", "closed_by"])
        return {
            "result": str(result), "result_account": equity.code,
            "closing_entry": closing_entry.entry_number if closing_entry else None,
            "opening_entry": opening.entry_number if opening else None,
            "next_year": nxt.name,
        }, check


def _since_last_opening(fy):
    """Q, der begrænser balancen til linjer efter det sidste afsluttede år (de
    tidligere år er allerede samlet i en primopostering)."""
    from accounts.models import FiscalYear
    prev = FiscalYear.objects.filter(is_closed=True, end_date__lt=fy.start_date).order_by("-end_date").first()
    if prev is None:
        return Q()
    return Q(journal_entry__date__gt=prev.end_date)


def _same_length_end(fy, start):
    # Næste år er altid 12 måneder (også efter et forlænget første regnskabsår, ÅRL § 15).
    y, m = start.year, start.month + 11
    y, m = y + (m - 1) // 12, (m - 1) % 12 + 1
    return date(y, m, calendar.monthrange(y, m)[1])


def _fy_name(start, end):
    return str(start.year) if (start.month, start.day, end.year) == (1, 1, start.year) else \
        f"{start.year}/{str(end.year)[-2:]}"


def year_status():
    """Alle regnskabsår med status og resultat, til årsafslutningssiden."""
    from accounts.models import FiscalYear
    out = []
    for fy in FiscalYear.objects.order_by("start_date"):
        out.append({
            "id": str(fy.id), "name": fy.name, "start_date": fy.start_date.isoformat(),
            "end_date": fy.end_date.isoformat(), "is_closed": fy.is_closed,
            "closed_at": fy.closed_at.isoformat() if fy.closed_at else None, "closed_by": fy.closed_by,
            "result": str(year_result(fy)),
        })
    return out
