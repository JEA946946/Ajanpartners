"""Posteringer (CRUD, bogfør/tilbagefør kladde), bankimport og bankposteringer."""

import csv
import io
import re
from datetime import datetime, timedelta, timezone
from decimal import Decimal, InvalidOperation

from django.db import transaction
from django.db.models import Sum, Q
from django.http import HttpResponse
from rest_framework import status
from rest_framework.decorators import api_view, parser_classes, permission_classes
from rest_framework.parsers import MultiPartParser, FormParser
from core.permissions import RoleWriteAccess
from core.csv_utils import SafeWriter
from rest_framework.response import Response

from accounts import chart
from accounts.models import Account, AccountType
from core.audit import log_action
from .journal_for import MISC, journal_for_account
from .models import BankDescriptionMapping, BankStatementUpload, Journal, JournalEntry, JournalEntryLine
from .periods import closed_period_error


# ─── helpers ──────────────────────────────────────────────────────────────────

def _line_dict(line):
    return {
        "id": str(line.id),
        "line_no": line.line_no,
        "account_id": str(line.account_id),
        "account_code": line.account.code,
        "account_name": line.account.name,
        "debit": str(line.debit),
        "credit": str(line.credit),
        "currency": line.currency,
        "exchange_rate": str(line.exchange_rate),
        "amount_currency": str(line.amount_currency) if line.amount_currency is not None else None,
        "vat_code": line.vat_code,
        "description": line.description,
        "partner_type": line.partner_type,
        "partner_id": line.partner_id,
        "partner_name": line.partner_name,
        "lettrage": line.lettrage,
    }


def _entry_dict(entry, include_lines=True):
    d = {
        "id": str(entry.id),
        "entry_number": entry.entry_number,
        "journal_id": entry.journal_id,
        "journal_code": entry.journal.code,
        "journal_name": entry.journal.name,
        "piece_number": entry.piece_number,
        "status": entry.status,
        "validated_at": entry.validated_at.isoformat() if entry.validated_at else None,
        "validated_by": entry.validated_by,
        "reversal_of": entry.reversal_of.entry_number if entry.reversal_of_id else None,
        "reversed_by": entry.reversed_by.entry_number if hasattr(entry, "reversed_by") else None,
        "documents": entry.documents.count(),
        "date": entry.date.isoformat() if hasattr(entry.date, 'isoformat') else str(entry.date),
        "description": entry.description,
        "reference": entry.reference,
        "source": entry.source,
        "source_id": entry.source_id,
        "is_posted": entry.is_posted,
        "total_debit": str(entry.total_debit),
        "total_credit": str(entry.total_credit),
        "is_balanced": entry.is_balanced,
        "created_by": entry.created_by,
        "created_at": entry.created_at.isoformat() if entry.created_at else None,
        "updated_at": entry.updated_at.isoformat() if entry.updated_at else None,
    }
    if include_lines:
        d["lines"] = [_line_dict(l) for l in entry.lines.select_related("account").all()]
        d["document_list"] = [{"id": str(doc.id), "filename": doc.filename, "piece_number": doc.piece_number}
                              for doc in entry.documents.all()]
    return d


def _next_entry_number():
    """Generate next sequential entry number like JE-0001."""
    from journals.numbering import next_je_number
    return next_je_number()


# ─── Journal Entries CRUD ─────────────────────────────────────────────────────

