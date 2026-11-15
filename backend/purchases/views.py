"""Purchases app views — Supplier, Bill, BillLine, Expense CRUD + approve."""

import csv
import io
import re
from journals.lettrage import auto_lettrer, supplier_partner, undo_lettrage_of
from datetime import date as date_today_mod
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP

from django.db import transaction
from django.db.models import Sum, Q
from django.http import HttpResponse
from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import api_view, parser_classes, permission_classes
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.response import Response

from core.audit import log_action
from core.permissions import RoleWriteAccess
from core.uploads import validate_upload
from core.csv_utils import SafeWriter

from accounts import chart
from core.vat import EntryBuilder, add_purchase, supplier_vat
from accounts.models import Account
from journals.models import JournalEntry, JournalEntryLine
from journals.periods import closed_period_error
from .models import (
    Supplier, Bill, BillLine, BillPaymentLink, Expense, ExpenseLine,
    BankTransactionCategorization,
)


# ─── helpers ──────────────────────────────────────────────────────────────────

def _rate(data):
    """Kurs (DKK pr. 1 enhed) for en regning i fremmed valuta; 1 for DKK."""
    if (data.get("currency") or "DKK").upper() == chart.BASE_CURRENCY:
        return Decimal("1")
    try:
        rate = Decimal(str(data.get("exchange_rate") or 0))
    except (InvalidOperation, TypeError):
        rate = Decimal("0")
    return rate if rate > 0 else Decimal("1")


def _supplier_dict(supplier):
    return {
        "id": str(supplier.id),
        "code": supplier.code,
        "name": supplier.name,
        "email": supplier.email,
        "phone": supplier.phone,
        "address": supplier.address,
        "tax_id": supplier.tax_id,
        "currency": supplier.currency,
        "payment_terms": supplier.payment_terms,
        "notes": supplier.notes,
        "country": supplier.country,
        "default_account_id": str(supplier.default_account_id) if supplier.default_account_id else None,
        "default_tax_code_id": str(supplier.default_tax_code_id) if supplier.default_tax_code_id else None,
        "is_active": supplier.is_active,
        "created_at": supplier.created_at.isoformat() if supplier.created_at else None,
        "updated_at": supplier.updated_at.isoformat() if supplier.updated_at else None,
    }


def _bill_line_dict(line):
    return {
        "id": str(line.id),
        "bill_id": str(line.bill_id),
        "description": line.description,
        "quantity": str(line.quantity),
        "unit_price": str(line.unit_price),
        "tax_code_id": str(line.tax_code_id) if line.tax_code_id else None,
        "tax_code_name": line.tax_code.name if line.tax_code else None,
        "tax_code_code": line.tax_code.code if line.tax_code else None,
        "reverse_charge": line.tax_code.reverse_charge if line.tax_code else "",
        "deduction_rate": str(line.tax_code.deduction_rate) if line.tax_code else None,
        "tax_rate": str(line.tax_code.rate) if line.tax_code else None,
        "account_id": str(line.account_id) if line.account_id else None,
        "account_code": line.account.code if line.account else None,
        "account_name": line.account.name if line.account else None,
        "amount": str(line.amount),
    }


def _bill_dict(bill, include_lines=True):
    supplier = bill.supplier if bill.supplier_id else None
    d = {
        "id": str(bill.id),
        "bill_number": bill.bill_number,
        "supplier_id": str(bill.supplier_id) if bill.supplier_id else None,
        "supplier_name": supplier.name if supplier else None,
        "date": bill.date.isoformat() if hasattr(bill.date, "isoformat") else str(bill.date),
        "due_date": bill.due_date.isoformat() if hasattr(bill.due_date, "isoformat") else str(bill.due_date),
        "status": bill.status,
        "subtotal": str(bill.subtotal),
        "tax_amount": str(bill.tax_amount),
        "total": str(bill.total),
        "paid_amount": str(bill.paid_amount),
        "balance_due": str(bill.balance_due),
        "currency": bill.currency,
        "exchange_rate": str(bill.exchange_rate),
        "reference": bill.reference,
        "notes": bill.notes,
        "journal_entry_id": str(bill.journal_entry_id) if bill.journal_entry_id else None,
        "created_by": bill.created_by,
        "created_at": bill.created_at.isoformat() if bill.created_at else None,
        "updated_at": bill.updated_at.isoformat() if bill.updated_at else None,
    }
    if include_lines:
        lines_qs = bill.lines.select_related("account", "tax_code").all()
        d["lines"] = [_bill_line_dict(l) for l in lines_qs]
    else:
        # Include account codes for row highlighting in list view
        if hasattr(bill, '_prefetched_objects_cache') and 'lines' in bill._prefetched_objects_cache:
            d["line_account_codes"] = list({
                l.account.code for l in bill.lines.all() if l.account_id and l.account
            })
        else:
            d["line_account_codes"] = list(
                bill.lines.filter(account__isnull=False)
                .values_list("account__code", flat=True)
                .distinct()
            )
    return d


def _expense_line_dict(line):
    return {
        "id": str(line.id),
        "description": line.description,
        "account_id": str(line.account_id) if line.account_id else None,
        "account_code": line.account.code if line.account else None,
        "account_name": line.account.name if line.account else None,
        "tax_code_id": str(line.tax_code_id) if line.tax_code_id else None,
        "tax_code_name": line.tax_code.name if line.tax_code else None,
        "tax_code_code": line.tax_code.code if line.tax_code else None,
        "reverse_charge": line.tax_code.reverse_charge if line.tax_code else "",
        "deduction_rate": str(line.tax_code.deduction_rate) if line.tax_code else None,
        "tax_rate": str(line.tax_code.rate) if line.tax_code else None,
        "amount": str(line.amount),
    }


def _expense_dict(expense):
    lines = expense.lines.select_related("account", "tax_code").all()
    return {
        "id": str(expense.id),
        "date": expense.date.isoformat() if hasattr(expense.date, "isoformat") else str(expense.date),
        "supplier_id": str(expense.supplier_id) if expense.supplier_id else None,
        "supplier_name": expense.supplier.name if expense.supplier else None,
        "description": expense.description,
        "amount": str(expense.amount),
        "tax_code_id": str(expense.tax_code_id) if expense.tax_code_id else None,
        "tax_code_name": expense.tax_code.name if expense.tax_code else None,
        "tax_rate": str(expense.tax_code.rate) if expense.tax_code else None,
        "account_id": str(expense.account_id) if expense.account_id else None,
        "account_code": expense.account.code if expense.account else None,
        "account_name": expense.account.name if expense.account else None,
        "payment_method": expense.payment_method,
        "reference": expense.reference,
        "receipt": expense.receipt.url if expense.receipt else None,
        "status": expense.status,
        "journal_entry_id": str(expense.journal_entry_id) if expense.journal_entry_id else None,
        "created_by": expense.created_by,
        "created_at": expense.created_at.isoformat() if expense.created_at else None,
        "lines": [_expense_line_dict(l) for l in lines],
        "is_split": len(lines) > 1,
    }


def _next_supplier_code():
    """Generate next sequential supplier code like SUP-0001."""
    from journals.numbering import next_number
    return next_number(Supplier, "code", "SUP")


def _next_bill_number():
    """Generate next sequential bill number like BILL-0001."""
    from journals.numbering import next_number
    return next_number(Bill, "bill_number", "BILL")


def _next_expense_number():
    """Generate next sequential expense number like EXP-0001.

    Expenses have no number column; this value is only a cosmetic reference label on
    the generated journal entry (not a unique key), so count-based is acceptable here.
    """
    count = Expense.objects.count()
    return f"EXP-{count + 1:04d}"


def _next_je_entry_number():
    """Generate next sequential journal entry number like JE-0001."""
    from journals.numbering import next_je_number
    return next_je_number()


# ─── Suppliers CRUD ──────────────────────────────────────────────────────────




