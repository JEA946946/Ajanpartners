"""Send og modtag e-fakturaer. Alt kører i kundens skema."""

from datetime import timedelta
from decimal import Decimal

from django.db import transaction
from django.utils import timezone

from integrations.base import AgreementRequired, IntegrationError, setting

from .access_point import get_access_point
from .models import IncomingEInvoice, OutgoingEInvoice
from .parse import ParseError, parse_ubl, suggest_bill
from .ubl import EInvoiceError, build_credit_note, build_invoice, customer_party


def default_format():
    fmt = (setting("EINVOICE_DEFAULT_FORMAT", "peppol") or "peppol").lower()
    return fmt if fmt in ("peppol", "oioubl") else "peppol"


def _user_name(user):
    if user is None:
        return "system"
    return f"{user.first_name} {user.last_name}".strip() or user.username


def generate(document, document_type="invoice", fmt=None, user=None):
    """Dan XML'en og gem den som OutgoingEInvoice (status generated)."""
    fmt = fmt or default_format()
    if document_type == "invoice":
        if document.status in ("draft", "cancelled"):
            raise EInvoiceError("Kun udstedte fakturaer kan sendes som e-faktura (ikke kladder eller annullerede).")
        xml, number = build_invoice(document, fmt), document.invoice_number
    elif document_type == "credit_note":
        xml, number = build_credit_note(document, fmt), document.credit_note_number
    else:
        raise EInvoiceError(f"Ukendt dokumenttype: {document_type}")
    party = customer_party(document.customer)
    scheme, endpoint = party.endpoint
    return OutgoingEInvoice.objects.create(
        document_type=document_type, format=fmt,
        invoice=document if document_type == "invoice" else None,
        credit_note=document if document_type == "credit_note" else None,
        document_number=number, receiver_scheme=scheme or "", receiver_endpoint=endpoint or "",
        receiver_name=party.name, xml=xml, created_by=_user_name(user))


def send(outgoing, user=None):
    """Send gennem access point'et. Fejl gemmes på dokumentet og rejses videre."""
    from core.audit import log_action

    ap = get_access_point()
    outgoing.access_point = ap.name
    try:
        result = ap.send(outgoing)
    except (AgreementRequired, IntegrationError) as e:
        outgoing.status, outgoing.error = "failed", str(e)
        outgoing.save()
        raise
    outgoing.access_point_id = result.message_id
    outgoing.status = result.status if not result.error else "failed"
    outgoing.error = result.error
    outgoing.sent_at = timezone.now()
    outgoing.save()
    log_action(user, "einvoice", "OutgoingEInvoice", outgoing.id, {
        "document_type": outgoing.document_type, "number": outgoing.document_number, "format": outgoing.format,
        "receiver": f"{outgoing.receiver_scheme}:{outgoing.receiver_endpoint}", "access_point": ap.name,
        "message_id": outgoing.access_point_id, "sha256": outgoing.sha256, "status": outgoing.status,
    })
    return outgoing


def receive(xml, access_point="", access_point_id=""):
    """Læg et modtaget dokument i indbakken. Samme XML to gange giver samme post."""
    if isinstance(xml, bytes):
        xml = xml.decode("utf-8-sig")
    from .models import sha256 as digest

    existing = IncomingEInvoice.objects.filter(sha256=digest(xml)).first()
    if existing:
        return existing
    incoming = IncomingEInvoice(xml=xml, access_point=access_point, access_point_id=access_point_id)
    try:
        parsed = parse_ubl(xml)
    except ParseError as e:
        incoming.status, incoming.error = "failed", str(e)
        incoming.save()
        return incoming
    sup = parsed.get("supplier") or {}
    incoming.document_type = parsed["document_type"]
    incoming.format = parsed["format"]
    incoming.document_number = parsed["number"][:100]
    incoming.issue_date = parsed["issue_date"]
    incoming.due_date = parsed["due_date"]
    incoming.currency = parsed["currency"][:3]
    incoming.total = Decimal(parsed["payable"] or "0")
    incoming.tax_amount = Decimal(parsed["tax_total"] or "0")
    incoming.sender_scheme = sup.get("endpoint_scheme", "")[:10]
    incoming.sender_endpoint = sup.get("endpoint_id", "")[:50]
    incoming.sender_name = sup.get("name", "")[:255]
    incoming.parsed = {**parsed, "suggestion": suggest_bill(parsed)}
    incoming.save()
    return incoming


def _supplier_for(incoming, supplier_id, create):
    from journals.numbering import next_number
    from purchases.models import Supplier

    if supplier_id:
        supplier = Supplier.objects.filter(id=supplier_id).first()
        if supplier is None:
            raise EInvoiceError("Leverandøren findes ikke.")
        return supplier
    suggested = (incoming.parsed.get("suggestion") or {}).get("supplier_id")
    if suggested:
        supplier = Supplier.objects.filter(id=suggested).first()
        if supplier:
            return supplier
    if not create:
        raise EInvoiceError("Leverandøren blev ikke fundet. Vælg en leverandør eller opret den.")
    sup = incoming.parsed.get("supplier") or {}
    address = "\n".join(x for x in (sup.get("street"), " ".join(
        x for x in (sup.get("zip_code"), sup.get("city")) if x)) if x)
    return Supplier.objects.create(
        code=next_number(Supplier, "code", "SUP"), name=sup.get("name") or "Ukendt leverandør",
        email=sup.get("email") or "", address=address, tax_id=sup.get("cvr") or sup.get("vat_id") or "",
        currency=incoming.currency or "DKK", notes="Oprettet fra e-faktura.")


