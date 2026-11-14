"""Løn-API (feature-gatet som "payroll" i tenancy/features.py)."""

import json
from datetime import date
from decimal import Decimal, InvalidOperation

from django.core.exceptions import ValidationError
from django.db import transaction
from django.http import HttpResponse
from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response

from core.audit import log_action
from core.permissions import RoleWriteAccess

from . import eindkomst, services
from .crypto import normalize_cpr
from .holidays import danish_holidays, working_days
from .models import Employee, PayrollLine, PayrollRun, PayrollSettings
from .pdf import payroll_list_pdf, payslips_pdf
from .rates import MissingRate, rates_for


def _err(message, code=status.HTTP_400_BAD_REQUEST):
    return Response({"success": False, "message": message}, status=code)


def _user_label(user):
    return (f"{user.first_name} {user.last_name}".strip() or user.get_username()) if user else ""


def _s(v):
    return None if v is None else str(v)


# ─── Medarbejdere ─────────────────────────────────────────────────────────────

EMP_TEXT = ("employee_number", "first_name", "last_name", "address", "email", "bank_reg", "bank_account",
            "pay_form", "tax_card", "holiday_scheme", "holiday_type", "holiday_allowance_mode",
            "pension_company", "atp_class", "notes")
EMP_DECIMAL = ("monthly_salary", "hourly_rate", "hours_per_week", "tax_rate", "deduction_month",
               "free_card_amount", "holiday_allowance_pct", "pension_employee_pct", "pension_employer_pct",
               "car_benefit_month")
EMP_DATE = ("start_date", "end_date")


def _employee_dict(e):
    d = {"id": str(e.id), "name": e.name, "cpr_masked": e.cpr_masked, "has_cpr": bool(e.cpr_last4),
         "is_active": e.is_active, "free_phone": e.free_phone, "tax_card_year": e.tax_card_year,
         "tax_card_fetched_at": e.tax_card_fetched_at.isoformat() if e.tax_card_fetched_at else None,
         "deduction_fortnight": _s(e.deduction_fortnight)}
    for f in EMP_TEXT:
        d[f] = getattr(e, f)
    for f in EMP_DECIMAL:
        d[f] = _s(getattr(e, f))
    for f in EMP_DATE:
        v = getattr(e, f)
        d[f] = v.isoformat() if v else None
    return d


def _apply_employee(emp, data):
    choices = {f.name: {c[0] for c in f.choices} for f in Employee._meta.fields if f.choices}
    for f in EMP_TEXT:
        if f in data and data[f] is not None:
            val = str(data[f]).strip()
            if f in choices and val not in choices[f]:
                raise ValidationError(f"Ugyldig værdi for {f}: {val}")
            setattr(emp, f, val)
    for f in EMP_DECIMAL:
        if f in data and data[f] not in (None, ""):
            try:
                setattr(emp, f, Decimal(str(data[f]).replace(",", ".")))
            except InvalidOperation:
                raise ValidationError(f"Ugyldigt tal i {f}") from None
    if "deduction_fortnight" in data:
        v = data["deduction_fortnight"]
        emp.deduction_fortnight = Decimal(str(v).replace(",", ".")) if v not in (None, "") else None
    for f in EMP_DATE:
        if f in data:
            setattr(emp, f, date.fromisoformat(data[f]) if data[f] else None)
    if "is_active" in data:
        emp.is_active = bool(data["is_active"])
    if "free_phone" in data:
        emp.free_phone = bool(data["free_phone"])
    if data.get("cpr"):
        emp.set_cpr(normalize_cpr(data["cpr"]))
    if emp.holiday_scheme == "feriekonto":
        emp.holiday_type = "without_pay"  # FerieKonto modtager kun feriepenge (ferie uden løn)
    if not emp.first_name or not emp.last_name:
        raise ValidationError("Fornavn og efternavn skal udfyldes.")
    if emp.end_date and emp.start_date and emp.end_date < emp.start_date:
        raise ValidationError("Fratrædelsesdato ligger før startdato.")


