"""Rapporter: saldobalance, resultatopgørelse og balance efter årsregnskabslovens
skema (Account.arl_line), og kontokort.

Beløb er DKK (debit/credit er altid DKK). Kun bogførte posteringer tæller.

Saldi: balancekonti summeres fra dagen efter det sidste afsluttede regnskabsår
(hvis der er et), fordi årsafslutningen har samlet alt før i en primopostering.
Resultatkonti summeres inden for perioden, uden årsafslutningsposteringen (ÅA),
så resultatet kan ses, også efter at året er lukket.
"""

from datetime import date, timedelta
from decimal import Decimal

from django.db.models import Q, Sum
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response

from accounts.models import Account, FiscalYear
from accounts.standardkontoplan import ARL_LINE_NAMES, ARL_LINES
from core.permissions import RoleWriteAccess

from .models import JournalEntryLine
from .periods import _to_date

ZERO = Decimal("0")
RESULT_LINES = [k for k, _, side in ARL_LINES if side == "result"]
ASSET_LINES = [k for k, _, side in ARL_LINES if side == "asset"]
LIABILITY_LINES = [k for k, _, side in ARL_LINES if side == "liability"]
EQUITY_LINES = ["virksomhedskapital", "overkurs", "reserver", "overfoert_resultat", "foreslaaet_udbytte"]
# Linjer med kreditsaldo som normal (vises med positivt fortegn).
CREDIT_RESULT_LINES = {"nettoomsaetning", "eget_arbejde", "andre_driftsindtaegter", "indtaegter_kapitalandele",
                       "finansielle_indtaegter"}


# ─── Byggeklodser ─────────────────────────────────────────────────────────────

def fiscal_year_start(d):
    """Første dag i regnskabsåret, der indeholder d (1. januar uden regnskabsår)."""
    fy = FiscalYear.objects.filter(start_date__lte=d, end_date__gte=d).first()
    return fy.start_date if fy else date(d.year, 1, 1)


def balance_start(d):
    """Dagen efter det sidste afsluttede regnskabsår før d, eller None."""
    prev = FiscalYear.objects.filter(is_closed=True, end_date__lt=d).order_by("-end_date").first()
    return prev.end_date + timedelta(days=1) if prev else None


def _posted():
    return JournalEntryLine.objects.filter(journal_entry__is_posted=True)


def movements(date_from=None, date_to=None, result_only=None, exclude_closing=False):
    """{account_id: (debit, credit)} for linjer i [date_from, date_to]."""
    qs = _posted()
    if date_from:
        qs = qs.filter(journal_entry__date__gte=date_from)
    if date_to:
        qs = qs.filter(journal_entry__date__lte=date_to)
    if result_only is True:
        qs = qs.filter(account__arl_line__in=RESULT_LINES)
    elif result_only is False:
        qs = qs.exclude(account__arl_line__in=RESULT_LINES)
    if exclude_closing:
        qs = qs.exclude(journal_entry__source="closing")
    return {r["account_id"]: (r["dr"] or ZERO, r["cr"] or ZERO)
            for r in qs.values("account_id").annotate(dr=Sum("debit"), cr=Sum("credit"))}


def balances_at(d):
    """Balancekontienes saldo (debet − kredit) pr. dag d."""
    rows = movements(balance_start(d), d, result_only=False)
    return {aid: dr - cr for aid, (dr, cr) in rows.items()}


def result_for(date_from, date_to):
    """Resultatkontienes bevægelse (debet − kredit) i perioden, uden ÅA."""
    rows = movements(date_from, date_to, result_only=True, exclude_closing=True)
    return {aid: dr - cr for aid, (dr, cr) in rows.items()}


def _shift_year(d, years=-1):
    try:
        return d.replace(year=d.year + years)
    except ValueError:  # 29. februar
        return d.replace(year=d.year + years, day=28)


def _period(request):
    """(date_from, date_to, fejl). Standard: regnskabsåret til dato."""
    today = date.today()
    date_to = _to_date(request.query_params.get("date_to")) or today
    date_from = _to_date(request.query_params.get("date_from")) or fiscal_year_start(date_to)
    if date_from > date_to:
        return None, None, "date_from er efter date_to"
    return date_from, date_to, None


