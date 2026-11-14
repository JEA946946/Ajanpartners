"""Moms-endpoints (vat/...), feature-gatet som "vat" i tenancy/features.py.

GET  vat/periods?year=            perioderne efter kundens momsperiode med status og frist
GET  vat/report?start=&end=       momsangivelsens felter, afstemning og momskontienes saldi
POST vat/settle   {start, end, date?}  bogfør momsafregningen
POST vat/unsettle {start, end}         fjern en ikke angivet momsafregning
POST vat/file     {start, end, receipt_number?}  angivet hos Skat: lås perioden
"""

from datetime import date

from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response

from core import vat
from core.audit import log_action
from core.models import VatReturn
from core.permissions import RoleWriteAccess
from journals.periods import _to_date


def _vat_period(request):
    return getattr(getattr(request, "tenant", None), "vat_period", None) or "quarter"


def _user(request):
    u = request.user
    return f"{u.first_name} {u.last_name}".strip() or u.username


def _bounds(request):
    src = request.data if request.method == "POST" else request.query_params
    start, end = _to_date(src.get("start") or src.get("period_start")), _to_date(src.get("end") or src.get("period_end"))
    if not start or not end or end < start:
        return None, None, Response({"success": False, "message": "start og end (åååå-mm-dd) skal angives"},
                                    status=status.HTTP_400_BAD_REQUEST)
    vp = _vat_period(request)
    p = vat.period_of(start, vp)
    if p is None or (p[0], p[1]) != (start, end):
        return None, None, Response({"success": False, "message":
                                     "Perioden passer ikke med kundens momsperiode"},
                                    status=status.HTTP_400_BAD_REQUEST)
    return start, end, None


def _return_dict(vr):
    if vr is None:
        return None
    return {"id": str(vr.id), "status": vr.status, "fields": vr.fields,
            "settlement_entry": vr.settlement_entry.entry_number if vr.settlement_entry_id else None,
            "settlement_entry_id": str(vr.settlement_entry_id) if vr.settlement_entry_id else None,
            "filed_at": vr.filed_at.isoformat() if vr.filed_at else None, "filed_by": vr.filed_by,
            "receipt_number": vr.receipt_number}


@api_view(["GET"])
@permission_classes([RoleWriteAccess])
def vat_periods(request):
    vp = _vat_period(request)
    if vp == "none":
        return Response({"success": True, "data": {"vat_period": vp, "periods": [],
                                                   "message": "Kunden er ikke momsregistreret"}})
    try:
        year = int(request.query_params.get("year") or date.today().year)
    except ValueError:
        return Response({"success": False, "message": "Ugyldigt år"}, status=status.HTTP_400_BAD_REQUEST)
    returns = {(r.period_start, r.period_end): r for r in VatReturn.objects.filter(period_start__year=year)}
    out = []
    for start, end, name in vat.periods_for(year, vp):
        vr = returns.get((start, end))
        out.append({"start": start.isoformat(), "end": end.isoformat(), "name": name,
                    "deadline": vat.deadline(end, vp).isoformat(),
                    "status": vr.status if vr else "open",
                    "settled": bool(vr and vr.settlement_entry_id),
                    "momstilsvar": (vr.fields or {}).get("momstilsvar") if vr else None})
    return Response({"success": True, "data": {"vat_period": vp, "year": year, "periods": out}})


@api_view(["GET"])
@permission_classes([RoleWriteAccess])
def vat_report(request):
    start, end, err = _bounds(request)
    if err:
        return err
    result = vat.compute(start, end)
    vr = VatReturn.objects.filter(period_start=start, period_end=end).select_related("settlement_entry").first()
    return Response({"success": True, "data": {
        "start": start.isoformat(), "end": end.isoformat(),
        "deadline": vat.deadline(end, _vat_period(request)).isoformat(),
        "fields": result["fields"], "reconciliation": result["reconciliation"],
        "account_balances": vat.balances_at(end), "return": _return_dict(vr),
    }})


@api_view(["POST"])
@permission_classes([RoleWriteAccess])
def vat_settle(request):
    start, end, err = _bounds(request)
    if err:
        return err
    vr, msg = vat.settle(start, end, _user(request), on_date=_to_date(request.data.get("date")),
                         vat_period=_vat_period(request))
    if msg:
        return Response({"success": False, "message": msg}, status=status.HTTP_400_BAD_REQUEST)
    log_action(request.user, "post", "VatReturn", vr.id, {"period": f"{start}–{end}", **vr.fields})
    return Response({"success": True, "message": "Momsafregningen er bogført", "data": {"return": _return_dict(vr)}})


@api_view(["POST"])
@permission_classes([RoleWriteAccess])
def vat_unsettle(request):
    start, end, err = _bounds(request)
    if err:
        return err
    vr = VatReturn.objects.filter(period_start=start, period_end=end).first()
    msg = vat.unsettle(vr) if vr else "Der er ingen momsafregning at fjerne"
    if msg:
        return Response({"success": False, "message": msg}, status=status.HTTP_400_BAD_REQUEST)
    log_action(request.user, "unpost", "VatReturn", vr.id, {"period": f"{start}–{end}"})
    return Response({"success": True, "message": "Momsafregningen er fjernet", "data": {"return": _return_dict(vr)}})


@api_view(["POST"])
@permission_classes([RoleWriteAccess])
def vat_file(request):
    start, end, err = _bounds(request)
    if err:
        return err
    vr = VatReturn.objects.filter(period_start=start, period_end=end).first()
    msg = vat.file_return(vr, _user(request), request.data.get("receipt_number", "")) if vr else \
        "Bogfør momsafregningen før angivelsen"
    if msg:
        return Response({"success": False, "message": msg}, status=status.HTTP_400_BAD_REQUEST)
    log_action(request.user, "update", "VatReturn", vr.id,
               {"period": f"{start}–{end}", "status": "filed", "receipt_number": vr.receipt_number})
    return Response({"success": True, "message": "Perioden er angivet og låst", "data": {"return": _return_dict(vr)}})
