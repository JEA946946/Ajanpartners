"""Tiers and lettrage on the third-party accounts (3421 Clients, 4411 Fournisseurs …).

Lines of one account and one tiers that settle each other (an invoice and the
payments of it) get the same lettrage code (AA, AB, … ZZ, AAA …), unique per
account and tiers. Lettering needs the lines to add up to zero. A bill paid in
full or an invoice received in full is lettered automatically; anything else is
lettered by hand on the Lettrage page. The lettrage fields are the only ones that
may change on a validated line (journals/signals.py, migration 0015).
"""

import string
from decimal import Decimal

from django.db import transaction
from django.db.models import Count, Max, Q, Sum
from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response

from accounts import chart
from core.audit import log_action
from core.permissions import RoleWriteAccess

from .models import JournalEntryLine

# Accounts whose lines carry a tiers and can be lettered.
TIERS_ACCOUNTS = {chart.RECEIVABLE: "customer", chart.CLIENT_ADVANCES: "customer", chart.PAYABLE: "supplier"}


def tiers_type(account_code):
    return TIERS_ACCOUNTS.get(account_code, "")


def customer_partner(customer):
    return {"partner_type": "customer", "partner_id": str(customer.id), "partner_name": customer.name} \
        if customer else {}


def supplier_partner(supplier):
    return {"partner_type": "supplier", "partner_id": str(supplier.id), "partner_name": supplier.name} \
        if supplier else {}


def _code(n):
    """0 → AA, 1 → AB, … 675 → ZZ, 676 → AAA."""
    letters = string.ascii_uppercase
    width = 2
    while n >= 26 ** width:
        n -= 26 ** width
        width += 1
    out = ""
    for _ in range(width):
        n, r = divmod(n, 26)
        out = letters[r] + out
    return out


def _index(code):
    letters = string.ascii_uppercase
    n = 0
    for c in code:
        n = n * 26 + letters.index(c)
    return n + sum(26 ** w for w in range(2, len(code)))


def next_code(account_id, partner_id):
    used = (JournalEntryLine.objects.filter(account_id=account_id, partner_id=partner_id)
            .exclude(lettrage="").values_list("lettrage", flat=True).distinct())
    return _code(max((_index(c) for c in used), default=-1) + 1)


def lettrer(lines, on_date=None):
    """Letter the lines together. Returns (code, error)."""
    lines = list(lines)
    if len(lines) < 2:
        return None, "Pick at least two lines"
    if len({l.account_id for l in lines}) != 1 or len({l.partner_id for l in lines}) != 1:
        return None, "The lines must be on the same account and tiers"
    if len({l.currency for l in lines}) != 1:
        return None, "The lines must be in the same currency"
    if any(l.lettrage for l in lines):
        return None, "Some lines are already lettered"
    if any(not l.journal_entry.is_posted for l in lines):
        return None, "Draft entries cannot be lettered"
    total = sum(((l.debit or Decimal("0")) - (l.credit or Decimal("0")) for l in lines), Decimal("0"))
    if total != 0:
        return None, f"The lines do not balance (difference {total})"
    code = next_code(lines[0].account_id, lines[0].partner_id)
    on_date = on_date or timezone.localdate()
    for l in lines:
        l.lettrage, l.lettrage_date = code, on_date
        l.save(update_fields=["lettrage", "lettrage_date"])
    return code, None


def delettrer(account_id, partner_id, code):
    n = 0
    for l in JournalEntryLine.objects.filter(account_id=account_id, partner_id=partner_id, lettrage=code):
        l.lettrage, l.lettrage_date = "", None
        l.save(update_fields=["lettrage", "lettrage_date"])
        n += 1
    return n


def auto_lettrer(lines):
    """Letter the lines if they settle each other; quietly do nothing otherwise."""
    lines = [l for l in lines if not l.lettrage]
    if len(lines) < 2:
        return None
    code, err = lettrer(lines)
    return code


def undo_lettrage_of(lines):
    """Remove the lettrage the given lines are part of (before a match is undone)."""
    for l in lines:
        if l.lettrage:
            delettrer(l.account_id, l.partner_id, l.lettrage)


# ─── API ────────────────────────────────────────────────────────────────────

def _account(request):
    from accounts.models import Account
    code = request.query_params.get("account") or request.data.get("account") or chart.PAYABLE
    return Account.objects.filter(code=code).first()