def _next_employee_number():
    nums = [int(n) for n in Employee.objects.values_list("employee_number", flat=True) if str(n).isdigit()]
    return str(max(nums, default=0) + 1)


@api_view(["GET", "POST"])
@permission_classes([RoleWriteAccess])
def employees_list_create(request):
    if request.method == "GET":
        qs = Employee.objects.all()
        if request.query_params.get("active") == "true":
            qs = qs.filter(is_active=True)
        return Response({"results": [_employee_dict(e) for e in qs]})
    emp = Employee(employee_number=str(request.data.get("employee_number") or _next_employee_number()))
    try:
        _apply_employee(emp, request.data)
    except (ValidationError, ValueError) as e:
        return _err(" ".join(getattr(e, "messages", [str(e)])))
    if Employee.objects.filter(employee_number=emp.employee_number).exists():
        return _err("Medarbejdernummeret er i brug.")
    emp.save()
    log_action(request.user, "create", "Employee", emp.id, {"employee_number": emp.employee_number})
    return Response({"success": True, "employee": _employee_dict(emp)}, status=status.HTTP_201_CREATED)


@api_view(["GET", "PUT", "DELETE"])
@permission_classes([RoleWriteAccess])
def employees_detail(request, pk):
    emp = Employee.objects.filter(id=pk).first()
    if emp is None:
        return _err("Medarbejderen findes ikke.", status.HTTP_404_NOT_FOUND)
    if request.method == "GET":
        return Response(_employee_dict(emp))
    if request.method == "DELETE":
        if emp.payroll_lines.exists():
            return _err("Medarbejderen har lønhistorik og kan ikke slettes. Sæt en fratrædelsesdato i stedet.")
        log_action(request.user, "delete", "Employee", emp.id, {"employee_number": emp.employee_number})
        emp.delete()
        return Response({"success": True})
    try:
        _apply_employee(emp, request.data)
    except (ValidationError, ValueError) as e:
        return _err(" ".join(getattr(e, "messages", [str(e)])))
    if Employee.objects.filter(employee_number=emp.employee_number).exclude(id=emp.id).exists():
        return _err("Medarbejdernummeret er i brug.")
    emp.save()
    changed = sorted(k for k in request.data if k != "cpr") + (["cpr"] if request.data.get("cpr") else [])
    log_action(request.user, "update", "Employee", emp.id, {"fields": changed})  # aldrig CPR i loggen
    return Response({"success": True, "employee": _employee_dict(emp)})


@api_view(["POST"])
@permission_classes([RoleWriteAccess])
def employee_fetch_tax_card(request, pk):
    emp = Employee.objects.filter(id=pk).first()
    if emp is None:
        return _err("Medarbejderen findes ikke.", status.HTTP_404_NOT_FOUND)
    year = int(request.data.get("year") or date.today().year)
    try:
        card = eindkomst.fetch_tax_card(emp.cpr, year)
    except NotImplementedError as e:
        return _err(str(e), status.HTTP_501_NOT_IMPLEMENTED)
    except ValueError as e:
        return _err(str(e))
    emp.tax_card, emp.tax_rate = card.card_type, card.rate
    emp.deduction_month, emp.deduction_fortnight = card.deduction_month, card.deduction_fortnight
    emp.free_card_amount, emp.tax_card_year = card.free_card_amount, card.year
    emp.tax_card_fetched_at = timezone.now()
    emp.save()
    log_action(request.user, "update", "Employee", emp.id, {"eskattekort": card.year, "card": card.card_type})
    return Response({"success": True, "employee": _employee_dict(emp)})


# ─── Indstillinger, helligdage, satser ────────────────────────────────────────

