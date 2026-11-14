"""Tilbud (quotes/...) og rykkere (reminders/...). Feature-gatet som "invoicing".

Tilbud:  GET/POST quotes, GET/PUT/DELETE quotes/<id>, POST quotes/<id>/status
         {status}, POST quotes/<id>/invoice → fakturaudkast.
Rykkere: GET reminders?invoice_id=, POST reminders {invoice_id, date?, fee?,
         interest?, text?} (bogfører gebyret), GET reminders/candidates.
"""

from datetime import date, timedelta
from decimal import Decimal, InvalidOperation

from django.db import transaction
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response

from accounts import chart
from accounts.models import Account
from core.audit import log_action
from core.permissions import RoleWriteAccess
from core.vat import EntryBuilder
from journals.lettrage import customer_partner
from journals.numbering import next_number
from journals.periods import _to_date, closed_period_error

from . import invoicing
from .models import Customer, Invoice, InvoiceLine, Quote, QuoteLine, Reminder


def _user(request):
    return f"{request.user.first_name} {request.user.last_name}".strip() or request.user.username


def _quote_dict(q, include_lines=True):
    d = {
        "id": str(q.id), "quote_number": q.quote_number, "customer_id": str(q.customer_id),
        "customer_name": q.customer.name, "date": q.date.isoformat(),
        "valid_until": q.valid_until.isoformat() if q.valid_until else None, "status": q.status,
        "currency": q.currency, "subtotal": str(q.subtotal), "tax_amount": str(q.tax_amount),
        "total": str(q.total), "notes": q.notes,
        "invoice_id": str(q.invoices.first().id) if q.invoices.exists() else None,
        "created_by": q.created_by,
    }
    if include_lines:
        d["lines"] = [{
            "id": str(l.id), "description": l.description, "quantity": str(l.quantity), "unit": l.unit,
            "unit_price": str(l.unit_price), "amount": str(l.amount), "is_text": l.is_text,
            "tax_code_id": str(l.tax_code_id) if l.tax_code_id else None,
            "tax_code_code": l.tax_code.code if l.tax_code_id else None,
            "account_id": str(l.account_id) if l.account_id else None, "position": l.position,
        } for l in q.lines.select_related("tax_code").all()]
    return d


def _apply_quote(q, data):
    if "customer_id" in data:
        c = Customer.objects.filter(id=data["customer_id"]).first()
        if c is None:
            return "Kunden findes ikke"
        q.customer = c
    if "date" in data:
        q.date = _to_date(data["date"])
        if q.date is None:
            return "Ugyldig dato"
    if "valid_until" in data:
        q.valid_until = _to_date(data["valid_until"]) if data["valid_until"] else None
    if "currency" in data:
        q.currency = (data["currency"] or chart.BASE_CURRENCY).upper()
    if "notes" in data:
        q.notes = data["notes"] or ""
    if q.valid_until is None and q.date:
        q.valid_until = q.date + timedelta(days=30)
    return None


@api_view(["GET", "POST"])
@permission_classes([RoleWriteAccess])
def quotes_list_create(request):
    if request.method == "GET":
        qs = Quote.objects.select_related("customer")
        if request.query_params.get("status"):
            qs = qs.filter(status=request.query_params["status"])
        if request.query_params.get("customer_id"):
            qs = qs.filter(customer_id=request.query_params["customer_id"])
        return Response({"success": True, "quotes": [_quote_dict(q, include_lines=False) for q in qs]})
    data = request.data
    if not data.get("customer_id") or not data.get("date"):
        return Response({"success": False, "message": "customer_id og date skal angives"},
                        status=status.HTTP_400_BAD_REQUEST)
    q = Quote(quote_number=next_number(Quote, "quote_number", "T"), created_by=_user(request))
    err = _apply_quote(q, data)
    if err:
        return Response({"success": False, "message": err}, status=status.HTTP_400_BAD_REQUEST)
    try:
        with transaction.atomic():
            q.save()
            invoicing.save_lines(q, QuoteLine, "quote", data.get("lines", []))
            invoicing.refresh_totals(q)
    except invoicing.LineError as e:
        return Response({"success": False, "message": str(e)}, status=status.HTTP_400_BAD_REQUEST)
    log_action(request.user, "create", "Quote", q.id, {"quote_number": q.quote_number})
    return Response({"success": True, "message": "Tilbud oprettet", "quote": _quote_dict(q)},
                    status=status.HTTP_201_CREATED)