def _line_dict(l):
    e = l.journal_entry
    return {
        "id": str(l.id), "date": e.date.isoformat(), "journal_code": e.journal.code,
        "entry_number": e.entry_number, "piece_number": e.piece_number,
        "description": l.description or e.description,
        "debit": str(l.debit), "credit": str(l.credit), "currency": l.currency,
        "lettrage": l.lettrage, "lettrage_date": l.lettrage_date.isoformat() if l.lettrage_date else None,
        "status": e.status,
    }


@api_view(["GET"])
@permission_classes([RoleWriteAccess])
def tiers_balances(request):
    """Balance per tiers on a tiers account: total, and what is not lettered."""
    account = _account(request)
    if not account:
        return Response({"success": False, "message": "Account not found"}, status=status.HTTP_400_BAD_REQUEST)
    rows = (JournalEntryLine.objects.filter(account=account, journal_entry__is_posted=True)
            .values("partner_id", "currency")
            .annotate(name=Max("partner_name"), dr=Sum("debit"), cr=Sum("credit"),
                      open_dr=Sum("debit", filter=Q(lettrage="")), open_cr=Sum("credit", filter=Q(lettrage="")),
                      open_lines=Count("id", filter=Q(lettrage="")))
            .order_by("name"))
    out = [{
        "partner_id": r["partner_id"], "partner_name": r["name"] or "—", "currency": r["currency"],
        "debit": str(r["dr"] or 0), "credit": str(r["cr"] or 0),
        "balance": str((r["dr"] or 0) - (r["cr"] or 0)),
        "open_balance": str((r["open_dr"] or 0) - (r["open_cr"] or 0)),
        "open_lines": r["open_lines"],
    } for r in rows]
    return Response({"success": True, "data": {"account": account.code, "tiers": out}})


@api_view(["GET"])
@permission_classes([RoleWriteAccess])
def tiers_lines(request):
    """The lines of one tiers on an account; state=open (default), lettered or all."""
    account = _account(request)
    if not account:
        return Response({"success": False, "message": "Account not found"}, status=status.HTTP_400_BAD_REQUEST)
    qs = (JournalEntryLine.objects.filter(account=account, journal_entry__is_posted=True,
                                          partner_id=request.query_params.get("partner_id", ""))
          .select_related("journal_entry__journal").order_by("journal_entry__date", "line_no"))
    state = request.query_params.get("state", "open")
    if state == "open":
        qs = qs.filter(lettrage="")
    elif state == "lettered":
        qs = qs.exclude(lettrage="")
    return Response({"success": True, "data": {"lines": [_line_dict(l) for l in qs]}})


@api_view(["POST"])
@permission_classes([RoleWriteAccess])
def lettrage_create(request):
    ids = request.data.get("line_ids") or []
    with transaction.atomic():
        lines = list(JournalEntryLine.objects.select_for_update().filter(id__in=ids)
                     .select_related("journal_entry", "account"))
        if len(lines) != len(set(ids)):
            return Response({"success": False, "message": "Line not found"}, status=status.HTTP_400_BAD_REQUEST)
        code, err = lettrer(lines)
        if err:
            return Response({"success": False, "message": err}, status=status.HTTP_400_BAD_REQUEST)
    log_action(request.user, "lettrer", "JournalEntryLine", lines[0].account.code,
               {"code": code, "partner": lines[0].partner_name, "lines": [str(l.id) for l in lines]})
    return Response({"success": True, "message": f"Lettered {code}", "data": {"code": code}})


@api_view(["POST"])
@permission_classes([RoleWriteAccess])
def lettrage_undo(request):
    account = _account(request)
    code = request.data.get("code") or ""
    if not account or not code:
        return Response({"success": False, "message": "account and code are required"},
                        status=status.HTTP_400_BAD_REQUEST)
    with transaction.atomic():
        n = delettrer(account.id, request.data.get("partner_id", ""), code)
    if not n:
        return Response({"success": False, "message": "Lettrage not found"}, status=status.HTTP_404_NOT_FOUND)
    log_action(request.user, "delettrer", "JournalEntryLine", account.code,
               {"code": code, "partner_id": request.data.get("partner_id", ""), "lines": n})
    return Response({"success": True, "message": f"{code} removed from {n} lines"})
