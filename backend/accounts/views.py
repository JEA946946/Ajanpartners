"""Accounts app views — Auth, AccountType, Account, FiscalYear CRUD."""

import csv
import io
from decimal import Decimal

import bcrypt
from django.contrib.auth import get_user_model
from django.db import transaction
from django.db.models import Sum, Q
from rest_framework import status
from rest_framework.decorators import (
    api_view, parser_classes, permission_classes, throttle_classes,
)
from rest_framework.parsers import MultiPartParser
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.throttling import AnonRateThrottle
from rest_framework_simplejwt.tokens import RefreshToken

from core.audit import log_action
from core.permissions import RoleWriteAccess

from .models import Account, AccountType, FiscalYear
from .standardkontoplan import ARL_LINE_NAMES, classify


class AuthRateThrottle(AnonRateThrottle):
    """Per-IP throttle for auth endpoints (rate defined in settings: 10/min)."""

    scope = "auth"

User = get_user_model()


# ─── helpers ──────────────────────────────────────────────────────────────────

def _user_dict(u):
    return {
        "id": str(u.id),
        "username": u.username,
        "email": u.email,
        "first_name": u.first_name,
        "last_name": u.last_name,
        "is_staff": u.is_staff,
    }


def _account_type_dict(t):
    return {
        "id": t.id,
        "name": t.name,
        "normal_balance": t.normal_balance,
        "display_order": t.display_order,
    }


def _account_dict(a):
    return {
        "id": str(a.id),
        "code": a.code,
        "name": a.name,
        "account_type_id": a.account_type_id,
        "account_type_name": a.account_type.name if a.account_type else None,
        "normal_balance": a.account_type.normal_balance if a.account_type else None,
        "parent_id": str(a.parent_id) if a.parent_id else None,
        "currency": a.currency,
        "standard_code": a.standard_code,
        "arl_line": a.arl_line,
        "arl_line_name": ARL_LINE_NAMES.get(a.arl_line, ""),
        "is_header": a.is_header,
        "description": a.description,
        "is_active": a.is_active,
        "manager_io_id": a.manager_io_id,
        "created_at": a.created_at.isoformat() if a.created_at else None,
        "updated_at": a.updated_at.isoformat() if a.updated_at else None,
    }


def _iso(value):
    """A date (or an ISO string not yet parsed after create) as ISO text."""
    if not value:
        return None
    return value.isoformat() if hasattr(value, "isoformat") else str(value)


def _standard_fields(code, parent, data):
    """standard_code and arl_line for a new or changed account: given, else the
    parent's, else from the number itself when it lies in the standard chart."""
    std = (data.get("standard_code") or "").strip()
    if not std and parent is not None:
        std = parent.standard_code
    arl = (data.get("arl_line") or "").strip()
    if not arl:
        for candidate in (std, code):
            try:
                arl = classify(candidate)[0]
                break
            except (ValueError, TypeError):
                continue
    if not arl and parent is not None:
        arl = parent.arl_line
    if arl and arl not in ARL_LINE_NAMES:
        return None, None, f"Ukendt ÅRL-linje: {arl}"
    return std, arl, None


def _fiscal_year_dict(fy):
    return {
        "id": str(fy.id),
        "name": fy.name,
        "start_date": _iso(fy.start_date),
        "end_date": _iso(fy.end_date),
        "is_closed": fy.is_closed,
        "closed_at": fy.closed_at.isoformat() if fy.closed_at else None,
        "closed_by": fy.closed_by,
        "created_at": fy.created_at.isoformat() if fy.created_at else None,
    }


# ─── Auth ─────────────────────────────────────────────────────────────────────

def _find_login_user(identifier):
    """Resolve the login field to a user: username first, then email (both
    case-insensitive). Email isn't unique on the user table, so it only matches
    when exactly one account has it — a shared address stays username-only."""
    identifier = str(identifier).strip()
    user = User.objects.filter(username__iexact=identifier).first()
    if user is not None or "@" not in identifier:
        return user
    matches = list(User.objects.filter(email__iexact=identifier)[:2])
    return matches[0] if len(matches) == 1 else None


