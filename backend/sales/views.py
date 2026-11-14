"""Salg: debitorer, fakturaer og kreditnotaer (CRUD og bogføring). Reglerne står i sales/invoicing.py."""

import csv
import io
import re
from decimal import Decimal, InvalidOperation

from django.db import transaction
from django.db.models import Sum, Q
from django.http import HttpResponse
from rest_framework import status
from rest_framework.decorators import api_view, parser_classes, permission_classes
from rest_framework.parsers import MultiPartParser
from rest_framework.response import Response

from core.audit import log_action
from core.permissions import RoleWriteAccess
from core.csv_utils import SafeWriter

from accounts import chart
from journals.numbering import next_number
from journals.periods import closed_period_error
from . import invoicing
from .models import Customer, Invoice, InvoiceLine, CreditNote


# ─── helpers ──────────────────────────────────────────────────────────────────







CUSTOMER_FIELDS = ("name", "email", "phone", "address", "postal_code", "city", "country", "tax_id", "vat_zone",
                   "ean", "currency", "notes", "payment_terms_code")


def _customer_dict(customer):
    return {
        "id": str(customer.id),
        "code": customer.code,
        "name": customer.name,
        "email": customer.email,
        "phone": customer.phone,
        "address": customer.address,
        "postal_code": customer.postal_code,
        "city": customer.city,
        "country": customer.country,
        "tax_id": customer.tax_id,
        "vat_zone": customer.vat_zone,
        "is_business": customer.is_business,
        "is_public": customer.is_public,
        "ean": customer.ean,
        "currency": customer.currency,
        "payment_terms": customer.payment_terms,
        "payment_terms_code": customer.payment_terms_code,
        "credit_limit": str(customer.credit_limit),
        "notes": customer.notes,
        "is_active": customer.is_active,
        "created_at": customer.created_at.isoformat() if customer.created_at else None,
        "updated_at": customer.updated_at.isoformat() if customer.updated_at else None,
    }


def _customer_error(data):
    ean = (data.get("ean") or "").strip()
    if ean and not re.fullmatch(r"\d{13}", ean):
        return "EAN-/GLN-nummeret skal være 13 cifre"
    if data.get("is_public") and not ean:
        return "En offentlig kunde skal have et EAN-nummer"
    if data.get("payment_terms_code") and data["payment_terms_code"] not in invoicing.TERMS:
        return "Ukendt betalingsbetingelse"
    return None


def _invoice_line_dict(line):
    return {
        "id": str(line.id),
        "description": line.description,
        "quantity": str(line.quantity),
        "unit": line.unit,
        "unit_price": str(line.unit_price),
        "tax_code_id": str(line.tax_code_id) if line.tax_code_id else None,
        "tax_code_code": line.tax_code.code if line.tax_code_id else None,
        "tax_code_rate": str(line.tax_code.rate) if line.tax_code_id else None,
        "account_id": str(line.account_id) if line.account_id else None,
        "account_code": line.account.code if line.account_id else None,
        "account_name": line.account.name if line.account_id else None,
        "amount": str(line.amount),
        "is_text": line.is_text,
        "position": line.position,
    }


def _iso(v):
    return v.isoformat() if hasattr(v, "isoformat") else (str(v) if v else None)


def _invoice_dict(invoice, include_lines=True):
    d = {
        "id": str(invoice.id),
        "invoice_number": invoice.invoice_number,
        "is_draft_number": invoicing.is_draft_number(invoice.invoice_number),
        "customer_id": str(invoice.customer_id),
        "customer_name": invoice.customer.name,
        "customer_code": invoice.customer.code,
        "date": _iso(invoice.date),
        "delivery_date": _iso(invoice.delivery_date),
        "due_date": _iso(invoice.due_date),
        "payment_terms_code": invoice.payment_terms_code,
        "status": invoice.status,
        "subtotal": str(invoice.subtotal),
        "tax_amount": str(invoice.tax_amount),
        "total": str(invoice.total),
        "paid_amount": str(invoice.paid_amount),
        "balance_due": str(invoice.balance_due),
        "currency": invoice.currency,
        "exchange_rate": str(invoice.exchange_rate),
        "customer_reference": invoice.customer_reference,
        "order_reference": invoice.order_reference,
        "quote_id": str(invoice.quote_id) if invoice.quote_id else None,
        "reminders": invoice.reminders.count(),
        "notes": invoice.notes,
        "journal_entry_id": str(invoice.journal_entry_id) if invoice.journal_entry_id else None,
        "created_by": invoice.created_by,
        "created_at": invoice.created_at.isoformat() if invoice.created_at else None,
        "updated_at": invoice.updated_at.isoformat() if invoice.updated_at else None,
    }
    if include_lines:
        d["lines"] = [_invoice_line_dict(l) for l in invoice.lines.select_related("account", "tax_code").all()]
        d["print"] = invoicing.invoice_print_data(invoice)
        d["compliance_errors"] = invoicing.compliance_errors(invoice) if invoice.status == "draft" else []
    return d