def _accounts():
    return {a.id: a for a in Account.objects.select_related("account_type")}


def _money(v):
    return f"{(v or ZERO):.2f}"


# ─── Saldobalance ─────────────────────────────────────────────────────────────

@api_view(["GET"])
@permission_classes([RoleWriteAccess])
def report_trial_balance(request):
    """Saldobalance pr. konto for perioden, med sammenligning.

    compare=period (samme periode sidste år, standard), year (år til dato),
    last_year (hele sidste regnskabsår). Kolonner: primo, debet, kredit,
    ultimo, og `compare` (bevægelse/saldo i sammenligningsperioden)."""
    date_from, date_to, err = _period(request)
    if err:
        return Response({"success": False, "message": err}, status=status.HTTP_400_BAD_REQUEST)
    compare = request.query_params.get("compare", "period")
    accounts = _accounts()
    fy_start = fiscal_year_start(date_from)

    period = movements(date_from, date_to, exclude_closing=True)
    opening_bal = balances_at(date_from - timedelta(days=1))
    opening_res = result_for(fy_start, date_from - timedelta(days=1)) if fy_start < date_from else {}

    if compare == "year":
        cmp_from, cmp_to = fiscal_year_start(date_to), date_to
    elif compare == "last_year":
        ly = _shift_year(date_to)
        cmp_from = fiscal_year_start(ly)
        fy = FiscalYear.objects.filter(start_date=cmp_from).first()
        cmp_to = fy.end_date if fy else date(ly.year, 12, 31)
    else:
        compare = "period"
        cmp_from, cmp_to = _shift_year(date_from), _shift_year(date_to)
    cmp_res = result_for(cmp_from, cmp_to)
    cmp_bal = balances_at(cmp_to)

    rows, tot = [], {"opening": ZERO, "debit": ZERO, "credit": ZERO, "closing": ZERO, "compare": ZERO}
    ids = set(period) | set(opening_bal) | set(opening_res) | set(cmp_res) | set(cmp_bal)
    for aid in ids:
        a = accounts[aid]
        is_result = a.arl_line in RESULT_LINES
        opening = (opening_res if is_result else opening_bal).get(aid, ZERO)
        dr, cr = period.get(aid, (ZERO, ZERO))
        closing = opening + dr - cr
        cmp = (cmp_res if is_result else cmp_bal).get(aid, ZERO)
        if not any((opening, dr, cr, cmp)):
            continue
        rows.append({
            "account_id": str(aid), "account_code": a.code, "account_name": a.name,
            "standard_code": a.standard_code, "arl_line": a.arl_line,
            "arl_line_name": ARL_LINE_NAMES.get(a.arl_line, ""),
            "account_type": a.account_type.name, "is_result": is_result,
            "opening": _money(opening), "debit": _money(dr), "credit": _money(cr),
            "closing": _money(closing), "compare": _money(cmp), "difference": _money(closing - cmp),
            # Bagudkompatibelt: saldo med normalt fortegn
            "balance": _money(closing if a.account_type.normal_balance == "debit" else -closing),
        })
        for k, v in (("opening", opening), ("debit", dr), ("credit", cr), ("closing", closing), ("compare", cmp)):
            tot[k] += v
    rows.sort(key=lambda r: r["account_code"])
    return Response({"success": True, "data": {
        "date_from": date_from.isoformat(), "date_to": date_to.isoformat(),
        "compare": compare, "compare_from": cmp_from.isoformat(), "compare_to": cmp_to.isoformat(),
        "rows": rows, "totals": {k: _money(v) for k, v in tot.items()},
        "is_balanced": tot["debit"] == tot["credit"],
    }})


# ─── Resultatopgørelse (ÅRL bilag 2, artsopdelt) ─────────────────────────────

SUBTOTALS = [
    # (efter linje, nøgle, navn)
    ("andre_eksterne_omkostninger", "bruttofortjeneste", "Bruttofortjeneste/bruttotab"),
    ("andre_driftsomkostninger", "resultat_primaer_drift", "Resultat af primær drift"),
    ("finansielle_omkostninger", "resultat_foer_skat", "Resultat før skat"),
    ("skat", "aarets_resultat", "Årets resultat"),
]