@api_view(["GET", "POST"])
@permission_classes([RoleWriteAccess])
def journal_entries_list_create(request):
    if request.method == "GET":
        qs = JournalEntry.objects.select_related("journal", "reversal_of")
        # Filters
        if request.query_params.get("is_posted"):
            qs = qs.filter(is_posted=request.query_params["is_posted"].lower() == "true")
        if request.query_params.get("journal"):
            qs = qs.filter(journal__code=request.query_params["journal"])
        st = request.query_params.get("status")
        if st == "validated":
            qs = qs.filter(validated_at__isnull=False)
        elif st in ("posted", "brouillard"):
            qs = qs.filter(is_posted=True, validated_at__isnull=True)
        elif st == "draft":
            qs = qs.filter(is_posted=False)
        if request.query_params.get("source"):
            qs = qs.filter(source=request.query_params["source"])
        if request.query_params.get("date_from"):
            qs = qs.filter(date__gte=request.query_params["date_from"])
        if request.query_params.get("date_to"):
            qs = qs.filter(date__lte=request.query_params["date_to"])
        if request.query_params.get("search"):
            q = request.query_params["search"]
            qs = qs.filter(
                Q(entry_number__icontains=q) |
                Q(description__icontains=q) |
                Q(reference__icontains=q)
            )

        total_count = qs.count()

        # Pagination
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
        entries = qs[offset:offset + page_size]

        return Response({
            "success": True,
            "data": {
                "journal_entries": [_entry_dict(e, include_lines=False) for e in entries],
                "count": total_count,
                "total_count": total_count,
                "page": page,
                "page_size": page_size,
            },
        })

    # POST — create journal entry with lines
    data = request.data
    if not data.get("date"):
        return Response(
            {"success": False, "message": "date is required"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    err = closed_period_error(data["date"])
    if err:
        return Response({"success": False, "message": err}, status=status.HTTP_400_BAD_REQUEST)

    lines_data = data.get("lines", [])
    if len(lines_data) < 2:
        return Response(
            {"success": False, "message": "At least 2 lines required for double-entry"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    # Validate balance
    total_debit = Decimal("0")
    total_credit = Decimal("0")
    for line in lines_data:
        try:
            d = Decimal(str(line.get("debit", 0)))
            c = Decimal(str(line.get("credit", 0)))
        except (InvalidOperation, TypeError):
            return Response(
                {"success": False, "message": "Invalid debit/credit amount"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        total_debit += d
        total_credit += c

    if total_debit != total_credit:
        return Response(
            {"success": False, "message": f"Entry not balanced: DR {total_debit} != CR {total_credit}"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    # Validate accounts exist
    account_ids = [line.get("account_id") for line in lines_data]
    accounts = {str(a.id): a for a in Account.objects.filter(id__in=account_ids)}
    for aid in account_ids:
        if aid not in accounts:
            return Response(
                {"success": False, "message": f"Account {aid} not found"},
                status=status.HTTP_400_BAD_REQUEST,
            )
    terr = _tiers_error(lines_data, accounts)
    if terr:
        return Response({"success": False, "message": terr}, status=status.HTTP_400_BAD_REQUEST)

    journal = _journal_from(data)
    if journal is None:
        return Response({"success": False, "message": "Journal not found"}, status=status.HTTP_400_BAD_REQUEST)

    # The number, source and source id are the system's; a manual entry gets a
    # draft number now and its final one when its month is closed.
    with transaction.atomic():
        entry = JournalEntry.objects.create(
            journal=journal,
            entry_number=_next_entry_number(),
            piece_number=data.get("piece_number", ""),
            date=data["date"],
            description=data.get("description", ""),
            reference=data.get("reference", ""),
            source="manual",
            is_posted=False,
            created_by=f"{request.user.first_name} {request.user.last_name}".strip() or request.user.username,
        )

        for line in lines_data:
            JournalEntryLine.objects.create(
                journal_entry=entry,
                account_id=line["account_id"],
                debit=Decimal(str(line.get("debit", 0))),
                credit=Decimal(str(line.get("credit", 0))),
                description=line.get("description", ""),
                vat_code=(line.get("vat_code") or "")[:20],
                **_line_currency(line),
                **_line_tiers(line),
            )

    entry.refresh_from_db()
    log_action(request.user, "create", "JournalEntry", entry.id,
               {"entry_number": entry.entry_number, "date": str(entry.date)})
    return Response({
        "success": True,
        "message": "Journal entry created",
        "data": {"journal_entry": _entry_dict(entry)},
    }, status=status.HTTP_201_CREATED)


def _line_currency(line):
    """Valutafelterne på en manuel linje. debit/credit er altid DKK; en linje i
    fremmed valuta har sin kurs og sit valutabeløb med."""
    currency = (line.get("currency") or chart.BASE_CURRENCY).upper()
    if currency == chart.BASE_CURRENCY:
        return {"currency": currency}
    try:
        rate = Decimal(str(line.get("exchange_rate") or 0))
        amount = line.get("amount_currency")
        amount = Decimal(str(amount)) if amount not in (None, "") else None
    except (InvalidOperation, TypeError):
        rate, amount = Decimal("0"), None
    if amount is None and rate > 0:
        dkk = Decimal(str(line.get("debit", 0))) - Decimal(str(line.get("credit", 0)))
        amount = (dkk / rate).quantize(Decimal("0.01"))
    return {"currency": currency, "exchange_rate": rate or Decimal("1"), "amount_currency": amount}


def _line_tiers(line):
    """The tiers fields of a manual line (resolved and checked by _tiers_error)."""
    return {k: line.get(k, "") for k in ("partner_type", "partner_id", "partner_name")}


def _tiers_error(lines_data, accounts):
    """En linje på debitor-, forudbetalings- eller kreditorkontoen skal have sin debitor/kreditor.
    Fills in partner_type and partner_name from the id. Returns an error or None."""
    from purchases.models import Supplier
    from sales.models import Customer
    from .lettrage import tiers_type

    for line in lines_data:
        kind = tiers_type(accounts[line["account_id"]].code)
        if not kind:
            for k in ("partner_type", "partner_id", "partner_name"):
                line[k] = ""
            continue
        model = Customer if kind == "customer" else Supplier
        obj = model.objects.filter(id=line.get("partner_id") or None).first() if line.get("partner_id") else None
        if obj is None:
            label = "customer" if kind == "customer" else "supplier"
            return f"Line on {accounts[line['account_id']].code} needs a {label}"
        line.update(partner_type=kind, partner_id=str(obj.id), partner_name=obj.name)
    return None


def _journal_from(data):
    """The journal a manual entry goes in: journal_id or journal_code, default OD."""
    if data.get("journal_id"):
        return Journal.objects.filter(id=data["journal_id"], is_active=True).first()
    return Journal.objects.filter(code=data.get("journal_code") or MISC, is_active=True).first()


def _entry_dependents(entry):
    """Why this entry's lines must not be deleted or replaced, or None.

    Bill payments and categorisations hang on its lines (they would cascade away
    and leave the bill "paid" with nothing behind it), and invoices, bills,
    expenses, payments and credit notes point at the entry itself."""
    from purchases.models import BankTransactionCategorization, Bill, BillPaymentLink, Expense
    from sales.models import CreditNote, Invoice
    from core.models import Payment

    if BillPaymentLink.objects.filter(journal_entry_line__journal_entry=entry).exists():
        return "This entry pays a bill. Undo the bill match first."
    if BankTransactionCategorization.objects.filter(journal_entry_line__journal_entry=entry).exists():
        return "This bank line is categorised. Undo the categorisation first."
    if entry.lines.exclude(lettrage="").exists():
        return "Lines of this entry are lettered. Remove the lettrage first."
    for model, label in ((Invoice, "an invoice"), (Bill, "a bill"), (Expense, "an expense"),
                         (Payment, "a payment"), (CreditNote, "a credit note")):
        if model.objects.filter(journal_entry=entry).exists():
            return f"This entry belongs to {label}. Change it there instead."
    return None


@api_view(["GET", "PUT", "DELETE"])
@permission_classes([RoleWriteAccess])
def journal_entries_detail(request, pk):
    try:
        entry = JournalEntry.objects.get(id=pk)
    except JournalEntry.DoesNotExist:
        return Response(
            {"success": False, "message": "Journal entry not found"},
            status=status.HTTP_404_NOT_FOUND,
        )

    if request.method == "GET":
        return Response({
            "success": True,
            "data": {"journal_entry": _entry_dict(entry)},
        })

    if request.method == "DELETE":
        if entry.is_posted:
            return Response(
                {"success": False, "message": "Cannot delete a posted entry. Unpost it first."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        err = closed_period_error(entry.date) or _entry_dependents(entry)
        if err:
            return Response({"success": False, "message": err}, status=status.HTTP_400_BAD_REQUEST)
        entry_number = entry.entry_number
        entry.delete()
        log_action(request.user, "delete", "JournalEntry", pk,
                   {"entry_number": entry_number})
        return Response({"success": True, "message": "Journal entry deleted"})

    # PUT — update
    if entry.is_posted:
        return Response(
            {"success": False, "message": "Cannot edit a posted entry. Unpost it first."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    data = request.data

    # Guard both the entry's current period and the one it is being moved to.
    err = closed_period_error(entry.date) or closed_period_error(data.get("date"))
    if err:
        return Response({"success": False, "message": err}, status=status.HTTP_400_BAD_REQUEST)

    lines_data = data.get("lines", [])

    if lines_data:
        dep = _entry_dependents(entry)
        if dep:
            return Response({"success": False, "message": dep}, status=status.HTTP_400_BAD_REQUEST)
        if len(lines_data) < 2:
            return Response(
                {"success": False, "message": "At least 2 lines required"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        total_debit = sum(Decimal(str(l.get("debit", 0))) for l in lines_data)
        total_credit = sum(Decimal(str(l.get("credit", 0))) for l in lines_data)
        if total_debit != total_credit:
            return Response(
                {"success": False, "message": f"Entry not balanced: DR {total_debit} != CR {total_credit}"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        accounts = {str(a.id): a for a in Account.objects.filter(id__in=[l.get("account_id") for l in lines_data])}
        if any(l.get("account_id") not in accounts for l in lines_data):
            return Response({"success": False, "message": "Account not found"}, status=status.HTTP_400_BAD_REQUEST)
        terr = _tiers_error(lines_data, accounts)
        if terr:
            return Response({"success": False, "message": terr}, status=status.HTTP_400_BAD_REQUEST)

    if "journal_id" in data or "journal_code" in data:
        journal = _journal_from(data)
        if journal is None:
            return Response({"success": False, "message": "Journal not found"}, status=status.HTTP_400_BAD_REQUEST)
        entry.journal = journal

    def snapshot():
        return {
            "journal": entry.journal.code, "date": str(entry.date), "description": entry.description,
            "piece_number": entry.piece_number,
            "lines": [[l.account.code, str(l.debit), str(l.credit), l.partner_name, l.description]
                      for l in entry.lines.select_related("account")],
        }

    before = snapshot()
    with transaction.atomic():
        for field in ("date", "description", "reference", "piece_number"):
            if field in data:
                setattr(entry, field, data[field])
        entry.save()

        if lines_data:
            entry.lines.all().delete()
            for line in lines_data:
                JournalEntryLine.objects.create(
                    journal_entry=entry,
                    account_id=line["account_id"],
                    debit=Decimal(str(line.get("debit", 0))),
                    credit=Decimal(str(line.get("credit", 0))),
                    description=line.get("description", ""),
                    vat_code=(line.get("vat_code") or "")[:20],
                    **_line_currency(line),
                    **_line_tiers(line),
                )

    log_action(request.user, "update", "JournalEntry", entry.id,
               {"entry_number": entry.entry_number, "before": before, "after": snapshot()})
    return Response({
        "success": True,
        "message": "Journal entry updated",
        "data": {"journal_entry": _entry_dict(entry)},
    })


@api_view(["POST"])
@permission_classes([RoleWriteAccess])
def journal_entry_post(request, pk):
    try:
        entry = JournalEntry.objects.get(id=pk)
    except JournalEntry.DoesNotExist:
        return Response(
            {"success": False, "message": "Journal entry not found"},
            status=status.HTTP_404_NOT_FOUND,
        )

    if entry.is_posted:
        return Response(
            {"success": False, "message": "Already posted"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    if not entry.is_balanced:
        return Response(
            {"success": False, "message": "Cannot post unbalanced entry"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    if entry.lines.count() < 2:
        return Response(
            {"success": False, "message": "Entry must have at least 2 lines"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    err = closed_period_error(entry.date)
    if err:
        return Response({"success": False, "message": err}, status=status.HTTP_400_BAD_REQUEST)

    entry.is_posted = True
    entry.save(update_fields=["is_posted", "updated_at"])
    log_action(request.user, "post", "JournalEntry", entry.id,
               {"entry_number": entry.entry_number, "date": str(entry.date)})
    return Response({
        "success": True,
        "message": "Journal entry posted",
        "data": {"journal_entry": _entry_dict(entry)},
    })


@api_view(["POST"])
@permission_classes([RoleWriteAccess])
def journal_entry_unpost(request, pk):
    try:
        entry = JournalEntry.objects.get(id=pk)
    except JournalEntry.DoesNotExist:
        return Response(
            {"success": False, "message": "Journal entry not found"},
            status=status.HTTP_404_NOT_FOUND,
        )

    if not entry.is_posted:
        return Response(
            {"success": False, "message": "Entry is not posted"},
            status=status.HTTP_400_BAD_REQUEST,
        )
    if entry.source != "manual":
        return Response(
            {"success": False, "message": "Only a manual entry can be unposted; change the document it comes from"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    err = closed_period_error(entry.date)
    if err:
        return Response({"success": False, "message": err}, status=status.HTTP_400_BAD_REQUEST)

    entry.is_posted = False
    entry.save(update_fields=["is_posted", "updated_at"])
    log_action(request.user, "unpost", "JournalEntry", entry.id,
               {"entry_number": entry.entry_number, "date": str(entry.date)})
    return Response({
        "success": True,
        "message": "Journal entry unposted",
        "data": {"journal_entry": _entry_dict(entry)},
    })


# ─── Bank Statement Upload ────────────────────────────────────────────────────

def _parse_date(val):
    """Parse a date value from CSV/Excel into a date object."""
    if hasattr(val, "date"):
        return val.date()
    if hasattr(val, "strftime"):
        return val
    if isinstance(val, str):
        val = val.strip()
        for fmt in ("%d-%m-%Y", "%d.%m.%Y", "%d/%m/%Y", "%Y-%m-%d", "%d-%m-%y", "%d.%m.%y", "%Y/%m/%d"):
            try:
                return datetime.strptime(val, fmt).date()
            except ValueError:
                continue
    return None


def _safe_decimal(val):
    """Convert a value to Decimal, returning 0 for empty/invalid.

    Handles European formats like 1.500,50 and 1 500,50 as well as
    standard formats like 1,500.50 and 1500.50.
    """
    if val is None:
        return Decimal("0")
    if isinstance(val, (int, float)):
        return Decimal(str(val))
    val = str(val).strip().replace("\xa0", "").replace(" ", "")
    if not val:
        return Decimal("0")
    # Detect European format: comma is decimal separator
    # e.g. "1.500,50" or "1500,50"
    if "," in val and "." in val:
        if val.rindex(",") > val.rindex("."):
            # European: 1.500,50 → 1500.50
            val = val.replace(".", "").replace(",", ".")
        else:
            # US: 1,500.50 → 1500.50
            val = val.replace(",", "")
    elif "," in val:
        # Could be "1500,50" (European decimal) or "1,500" (US thousands)
        # If exactly 3 digits after comma, treat as thousands separator
        parts = val.split(",")
        if len(parts) == 2 and len(parts[1]) == 3 and parts[1].isdigit():
            val = val.replace(",", "")
        elif len(parts) > 2 and all(len(p) == 3 and p.isdigit() for p in parts[1:]):
            val = val.replace(",", "")  # "1,234,567" — thousands, it used to become 0
        else:
            val = val.replace(",", ".")
    try:
        return Decimal(val)
    except InvalidOperation:
        return Decimal("0")


# Kolonnenavne i danske bankers eksport (Danske Bank, Nordea, Jyske Bank,
# Sydbank, Lunar, Spar Nord, Arbejdernes Landsbank) og generiske navne.
_DATE_COLS = ("dato", "bogføringsdato", "bogfoeringsdato", "bogført", "posteringsdato", "date",
              "transaktionsdato", "valørdato", "rentedato")
_TEXT_COLS = ("tekst", "beskrivelse", "posteringstekst", "navn", "text", "description", "modtager")
_REF_COLS = ("reference", "ref", "id", "transaktions-id", "bilagsnr")
_AMOUNT_COLS = ("beløb", "beloeb", "belob", "amount", "beløb i dkk")
_IN_COLS = ("indbetaling", "ind", "kredit", "credit", "indsat")
_OUT_COLS = ("udbetaling", "ud", "debet", "debit", "hævet")


def _col(cols, names):
    for n in names:
        if cols.get(n) not in (None, ""):
            return cols[n]
    return None


def _amounts(cols):
    """(ud, ind) fra en række: et fortegnsbeløb ('Beløb': positiv = ind) eller
    separate ind-/udkolonner. Returnerer (debit, credit) i kontoudtogets
    betydning: debit = penge ud, credit = penge ind."""
    signed = _col(cols, _AMOUNT_COLS)
    if signed is not None:
        amount = _safe_decimal(signed)
        return (-amount, Decimal("0")) if amount < 0 else (Decimal("0"), amount)
    out = abs(_safe_decimal(_col(cols, _OUT_COLS)))
    inn = abs(_safe_decimal(_col(cols, _IN_COLS)))
    return out, inn


@api_view(["POST"])
@permission_classes([RoleWriteAccess])
@parser_classes([MultiPartParser, FormParser])
def bank_statement_upload(request):
    """Parse an uploaded bank statement file and return transactions as JSON."""
    uploaded = request.FILES.get("file")
    if not uploaded:
        return Response(
            {"success": False, "message": "No file uploaded"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    bank_account_id = request.data.get("bank_account_id")
    if not bank_account_id:
        return Response(
            {"success": False, "message": "bank_account_id is required"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    # Verify bank account exists
    try:
        Account.objects.get(id=bank_account_id)
    except Account.DoesNotExist:
        return Response(
            {"success": False, "message": "Bank account not found"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    name = uploaded.name.lower()
    transactions = []
    file_format = "raw"

    # Pre-load all accounts by code for fast lookup (no per-row queries)
    account_by_code = {a.code: a for a in Account.objects.filter(is_active=True)}

    try:
        if name.endswith(".csv"):
            raw = uploaded.read()
            try:
                content = raw.decode("utf-8-sig")
            except UnicodeDecodeError:
                content = raw.decode("cp1252")  # ældre danske bankeksporter
            first = content.splitlines()[0] if content else ""
            delimiter = ";" if first.count(";") >= first.count(",") else ","
            reader = csv.DictReader(io.StringIO(content), delimiter=delimiter)
            for row in reader:
                cols = {(k or "").strip().strip('"').lower(): v for k, v in row.items()}
                op_date = _col(cols, _DATE_COLS)
                description = _col(cols, _TEXT_COLS) or ""
                reference = _col(cols, _REF_COLS) or ""
                debit, credit = _amounts(cols)

                parsed_date = _parse_date(op_date)
                if not parsed_date:
                    continue
                if debit == 0 and credit == 0:
                    continue

                txn = {
                    "date": parsed_date.isoformat(),
                    "description": str(description).strip(),
                    "reference": str(reference).strip(),
                    "debit": str(debit),
                    "credit": str(credit),
                    "account_id": None,
                }
                # Check for account_code column (pre-categorized)
                acct_code = cols.get("account_code") or cols.get("account code") or cols.get("kontonr")
                if acct_code:
                    file_format = "categorized"
                    acct_code = str(acct_code).strip()
                    acct = account_by_code.get(acct_code)
                    if acct:
                        txn["account_id"] = str(acct.id)
                        txn["account_code"] = acct.code
                        txn["account_name"] = acct.name
                    else:
                        txn["account_code"] = acct_code
                        txn["account_name"] = f"(unknown: {acct_code})"

                transactions.append(txn)

        elif name.endswith(".xlsx") or name.endswith(".xls"):
            # Read headers and data rows from either format
            if name.endswith(".xls"):
                import xlrd
                raw_bytes = uploaded.read()
                xls_wb = xlrd.open_workbook(file_contents=raw_bytes)
                xls_ws = xls_wb.sheet_by_index(0)
                headers = [str(xls_ws.cell_value(0, c) or "").strip().lower() for c in range(xls_ws.ncols)]
                data_rows = []
                for r in range(1, xls_ws.nrows):
                    row_vals = []
                    for c in range(xls_ws.ncols):
                        cell = xls_ws.cell(r, c)
                        if cell.ctype == xlrd.XL_CELL_DATE:
                            dt_tuple = xlrd.xldate_as_tuple(cell.value, xls_wb.datemode)
                            from datetime import date as _date
                            row_vals.append(_date(dt_tuple[0], dt_tuple[1], dt_tuple[2]))
                        else:
                            row_vals.append(cell.value)
                    data_rows.append(row_vals)
            else:
                import openpyxl
                wb = openpyxl.load_workbook(uploaded, data_only=True)
                ws = wb.active
                headers = [str(cell.value or "").strip().lower() for cell in ws[1]]
                data_rows = [list(row) for row in ws.iter_rows(min_row=2, values_only=True)]

            # Detect if this is a categorized file (has account_code column)
            has_acct = any(h in headers for h in ("account_code", "account code", "konto", "kontonr"))

            # Map column indices
            col_map = {}
            for i, h in enumerate(headers):
                if h in _DATE_COLS and "date" not in col_map:
                    col_map["date"] = i
                elif h in _TEXT_COLS and "description" not in col_map:
                    col_map["description"] = i
                elif h in _REF_COLS:
                    col_map["reference"] = i
                elif h in ("account_code", "account code", "konto", "kontonr"):
                    col_map["account_code"] = i

            if "date" not in col_map:
                return Response(
                    {"success": False, "message": "Kan ikke finde en datokolonne (fx 'Dato' eller 'Bogføringsdato')."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            for vals in data_rows:
                op_date = vals[col_map["date"]] if col_map.get("date") is not None else None
                description = vals[col_map["description"]] if col_map.get("description") is not None else ""
                reference = vals[col_map["reference"]] if col_map.get("reference") is not None else ""
                debit, credit = _amounts({h: vals[i] for i, h in enumerate(headers) if i < len(vals)})

                parsed_date = _parse_date(op_date)
                if not parsed_date:
                    continue
                if debit == 0 and credit == 0:
                    continue

                txn = {
                    "date": parsed_date.isoformat(),
                    "description": str(description or "").strip(),
                    "reference": str(reference or "").strip(),
                    "debit": str(debit),
                    "credit": str(credit),
                    "account_id": None,
                }

                if has_acct and col_map.get("account_code") is not None:
                    file_format = "categorized"
                    acct_code = str(vals[col_map["account_code"]] or "").strip()
                    if acct_code:
                        acct = account_by_code.get(acct_code)
                        if acct:
                            txn["account_id"] = str(acct.id)
                            txn["account_code"] = acct.code
                            txn["account_name"] = acct.name
                        else:
                            txn["account_code"] = acct_code
                            txn["account_name"] = f"(unknown: {acct_code})"

                transactions.append(txn)
        else:
            return Response(
                {"success": False, "message": "Unsupported file format. Use .csv or .xlsx"},
                status=status.HTTP_400_BAD_REQUEST,
            )
    except Exception as e:
        return Response(
            {"success": False, "message": f"Error parsing file: {str(e)}"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    # Duplicate detection: check for existing bank-source entries in the same date range
    duplicate_warning = ""
    if transactions:
        dates = [t["date"] for t in transactions]
        min_date = min(dates)
        max_date = max(dates)
        existing_count = JournalEntry.objects.filter(
            source="bank",
            date__gte=min_date,
            date__lte=max_date,
        ).count()
        if existing_count > 0:
            duplicate_warning = (
                f"Warning: {existing_count} bank-source journal entries already exist "
                f"between {min_date} and {max_date}. This upload may create duplicates."
            )

    return Response({
        "success": True,
        "data": {
            "transactions": transactions,
            "format": file_format,
            "duplicate_warning": duplicate_warning,
        },
    })


# Danske bankers tekster → navnet på modparten (Danske Bank, Nordea, Jyske,
# Sydbank, Lunar m.fl. skriver typisk "Dankort-køb NETTO 1234" osv.).
_ENTITY_PATTERNS = [
    re.compile(r"(?:dankort|visa|mastercard|kort)[\s-]*(?:køb|kob|nota)?\s+(.+)", re.I),
    re.compile(r"mobilepay\s+(?:til|fra)?\s*(.+)", re.I),
    re.compile(r"(?:overførsel|overforsel|overf\.)\s+(?:til|fra)?\s*(.+)", re.I),
    re.compile(r"(?:betalingsservice|bs)\s+(.+)", re.I),
    re.compile(r"(?:indbetaling|udbetaling)\s+(?:fra|til)?\s*(.+)", re.I),
    re.compile(r"(?:fi-kort|fik|kort\s*71|\+71)\s+(.+)", re.I),
]

# Faste nøgleord → konto
_KEYWORD_ACCOUNT_MAP = {
    "gebyr": chart.BANK_FEES,
    "kortgebyr": chart.BANK_FEES,
    "overførselsgebyr": chart.BANK_FEES,
    "kontoførelse": chart.BANK_FEES,
    "debetrente": chart.INTEREST,
    "renter af kassekredit": chart.INTEREST,
    "kreditrente": chart.INTEREST_INCOME,
}

# Navne → konto, hvor navnet ikke findes i kontoplanen
_ENTITY_ALIAS_MAP = {
    "skat": chart.VAT_SETTLEMENT,
    "skattestyrelsen": chart.VAT_SETTLEMENT,
    "revisor": chart.FEES,
}


def _normalize_entity(raw):
    """Normalize an entity name extracted from bank description."""
    name = raw.strip()
    # Remove trailing reference numbers, dates
    name = re.sub(r"\s+REF\s+\w*\d+.*$", "", name, flags=re.I)
    name = re.sub(r"\s+\d{6,}.*$", "", name)
    name = name.replace("+", " ")
    # Kortnumre og datoer ("NETTO 1234 12.03") fjernes
    name = re.sub(r"\s+\d{2}[./]\d{2}(?:[./]\d{2,4})?$", "", name)
    name = re.sub(r"\s+\d{4,}$", "", name)
    return name.strip().lower()


def _extract_description_key(description):
    """Extract a stable key from a bank description for learning.

    Uses the entity patterns to extract the entity name, which stays the same
    across transactions even when reference numbers change.
    Falls back to the full normalized description.
    """
    desc = (description or "").strip()
    if not desc:
        return ""
    for pattern in _ENTITY_PATTERNS:
        m = pattern.search(desc)
        if m:
            return _normalize_entity(m.group(1))
    # Fallback: remove numbers/references and normalize
    key = desc.lower()
    key = re.sub(r"\s+\d{6,}", "", key)
    key = key.replace("+", " ")
    key = re.sub(r"\s+", " ", key).strip()
    return key


@api_view(["POST"])
@permission_classes([RoleWriteAccess])
def bank_statement_auto_map(request):
    """Foreslå konti til banklinjer: først lærte tekster, så faste nøgleord
    (gebyr, renter), så modpartens navn (Dankort-køb, MobilePay, overførsel,
    Betalingsservice …) mod kontonavnene."""
    txns = request.data.get("transactions", [])
    bank_account_id = request.data.get("bank_account_id")
    if not txns:
        return Response({"success": True, "data": {"suggestions": []}})

    SYSTEM_CODES = set(chart.SYSTEM_ACCOUNTS)

    # Load learned mappings (highest priority)
    learned = {}  # description_key → {account_id, code, name}
    for m in BankDescriptionMapping.objects.select_related("account").all():
        learned[m.description_key] = {
            "account_id": str(m.account_id),
            "account_code": m.account.code,
            "account_name": m.account.name,
        }

    # Load all non-bank, non-system accounts
    all_accounts = list(
        Account.objects.filter(is_active=True, is_header=False)
        .exclude(chart.treasury_q())
        .exclude(code__in=SYSTEM_CODES)
        .values("id", "code", "name")
    )
    acct_by_code = {}
    for a in all_accounts:
        acct_by_code[a["code"]] = a

    # Find parent accounts (accounts that have children) — prefer children over parents
    parent_ids = set(
        str(v) for v in
        Account.objects.filter(parent__isnull=False)
        .values_list("parent_id", flat=True).distinct()
    )

    # Build name lookup: normalized name → account dict
    # "hotel perle du sud" → {id, code, name}
    name_index = {}  # normalized_name → account
    word_index = {}  # word → list of (account, total_words_in_name)
    for a in all_accounts:
        norm = a["name"].lower().strip()
        name_index[norm] = a
        words = norm.split()
        is_parent = str(a["id"]) in parent_ids
        for w in words:
            if len(w) > 2:
                word_index.setdefault(w, []).append((a, len(words), is_parent))

    def _make_suggestion(a):
        return {"account_id": str(a["id"]), "account_code": a["code"], "account_name": a["name"]}

    def _match_entity(entity_name):
        """Try to match an extracted entity name against account names."""
        if not entity_name:
            return None
        norm = entity_name.lower().strip()

        # 0) Check alias map first
        if norm in _ENTITY_ALIAS_MAP:
            acct = acct_by_code.get(_ENTITY_ALIAS_MAP[norm])
            if acct:
                return acct

        # 1) Exact name match
        if norm in name_index:
            return name_index[norm]

        # 2) Check if entity is contained in an account name or vice versa
        #    Skip parent accounts — prefer specific children
        for acct_name, acct in name_index.items():
            if str(acct["id"]) in parent_ids:
                continue
            if norm in acct_name or acct_name in norm:
                return acct

        # 3) Word scoring with prefix matching
        #    "hachimi moha" should match "Guide hachimi mohamed" (moha→mohamed)
        entity_words = [w for w in norm.split() if len(w) > 2]
        if not entity_words:
            return None
        scores = {}  # account_id → [match_count, total_words, acct, is_parent]
        for w in entity_words:
            # Exact word match
            if w in word_index:
                for acct, total_words, is_parent in word_index[w]:
                    aid = str(acct["id"])
                    if aid not in scores:
                        scores[aid] = [0, total_words, acct, is_parent]
                    scores[aid][0] += 1
            # Prefix match: "moha" matches "mohamed", "seban" matches "sebban"
            for kw, entries in word_index.items():
                if kw == w:
                    continue
                if kw.startswith(w) or w.startswith(kw):
                    for acct, total_words, is_parent in entries:
                        aid = str(acct["id"])
                        if aid not in scores:
                            scores[aid] = [0, total_words, acct, is_parent]
                        scores[aid][0] += 0.5

        if not scores:
            return None
        # Best = most matches, prefer non-parent (leaf), tiebreak fewer words
        best_id = max(
            scores,
            key=lambda k: (scores[k][0], not scores[k][3], -scores[k][1]),
        )
        match_count = scores[best_id][0]
        if match_count >= 1:
            return scores[best_id][2]
        return None

    # ── Map each transaction ──
    suggestions = []
    for i, txn in enumerate(txns):
        desc = (txn.get("description") or "").strip()
        desc_lower = desc.lower()
        if not desc_lower:
            suggestions.append(None)
            continue

        matched = None

        # Step 0: Check learned mappings (highest priority)
        desc_key = _extract_description_key(desc)
        if desc_key and desc_key in learned:
            lm = learned[desc_key]
            suggestions.append({
                "index": i,
                "account_id": lm["account_id"],
                "account_code": lm["account_code"],
                "account_name": lm["account_name"],
            })
            continue

        # Step 1: Check fixed keyword patterns (commissions, fees)
        for keyword, code in _KEYWORD_ACCOUNT_MAP.items():
            if keyword in desc_lower:
                acct = acct_by_code.get(code)
                if acct:
                    matched = acct
                break

        # Step 2: modpartens navn fra bankteksten matches mod kontonavnene
        if not matched:
            for pattern in _ENTITY_PATTERNS:
                m = pattern.search(desc)
                if m:
                    entity = _normalize_entity(m.group(1))
                    matched = _match_entity(entity)
                    break

        # Step 3: If still no match, try matching the full description against account names
        if not matched:
            matched = _match_entity(desc_lower)

        if matched:
            suggestions.append({
                "index": i,
                "account_id": str(matched["id"]),
                "account_code": matched["code"],
                "account_name": matched["name"],
            })
        else:
            suggestions.append(None)

    return Response({
        "success": True,
        "data": {"suggestions": suggestions},
    })


def _normalize_bank_desc(description):
    """Normalize a bank description for duplicate detection (pure).

    Casefold + collapse all whitespace runs to a single space.
    """
    return re.sub(r"\s+", " ", str(description or "")).strip().casefold()


@api_view(["POST"])
@permission_classes([RoleWriteAccess])
def bank_statement_confirm(request):
    """Bogfør de godkendte banklinjer.

    Hver linje parkeres på mellemregningskontoen (chart.SUSPENSE) mod
    bankkontoen; når den afstemmes, omposteres det ben til den rigtige konto.
    En bankkonto i fremmed valuta kræver en kurs (exchange_rate pr. linje eller
    for hele filen): beløbene bogføres i DKK og valutabeløbet gemmes.
    """
    data = request.data
    bank_account_id = data.get("bank_account_id")
    txns = data.get("transactions", [])

    if not bank_account_id:
        return Response(
            {"success": False, "message": "bank_account_id is required"},
            status=status.HTTP_400_BAD_REQUEST,
        )
    if not txns:
        return Response(
            {"success": False, "message": "No transactions to create"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    try:
        bank_account = Account.objects.get(id=bank_account_id)
    except Account.DoesNotExist:
        return Response(
            {"success": False, "message": "Bank account not found"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    # Split into mapped (have account) and all (for upload history)
    all_txns = txns
    mapped_txns = [t for t in txns if t.get("account_id")]

    account_ids = [t.get("account_id") for t in mapped_txns]
    accounts_map = {}
    if account_ids:
        accounts_map = {str(a.id): a for a in Account.objects.filter(id__in=account_ids)}
        for aid in account_ids:
            if aid not in accounts_map:
                return Response(
                    {"success": False, "message": f"Account {aid} not found"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

    try:
        suspense_acct = Account.objects.get(code=chart.SUSPENSE)
    except Account.DoesNotExist:
        return Response(
            {"success": False, "message": f"Konto {chart.SUSPENSE} (uafklarede poster) findes ikke"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    # Closed fiscal-year guard: check EVERY row's date before creating anything,
    # so the whole batch is rejected atomically with the offending date named.
    for d in sorted({t.get("date") for t in txns if t.get("date")}):
        err = closed_period_error(d)
        if err:
            return Response(
                {"success": False,
                 "message": f"Batch rejected — transaction dated {d} is in a closed fiscal year. {err}"},
                status=status.HTTP_400_BAD_REQUEST,
            )

    created_by = f"{request.user.first_name} {request.user.last_name}".strip() or request.user.username
    currency = bank_account.currency or chart.BASE_CURRENCY
    default_rate = data.get("exchange_rate")
    if currency != chart.BASE_CURRENCY:
        for t in txns:
            try:
                rate = Decimal(str(t.get("exchange_rate") or default_rate or 0))
            except InvalidOperation:
                rate = Decimal("0")
            if rate <= 0:
                return Response({"success": False, "message":
                                 f"Bankkontoen er i {currency}: angiv kursen (DKK pr. 1 {currency})"},
                                status=status.HTTP_400_BAD_REQUEST)
    journal = journal_for_account(bank_account)
    if journal is None:
        return Response(
            {"success": False, "message": f"Account {bank_account.code} has no bank journal"},
            status=status.HTTP_400_BAD_REQUEST,
        )
    created = 0
    skipped = 0
    skipped_by_ref = 0
    skipped_no_ref = 0

    # Pre-load existing bank references for duplicate detection
    existing_refs = set(
        JournalEntry.objects.filter(source="bank")
        .exclude(reference="")
        .values_list("reference", flat=True)
    )

    # For rows WITHOUT a reference: duplicate = an existing bank-source line on
    # the same bank account with the same date, same amount (same direction) and
    # the same normalized description. Build the key set from the DB once.
    def _txn_key(date_iso, debit, credit, description):
        direction = "in" if credit > 0 else "out"
        amount = credit if credit > 0 else debit
        return (str(date_iso), direction, f"{amount:.2f}", _normalize_bank_desc(description))

    existing_keys = set()
    txn_dates = [t.get("date") for t in txns if t.get("date")]
    if txn_dates:
        existing_bank_lines = JournalEntryLine.objects.filter(
            journal_entry__source="bank",
            account=bank_account,
            journal_entry__date__gte=min(txn_dates),
            journal_entry__date__lte=max(txn_dates),
        ).select_related("journal_entry")
        for jl in existing_bank_lines:
            # On import, money-in is a DEBIT on the bank line and money-out a CREDIT.
            txn_credit = jl.debit or Decimal("0")
            txn_debit = jl.credit or Decimal("0")
            existing_keys.add(_txn_key(
                jl.journal_entry.date.isoformat() if hasattr(jl.journal_entry.date, "isoformat") else jl.journal_entry.date,
                txn_debit, txn_credit, jl.journal_entry.description,
            ))

    with transaction.atomic():
        for txn in txns:
            debit = Decimal(str(txn.get("debit", 0)))
            credit = Decimal(str(txn.get("credit", 0)))
            if debit == 0 and credit == 0:
                continue

            desc = txn.get("description", "Bank transaction")
            ref = txn.get("reference", "")

            # Skip duplicates by reference
            if ref and ref in existing_refs:
                skipped += 1
                skipped_by_ref += 1
                continue

            # No reference: dedup on bank account + date + amount + normalized
            # description — against existing DB entries AND within this batch.
            if not ref:
                key = _txn_key(txn.get("date"), debit, credit, desc)
                if key in existing_keys:
                    skipped += 1
                    skipped_no_ref += 1
                    continue
                existing_keys.add(key)

            entry = JournalEntry.objects.create(
                journal=journal,
                entry_number=_next_entry_number(),
                piece_number=ref,
                date=txn["date"],
                description=desc,
                reference=ref,
                source="bank",
                is_posted=True,
                created_by=created_by,
            )

            # Hver banklinje venter på mellemregningskontoen, til den afstemmes.
            fx = {}
            amount_fc = credit if credit > 0 else debit
            amount = amount_fc
            if currency != chart.BASE_CURRENCY:
                rate = Decimal(str(txn.get("exchange_rate") or default_rate))
                amount = (amount_fc * rate).quantize(Decimal("0.01"))
                fx = {"currency": currency, "exchange_rate": rate}
            sign = 1 if credit > 0 else -1
            if credit > 0:
                # Penge ind → DR bank, CR mellemregning
                bank_dr, bank_cr = amount, Decimal("0")
            else:
                # Penge ud → DR mellemregning, CR bank
                bank_dr, bank_cr = Decimal("0"), amount
            JournalEntryLine.objects.create(
                journal_entry=entry, account=bank_account, debit=bank_dr, credit=bank_cr, description=desc,
                amount_currency=sign * amount_fc if fx else None, **fx,
            )
            JournalEntryLine.objects.create(
                journal_entry=entry, account=suspense_acct, debit=bank_cr, credit=bank_dr, description=desc,
                amount_currency=-sign * amount_fc if fx else None, **fx,
            )

            created += 1

        # Save learned description→account mappings for future auto-map
        for txn in mapped_txns:
            desc = txn.get("description", "")
            acct_id = txn.get("account_id")
            if not desc or not acct_id:
                continue
            desc_key = _extract_description_key(desc)
            if not desc_key:
                continue
            acct = accounts_map.get(acct_id)
            if not acct:
                continue
            # Skip system accounts (not useful as learned mappings)
            if acct.code in chart.SYSTEM_ACCOUNTS:
                continue
            BankDescriptionMapping.objects.update_or_create(
                description_key=desc_key,
                defaults={
                    "account": acct,
                    "example_description": desc[:500],
                },
            )

    # Save upload history record
    dates = [t["date"] for t in all_txns if t.get("date")]
    try:
        BankStatementUpload.objects.create(
            filename=data.get("filename", "bank_statement"),
            bank_account=bank_account,
            date_from=min(dates) if dates else None,
            date_to=max(dates) if dates else None,
            transaction_count=len(all_txns),
            uploaded_by=f"{request.user.first_name} {request.user.last_name}".strip() or request.user.username,
        )
    except Exception:
        pass  # Don't fail the whole request if history save fails

    log_action(request.user, "import", "BankStatement", bank_account.code, {
        "filename": data.get("filename", ""), "journal": journal.code, "created": created, "skipped": skipped,
        "date_from": str(min(dates)) if dates else None, "date_to": str(max(dates)) if dates else None,
    })

    message = f"{created} journal entries created, {skipped} duplicates skipped"
    if skipped:
        message += (
            f" ({skipped_by_ref} by reference, "
            f"{skipped_no_ref} by date/amount/description match)"
        )
    return Response({
        "success": True,
        "message": message,
        "data": {"count": created, "skipped": skipped, "duplicates": skipped},
    }, status=status.HTTP_201_CREATED)


# ─── Google Places API ─────────────────────────────────────────────────────────


@api_view(["GET"])
@permission_classes([RoleWriteAccess])
def places_autocomplete(request):
    """Google Places Autocomplete (New API) — called directly."""
    query = request.query_params.get("q", "").strip()
    if not query or len(query) < 2:
        return Response({"success": True, "data": {"predictions": []}})

    from django.conf import settings
    import requests as http_requests

    api_key = settings.GOOGLE_PLACES_API_KEY
    if not api_key:
        return Response({"success": False, "message": "GOOGLE_PLACES_API_KEY not configured"}, status=500)

    region = request.query_params.get("region", "").strip()
    url = "https://places.googleapis.com/v1/places:autocomplete"
    headers = {
        "Content-Type": "application/json",
        "X-Goog-Api-Key": api_key,
    }
    body = {"input": query, "languageCode": "en"}
    if region:
        body["includedRegionCodes"] = [region]

    try:
        resp = http_requests.post(url, json=body, headers=headers, timeout=5)
        data = resp.json()
        predictions = []
        for s in data.get("suggestions", []):
            p = s.get("placePrediction")
            if p:
                predictions.append({
                    "place_id": p.get("placeId"),
                    "description": p.get("text", {}).get("text", ""),
                })
        return Response({"success": True, "data": {"predictions": predictions}})
    except Exception as e:
        return Response({"success": False, "message": str(e)}, status=500)


@api_view(["GET"])
@permission_classes([RoleWriteAccess])
def places_details(request):
    """Google Places Details (New API) — called directly."""
    place_id = request.query_params.get("place_id", "").strip()
    if not place_id:
        return Response({"success": False, "message": "place_id required"}, status=400)

    from django.conf import settings
    import requests as http_requests

    api_key = settings.GOOGLE_PLACES_API_KEY
    if not api_key:
        return Response({"success": False, "message": "GOOGLE_PLACES_API_KEY not configured"}, status=500)

    url = f"https://places.googleapis.com/v1/places/{place_id}"
    headers = {
        "X-Goog-Api-Key": api_key,
        "X-Goog-FieldMask": "displayName,formattedAddress,internationalPhoneNumber,nationalPhoneNumber,addressComponents,websiteUri",
    }
    try:
        resp = http_requests.get(url, headers=headers, timeout=5)
        data = resp.json()

        city = ""
        country = ""
        postal_code = ""
        state = ""
        for comp in data.get("addressComponents", []):
            types = comp.get("types", [])
            if "locality" in types:
                city = comp.get("longText", "")
            elif "country" in types:
                country = comp.get("longText", "")
            elif "postal_code" in types:
                postal_code = comp.get("longText", "")
            elif "administrative_area_level_1" in types:
                state = comp.get("longText", "")

        result = {
            "name": data.get("displayName", {}).get("text", ""),
            "address": data.get("formattedAddress", ""),
            "phone": data.get("internationalPhoneNumber", "") or data.get("nationalPhoneNumber", ""),
            "website": data.get("websiteUri", ""),
            "city": city,
            "country": country,
            "postal_code": postal_code,
            "state": state,
        }
        return Response({"success": True, "data": result})
    except Exception as e:
        return Response({"success": False, "message": str(e)}, status=500)


@api_view(["GET"])
@permission_classes([RoleWriteAccess])
def bank_statement_history(request):
    """Return list of previous bank statement uploads."""
    uploads = BankStatementUpload.objects.select_related("bank_account").order_by("-uploaded_at")[:100]
    return Response({
        "success": True,
        "data": {
            "uploads": [
                {
                    "id": str(u.id),
                    "filename": u.filename,
                    "bank_account_code": u.bank_account.code,
                    "bank_account_name": u.bank_account.name,
                    "date_from": u.date_from.isoformat() if u.date_from else None,
                    "date_to": u.date_to.isoformat() if u.date_to else None,
                    "transaction_count": u.transaction_count,
                    "uploaded_by": u.uploaded_by,
                    "uploaded_at": u.uploaded_at.isoformat() if u.uploaded_at else None,
                }
                for u in uploads
            ],
        },
    })


# ─── Journal Entries Export (server-side CSV) ────────────────────────────────

@api_view(["GET"])
@permission_classes([RoleWriteAccess])
def journal_entries_export(request):
    """Export journal entries (with lines) as a flat CSV."""
    qs = JournalEntry.objects.prefetch_related("lines__account").all()

    if request.query_params.get("date_from"):
        qs = qs.filter(date__gte=request.query_params["date_from"])
    if request.query_params.get("date_to"):
        qs = qs.filter(date__lte=request.query_params["date_to"])
    if request.query_params.get("source"):
        qs = qs.filter(source=request.query_params["source"])
    if request.query_params.get("is_posted"):
        qs = qs.filter(is_posted=request.query_params["is_posted"].lower() == "true")
    if request.query_params.get("search"):
        q = request.query_params["search"]
        qs = qs.filter(
            Q(entry_number__icontains=q) | Q(description__icontains=q) | Q(reference__icontains=q)
        )

    qs = qs.order_by("-date", "-entry_number")

    response = HttpResponse(content_type="text/csv; charset=utf-8")
    response["Content-Disposition"] = 'attachment; filename="journal_entries.csv"'
    response.write("\ufeff")

    writer = SafeWriter(response)
    writer.writerow([
        "entry_number", "date", "description", "reference", "source", "is_posted",
        "line_account_code", "line_account_name", "line_debit", "line_credit",
        "line_description", "total_debit", "total_credit",
    ])

    for entry in qs:
        lines = entry.lines.select_related("account").all()
        if lines:
            for line in lines:
                writer.writerow([
                    entry.entry_number, entry.date.isoformat(),
                    entry.description, entry.reference, entry.source,
                    "Yes" if entry.is_posted else "No",
                    line.account.code, line.account.name,
                    str(line.debit), str(line.credit), line.description,
                    str(entry.total_debit), str(entry.total_credit),
                ])
        else:
            writer.writerow([
                entry.entry_number, entry.date.isoformat(),
                entry.description, entry.reference, entry.source,
                "Yes" if entry.is_posted else "No",
                "", "", "", "", "",
                str(entry.total_debit), str(entry.total_credit),
            ])

    return response


# ─── Bank Transactions (flat view) ───────────────────────────────────────────

def _bank_txn_queryset(request):
    """Build filtered queryset for bank transaction lines."""
    qs = JournalEntryLine.objects.filter(
        chart.treasury_q("account__code"),
        journal_entry__source="bank",
    ).select_related("journal_entry", "account").order_by(
        "-journal_entry__date", "-journal_entry__entry_number"
    )

    if request.query_params.get("bank_account_id"):
        qs = qs.filter(account_id=request.query_params["bank_account_id"])
    # direction: "out" = money leaving the bank (credit on bank line),
    # "in" = money received (debit on bank line). Absent = both.
    direction = request.query_params.get("direction")
    if direction == "out":
        qs = qs.filter(credit__gt=0)
    elif direction == "in":
        qs = qs.filter(debit__gt=0)
    if request.query_params.get("date_from"):
        qs = qs.filter(journal_entry__date__gte=request.query_params["date_from"])
    if request.query_params.get("date_to"):
        qs = qs.filter(journal_entry__date__lte=request.query_params["date_to"])
    if request.query_params.get("search"):
        q = request.query_params["search"]
        qs = qs.filter(
            Q(journal_entry__entry_number__icontains=q) |
            Q(journal_entry__description__icontains=q) |
            Q(journal_entry__reference__icontains=q)
        )

    # Sorting
    sort_field = request.query_params.get("sort", "date")
    sort_dir = request.query_params.get("sort_dir", "desc")
    allowed_sort = {
        "date": "journal_entry__date",
        "entry_number": "journal_entry__entry_number",
        "description": "journal_entry__description",
        "reference": "journal_entry__reference",
        "bank_account": "account__code",
        "debit": "debit",
        "credit": "credit",
    }
    order_field = allowed_sort.get(sort_field, "journal_entry__date")
    prefix = "-" if sort_dir == "desc" else ""
    qs = qs.order_by(f"{prefix}{order_field}", "-journal_entry__date")

    return qs


@api_view(["GET"])
@permission_classes([RoleWriteAccess])
def bank_transactions_list(request):
    """Flat list of bank-source transactions (one row per bank-side JE line)."""
    qs = _bank_txn_queryset(request)

    # Totaler i DKK (debit/credit er altid DKK).
    agg = qs.order_by().aggregate(total_debit=Sum("debit"), total_credit=Sum("credit"))
    dr, cr = agg["total_debit"] or Decimal("0"), agg["total_credit"] or Decimal("0")
    summaries = [{"currency": chart.BASE_CURRENCY, "total_debit": str(dr), "total_credit": str(cr),
                  "net": str(dr - cr)}]

    total_count = qs.count()

    # Pagination
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
    lines = qs[offset:offset + page_size]

    rows = []
    for line in lines:
        je = line.journal_entry
        rows.append({
            "id": str(line.id),
            "entry_number": je.entry_number,
            "date": je.date.isoformat() if hasattr(je.date, "isoformat") else str(je.date),
            "description": je.description,
            "reference": je.reference,
            "debit": str(line.debit),
            "credit": str(line.credit),
            "currency": line.currency,
            "amount_currency": str(line.amount_currency) if line.amount_currency is not None else None,
            "bank_account_id": str(line.account_id),
            "bank_account_code": line.account.code,
            "bank_account_name": line.account.name,
        })

    # Bank accounts for filter dropdown
    bank_accounts = list(
        chart.treasury_accounts()
        .order_by("code")
        .values("id", "code", "name")
    )
    bank_accounts = [
        {"id": str(a["id"]), "code": a["code"], "name": a["name"]}
        for a in bank_accounts
    ]

    return Response({
        "success": True,
        "data": {
            "transactions": rows,
            "count": total_count,
            "total_count": total_count,
            "page": page,
            "page_size": page_size,
            "summaries": summaries,
            "bank_accounts": bank_accounts,
        },
    })


@api_view(["GET"])
@permission_classes([RoleWriteAccess])
def bank_transactions_export(request):
    """Export bank transactions as CSV with BOM."""
    qs = _bank_txn_queryset(request)

    response = HttpResponse(content_type="text/csv; charset=utf-8")
    response["Content-Disposition"] = 'attachment; filename="bank_transactions.csv"'
    response.write("\ufeff")

    writer = SafeWriter(response)
    writer.writerow(["Date", "Entry Number", "Description", "Reference", "Bank Account", "Debit", "Credit", "Currency"])

    for line in qs:
        je = line.journal_entry
        writer.writerow([
            je.date.isoformat() if hasattr(je.date, "isoformat") else str(je.date),
            je.entry_number,
            je.description,
            je.reference,
            f"{line.account.code} - {line.account.name}",
            str(line.debit),
            str(line.credit),
            line.currency,
        ])

    return response