@api_view(["POST"])
@permission_classes([AllowAny])
@throttle_classes([AuthRateThrottle])
def login(request):
    username = request.data.get("username")
    password = request.data.get("password")
    if not username or not password:
        return Response(
            {"success": False, "message": "Username and password required"},
            status=status.HTTP_400_BAD_REQUEST,
        )
    user = _find_login_user(username)
    if user is None:
        return Response(
            {"success": False, "message": "Invalid credentials"},
            status=status.HTTP_401_UNAUTHORIZED,
        )
    if not user.is_active:
        return Response(
            {"success": False, "message": "Account is inactive"},
            status=status.HTTP_401_UNAUTHORIZED,
        )

    stored_hash = user.password
    valid = False
    if stored_hash and stored_hash.startswith(("$2b$", "$2a$")):
        valid = bcrypt.checkpw(password.encode("utf-8"), stored_hash.encode("utf-8"))
    else:
        valid = user.check_password(password)

    if not valid:
        return Response(
            {"success": False, "message": "Invalid credentials"},
            status=status.HTTP_401_UNAUTHORIZED,
        )

    refresh = RefreshToken.for_user(user)
    return Response({
        "success": True,
        "message": "Login successful",
        "data": {
            "user": _user_dict(user),
            "token": str(refresh.access_token),
            "refreshToken": str(refresh),
        },
    })


@api_view(["POST"])
@permission_classes([AllowAny])
@throttle_classes([AuthRateThrottle])
def refresh_token(request):
    token = request.data.get("refreshToken")
    if not token:
        return Response(
            {"success": False, "message": "Refresh token required"},
            status=status.HTTP_400_BAD_REQUEST,
        )
    try:
        refresh = RefreshToken(token)
        return Response({
            "success": True,
            "data": {
                "token": str(refresh.access_token),
                "refreshToken": str(refresh),
            },
        })
    except Exception:
        return Response(
            {"success": False, "message": "Invalid refresh token"},
            status=status.HTTP_401_UNAUTHORIZED,
        )


@api_view(["GET"])
@permission_classes([IsAuthenticated])  # public: kræver ingen valgt kunde (bruges ved genindlæsning)
def profile(request):
    return Response({
        "success": True,
        "data": {"user": _user_dict(request.user)},
    })


# ─── Account Types ────────────────────────────────────────────────────────────

@api_view(["GET"])
@permission_classes([RoleWriteAccess])
def account_types_list(request):
    types = AccountType.objects.all()
    return Response({
        "success": True,
        "data": {"account_types": [_account_type_dict(t) for t in types]},
    })


# ─── Accounts CRUD ────────────────────────────────────────────────────────────

