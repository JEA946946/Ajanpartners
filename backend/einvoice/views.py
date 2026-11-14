"""E-faktura-endpoints (/api/v1/einvoice/..., kundens skema).

einvoice/send/...   kræver funktionen einvoice_send
einvoice/inbox/...  kræver funktionen einvoice_receive
(se tenancy.features.FEATURE_PATHS)
"""

from django.http import HttpResponse
from rest_framework.decorators import api_view, parser_classes, permission_classes
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.response import Response

from core.permissions import RoleWriteAccess
from integrations.base import AgreementRequired, IntegrationError

from . import services
from .models import IncomingEInvoice, OutgoingEInvoice
from .ubl import EInvoiceError


def _ok(data=None, code=200, message=None):
    body = {"success": True, "data": data if data is not None else {}}
    if message:
        body["message"] = message
    return Response(body, status=code)


def _err(message, code=400, error_code=None):
    body = {"success": False, "message": message}
    if error_code:
        body["code"] = error_code
    return Response(body, status=code)


def _out_dict(o, xml=False):
    d = {
        "id": str(o.id), "document_type": o.document_type, "format": o.format,
        "invoice_id": str(o.invoice_id) if o.invoice_id else None,
        "credit_note_id": str(o.credit_note_id) if o.credit_note_id else None,
        "document_number": o.document_number, "receiver": f"{o.receiver_scheme}:{o.receiver_endpoint}",
        "receiver_name": o.receiver_name, "status": o.status, "status_display": o.get_status_display(),
        "access_point": o.access_point, "access_point_id": o.access_point_id, "error": o.error,
        "sha256": o.sha256, "sent_at": o.sent_at.isoformat() if o.sent_at else None,
        "created_at": o.created_at.isoformat(), "created_by": o.created_by,
    }
    if xml:
        d["xml"] = o.xml
    return d


def _in_dict(i, full=False):
    d = {
        "id": str(i.id), "document_type": i.document_type, "format": i.format,
        "document_number": i.document_number, "issue_date": i.issue_date.isoformat() if i.issue_date else None,
        "due_date": i.due_date.isoformat() if i.due_date else None, "currency": i.currency,
        "total": str(i.total), "tax_amount": str(i.tax_amount), "sender_name": i.sender_name,
        "sender": f"{i.sender_scheme}:{i.sender_endpoint}" if i.sender_endpoint else "",
        "status": i.status, "status_display": i.get_status_display(), "error": i.error,
        "bill_id": str(i.bill_id) if i.bill_id else None, "access_point": i.access_point,
        "received_at": i.received_at.isoformat(), "sha256": i.sha256,
        "supplier_found": bool((i.parsed.get("suggestion") or {}).get("supplier_found")),
    }
    if full:
        d["parsed"] = i.parsed
        d["xml"] = i.xml
    return d


@api_view(["GET"])
@permission_classes([RoleWriteAccess])
def outgoing_list(request):
    qs = OutgoingEInvoice.objects.all()
    if request.query_params.get("invoice_id"):
        qs = qs.filter(invoice_id=request.query_params["invoice_id"])
    if request.query_params.get("credit_note_id"):
        qs = qs.filter(credit_note_id=request.query_params["credit_note_id"])
    return _ok({"documents": [_out_dict(o) for o in qs[:200]]})


@api_view(["POST"])
@permission_classes([RoleWriteAccess])
def send_document(request, pk):
    """Send en faktura (eller kreditnota med document_type=credit_note) som e-faktura."""
    from sales.models import CreditNote, Invoice

    document_type = request.data.get("document_type") or request.query_params.get("document_type") or "invoice"
    fmt = request.data.get("format") or None
    model = Invoice if document_type == "invoice" else CreditNote if document_type == "credit_note" else None
    if model is None:
        return _err("document_type skal være invoice eller credit_note.")
    document = model.objects.select_related("customer").filter(pk=pk).first()
    if document is None:
        return _err("Dokumentet findes ikke.", 404)
    if not request.data.get("resend") and OutgoingEInvoice.objects.filter(
            **{document_type: document}, status__in=("sent", "delivered")).exists():
        return _err("Dokumentet er allerede sendt som e-faktura. Send igen med resend=true.", 409,
                    "already_sent")
    try:
        outgoing = services.generate(document, document_type, fmt, request.user)
    except EInvoiceError as e:
        return _err(str(e))
    try:
        services.send(outgoing, request.user)
    except AgreementRequired as e:
        return Response({"success": False, "message": str(e), "code": "agreement_required",
                         "data": _out_dict(outgoing)}, status=501)
    except IntegrationError as e:
        return Response({"success": False, "message": str(e), "data": _out_dict(outgoing)}, status=502)
    return _ok(_out_dict(outgoing), 201, message="E-fakturaen er sendt.")


@api_view(["GET"])
@permission_classes([RoleWriteAccess])
def outgoing_xml(request, pk):
    o = OutgoingEInvoice.objects.filter(pk=pk).first()
    if o is None:
        return _err("Findes ikke.", 404)
    resp = HttpResponse(o.xml, content_type="application/xml; charset=utf-8")
    resp["Content-Disposition"] = f'attachment; filename="{o.document_number or o.id}.xml"'
    return resp


@api_view(["GET", "POST"])
@permission_classes([RoleWriteAccess])
@parser_classes([JSONParser, MultiPartParser, FormParser])
def inbox(request):
    """GET: indbakken. POST: læg en UBL-fil i indbakken manuelt (fil eller xml-felt)."""
    if request.method == "GET":
        qs = IncomingEInvoice.objects.all()
        if request.query_params.get("status"):
            qs = qs.filter(status=request.query_params["status"])
        return _ok({"documents": [_in_dict(i) for i in qs[:500]],
                    "new_count": IncomingEInvoice.objects.filter(status="new").count()})
    uploaded = request.FILES.get("file")
    xml = uploaded.read() if uploaded else (request.data.get("xml") or "")
    if not xml:
        return _err("Vedhæft en UBL-fil (file) eller send XML i feltet xml.")
    if len(xml) > 10 * 1024 * 1024:
        return _err("Filen er for stor (maks. 10 MB).")
    incoming = services.receive(xml, access_point="upload")
    if incoming.status == "failed":
        return _err(incoming.error)
    return _ok(_in_dict(incoming, full=True), 201)


@api_view(["GET", "PATCH"])
@permission_classes([RoleWriteAccess])
def inbox_detail(request, pk):
    i = IncomingEInvoice.objects.filter(pk=pk).first()
    if i is None:
        return _err("Findes ikke.", 404)
    if request.method == "PATCH":
        if request.data.get("status") == "rejected" and i.status == "new":
            i.status = "rejected"
            i.save(update_fields=["status"])
        else:
            return _err("Kun en ny e-faktura kan afvises.")
    return _ok(_in_dict(i, full=True))


@api_view(["POST"])
@permission_classes([RoleWriteAccess])
def inbox_to_bill(request, pk):
    i = IncomingEInvoice.objects.filter(pk=pk).first()
    if i is None:
        return _err("Findes ikke.", 404)
    try:
        bill = services.to_bill(i, request.user, supplier_id=request.data.get("supplier_id"),
                                create_supplier=request.data.get("create_supplier", True) not in (False, "false"),
                                lines=request.data.get("lines"))
    except EInvoiceError as e:
        return _err(str(e))
    return _ok({"bill_id": str(bill.id), "bill_number": bill.bill_number, "incoming": _in_dict(i)}, 201,
               message=f"Regningen {bill.bill_number} er oprettet som kladde.")