def _credit_note_dict(cn):
    return {
        "id": str(cn.id),
        "credit_note_number": cn.credit_note_number,
        "customer_id": str(cn.customer_id),
        "customer_name": cn.customer.name,
        "customer_code": cn.customer.code,
        "invoice_id": str(cn.invoice_id) if cn.invoice_id else None,
        "invoice_number": cn.invoice.invoice_number if cn.invoice_id else None,
        "date": cn.date.isoformat() if hasattr(cn.date, "isoformat") else str(cn.date),
        "status": cn.status,
        "subtotal": str(cn.subtotal),
        "tax_amount": str(cn.tax_amount),
        "total": str(cn.total),
        "notes": cn.notes,
        "journal_entry_id": str(cn.journal_entry_id) if cn.journal_entry_id else None,
        "created_by": cn.created_by,
        "created_at": cn.created_at.isoformat() if cn.created_at else None,
    }


def _next_customer_code():
    """Next customer code like CUS-0001 (numeric max — see journals/numbering.py)."""
    return next_number(Customer, "code", "CUS")




def _next_credit_note_number():
    """Kladdenummer; det fortløbende kreditnotanummer gives ved bogføring."""
    return next_number(CreditNote, "credit_note_number", invoicing.DRAFT_PREFIX, 5)


def _next_entry_number():
    """Generate next sequential journal entry number like JE-0001."""
    from journals.numbering import next_je_number
    return next_je_number()


# ─── Customers CRUD ──────────────────────────────────────────────────────────