@api_view(["GET", "PUT", "DELETE"])
@permission_classes([RoleWriteAccess])
def quotes_detail(request, pk):
    q = Quote.objects.select_related("customer").filter(id=pk).first()
    if q is None:
        return Response({"success": False, "message": "Tilbuddet findes ikke"}, status=status.HTTP_404_NOT_FOUND)
    if request.method == "GET":
        return Response({"success": True, "quote": _quote_dict(q)})
    if q.status == "invoiced":
        return Response({"success": False, "message": "Tilbuddet er faktureret"}, status=status.HTTP_400_BAD_REQUEST)
    if request.method == "DELETE":
        q.delete()
        log_action(request.user, "delete", "Quote", pk, {"quote_number": q.quote_number})
        return Response({"success": True, "message": "Tilbuddet er slettet"})
    err = _apply_quote(q, request.data)
    if err:
        return Response({"success": False, "message": err}, status=status.HTTP_400_BAD_REQUEST)
    try:
        with transaction.atomic():
            q.save()
            if request.data.get("lines") is not None:
                invoicing.save_lines(q, QuoteLine, "quote", request.data["lines"])
            invoicing.refresh_totals(q)
    except invoicing.LineError as e:
        return Response({"success": False, "message": str(e)}, status=status.HTTP_400_BAD_REQUEST)
    return Response({"success": True, "message": "Tilbuddet er opdateret", "quote": _quote_dict(q)})


@api_view(["POST"])
@permission_classes([RoleWriteAccess])
def quote_status(request, pk):
    q = Quote.objects.select_related("customer").filter(id=pk).first()
    if q is None:
        return Response({"success": False, "message": "Tilbuddet findes ikke"}, status=status.HTTP_404_NOT_FOUND)
    new = request.data.get("status")
    if new not in ("draft", "sent", "accepted", "rejected") or q.status == "invoiced":
        return Response({"success": False, "message": "Ugyldig status"}, status=status.HTTP_400_BAD_REQUEST)
    q.status = new
    q.save(update_fields=["status"])
    log_action(request.user, "update", "Quote", q.id, {"quote_number": q.quote_number, "status": new})
    return Response({"success": True, "quote": _quote_dict(q)})


@api_view(["POST"])
@permission_classes([RoleWriteAccess])
def quote_to_invoice(request, pk):
    """Lav et fakturaudkast ud fra tilbuddet."""
    q = Quote.objects.select_related("customer").filter(id=pk).first()
    if q is None:
        return Response({"success": False, "message": "Tilbuddet findes ikke"}, status=status.HTTP_404_NOT_FOUND)
    if q.status == "invoiced":
        return Response({"success": False, "message": "Tilbuddet er allerede faktureret"},
                        status=status.HTTP_400_BAD_REQUEST)
    on = _to_date(request.data.get("date")) or date.today()
    c = q.customer
    with transaction.atomic():
        inv = Invoice.objects.create(
            invoice_number=invoicing.draft_number(), customer=c, date=on,
            due_date=invoicing.due_date_for(on, c.payment_terms_code), payment_terms_code=c.payment_terms_code,
            currency=q.currency, quote=q, notes=q.notes, created_by=_user(request))
        for l in q.lines.all():
            InvoiceLine.objects.create(invoice=inv, description=l.description, quantity=l.quantity, unit=l.unit,
                                       unit_price=l.unit_price, tax_code=l.tax_code, account=l.account,
                                       is_text=l.is_text, position=l.position)
        invoicing.refresh_totals(inv)
        q.status = "invoiced"
        q.save(update_fields=["status"])
    log_action(request.user, "create", "Invoice", inv.id, {"from_quote": q.quote_number})
    return Response({"success": True, "message": "Fakturaudkast oprettet fra tilbuddet",
                     "invoice_id": str(inv.id)}, status=status.HTTP_201_CREATED)


# ─── Rykkere (renteloven) ─────────────────────────────────────────────────────

def _reminder_dict(r):
    return {"id": str(r.id), "invoice_id": str(r.invoice_id), "invoice_number": r.invoice.invoice_number,
            "customer_name": r.invoice.customer.name, "level": r.level, "date": r.date.isoformat(),
            "due_date": r.due_date.isoformat(), "fee": str(r.fee), "interest": str(r.interest), "text": r.text,
            "journal_entry_id": str(r.journal_entry_id) if r.journal_entry_id else None,
            "balance_due": str(r.invoice.balance_due),
            "total_due": str(r.invoice.balance_due + sum((x.fee + x.interest for x in r.invoice.reminders.all()),
                                                        Decimal("0")))}


def reminder_error(invoice, on, fee):
    """Hvorfor rykkeren ikke må sendes, eller None (renteloven § 9 b)."""
    from core.models import CompanySettings

    if not invoice.journal_entry_id:
        return "Fakturaen er ikke udstedt"
    if invoice.balance_due <= 0:
        return "Fakturaen er betalt"
    if on <= invoice.due_date:
        return "Fakturaen er ikke forfalden"
    last = invoice.reminders.order_by("-level").first()
    if last and last.level >= Reminder.MAX_LEVEL:
        return f"Der er allerede sendt {Reminder.MAX_LEVEL} rykkere (renteloven § 9 b)"
    s = CompanySettings.objects.first()
    interval = s.reminder_interval_days if s else 10
    if last and (on - last.date).days < max(interval, 10):
        return "Der skal gå mindst 10 dage mellem rykkerne (renteloven § 9 b, stk. 1)"
    if fee < 0 or fee > Reminder.MAX_FEE:
        return f"Rykkergebyret må højst være {Reminder.MAX_FEE} kr. (renteloven § 9 b)"
    return None