def _by_line(values, accounts, lines):
    """{arl_line: [konti]} med beløb (kredit positiv for resultat)."""
    out = {k: [] for k in lines}
    for aid, net in values.items():
        a = accounts[aid]
        if a.arl_line in out and net:
            out[a.arl_line].append((a, net))
    return out


@api_view(["GET"])
@permission_classes([RoleWriteAccess])
def report_profit_and_loss(request):
    """Resultatopgørelse efter ÅRL (artsopdelt), med samme periode sidste år."""
    date_from, date_to, err = _period(request)
    if err:
        return Response({"success": False, "message": err}, status=status.HTTP_400_BAD_REQUEST)
    accounts = _accounts()
    cur = {aid: -v for aid, v in result_for(date_from, date_to).items()}  # kredit positiv
    prev = {aid: -v for aid, v in result_for(_shift_year(date_from), _shift_year(date_to)).items()}
    cur_lines, prev_lines = _by_line(cur, accounts, RESULT_LINES), _by_line(prev, accounts, RESULT_LINES)

    sections, running, running_prev = [], ZERO, ZERO
    subtotal_after = {after: (key, name) for after, key, name in SUBTOTALS}
    for key, name, _ in [x for x in ARL_LINES if x[2] == "result"]:
        amount = sum((v for _, v in cur_lines[key]), ZERO)
        amount_prev = sum((v for _, v in prev_lines[key]), ZERO)
        running += amount
        running_prev += amount_prev
        prev_by_id = {a.id: v for a, v in prev_lines[key]}
        accs = {a.id: a for a, _ in cur_lines[key] + prev_lines[key]}
        sections.append({
            "type": "line", "key": key, "name": name,
            "amount": _money(amount), "amount_prev": _money(amount_prev),
            "accounts": sorted([{
                "account_id": str(a.id), "account_code": a.code, "account_name": a.name,
                "amount": _money(dict((x.id, v) for x, v in cur_lines[key]).get(a.id, ZERO)),
                "amount_prev": _money(prev_by_id.get(a.id, ZERO)),
            } for a in accs.values()], key=lambda r: r["account_code"]),
        })
        if key in subtotal_after:
            skey, sname = subtotal_after[key]
            sections.append({"type": "subtotal", "key": skey, "name": sname,
                             "amount": _money(running), "amount_prev": _money(running_prev)})
    return Response({"success": True, "data": {
        "date_from": date_from.isoformat(), "date_to": date_to.isoformat(),
        "compare_from": _shift_year(date_from).isoformat(), "compare_to": _shift_year(date_to).isoformat(),
        "sections": sections, "net_result": _money(running), "net_result_prev": _money(running_prev),
    }})


# ─── Balance ──────────────────────────────────────────────────────────────────

def _balance_sheet(d):
    accounts = _accounts()
    bal = balances_at(d)
    # Resultat, der endnu ikke er overført til egenkapitalen (åbent år).
    start = balance_start(d)
    res = movements(start, d, result_only=True)
    open_result = sum(((cr - dr) for dr, cr in res.values()), ZERO)

    def side(lines, sign):
        out, total = [], ZERO
        grouped = _by_line(bal, accounts, lines)
        for key in lines:
            items = [(a, sign * v) for a, v in grouped[key]]
            amount = sum((v for _, v in items), ZERO)
            if key == "overfoert_resultat" and open_result:
                amount += open_result
            total += amount
            out.append({"key": key, "name": ARL_LINE_NAMES[key], "amount": amount, "accounts": items})
        return out, total

    assets, total_assets = side(ASSET_LINES, 1)
    liabilities, total_liab = side(LIABILITY_LINES, -1)
    return assets, total_assets, liabilities, total_liab, open_result