@api_view(["GET", "POST"])
@permission_classes([RoleWriteAccess])
def accounts_list_create(request):
    if request.method == "GET":
        qs = Account.objects.select_related("account_type", "parent")
        if request.query_params.get("is_active"):
            qs = qs.filter(is_active=request.query_params["is_active"].lower() == "true")
        if request.query_params.get("type_id"):
            qs = qs.filter(account_type_id=request.query_params["type_id"])
        return Response({
            "success": True,
            "data": {"accounts": [_account_dict(a) for a in qs]},
        })

    # POST — create
    data = request.data
    required = ["code", "name", "account_type_id"]
    for field in required:
        if not data.get(field):
            return Response(
                {"success": False, "message": f"{field} is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )
    if Account.objects.filter(code=data["code"]).exists():
        return Response(
            {"success": False, "message": f"Account code {data['code']} already exists"},
            status=status.HTTP_400_BAD_REQUEST,
        )
    try:
        account_type = AccountType.objects.get(id=data["account_type_id"])
    except AccountType.DoesNotExist:
        return Response(
            {"success": False, "message": "Invalid account type"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    parent = None
    if data.get("parent_id"):
        try:
            parent = Account.objects.get(id=data["parent_id"])
        except Account.DoesNotExist:
            return Response(
                {"success": False, "message": "Invalid parent account"},
                status=status.HTTP_400_BAD_REQUEST,
            )

    if parent is not None and not parent.is_header:
        return Response({"success": False, "message": "Overkontoen skal være en overskrift (gruppekonto)"},
                        status=status.HTTP_400_BAD_REQUEST)
    std, arl, err = _standard_fields(data["code"], parent, data)
    if err:
        return Response({"success": False, "message": err}, status=status.HTTP_400_BAD_REQUEST)
    account = Account.objects.create(
        code=data["code"],
        name=data["name"],
        account_type=account_type,
        parent=parent,
        currency=data.get("currency", "DKK"),
        standard_code=std,
        arl_line=arl,
        is_header=bool(data.get("is_header", False)),
        description=data.get("description", ""),
        is_active=data.get("is_active", True),
    )
    log_action(request.user, "create", "Account", account.id,
               {"code": account.code, "name": account.name})
    return Response({
        "success": True,
        "message": "Account created",
        "data": {"account": _account_dict(account)},
    }, status=status.HTTP_201_CREATED)


@api_view(["GET", "PUT", "DELETE"])
@permission_classes([RoleWriteAccess])
def accounts_detail(request, pk):
    try:
        account = Account.objects.select_related("account_type", "parent").get(id=pk)
    except Account.DoesNotExist:
        return Response(
            {"success": False, "message": "Account not found"},
            status=status.HTTP_404_NOT_FOUND,
        )

    if request.method == "GET":
        return Response({
            "success": True,
            "data": {"account": _account_dict(account)},
        })

    if request.method == "PUT":
        data = request.data
        if "code" in data and data["code"] != account.code:
            if Account.objects.filter(code=data["code"]).exclude(id=pk).exists():
                return Response(
                    {"success": False, "message": "Account code already exists"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            account.code = data["code"]
        if "name" in data:
            account.name = data["name"]
        if "account_type_id" in data:
            try:
                account.account_type = AccountType.objects.get(id=data["account_type_id"])
            except AccountType.DoesNotExist:
                return Response(
                    {"success": False, "message": "Invalid account type"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
        if "parent_id" in data:
            if data["parent_id"]:
                try:
                    account.parent = Account.objects.get(id=data["parent_id"])
                except Account.DoesNotExist:
                    return Response(
                        {"success": False, "message": "Invalid parent account"},
                        status=status.HTTP_400_BAD_REQUEST,
                    )
            else:
                account.parent = None
        for field in ("currency", "description", "is_active", "manager_io_id"):
            if field in data:
                setattr(account, field, data[field])
        if "standard_code" in data or "arl_line" in data:
            std, arl, err = _standard_fields(account.code, account.parent, {
                "standard_code": data.get("standard_code", account.standard_code),
                "arl_line": data.get("arl_line", account.arl_line)})
            if err:
                return Response({"success": False, "message": err}, status=status.HTTP_400_BAD_REQUEST)
            account.standard_code, account.arl_line = std, arl
        account.save()
        log_action(request.user, "update", "Account", account.id,
                   {"code": account.code, "name": account.name})
        return Response({
            "success": True,
            "message": "Account updated",
            "data": {"account": _account_dict(account)},
        })

    # DELETE — soft delete
    account.is_active = False
    account.save()
    log_action(request.user, "deactivate", "Account", account.id, {"code": account.code})
    return Response({"success": True, "message": "Account deactivated"})


@api_view(["GET"])
@permission_classes([RoleWriteAccess])
def account_ledger(request, pk):
    """Return journal entry lines for a specific account."""
    from journals.models import JournalEntryLine

    try:
        account = Account.objects.get(id=pk)
    except Account.DoesNotExist:
        return Response(
            {"success": False, "message": "Account not found"},
            status=status.HTTP_404_NOT_FOUND,
        )

    qs = JournalEntryLine.objects.filter(
        account=account,
        journal_entry__is_posted=True,
    ).select_related("journal_entry").order_by("journal_entry__date", "journal_entry__entry_number")

    date_from = request.query_params.get("date_from")
    date_to = request.query_params.get("date_to")
    if date_from:
        qs = qs.filter(journal_entry__date__gte=date_from)
    if date_to:
        qs = qs.filter(journal_entry__date__lte=date_to)

    lines = []
    # Accumulate in Decimal — binary float drifts on money (e.g. 0.10 is inexact) and
    # this balance is shown to accountants as the account balance.
    running_balance = Decimal("0")
    is_debit_normal = account.account_type.normal_balance == "debit"
    for line in qs:
        debit = line.debit or Decimal("0")
        credit = line.credit or Decimal("0")
        # Debet/kredit er altid DKK; et beløb i fremmed valuta vises ved siden af.
        if is_debit_normal:
            running_balance += debit - credit
        else:
            running_balance += credit - debit
        lines.append({
            "id": str(line.id),
            "date": line.journal_entry.date.isoformat(),
            "entry_number": line.journal_entry.entry_number,
            "description": line.journal_entry.description,
            "debit": str(line.debit),
            "credit": str(line.credit),
            "currency": line.currency,
            "amount_currency": str(line.amount_currency) if line.amount_currency is not None else None,
            "exchange_rate": str(line.exchange_rate),
            "running_balance": f"{running_balance:.2f}",
        })

    totals = qs.aggregate(total_debit=Sum("debit"), total_credit=Sum("credit"))
    return Response({
        "success": True,
        "data": {
            "account": _account_dict(account),
            "lines": lines,
            "total_debit": str(totals["total_debit"] or 0),
            "total_credit": str(totals["total_credit"] or 0),
        },
    })


# ─── Fiscal Years CRUD ────────────────────────────────────────────────────────

@api_view(["GET", "POST"])
@permission_classes([RoleWriteAccess])
def fiscal_years_list_create(request):
    if request.method == "GET":
        years = FiscalYear.objects.all()
        return Response({
            "success": True,
            "data": {"fiscal_years": [_fiscal_year_dict(fy) for fy in years]},
        })

    data = request.data
    for field in ("name", "start_date", "end_date"):
        if not data.get(field):
            return Response(
                {"success": False, "message": f"{field} is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

    from journals.periods import _to_date
    start, end = _to_date(data["start_date"]), _to_date(data["end_date"])
    if not start or not end or end < start:
        return Response({"success": False, "message": "Ugyldig periode: start_date og end_date (åååå-mm-dd)"},
                        status=status.HTTP_400_BAD_REQUEST)
    if FiscalYear.objects.filter(start_date__lte=end, end_date__gte=start).exists():
        return Response({"success": False, "message": "Perioden overlapper et eksisterende regnskabsår"},
                        status=status.HTTP_400_BAD_REQUEST)
    fy = FiscalYear.objects.create(name=data["name"], start_date=start, end_date=end)
    log_action(request.user, "create", "FiscalYear", fy.id,
               {"name": fy.name, "start_date": str(fy.start_date), "end_date": str(fy.end_date)})
    return Response({
        "success": True,
        "message": "Fiscal year created",
        "data": {"fiscal_year": _fiscal_year_dict(fy)},
    }, status=status.HTTP_201_CREATED)


@api_view(["PUT", "DELETE"])
@permission_classes([RoleWriteAccess])
def fiscal_years_detail(request, pk):
    try:
        fy = FiscalYear.objects.get(id=pk)
    except FiscalYear.DoesNotExist:
        return Response(
            {"success": False, "message": "Fiscal year not found"},
            status=status.HTTP_404_NOT_FOUND,
        )

    # Et afsluttet år er endeligt (Bogføringsloven). Det lukkes kun gennem
    # årsafslutningen (year-end/...), som bogfører resultatet og primoposteringerne.
    if fy.is_closed:
        return Response(
            {"success": False, "message": f"Fiscal year {fy.name} is closed and cannot be changed or deleted"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    if request.method == "PUT":
        data = request.data
        from journals.periods import _to_date
        if "name" in data:
            fy.name = data["name"]
        for field in ("start_date", "end_date"):
            if field in data:
                value = _to_date(data[field])
                if value is None:
                    return Response({"success": False, "message": f"Ugyldig {field}"},
                                    status=status.HTTP_400_BAD_REQUEST)
                setattr(fy, field, value)
        if fy.end_date < fy.start_date:
            return Response({"success": False, "message": "Slutdato før startdato"},
                            status=status.HTTP_400_BAD_REQUEST)
        fy.save()
        log_action(request.user, "update", "FiscalYear", fy.id, {"name": fy.name})
        return Response({
            "success": True,
            "message": "Fiscal year updated",
            "data": {"fiscal_year": _fiscal_year_dict(fy)},
        })

    fy_name = fy.name
    fy.delete()
    log_action(request.user, "delete", "FiscalYear", pk, {"name": fy_name})
    return Response({"success": True, "message": "Fiscal year deleted"})


# ─── Account Import ──────────────────────────────────────────────────────────

@api_view(["POST"])
@permission_classes([RoleWriteAccess])
@parser_classes([MultiPartParser])
def accounts_import_preview(request):
    """Parse uploaded CSV and return preview with duplicate detection."""
    f = request.FILES.get("file")
    if not f:
        return Response({"success": False, "message": "No file uploaded"}, status=400)

    try:
        text = f.read().decode("utf-8-sig")
    except UnicodeDecodeError:
        return Response({"success": False, "message": "File must be UTF-8 encoded"}, status=400)

    reader = csv.DictReader(io.StringIO(text))
    if not reader.fieldnames:
        return Response({"success": False, "message": "Empty or invalid CSV"}, status=400)

    existing_codes = {a.code: a for a in Account.objects.all()}
    account_types_by_name = {
        at.name.lower(): at for at in AccountType.objects.all()
    }
    rows = []

    for i, row in enumerate(reader, start=1):
        code = (row.get("code") or "").strip()
        name = (row.get("name") or "").strip()
        account_type_name = (row.get("account_type") or "").strip()
        parent_code = (row.get("parent_code") or "").strip()
        currency = (row.get("currency") or "DKK").strip().upper()
        description = (row.get("description") or "").strip()

        errors = []
        if not name:
            errors.append("name is required")
        if not code:
            errors.append("code is required")

        # Validate account_type
        resolved_type_id = None
        if account_type_name:
            at = account_types_by_name.get(account_type_name.lower())
            if at:
                resolved_type_id = at.id
            else:
                errors.append(f"unknown account_type: {account_type_name}")
        else:
            errors.append("account_type is required")

        # Validate parent_code
        resolved_parent_id = None
        if parent_code:
            parent = existing_codes.get(parent_code)
            if parent:
                resolved_parent_id = str(parent.id)
            else:
                # Parent might be in the import itself — we'll check later
                # For preview, just flag a warning if it doesn't exist yet
                errors.append(f"parent_code '{parent_code}' not found (may be created during import)")
                # Downgrade from error - the confirm step handles ordering
                errors = [e for e in errors if "parent_code" not in e]

        row_status = "new"
        existing_id = None
        if errors:
            row_status = "error"
        elif code in existing_codes:
            row_status = "duplicate"
            existing_id = str(existing_codes[code].id)

        rows.append({
            "row_number": i,
            "status": row_status,
            "existing_id": existing_id,
            "errors": errors,
            "data": {
                "code": code,
                "name": name,
                "account_type": account_type_name,
                "account_type_id": resolved_type_id,
                "parent_code": parent_code,
                "parent_id": resolved_parent_id,
                "currency": currency or "DKK",
                "description": description,
            },
        })

    summary = {
        "new": sum(1 for r in rows if r["status"] == "new"),
        "duplicate": sum(1 for r in rows if r["status"] == "duplicate"),
        "error": sum(1 for r in rows if r["status"] == "error"),
        "total": len(rows),
    }

    return Response({"success": True, "rows": rows, "summary": summary})


@api_view(["POST"])
@permission_classes([RoleWriteAccess])
def accounts_import_confirm(request):
    """Create or update accounts from previewed data."""
    rows = request.data.get("rows", [])
    update_existing = request.data.get("update_existing", False)

    # Sort by code length to create parent accounts before children
    rows = sorted(rows, key=lambda r: len(r.get("data", {}).get("code", "")))

    account_types_by_name = {
        at.name.lower(): at for at in AccountType.objects.all()
    }

    created = 0
    updated = 0
    errors = []

    with transaction.atomic():
        for r in rows:
            if r.get("status") == "error":
                continue

            data = r.get("data", {})
            code = data.get("code", "").strip()
            name = data.get("name", "").strip()
            if not code or not name:
                continue

            # Resolve account type
            at_name = data.get("account_type", "").strip().lower()
            account_type = account_types_by_name.get(at_name)
            if not account_type:
                errors.append(f"Row {r.get('row_number')}: unknown account_type")
                continue

            # Resolve parent
            parent = None
            parent_code = data.get("parent_code", "").strip()
            if parent_code:
                try:
                    parent = Account.objects.get(code=parent_code)
                except Account.DoesNotExist:
                    errors.append(f"Row {r.get('row_number')}: parent_code '{parent_code}' not found")
                    continue

            if r.get("status") == "duplicate" and update_existing and r.get("existing_id"):
                try:
                    account = Account.objects.get(id=r["existing_id"])
                    account.name = name
                    account.account_type = account_type
                    account.parent = parent
                    account.currency = data.get("currency", "DKK")
                    if data.get("description"):
                        account.description = data["description"]
                    account.save()
                    updated += 1
                except Account.DoesNotExist:
                    errors.append(f"Row {r.get('row_number')}: account not found")
            elif r.get("status") == "new":
                Account.objects.create(
                    code=code,
                    name=name,
                    account_type=account_type,
                    parent=parent,
                    currency=data.get("currency", "DKK"),
                    description=data.get("description", ""),
                )
                created += 1

    return Response({
        "success": True,
        "created": created,
        "updated": updated,
        "errors": errors,
    })