@api_view(["GET", "POST"])
@permission_classes([RoleWriteAccess])
def reminders_list_create(request):
    from core.models import CompanySettings

    if request.method == "GET":
        qs = Reminder.objects.select_related("invoice", "invoice__customer")
        if request.query_params.get("invoice_id"):
            qs = qs.filter(invoice_id=request.query_params["invoice_id"])
        return Response({"success": True, "reminders": [_reminder_dict(r) for r in qs]})
    data = request.data
    invoice = Invoice.objects.select_related("customer").filter(id=data.get("invoice_id") or None).first()
    if invoice is None:
        return Response({"success": False, "message": "Fakturaen findes ikke"}, status=status.HTTP_404_NOT_FOUND)
    on = _to_date(data.get("date")) or date.today()
    s = CompanySettings.objects.first()
    try:
        fee = Decimal(str(data["fee"])) if data.get("fee") not in (None, "") else (s.reminder_fee if s else
                                                                                     Decimal("100"))
        interest = Decimal(str(data.get("interest") or 0))
    except InvalidOperation:
        return Response({"success": False, "message": "Ugyldigt beløb"}, status=status.HTTP_400_BAD_REQUEST)
    err = reminder_error(invoice, on, fee) or closed_period_error(on)
    if err:
        return Response({"success": False, "message": err}, status=status.HTTP_400_BAD_REQUEST)
    with transaction.atomic():
        level = (invoice.reminders.order_by("-level").values_list("level", flat=True).first() or 0) + 1
        r = Reminder.objects.create(
            invoice=invoice, level=level, date=on, due_date=on + timedelta(days=10), fee=fee, interest=interest,
            text=data.get("text") or f"{level}. rykker for faktura {invoice.invoice_number}",
            created_by=_user(request))
        amount = fee + interest
        if amount > 0:
            from journals.models import JournalEntry
            from journals.numbering import next_je_number
            # Rykkergebyr og morarenter er erstatning, ikke vederlag: ingen moms.
            builder = EntryBuilder()
            label = f"Rykker {level} faktura {invoice.invoice_number} — {invoice.customer.name}"
            builder.add(Account.objects.get(code=chart.RECEIVABLE), amount, description=label,
                        partner=customer_partner(invoice.customer))
            builder.add(Account.objects.get(code=chart.REMINDER_FEES), -amount, description=label)
            entry = JournalEntry.objects.create(
                entry_number=next_je_number(), date=on, description=label,
                reference=f"RYKKER:{invoice.invoice_number}:{level}", piece_number=invoice.invoice_number,
                source="reminder", source_id=str(r.id), is_posted=True, created_by=_user(request))
            builder.write(entry)
            r.journal_entry = entry
            r.save(update_fields=["journal_entry"])
        if invoice.status == "sent":
            invoice.status = "overdue"
            invoice.save(update_fields=["status"])
    log_action(request.user, "create", "Reminder", r.id,
               {"invoice_number": invoice.invoice_number, "level": level, "fee": str(fee)})
    return Response({"success": True, "message": f"{level}. rykker er oprettet", "reminder": _reminder_dict(r)},
                    status=status.HTTP_201_CREATED)


@api_view(["GET"])
@permission_classes([RoleWriteAccess])
def reminder_candidates(request):
    """Forfaldne, ubetalte fakturaer, og om de kan rykkes i dag."""
    from core.models import CompanySettings

    today = _to_date(request.query_params.get("date")) or date.today()
    s = CompanySettings.objects.first()
    fee = s.reminder_fee if s else Decimal("100")
    out = []
    for inv in (Invoice.objects.select_related("customer").filter(journal_entry__isnull=False, due_date__lt=today)
                .exclude(status__in=("paid", "cancelled"))):
        if inv.balance_due <= 0:
            continue
        last = inv.reminders.order_by("-level").first()
        out.append({"invoice_id": str(inv.id), "invoice_number": inv.invoice_number,
                    "customer_name": inv.customer.name, "due_date": inv.due_date.isoformat(),
                    "days_overdue": (today - inv.due_date).days, "balance_due": str(inv.balance_due),
                    "reminders_sent": last.level if last else 0,
                    "last_reminder": last.date.isoformat() if last else None,
                    "can_remind": reminder_error(inv, today, fee) is None,
                    "reason": reminder_error(inv, today, fee) or ""})
    return Response({"success": True, "candidates": out, "default_fee": str(fee)})