@api_view(["GET", "PUT"])
@permission_classes([RoleWriteAccess])
def payroll_settings(request):
    ps = PayrollSettings.get()
    if request.method == "PUT":
        if "se_number" in request.data:
            se = str(request.data["se_number"] or "").strip()
            if se and not (se.isdigit() and len(se) == 8):
                return _err("SE-nummeret skal have 8 cifre.")
            ps.se_number = se
        if "grundlovsdag" in request.data:
            if request.data["grundlovsdag"] not in ("none", "half", "full"):
                return _err("Ugyldig værdi for grundlovsdag.")
            ps.grundlovsdag = request.data["grundlovsdag"]
        ps.save()
        log_action(request.user, "update", "PayrollSettings", ps.id,
                   {"se_number": ps.se_number, "grundlovsdag": ps.grundlovsdag})
    return Response({"se_number": ps.se_number, "grundlovsdag": ps.grundlovsdag})


@api_view(["GET"])
@permission_classes([RoleWriteAccess])
def holidays_list(request):
    year = int(request.query_params.get("year") or date.today().year)
    mode = request.query_params.get("grundlovsdag") or PayrollSettings.get().grundlovsdag
    try:
        days = danish_holidays(year, mode)
    except ValueError as e:
        return _err(str(e))
    return Response({
        "year": year, "grundlovsdag": mode,
        "results": [{"date": d.isoformat(), "name": n, "share": str(s)} for d, n, s in days],
        "working_days": {m: str(working_days(year, m, mode)) for m in range(1, 13)},
    })


@api_view(["GET"])
@permission_classes([RoleWriteAccess])
def rates_view(request):
    year = int(request.query_params.get("year") or date.today().year)
    try:
        r = rates_for(year)
    except MissingRate as e:
        return _err(str(e), status.HTTP_404_NOT_FOUND)
    return Response({"year": year, "am_rate": str(r["am_rate"]), "holiday_pay_rate": str(r["holiday_pay_rate"]),
                     "holiday_allowance_rate": str(r["holiday_allowance_rate"]),
                     "free_phone_year": str(r["free_phone_year"]),
                     "atp_a_month": [[str(x) for x in row] for row in r["atp"]["A"]["month"]]})


# ─── Lønkørsler ───────────────────────────────────────────────────────────────

LINE_OUT = PayrollLine.INPUT_FIELDS + services.RESULT_FIELDS + ("tax_card", "tax_rate", "calculated")


def _line_dict(l):
    d = {"id": str(l.id), "employee_id": str(l.employee_id), "employee_number": l.employee.employee_number,
         "employee_name": l.employee.name, "pay_form": l.employee.pay_form}
    for f in LINE_OUT:
        v = getattr(l, f)
        d[f] = v if isinstance(v, (bool, list, str)) else _s(v)
    return d


RUN_TOTALS = ("total_gross", "total_benefits", "total_am", "total_a_tax", "total_atp_employee",
              "total_atp_employer", "total_pension_employee", "total_pension_employer", "total_holiday",
              "total_b_income", "total_net")


def _run_dict(run, include_lines=False):
    d = {"id": str(run.id), "frequency": run.frequency, "year": run.year, "month": run.month,
         "label": run.label, "period_start": run.period_start.isoformat(), "period_end": run.period_end.isoformat(),
         "pay_date": run.pay_date.isoformat(), "status": run.status, "is_editable": run.is_editable,
         "journal_entry_id": _s(run.journal_entry_id), "approved_by": run.approved_by,
         "approved_at": run.approved_at.isoformat() if run.approved_at else None,
         "eindkomst_status": run.eindkomst_status, "eindkomst_reference": run.eindkomst_reference,
         "eindkomst_submitted_at": run.eindkomst_submitted_at.isoformat() if run.eindkomst_submitted_at else None,
         "notes": run.notes, "created_by": run.created_by, "line_count": run.lines.count()}
    for f in RUN_TOTALS:
        d[f] = _s(getattr(run, f))
    if include_lines:
        d["lines"] = [_line_dict(l) for l in run.lines.select_related("employee")]
    return d