def attach_xml(incoming, bill, user=None):
    """Gem den modtagne XML uændret som bilag (core.Document) på regningen.

    SHA-256 og størrelse beregnes som ved upload (core.views.documents_list_create), så
    bilaget kan kontrolleres mod e-fakturaens hash i hele opbevaringsperioden.
    core.uploads.validate_upload bruges ikke: den tillader ikke .xml, og filen kommer
    fra access point'et, ikke fra en bruger.
    """
    import hashlib
    import re

    from django.core.files.base import ContentFile

    from core.models import Document

    content = incoming.xml.encode("utf-8")
    safe = re.sub(r"[^A-Za-z0-9._-]+", "_", incoming.document_number or str(incoming.id))[:80]
    name = f"efaktura_{safe}.xml"
    return Document.objects.create(
        file=ContentFile(content, name=name), filename=name,
        description=f"E-faktura fra {incoming.sender_name} ({incoming.sender_scheme}:{incoming.sender_endpoint})"[:500],
        piece_number=(incoming.document_number or "")[:100], sha256=hashlib.sha256(content).hexdigest(),
        size=len(content), bill=bill, uploaded_by=_user_name(user))


def to_bill(incoming, user=None, supplier_id=None, create_supplier=True, lines=None):
    """Opret en regning (kladde) ud fra en modtaget e-faktura.

    ``lines`` kan overskrive forslaget: [{"account_id": …, "tax_code_id": …}, …] i
    samme rækkefølge som e-fakturaens linjer.
    """
    from core.audit import log_action
    from core.models import TaxCode
    from accounts.models import Account
    from journals.numbering import next_number
    from purchases.models import Bill, BillLine

    if incoming.status == "converted" and incoming.bill_id:
        raise EInvoiceError("E-fakturaen er allerede oprettet som regning.")
    if incoming.status == "failed":
        raise EInvoiceError("E-fakturaen kunne ikke læses og kan ikke oprettes som regning.")
    if incoming.document_type != "invoice":
        raise EInvoiceError("Kreditnotaer fra leverandører modregnes manuelt i den oprindelige regning.")
    if not incoming.issue_date:
        raise EInvoiceError("E-fakturaen mangler en fakturadato.")
    suggestion = incoming.parsed.get("suggestion") or {}
    proposed = suggestion.get("lines") or incoming.parsed.get("lines") or []
    overrides = lines or []
    with transaction.atomic():
        supplier = _supplier_for(incoming, supplier_id, create_supplier)
        issue = incoming.issue_date
        if isinstance(issue, str):
            from datetime import date
            issue = date.fromisoformat(issue)
        due = incoming.due_date or (issue + timedelta(days=getattr(supplier, "payment_terms", 30) or 30))
        if isinstance(due, str):
            from datetime import date
            due = date.fromisoformat(due)
        extra = {}
        field_names = {f.name for f in Bill._meta.get_fields()}
        if "vat_quarter" in field_names:  # ældre udgave af purchases-modellen
            extra = {"vat_quarter": (issue.month - 1) // 3 + 1, "vat_year": issue.year}
        bill = Bill.objects.create(**extra,
            bill_number=next_number(Bill, "bill_number", "BILL"), supplier=supplier, date=issue, due_date=due,
            status="draft", currency=incoming.currency or "DKK",
            reference=incoming.document_number[:200],
            notes=f"E-faktura fra {incoming.sender_name} ({incoming.sender_scheme}:{incoming.sender_endpoint}).",
            created_by=_user_name(user))
        subtotal = Decimal("0")
        for i, l in enumerate(proposed):
            o = overrides[i] if i < len(overrides) else {}
            account_id = o.get("account_id") or l.get("account_id") or (
                str(supplier.default_account_id) if getattr(supplier, "default_account_id", None) else None)
            tax_code_id = o.get("tax_code_id") or l.get("tax_code_id")
            line = BillLine.objects.create(
                bill=bill, description=(l.get("description") or "E-fakturalinje")[:500],
                quantity=Decimal(l.get("quantity") or "1"), unit_price=Decimal(l.get("unit_price") or "0"),
                account=Account.objects.filter(id=account_id).first() if account_id else None,
                tax_code=TaxCode.objects.filter(id=tax_code_id).first() if tax_code_id else None)
            subtotal += line.amount
        bill.subtotal = subtotal
        bill.tax_amount = incoming.tax_amount
        bill.total = subtotal + incoming.tax_amount
        bill.save(update_fields=["subtotal", "tax_amount", "total"])
        document = attach_xml(incoming, bill, user)
        incoming.bill = bill
        incoming.status = "converted"
        incoming.converted_by = _user_name(user)
        incoming.converted_at = timezone.now()
        incoming.save()
        log_action(user, "create", "Bill", bill.id, {
            "source": "einvoice", "incoming_id": str(incoming.id), "sha256": incoming.sha256,
            "supplier": supplier.name, "reference": bill.reference, "total": str(bill.total),
            "document_id": str(document.id),
        })
    return bill
