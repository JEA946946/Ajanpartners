"""TVA on the margin (Art. 125 bis CGI) for an inbound travel agency.

Sales are booked gross (TTC) on 71243 and tourism supplier costs TTC on 61263*
without TVA deduction. For a period:

    margin TTC     = sales TTC − costs TTC
    TVA collectée  = margin TTC / 1.2 × 20 %      (posted DR 71243 / CR 4455)
    TVA déductible = TVA récupérable on overheads (34552)
"""

from decimal import Decimal

from django.db.models import Q, Sum

from accounts import chart

from .models import JournalEntryLine

ZERO = Decimal("0")


def _sum(qs):
    t = qs.aggregate(dr=Sum("debit"), cr=Sum("credit"))
    return t["dr"] or ZERO, t["cr"] or ZERO


def period_margin(date_from=None, date_to=None):
    lines = JournalEntryLine.objects.in_mad().filter(journal_entry__is_posted=True)
    if date_from:
        lines = lines.filter(journal_entry__date__gte=date_from)
    if date_to:
        lines = lines.filter(journal_entry__date__lte=date_to)

    # The TVA entry itself debits 71243; it is not a sale reduction.
    dr, cr = _sum(lines.filter(account__code__startswith=chart.REVENUE).exclude(journal_entry__source="tva_margin"))
    sales = cr - dr
    dr, cr = _sum(lines.filter(account__code__startswith=chart.COST_OF_SALES))
    costs = dr - cr
    margin = sales - costs
    dr, cr = _sum(lines.filter(Q(account__code__startswith=chart.TVA_RECOVERABLE)))
    deductible = dr - cr
    collectee = chart.margin_tva(margin) if margin > 0 else ZERO
    return {
        "sales": sales,
        "costs": costs,
        "margin": margin,
        "tva_collectee": collectee,
        "tva_deductible": deductible,
        "tva_a_payer": collectee - deductible,
    }