def _get_run(pk):
    return PayrollRun.objects.filter(id=pk).first()


@api_view(["GET", "POST"])
@permission_classes([RoleWriteAccess])
def runs_list_create(request):
    if request.method == "GET":
        qs = PayrollRun.objects.all()
        if request.query_params.get("year"):
            qs = qs.filter(year=int(request.query_params["year"]))
        return Response({"results": [_run_dict(r) for r in qs]})
    data = request.data
    today = date.today()
    try:
        frequency = data.get("frequency", "month")
        if frequency not in ("month", "fortnight"):
            raise services.PayrollError("Ugyldig lønperiode.")
        ps = date.fromisoformat(data["period_start"]) if data.get("period_start") else None
        pay_date = date.fromisoformat(data["pay_date"]) if data.get("pay_date") else None
        year, month = int(data.get("year", today.year)), int(data.get("month", today.month))
        rates_for(ps.year if ps else year)
        run = services.create_run(frequency=frequency, year=year, month=month, period_start=ps,
                                  pay_date=pay_date, created_by=_user_label(request.user))
    except (services.PayrollError, MissingRate, ValueError) as e:
        return _err(str(e))
    log_action(request.user, "create", "PayrollRun", run.id, {"period": run.label})
    return Response({"success": True, "payroll_run": _run_dict(run, True)}, status=status.HTTP_201_CREATED)


@api_view(["GET", "PUT", "DELETE"])
@permission_classes([RoleWriteAccess])
def runs_detail(request, pk):
    run = _get_run(pk)
    if run is None:
        return _err("Lønkørslen findes ikke.", status.HTTP_404_NOT_FOUND)
    if request.method == "GET":
        return Response(_run_dict(run, True))
    if not run.is_editable:
        return _err("Lønkørslen er godkendt eller bogført og kan ikke ændres.")
    if request.method == "DELETE":
        label = run.label
        run.delete()
        log_action(request.user, "delete", "PayrollRun", pk, {"period": label})
        return Response({"success": True})
    if request.data.get("pay_date"):
        run.pay_date = date.fromisoformat(request.data["pay_date"])
    if "notes" in request.data:
        run.notes = str(request.data["notes"] or "")
    run.save()
    return Response({"success": True, "payroll_run": _run_dict(run, True)})


@api_view(["PUT"])
@permission_classes([RoleWriteAccess])
def run_line_update(request, pk, line_pk):
    run = _get_run(pk)
    if run is None:
        return _err("Lønkørslen findes ikke.", status.HTTP_404_NOT_FOUND)
    line = run.lines.filter(id=line_pk).select_related("employee").first()
    if line is None:
        return _err("Lønlinjen findes ikke.", status.HTTP_404_NOT_FOUND)
    try:
        services.update_line(run, line, request.data)
    except services.PayrollError as e:
        return _err(str(e))
    run.refresh_from_db()
    return Response({"success": True, "payroll_run": _run_dict(run, True)})


def _transition(request, pk, action):
    run = _get_run(pk)
    if run is None:
        return _err("Lønkørslen findes ikke.", status.HTTP_404_NOT_FOUND)
    label = _user_label(request.user)
    try:
        with transaction.atomic():
            if action == "calculate":
                run = services.calculate_run(run)
                details = {"period": run.label, "total_net": str(run.total_net)}
            elif action == "approve":
                run = services.approve_run(run, label)
                details = {"period": run.label}
            elif action == "reopen":
                run = services.reopen_run(run)
                details = {"period": run.label}
            else:
                run, entry = services.post_run(run, label)
                details = {"period": run.label, "journal_entry": str(entry.id), "total_net": str(run.total_net)}
            log_action(request.user, action[:10], "PayrollRun", run.id, details)
    except (services.PayrollError, MissingRate, ValueError) as e:
        return _err(str(e))
    run.refresh_from_db()
    return Response({"success": True, "payroll_run": _run_dict(run, True)})