@api_view(["GET", "POST"])
@permission_classes([RoleWriteAccess])
def customers_list_create(request):
    if request.method == "GET":
        qs = Customer.objects.all()

        # Filter by is_active
        if request.query_params.get("is_active"):
            qs = qs.filter(is_active=request.query_params["is_active"].lower() == "true")

        # Search by name or code
        if request.query_params.get("search"):
            q = request.query_params["search"]
            qs = qs.filter(Q(name__icontains=q) | Q(code__icontains=q))

        return Response({
            "success": True,
            "customers": [_customer_dict(c) for c in qs],
        })

    # POST — create customer
    data = request.data
    if not data.get("name"):
        return Response(
            {"success": False, "message": "name is required"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    code = data.get("code") or _next_customer_code()
    if Customer.objects.filter(code=code).exists():
        return Response(
            {"success": False, "message": f"Customer code {code} already exists"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    err = _customer_error(data)
    if err:
        return Response({"success": False, "message": err}, status=status.HTTP_400_BAD_REQUEST)
    try:
        customer = Customer.objects.create(
            code=code,
            **{f: data.get(f) for f in CUSTOMER_FIELDS if data.get(f) not in (None, "")},
            is_business=bool(data.get("is_business", True)),
            is_public=bool(data.get("is_public", False)),
            payment_terms=int(data.get("payment_terms", 14)),
            credit_limit=Decimal(str(data.get("credit_limit", 0))),
            is_active=data.get("is_active", True),
        )
    except (ValueError, InvalidOperation) as e:
        return Response(
            {"success": False, "message": f"Invalid data: {e}"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    return Response({
        "success": True,
        "message": "Customer created",
        "customer": _customer_dict(customer),
    }, status=status.HTTP_201_CREATED)


@api_view(["GET", "PUT", "DELETE"])
@permission_classes([RoleWriteAccess])
def customers_detail(request, pk):
    try:
        customer = Customer.objects.get(id=pk)
    except Customer.DoesNotExist:
        return Response(
            {"success": False, "message": "Customer not found"},
            status=status.HTTP_404_NOT_FOUND,
        )

    if request.method == "GET":
        return Response({
            "success": True,
            "customer": _customer_dict(customer),
        })

    if request.method == "PUT":
        data = request.data
        if "code" in data and data["code"] != customer.code:
            if Customer.objects.filter(code=data["code"]).exclude(id=pk).exists():
                return Response(
                    {"success": False, "message": "Customer code already exists"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            customer.code = data["code"]

        err = _customer_error({**_customer_dict(customer), **data})
        if err:
            return Response({"success": False, "message": err}, status=status.HTTP_400_BAD_REQUEST)
        for field in CUSTOMER_FIELDS:
            if field in data:
                setattr(customer, field, data[field] or "")
        for field in ("is_business", "is_public"):
            if field in data:
                setattr(customer, field, bool(data[field]))

        if "payment_terms" in data:
            try:
                customer.payment_terms = int(data["payment_terms"])
            except (ValueError, TypeError):
                return Response(
                    {"success": False, "message": "Invalid payment_terms value"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        if "credit_limit" in data:
            try:
                customer.credit_limit = Decimal(str(data["credit_limit"]))
            except (InvalidOperation, TypeError):
                return Response(
                    {"success": False, "message": "Invalid credit_limit value"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        if "is_active" in data:
            customer.is_active = data["is_active"]

        customer.save()
        return Response({
            "success": True,
            "message": "Customer updated",
            "customer": _customer_dict(customer),
        })

    # DELETE — soft delete
    customer.is_active = False
    customer.save()
    return Response({"success": True, "message": "Customer deactivated"})


@api_view(["GET"])
@permission_classes([RoleWriteAccess])
def customer_statement(request, pk):
    """Return all invoices and credit notes for a customer."""
    try:
        customer = Customer.objects.get(id=pk)
    except Customer.DoesNotExist:
        return Response(
            {"success": False, "message": "Customer not found"},
            status=status.HTTP_404_NOT_FOUND,
        )

    invoices = Invoice.objects.filter(customer=customer).select_related("customer")
    credit_notes = CreditNote.objects.filter(customer=customer).select_related(
        "customer", "invoice"
    )

    # Compute totals
    invoice_totals = invoices.aggregate(
        total_invoiced=Sum("total"),
        total_paid=Sum("paid_amount"),
    )
    total_invoiced = invoice_totals["total_invoiced"] or Decimal("0")
    total_paid = invoice_totals["total_paid"] or Decimal("0")

    cn_totals = credit_notes.aggregate(total_credits=Sum("total"))
    total_credits = cn_totals["total_credits"] or Decimal("0")

    balance = total_invoiced - total_paid - total_credits

    return Response({
        "success": True,
        "customer": _customer_dict(customer),
        "invoices": [_invoice_dict(inv, include_lines=False) for inv in invoices],
        "credit_notes": [_credit_note_dict(cn) for cn in credit_notes],
        "summary": {
            "total_invoiced": str(total_invoiced),
            "total_paid": str(total_paid),
            "total_credits": str(total_credits),
            "balance": str(balance),
        },
    })


# ─── Fakturaer ───────────────────────────────────────────────────────────────

def _user(request):
    return f"{request.user.first_name} {request.user.last_name}".strip() or request.user.username


def _apply_invoice_fields(invoice, data):
    """Hovedfelter på et udkast. Returnerer fejltekst eller None."""
    from journals.periods import _to_date

    if "customer_id" in data:
        customer = Customer.objects.filter(id=data["customer_id"]).first()
        if customer is None:
            return "Kunden findes ikke"
        invoice.customer = customer
    for field in ("date", "delivery_date", "due_date"):
        if field in data:
            value = _to_date(data[field]) if data[field] else None
            if field != "delivery_date" and value is None:
                return f"Ugyldig {field}"
            setattr(invoice, field, value)
    for field in ("notes", "customer_reference", "order_reference"):
        if field in data:
            setattr(invoice, field, data[field] or "")
    if "currency" in data:
        invoice.currency = (data["currency"] or chart.BASE_CURRENCY).upper()
    if "exchange_rate" in data:
        try:
            invoice.exchange_rate = Decimal(str(data["exchange_rate"] or 1))
        except InvalidOperation:
            return "Ugyldig kurs"
    if invoice.currency == chart.BASE_CURRENCY:
        invoice.exchange_rate = Decimal("1")
    if "payment_terms_code" in data:
        if data["payment_terms_code"] not in invoicing.TERMS:
            return "Ukendt betalingsbetingelse"
        invoice.payment_terms_code = data["payment_terms_code"]
    if not data.get("due_date") and ("date" in data or "payment_terms_code" in data or not invoice.due_date):
        invoice.due_date = invoicing.due_date_for(invoice.date, invoice.payment_terms_code)
    return None


@api_view(["GET", "POST"])
@permission_classes([RoleWriteAccess])
def invoices_list_create(request):
    if request.method == "GET":
        qs = Invoice.objects.select_related("customer").all()
        p = request.query_params
        if p.get("status"):
            qs = qs.filter(status=p["status"])
        if p.get("customer_id"):
            qs = qs.filter(customer_id=p["customer_id"])
        if p.get("date_from"):
            qs = qs.filter(date__gte=p["date_from"])
        if p.get("date_to"):
            qs = qs.filter(date__lte=p["date_to"])
        if p.get("overdue") == "true":
            from datetime import date as _date
            qs = qs.filter(journal_entry__isnull=False, due_date__lt=_date.today()).exclude(status__in=("paid", "cancelled"))
        if p.get("search"):
            q = p["search"]
            qs = qs.filter(Q(invoice_number__icontains=q) | Q(customer__name__icontains=q) | Q(notes__icontains=q))
        return Response({"success": True, "invoices": [_invoice_dict(inv, include_lines=False) for inv in qs]})

    data = request.data
    if not data.get("customer_id") or not data.get("date"):
        return Response({"success": False, "message": "customer_id og date skal angives"},
                        status=status.HTTP_400_BAD_REQUEST)
    customer = Customer.objects.filter(id=data["customer_id"]).first()
    if customer is None:
        return Response({"success": False, "message": "Kunden findes ikke"}, status=status.HTTP_404_NOT_FOUND)
    invoice = Invoice(customer=customer, invoice_number=invoicing.draft_number(), status="draft",
                      currency=customer.currency or chart.BASE_CURRENCY,
                      payment_terms_code=customer.payment_terms_code, created_by=_user(request))
    err = _apply_invoice_fields(invoice, data)
    if err:
        return Response({"success": False, "message": err}, status=status.HTTP_400_BAD_REQUEST)
    try:
        with transaction.atomic():
            invoice.save()
            invoicing.save_lines(invoice, InvoiceLine, "invoice", data.get("lines", []))
            invoicing.refresh_totals(invoice)
    except invoicing.LineError as e:
        return Response({"success": False, "message": str(e)}, status=status.HTTP_400_BAD_REQUEST)
    log_action(request.user, "create", "Invoice", invoice.id, {"invoice_number": invoice.invoice_number})
    return Response({"success": True, "message": "Fakturaudkast oprettet", "invoice": _invoice_dict(invoice)},
                    status=status.HTTP_201_CREATED)


@api_view(["GET", "PUT", "DELETE"])
@permission_classes([RoleWriteAccess])
def invoices_detail(request, pk):
    invoice = Invoice.objects.select_related("customer").filter(id=pk).first()
    if invoice is None:
        return Response({"success": False, "message": "Fakturaen findes ikke"}, status=status.HTTP_404_NOT_FOUND)
    if request.method == "GET":
        return Response({"success": True, "invoice": _invoice_dict(invoice)})
    # En udstedt (bogført) faktura ændres aldrig: rettelser sker med en kreditnota.
    if invoice.journal_entry_id or invoice.status != "draft":
        return Response({"success": False, "message":
                         "Fakturaen er udstedt og kan ikke ændres eller slettes. Lav en kreditnota."},
                        status=status.HTTP_400_BAD_REQUEST)
    if request.method == "DELETE":
        number = invoice.invoice_number
        invoice.delete()
        log_action(request.user, "delete", "Invoice", pk, {"invoice_number": number})
        return Response({"success": True, "message": "Fakturaudkastet er slettet"})
    data = request.data
    err = _apply_invoice_fields(invoice, data)
    if err:
        return Response({"success": False, "message": err}, status=status.HTTP_400_BAD_REQUEST)
    try:
        with transaction.atomic():
            invoice.save()
            if data.get("lines") is not None:
                invoicing.save_lines(invoice, InvoiceLine, "invoice", data["lines"])
            invoicing.refresh_totals(invoice)
    except invoicing.LineError as e:
        return Response({"success": False, "message": str(e)}, status=status.HTTP_400_BAD_REQUEST)
    log_action(request.user, "update", "Invoice", invoice.id, {"invoice_number": invoice.invoice_number})
    return Response({"success": True, "message": "Fakturaen er opdateret", "invoice": _invoice_dict(invoice)})


@api_view(["POST"])
@permission_classes([RoleWriteAccess])
def invoice_post(request, pk):
    """Udsted og bogfør: fortløbende nummer, § 58-tjek, DR debitorer / CR omsætning og moms."""
    invoice = Invoice.objects.select_related("customer").filter(id=pk).first()
    if invoice is None:
        return Response({"success": False, "message": "Fakturaen findes ikke"}, status=status.HTTP_404_NOT_FOUND)
    if invoice.journal_entry_id:
        return Response({"success": False, "message": "Fakturaen er allerede bogført"},
                        status=status.HTTP_400_BAD_REQUEST)
    err = closed_period_error(invoice.date)
    if err:
        return Response({"success": False, "message": err}, status=status.HTTP_400_BAD_REQUEST)
    with transaction.atomic():
        Invoice.objects.select_for_update().filter(id=invoice.id).first()
        _, perr = invoicing.post_invoice(invoice, _user(request))
        if perr:
            transaction.set_rollback(True)
            return Response({"success": False, "message": perr}, status=status.HTTP_400_BAD_REQUEST)
        if invoice.status == "draft":
            invoice.status = "sent"
            invoice.save(update_fields=["status"])
    invoice.refresh_from_db()
    log_action(request.user, "post", "Invoice", invoice.id,
               {"invoice_number": invoice.invoice_number, "total": str(invoice.total)})
    return Response({"success": True, "message": f"Faktura {invoice.invoice_number} er udstedt og bogført",
                     "invoice": _invoice_dict(invoice)})


@api_view(["POST"])
@permission_classes([RoleWriteAccess])
def credit_note_apply(request, pk):
    """Bogfør en kreditnota mod en faktura (andel af fakturaens linjer, med samme momskoder)."""
    cn = CreditNote.objects.select_related("customer", "invoice").filter(id=pk).first()
    if cn is None:
        return Response({"success": False, "message": "Kreditnotaen findes ikke"}, status=status.HTTP_404_NOT_FOUND)
    if cn.status == "applied":
        return Response({"success": False, "message": "Kreditnotaen er allerede bogført"},
                        status=status.HTTP_400_BAD_REQUEST)
    invoice_id = request.data.get("invoice_id") or (str(cn.invoice_id) if cn.invoice_id else None)
    invoice = Invoice.objects.select_related("customer").filter(id=invoice_id).first() if invoice_id else None
    if invoice is None:
        return Response({"success": False, "message": "Kreditnotaen skal henvise til en faktura"},
                        status=status.HTTP_400_BAD_REQUEST)
    if invoice.customer_id != cn.customer_id:
        return Response({"success": False, "message": "Kreditnota og faktura skal have samme kunde"},
                        status=status.HTTP_400_BAD_REQUEST)
    if cn.total <= 0 or cn.total > invoice.balance_due:
        return Response({"success": False, "message":
                         f"Kreditnotaens beløb skal være mellem 0 og fakturaens restbeløb ({invoice.balance_due})"},
                        status=status.HTTP_400_BAD_REQUEST)
    err = closed_period_error(cn.date)
    if err:
        return Response({"success": False, "message": err}, status=status.HTTP_400_BAD_REQUEST)
    with transaction.atomic():
        if invoicing.is_draft_number(cn.credit_note_number):
            cn.credit_note_number = invoicing.next_invoice_number(CreditNote, "credit_note_number")
        entry, perr = invoicing.post_credit_note(cn, invoice, _user(request))
        if perr:
            transaction.set_rollback(True)
            return Response({"success": False, "message": perr}, status=status.HTTP_400_BAD_REQUEST)
        ratio = (cn.total / invoice.total) if invoice.total else Decimal("1")
        cn.tax_amount = (invoice.tax_amount * ratio).quantize(Decimal("0.01"))
        cn.subtotal = cn.total - cn.tax_amount
        invoice.paid_amount += cn.total
        if invoice.paid_amount >= invoice.total:
            invoice.status = "paid"
        invoice.save()
        cn.status, cn.invoice, cn.journal_entry = "applied", invoice, entry
        cn.save()
    log_action(request.user, "post", "CreditNote", cn.id,
               {"credit_note_number": cn.credit_note_number, "invoice_number": invoice.invoice_number,
                "total": str(cn.total)})
    return Response({"success": True, "message": "Kreditnotaen er bogført", "credit_note": _credit_note_dict(cn),
                     "invoice": _invoice_dict(invoice, include_lines=False)})







CENT = Decimal("0.01")






@api_view(["POST"])
@permission_classes([RoleWriteAccess])
def invoice_send(request, pk):
    """Markér en udstedt faktura som sendt. Et udkast skal udstedes (bogføres) først,
    så det får sit fortløbende nummer."""
    invoice = Invoice.objects.select_related("customer").filter(id=pk).first()
    if invoice is None:
        return Response({"success": False, "message": "Fakturaen findes ikke"}, status=status.HTTP_404_NOT_FOUND)
    if not invoice.journal_entry_id:
        return Response({"success": False, "message": "Udsted (bogfør) fakturaen, før den sendes"},
                        status=status.HTTP_400_BAD_REQUEST)

    invoice.status = "sent"
    invoice.save()

    return Response({
        "success": True,
        "message": "Invoice marked as sent",
        "invoice": _invoice_dict(invoice),
    })


# ─── Credit Notes CRUD ──────────────────────────────────────────────────────

@api_view(["GET", "POST"])
@permission_classes([RoleWriteAccess])
def credit_notes_list_create(request):
    if request.method == "GET":
        qs = CreditNote.objects.select_related("customer", "invoice").all()

        if request.query_params.get("status"):
            qs = qs.filter(status=request.query_params["status"])
        if request.query_params.get("customer_id"):
            qs = qs.filter(customer_id=request.query_params["customer_id"])
        if request.query_params.get("search"):
            q = request.query_params["search"]
            qs = qs.filter(
                Q(credit_note_number__icontains=q)
                | Q(customer__name__icontains=q)
            )

        return Response({
            "success": True,
            "credit_notes": [_credit_note_dict(cn) for cn in qs],
        })

    # POST — create credit note
    data = request.data

    if not data.get("customer_id"):
        return Response(
            {"success": False, "message": "customer_id is required"},
            status=status.HTTP_400_BAD_REQUEST,
        )
    if not data.get("date"):
        return Response(
            {"success": False, "message": "date is required"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    try:
        customer = Customer.objects.get(id=data["customer_id"])
    except Customer.DoesNotExist:
        return Response(
            {"success": False, "message": "Customer not found"},
            status=status.HTTP_404_NOT_FOUND,
        )

    invoice = None
    if data.get("invoice_id"):
        try:
            invoice = Invoice.objects.get(id=data["invoice_id"])
            if invoice.customer_id != customer.id:
                return Response(
                    {"success": False, "message": "Invoice does not belong to this customer"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
        except Invoice.DoesNotExist:
            return Response(
                {"success": False, "message": "Invoice not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

    credit_note_number = data.get("credit_note_number") or _next_credit_note_number()
    if CreditNote.objects.filter(credit_note_number=credit_note_number).exists():
        return Response(
            {"success": False, "message": f"Credit note number {credit_note_number} already exists"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    try:
        subtotal = Decimal(str(data.get("subtotal", 0)))
        tax_amount = Decimal(str(data.get("tax_amount", 0)))
        total = Decimal(str(data.get("total", 0)))
    except (InvalidOperation, TypeError):
        return Response(
            {"success": False, "message": "Invalid amount values"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    # If total not provided, compute from subtotal + tax
    if total == 0 and subtotal > 0:
        total = subtotal + tax_amount

    cn = CreditNote.objects.create(
        credit_note_number=credit_note_number,
        customer=customer,
        invoice=invoice,
        date=data["date"],
        status="draft",
        subtotal=subtotal,
        tax_amount=tax_amount,
        total=total,
        notes=data.get("notes", ""),
        created_by=(
            f"{request.user.first_name} {request.user.last_name}".strip()
            or request.user.username
        ),
    )

    return Response({
        "success": True,
        "message": "Credit note created",
        "credit_note": _credit_note_dict(cn),
    }, status=status.HTTP_201_CREATED)


@api_view(["GET", "PUT", "DELETE"])
@permission_classes([RoleWriteAccess])
def credit_notes_detail(request, pk):
    try:
        cn = CreditNote.objects.select_related("customer", "invoice").get(id=pk)
    except CreditNote.DoesNotExist:
        return Response(
            {"success": False, "message": "Credit note not found"},
            status=status.HTTP_404_NOT_FOUND,
        )

    if request.method == "GET":
        return Response({
            "success": True,
            "credit_note": _credit_note_dict(cn),
        })

    if request.method == "DELETE":
        if cn.status != "draft":
            return Response(
                {"success": False, "message": "Only draft credit notes can be deleted"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        cn.delete()
        return Response({"success": True, "message": "Credit note deleted"})

    # PUT — update
    if cn.status != "draft":
        return Response(
            {"success": False, "message": "Only draft credit notes can be edited"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    data = request.data

    if "customer_id" in data:
        try:
            customer = Customer.objects.get(id=data["customer_id"])
            cn.customer = customer
        except Customer.DoesNotExist:
            return Response(
                {"success": False, "message": "Customer not found"},
                status=status.HTTP_400_BAD_REQUEST,
            )

    if "invoice_id" in data:
        if data["invoice_id"]:
            try:
                invoice = Invoice.objects.get(id=data["invoice_id"])
                if invoice.customer_id != cn.customer_id:
                    return Response(
                        {"success": False, "message": "Invoice does not belong to this customer"},
                        status=status.HTTP_400_BAD_REQUEST,
                    )
                cn.invoice = invoice
            except Invoice.DoesNotExist:
                return Response(
                    {"success": False, "message": "Invoice not found"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
        else:
            cn.invoice = None

    if "credit_note_number" in data and data["credit_note_number"] != cn.credit_note_number:
        if CreditNote.objects.filter(credit_note_number=data["credit_note_number"]).exclude(id=pk).exists():
            return Response(
                {"success": False, "message": "Credit note number already exists"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        cn.credit_note_number = data["credit_note_number"]

    for field in ("date", "notes"):
        if field in data:
            setattr(cn, field, data[field])

    for decimal_field in ("subtotal", "tax_amount", "total"):
        if decimal_field in data:
            try:
                setattr(cn, decimal_field, Decimal(str(data[decimal_field])))
            except (InvalidOperation, TypeError):
                return Response(
                    {"success": False, "message": f"Invalid {decimal_field} value"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

    cn.save()
    cn.refresh_from_db()
    return Response({
        "success": True,
        "message": "Credit note updated",
        "credit_note": _credit_note_dict(cn),
    })




# ─── Customer Import / Export ────────────────────────────────────────────────

@api_view(["POST"])
@permission_classes([RoleWriteAccess])
@parser_classes([MultiPartParser])
def customers_import_preview(request):
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

    existing_codes = {c.code: c for c in Customer.objects.all()}
    existing_names = {c.name.lower(): c for c in Customer.objects.all()}
    rows = []

    for i, row in enumerate(reader, start=1):
        name = (row.get("name") or "").strip()
        code = (row.get("code") or "").strip()
        email = (row.get("email") or "").strip()
        phone = (row.get("phone") or "").strip()
        address = (row.get("address") or "").strip()
        tax_id = (row.get("tax_id") or "").strip()
        currency = (row.get("currency") or "DKK").strip().upper()
        payment_terms = (row.get("payment_terms") or "").strip()
        credit_limit = (row.get("credit_limit") or "").strip()
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

        if credit_limit:
            try:
                Decimal(credit_limit)
            except InvalidOperation:
                errors.append("credit_limit must be a number")

        if currency and len(currency) != 3:
            errors.append("currency must be 3 characters")

        # Determine status
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
                "credit_limit": credit_limit or "0",
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
def customers_import_confirm(request):
    """Create or update customers from previewed data."""
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
                    customer = Customer.objects.get(id=r["existing_id"])
                    customer.name = name
                    if data.get("email"):
                        customer.email = data["email"]
                    if data.get("phone"):
                        customer.phone = data["phone"]
                    if data.get("address"):
                        customer.address = data["address"]
                    if data.get("tax_id"):
                        customer.tax_id = data["tax_id"]
                    if data.get("currency"):
                        customer.currency = data["currency"]
                    if data.get("payment_terms"):
                        customer.payment_terms = int(data["payment_terms"])
                    if data.get("credit_limit"):
                        customer.credit_limit = Decimal(data["credit_limit"])
                    if data.get("notes"):
                        customer.notes = data["notes"]
                    customer.save()
                    updated += 1
                except Customer.DoesNotExist:
                    errors.append(f"Row {r.get('row_number')}: customer not found")
            elif r.get("status") == "new":
                code = data.get("code") or _next_customer_code()
                Customer.objects.create(
                    code=code,
                    name=name,
                    email=data.get("email", ""),
                    phone=data.get("phone", ""),
                    address=data.get("address", ""),
                    tax_id=data.get("tax_id", ""),
                    currency=data.get("currency", "DKK"),
                    payment_terms=int(data.get("payment_terms", 30)),
                    credit_limit=Decimal(data.get("credit_limit", "0")),
                    notes=data.get("notes", ""),
                )
                created += 1

    return Response({
        "success": True,
        "created": created,
        "updated": updated,
        "errors": errors,
    })


# ─── Invoice Export (server-side CSV) ────────────────────────────────────────

@api_view(["GET"])
@permission_classes([RoleWriteAccess])
def invoices_export(request):
    """Export all invoices (with lines) as a flat CSV."""
    qs = Invoice.objects.select_related("customer").prefetch_related(
        "lines__account", "lines__tax_code"
    ).all()

    # Apply same filters as list view
    if request.query_params.get("status"):
        qs = qs.filter(status=request.query_params["status"])
    if request.query_params.get("customer_id"):
        qs = qs.filter(customer_id=request.query_params["customer_id"])
    if request.query_params.get("date_from"):
        qs = qs.filter(date__gte=request.query_params["date_from"])
    if request.query_params.get("date_to"):
        qs = qs.filter(date__lte=request.query_params["date_to"])
    response = HttpResponse(content_type="text/csv; charset=utf-8")
    response["Content-Disposition"] = 'attachment; filename="invoices.csv"'
    response.write("\ufeff")  # BOM for Excel

    writer = SafeWriter(response)
    writer.writerow([
        "invoice_number", "customer_code", "customer_name", "date", "due_date",
        "status", "currency", "exchange_rate", "delivery_date",
        "line_description", "line_quantity", "line_unit_price",
        "line_account_code", "line_tax_code", "line_amount",
        "subtotal", "tax_amount", "total",
    ])

    for inv in qs:
        lines = inv.lines.select_related("account", "tax_code").all()
        vq = str(inv.exchange_rate)
        vy = inv.delivery_date.isoformat() if inv.delivery_date else ""
        if lines:
            for line in lines:
                writer.writerow([
                    inv.invoice_number, inv.customer.code, inv.customer.name,
                    inv.date.isoformat(), inv.due_date.isoformat(),
                    inv.status, inv.currency, vq, vy,
                    line.description, str(line.quantity), str(line.unit_price),
                    line.account.code if line.account else "",
                    line.tax_code.code if line.tax_code else "",
                    str(line.amount),
                    str(inv.subtotal), str(inv.tax_amount), str(inv.total),
                ])
        else:
            writer.writerow([
                inv.invoice_number, inv.customer.code, inv.customer.name,
                inv.date.isoformat(), inv.due_date.isoformat(),
                inv.status, inv.currency, vq, vy,
                "", "", "", "", "", "",
                str(inv.subtotal), str(inv.tax_amount), str(inv.total),
            ])

    return response
