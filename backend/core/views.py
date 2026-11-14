"""Core views: TaxCodes, Payments, BankRules, BankReconciliation, Projects,
Documents, Reports, AuditLog, CompanySettings, UserRoles."""

import hashlib
import re
import secrets
from datetime import datetime
from decimal import Decimal

from django.conf import settings
from django.contrib.auth.models import User
from django.db import transaction
from django.db.models import Sum, Q, F
from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import api_view, parser_classes, permission_classes
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.response import Response

from core.permissions import IsAdmin, RoleWriteAccess
from core.uploads import validate_upload

from accounts import chart
from accounts.models import Account, AccountType
from journals.models import JournalEntry, JournalEntryLine
from sales.models import Customer, Invoice
from purchases.models import Supplier, Bill
from .models import (
    TaxCode, Payment, PaymentAllocation, BankRule, BankReconciliation,
    BankReconciliationLine, Project, ProjectTransaction, Document,
    AuditLog, CompanySettings, UserRole,
)


# =============================================================================
# Helpers
# =============================================================================

# Re-exported so the existing ~20 call sites in this module (and any external
# importer) keep working; the implementation lives in core.audit so other apps
# can log actions without importing core.views.
from core.audit import log_action  # noqa: E402

from journals.periods import closed_period_error  # noqa: E402


def _get_client_ip(request):
    """Extract client IP from request."""
    xff = request.META.get("HTTP_X_FORWARDED_FOR")
    if xff:
        return xff.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR")


# ── Serialisation helpers ────────────────────────────────────────────────────

def _tax_code_dict(tc):
    return {
        "id": str(tc.id),
        "code": tc.code,
        "name": tc.name,
        "rate": str(tc.rate),
        "type": tc.type,
        "account_id": str(tc.account_id),
        "account_code": tc.account.code if tc.account else None,
        "account_name": tc.account.name if tc.account else None,
        "is_active": tc.is_active,
    }


def _allocation_dict(alloc):
    return {
        "id": str(alloc.id),
        "payment_id": str(alloc.payment_id),
        "content_type": alloc.content_type,
        "object_id": str(alloc.object_id),
        "amount": str(alloc.amount),
    }


def _payment_dict(payment, include_allocations=True):
    d = {
        "id": str(payment.id),
        "payment_number": payment.payment_number,
        "type": payment.type,
        "date": payment.date.isoformat() if payment.date else None,
        "amount": str(payment.amount),
        "currency": payment.currency,
        "method": payment.method,
        "reference": payment.reference,
        "bank_account_id": str(payment.bank_account_id) if payment.bank_account_id else None,
        "bank_account_code": payment.bank_account.code if payment.bank_account else None,
        "customer_id": str(payment.customer_id) if payment.customer_id else None,
        "customer_name": payment.customer.name if payment.customer else None,
        "supplier_id": str(payment.supplier_id) if payment.supplier_id else None,
        "supplier_name": payment.supplier.name if payment.supplier else None,
        "journal_entry_id": str(payment.journal_entry_id) if payment.journal_entry_id else None,
        "notes": payment.notes,
        "created_by": payment.created_by,
        "created_at": payment.created_at.isoformat() if payment.created_at else None,
    }
    if include_allocations:
        d["allocations"] = [
            _allocation_dict(a)
            for a in payment.allocations.all()
        ]
    return d


def _bank_rule_dict(rule):
    return {
        "id": str(rule.id),
        "pattern": rule.pattern,
        "match_type": rule.match_type,
        "match_field": rule.match_field,
        "account_id": str(rule.account_id),
        "account_code": rule.account.code if rule.account else None,
        "account_name": rule.account.name if rule.account else None,
        "description_template": rule.description_template,
        "priority": rule.priority,
        "is_active": rule.is_active,
        "created_at": rule.created_at.isoformat() if rule.created_at else None,
    }


def _recon_line_dict(line):
    jl = line.journal_line
    je = jl.journal_entry
    # Use line description if set, otherwise fall back to journal entry description
    description = jl.description or je.description or ""
    entry_date = je.date.isoformat() if je.date else None
    return {
        "id": str(line.id),
        "journal_line_id": str(jl.id),
        "account_id": str(jl.account_id),
        "account_code": jl.account.code,
        "account_name": jl.account.name,
        "debit": str(jl.debit),
        "credit": str(jl.credit),
        "description": description,
        "reference": je.reference or "",
        "entry_number": je.entry_number,
        "date": entry_date,
        "entry_date": entry_date,
        "is_matched": line.is_matched,
        "matched_at": line.matched_at.isoformat() if line.matched_at else None,
    }


def _reconciliation_dict(recon, include_lines=True):
    d = {
        "id": str(recon.id),
        "bank_account_id": str(recon.bank_account_id),
        "bank_account_code": recon.bank_account.code if recon.bank_account else None,
        "bank_account_name": recon.bank_account.name if recon.bank_account else None,
        "date": recon.date.isoformat() if recon.date else None,
        "statement_balance": str(recon.statement_balance),
        "status": recon.status,
        "completed_at": recon.completed_at.isoformat() if recon.completed_at else None,
        "completed_by": recon.completed_by,
        "created_at": recon.created_at.isoformat() if recon.created_at else None,
    }
    if include_lines:
        lines = recon.lines.select_related(
            "journal_line__account",
            "journal_line__journal_entry",
        ).all()
        d["lines"] = [_recon_line_dict(l) for l in lines]
        d["matched_count"] = sum(1 for l in lines if l.is_matched)
        d["unmatched_count"] = sum(1 for l in lines if not l.is_matched)
    else:
        # Always include counts even in list view
        d["matched_count"] = recon.lines.filter(is_matched=True).count()
        d["unmatched_count"] = recon.lines.filter(is_matched=False).count()
    return d


def _project_dict(project):
    return {
        "id": str(project.id),
        "code": project.code,
        "name": project.name,
        "customer_id": str(project.customer_id) if project.customer_id else None,
        "customer_name": project.customer.name if project.customer else None,
        "status": project.status,
        "start_date": project.start_date.isoformat() if project.start_date else None,
        "end_date": project.end_date.isoformat() if project.end_date else None,
        "budget": str(project.budget),
        "notes": project.notes,
        "created_by": project.created_by,
        "created_at": project.created_at.isoformat() if project.created_at else None,
        "updated_at": project.updated_at.isoformat() if project.updated_at else None,
    }


def _project_txn_dict(txn):
    jl = txn.journal_line
    return {
        "id": str(txn.id),
        "project_id": str(txn.project_id),
        "journal_line_id": str(jl.id),
        "account_id": str(jl.account_id),
        "account_code": jl.account.code,
        "account_name": jl.account.name,
        "debit": str(jl.debit),
        "credit": str(jl.credit),
        "description": jl.description,
        "entry_number": jl.journal_entry.entry_number,
        "entry_date": jl.journal_entry.date.isoformat() if jl.journal_entry.date else None,
        "created_at": txn.created_at.isoformat() if txn.created_at else None,
    }


def _document_dict(doc):
    return {
        "id": str(doc.id),
        "file": doc.file.url if doc.file else None,
        "filename": doc.filename,
        "description": doc.description,
        "piece_number": doc.piece_number,
        "sha256": doc.sha256,
        "size": doc.size,
        "journal_entry_id": str(doc.journal_entry_id) if doc.journal_entry_id else None,
        "invoice_id": str(doc.invoice_id) if doc.invoice_id else None,
        "bill_id": str(doc.bill_id) if doc.bill_id else None,
        "expense_id": str(doc.expense_id) if doc.expense_id else None,
        "uploaded_by": doc.uploaded_by,
        "uploaded_at": doc.uploaded_at.isoformat() if doc.uploaded_at else None,
    }


def _audit_log_dict(log):
    return {
        "id": str(log.id),
        "user_id": str(log.user_id) if log.user_id else None,
        "username": log.user.username if log.user else None,
        "action": log.action,
        "model_name": log.model_name,
        "record_id": log.record_id,
        "seq": log.seq,
        "hash": log.hash,
        "changes": log.changes,
        "timestamp": log.timestamp.isoformat() if log.timestamp else None,
        "ip_address": log.ip_address,
    }


def _settings_dict(settings_obj):
    return {
        "id": str(settings_obj.id),
        "company_name": settings_obj.company_name,
        "address": settings_obj.address,
        "city": settings_obj.city,
        "country": settings_obj.country,
        "tax_id": settings_obj.tax_id,
        "phone": settings_obj.phone,
        "email": settings_obj.email,
        "currency": settings_obj.currency,
        "fiscal_year_start_month": settings_obj.fiscal_year_start_month,
        "date_format": settings_obj.date_format,
        "logo": settings_obj.logo.url if settings_obj.logo else None,
        "logo1": settings_obj.logo1,
        "logo2": settings_obj.logo2,
        "logo3": settings_obj.logo3,
    }


