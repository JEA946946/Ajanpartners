"""Journals, month closing and reversals (see journals/closing.py)."""

from datetime import date

from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response

from core.audit import log_action
from core.permissions import RoleWriteAccess

from . import closing
from .models import Journal, JournalEntry
from .periods import _to_date


def _user_name(user):
    return f"{user.first_name} {user.last_name}".strip() or user.username


def _journal_dict(j):
    return {
        "id": j.id, "code": j.code, "name": j.name, "type": j.type,
        "account_id": str(j.account_id) if j.account_id else None,
        "account_code": j.account.code if j.account_id else None,
        "currency": j.currency, "is_active": j.is_active,
    }


@api_view(["GET"])
@permission_classes([RoleWriteAccess])
def journals_list(request):
    journals = Journal.objects.select_related("account").all()
    return Response({"success": True, "data": {"journals": [_journal_dict(j) for j in journals]}})


@api_view(["PUT"])
@permission_classes([RoleWriteAccess])
def journals_detail(request, pk):
    """Rename or (de)activate a journal. Its code, type and account are fixed:
    numbers and entries already refer to them."""
    j = Journal.objects.select_related("account").filter(id=pk).first()
    if not j:
        return Response({"success": False, "message": "Journal not found"}, status=status.HTTP_404_NOT_FOUND)
    if "name" in request.data:
        j.name = (request.data["name"] or "").strip() or j.name
    if "is_active" in request.data:
        j.is_active = bool(request.data["is_active"])
    j.save()
    log_action(request.user, "update", "Journal", j.id, {"code": j.code, "name": j.name, "is_active": j.is_active})
    return Response({"success": True, "data": {"journal": _journal_dict(j)}})


@api_view(["GET"])
@permission_classes([RoleWriteAccess])
def periods_list(request):
    try:
        year = int(request.query_params.get("year") or date.today().year)
    except ValueError:
        return Response({"success": False, "message": "Invalid year"}, status=status.HTTP_400_BAD_REQUEST)
    nxt = closing.first_open_month()
    return Response({"success": True, "data": {
        "year": year, "months": closing.period_status(year),
        "next_to_close": {"year": nxt[0], "month": nxt[1]} if nxt else None,
    }})


def _year_month(request):
    try:
        year, month = int(request.data.get("year") or request.query_params.get("year")), \
            int(request.data.get("month") or request.query_params.get("month"))
        date(year, month, 1)
        return year, month
    except (TypeError, ValueError):
        return None


@api_view(["GET"])
@permission_classes([RoleWriteAccess])
def period_check(request):
    ym = _year_month(request)
    if not ym:
        return Response({"success": False, "message": "year and month are required"},
                        status=status.HTTP_400_BAD_REQUEST)
    return Response({"success": True, "data": closing.check_month(*ym)})


@api_view(["POST"])
@permission_classes([RoleWriteAccess])
def period_close(request):
    """Close a month: validate and number its entries. Cannot be undone."""
    ym = _year_month(request)
    if not ym:
        return Response({"success": False, "message": "year and month are required"},
                        status=status.HTTP_400_BAD_REQUEST)
    period, check = closing.close_month(*ym, closed_by=_user_name(request.user),
                                        confirm_warnings=bool(request.data.get("confirm_warnings")))
    if period is None:
        msg = "; ".join(check["blockers"]) or "Confirm the warnings to close the month"
        return Response({"success": False, "message": msg, "data": check}, status=status.HTTP_400_BAD_REQUEST)
    log_action(request.user, "close", "Period", period.id,
               {"period": str(period), "validated": check["validated"], "warnings": check["warnings"]})
    return Response({"success": True, "message": f"{period} closed — {check['validated']} entries validated",
                     "data": check})


@api_view(["POST"])
@permission_classes([RoleWriteAccess])
def journal_entry_reverse(request, pk):
    """Contre-passation of a validated entry, dated `date` (default today)."""
    entry = JournalEntry.objects.filter(id=pk).first()
    if not entry:
        return Response({"success": False, "message": "Journal entry not found"}, status=status.HTTP_404_NOT_FOUND)
    on_date = _to_date(request.data.get("date")) or date.today()
    rev, err = closing.reverse_entry(entry, on_date, _user_name(request.user))
    if err:
        return Response({"success": False, "message": err}, status=status.HTTP_400_BAD_REQUEST)
    log_action(request.user, "reverse", "JournalEntry", entry.id,
               {"entry_number": entry.entry_number, "reversal": rev.entry_number, "date": str(on_date)})
    return Response({"success": True, "message": f"Reversed by {rev.entry_number}",
                     "data": {"reversal_id": str(rev.id), "reversal_number": rev.entry_number}})