@api_view(["GET"])
@permission_classes([RoleWriteAccess])
def report_balance_sheet(request):
    """Balance efter ÅRL (kontoform), pr. date (standard i dag), med sidste år."""
    d = _to_date(request.query_params.get("date") or request.query_params.get("date_to")) or date.today()
    d_prev = _shift_year(d)
    cur = _balance_sheet(d)
    prev = _balance_sheet(d_prev)

    def merge(cur_side, prev_side):
        out = []
        for c, p in zip(cur_side, prev_side):
            prev_by = {a.id: v for a, v in p["accounts"]}
            accs = {a.id: a for a, _ in c["accounts"] + p["accounts"]}
            cur_by = {a.id: v for a, v in c["accounts"]}
            out.append({
                "key": c["key"], "name": c["name"], "amount": _money(c["amount"]),
                "amount_prev": _money(p["amount"]),
                "is_equity": c["key"] in EQUITY_LINES,
                "accounts": sorted([{"account_id": str(a.id), "account_code": a.code, "account_name": a.name,
                                     "amount": _money(cur_by.get(a.id, ZERO)),
                                     "amount_prev": _money(prev_by.get(a.id, ZERO))} for a in accs.values()],
                                   key=lambda r: r["account_code"]),
            })
        return out

    equity = sum((Decimal(x["amount"]) for x in merge(cur[2], prev[2]) if x["key"] in EQUITY_LINES), ZERO)
    return Response({"success": True, "data": {
        "date": d.isoformat(), "compare_date": d_prev.isoformat(),
        "assets": merge(cur[0], prev[0]), "liabilities": merge(cur[2], prev[2]),
        "total_assets": _money(cur[1]), "total_assets_prev": _money(prev[1]),
        "total_liabilities": _money(cur[3]), "total_liabilities_prev": _money(prev[3]),
        "total_equity": _money(equity),
        "unallocated_result": _money(cur[4]),
        "is_balanced": cur[1] == cur[3],
    }})


# ─── Kontokort ────────────────────────────────────────────────────────────────

@api_view(["GET"])
@permission_classes([RoleWriteAccess])
def report_account_card(request):
    """Kontokort: primosaldo, alle linjer i perioden med løbende saldo, ultimo.

    Parametre: account (kontonummer) eller account_id, date_from, date_to."""
    date_from, date_to, err = _period(request)
    if err:
        return Response({"success": False, "message": err}, status=status.HTTP_400_BAD_REQUEST)
    q = Q(code=request.query_params.get("account")) if request.query_params.get("account") else \
        Q(id=request.query_params.get("account_id") or None)
    account = Account.objects.filter(q).select_related("account_type").first()
    if account is None:
        return Response({"success": False, "message": "Kontoen findes ikke"}, status=status.HTTP_404_NOT_FOUND)
    is_result = account.arl_line in RESULT_LINES
    day_before = date_from - timedelta(days=1)
    if is_result:
        fy_start = fiscal_year_start(date_from)
        opening = result_for(fy_start, day_before).get(account.id, ZERO) if fy_start <= day_before else ZERO
    else:
        opening = balances_at(day_before).get(account.id, ZERO)
    lines = (_posted().filter(account=account, journal_entry__date__gte=date_from, journal_entry__date__lte=date_to)
             .select_related("journal_entry", "journal_entry__journal")
             .order_by("journal_entry__date", "journal_entry__entry_number", "line_no"))
    if is_result:
        lines = lines.exclude(journal_entry__source="closing")
    running, out, tdr, tcr = opening, [], ZERO, ZERO
    for line in lines:
        running += line.debit - line.credit
        tdr += line.debit
        tcr += line.credit
        je = line.journal_entry
        out.append({
            "id": str(line.id), "date": je.date.isoformat(), "entry_id": str(je.id),
            "entry_number": je.entry_number, "journal": je.journal.code, "piece_number": je.piece_number,
            "description": line.description or je.description, "vat_code": line.vat_code,
            "partner_name": line.partner_name, "lettrage": line.lettrage,
            "debit": _money(line.debit), "credit": _money(line.credit), "balance": _money(running),
            "currency": line.currency,
            "amount_currency": str(line.amount_currency) if line.amount_currency is not None else None,
        })
    return Response({"success": True, "data": {
        "account": {"id": str(account.id), "code": account.code, "name": account.name,
                    "standard_code": account.standard_code, "arl_line": account.arl_line},
        "date_from": date_from.isoformat(), "date_to": date_to.isoformat(),
        "opening": _money(opening), "lines": out, "total_debit": _money(tdr), "total_credit": _money(tcr),
        "closing": _money(running),
    }})