def _membership(user, tenant):
    from tenancy.models import ClientMembership
    return ClientMembership.objects.filter(user=user, client=tenant).first()


def _user_dict(user, tenant=None):
    m = _membership(user, tenant) if tenant is not None else None
    return {
        "id": str(user.id),
        "username": user.username,
        "email": user.email,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "is_active": bool(user.is_active and (m.is_active if m else True)),
        "role": m.role if m else None,
    }


def _client_users(tenant):
    """Kun kundens egne brugere. Revisorhusets medarbejdere styres i admin-portalen."""
    return User.objects.filter(memberships__client=tenant).distinct()


def _owned_only_by(user, tenant):
    """True when the user belongs to this client alone (no other client, not firm
    staff), so this client's admin may change its login and password."""
    from tenancy.models import ClientMembership, FirmStaff
    if FirmStaff.objects.filter(user=user).exists() or user.is_superuser:
        return False
    return not ClientMembership.objects.filter(user=user).exclude(client=tenant).exists()


# =============================================================================
# 1-2  Tax Codes
# =============================================================================

@api_view(["GET", "POST"])
@permission_classes([RoleWriteAccess])
def tax_codes_list_create(request):
    if request.method == "GET":
        qs = TaxCode.objects.select_related("account").all()
        return Response({
            "success": True,
            "data": {"tax_codes": [_tax_code_dict(tc) for tc in qs]},
        })

    # POST
    data = request.data
    for field in ("code", "name", "rate", "account_id"):
        if not data.get(field):
            return Response(
                {"success": False, "message": f"{field} is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

    if TaxCode.objects.filter(code=data["code"]).exists():
        return Response(
            {"success": False, "message": f"Tax code '{data['code']}' already exists"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    try:
        account = Account.objects.get(id=data["account_id"])
    except Account.DoesNotExist:
        return Response(
            {"success": False, "message": "Account not found"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    tc = TaxCode.objects.create(
        code=data["code"],
        name=data["name"],
        rate=Decimal(str(data["rate"])),
        type=data.get("type", "both"),
        account=account,
        is_active=data.get("is_active", True),
    )
    log_action(request.user, "create", "TaxCode", tc.id, ip=_get_client_ip(request))
    return Response({
        "success": True,
        "message": "Tax code created",
        "data": {"tax_code": _tax_code_dict(tc)},
    }, status=status.HTTP_201_CREATED)


@api_view(["GET", "PUT", "DELETE"])
@permission_classes([RoleWriteAccess])
def tax_codes_detail(request, pk):
    try:
        tc = TaxCode.objects.select_related("account").get(id=pk)
    except TaxCode.DoesNotExist:
        return Response(
            {"success": False, "message": "Tax code not found"},
            status=status.HTTP_404_NOT_FOUND,
        )

    if request.method == "GET":
        return Response({
            "success": True,
            "data": {"tax_code": _tax_code_dict(tc)},
        })

    if request.method == "PUT":
        data = request.data
        if "code" in data and data["code"] != tc.code:
            if TaxCode.objects.filter(code=data["code"]).exclude(id=pk).exists():
                return Response(
                    {"success": False, "message": "Tax code already exists"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            tc.code = data["code"]
        if "name" in data:
            tc.name = data["name"]
        if "rate" in data:
            tc.rate = Decimal(str(data["rate"]))
        if "type" in data:
            tc.type = data["type"]
        if "account_id" in data:
            try:
                tc.account = Account.objects.get(id=data["account_id"])
            except Account.DoesNotExist:
                return Response(
                    {"success": False, "message": "Account not found"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
        if "is_active" in data:
            tc.is_active = data["is_active"]
        tc.save()
        log_action(request.user, "update", "TaxCode", tc.id, ip=_get_client_ip(request))
        return Response({
            "success": True,
            "message": "Tax code updated",
            "data": {"tax_code": _tax_code_dict(tc)},
        })

    # DELETE
    tc.is_active = False
    tc.save()
    log_action(request.user, "delete", "TaxCode", tc.id, ip=_get_client_ip(request))
    return Response({"success": True, "message": "Tax code deactivated"})


# =============================================================================
# 3-5  Payments
# =============================================================================

@api_view(["GET", "POST"])
@permission_classes([RoleWriteAccess])
def payments_list_create(request):
    if request.method == "GET":
        qs = Payment.objects.select_related(
            "bank_account", "customer", "supplier", "journal_entry",
        ).prefetch_related("allocations")

        if request.query_params.get("type"):
            qs = qs.filter(type=request.query_params["type"])
        if request.query_params.get("date_from"):
            qs = qs.filter(date__gte=request.query_params["date_from"])
        if request.query_params.get("date_to"):
            qs = qs.filter(date__lte=request.query_params["date_to"])
        if request.query_params.get("customer_id"):
            qs = qs.filter(customer_id=request.query_params["customer_id"])
        if request.query_params.get("supplier_id"):
            qs = qs.filter(supplier_id=request.query_params["supplier_id"])

        return Response({
            "success": True,
            "data": {"payments": [_payment_dict(p) for p in qs]},
        })

    # POST - create payment. Money in and out of a bank is booked once, from the
    # bank statement: the bank line is matched to the invoice or bill on Bank
    # transactions. A payment booked here as well counted it twice.
    return Response(
        {"success": False, "message": (
            "Payments are booked from the bank statement: match the bank line to the invoice "
            "or bill on Bank transactions.")},
        status=status.HTTP_400_BAD_REQUEST,
    )


@api_view(["GET", "PUT", "DELETE"])
@permission_classes([RoleWriteAccess])
def payments_detail(request, pk):
    try:
        payment = Payment.objects.select_related(
            "bank_account", "customer", "supplier", "journal_entry",
        ).prefetch_related("allocations").get(id=pk)
    except Payment.DoesNotExist:
        return Response(
            {"success": False, "message": "Payment not found"},
            status=status.HTTP_404_NOT_FOUND,
        )

    if request.method == "GET":
        return Response({
            "success": True,
            "data": {"payment": _payment_dict(payment)},
        })

    if request.method == "PUT":
        data = request.data
        # Amount, date and bank are in the posted entry and in the allocations to
        # invoices/bills. Changing them here left the ledger and the paid amounts
        # as they were, so once either exists they are fixed: delete the payment
        # (which unwinds both) and enter it again.
        locked = payment.journal_entry_id is not None or payment.allocations.exists()
        ledger_change = (
            ("amount" in data and Decimal(str(data["amount"])) != payment.amount)
            or ("date" in data and str(data["date"])[:10] != str(payment.date)[:10])
            or ("bank_account_id" in data and str(data["bank_account_id"] or "") != str(payment.bank_account_id or ""))
        )
        if locked and ledger_change:
            return Response(
                {"success": False, "message": "This payment is posted or allocated — its amount, date and "
                 "bank cannot be changed. Delete it and enter it again."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if "date" in data:
            err = closed_period_error(data["date"])
            if err:
                return Response({"success": False, "message": err}, status=status.HTTP_400_BAD_REQUEST)
        for field in ("date", "amount", "currency", "method", "reference", "notes"):
            if field in data:
                if field == "amount":
                    payment.amount = Decimal(str(data[field]))
                else:
                    setattr(payment, field, data[field])
        if "bank_account_id" in data:
            if data["bank_account_id"]:
                try:
                    payment.bank_account = Account.objects.get(id=data["bank_account_id"])
                except Account.DoesNotExist:
                    return Response(
                        {"success": False, "message": "Bank account not found"},
                        status=status.HTTP_400_BAD_REQUEST,
                    )
            else:
                payment.bank_account = None
        if "customer_id" in data:
            if data["customer_id"]:
                try:
                    payment.customer = Customer.objects.get(id=data["customer_id"])
                except Customer.DoesNotExist:
                    return Response(
                        {"success": False, "message": "Customer not found"},
                        status=status.HTTP_400_BAD_REQUEST,
                    )
            else:
                payment.customer = None
        if "supplier_id" in data:
            if data["supplier_id"]:
                try:
                    payment.supplier = Supplier.objects.get(id=data["supplier_id"])
                except Supplier.DoesNotExist:
                    return Response(
                        {"success": False, "message": "Supplier not found"},
                        status=status.HTTP_400_BAD_REQUEST,
                    )
            else:
                payment.supplier = None
        payment.save()
        log_action(request.user, "update", "Payment", payment.id, ip=_get_client_ip(request))
        return Response({
            "success": True,
            "message": "Payment updated",
            "data": {"payment": _payment_dict(payment)},
        })

    # DELETE — unwind what the payment did: take its allocations back off the
    # invoices/bills and remove its journal entry. Deleting only the row left the
    # invoice "paid" and the bank showing money that was never received.
    err = closed_period_error(payment.date)
    if err:
        return Response({"success": False, "message": err}, status=status.HTTP_400_BAD_REQUEST)
    with transaction.atomic():
        for alloc in payment.allocations.all():
            model = Invoice if alloc.content_type == "invoice" else Bill if alloc.content_type == "bill" else None
            if model is None:
                continue
            doc = model.objects.select_for_update().filter(id=alloc.object_id).first()
            if not doc:
                continue
            doc.paid_amount = max(Decimal("0"), (doc.paid_amount or Decimal("0")) - alloc.amount)
            if doc.status == "paid" and doc.paid_amount < (doc.total or Decimal("0")):
                doc.status = "sent" if model is Invoice else "approved"
            doc.save(update_fields=["paid_amount", "status"])
        je = payment.journal_entry
        payment.delete()
        if je is not None:
            je.delete()
    log_action(request.user, "delete", "Payment", pk, ip=_get_client_ip(request))
    return Response({"success": True, "message": "Payment deleted"})


@api_view(["POST"])
@permission_classes([RoleWriteAccess])
def payment_allocate(request, pk):
    """Allocate a payment to invoices/bills."""
    try:
        payment = Payment.objects.get(id=pk)
    except Payment.DoesNotExist:
        return Response(
            {"success": False, "message": "Payment not found"},
            status=status.HTTP_404_NOT_FOUND,
        )

    allocations_data = request.data.get("allocations", [])
    if not allocations_data:
        return Response(
            {"success": False, "message": "allocations list is required"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    # Validate total allocation does not exceed payment amount
    total_alloc = sum(Decimal(str(a.get("amount", 0))) for a in allocations_data)
    existing_alloc = payment.allocations.aggregate(total=Sum("amount"))["total"] or Decimal("0")
    if existing_alloc + total_alloc > payment.amount:
        return Response(
            {"success": False, "message": "Total allocations exceed payment amount"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    with transaction.atomic():
        for alloc_data in allocations_data:
            content_type = alloc_data.get("content_type")
            object_id = alloc_data.get("object_id")
            alloc_amount = Decimal(str(alloc_data.get("amount", 0)))

            if content_type not in ("invoice", "bill", "credit_note"):
                return Response(
                    {"success": False, "message": f"Invalid content_type: {content_type}"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            PaymentAllocation.objects.create(
                payment=payment,
                content_type=content_type,
                object_id=object_id,
                amount=alloc_amount,
            )

            # Update paid_amount on target
            if content_type == "invoice":
                try:
                    inv = Invoice.objects.get(id=object_id)
                    inv.paid_amount = inv.paid_amount + alloc_amount
                    if inv.paid_amount >= inv.total:
                        inv.status = "paid"
                    inv.save()
                except Invoice.DoesNotExist:
                    pass
            elif content_type == "bill":
                try:
                    bill = Bill.objects.get(id=object_id)
                    bill.paid_amount = bill.paid_amount + alloc_amount
                    if bill.paid_amount >= bill.total:
                        bill.status = "paid"
                    bill.save()
                except Bill.DoesNotExist:
                    pass

    payment.refresh_from_db()
    payment = Payment.objects.select_related(
        "bank_account", "customer", "supplier", "journal_entry",
    ).prefetch_related("allocations").get(id=pk)

    return Response({
        "success": True,
        "message": "Payment allocated",
        "data": {"payment": _payment_dict(payment)},
    })


# =============================================================================
# 6-8  Bank Rules
# =============================================================================

@api_view(["GET", "POST"])
@permission_classes([RoleWriteAccess])
def bank_rules_list_create(request):
    if request.method == "GET":
        qs = BankRule.objects.select_related("account").all()
        return Response({
            "success": True,
            "data": {"bank_rules": [_bank_rule_dict(r) for r in qs]},
        })

    # POST
    data = request.data
    for field in ("pattern", "account_id"):
        if not data.get(field):
            return Response(
                {"success": False, "message": f"{field} is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

    try:
        account = Account.objects.get(id=data["account_id"])
    except Account.DoesNotExist:
        return Response(
            {"success": False, "message": "Account not found"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    rule = BankRule.objects.create(
        pattern=data["pattern"],
        match_type=data.get("match_type", "contains"),
        match_field=data.get("match_field", "description"),
        account=account,
        description_template=data.get("description_template", ""),
        priority=data.get("priority", 0),
        is_active=data.get("is_active", True),
    )
    log_action(request.user, "create", "BankRule", rule.id, ip=_get_client_ip(request))
    return Response({
        "success": True,
        "message": "Bank rule created",
        "data": {"bank_rule": _bank_rule_dict(rule)},
    }, status=status.HTTP_201_CREATED)


@api_view(["GET", "PUT", "DELETE"])
@permission_classes([RoleWriteAccess])
def bank_rules_detail(request, pk):
    try:
        rule = BankRule.objects.select_related("account").get(id=pk)
    except BankRule.DoesNotExist:
        return Response(
            {"success": False, "message": "Bank rule not found"},
            status=status.HTTP_404_NOT_FOUND,
        )

    if request.method == "GET":
        return Response({
            "success": True,
            "data": {"bank_rule": _bank_rule_dict(rule)},
        })

    if request.method == "PUT":
        data = request.data
        for field in ("pattern", "match_type", "match_field",
                       "description_template", "priority", "is_active"):
            if field in data:
                setattr(rule, field, data[field])
        if "account_id" in data:
            try:
                rule.account = Account.objects.get(id=data["account_id"])
            except Account.DoesNotExist:
                return Response(
                    {"success": False, "message": "Account not found"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
        rule.save()
        log_action(request.user, "update", "BankRule", rule.id, ip=_get_client_ip(request))
        return Response({
            "success": True,
            "message": "Bank rule updated",
            "data": {"bank_rule": _bank_rule_dict(rule)},
        })

    # DELETE
    rule.delete()
    log_action(request.user, "delete", "BankRule", pk, ip=_get_client_ip(request))
    return Response({"success": True, "message": "Bank rule deleted"})


@api_view(["POST"])
@permission_classes([RoleWriteAccess])
def bank_rules_test(request):
    """Test a bank rule pattern against a description string."""
    description = request.data.get("description", "")
    pattern = request.data.get("pattern", "")
    match_type = request.data.get("match_type", "contains")

    if not pattern:
        return Response(
            {"success": False, "message": "pattern is required"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    matched = False
    if match_type == "contains":
        matched = pattern.lower() in description.lower()
    elif match_type == "regex":
        try:
            matched = bool(re.search(pattern, description, re.IGNORECASE))
        except re.error as e:
            return Response(
                {"success": False, "message": f"Invalid regex: {e}"},
                status=status.HTTP_400_BAD_REQUEST,
            )
    else:
        return Response(
            {"success": False, "message": "match_type must be 'contains' or 'regex'"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    return Response({
        "success": True,
        "data": {
            "matched": matched,
            "description": description,
            "pattern": pattern,
            "match_type": match_type,
        },
    })


# =============================================================================
# 9-12  Bank Reconciliation
# =============================================================================

@api_view(["GET", "POST"])
@permission_classes([RoleWriteAccess])
def bank_reconciliations_list_create(request):
    if request.method == "GET":
        qs = BankReconciliation.objects.select_related("bank_account").all()
        return Response({
            "success": True,
            "data": {
                "reconciliations": [
                    _reconciliation_dict(r, include_lines=False) for r in qs
                ],
            },
        })

    # POST - create reconciliation session
    data = request.data
    for field in ("bank_account_id", "date", "statement_balance"):
        if not data.get(field):
            return Response(
                {"success": False, "message": f"{field} is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

    try:
        bank_account = Account.objects.get(id=data["bank_account_id"])
    except Account.DoesNotExist:
        return Response(
            {"success": False, "message": "Bank account not found"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    with transaction.atomic():
        recon = BankReconciliation.objects.create(
            bank_account=bank_account,
            date=data["date"],
            statement_balance=Decimal(str(data["statement_balance"])),
        )

        # Load unmatched posted journal lines for this bank account
        # Exclude lines already matched in other completed reconciliations
        already_matched_line_ids = BankReconciliationLine.objects.filter(
            is_matched=True,
            reconciliation__status="completed",
        ).values_list("journal_line_id", flat=True)

        unmatched_lines = JournalEntryLine.objects.filter(
            account=bank_account,
            journal_entry__is_posted=True,
            journal_entry__date__lte=data["date"],
        ).exclude(
            id__in=already_matched_line_ids,
        ).select_related("journal_entry")

        for jl in unmatched_lines:
            BankReconciliationLine.objects.create(
                reconciliation=recon,
                journal_line=jl,
            )

    recon = BankReconciliation.objects.select_related("bank_account").get(id=recon.id)
    log_action(request.user, "create", "BankReconciliation", recon.id, ip=_get_client_ip(request))
    return Response({
        "success": True,
        "message": "Reconciliation session created",
        "data": {"reconciliation": _reconciliation_dict(recon)},
    }, status=status.HTTP_201_CREATED)


@api_view(["GET"])
@permission_classes([RoleWriteAccess])
def bank_reconciliations_detail(request, pk):
    try:
        recon = BankReconciliation.objects.select_related("bank_account").get(id=pk)
    except BankReconciliation.DoesNotExist:
        return Response(
            {"success": False, "message": "Reconciliation not found"},
            status=status.HTTP_404_NOT_FOUND,
        )

    return Response({
        "success": True,
        "data": {"reconciliation": _reconciliation_dict(recon)},
    })


@api_view(["POST"])
@permission_classes([RoleWriteAccess])
def bank_reconciliation_match(request, pk):
    """Mark reconciliation lines as matched."""
    try:
        recon = BankReconciliation.objects.get(id=pk)
    except BankReconciliation.DoesNotExist:
        return Response(
            {"success": False, "message": "Reconciliation not found"},
            status=status.HTTP_404_NOT_FOUND,
        )

    if recon.status == "completed":
        return Response(
            {"success": False, "message": "Reconciliation is already completed"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    line_ids = request.data.get("line_ids", [])
    if not line_ids:
        return Response(
            {"success": False, "message": "line_ids is required"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    now = timezone.now()
    matched_count = BankReconciliationLine.objects.filter(
        reconciliation=recon,
        id__in=line_ids,
    ).update(is_matched=True, matched_at=now)

    return Response({
        "success": True,
        "message": f"{matched_count} lines matched",
        "data": {"matched_count": matched_count},
    })


@api_view(["POST"])
@permission_classes([RoleWriteAccess])
def bank_reconciliation_complete(request, pk):
    """Mark reconciliation as completed."""
    try:
        recon = BankReconciliation.objects.get(id=pk)
    except BankReconciliation.DoesNotExist:
        return Response(
            {"success": False, "message": "Reconciliation not found"},
            status=status.HTTP_404_NOT_FOUND,
        )

    if recon.status == "completed":
        return Response(
            {"success": False, "message": "Reconciliation is already completed"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    # Server-side balance check: the matched ledger movement (bank-account
    # debits minus credits) must equal the statement balance before the
    # session can be completed. Never trust the client's difference.
    matched = recon.lines.filter(is_matched=True).aggregate(
        total_debit=Sum("journal_line__debit"),
        total_credit=Sum("journal_line__credit"),
    )
    cleared_balance = (matched["total_debit"] or Decimal("0")) - (matched["total_credit"] or Decimal("0"))
    difference = (recon.statement_balance or Decimal("0")) - cleared_balance
    if abs(difference) >= Decimal("0.01"):
        return Response(
            {"success": False,
             "message": f"Reconciliation is not balanced (difference {difference:.2f})"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    recon.status = "completed"
    recon.completed_at = timezone.now()
    recon.completed_by = (
        f"{request.user.first_name} {request.user.last_name}".strip()
        or request.user.username
    )
    recon.save()
    log_action(request.user, "update", "BankReconciliation", recon.id, ip=_get_client_ip(request))

    recon = BankReconciliation.objects.select_related("bank_account").get(id=pk)
    return Response({
        "success": True,
        "message": "Reconciliation completed",
        "data": {"reconciliation": _reconciliation_dict(recon)},
    })


# =============================================================================
# 13-17  Projects
# =============================================================================

@api_view(["GET", "POST"])
@permission_classes([RoleWriteAccess])
def projects_list_create(request):
    if request.method == "GET":
        qs = Project.objects.select_related("customer").all()

        if request.query_params.get("status"):
            qs = qs.filter(status=request.query_params["status"])
        if request.query_params.get("customer_id"):
            qs = qs.filter(customer_id=request.query_params["customer_id"])

        return Response({
            "success": True,
            "data": {"projects": [_project_dict(p) for p in qs]},
        })

    # POST
    data = request.data
    for field in ("code", "name"):
        if not data.get(field):
            return Response(
                {"success": False, "message": f"{field} is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

    if Project.objects.filter(code=data["code"]).exists():
        return Response(
            {"success": False, "message": f"Project code '{data['code']}' already exists"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    customer = None
    if data.get("customer_id"):
        try:
            customer = Customer.objects.get(id=data["customer_id"])
        except Customer.DoesNotExist:
            return Response(
                {"success": False, "message": "Customer not found"},
                status=status.HTTP_400_BAD_REQUEST,
            )

    project = Project.objects.create(
        code=data["code"],
        name=data["name"],
        customer=customer,
        status=data.get("status", "active"),
        start_date=data.get("start_date"),
        end_date=data.get("end_date"),
        budget=Decimal(str(data.get("budget", 0))),
        notes=data.get("notes", ""),
        created_by=(
            f"{request.user.first_name} {request.user.last_name}".strip()
            or request.user.username
        ),
    )
    log_action(request.user, "create", "Project", project.id, ip=_get_client_ip(request))
    return Response({
        "success": True,
        "message": "Project created",
        "data": {"project": _project_dict(project)},
    }, status=status.HTTP_201_CREATED)


@api_view(["GET", "PUT", "DELETE"])
@permission_classes([RoleWriteAccess])
def projects_detail(request, pk):
    try:
        project = Project.objects.select_related("customer").get(id=pk)
    except Project.DoesNotExist:
        return Response(
            {"success": False, "message": "Project not found"},
            status=status.HTTP_404_NOT_FOUND,
        )

    if request.method == "GET":
        return Response({
            "success": True,
            "data": {"project": _project_dict(project)},
        })

    if request.method == "PUT":
        data = request.data
        if "code" in data and data["code"] != project.code:
            if Project.objects.filter(code=data["code"]).exclude(id=pk).exists():
                return Response(
                    {"success": False, "message": "Project code already exists"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            project.code = data["code"]
        for field in ("name", "status", "start_date", "end_date", "notes"):
            if field in data:
                setattr(project, field, data[field])
        if "budget" in data:
            project.budget = Decimal(str(data["budget"]))
        if "customer_id" in data:
            if data["customer_id"]:
                try:
                    project.customer = Customer.objects.get(id=data["customer_id"])
                except Customer.DoesNotExist:
                    return Response(
                        {"success": False, "message": "Customer not found"},
                        status=status.HTTP_400_BAD_REQUEST,
                    )
            else:
                project.customer = None
        project.save()
        log_action(request.user, "update", "Project", project.id, ip=_get_client_ip(request))
        return Response({
            "success": True,
            "message": "Project updated",
            "data": {"project": _project_dict(project)},
        })

    # DELETE
    project.delete()
    log_action(request.user, "delete", "Project", pk, ip=_get_client_ip(request))
    return Response({"success": True, "message": "Project deleted"})


@api_view(["GET"])
@permission_classes([RoleWriteAccess])
def project_transactions(request, pk):
    """List project transactions with journal line details."""
    try:
        project = Project.objects.get(id=pk)
    except Project.DoesNotExist:
        return Response(
            {"success": False, "message": "Project not found"},
            status=status.HTTP_404_NOT_FOUND,
        )

    txns = ProjectTransaction.objects.filter(
        project=project,
    ).select_related(
        "journal_line__account",
        "journal_line__journal_entry",
    ).order_by("journal_line__journal_entry__date")

    return Response({
        "success": True,
        "data": {
            "project": _project_dict(project),
            "transactions": [_project_txn_dict(t) for t in txns],
        },
    })


@api_view(["POST"])
@permission_classes([RoleWriteAccess])
def project_assign(request, pk):
    """Assign journal lines to a project."""
    try:
        project = Project.objects.get(id=pk)
    except Project.DoesNotExist:
        return Response(
            {"success": False, "message": "Project not found"},
            status=status.HTTP_404_NOT_FOUND,
        )

    journal_line_ids = request.data.get("journal_line_ids", [])
    if not journal_line_ids:
        return Response(
            {"success": False, "message": "journal_line_ids is required"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    # Validate that journal lines exist
    existing_lines = JournalEntryLine.objects.filter(id__in=journal_line_ids)
    found_ids = set(str(jl.id) for jl in existing_lines)
    missing = [lid for lid in journal_line_ids if str(lid) not in found_ids]
    if missing:
        return Response(
            {"success": False, "message": f"Journal lines not found: {missing}"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    created_count = 0
    for jl in existing_lines:
        _, created = ProjectTransaction.objects.get_or_create(
            project=project,
            journal_line=jl,
        )
        if created:
            created_count += 1

    return Response({
        "success": True,
        "message": f"{created_count} journal lines assigned to project",
        "data": {"assigned_count": created_count},
    })


@api_view(["GET"])
@permission_classes([RoleWriteAccess])
def project_pnl(request, pk):
    """Calculate project P&L from assigned transactions."""
    try:
        project = Project.objects.select_related("customer").get(id=pk)
    except Project.DoesNotExist:
        return Response(
            {"success": False, "message": "Project not found"},
            status=status.HTTP_404_NOT_FOUND,
        )

    txns = ProjectTransaction.objects.filter(
        project=project,
    ).select_related(
        "journal_line__account__account_type",
        "journal_line__journal_entry",
    )

    revenue_rows = []
    expense_rows = []
    revenue_total = Decimal("0")
    expense_total = Decimal("0")

    for txn in txns:
        jl = txn.journal_line
        acct = jl.account
        acct_type_name = acct.account_type.name if acct.account_type else ""

        row = {
            "account_code": acct.code,
            "account_name": acct.name,
            "debit": str(jl.debit),
            "credit": str(jl.credit),
            "entry_number": jl.journal_entry.entry_number,
            "entry_date": jl.journal_entry.date.isoformat() if jl.journal_entry.date else None,
            "description": jl.description,
        }

        if acct_type_name == "Revenue":
            amount = jl.credit - jl.debit
            row["amount"] = str(amount)
            revenue_rows.append(row)
            revenue_total += amount
        elif acct_type_name == "Expense":
            amount = jl.debit - jl.credit
            row["amount"] = str(amount)
            expense_rows.append(row)
            expense_total += amount

    net_income = revenue_total - expense_total

    return Response({
        "success": True,
        "data": {
            "project": _project_dict(project),
            "revenue": {"rows": revenue_rows, "total": str(revenue_total)},
            "expenses": {"rows": expense_rows, "total": str(expense_total)},
            "net_income": str(net_income),
            "budget": str(project.budget),
            "budget_remaining": str(project.budget - expense_total),
        },
    })


# =============================================================================
# 18-20  Documents
# =============================================================================

@api_view(["GET", "POST"])
@permission_classes([RoleWriteAccess])
@parser_classes([MultiPartParser, FormParser])
def documents_list_create(request):
    if request.method == "GET":
        qs = Document.objects.all()

        if request.query_params.get("journal_entry_id"):
            qs = qs.filter(journal_entry_id=request.query_params["journal_entry_id"])
        if request.query_params.get("invoice_id"):
            qs = qs.filter(invoice_id=request.query_params["invoice_id"])
        if request.query_params.get("bill_id"):
            qs = qs.filter(bill_id=request.query_params["bill_id"])

        return Response({
            "success": True,
            "data": {"documents": [_document_dict(d) for d in qs]},
        })

    # POST - file upload
    uploaded_file = request.FILES.get("file")
    if not uploaded_file:
        return Response(
            {"success": False, "message": "No file uploaded"},
            status=status.HTTP_400_BAD_REQUEST,
        )
    upload_err = validate_upload(uploaded_file)
    if upload_err:
        return Response(
            {"success": False, "message": upload_err},
            status=status.HTTP_400_BAD_REQUEST,
        )

    digest = hashlib.sha256()
    for chunk in uploaded_file.chunks():
        digest.update(chunk)
    uploaded_file.seek(0)
    doc = Document.objects.create(
        file=uploaded_file,
        filename=uploaded_file.name,
        description=request.data.get("description", ""),
        piece_number=request.data.get("piece_number", ""),
        sha256=digest.hexdigest(),
        size=uploaded_file.size or 0,
        journal_entry_id=request.data.get("journal_entry_id") or None,
        invoice_id=request.data.get("invoice_id") or None,
        bill_id=request.data.get("bill_id") or None,
        expense_id=request.data.get("expense_id") or None,
        uploaded_by=(
            f"{request.user.first_name} {request.user.last_name}".strip()
            or request.user.username
        ),
    )
    log_action(request.user, "create", "Document", doc.id, ip=_get_client_ip(request))
    return Response({
        "success": True,
        "message": "Document uploaded",
        "data": {"document": _document_dict(doc)},
    }, status=status.HTTP_201_CREATED)


@api_view(["GET", "DELETE"])
@permission_classes([RoleWriteAccess])
def documents_detail(request, pk):
    try:
        doc = Document.objects.get(id=pk)
    except Document.DoesNotExist:
        return Response(
            {"success": False, "message": "Document not found"},
            status=status.HTTP_404_NOT_FOUND,
        )

    if request.method == "GET":
        return Response({
            "success": True,
            "data": {"document": _document_dict(doc)},
        })

    # DELETE
    err = _document_locked(doc)
    if err:
        return Response({"success": False, "message": err}, status=status.HTTP_400_BAD_REQUEST)
    log_action(request.user, "delete", "Document", pk,
               {"filename": doc.filename, "sha256": doc.sha256}, ip=_get_client_ip(request))
    doc.file.delete(save=False)
    doc.delete()
    return Response({"success": True, "message": "Document deleted"})


def _document_locked(doc):
    """A pièce of a validated entry stays (Loi 9-88: kept 10 years)."""
    entries = [doc.journal_entry] if doc.journal_entry_id else []
    for rel in ("invoice", "bill", "expense"):
        obj = getattr(doc, rel)
        if obj is not None and getattr(obj, "journal_entry_id", None):
            entries.append(obj.journal_entry)
    for e in entries:
        if e.validated_at:
            return f"This document supports validated entry {e.entry_number} and must be kept"
    return None


@api_view(["GET"])
@permission_classes([RoleWriteAccess])
def document_download(request, pk):
    """The file itself, for signed-in users (media is not served publicly)."""
    from django.http import FileResponse

    doc = Document.objects.filter(id=pk).first()
    if not doc or not doc.file:
        return Response({"success": False, "message": "Document not found"}, status=status.HTTP_404_NOT_FOUND)
    try:
        handle = doc.file.open("rb")
    except FileNotFoundError:
        return Response({"success": False, "message": "The file is missing on the server"},
                        status=status.HTTP_404_NOT_FOUND)
    return FileResponse(handle, as_attachment=False, filename=doc.filename)


@api_view(["POST"])
@permission_classes([RoleWriteAccess])
def document_link(request, pk):
    """Link a document to a journal entry, invoice, bill, or expense."""
    try:
        doc = Document.objects.get(id=pk)
    except Document.DoesNotExist:
        return Response(
            {"success": False, "message": "Document not found"},
            status=status.HTTP_404_NOT_FOUND,
        )
    err = _document_locked(doc)
    if err:
        return Response({"success": False, "message": err}, status=status.HTTP_400_BAD_REQUEST)

    data = request.data
    if "journal_entry_id" in data:
        if data["journal_entry_id"]:
            try:
                JournalEntry.objects.get(id=data["journal_entry_id"])
            except JournalEntry.DoesNotExist:
                return Response(
                    {"success": False, "message": "Journal entry not found"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
        doc.journal_entry_id = data["journal_entry_id"] or None

    if "invoice_id" in data:
        if data["invoice_id"]:
            try:
                Invoice.objects.get(id=data["invoice_id"])
            except Invoice.DoesNotExist:
                return Response(
                    {"success": False, "message": "Invoice not found"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
        doc.invoice_id = data["invoice_id"] or None

    if "bill_id" in data:
        if data["bill_id"]:
            try:
                Bill.objects.get(id=data["bill_id"])
            except Bill.DoesNotExist:
                return Response(
                    {"success": False, "message": "Bill not found"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
        doc.bill_id = data["bill_id"] or None

    if "expense_id" in data:
        from purchases.models import Expense
        if data["expense_id"]:
            try:
                Expense.objects.get(id=data["expense_id"])
            except Expense.DoesNotExist:
                return Response(
                    {"success": False, "message": "Expense not found"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
        doc.expense_id = data["expense_id"] or None

    doc.save()
    return Response({
        "success": True,
        "message": "Document linked",
        "data": {"document": _document_dict(doc)},
    })


# =============================================================================
# 21-27  Reports
# =============================================================================

@api_view(["GET"])
@permission_classes([RoleWriteAccess])
def report_tax(request):
    """Tax report for a period: tax collected (sales) vs tax paid (purchases)."""
    date_from = request.query_params.get("date_from")
    date_to = request.query_params.get("date_to")

    if not date_from or not date_to:
        return Response(
            {"success": False, "message": "date_from and date_to are required"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    tax_codes = TaxCode.objects.select_related("account").filter(is_active=True)

    filters = {
        "journal_entry__is_posted": True,
        "journal_entry__date__gte": date_from,
        "journal_entry__date__lte": date_to,
    }

    collected_rows = []
    paid_rows = []
    total_collected = Decimal("0")
    total_paid = Decimal("0")

    # One row per tax ACCOUNT, counted once. A "both" code used to be added to
    # collected (cr − dr) AND to paid (dr − cr), so the net came out doubled, and
    # two codes sharing an account counted it twice. A sales-only account is
    # collected, a purchase-only one paid; a shared or "both" account goes on the
    # side its balance is on. Net payable is then simply credits − debits.
    by_account = {}
    for tc in tax_codes:
        entry = by_account.setdefault(tc.account_id, {"account": tc.account, "codes": []})
        entry["codes"].append(tc)

    for entry in by_account.values():
        acct, codes = entry["account"], entry["codes"]
        totals = JournalEntryLine.objects.in_mad().filter(
            account=acct, **filters,
        ).aggregate(total_debit=Sum("debit"), total_credit=Sum("credit"))

        dr = totals["total_debit"] or Decimal("0")
        cr = totals["total_credit"] or Decimal("0")

        if dr == 0 and cr == 0:
            continue

        row = {
            "tax_code": ", ".join(tc.code for tc in codes),
            "tax_name": ", ".join(tc.name for tc in codes),
            "rate": ", ".join(str(tc.rate) for tc in codes),
            "account_code": acct.code,
            "debit": str(dr),
            "credit": str(cr),
        }

        types = {tc.type for tc in codes}
        if types == {"sales"}:
            side = "collected"
        elif types == {"purchase"}:
            side = "paid"
        else:
            side = "collected" if cr - dr >= 0 else "paid"

        if side == "collected":
            amount = cr - dr
            row["amount"] = str(amount)
            collected_rows.append(row)
            total_collected += amount
        else:
            amount = dr - cr
            row["amount"] = str(amount)
            paid_rows.append(row)
            total_paid += amount

    net_tax = total_collected - total_paid

    return Response({
        "success": True,
        "data": {
            "period": {"date_from": date_from, "date_to": date_to},
            "tax_collected": {"rows": collected_rows, "total": str(total_collected)},
            "tax_paid": {"rows": paid_rows, "total": str(total_paid)},
            "net_tax_payable": str(net_tax),
        },
    })


@api_view(["GET"])
@permission_classes([RoleWriteAccess])
def report_cash_flow(request):
    """Cash flow statement for a period, grouped by operating/investing/financing."""
    date_from = request.query_params.get("date_from")
    date_to = request.query_params.get("date_to")

    if not date_from or not date_to:
        return Response(
            {"success": False, "message": "date_from and date_to are required"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    filters = {
        "journal_entry__is_posted": True,
        "journal_entry__date__gte": date_from,
        "journal_entry__date__lte": date_to,
    }

    # Cash/bank accounts (514x banks, 516x cash)
    cash_accounts = Account.objects.filter(chart.treasury_q(), is_active=True)
    cash_account_ids = set(str(a.id) for a in cash_accounts)

    # Get all posted journal entries that touch cash accounts in the period.
    # Euros not exchanged yet have no dirham value and stay out.
    cash_lines = JournalEntryLine.objects.in_mad().filter(
        account__in=cash_accounts, **filters,
    ).select_related("journal_entry", "account")

    # For each cash line, find the contra accounts to classify
    operating = []
    investing = []
    financing = []
    operating_total = Decimal("0")
    investing_total = Decimal("0")
    financing_total = Decimal("0")

    # Classify based on account type of the contra entry
    # Revenue/Expense accounts -> Operating
    # Asset accounts (non-cash) -> Investing
    # Liability/Equity accounts -> Financing

    for cl in cash_lines:
        # Net cash effect: debit = inflow, credit = outflow
        net = cl.debit - cl.credit

        # Find contra lines in the same journal entry (non-cash accounts)
        contra_lines = JournalEntryLine.objects.filter(
            journal_entry=cl.journal_entry,
        ).exclude(id=cl.id).select_related("account__account_type")

        # Use the first contra line's account type for classification
        category = "operating"
        contra_desc = ""
        for contra in contra_lines:
            if str(contra.account_id) in cash_account_ids:
                continue
            acct_type = contra.account.account_type.name if contra.account.account_type else ""
            contra_desc = contra.account.name
            if acct_type in ("Revenue", "Expense"):
                category = "operating"
            elif acct_type == "Asset":
                category = "investing"
            elif acct_type in ("Liability", "Equity"):
                category = "financing"
            break

        row = {
            "date": cl.journal_entry.date.isoformat(),
            "entry_number": cl.journal_entry.entry_number,
            "description": cl.journal_entry.description or contra_desc,
            "amount": str(net),
        }

        if category == "operating":
            operating.append(row)
            operating_total += net
        elif category == "investing":
            investing.append(row)
            investing_total += net
        else:
            financing.append(row)
            financing_total += net

    net_change = operating_total + investing_total + financing_total

    return Response({
        "success": True,
        "data": {
            "period": {"date_from": date_from, "date_to": date_to},
            "operating": {"rows": operating, "total": str(operating_total)},
            "investing": {"rows": investing, "total": str(investing_total)},
            "financing": {"rows": financing, "total": str(financing_total)},
            "net_cash_change": str(net_change),
        },
    })


# Payment term used to age open items: Loi 69-21 sets 60 days when nothing else
# is agreed.
PAYMENT_TERM_DAYS = 60
AGING_BUCKETS = ("current", "days_1_30", "days_31_60", "days_61_90", "days_over_90")


def _aging_bucket(days_overdue):
    if days_overdue <= 0:
        return "current"
    if days_overdue <= 30:
        return "days_1_30"
    if days_overdue <= 60:
        return "days_31_60"
    if days_overdue <= 90:
        return "days_61_90"
    return "days_over_90"


def _ledger_aging(account_code, sign, name_field, as_of):
    """Open items per tiers from the ledger: the lines on the tiers account that
    are not lettered, with what was paid set against the oldest first (FIFO).
    sign=1 for receivables (debit open), -1 for payables (credit open)."""
    lines = (JournalEntryLine.objects.in_mad()
             .filter(account__code=account_code, lettrage="", journal_entry__is_posted=True,
                     journal_entry__date__lte=as_of)
             .select_related("journal_entry").order_by("journal_entry__date"))
    by_partner = {}
    for l in lines:
        p = by_partner.setdefault(l.partner_id, {"name": l.partner_name or "—", "items": [], "paid": Decimal("0")})
        amount = sign * ((l.debit or Decimal("0")) - (l.credit or Decimal("0")))
        if amount > 0:
            p["items"].append([l.journal_entry.date, amount])
        else:
            p["paid"] += -amount
    rows, totals = [], {b: Decimal("0") for b in AGING_BUCKETS + ("total",)}
    for partner_id, p in by_partner.items():
        paid = p["paid"]
        row = {b: Decimal("0") for b in AGING_BUCKETS}
        for d, amount in p["items"]:
            used = min(paid, amount)
            paid -= used
            left = amount - used
            if left > 0:
                row[_aging_bucket((as_of - d).days - PAYMENT_TERM_DAYS)] += left
        total = sum(row.values()) - paid  # money paid in advance shows as a negative total
        if total == 0 and not any(row.values()):
            continue
        row["current"] -= paid
        for b in AGING_BUCKETS:
            totals[b] += row[b]
        totals["total"] += total
        rows.append({"partner_id": partner_id, name_field: p["name"],
                     **{b: str(v) for b, v in row.items()}, "total": str(total)})
    rows.sort(key=lambda r: -Decimal(r["total"]))
    return {"as_of": as_of.isoformat(), "payment_term_days": PAYMENT_TERM_DAYS, "rows": rows,
            "totals": {b: str(v) for b, v in totals.items()}}


def _as_of(request):
    from journals.periods import _to_date
    return _to_date(request.query_params.get("as_of")) or datetime.now().date()


@api_view(["GET"])
@permission_classes([RoleWriteAccess])
def report_aging_receivable(request):
    """Customers' open items (3421, not lettered) by days overdue."""
    return Response({"success": True,
                     "data": _ledger_aging(chart.RECEIVABLE, 1, "customer_name", _as_of(request))})


@api_view(["GET"])
@permission_classes([RoleWriteAccess])
def report_aging_payable(request):
    """Suppliers' open items (4411, not lettered) by days overdue."""
    return Response({"success": True,
                     "data": _ledger_aging(chart.PAYABLE, -1, "supplier_name", _as_of(request))})


@api_view(["GET"])
@permission_classes([RoleWriteAccess])
def report_general_ledger(request):
    """General ledger: all accounts with all posted entries for a period."""
    date_from = request.query_params.get("date_from")
    date_to = request.query_params.get("date_to")

    if not date_from or not date_to:
        return Response(
            {"success": False, "message": "date_from and date_to are required"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    filters = {
        "journal_entry__is_posted": True,
        "journal_entry__date__gte": date_from,
        "journal_entry__date__lte": date_to,
    }

    accounts = Account.objects.filter(
        is_active=True,
    ).select_related("account_type").order_by("code")

    ledger = []
    for acct in accounts:
        lines_qs = JournalEntryLine.objects.filter(
            account=acct, **filters,
        ).select_related("journal_entry").order_by(
            "journal_entry__date", "journal_entry__entry_number",
        )

        if not lines_qs.exists():
            continue

        # The balance is in the account's currency; a line in another currency
        # (euros on a MAD account) is listed but does not move it.
        lines = []
        running_balance = Decimal("0")
        for line in lines_qs:
            if line.currency != acct.currency:
                pass
            elif acct.account_type.normal_balance == "debit":
                running_balance += line.debit - line.credit
            else:
                running_balance += line.credit - line.debit

            lines.append({
                "id": str(line.id),
                "date": line.journal_entry.date.isoformat(),
                "entry_number": line.journal_entry.entry_number,
                "description": line.description or line.journal_entry.description,
                "debit": str(line.debit),
                "credit": str(line.credit),
                "currency": line.currency,
                "running_balance": str(running_balance),
            })

        totals = lines_qs.filter(currency=acct.currency).aggregate(
            total_debit=Sum("debit"),
            total_credit=Sum("credit"),
        )

        ledger.append({
            "account_id": str(acct.id),
            "account_code": acct.code,
            "account_name": acct.name,
            "account_type": acct.account_type.name,
            "currency": acct.currency,
            "lines": lines,
            "total_debit": str(totals["total_debit"] or 0),
            "total_credit": str(totals["total_credit"] or 0),
            "closing_balance": str(running_balance),
        })

    return Response({
        "success": True,
        "data": {
            "period": {"date_from": date_from, "date_to": date_to},
            "accounts": ledger,
        },
    })


@api_view(["GET"])
@permission_classes([RoleWriteAccess])
def report_account_specification(request):
    """Single account detail with all posted lines and running balance."""
    account_id = request.query_params.get("account_id")
    date_from = request.query_params.get("date_from")
    date_to = request.query_params.get("date_to")

    if not account_id:
        return Response(
            {"success": False, "message": "account_id is required"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    try:
        acct = Account.objects.select_related("account_type").get(id=account_id)
    except Account.DoesNotExist:
        return Response(
            {"success": False, "message": "Account not found"},
            status=status.HTTP_404_NOT_FOUND,
        )

    # Opening balance: sum of all posted lines before date_from
    opening_balance = Decimal("0")
    if date_from:
        ob_totals = JournalEntryLine.objects.filter(
            account=acct, currency=acct.currency,
            journal_entry__is_posted=True,
            journal_entry__date__lt=date_from,
        ).aggregate(total_debit=Sum("debit"), total_credit=Sum("credit"))

        ob_dr = ob_totals["total_debit"] or Decimal("0")
        ob_cr = ob_totals["total_credit"] or Decimal("0")
        if acct.account_type.normal_balance == "debit":
            opening_balance = ob_dr - ob_cr
        else:
            opening_balance = ob_cr - ob_dr

    # Lines in period
    filters = {
        "journal_entry__is_posted": True,
    }
    if date_from:
        filters["journal_entry__date__gte"] = date_from
    if date_to:
        filters["journal_entry__date__lte"] = date_to

    lines_qs = JournalEntryLine.objects.filter(
        account=acct, **filters,
    ).select_related("journal_entry").order_by(
        "journal_entry__date", "journal_entry__entry_number",
    )

    # The balance is in the account's currency; a line in another currency
    # (euros on a MAD account) is listed but does not move it.
    running_balance = opening_balance
    lines = []
    for line in lines_qs:
        if line.currency != acct.currency:
            pass
        elif acct.account_type.normal_balance == "debit":
            running_balance += line.debit - line.credit
        else:
            running_balance += line.credit - line.debit

        lines.append({
            "id": str(line.id),
            "date": line.journal_entry.date.isoformat(),
            "entry_number": line.journal_entry.entry_number,
            "description": line.description or line.journal_entry.description,
            "reference": line.journal_entry.reference,
            "debit": str(line.debit),
            "credit": str(line.credit),
            "currency": line.currency,
            "running_balance": str(running_balance),
        })

    period_totals = lines_qs.filter(currency=acct.currency).aggregate(
        total_debit=Sum("debit"),
        total_credit=Sum("credit"),
    )

    return Response({
        "success": True,
        "data": {
            "account": {
                "id": str(acct.id),
                "code": acct.code,
                "name": acct.name,
                "account_type": acct.account_type.name,
                "normal_balance": acct.account_type.normal_balance,
                "currency": acct.currency,
            },
            "period": {"date_from": date_from, "date_to": date_to},
            "opening_balance": str(opening_balance),
            "lines": lines,
            "total_debit": str(period_totals["total_debit"] or 0),
            "total_credit": str(period_totals["total_credit"] or 0),
            "closing_balance": str(running_balance),
        },
    })


@api_view(["GET"])
@permission_classes([RoleWriteAccess])
def report_project_pnl(request):
    """P&L for a specific project (query param: project_id)."""
    project_id = request.query_params.get("project_id")
    if not project_id:
        return Response(
            {"success": False, "message": "project_id is required"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    try:
        project = Project.objects.select_related("customer").get(id=project_id)
    except Project.DoesNotExist:
        return Response(
            {"success": False, "message": "Project not found"},
            status=status.HTTP_404_NOT_FOUND,
        )

    txns = ProjectTransaction.objects.filter(
        project=project,
    ).select_related(
        "journal_line__account__account_type",
        "journal_line__journal_entry",
    )

    revenue_rows = []
    expense_rows = []
    revenue_total = Decimal("0")
    expense_total = Decimal("0")

    for txn in txns:
        jl = txn.journal_line
        acct = jl.account
        acct_type_name = acct.account_type.name if acct.account_type else ""

        row = {
            "account_code": acct.code,
            "account_name": acct.name,
            "debit": str(jl.debit),
            "credit": str(jl.credit),
            "entry_number": jl.journal_entry.entry_number,
            "entry_date": jl.journal_entry.date.isoformat() if jl.journal_entry.date else None,
            "description": jl.description,
        }

        if acct_type_name == "Revenue":
            amount = jl.credit - jl.debit
            row["amount"] = str(amount)
            revenue_rows.append(row)
            revenue_total += amount
        elif acct_type_name == "Expense":
            amount = jl.debit - jl.credit
            row["amount"] = str(amount)
            expense_rows.append(row)
            expense_total += amount

    net_income = revenue_total - expense_total

    return Response({
        "success": True,
        "data": {
            "project": _project_dict(project),
            "revenue": {"rows": revenue_rows, "total": str(revenue_total)},
            "expenses": {"rows": expense_rows, "total": str(expense_total)},
            "net_income": str(net_income),
            "budget": str(project.budget),
            "budget_remaining": str(project.budget - expense_total),
        },
    })


# =============================================================================
# 28  Audit Log
# =============================================================================

@api_view(["GET"])
@permission_classes([RoleWriteAccess])
def audit_log_verify(request):
    """Recompute the hash chain of the audit log."""
    from core.audit import verify_chain
    return Response({"success": True, "data": verify_chain()})


@api_view(["GET"])
@permission_classes([RoleWriteAccess])
def audit_log_list(request):
    """List audit logs with filters and pagination."""
    qs = AuditLog.objects.select_related("user").all()

    if request.query_params.get("user_id"):
        qs = qs.filter(user_id=request.query_params["user_id"])
    if request.query_params.get("action"):
        qs = qs.filter(action=request.query_params["action"])
    if request.query_params.get("model_name"):
        qs = qs.filter(model_name=request.query_params["model_name"])
    if request.query_params.get("date_from"):
        qs = qs.filter(timestamp__date__gte=request.query_params["date_from"])
    if request.query_params.get("date_to"):
        qs = qs.filter(timestamp__date__lte=request.query_params["date_to"])

    total_count = qs.count()

    try:
        page = int(request.query_params.get("page", 1))
    except (ValueError, TypeError):
        page = 1
    try:
        page_size = int(request.query_params.get("page_size", 50))
    except (ValueError, TypeError):
        page_size = 50
    page_size = min(page_size, 200)
    offset = (page - 1) * page_size

    logs = qs[offset:offset + page_size]

    return Response({
        "success": True,
        "data": {
            "audit_logs": [_audit_log_dict(log) for log in logs],
            "total_count": total_count,
            "page": page,
            "page_size": page_size,
        },
    })


# =============================================================================
# 29  Company Settings
# =============================================================================

@api_view(["GET", "PUT"])
@permission_classes([RoleWriteAccess])
def settings_detail(request):
    """Company settings (singleton - create on first GET if not exists)."""
    settings_obj, _ = CompanySettings.objects.get_or_create(
        defaults={
            "company_name": "",
            "country": "Danmark",
            "currency": "DKK",
            "fiscal_year_start_month": 1,
        },
        **({} if CompanySettings.objects.exists() else {}),
    )
    # get_or_create needs a unique lookup. Since it is a singleton, just get or
    # create the first (and only) row.
    settings_obj = CompanySettings.objects.first()
    if not settings_obj:
        settings_obj = CompanySettings.objects.create(
            company_name="",
            country="Danmark",
            currency="DKK",
            fiscal_year_start_month=1,
        )

    if request.method == "GET":
        return Response({
            "success": True,
            "data": {"settings": _settings_dict(settings_obj)},
        })

    # PUT
    data = request.data
    for field in (
        "company_name", "address", "city", "country", "tax_id",
        "phone", "email", "currency", "fiscal_year_start_month", "date_format",
        "logo1", "logo2", "logo3",
    ):
        if field in data:
            setattr(settings_obj, field, data[field])
    settings_obj.save()
    log_action(request.user, "update", "CompanySettings", settings_obj.id, ip=_get_client_ip(request))

    return Response({
        "success": True,
        "message": "Settings updated",
        "data": {"settings": _settings_dict(settings_obj)},
    })


# =============================================================================
# 30-31  Users & Roles
# =============================================================================

@api_view(["GET", "POST"])
@permission_classes([IsAdmin])
def users_list_create(request):
    from tenancy.models import ClientMembership

    tenant = request.tenant
    if request.method == "GET":
        users = _client_users(tenant).order_by("username")
        return Response({"success": True, "data": {"users": [_user_dict(u, tenant) for u in users]}})

    data = request.data
    limit = tenant.limit("users")
    if limit is not None and ClientMembership.objects.filter(client=tenant, is_active=True).count() >= limit:
        return Response({"success": False, "code": "user_limit",
                         "message": f"Jeres pakke ({tenant.package.name}) har plads til {limit} bruger(e)."},
                        status=status.HTTP_403_FORBIDDEN)
    for field in ("username", "password"):
        if not data.get(field):
            return Response({"success": False, "message": f"{field} skal udfyldes"},
                            status=status.HTTP_400_BAD_REQUEST)
    if len(data["password"]) < 10:
        return Response({"success": False, "message": "Adgangskoden skal være mindst 10 tegn"},
                        status=status.HTTP_400_BAD_REQUEST)
    if User.objects.filter(username__iexact=data["username"]).exists():
        return Response({"success": False, "message": "Brugernavnet findes allerede"},
                        status=status.HTTP_400_BAD_REQUEST)
    role_name = data.get("role", "viewer")
    if role_name not in ("admin", "accountant", "viewer"):
        return Response({"success": False, "message": "Ugyldig rolle"}, status=status.HTTP_400_BAD_REQUEST)
    user = User.objects.create_user(
        username=data["username"], password=data["password"], email=data.get("email", ""),
        first_name=data.get("first_name", ""), last_name=data.get("last_name", ""),
    )
    ClientMembership.objects.create(user=user, client=tenant, role=role_name)
    log_action(request.user, "create", "User", user.id, changes={"role": role_name}, ip=_get_client_ip(request))
    return Response({"success": True, "message": "Bruger oprettet", "data": {"user": _user_dict(user, tenant)}},
                    status=status.HTTP_201_CREATED)


def _get_client_user(request, pk):
    return _client_users(request.tenant).filter(id=pk).first()


@api_view(["PUT"])
@permission_classes([IsAdmin])
def user_update(request, pk):
    """Ret en bruger i virksomheden: navn, e-mail, rolle, aktiv.

    Login-felterne (brugernavn, e-mail) må kun ændres for brugere, der alene
    hører til denne virksomhed. Deaktivering gælder kun adgangen hertil.
    En administrator kan ikke fjerne sin egen administratorrolle.
    """
    tenant = request.tenant
    target = _get_client_user(request, pk)
    if target is None:
        return Response({"success": False, "message": "Brugeren findes ikke"}, status=status.HTTP_404_NOT_FOUND)
    membership = _membership(target, tenant)
    data = request.data
    changes = {}
    own_login = _owned_only_by(target, tenant)

    if "username" in data and (data.get("username") or "").strip() != target.username:
        if not own_login:
            return Response({"success": False, "message": "Brugeren hører også til andre virksomheder; "
                                                          "login kan ikke ændres herfra."},
                            status=status.HTTP_400_BAD_REQUEST)
        username = (data.get("username") or "").strip()
        if not username:
            return Response({"success": False, "message": "Brugernavn skal udfyldes"},
                            status=status.HTTP_400_BAD_REQUEST)
        if User.objects.filter(username__iexact=username).exclude(id=target.id).exists():
            return Response({"success": False, "message": "Brugernavnet findes allerede"},
                            status=status.HTTP_400_BAD_REQUEST)
        changes["username"] = [target.username, username]
        target.username = username
    for field in ("first_name", "last_name", "email"):
        if field in data:
            value = (data.get(field) or "").strip()
            if value != getattr(target, field):
                if not own_login:
                    continue
                changes[field] = [getattr(target, field), value]
                setattr(target, field, value)
    target.save()

    if "is_active" in data:
        active = bool(data.get("is_active"))
        if not active and target.id == request.user.id:
            return Response({"success": False, "message": "Du kan ikke deaktivere dig selv"},
                            status=status.HTTP_400_BAD_REQUEST)
        if active != membership.is_active:
            changes["is_active"] = [membership.is_active, active]
            membership.is_active = active
            membership.save(update_fields=["is_active"])

    if "role" in data:
        role_name = data.get("role")
        if role_name not in ("admin", "accountant", "viewer"):
            return Response({"success": False, "message": "Ugyldig rolle"}, status=status.HTTP_400_BAD_REQUEST)
        if role_name != "admin" and target.id == request.user.id:
            return Response({"success": False, "message": "Du kan ikke fjerne din egen administratorrolle"},
                            status=status.HTTP_400_BAD_REQUEST)
        if membership.role != role_name:
            changes["role"] = [membership.role, role_name]
            membership.role = role_name
            membership.save(update_fields=["role"])

    if changes:
        log_action(request.user, "update", "User", target.id, changes=changes, ip=_get_client_ip(request))
    return Response({"success": True, "message": "Bruger opdateret", "data": {"user": _user_dict(target, tenant)}})


@api_view(["PUT"])
@permission_classes([IsAdmin])
def user_role_update(request, pk):
    tenant = request.tenant
    target = _get_client_user(request, pk)
    if target is None:
        return Response({"success": False, "message": "Brugeren findes ikke"}, status=status.HTTP_404_NOT_FOUND)
    role_name = request.data.get("role")
    if role_name not in ("admin", "accountant", "viewer"):
        return Response({"success": False, "message": "Rollen skal være admin, accountant eller viewer"},
                        status=status.HTTP_400_BAD_REQUEST)
    if role_name != "admin" and target.id == request.user.id:
        return Response({"success": False, "message": "Du kan ikke fjerne din egen administratorrolle"},
                        status=status.HTTP_400_BAD_REQUEST)
    membership = _membership(target, tenant)
    old = membership.role
    membership.role = role_name
    membership.save(update_fields=["role"])
    log_action(request.user, "update", "UserRole", target.id, changes={"role": [old, role_name]},
               ip=_get_client_ip(request))
    return Response({"success": True, "message": "Rolle opdateret", "data": {"user": _user_dict(target, tenant)}})


@api_view(["POST"])
@permission_classes([IsAdmin])
def user_reset_password(request, pk):
    """Ny adgangskode til en bruger, der alene hører til denne virksomhed."""
    tenant = request.tenant
    target_user = _get_client_user(request, pk)
    if target_user is None:
        return Response({"success": False, "message": "Brugeren findes ikke"}, status=status.HTTP_404_NOT_FOUND)
    if not _owned_only_by(target_user, tenant):
        return Response({"success": False, "message": "Brugeren hører også til andre virksomheder og skal selv "
                                                      "nulstille sin adgangskode."},
                        status=status.HTTP_400_BAD_REQUEST)
    chosen = (request.data.get("password") or "").strip() if hasattr(request, "data") else ""
    if chosen and len(chosen) < 10:
        return Response({"success": False, "message": "Adgangskoden skal være mindst 10 tegn"},
                        status=status.HTTP_400_BAD_REQUEST)
    new_password = chosen or secrets.token_urlsafe(12)
    target_user.set_password(new_password)
    target_user.save()
    log_action(request.user, "update", "User", target_user.id,
               changes={"action": "password_reset"}, ip=_get_client_ip(request))
    return Response({"success": True, "message": f"Adgangskoden for '{target_user.username}' er nulstillet",
                     "data": {"password": new_password}})