@api_view(["POST"])
@permission_classes([RoleWriteAccess])
def run_calculate(request, pk):
    return _transition(request, pk, "calculate")


@api_view(["POST"])
@permission_classes([RoleWriteAccess])
def run_approve(request, pk):
    return _transition(request, pk, "approve")


@api_view(["POST"])
@permission_classes([RoleWriteAccess])
def run_reopen(request, pk):
    return _transition(request, pk, "reopen")


@api_view(["POST"])
@permission_classes([RoleWriteAccess])
def run_post(request, pk):
    return _transition(request, pk, "post")


def _pdf(content, filename):
    resp = HttpResponse(content, content_type="application/pdf")
    resp["Content-Disposition"] = f'inline; filename="{filename}"'
    return resp


@api_view(["GET"])
@permission_classes([RoleWriteAccess])
def run_payslips(request, pk):
    run = _get_run(pk)
    if run is None:
        return _err("Lønkørslen findes ikke.", status.HTTP_404_NOT_FOUND)
    lines = run.lines.select_related("employee", "payroll_run")
    if request.query_params.get("line"):
        lines = lines.filter(id=request.query_params["line"])
    lines = list(lines)
    if not lines or not all(l.calculated for l in lines):
        return _err("Lønsedler kræver en beregnet lønkørsel.")
    return _pdf(payslips_pdf(lines), f"loenseddel-{run.label}.pdf")


@api_view(["GET"])
@permission_classes([RoleWriteAccess])
def run_payroll_list(request, pk):
    run = _get_run(pk)
    if run is None:
        return _err("Lønkørslen findes ikke.", status.HTTP_404_NOT_FOUND)
    return _pdf(payroll_list_pdf(run), f"loenliste-{run.label}.pdf")


def _can_export(request, run):
    from core.permissions import get_access
    access = get_access(request)
    if not (access and access.can_write):
        return "Eksport med CPR-numre kræver skriveadgang."
    if run.status not in ("approved", "posted"):
        return "Lønkørslen skal være godkendt, før den kan indberettes."
    return None


@api_view(["GET"])
@permission_classes([RoleWriteAccess])
def run_eindkomst_export(request, pk):
    run = _get_run(pk)
    if run is None:
        return _err("Lønkørslen findes ikke.", status.HTTP_404_NOT_FOUND)
    err = _can_export(request, run)
    if err:
        return _err(err, status.HTTP_403_FORBIDDEN if "skriveadgang" in err else status.HTTP_400_BAD_REQUEST)
    data = eindkomst.build_export(run)
    log_action(request.user, "export", "PayrollRun", run.id, {"eindkomst": run.label})
    resp = HttpResponse(json.dumps(data, ensure_ascii=False, indent=2), content_type="application/json")
    resp["Content-Disposition"] = f'attachment; filename="eindkomst-{run.label}.json"'
    return resp


@api_view(["POST"])
@permission_classes([RoleWriteAccess])
def run_eindkomst_submit(request, pk):
    run = _get_run(pk)
    if run is None:
        return _err("Lønkørslen findes ikke.", status.HTTP_404_NOT_FOUND)
    err = _can_export(request, run)
    if err:
        return _err(err)
    try:
        result = eindkomst.submit(run)
    except NotImplementedError as e:
        return _err(str(e), status.HTTP_501_NOT_IMPLEMENTED)
    run.eindkomst_status = result.status
    run.eindkomst_reference = result.reference
    if result.status == "accepted":
        run.eindkomst_submitted_at = timezone.now()
    run.save()
    log_action(request.user, "submit", "PayrollRun", run.id,
               {"eindkomst": result.status, "reference": result.reference})
    return Response({"success": result.status == "accepted", "status": result.status,
                     "reference": result.reference, "message": result.message,
                     "payroll_run": _run_dict(run)})