@api_view(["GET", "POST"])
@permission_classes([RoleWriteAccess])
def suppliers_list_create(request):
    if request.method == "GET":
        qs = Supplier.objects.all()

        # Filter by is_active
        if request.query_params.get("is_active"):
            qs = qs.filter(is_active=request.query_params["is_active"].lower() == "true")

        # Search by name or code
        if request.query_params.get("search"):
            q = request.query_params["search"]
            qs = qs.filter(Q(name__icontains=q) | Q(code__icontains=q))

        return Response({
            "success": True,
            "data": {"suppliers": [_supplier_dict(s) for s in qs]},
        })

    # POST — create supplier
    data = request.data
    required = ["name"]
    for field in required:
        if not data.get(field):
            return Response(
                {"success": False, "message": f"{field} is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

    code = data.get("code") or _next_supplier_code()
    if Supplier.objects.filter(code=code).exists():
        return Response(
            {"success": False, "message": f"Supplier code {code} already exists"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    default_account_id = data.get("default_account_id") or None
    supplier = Supplier.objects.create(
        code=code,
        name=data["name"],
        email=data.get("email", ""),
        phone=data.get("phone", ""),
        address=data.get("address", ""),
        tax_id=data.get("tax_id", ""),
        currency=data.get("currency", "DKK"),
        payment_terms=int(data["payment_terms"]) if data.get("payment_terms") else 30,
        notes=data.get("notes", ""),
        default_account_id=default_account_id,
        country=(data.get("country") or "DK").upper()[:2],
        default_tax_code_id=data.get("default_tax_code_id") or None,
        is_active=data.get("is_active", True),
    )
    return Response({
        "success": True,
        "message": "Supplier created",
        "data": {"supplier": _supplier_dict(supplier)},
    }, status=status.HTTP_201_CREATED)


@api_view(["GET", "PUT", "DELETE"])
@permission_classes([RoleWriteAccess])
def suppliers_detail(request, pk):
    try:
        supplier = Supplier.objects.get(id=pk)
    except Supplier.DoesNotExist:
        return Response(
            {"success": False, "message": "Supplier not found"},
            status=status.HTTP_404_NOT_FOUND,
        )

    if request.method == "GET":
        return Response({
            "success": True,
            "data": {"supplier": _supplier_dict(supplier)},
        })

    if request.method == "PUT":
        data = request.data
        if "code" in data and data["code"] != supplier.code:
            if Supplier.objects.filter(code=data["code"]).exclude(id=pk).exists():
                return Response(
                    {"success": False, "message": "Supplier code already exists"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            supplier.code = data["code"]
        for field in ("name", "email", "phone", "address", "tax_id",
                      "currency", "notes", "is_active"):
            if field in data:
                setattr(supplier, field, data[field])
        if "payment_terms" in data:
            supplier.payment_terms = int(data["payment_terms"]) if data["payment_terms"] else 30
        if "default_account_id" in data:
            supplier.default_account_id = data["default_account_id"] or None
        if "default_tax_code_id" in data:
            supplier.default_tax_code_id = data["default_tax_code_id"] or None
        if "country" in data:
            supplier.country = (data["country"] or "DK").upper()[:2]
        supplier.save()
        return Response({
            "success": True,
            "message": "Supplier updated",
            "data": {"supplier": _supplier_dict(supplier)},
        })

    # DELETE — soft delete
    supplier.is_active = False
    supplier.save()
    return Response({"success": True, "message": "Supplier deactivated"})


@api_view(["GET"])
@permission_classes([RoleWriteAccess])
def supplier_statement(request, pk):
    """Return all bills and payments for a supplier."""
    try:
        supplier = Supplier.objects.get(id=pk)
    except Supplier.DoesNotExist:
        return Response(
            {"success": False, "message": "Supplier not found"},
            status=status.HTTP_404_NOT_FOUND,
        )

    bills = Bill.objects.filter(supplier=supplier).select_related("supplier")
    bill_data = [_bill_dict(b, include_lines=False) for b in bills]

    # Aggregate totals
    totals = bills.aggregate(
        total_billed=Sum("total"),
        total_paid=Sum("paid_amount"),
    )
    total_billed = totals["total_billed"] or Decimal("0")
    total_paid = totals["total_paid"] or Decimal("0")
    balance_due = total_billed - total_paid

    return Response({
        "success": True,
        "data": {
            "supplier": _supplier_dict(supplier),
            "bills": bill_data,
            "total_billed": str(total_billed),
            "total_paid": str(total_paid),
            "balance_due": str(balance_due),
        },
    })


# ─── Bills CRUD ──────────────────────────────────────────────────────────────

@api_view(["GET", "POST"])
@permission_classes([RoleWriteAccess])
def bills_list_create(request):
    if request.method == "GET":
        qs = Bill.objects.all()

        # Filters
        if request.query_params.get("status"):
            qs = qs.filter(status=request.query_params["status"])
        if request.query_params.get("supplier_id"):
            qs = qs.filter(supplier_id=request.query_params["supplier_id"])
        if request.query_params.get("date_from"):
            qs = qs.filter(date__gte=request.query_params["date_from"])
        if request.query_params.get("date_to"):
            qs = qs.filter(date__lte=request.query_params["date_to"])
        if request.query_params.get("search"):
            q = request.query_params["search"]
            qs = qs.filter(
                Q(bill_number__icontains=q)
                | Q(supplier__name__icontains=q)
                | Q(reference__icontains=q)
                | Q(notes__icontains=q)
            )
        if request.query_params.get("amount_min"):
            qs = qs.filter(total__gte=request.query_params["amount_min"])
        if request.query_params.get("amount_max"):
            qs = qs.filter(total__lte=request.query_params["amount_max"])
        if request.query_params.get("overdue") == "true":
            qs = qs.filter(due_date__lt=timezone.localdate()).exclude(status="paid")
        if request.query_params.get("no_supplier") == "true":
            qs = qs.filter(supplier__isnull=True)
        if request.query_params.get("has_supplier") == "true":
            qs = qs.filter(supplier__isnull=False)

        # Sorting
        sort_field = request.query_params.get("sort", "date")
        sort_dir = request.query_params.get("sort_dir", "desc")
        allowed_sort = {
            "bill_number": "bill_number",
            "supplier_name": "supplier__name",
            "date": "date",
            "due_date": "due_date",
            "subtotal": "subtotal",
            "tax_amount": "tax_amount",
            "total": "total",
            "paid_amount": "paid_amount",
            "status": "status",
        }
        order_field = allowed_sort.get(sort_field, "date")
        prefix = "-" if sort_dir == "desc" else ""
        qs = qs.order_by(f"{prefix}{order_field}", "-created_at")
        total_count = qs.count()

        # Pagination
        try:
            page = int(request.query_params.get("page", 1))
            page_size = int(request.query_params.get("page_size", 50))
        except (ValueError, TypeError):
            page, page_size = 1, 50
        page_size = min(page_size, 200)
        offset = (page - 1) * page_size
        qs = qs[offset : offset + page_size]
        qs = qs.prefetch_related("lines__account")

        return Response({
            "success": True,
            "data": {
                "bills": [_bill_dict(b, include_lines=False) for b in qs],
                "total_count": total_count,
            },
        })

    # POST — create bill with lines
    data = request.data
    for field in ("supplier_id", "date", "due_date"):
        if not data.get(field):
            return Response(
                {"success": False, "message": f"{field} is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

    try:
        supplier = Supplier.objects.get(id=data["supplier_id"])
    except Supplier.DoesNotExist:
        return Response(
            {"success": False, "message": "Supplier not found"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    lines_data = data.get("lines", [])
    if not lines_data:
        return Response(
            {"success": False, "message": "At least one line is required"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    # Validate line accounts exist
    account_ids = [line.get("account_id") for line in lines_data]
    accounts = {str(a.id): a for a in Account.objects.filter(id__in=account_ids)}
    for aid in account_ids:
        if aid not in accounts:
            return Response(
                {"success": False, "message": f"Account {aid} not found"},
                status=status.HTTP_400_BAD_REQUEST,
            )

    # Validate tax codes if provided
    from core.models import TaxCode
    tax_code_ids = [line.get("tax_code_id") for line in lines_data if line.get("tax_code_id")]
    tax_codes = {}
    if tax_code_ids:
        tax_codes = {str(tc.id): tc for tc in TaxCode.objects.filter(id__in=tax_code_ids)}
        for tcid in tax_code_ids:
            if tcid not in tax_codes:
                return Response(
                    {"success": False, "message": f"Tax code {tcid} not found"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

    bill_number = data.get("bill_number") or _next_bill_number()

    with transaction.atomic():
        bill = Bill.objects.create(
            bill_number=bill_number,
            supplier=supplier,
            date=data["date"],
            due_date=data["due_date"],
            status="draft",
            currency=(data.get("currency") or "DKK").upper(),
            exchange_rate=_rate(data),
            reference=data.get("reference", ""),
            notes=data.get("notes", ""),
            created_by=(
                f"{request.user.first_name} {request.user.last_name}".strip()
                or request.user.username
            ),
        )

        subtotal = Decimal("0")
        tax_amount = Decimal("0")

        for line_data in lines_data:
            try:
                quantity = Decimal(str(line_data.get("quantity", 1)))
                unit_price = Decimal(str(line_data.get("unit_price", 0)))
            except (InvalidOperation, TypeError):
                # Rollback handled by atomic
                return Response(
                    {"success": False, "message": "Invalid quantity or unit_price"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            line_amount = quantity * unit_price
            subtotal += line_amount

            tc = tax_codes.get(line_data.get("tax_code_id")) if line_data.get("tax_code_id") else None
            tax_amount += supplier_vat(line_amount, tc)

            BillLine.objects.create(
                bill=bill,
                description=line_data.get("description", ""),
                quantity=quantity,
                unit_price=unit_price,
                tax_code=tc,
                account_id=line_data["account_id"],
            )

        bill.subtotal = subtotal
        bill.tax_amount = tax_amount
        bill.total = subtotal + tax_amount
        bill.save()

        # Bilag fra "Læs faktura": kobl den uploadede fil til regningen.
        if data.get("document_id"):
            from core.models import Document
            Document.objects.filter(id=data["document_id"], bill=None, journal_entry=None).update(bill=bill)

    bill.refresh_from_db()
    return Response({
        "success": True,
        "message": "Bill created",
        "data": {"bill": _bill_dict(bill)},
    }, status=status.HTTP_201_CREATED)


@api_view(["GET", "PUT", "DELETE"])
@permission_classes([RoleWriteAccess])
def bills_detail(request, pk):
    try:
        bill = Bill.objects.get(id=pk)
    except Bill.DoesNotExist:
        return Response(
            {"success": False, "message": "Bill not found"},
            status=status.HTTP_404_NOT_FOUND,
        )

    if request.method == "GET":
        return Response({
            "success": True,
            "data": {"bill": _bill_dict(bill)},
        })

    if request.method == "DELETE":
        if bill.status != "draft":
            return Response(
                {"success": False, "message": "Only draft bills can be deleted"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        bill_number = bill.bill_number
        bill.delete()
        log_action(request.user, "delete", "Bill", pk, {"bill_number": bill_number})
        return Response({"success": True, "message": "Bill deleted"})

    # PUT — update. All bills can be edited. Editing a posted bill
    # (approved/paid/overdue) re-syncs its expense journal entry so the books
    # match the new lines. Existing payments are left untouched; the paid/
    # approved status is recomputed against the new total afterwards.
    if bill.status not in ("draft", "approved", "paid", "overdue"):
        return Response(
            {"success": False, "message": "This bill cannot be edited"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    data = request.data

    # Editing a posted bill deletes its journal entry (below) — refuse when that
    # entry, or the date the bill is being moved to, is in a closed fiscal year.
    if bill.journal_entry_id:
        err = closed_period_error(bill.journal_entry.date) or closed_period_error(data.get("date"))
        if err:
            return Response({"success": False, "message": err}, status=status.HTTP_400_BAD_REQUEST)

    if "supplier_id" in data:
        if data["supplier_id"]:
            try:
                supplier = Supplier.objects.get(id=data["supplier_id"])
                bill.supplier = supplier
            except Supplier.DoesNotExist:
                return Response(
                    {"success": False, "message": "Supplier not found"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
        else:
            bill.supplier = None

    for field in ("date", "due_date", "currency", "reference", "notes"):
        if field in data:
            setattr(bill, field, data[field])

    if "exchange_rate" in data or "currency" in data:
        bill.exchange_rate = _rate({"currency": bill.currency, **data})

    if "bill_number" in data and data["bill_number"] != bill.bill_number:
        if Bill.objects.filter(bill_number=data["bill_number"]).exclude(id=pk).exists():
            return Response(
                {"success": False, "message": "Bill number already exists"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        bill.bill_number = data["bill_number"]

    lines_data = data.get("lines")
    if lines_data is not None:
        if not lines_data:
            return Response(
                {"success": False, "message": "At least one line is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Validate accounts
        account_ids = [l.get("account_id") for l in lines_data]
        accounts = {str(a.id): a for a in Account.objects.filter(id__in=account_ids)}
        for aid in account_ids:
            if aid not in accounts:
                return Response(
                    {"success": False, "message": f"Account {aid} not found"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        # Validate tax codes
        from core.models import TaxCode
        tax_code_ids = [l.get("tax_code_id") for l in lines_data if l.get("tax_code_id")]
        tax_codes = {}
        if tax_code_ids:
            tax_codes = {str(tc.id): tc for tc in TaxCode.objects.filter(id__in=tax_code_ids)}

        with transaction.atomic():
            bill.lines.all().delete()
            subtotal = Decimal("0")
            tax_amount = Decimal("0")

            for line_data in lines_data:
                quantity = Decimal(str(line_data.get("quantity", 1)))
                unit_price = Decimal(str(line_data.get("unit_price", 0)))
                line_amount = quantity * unit_price
                subtotal += line_amount

                tc = tax_codes.get(line_data.get("tax_code_id")) if line_data.get("tax_code_id") else None
                tax_amount += supplier_vat(line_amount, tc)

                BillLine.objects.create(
                    bill=bill,
                    description=line_data.get("description", ""),
                    quantity=quantity,
                    unit_price=unit_price,
                    tax_code=tc,
                    account_id=line_data["account_id"],
                )

            bill.subtotal = subtotal
            bill.tax_amount = tax_amount
            bill.total = subtotal + tax_amount
            bill.save()
    else:
        bill.save()

    # Editing a posted bill pulls it back to draft and removes its journal
    # entry — it must be approved again to re-post. Any payments (paid_amount /
    # payment links) are left untouched; the paid status is recomputed when the
    # bill is re-approved.
    if bill.status != "draft" and bill.journal_entry_id:
        with transaction.atomic():
            entry = bill.journal_entry
            bill.status = "draft"
            bill.journal_entry = None
            bill.save(update_fields=["status", "journal_entry"])
            entry.lines.all().delete()
            entry.delete()

    bill.refresh_from_db()
    return Response({
        "success": True,
        "message": "Bill updated",
        "data": {"bill": _bill_dict(bill)},
    })


def _post_bill_journal_lines(entry, bill, ap_account):
    """Regningens linjer på den (tomme) postering, efter momskoden pr. linje
    (core/vat.py: add_purchase): DR omkostning (+ ikke-fradragsberettiget moms),
    DR købsmoms, ved omvendt betalingspligt CR moms af køb i udlandet, og CR
    kreditorer for det, leverandøren skal have. Beløb omregnes til DKK med kursen."""
    fx = {"currency": bill.currency, "exchange_rate": bill.exchange_rate} \
        if bill.currency != chart.BASE_CURRENCY else {}
    rate = bill.exchange_rate if fx else Decimal("1")
    builder = EntryBuilder(fx=fx)
    label = f"Regning {bill.bill_number} — {bill.supplier.name}"
    for line in bill.lines.select_related("account", "tax_code").all():
        net = (Decimal(line.amount) * rate).quantize(_CENT, ROUND_HALF_UP)
        add_purchase(builder, line.account, net, line.tax_code, label)
    payable = builder.balance
    builder.add(ap_account, -payable, description=label, partner=supplier_partner(bill.supplier))
    builder.write(entry)
    # Regningens total (i dens valuta) følger det bogførte.
    return payable


def _approve_bill(bill, created_by):
    """Approve a single bill: create journal entry (DR expense, CR AP).

    Returns (True, None) on success or (False, "error message") on failure.
    """
    if bill.status != "draft":
        return False, "Only draft bills can be approved"

    err = closed_period_error(bill.date)
    if err:
        return False, err

    if not bill.supplier:
        return False, "Supplier must be assigned before approving"

    try:
        ap_account = Account.objects.get(code=chart.PAYABLE)
    except Account.DoesNotExist:
        return False, f"Kreditorkontoen ({chart.PAYABLE}) findes ikke"

    lines = bill.lines.select_related("account", "tax_code").all()
    if not lines:
        return False, "Bill has no lines"

    with transaction.atomic():
        entry = JournalEntry.objects.create(
            entry_number=_next_je_entry_number(),
            date=bill.date,
            description=f"Bill {bill.bill_number} — {bill.supplier.name}",
            reference=bill.bill_number,
            piece_number=bill.bill_number,
            source="expense",
            is_posted=True,
            created_by=created_by,
        )

        _post_bill_journal_lines(entry, bill, ap_account)

        bill.journal_entry = entry
        # A bill that was already (fully) paid before being edited and pulled
        # back to draft returns straight to "paid" on re-approval; otherwise it
        # becomes "approved".
        if bill.total > 0 and bill.paid_amount >= bill.total:
            bill.status = "paid"
        else:
            bill.status = "approved"
        bill.save()

    return True, None


_CENT = Decimal("0.01")


def _split_vat_inclusive(gross, rate):
    """Split a VAT-inclusive amount into (base, vat) with vat as the EXACT
    remainder, so base + vat == gross always — the invariant every bank-money
    flow depends on (the gross is what actually left the bank)."""
    base = (gross / (Decimal("1") + rate / Decimal("100"))).quantize(_CENT)
    return base, gross - base


def _validate_bank_line_for_matching(jel):
    """Why this journal line can't be matched to a bill, or None if it can.

    Mirrors the categorize guards: only real bank lines, and never a line that is
    already categorized (a line must be reconciled exactly one way)."""
    if jel.journal_entry.source != "bank" or not (jel.account and chart.is_treasury(jel.account.code)):
        return "Not a bank transaction line"
    if not (jel.credit and jel.credit > 0):
        # A bill payment is money OUT. Incoming money is categorized instead
        # (revenue/refund/deposit), never matched to a bill.
        return "Only outgoing transactions can be matched to bills"
    if BankTransactionCategorization.objects.filter(journal_entry_line=jel).exists():
        return "This transaction is already categorized"
    return None


def _bank_line_remaining(jel):
    """How much of the bank line's cash is not yet allocated to bills. One transfer
    may legitimately pay several bills, but the links must never exceed the money
    that actually moved."""
    txn_amount = jel.credit if (jel.credit and jel.credit > 0) else jel.debit
    linked = BillPaymentLink.objects.filter(journal_entry_line=jel).aggregate(
        total=Sum("amount"))["total"] or Decimal("0")
    return (txn_amount or Decimal("0")) - linked


def _apply_bill_payment(bill, jel, amount, matched_by):
    """Link a bank line to a bill AND post the clearing entry.

    Importen parkerede banklinjen på mellemregningskontoen; godkendelsen bogførte DR
    omkostning / CR kreditorer. Mellemregningsbenet bliver DR kreditorer, så
    betalingen er DR kreditorer / CR bank.
    Returns (link, error).

    Caller must hold transaction.atomic() with the bill row locked
    (select_for_update) — paid_amount is read-modify-write."""
    if amount is None or amount <= 0:
        return None, "Amount must be positive"

    err = closed_period_error(jel.journal_entry.date)
    if err:
        return None, err

    balance_due = (bill.total or Decimal("0")) - (bill.paid_amount or Decimal("0"))
    if amount > balance_due + _CENT:
        return None, f"Amount exceeds the bill's remaining balance ({balance_due})"

    remaining = _bank_line_remaining(jel)
    if amount > remaining + _CENT:
        return None, f"Amount exceeds the transaction's unallocated amount ({remaining})"

    try:
        ap_account = Account.objects.get(code=chart.PAYABLE)
    except Account.DoesNotExist:
        return None, f"Kreditorkontoen ({chart.PAYABLE}) findes ikke"

    # Omposter `amount` af bankposteringens mellemregningsben til kreditorer, så
    # betalingen er DR kreditorer / CR bank.
    be = jel.journal_entry
    outgoing = bool(jel.credit and jel.credit > 0)   # a bill payment is money OUT
    susp = be.lines.filter(account__code=chart.SUSPENSE).first()
    if susp:
        if outgoing:
            susp.debit = (susp.debit or Decimal("0")) - amount
        else:
            susp.credit = (susp.credit or Decimal("0")) - amount
        if (susp.debit or Decimal("0")) <= 0 and (susp.credit or Decimal("0")) <= 0:
            susp.delete()
        else:
            susp.save()
    JournalEntryLine.objects.create(
        journal_entry=be, account=ap_account,
        debit=amount if outgoing else Decimal("0"),
        credit=Decimal("0") if outgoing else amount,
        currency=jel.currency, description=f"Payment {bill.bill_number}",
        **supplier_partner(bill.supplier),
    )

    link = BillPaymentLink.objects.create(
        bill=bill, journal_entry_line=jel, amount=amount,
        matched_by=matched_by, clearing_entry=None,
    )
    bill.paid_amount = (bill.paid_amount or Decimal("0")) + amount
    if bill.total > 0 and bill.paid_amount >= bill.total:
        bill.status = "paid"
        auto_lettrer(_bill_ap_lines(bill))
    bill.save()
    return link, None


def _bill_ap_lines(bill):
    """Regningens kreditorlinje og betalingernes kreditorben (udlignes sammen)."""
    lines = []
    if bill.journal_entry_id:
        lines += list(bill.journal_entry.lines.filter(account__code=chart.PAYABLE).select_related("journal_entry"))
    for link in bill.payment_links.select_related("journal_entry_line__journal_entry"):
        lines += list(link.journal_entry_line.journal_entry.lines.filter(
            account__code=chart.PAYABLE, description=f"Payment {bill.bill_number}").select_related("journal_entry"))
    return lines


@api_view(["POST"])
@permission_classes([RoleWriteAccess])
def bill_approve(request, pk):
    """Approve a bill: create journal entry (DR expense accounts, CR Accounts Payable)."""
    try:
        bill = Bill.objects.get(id=pk)
    except Bill.DoesNotExist:
        return Response(
            {"success": False, "message": "Bill not found"},
            status=status.HTTP_404_NOT_FOUND,
        )

    created_by = (
        f"{request.user.first_name} {request.user.last_name}".strip()
        or request.user.username
    )

    ok, err = _approve_bill(bill, created_by)
    if not ok:
        return Response(
            {"success": False, "message": err},
            status=status.HTTP_400_BAD_REQUEST,
        )

    bill.refresh_from_db()
    log_action(request.user, "approve", "Bill", bill.id,
               {"bill_number": bill.bill_number, "total": str(bill.total)})
    return Response({
        "success": True,
        "message": "Bill approved and journal entry created",
        "data": {"bill": _bill_dict(bill)},
    })


@api_view(["POST"])
@permission_classes([RoleWriteAccess])
def bills_bulk_approve(request):
    """Bulk-approve draft bills that have a supplier assigned."""
    bill_ids = request.data.get("bill_ids", [])
    if not bill_ids:
        return Response(
            {"success": False, "message": "No bill IDs provided"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    created_by = (
        f"{request.user.first_name} {request.user.last_name}".strip()
        or request.user.username
    )

    bills = Bill.objects.filter(
        id__in=bill_ids, status="draft", supplier__isnull=False
    )

    approved_count = 0
    errors = []
    for bill in bills:
        ok, err = _approve_bill(bill, created_by)
        if ok:
            approved_count += 1
        else:
            errors.append(f"{bill.bill_number}: {err}")

    return Response({
        "success": True,
        "approved_count": approved_count,
        "errors": errors,
    })


@api_view(["POST"])
@permission_classes([RoleWriteAccess])
def bill_move_to_expenses(request, pk):
    """Move a draft bill to expenses: create one Expense per BillLine, then delete the bill."""
    try:
        bill = Bill.objects.get(id=pk)
    except Bill.DoesNotExist:
        return Response(
            {"success": False, "message": "Bill not found"},
            status=status.HTTP_404_NOT_FOUND,
        )

    if bill.status != "draft":
        return Response(
            {"success": False, "message": "Only draft bills can be moved to expenses"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    lines = bill.lines.select_related("account", "tax_code").all()
    if not lines:
        return Response(
            {"success": False, "message": "Bill has no lines"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    # Validate all lines have an account
    missing = [i + 1 for i, line in enumerate(lines) if not line.account_id]
    if missing:
        return Response(
            {"success": False, "message": f"All bill lines must have an account. Lines missing account: {missing}"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    created_by = (
        f"{request.user.first_name} {request.user.last_name}".strip()
        or request.user.username
    )

    reference = bill.reference or bill.bill_number

    with transaction.atomic():
        for line in lines:
            Expense.objects.create(
                date=bill.date,
                supplier=bill.supplier,
                description=line.description or f"From bill {bill.bill_number}",
                amount=line.amount,
                tax_code=line.tax_code,
                account=line.account,
                payment_method="bank_transfer",
                reference=reference,
                status="pending",
                created_by=created_by,
            )
        expense_count = len(lines)
        bill.delete()

    return Response({
        "success": True,
        "message": f"Bill moved to {expense_count} expense(s)",
        "data": {"expense_count": expense_count},
    })


# ─── Expenses CRUD ───────────────────────────────────────────────────────────

def _parse_expense_lines(data):
    """Read the optional split `lines` field (a JSON string in multipart, or a
    list). Returns (lines_list_or_None, error_message_or_None)."""
    raw = data.get("lines")
    if not raw:
        return None, None
    if isinstance(raw, str):
        import json
        try:
            raw = json.loads(raw)
        except (ValueError, TypeError):
            return None, "Invalid lines payload"
    if not isinstance(raw, list):
        return None, "Invalid lines payload"
    # Drop fully-empty rows
    raw = [l for l in raw if l and (l.get("account_id") or l.get("amount"))]
    return raw, None


def _build_expense_allocation(lines_data):
    """Validate split lines. Returns (allocations, total, error_message).

    allocations: list of {account, tax_code, amount, description}.
    """
    from core.models import TaxCode
    account_ids = [l.get("account_id") for l in lines_data]
    if not account_ids or any(not a for a in account_ids):
        return None, None, "Each split line needs an account"
    accounts = {str(a.id): a for a in Account.objects.filter(id__in=account_ids)}
    for aid in account_ids:
        if aid not in accounts:
            return None, None, f"Account {aid} not found"
    tax_ids = [l.get("tax_code_id") for l in lines_data if l.get("tax_code_id")]
    tax_codes = {str(tc.id): tc for tc in TaxCode.objects.filter(id__in=tax_ids)} if tax_ids else {}
    allocs = []
    total = Decimal("0")
    for l in lines_data:
        try:
            amt = Decimal(str(l.get("amount", 0)))
        except (InvalidOperation, TypeError):
            return None, None, "Invalid line amount"
        allocs.append({
            "account": accounts[str(l["account_id"])],
            "tax_code": tax_codes.get(str(l.get("tax_code_id"))) if l.get("tax_code_id") else None,
            "amount": amt,
            "description": l.get("description", ""),
        })
        total += amt
    return allocs, total, None


@api_view(["GET", "POST"])
@permission_classes([RoleWriteAccess])
@parser_classes([MultiPartParser, FormParser])
def expenses_list_create(request):
    if request.method == "GET":
        qs = Expense.objects.select_related("supplier", "account", "tax_code")

        # Filters
        if request.query_params.get("status"):
            qs = qs.filter(status=request.query_params["status"])
        if request.query_params.get("date_from"):
            qs = qs.filter(date__gte=request.query_params["date_from"])
        if request.query_params.get("date_to"):
            qs = qs.filter(date__lte=request.query_params["date_to"])
        if request.query_params.get("search"):
            q = request.query_params["search"]
            qs = qs.filter(
                Q(description__icontains=q)
                | Q(reference__icontains=q)
                | Q(supplier__name__icontains=q)
            )

        return Response({
            "success": True,
            "data": {"expenses": [_expense_dict(e) for e in qs]},
        })

    # POST — create expense (supports split lines via `lines`)
    data = request.data
    if not data.get("date") or not data.get("description"):
        return Response(
            {"success": False, "message": "date and description are required"},
            status=status.HTTP_400_BAD_REQUEST,
        )
    receipt_err = validate_upload(request.FILES.get("receipt"))
    if receipt_err:
        return Response({"success": False, "message": receipt_err}, status=status.HTTP_400_BAD_REQUEST)

    lines_data, lerr = _parse_expense_lines(data)
    if lerr:
        return Response({"success": False, "message": lerr}, status=status.HTTP_400_BAD_REQUEST)

    supplier = None
    if data.get("supplier_id"):
        try:
            supplier = Supplier.objects.get(id=data["supplier_id"])
        except Supplier.DoesNotExist:
            return Response(
                {"success": False, "message": "Supplier not found"},
                status=status.HTTP_400_BAD_REQUEST,
            )

    created_by = (
        f"{request.user.first_name} {request.user.last_name}".strip()
        or request.user.username
    )

    if lines_data:
        allocs, total, aerr = _build_expense_allocation(lines_data)
        if aerr:
            return Response({"success": False, "message": aerr}, status=status.HTTP_400_BAD_REQUEST)
        if not allocs:
            return Response(
                {"success": False, "message": "At least one line is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        with transaction.atomic():
            expense = Expense.objects.create(
                date=data["date"], supplier=supplier, description=data["description"],
                amount=total, tax_code=allocs[0]["tax_code"], account=allocs[0]["account"],
                payment_method=data.get("payment_method", "bank_transfer"),
                reference=data.get("reference", ""), receipt=request.FILES.get("receipt"),
                status="pending", created_by=created_by,
            )
            for a in allocs:
                ExpenseLine.objects.create(
                    expense=expense, description=a["description"], account=a["account"],
                    tax_code=a["tax_code"], amount=a["amount"],
                )
        return Response({
            "success": True, "message": "Expense created",
            "data": {"expense": _expense_dict(expense)},
        }, status=status.HTTP_201_CREATED)

    # Legacy single-account expense
    for field in ("amount", "account_id"):
        if not data.get(field):
            return Response(
                {"success": False, "message": f"{field} is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )
    try:
        amount = Decimal(str(data["amount"]))
    except (InvalidOperation, TypeError):
        return Response(
            {"success": False, "message": "Invalid amount"},
            status=status.HTTP_400_BAD_REQUEST,
        )
    try:
        account = Account.objects.get(id=data["account_id"])
    except Account.DoesNotExist:
        return Response(
            {"success": False, "message": "Account not found"},
            status=status.HTTP_400_BAD_REQUEST,
        )
    tax_code = None
    if data.get("tax_code_id"):
        from core.models import TaxCode
        try:
            tax_code = TaxCode.objects.get(id=data["tax_code_id"])
        except TaxCode.DoesNotExist:
            return Response(
                {"success": False, "message": "Tax code not found"},
                status=status.HTTP_400_BAD_REQUEST,
            )

    receipt_err = validate_upload(request.FILES.get("receipt"))
    if receipt_err:
        return Response({"success": False, "message": receipt_err}, status=status.HTTP_400_BAD_REQUEST)

    expense = Expense.objects.create(
        date=data["date"],
        supplier=supplier,
        description=data["description"],
        amount=amount,
        tax_code=tax_code,
        account=account,
        payment_method=data.get("payment_method", "bank_transfer"),
        reference=data.get("reference", ""),
        receipt=request.FILES.get("receipt"),
        status="pending",
        created_by=created_by,
    )

    return Response({
        "success": True,
        "message": "Expense created",
        "data": {"expense": _expense_dict(expense)},
    }, status=status.HTTP_201_CREATED)


@api_view(["GET", "PUT", "DELETE"])
@permission_classes([RoleWriteAccess])
@parser_classes([MultiPartParser, FormParser])
def expenses_detail(request, pk):
    try:
        expense = Expense.objects.select_related("supplier", "account", "tax_code").get(id=pk)
    except Expense.DoesNotExist:
        return Response(
            {"success": False, "message": "Expense not found"},
            status=status.HTTP_404_NOT_FOUND,
        )

    if request.method == "GET":
        return Response({
            "success": True,
            "data": {"expense": _expense_dict(expense)},
        })

    if request.method == "DELETE":
        if expense.status == "approved":
            return Response(
                {"success": False, "message": "Cannot delete an approved expense"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        expense_desc = expense.description
        expense.delete()
        log_action(request.user, "delete", "Expense", pk, {"description": expense_desc})
        return Response({"success": True, "message": "Expense deleted"})

    # PUT — update
    if expense.status == "approved":
        return Response(
            {"success": False, "message": "Cannot edit an approved expense"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    data = request.data

    if "account_id" in data:
        try:
            expense.account = Account.objects.get(id=data["account_id"])
        except Account.DoesNotExist:
            return Response(
                {"success": False, "message": "Account not found"},
                status=status.HTTP_400_BAD_REQUEST,
            )

    if "supplier_id" in data:
        if data["supplier_id"]:
            try:
                expense.supplier = Supplier.objects.get(id=data["supplier_id"])
            except Supplier.DoesNotExist:
                return Response(
                    {"success": False, "message": "Supplier not found"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
        else:
            expense.supplier = None

    if "tax_code_id" in data:
        if data["tax_code_id"]:
            from core.models import TaxCode
            try:
                expense.tax_code = TaxCode.objects.get(id=data["tax_code_id"])
            except TaxCode.DoesNotExist:
                return Response(
                    {"success": False, "message": "Tax code not found"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
        else:
            expense.tax_code = None

    if "amount" in data:
        try:
            expense.amount = Decimal(str(data["amount"]))
        except (InvalidOperation, TypeError):
            return Response(
                {"success": False, "message": "Invalid amount"},
                status=status.HTTP_400_BAD_REQUEST,
            )

    # Not "status": approval goes through expense_approve, which posts the entry.
    # Setting "approved" here gave an approved expense with no journal entry.
    for field in ("date", "description", "payment_method", "reference"):
        if field in data:
            setattr(expense, field, data[field])

    if request.FILES.get("receipt"):
        receipt_err = validate_upload(request.FILES["receipt"])
        if receipt_err:
            return Response({"success": False, "message": receipt_err}, status=status.HTTP_400_BAD_REQUEST)
        expense.receipt = request.FILES["receipt"]

    lines_data, lerr = _parse_expense_lines(data)
    if lerr:
        return Response({"success": False, "message": lerr}, status=status.HTTP_400_BAD_REQUEST)

    if lines_data is not None:
        allocs, total, aerr = _build_expense_allocation(lines_data)
        if aerr:
            return Response({"success": False, "message": aerr}, status=status.HTTP_400_BAD_REQUEST)
        if not allocs:
            return Response(
                {"success": False, "message": "At least one line is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        with transaction.atomic():
            expense.amount = total
            expense.account = allocs[0]["account"]
            expense.tax_code = allocs[0]["tax_code"]
            expense.save()
            expense.lines.all().delete()
            for a in allocs:
                ExpenseLine.objects.create(
                    expense=expense, description=a["description"], account=a["account"],
                    tax_code=a["tax_code"], amount=a["amount"],
                )
    else:
        expense.save()

    # Refresh to get updated select_related fields
    expense = Expense.objects.select_related("supplier", "account", "tax_code").get(id=pk)
    return Response({
        "success": True,
        "message": "Expense updated",
        "data": {"expense": _expense_dict(expense)},
    })


@api_view(["POST"])
@permission_classes([RoleWriteAccess])
def expense_approve(request, pk):
    """Godkend en kontant udgift: kassejournalen, DR omkostning (+ købsmoms) / CR kasse."""
    try:
        expense = Expense.objects.select_related("supplier", "account", "tax_code").get(id=pk)
    except Expense.DoesNotExist:
        return Response(
            {"success": False, "message": "Expense not found"},
            status=status.HTTP_404_NOT_FOUND,
        )

    if expense.status != "pending":
        return Response(
            {"success": False, "message": "Only pending expenses can be approved"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    err = closed_period_error(expense.date)
    if err:
        return Response({"success": False, "message": err}, status=status.HTTP_400_BAD_REQUEST)

    # Udgifter betales af kassen og går i kassejournalen (KAS). Money
    # that left a bank is booked from the bank statement (categorise the line, or
    # enter a bill and match the payment); booking it here too counted it twice.
    cr_account = None
    chosen = request.data.get("bank_account_id")
    if chosen:
        cr_account = chart.treasury_accounts().filter(id=chosen).first()
        if not cr_account:
            return Response({"success": False, "message": "Bank/cash account not found"},
                            status=status.HTTP_400_BAD_REQUEST)
    else:
        cr_account = Account.objects.filter(code=chart.CASH, is_active=True).first()
        if not cr_account:
            return Response({"success": False, "message": f"Account {chart.CASH} not found"},
                            status=status.HTTP_400_BAD_REQUEST)
    if not chart.is_cash(cr_account.code):
        return Response({"success": False, "message": (
            "Only cash expenses are booked here. An expense paid by bank is booked from the bank "
            "statement: categorise its line on Bank transactions, or enter a bill and match the payment.")},
            status=status.HTTP_400_BAD_REQUEST)

    created_by = (
        f"{request.user.first_name} {request.user.last_name}".strip()
        or request.user.username
    )

    expense_ref = _next_expense_number()

    with transaction.atomic():
        from journals.journal_for import journal_for_account
        entry = JournalEntry.objects.create(
            # Paid in cash → CA; from a bank → that bank's journal.
            journal=journal_for_account(cr_account) or None,
            entry_number=_next_je_entry_number(),
            piece_number=expense_ref,
            date=expense.date,
            description=f"Expense: {expense.description}",
            reference=expense_ref,
            source="expense",
            is_posted=True,
            created_by=created_by,
        )

        # Linjer efter momskoden (core/vat.py), CR kasse/bank for det betalte.
        builder = EntryBuilder()
        exp_lines = list(expense.lines.select_related("account", "tax_code").all())
        if exp_lines:
            for ln in exp_lines:
                net = Decimal(ln.amount).quantize(_CENT, ROUND_HALF_UP)
                add_purchase(builder, ln.account, net, ln.tax_code, expense.description)
        else:
            add_purchase(builder, expense.account, Decimal(expense.amount).quantize(_CENT, ROUND_HALF_UP),
                         expense.tax_code, expense.description)
        builder.add(cr_account, -builder.balance, description=expense.description)
        builder.write(entry)

        # Update expense
        expense.status = "approved"
        expense.journal_entry = entry
        expense.save()

    expense = Expense.objects.select_related("supplier", "account", "tax_code").get(id=pk)
    log_action(request.user, "approve", "Expense", expense.id,
               {"amount": str(expense.amount), "reference": expense_ref})
    return Response({
        "success": True,
        "message": "Expense approved and journal entry created",
        "data": {"expense": _expense_dict(expense)},
    })


# ─── Supplier Import / Export ────────────────────────────────────────────────

def _parse_import_file(f):
    """Parse CSV or Excel file and return list of dicts (rows)."""
    filename = getattr(f, "name", "").lower()
    if filename.endswith((".xlsx", ".xls")):
        import openpyxl
        # Ensure file pointer is at start and wrap in BytesIO for openpyxl
        raw = f.read()
        wb = openpyxl.load_workbook(io.BytesIO(raw), read_only=True, data_only=True)
        ws = wb.active
        rows_iter = ws.iter_rows(values_only=True)
        header_row = next(rows_iter, None)
        if not header_row:
            return None, "Empty spreadsheet"
        headers = [str(h).strip().lower() if h else "" for h in header_row]
        parsed = []
        for row in rows_iter:
            if all(c is None or str(c).strip() == "" for c in row):
                continue
            d = {}
            for i, h in enumerate(headers):
                if h and i < len(row):
                    val = row[i]
                    if val is None:
                        d[h] = ""
                    elif hasattr(val, "isoformat"):
                        # datetime/date objects from Excel → ISO string
                        d[h] = val.isoformat().split("T")[0] if hasattr(val, "date") else val.isoformat()
                    else:
                        d[h] = str(val).strip()
                elif h:
                    d[h] = ""
            parsed.append(d)
        wb.close()
        return parsed, None
    else:
        try:
            text = f.read().decode("utf-8-sig")
        except UnicodeDecodeError:
            return None, "File must be UTF-8 encoded"
        reader = csv.DictReader(io.StringIO(text))
        if not reader.fieldnames:
            return None, "Empty or invalid CSV"
        return list(reader), None


@api_view(["POST"])
@parser_classes([MultiPartParser, FormParser])
@permission_classes([RoleWriteAccess])
def suppliers_import_preview(request):
    """Parse uploaded CSV/Excel and return preview with duplicate detection."""
    f = request.FILES.get("file")
    if not f:
        return Response({"success": False, "message": "No file uploaded"}, status=400)

    parsed_rows, err = _parse_import_file(f)
    if err:
        return Response({"success": False, "message": err}, status=400)
    if not parsed_rows:
        return Response({"success": False, "message": "No data found in file"}, status=400)

    existing_codes = {s.code: s for s in Supplier.objects.all()}
    existing_names = {s.name.lower(): s for s in Supplier.objects.all()}
    rows = []

    for i, row in enumerate(parsed_rows, start=1):
        name = (row.get("name") or "").strip()
        code = (row.get("code") or "").strip()
        email = (row.get("email") or "").strip()
        phone = (row.get("phone") or "").strip()
        address = (row.get("address") or "").strip()
        tax_id = (row.get("tax_id") or "").strip()
        currency = (row.get("currency") or "DKK").strip().upper()
        payment_terms = (row.get("payment_terms") or "").strip()
        notes = (row.get("notes") or "").strip()

        errors = []
        if not name:
            errors.append("name is required")

        if email and not re.match(r"[^@]+@[^@]+\.[^@]+", email):
            errors.append("invalid email format")

        if payment_terms:
            try:
                int(payment_terms)
            except ValueError:
                errors.append("payment_terms must be an integer")

        if currency and len(currency) != 3:
            errors.append("currency must be 3 characters")

        row_status = "new"
        existing_id = None
        if errors:
            row_status = "error"
        elif code and code in existing_codes:
            row_status = "duplicate"
            existing_id = str(existing_codes[code].id)
        elif name and name.lower() in existing_names:
            row_status = "duplicate"
            existing_id = str(existing_names[name.lower()].id)

        rows.append({
            "row_number": i,
            "status": row_status,
            "existing_id": existing_id,
            "errors": errors,
            "data": {
                "code": code,
                "name": name,
                "email": email,
                "phone": phone,
                "address": address,
                "tax_id": tax_id,
                "currency": currency or "DKK",
                "payment_terms": payment_terms or "30",
                "notes": notes,
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
def suppliers_import_confirm(request):
    """Create or update suppliers from previewed data."""
    rows = request.data.get("rows", [])
    update_existing = request.data.get("update_existing", False)

    created = 0
    updated = 0
    errors = []

    with transaction.atomic():
        for r in rows:
            if r.get("status") == "error":
                continue

            data = r.get("data", {})
            name = data.get("name", "").strip()
            if not name:
                continue

            if r.get("status") == "duplicate" and update_existing and r.get("existing_id"):
                try:
                    supplier = Supplier.objects.get(id=r["existing_id"])
                    supplier.name = name
                    if data.get("email"):
                        supplier.email = data["email"]
                    if data.get("phone"):
                        supplier.phone = data["phone"]
                    if data.get("address"):
                        supplier.address = data["address"]
                    if data.get("tax_id"):
                        supplier.tax_id = data["tax_id"]
                    if data.get("currency"):
                        supplier.currency = data["currency"]
                    if data.get("payment_terms"):
                        supplier.payment_terms = int(data["payment_terms"])
                    if data.get("notes"):
                        supplier.notes = data["notes"]
                    supplier.save()
                    updated += 1
                except Supplier.DoesNotExist:
                    errors.append(f"Row {r.get('row_number')}: supplier not found")
            elif r.get("status") == "new":
                code = data.get("code") or _next_supplier_code()
                Supplier.objects.create(
                    code=code,
                    name=name,
                    email=data.get("email", ""),
                    phone=data.get("phone", ""),
                    address=data.get("address", ""),
                    tax_id=data.get("tax_id", ""),
                    currency=data.get("currency", "DKK"),
                    payment_terms=int(data.get("payment_terms", 30)),
                    notes=data.get("notes", ""),
                )
                created += 1

    return Response({
        "success": True,
        "created": created,
        "updated": updated,
        "errors": errors,
    })


# ─── Bill Export (server-side CSV) ───────────────────────────────────────────

@api_view(["GET"])
@permission_classes([RoleWriteAccess])
def bills_export(request):
    """Export all bills (with lines) as a flat CSV."""
    qs = Bill.objects.prefetch_related(
        "lines__account", "lines__tax_code"
    ).all()

    if request.query_params.get("status"):
        qs = qs.filter(status=request.query_params["status"])
    if request.query_params.get("supplier_id"):
        qs = qs.filter(supplier_id=request.query_params["supplier_id"])
    if request.query_params.get("date_from"):
        qs = qs.filter(date__gte=request.query_params["date_from"])
    if request.query_params.get("date_to"):
        qs = qs.filter(date__lte=request.query_params["date_to"])
    if request.query_params.get("amount_min"):
        qs = qs.filter(total__gte=request.query_params["amount_min"])
    if request.query_params.get("amount_max"):
        qs = qs.filter(total__lte=request.query_params["amount_max"])
    if request.query_params.get("overdue") == "true":
        qs = qs.filter(due_date__lt=timezone.localdate()).exclude(status="paid")
    if request.query_params.get("no_supplier") == "true":
        qs = qs.filter(supplier__isnull=True)

    response = HttpResponse(content_type="text/csv; charset=utf-8")
    response["Content-Disposition"] = 'attachment; filename="bills.csv"'
    response.write("\ufeff")

    writer = SafeWriter(response)
    writer.writerow([
        "bill_number", "supplier_code", "supplier_name", "date", "due_date",
        "status", "reference", "currency", "exchange_rate", "created_by",
        "line_description", "line_quantity",
        "line_unit_price", "line_account_code", "line_tax_code", "line_amount",
        "subtotal", "tax_amount", "total",
    ])

    for bill in qs:
        lines = bill.lines.select_related("account", "tax_code").all()
        sup_code = bill.supplier.code if bill.supplier else ""
        sup_name = bill.supplier.name if bill.supplier else ""
        vq = str(bill.exchange_rate)
        vy = bill.created_by
        if lines:
            for line in lines:
                writer.writerow([
                    bill.bill_number, sup_code, sup_name,
                    bill.date.isoformat(), bill.due_date.isoformat(),
                    bill.status, bill.reference, bill.currency, vq, vy,
                    line.description, str(line.quantity), str(line.unit_price),
                    line.account.code if line.account else "",
                    line.tax_code.code if line.tax_code else "",
                    str(line.amount),
                    str(bill.subtotal), str(bill.tax_amount), str(bill.total),
                ])
        else:
            writer.writerow([
                bill.bill_number, sup_code, sup_name,
                bill.date.isoformat(), bill.due_date.isoformat(),
                bill.status, bill.reference, bill.currency, vq, vy,
                "", "", "", "", "", "",
                str(bill.subtotal), str(bill.tax_amount), str(bill.total),
            ])

    return response


# ─── Bill Import ─────────────────────────────────────────────────────────────
#
# Expected columns:
#   supplier, document_type, document_no, description, invoice_date,
#   due_date, currency, amount, account, tax_code, status, notes
#

@api_view(["POST"])
@parser_classes([MultiPartParser, FormParser])
@permission_classes([RoleWriteAccess])
def bills_import_preview(request):
    """Parse uploaded CSV/Excel and return preview of bills to create."""
    f = request.FILES.get("file")
    if not f:
        return Response({"success": False, "message": "No file uploaded"}, status=400)

    parsed_rows, err = _parse_import_file(f)
    if err:
        return Response({"success": False, "message": err}, status=400)
    if not parsed_rows:
        return Response({"success": False, "message": "No data found in file"}, status=400)

    # Build lookup maps
    suppliers_by_code = {s.code.lower(): s for s in Supplier.objects.all()}
    suppliers_by_name = {s.name.lower(): s for s in Supplier.objects.all()}
    accounts_by_code = {a.code: a for a in Account.objects.filter(is_active=True)}
    from core.models import TaxCode
    tax_codes_by_code = {tc.code.lower(): tc for tc in TaxCode.objects.all()}

    existing_doc_nos = set(
        Bill.objects.exclude(reference="").values_list("reference", flat=True)
    )

    rows = []
    for i, row in enumerate(parsed_rows, start=1):
        supplier_name = (row.get("supplier") or row.get("leverandør") or row.get("supplier_name") or "").strip()
        supplier_code = (row.get("supplier mr") or row.get("supplier_code") or row.get("leverandør nr") or "").strip()
        bill_number_raw = (row.get("regning nr") or row.get("bill_number") or row.get("regningsnr") or "").strip()
        document_type = (row.get("document_type") or row.get("dokumenttype") or row.get("type") or "").strip()
        document_no = (row.get("document_no") or row.get("dokumentnr") or row.get("document_number") or bill_number_raw or "").strip()
        line_text = (row.get("description") or row.get("beskrivelse") or row.get("tekst") or "").strip()
        invoice_date = (row.get("invoice_date") or row.get("fakturadato") or row.get("date") or row.get("dato") or "").strip()
        due_date = (row.get("due_date") or row.get("forfaldsdato") or "").strip()
        currency = (row.get("currency") or row.get("valuta") or "DKK").strip().upper()
        amount = (row.get("amount") or row.get("beløb") or "0").strip()
        account_code = (row.get("account") or row.get("konto") or row.get("account_code") or "").strip()
        tax_code = (row.get("tax_code") or row.get("momskode") or "").strip()
        bill_status = (row.get("status") or "").strip()
        notes = (row.get("notes") or row.get("bemærkninger") or "").strip()

        errors = []

        # Resolve supplier by name, then by code — not required at preview time
        supplier_id = None
        resolved_supplier_name = supplier_name
        # Try by supplier name first
        if supplier_name and supplier_name.lower() in suppliers_by_name:
            s = suppliers_by_name[supplier_name.lower()]
            supplier_id = str(s.id)
            resolved_supplier_name = s.name
        elif supplier_name and supplier_name.lower() in suppliers_by_code:
            s = suppliers_by_code[supplier_name.lower()]
            supplier_id = str(s.id)
            resolved_supplier_name = s.name
        # Try by supplier_code column (supplier mr)
        if not supplier_id and supplier_code and supplier_code.lower() in suppliers_by_code:
            s = suppliers_by_code[supplier_code.lower()]
            supplier_id = str(s.id)
            resolved_supplier_name = s.name

        # Resolve account (optional)
        account_id = None
        if account_code and account_code in accounts_by_code:
            account_id = str(accounts_by_code[account_code].id)

        # Resolve tax code (optional)
        tax_code_id = None
        if tax_code and tax_code.lower() in tax_codes_by_code:
            tax_code_id = str(tax_codes_by_code[tax_code.lower()].id)

        # Validate amount format only
        try:
            float(amount) if amount else 0
        except ValueError:
            errors.append(f"Invalid amount: {amount}")

        description = line_text or " | ".join(p for p in (document_type, document_no) if p) or supplier_name

        row_status = "new"
        if errors:
            row_status = "error"
        elif document_no and document_no in existing_doc_nos:
            row_status = "duplicate"

        rows.append({
            "row_number": i,
            "status": row_status,
            "errors": errors,
            "data": {
                "supplier": resolved_supplier_name,
                "supplier_id": supplier_id or "",
                "document_type": document_type,
                "document_no": document_no,
                "invoice_date": invoice_date,
                "due_date": due_date or invoice_date,
                "currency": currency,
                "amount": amount or "0",
                "account": account_code,
                "account_id": account_id or "",
                "tax_code": tax_code,
                "tax_code_id": tax_code_id or "",
                "status": bill_status,
                "notes": notes,
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
def bills_import_confirm(request):
    """Create bills from previewed rows. Each row = one bill with one line."""
    import datetime as dt

    rows = request.data.get("rows", [])
    update_existing = request.data.get("update_existing", False)

    from core.models import TaxCode

    created_by = (
        f"{request.user.first_name} {request.user.last_name}".strip()
        or request.user.username
    )

    today = timezone.localdate().isoformat()

    def _clean_date(val):
        """Normalise a date value to YYYY-MM-DD or return today."""
        if not val:
            return today
        s = str(val).strip()
        if not s:
            return today
        # Strip time portion: "2026-05-20 00:00:00" → "2026-05-20"
        s = s.split(" ")[0].split("T")[0]
        # Validate it looks like a date
        try:
            dt.date.fromisoformat(s)
            return s
        except ValueError:
            return today

    try:
        created = 0
        updated = 0
        errors = []

        for r in rows:
            if r.get("status") == "error":
                continue
            if r.get("status") == "duplicate" and not update_existing:
                continue

            data = r.get("data", {})
            supplier_id = data.get("supplier_id")

            supplier = None
            if supplier_id:
                try:
                    supplier = Supplier.objects.get(id=supplier_id)
                except Supplier.DoesNotExist:
                    pass

            invoice_date = _clean_date(data.get("invoice_date"))
            due_date = _clean_date(data.get("due_date")) or invoice_date
            document_no = (data.get("document_no") or "").strip()
            currency = (data.get("currency") or "DKK").strip() or "DKK"
            notes = (data.get("notes") or "").strip()
            description = (data.get("description") or "").strip()

            try:
                amt = Decimal(str(data.get("amount", 0) or 0))
            except (InvalidOperation, TypeError):
                amt = Decimal("0")

            # Resolve tax
            tc = None
            tax_amt = Decimal("0")
            if data.get("tax_code_id"):
                try:
                    tc = TaxCode.objects.get(id=data["tax_code_id"])
                    tax_amt = supplier_vat(amt, tc)
                except TaxCode.DoesNotExist:
                    pass

            account_id = data.get("account_id") or None

            try:
                bill = Bill.objects.create(
                    bill_number=_next_bill_number(),
                    supplier=supplier,
                    date=invoice_date,
                    due_date=due_date,
                    status="draft",
                    currency=currency,
                    reference=document_no,
                    notes=notes,
                    subtotal=amt,
                    tax_amount=tax_amt,
                    total=amt + tax_amt,
                    created_by=created_by,
                )

                BillLine.objects.create(
                    bill=bill,
                    description=description,
                    quantity=Decimal("1"),
                    unit_price=amt,
                    tax_code=tc,
                    account_id=account_id,
                )

                created += 1
            except Exception as e:
                errors.append(f"Row {r.get('row_number', '?')}: {str(e)}")

        return Response({
            "success": True,
            "created": created,
            "updated": updated,
            "errors": errors,
        })
    except Exception as e:
        return Response(
            {"success": False, "message": f"Import error: {str(e)}"},
            status=400,
        )


# ─── Bill Matching (Regningsafstemning) ──────────────────────────────────────

_STOP_WORDS = frozenset({
    "de", "du", "le", "la", "les", "en", "et", "au", "aux", "des", "un", "une",
    "the", "of", "and", "in", "to", "for", "at", "by", "on", "with", "from",
    "og", "i", "til", "fra", "med", "den", "det", "er", "en", "af", "på",
    "virement", "emis", "faveur", "commission", "recu", "commercial",
    "reception", "rapatriement", "instantane",
    "sarl", "srl", "sa", "llc", "ltd", "inc",
})


def _score_bill_match(bill, amount, txn_date, description, reference):
    """Score how well a bill matches a bank transaction (0–100)."""
    import datetime as _dt
    import re
    score = 0
    description_lower = (description or "").lower()
    reference_lower = (reference or "").lower()

    # --- Amount (max 40 pts) ---
    bill_balance = bill.balance_due
    if bill_balance and amount:
        try:
            diff_pct = abs(float(amount) - float(bill_balance)) / float(bill_balance) * 100
        except (ZeroDivisionError, ValueError):
            diff_pct = 100
        if diff_pct == 0:
            score += 40
        elif diff_pct <= 1:
            score += 32
        elif diff_pct <= 5:
            score += 20
        elif diff_pct <= 10:
            score += 8

    # --- Date proximity (max 20 pts) ---
    if txn_date and bill.date:
        try:
            if isinstance(txn_date, str):
                txn_date_parsed = _dt.date.fromisoformat(txn_date.split("T")[0])
            else:
                txn_date_parsed = txn_date
            day_diff = abs((txn_date_parsed - bill.date).days)
            if day_diff == 0:
                score += 20
            elif day_diff <= 7:
                score += 15
            elif day_diff <= 30:
                score += 10
            elif day_diff <= 60:
                score += 5
        except (ValueError, TypeError):
            pass

    # --- Supplier name in description (max 15 pts) ---
    if bill.supplier and description_lower:
        supplier_name = bill.supplier.name.lower()
        if supplier_name and supplier_name in description_lower:
            score += 15
        elif supplier_name:
            words = [w for w in supplier_name.split() if len(w) > 2 and w not in _STOP_WORDS]
            if words:
                matched = sum(1 for w in words if w in description_lower)
                score += min(10, int(matched / len(words) * 10))

    # --- Reference match (max 10 pts) ---
    bill_ref = (bill.reference or "").lower()
    bill_number = (bill.bill_number or "").lower()
    combined = description_lower + " " + reference_lower
    if bill_ref and bill_ref in combined:
        score += 10
    elif bill_number and bill_number in combined:
        score += 10

    # --- Text / word overlap (max 15 pts) ---
    # Collect meaningful words from the bank transaction description
    txn_words = set(re.findall(r"[a-zà-ÿ]{3,}", description_lower + " " + reference_lower))
    txn_words -= _STOP_WORDS

    if txn_words:
        # Build text from bill reference, notes, and line descriptions
        bill_text_parts = []
        if bill.reference:
            bill_text_parts.append(bill.reference.lower())
        if bill.notes:
            bill_text_parts.append(bill.notes.lower())
        if bill.supplier:
            bill_text_parts.append(bill.supplier.name.lower())
        # Include bill line descriptions (prefetched or queried)
        try:
            for line in bill.lines.all():
                if line.description:
                    bill_text_parts.append(line.description.lower())
        except Exception:
            pass

        bill_text = " ".join(bill_text_parts)
        if bill_text:
            bill_words = set(re.findall(r"[a-zà-ÿ]{3,}", bill_text))
            bill_words -= _STOP_WORDS

            if bill_words:
                overlap = txn_words & bill_words
                if overlap:
                    # Score based on overlap ratio relative to the smaller set
                    ratio = len(overlap) / min(len(txn_words), len(bill_words))
                    score += min(15, int(ratio * 15))

    return score


@api_view(["GET"])
@permission_classes([RoleWriteAccess])
def bill_linked_transaction_ids(request):
    """Return all journal_entry_line IDs that are reconciled — either linked to a
    bill (BillPaymentLink) or categorized directly to an account
    (BankTransactionCategorization)."""
    ids = set(
        BillPaymentLink.objects.values_list("journal_entry_line_id", flat=True)
    )
    ids |= set(
        BankTransactionCategorization.objects.values_list("journal_entry_line_id", flat=True)
    )
    return Response({
        "success": True,
        "data": {"linked_ids": [str(i) for i in ids]},
    })


@api_view(["POST"])
@permission_classes([RoleWriteAccess])
def bill_match_suggestions(request):
    """Return bills sorted by match score for a given bank transaction."""
    amount = request.data.get("amount")
    txn_date = request.data.get("date")
    description = request.data.get("description", "")
    reference = request.data.get("reference", "")

    try:
        amount = Decimal(str(amount)) if amount else Decimal("0")
    except (InvalidOperation, TypeError):
        amount = Decimal("0")

    bills = Bill.objects.filter(
        status__in=("draft", "approved"),
    ).select_related("supplier").prefetch_related("lines")

    # Only include bills with balance_due > 0
    results = []
    for bill in bills:
        if bill.balance_due <= 0:
            continue
        score = _score_bill_match(bill, amount, txn_date, description, reference)
        if score > 0:
            d = _bill_dict(bill, include_lines=False)
            d["match_score"] = score
            results.append(d)

    results.sort(key=lambda x: x["match_score"], reverse=True)

    return Response({
        "success": True,
        "data": {"suggestions": results},
    })


@api_view(["POST"])
@permission_classes([RoleWriteAccess])
def bill_auto_match(request):
    """Auto-match a list of bank transactions to bills.

    For each transaction, finds the single best bill with score >= min_score.
    Only matches when exactly one bill scores above threshold (unambiguous).

    Set preview=true to return proposals without recording them.
    """
    transactions = request.data.get("transactions", [])
    min_score = int(request.data.get("min_score", 70))
    preview = request.data.get("preview", False)

    if not transactions:
        return Response(
            {"success": False, "message": "transactions list is required"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    bills = list(
        Bill.objects.filter(status__in=("draft", "approved"))
        .select_related("supplier").prefetch_related("lines")
    )
    # Filter to bills with remaining balance
    open_bills = [b for b in bills if b.balance_due > 0]

    matched_by = (
        f"{request.user.first_name} {request.user.last_name}".strip()
        or request.user.username
    )

    matches = []
    # Track bills already matched in this batch to avoid double-matching
    matched_bill_ids = set()

    for txn in transactions:
        txn_id = txn.get("id")
        try:
            amount = Decimal(str(txn.get("amount", 0)))
        except (InvalidOperation, TypeError):
            continue
        txn_date = txn.get("date", "")
        description = txn.get("description", "")
        reference = txn.get("reference", "")

        # Score all open bills
        scored = []
        for bill in open_bills:
            if str(bill.id) in matched_bill_ids:
                continue
            score = _score_bill_match(bill, amount, txn_date, description, reference)
            if score >= min_score:
                scored.append((bill, score))

        if not scored:
            continue

        scored.sort(key=lambda x: x[1], reverse=True)
        best_bill, best_score = scored[0]

        # Only auto-match if the best score is clearly ahead (at least 10pts above second)
        if len(scored) >= 2 and scored[0][1] - scored[1][1] < 10:
            continue

        # Check this journal_entry_line hasn't already been linked
        already_linked = BillPaymentLink.objects.filter(
            journal_entry_line_id=txn_id
        ).exists()
        if already_linked:
            continue

        matched_bill_ids.add(str(best_bill.id))
        matches.append({
            "transaction_id": txn_id,
            "transaction_description": description,
            "transaction_date": txn_date,
            "bill_id": str(best_bill.id),
            "bill_number": best_bill.bill_number,
            "supplier_name": best_bill.supplier.name if best_bill.supplier else None,
            "score": best_score,
            "amount": str(amount),
        })

    if preview:
        return Response({
            "success": True,
            "message": f"{len(matches)} potential matches found",
            "data": {"matches": matches, "count": len(matches)},
        })

    # Execute the confirmed matches — same validated path as manual matching,
    # including the clearing entry (DR AP / CR client funds).
    executed = []
    for m in matches:
        try:
            jel = JournalEntryLine.objects.select_related("journal_entry", "account").get(
                id=m["transaction_id"])
            amt = Decimal(m["amount"])
        except (JournalEntryLine.DoesNotExist, InvalidOperation):
            continue

        if _validate_bank_line_for_matching(jel):
            continue

        try:
            with transaction.atomic():
                bill = Bill.objects.select_for_update().get(id=m["bill_id"])
                link, aerr = _apply_bill_payment(bill, jel, amt, f"{matched_by} (auto)")
                if aerr:
                    transaction.set_rollback(True)
                    continue
            executed.append(m)
        except Exception:
            continue

    log_action(request.user, "auto_match", "Bill", "batch", {"count": len(executed)})
    return Response({
        "success": True,
        "message": f"{len(executed)} transactions auto-matched",
        "data": {"matches": executed, "count": len(executed)},
    })


@api_view(["POST"])
@permission_classes([RoleWriteAccess])
def bill_record_payment(request, pk):
    """Record a payment on a bill by linking it to a journal entry line."""
    try:
        bill = Bill.objects.get(id=pk)
    except Bill.DoesNotExist:
        return Response(
            {"success": False, "message": "Bill not found"},
            status=status.HTTP_404_NOT_FOUND,
        )

    jel_id = request.data.get("journal_entry_line_id")
    amount = request.data.get("amount")

    if not jel_id or not amount:
        return Response(
            {"success": False, "message": "journal_entry_line_id and amount are required"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    try:
        amount = Decimal(str(amount))
    except (InvalidOperation, TypeError):
        return Response(
            {"success": False, "message": "Invalid amount"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    try:
        jel = JournalEntryLine.objects.select_related("journal_entry", "account").get(id=jel_id)
    except JournalEntryLine.DoesNotExist:
        return Response(
            {"success": False, "message": "Journal entry line not found"},
            status=status.HTTP_404_NOT_FOUND,
        )

    verr = _validate_bank_line_for_matching(jel)
    if verr:
        return Response({"success": False, "message": verr}, status=status.HTTP_400_BAD_REQUEST)

    matched_by = (
        f"{request.user.first_name} {request.user.last_name}".strip()
        or request.user.username
    )

    with transaction.atomic():
        # Lock the bill: paid_amount is read-modify-write, and two concurrent
        # matches must not both count.
        bill = Bill.objects.select_for_update().get(id=bill.id)
        link, aerr = _apply_bill_payment(bill, jel, amount, matched_by)
        if aerr:
            return Response({"success": False, "message": aerr}, status=status.HTTP_400_BAD_REQUEST)

    bill.refresh_from_db()
    log_action(request.user, "match", "Bill", bill.id,
               {"bill_number": bill.bill_number, "amount": str(amount)})
    return Response({
        "success": True,
        "message": "Payment recorded",
        "data": {"bill": _bill_dict(bill, include_lines=False)},
    })


@api_view(["POST"])
@permission_classes([RoleWriteAccess])
def bill_create_from_transaction(request):
    """Create a bill from a bank transaction (journal entry line), approve it,
    and link the transaction as its payment — the one-click 'turn this bank
    transaction into a matched bill' flow.

    Uses the same matching mechanism as manual reconciliation (BillPaymentLink
    + paid_amount); no extra journal entry beyond the bill's own approval entry.
    """
    data = request.data
    jel_id = data.get("journal_entry_line_id")
    supplier_id = data.get("supplier_id")
    account_id = data.get("account_id")
    lines_data, lerr = _parse_expense_lines(data)
    if lerr:
        return Response({"success": False, "message": lerr}, status=status.HTTP_400_BAD_REQUEST)
    if not jel_id or not supplier_id or (not account_id and not lines_data):
        return Response(
            {"success": False, "message": "journal_entry_line_id, supplier_id and an account (or split lines) are required"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    try:
        jel = JournalEntryLine.objects.select_related("journal_entry").get(id=jel_id)
    except JournalEntryLine.DoesNotExist:
        return Response({"success": False, "message": "Transaction not found"}, status=status.HTTP_404_NOT_FOUND)
    try:
        supplier = Supplier.objects.get(id=supplier_id)
    except Supplier.DoesNotExist:
        return Response({"success": False, "message": "Supplier not found"}, status=status.HTTP_400_BAD_REQUEST)
    account = None
    if not lines_data:
        try:
            account = Account.objects.get(id=account_id)
        except Account.DoesNotExist:
            return Response({"success": False, "message": "Account not found"}, status=status.HTTP_400_BAD_REQUEST)

    tax_code = None
    if data.get("tax_code_id"):
        from core.models import TaxCode
        try:
            tax_code = TaxCode.objects.get(id=data["tax_code_id"])
        except TaxCode.DoesNotExist:
            return Response({"success": False, "message": "Tax code not found"}, status=status.HTTP_400_BAD_REQUEST)

    verr = _validate_bank_line_for_matching(jel)
    if verr:
        return Response({"success": False, "message": verr}, status=status.HTTP_400_BAD_REQUEST)

    if BillPaymentLink.objects.filter(journal_entry_line=jel).exists():
        return Response(
            {"success": False, "message": "This transaction is already matched to a bill"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    if not Account.objects.filter(code=chart.PAYABLE).exists():
        return Response(
            {"success": False, "message": f"Kreditorkontoen ({chart.PAYABLE}) findes ikke"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    # The cash that actually moved on the bank line (credit = out, else debit).
    txn_amount = jel.credit if (jel.credit and jel.credit > 0) else jel.debit
    try:
        gross_amount = Decimal(str(data.get("amount") or txn_amount))
    except (InvalidOperation, TypeError):
        return Response({"success": False, "message": "Invalid amount"}, status=status.HTTP_400_BAD_REQUEST)

    import datetime as _dt
    je = jel.journal_entry
    try:
        bill_date = _dt.date.fromisoformat(str(data.get("date") or je.date).split("T")[0])
    except (ValueError, TypeError):
        bill_date = je.date
    err = closed_period_error(bill_date)
    if err:
        return Response({"success": False, "message": err}, status=status.HTTP_400_BAD_REQUEST)
    created_by = (
        f"{request.user.first_name} {request.user.last_name}".strip() or request.user.username
    )

    with transaction.atomic():
        bill = Bill.objects.create(
            bill_number=_next_bill_number(),
            supplier=supplier,
            date=bill_date,
            due_date=data.get("due_date") or bill_date,
            status="draft",
            currency=jel.currency or "DKK",
            reference=data.get("reference") or je.reference or "",
            notes=data.get("notes", ""),
            created_by=created_by,
        )
        default_desc = data.get("description") or je.description or ""
        # Amounts entered here are the money that LEFT THE BANK — VAT-inclusive,
        # same convention as categorize. VAT is split out as the exact remainder
        # (base = gross/(1+r), vat = gross - base) so base+vat == gross per line.
        if lines_data:
            allocs, gross_total, aerr = _build_expense_allocation(lines_data)
            if aerr:
                transaction.set_rollback(True)
                return Response({"success": False, "message": aerr}, status=status.HTTP_400_BAD_REQUEST)
            subtotal = Decimal("0")
            tax_amount = Decimal("0")
            for a in allocs:
                gross = a["amount"]
                base = gross
                tc = a["tax_code"]
                if tc and tc.rate:
                    base, vat = _split_vat_inclusive(gross, tc.rate)
                    tax_amount += vat
                subtotal += base
                BillLine.objects.create(
                    bill=bill, description=a["description"] or default_desc,
                    quantity=Decimal("1"), unit_price=base,
                    tax_code=tc, account=a["account"],
                )
            bill.subtotal = subtotal
            bill.tax_amount = tax_amount
            bill.total = gross_total
            bill.save()
        else:
            base = gross_amount
            tax_amount = Decimal("0")
            if tax_code and tax_code.rate:
                base, tax_amount = _split_vat_inclusive(gross_amount, tax_code.rate)
            BillLine.objects.create(
                bill=bill,
                description=default_desc,
                quantity=Decimal("1"),
                unit_price=base,
                tax_code=tax_code,
                account=account,
            )
            bill.subtotal = base
            bill.tax_amount = tax_amount
            bill.total = gross_amount
            bill.save()

        # The bill IS this bank payment, so its total must equal the money that
        # moved — otherwise a phantom balance_due (or overpayment) is born.
        if txn_amount and bill.total.quantize(_CENT) != Decimal(str(txn_amount)).quantize(_CENT):
            transaction.set_rollback(True)
            return Response(
                {"success": False,
                 "message": "Bill total must equal the transaction amount"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        ok, err = _approve_bill(bill, created_by)
        if not ok:
            transaction.set_rollback(True)
            return Response({"success": False, "message": err}, status=status.HTTP_400_BAD_REQUEST)
        bill.refresh_from_db()

        # Link the transaction as payment (DR kreditorer / CR bank) — same path as manual matching.
        link_amount = txn_amount or bill.total
        link, aerr = _apply_bill_payment(bill, jel, link_amount, created_by)
        if aerr:
            transaction.set_rollback(True)
            return Response({"success": False, "message": aerr}, status=status.HTTP_400_BAD_REQUEST)

    bill.refresh_from_db()
    return Response({
        "success": True,
        "message": "Bill created and matched to the transaction",
        "data": {"bill": _bill_dict(bill)},
    }, status=status.HTTP_201_CREATED)


@api_view(["POST"])
@permission_classes([RoleWriteAccess])
def bank_transaction_categorize(request, jel_id):
    """Reconcile a bank transaction by booking it to one or more accounts: the
    bank entry's suspense leg (chart.SUSPENSE) is replaced by the chosen accounts.
    Direction-aware:

    - OUTGOING (money left the bank): DR chosen accounts (+ VAT) / CR bank.
    - INCOMING (money arrived): DR bank / CR chosen accounts (+ output VAT) —
      e.g. revenue, refunds, owner deposits.

    Records a BankTransactionCategorization so the transaction reads as
    matched. The original bank line is untouched.
    """
    data = request.data

    lines_data, lerr = _parse_expense_lines(data)
    if lerr:
        return Response({"success": False, "message": lerr}, status=status.HTTP_400_BAD_REQUEST)
    if not lines_data:
        return Response(
            {"success": False, "message": "At least one account line is required"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    try:
        jel = JournalEntryLine.objects.select_related("journal_entry", "account").get(id=jel_id)
    except JournalEntryLine.DoesNotExist:
        return Response({"success": False, "message": "Transaction not found"}, status=status.HTTP_404_NOT_FOUND)

    if jel.journal_entry.source != "bank" or not (jel.account and chart.is_treasury(jel.account.code)):
        return Response(
            {"success": False, "message": "Not a bank transaction line"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    if (BillPaymentLink.objects.filter(journal_entry_line=jel).exists()
            or BankTransactionCategorization.objects.filter(journal_entry_line=jel).exists()):
        return Response(
            {"success": False, "message": "This transaction is already matched"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    # Cash that moved on the bank line: credit = money OUT, debit = money IN.
    outgoing = bool(jel.credit and jel.credit > 0)
    txn_amount = jel.credit if outgoing else jel.debit
    if not txn_amount or txn_amount <= 0:
        return Response(
            {"success": False, "message": "Transaction has no amount"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    # En indbetaling kan betale en faktura: linjen med invoice_id bogføres på
    # debitorer med kundens debitor og nedskriver fakturaens restbeløb.
    from sales.models import Invoice
    invoices = {}
    receivable = Account.objects.filter(code=chart.RECEIVABLE).first()
    for l in lines_data:
        if l.get("invoice_id"):
            inv = Invoice.objects.select_related("customer").filter(id=l["invoice_id"]).first()
            if inv is None or not inv.journal_entry_id:
                return Response({"success": False, "message": "Fakturaen findes ikke eller er ikke udstedt"},
                                status=status.HTTP_400_BAD_REQUEST)
            if outgoing:
                return Response({"success": False, "message": "En udbetaling kan ikke betale en salgsfaktura"},
                                status=status.HTTP_400_BAD_REQUEST)
            l["account_id"] = str(receivable.id)
            l["tax_code_id"] = None
            invoices[id(l)] = inv

    allocs, subtotal, aerr = _build_expense_allocation(lines_data)
    if aerr:
        return Response({"success": False, "message": aerr}, status=status.HTTP_400_BAD_REQUEST)
    for a, l in zip(allocs, lines_data):
        a["invoice"] = invoices.get(id(l))
        if a["invoice"] is not None and a["amount"] > a["invoice"].balance_due:
            return Response({"success": False, "message":
                             f"Beløbet overstiger restbeløbet på faktura {a['invoice'].invoice_number}"},
                            status=status.HTTP_400_BAD_REQUEST)

    # Bankbeløb er inkl. moms: linjens beløb er det, der gik ind/ud af banken.
    # Med en momskode deles det i netto + moms efter koden (core/vat.py); øreafrunding
    # lægges på omkostnings-/indtægtslinjen, så summen altid er bankbeløbet.
    from core.vat import add_sale
    builder = EntryBuilder()
    line_desc = data.get("description") or jel.journal_entry.description or "Banktransaktion"
    for a in allocs:
        gross = a["amount"]
        tc = a["tax_code"]
        charged = supplier_vat(Decimal("100"), tc) if outgoing else (
            tc.rate if tc and not tc.energy_tax else Decimal("0"))
        base = _split_vat_inclusive(gross, charged)[0] if charged else gross
        if a.get("invoice") is not None:
            inv = a["invoice"]
            builder.add(a["account"], -gross, description=f"Betaling faktura {inv.invoice_number}",
                        partner={"partner_type": "customer", "partner_id": str(inv.customer_id),
                                 "partner_name": inv.customer.name})
            continue
        before = builder.balance
        code = tc.code if tc else ""
        if outgoing:
            add_purchase(builder, a["account"], base, tc, a.get("description") or line_desc)
            fix = gross - (builder.balance - before)
        else:
            add_sale(builder, a["account"], base, tc, a.get("description") or line_desc)
            fix = -gross - (builder.balance - before)
        if fix:
            builder.add(a["account"], fix, code, a.get("description") or line_desc)
    posted_total = subtotal  # gross total = sum of entered (inclusive) amounts

    # The reclassification must fully clear the amount that left the bank.
    if posted_total.quantize(Decimal("0.01")) != Decimal(str(txn_amount)).quantize(Decimal("0.01")):
        return Response(
            {"success": False, "message": "Line total must equal the transaction amount"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    import datetime as _dt
    je = jel.journal_entry
    try:
        post_date = _dt.date.fromisoformat(str(data.get("date") or je.date).split("T")[0])
    except (ValueError, TypeError):
        post_date = je.date
    # The bank entry's own lines are rewritten (dated je.date), so its year must
    # be open too — not only the date typed in.
    err = closed_period_error(post_date) or closed_period_error(je.date)
    if err:
        return Response({"success": False, "message": err}, status=status.HTTP_400_BAD_REQUEST)
    created_by = (
        f"{request.user.first_name} {request.user.last_name}".strip() or request.user.username
    )
    desc = data.get("description") or je.description or "Bank transaction"

    with transaction.atomic():
        # Single-entry model: rewrite the bank entry's counter leg (the suspense
        # parked at import) into the chosen account(s) (+VAT), so the booking becomes a
        # single DR account / CR bank (income: DR bank / CR account). No separate
        # reclass entry. The bank line (jel) is kept; everything else is replaced.
        be = je
        for l in list(be.lines.exclude(id=jel.id)):
            l.delete()

        # Konti og moms efter momskoderne (udgående: debet; indgående: kredit).
        builder.write(be)
        for a in allocs:
            inv = a.get("invoice")
            if inv is None:
                continue
            inv.paid_amount = (inv.paid_amount or Decimal("0")) + a["amount"]
            if inv.paid_amount >= inv.total:
                inv.status = "paid"
                auto_lettrer(list(JournalEntryLine.objects.filter(
                    Q(journal_entry=inv.journal_entry) | Q(description=f"Betaling faktura {inv.invoice_number}"),
                    account__code=chart.RECEIVABLE, partner_id=str(inv.customer_id), lettrage="",
                ).select_related("journal_entry")))
            inv.save(update_fields=["paid_amount", "status"])

        BankTransactionCategorization.objects.create(
            journal_entry_line=jel,
            journal_entry=be,
            amount=posted_total,
            categorized_by=created_by,
        )

    log_action(request.user, "categorize", "JournalEntryLine", jel.id,
               {"journal_entry_id": str(be.id), "amount": str(posted_total)})
    return Response({
        "success": True,
        "message": "Transaction categorized",
        "data": {"journal_entry_id": str(be.id)},
    }, status=status.HTTP_201_CREATED)


@api_view(["GET", "DELETE"])
@permission_classes([RoleWriteAccess])
def bank_transaction_reconciliation(request, jel_id):
    """Inspect or undo how a bank transaction is reconciled.

    GET  → what the transaction is linked to (a categorization or a bill).
    DELETE → undo the reconciliation so the transaction can be redone:
        - categorization: delete the reclassification journal entry + link.
        - bill payment link: remove the link and roll the bill's paid amount
          back (the bill itself is left in place).
    """
    try:
        jel = JournalEntryLine.objects.select_related("journal_entry").get(id=jel_id)
    except JournalEntryLine.DoesNotExist:
        return Response({"success": False, "message": "Transaction not found"}, status=status.HTTP_404_NOT_FOUND)

    cat = BankTransactionCategorization.objects.filter(journal_entry_line=jel).select_related("journal_entry").first()
    links = list(BillPaymentLink.objects.filter(journal_entry_line=jel).select_related("bill", "bill__supplier"))
    if request.method == "GET":
        if cat:
            je = cat.journal_entry
            lines = [
                {
                    "account_code": l.account.code,
                    "account_name": l.account.name,
                    "debit": str(l.debit),
                    "credit": str(l.credit),
                }
                for l in je.lines.select_related("account").all()
            ]
            return Response({"success": True, "data": {
                "type": "categorization",
                "amount": str(cat.amount),
                "categorized_by": cat.categorized_by,
                "created_at": cat.created_at.isoformat() if cat.created_at else None,
                "journal_entry": {
                    "id": str(je.id),
                    "entry_number": je.entry_number,
                    "date": je.date.isoformat() if hasattr(je.date, "isoformat") else str(je.date),
                    "lines": lines,
                },
            }})
        if links:
            link = links[0]
            return Response({"success": True, "data": {
                "type": "bill",
                "amount": str(sum((lk.amount for lk in links), Decimal("0"))),
                "bill": _bill_dict(link.bill, include_lines=False),
            }})
        return Response({"success": True, "data": {"type": None}})

    # DELETE — undo. It rewrites or deletes ledger lines, so not in a closed year.
    err = closed_period_error(jel.journal_entry.date) or (
        closed_period_error(cat.journal_entry.date) if cat else None)
    if err:
        return Response({"success": False, "message": err}, status=status.HTTP_400_BAD_REQUEST)
    suspense = Account.objects.filter(code=chart.SUSPENSE).first()
    if cat:
        with transaction.atomic():
            je = cat.journal_entry
            if je.source == "bank":
                # Single-entry model: the categorization points at the bank entry itself
                # (DR account / CR bank). Revert the non-bank leg(s) back to the
                # suspense so the line becomes uncategorised again — do NOT delete the
                # bank entry (that would destroy the transaction).
                cat.delete()
                if suspense:
                    for l in list(je.lines.exclude(id=jel.id)):
                        if chart.is_treasury(l.account.code):
                            continue
                        JournalEntryLine.objects.create(
                            journal_entry=je, account=suspense, debit=l.debit, credit=l.credit,
                            currency=l.currency, description=l.description)
                        l.delete()
            else:
                # Legacy two-entry model (separate reclass entry): drop it.
                cat.delete()
                je.delete()
        log_action(request.user, "unmatch", "JournalEntryLine", jel_id, {"type": "categorization"})
        return Response({"success": True, "message": "Categorization removed"})

    if links:
        with transaction.atomic():
            for link in links:
                bill = Bill.objects.select_for_update().get(id=link.bill_id)
                undo_lettrage_of(_bill_ap_lines(bill))
                bill.paid_amount = (bill.paid_amount or Decimal("0")) - link.amount
                if bill.paid_amount < 0:
                    bill.paid_amount = Decimal("0")
                if bill.status == "paid" and bill.paid_amount < bill.total:
                    bill.status = "approved"
                bill.save()
                clearing = link.clearing_entry
                pay_jel = link.journal_entry_line
                link.delete()
                if clearing:
                    # Legacy: remove the DR AP / CR client-funds clearing entry.
                    clearing.delete()
                elif suspense and pay_jel:
                    # Single-entry payment (DR AP / CR bank): revert the AP leg to suspense
                    # so the bank line becomes uncategorised again; keep the bank entry.
                    for l in list(pay_jel.journal_entry.lines.all()):
                        if l.account.code == chart.PAYABLE:
                            JournalEntryLine.objects.create(
                                journal_entry=l.journal_entry, account=suspense,
                                debit=l.debit, credit=l.credit, currency=l.currency,
                                description=l.description)
                            l.delete()
        log_action(request.user, "unmatch", "JournalEntryLine", jel_id, {"type": "bill_payment_link"})
        return Response({"success": True, "message": "Payment link removed"})

    return Response({"success": False, "message": "Transaction is not reconciled"}, status=status.HTTP_400_BAD_REQUEST)


# ─── Læs leverandørfaktura (PDF/XML, lokalt) ──────────────────────────────────

READABLE_EXTENSIONS = {".pdf", ".xml", ".png", ".jpg", ".jpeg", ".tif", ".tiff"}


@api_view(["POST"])
@permission_classes([RoleWriteAccess])
@parser_classes([MultiPartParser, FormParser])
def bills_read_invoice(request):
    """Upload en leverandørfaktura. Filen gemmes som bilag (SHA-256), læses lokalt og
    returneres som forslag til en regning. Forslaget gemmes ikke – brugeren tjekker det
    og opretter regningen med POST /bills (med document_id)."""
    import hashlib
    import os

    from core.models import Document
    from .invoice_reader import ReadError, ocr_available, read_invoice, suggest

    f = request.FILES.get("file")
    if f is None:
        return Response({"success": False, "message": "Vælg en fil"}, status=status.HTTP_400_BAD_REQUEST)
    ext = os.path.splitext(f.name or "")[1].lower()
    if ext not in READABLE_EXTENSIONS:
        return Response({"success": False, "message": "Kun PDF, XML (OIOUBL/Peppol) og billeder kan læses."},
                        status=status.HTTP_400_BAD_REQUEST)
    if ext != ".xml":
        err = validate_upload(f)
        if err:
            return Response({"success": False, "message": err}, status=status.HTTP_400_BAD_REQUEST)
    elif f.size > 15 * 1024 * 1024:
        return Response({"success": False, "message": "Filen er for stor (maks. 15 MB)"},
                        status=status.HTTP_400_BAD_REQUEST)
    content = f.read()
    digest = hashlib.sha256(content).hexdigest()
    existing = Document.objects.filter(sha256=digest).exclude(bill=None).select_related("bill").first()
    f.seek(0)
    doc = Document.objects.create(
        file=f, filename=f.name, description="Leverandørfaktura (læst automatisk)", sha256=digest,
        size=f.size or len(content),
        uploaded_by=f"{request.user.first_name} {request.user.last_name}".strip() or request.user.username,
    )
    log_action(request.user, "create", "Document", doc.id, {"source": "read_invoice", "sha256": digest})
    data = {"document_id": str(doc.id), "filename": doc.filename, "ocr_available": ocr_available()}
    if existing:
        data["duplicate_of"] = {"bill_id": str(existing.bill_id), "bill_number": existing.bill.bill_number}
    try:
        result = read_invoice(content, f.name, getattr(getattr(request, "tenant", None), "cvr", "") or "")
    except ReadError as e:
        data.update({"read": False, "message": str(e)})
        return Response({"success": True, "data": data})
    parsed = result["parsed"]
    sug = suggest(result)
    sup = parsed.get("supplier") or {}
    data.update({
        "read": True, "source": result["source"], "confidence": result["confidence"],
        "warnings": result["warnings"], "parsed": parsed,
        "proposal": {
            "supplier_id": sug.get("supplier_id"),
            "new_supplier": None if sug.get("supplier_id") else {
                "name": sup.get("name") or "", "tax_id": sup.get("cvr") or sup.get("vat_id") or "",
                "address": "\n".join(x for x in (sup.get("street"), " ".join(
                    x for x in (sup.get("zip_code"), sup.get("city")) if x)) if x)},
            "reference": parsed.get("number") or "",
            "date": parsed.get("issue_date"), "due_date": parsed.get("due_date"),
            "currency": parsed.get("currency") or "DKK",
            "notes": " ".join(x for x in (
                f"Betaling: {parsed['payment_id']}" if parsed.get("payment_id") else "",
                f"IBAN {parsed['payment_iban']}" if parsed.get("payment_iban") else "") if x),
            "lines": [{"description": l.get("description") or "", "quantity": l.get("quantity") or "1",
                       "unit_price": l.get("unit_price") or "0", "account_id": l.get("account_id") or "",
                       "tax_code_id": l.get("tax_code_id") or "", "amount": l.get("amount") or "0"}
                      for l in sug.get("lines") or []],
            "totals": {"net": parsed.get("tax_exclusive"), "vat": parsed.get("tax_total"),
                       "total": parsed.get("tax_inclusive")},
        },
    })
    return Response({"success": True, "data": data})
