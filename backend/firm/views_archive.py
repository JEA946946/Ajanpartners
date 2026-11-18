"""Admin-portalen: materialelister (PBC) til kunden og dokumentarkiv pr. kunde.

/api/firm/engagements/<id>/pbc                 GET (punkter + fremdrift) / POST {list_name, due_date, items}
/api/firm/engagements/<id>/pbc/preview         GET ?template=<id> – punkter fra en verificeret skabelon
/api/firm/clients/<slug>/documents             GET (?engagement) / POST (multipart: file, kind, title, …)
/api/firm/documents/<id>                       GET (download) / PUT {visible_to_client, signed_on, signed_note,
                                               retain_until, note, engagement}
/api/firm/templates/<id>/archive               POST {client, year, values, text, engagement, kind, title}

Kundens side (X-Client): /api/v1/firm-documents og /api/v1/firm-documents/<id> (kun dokumenter, der er delt).

Materialelisten er almindelige opgaver (FirmTask, kind=bilag_mangler, synlige for kunden) med samme opdrag og
listenavn, så kunden besvarer dem i sin indbakke. Punkterne kommer fra de verificerede skabeloner.
Arkivet sletter aldrig: en ny fil med samme type og titel bliver en ny version.
"""

import hashlib
import os
import re
from datetime import datetime

from django.core.files.base import ContentFile
from django.db import transaction
from django.db.models import Max
from django.http import FileResponse
from django.utils import timezone
from rest_framework.decorators import api_view, parser_classes, permission_classes
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from core.permissions import IsFirmStaff
from tenancy.access import staff_of

from . import templating
from .models import ClientDocument, Engagement, FirmTask
from .views import _client_or_404, _clients_for, _err, _log, _ok, _user_name
from .views_engagements import render_items

MAX_UPLOAD = 25 * 1024 * 1024
PBC_TEMPLATES = ("materialeliste-aarsafslutning", "materialeliste-personlig-skat")


def _date(v):
    try:
        return datetime.strptime(str(v)[:10], "%Y-%m-%d").date() if v else None
    except ValueError:
        return None


def _engagement(request, pk):
    staff = staff_of(request.user)
    return Engagement.objects.filter(pk=pk, client__in=_clients_for(staff)).select_related("client").first()


# ─── Materialeliste (PBC) ─────────────────────────────────────────────────────

def _pbc_dict(e):
    tasks = list(FirmTask.objects.filter(engagement=e).select_related("client", "assigned_to", "created_by")
                 .order_by("list_name", "position", "created_at"))
    today = timezone.localdate()
    lists = {}
    for t in tasks:
        lst = lists.setdefault(t.list_name or "Øvrige", {"name": t.list_name or "Øvrige", "items": [], "done": 0,
                                                         "answered": 0, "overdue": 0})
        lst["items"].append({"id": str(t.id), "title": t.title, "description": t.description, "status": t.status,
                             "status_label": t.get_status_display(),
                             "due_date": t.due_date.isoformat() if t.due_date else None})
        if t.status == "closed":
            lst["done"] += 1
        elif t.status == "answered":
            lst["answered"] += 1
        if t.status != "closed" and t.due_date and t.due_date < today:
            lst["overdue"] += 1
    templates = [templating.get(tid) for tid in PBC_TEMPLATES]
    return {"lists": list(lists.values()),
            "templates": [{"id": t["id"], "title": t["title"]} for t in templates if t]}


@api_view(["GET"])
@permission_classes([IsFirmStaff])
def pbc_preview(request, pk):
    e = _engagement(request, pk)
    if e is None:
        return _err("Opdraget findes ikke", 404)
    tid = request.query_params.get("template") or PBC_TEMPLATES[0]
    t, items, _vals, msg = render_items(request, e, tid)
    if msg:
        return _err(msg)
    return _ok({"template": {"id": t["id"], "title": t["title"]},
                "items": [{"section": i["section"], "text": i["text"]} for i in items]})


@api_view(["GET", "POST"])
@permission_classes([IsFirmStaff])
def engagement_pbc(request, pk):
    e = _engagement(request, pk)
    if e is None:
        return _err("Opdraget findes ikke", 404)
    if request.method == "GET":
        return _ok(_pbc_dict(e))
    d = request.data
    name = str(d.get("list_name") or "").strip()[:255]
    items = [i for i in (d.get("items") or []) if isinstance(i, dict) and str(i.get("title") or "").strip()]
    if not name:
        return _err("Giv listen et navn")
    if not items:
        return _err("Vælg mindst ét punkt")
    if len(items) > 300:
        return _err("Højst 300 punkter pr. liste")
    if e.client.status == "archived":
        return _err("Kunden er arkiveret.")
    due = _date(d.get("due_date"))
    start = (FirmTask.objects.filter(engagement=e, list_name=name).aggregate(m=Max("position"))["m"] or 0) + 1
    with transaction.atomic():
        for n, i in enumerate(items):
            title = re.sub(r"\*\*(.+?)\*\*|\*(.+?)\*", lambda m: m.group(1) or m.group(2), str(i["title"]).strip())
            FirmTask.objects.create(
                client=e.client, engagement=e, list_name=name, position=start + n, kind="bilag_mangler",
                title=title[:255], description=str(i.get("section") or i.get("description") or "")[:2000],
                visible_to_client=True, due_date=due, assigned_to=e.manager or request.user, created_by=request.user)
    _log(request, "pbc_sent", e.client, engagement=str(e.id), list=name, items=len(items))
    return _ok(_pbc_dict(e), 201)


# ─── Dokumentarkiv ────────────────────────────────────────────────────────────

def document_dict(doc):
    return {
        "id": str(doc.id), "client": doc.client.slug, "engagement": str(doc.engagement_id) if doc.engagement_id else None,
        "engagement_title": (doc.engagement.title or doc.engagement.get_kind_display()) if doc.engagement_id else None,
        "kind": doc.kind, "kind_label": doc.get_kind_display(), "title": doc.title, "version": doc.version,
        "filename": doc.filename, "size": doc.size, "sha256": doc.sha256, "source": doc.source,
        "visible_to_client": doc.visible_to_client, "signed_on": doc.signed_on.isoformat() if doc.signed_on else None,
        "signed_note": doc.signed_note, "retain_until": doc.retain_until.isoformat() if doc.retain_until else None,
        "note": doc.note, "created_by": _user_name(doc.created_by), "created_at": doc.created_at.isoformat(),
    }


def store_document(*, client, kind, title, filename, content, user, engagement=None, source="upload",
                   visible_to_client=False, retain_until=None, note=""):
    """Gem en fil i arkivet som næste version af (kunde, type, titel)."""
    with transaction.atomic():
        last = ClientDocument.objects.select_for_update().filter(client=client, kind=kind, title=title) \
            .aggregate(m=Max("version"))["m"] or 0
        doc = ClientDocument(client=client, engagement=engagement, kind=kind, title=title, version=last + 1,
                             filename=filename, size=len(content), sha256=hashlib.sha256(content).hexdigest(),
                             source=source, visible_to_client=visible_to_client, retain_until=retain_until,
                             note=note, created_by=user)
        doc.file.save(filename, ContentFile(content), save=False)
        doc.save()
    return doc


def _bool(v):
    return str(v).lower() in ("1", "true", "yes", "on")


def _engagement_for(client, eid):
    if not eid:
        return None, None
    e = Engagement.objects.filter(pk=eid, client=client).first()
    return e, (None if e else "Opdraget hører ikke til kunden")


@api_view(["GET", "POST"])
@permission_classes([IsFirmStaff])
@parser_classes([MultiPartParser, FormParser, JSONParser])
def client_documents(request, slug):
    client, _staff = _client_or_404(request, slug)
    if client is None:
        return _err("Kunden findes ikke", 404)
    if request.method == "GET":
        qs = ClientDocument.objects.filter(client=client).select_related("client", "engagement", "created_by")
        if request.query_params.get("engagement"):
            qs = qs.filter(engagement_id=request.query_params["engagement"])
        return _ok({"documents": [document_dict(d) for d in qs],
                    "kinds": [{"value": k, "label": v} for k, v in ClientDocument.KINDS]})
    f = request.FILES.get("file")
    d = request.data
    if f is None:
        return _err("Vælg en fil")
    if f.size > MAX_UPLOAD:
        return _err("Filen må højst fylde 25 MB")
    if d.get("kind") not in dict(ClientDocument.KINDS):
        return _err("Vælg dokumenttype")
    title = str(d.get("title") or "").strip()[:255] or os.path.splitext(f.name)[0][:255]
    eng, msg = _engagement_for(client, d.get("engagement"))
    if msg:
        return _err(msg)
    doc = store_document(client=client, kind=d["kind"], title=title, filename=os.path.basename(f.name)[:200],
                         content=f.read(), user=request.user, engagement=eng,
                         visible_to_client=_bool(d.get("visible_to_client")), retain_until=_date(d.get("retain_until")),
                         note=str(d.get("note") or "").strip())
    _log(request, "document_archived", client, document=str(doc.id), kind=doc.kind, version=doc.version)
    return _ok({"document": document_dict(doc)}, 201)


@api_view(["GET", "PUT"])
@permission_classes([IsFirmStaff])
def document_detail(request, pk):
    staff = staff_of(request.user)
    doc = ClientDocument.objects.filter(pk=pk, client__in=_clients_for(staff)).select_related(
        "client", "engagement", "created_by").first()
    if doc is None:
        return _err("Dokumentet findes ikke", 404)
    if request.method == "GET":
        _log(request, "document_downloaded", doc.client, document=str(doc.id))
        return FileResponse(doc.file.open("rb"), as_attachment=True, filename=doc.filename)
    d = request.data
    # Filen, typen og titlen kan ikke ændres (ny fil = ny version). Kun oplysninger om dokumentet.
    if "visible_to_client" in d:
        doc.visible_to_client = bool(d["visible_to_client"])
    if "signed_on" in d:
        doc.signed_on = _date(d["signed_on"])
    for f in ("signed_note", "note"):
        if f in d:
            setattr(doc, f, str(d[f] or "").strip()[:255 if f == "signed_note" else 4000])
    if "retain_until" in d:
        doc.retain_until = _date(d["retain_until"])
    if "engagement" in d:
        eng, msg = _engagement_for(doc.client, d["engagement"])
        if msg:
            return _err(msg)
        doc.engagement = eng
    doc.save()
    _log(request, "document_updated", doc.client, document=str(doc.id), visible=doc.visible_to_client)
    return _ok({"document": document_dict(doc)})


@api_view(["POST"])
@permission_classes([IsFirmStaff])
def template_archive(request, template_id):
    """Gem den flettede (evt. redigerede) skabelon som Word-fil i kundens arkiv."""
    from firm.docx_export import markdown_to_docx
    from tenancy.models import Firm

    from .views_templates import _prepare, _values

    template, client, ctx, year, _years, error = _prepare(request, template_id)
    if error:
        return error
    if client is None:
        return _err("Vælg en kunde")
    d = request.data
    kind = d.get("kind") or "andet"
    if kind not in dict(ClientDocument.KINDS):
        return _err("Ugyldig dokumenttype")
    eng, msg = _engagement_for(client, d.get("engagement"))
    if msg:
        return _err(msg)
    text = d.get("text")
    if not isinstance(text, str) or not text.strip():
        text, _ = templating.render(template, ctx, _values(request))
    firm = Firm.current()
    data = markdown_to_docx(text, title=template["title"], firm_name=firm.name if firm else "")
    title = str(d.get("title") or "").strip()[:255] or template["title"]
    year_part = f" {templating.year_label(year['start'], year['end'])}" if year else ""
    safe = re.sub(r'[\\/:*?"<>|]+', "-", f"{template['title']}{year_part}")[:150]
    doc = store_document(client=client, kind=kind, title=title, filename=f"{safe}.docx", content=data,
                         user=request.user, engagement=eng, source=f"skabelon:{template['id']}")
    _log(request, "document_archived", client, document=str(doc.id), template=template["id"], version=doc.version)
    return _ok({"document": document_dict(doc)}, 201)


# ─── Kundens side ─────────────────────────────────────────────────────────────

def _client_docs(request):
    if getattr(request, "tenant", None) is None or getattr(request, "client_access", None) is None:
        return None
    return ClientDocument.objects.filter(client=request.tenant, visible_to_client=True).select_related(
        "client", "engagement", "created_by")


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def client_firm_documents(request):
    qs = _client_docs(request)
    if qs is None:
        return Response({"success": False, "message": "Vælg en kunde."}, status=400)
    return Response({"success": True, "data": {"documents": [
        {k: v for k, v in document_dict(d).items() if k not in ("note", "created_by", "source")} for d in qs]}})


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def client_firm_document(request, pk):
    qs = _client_docs(request)
    doc = qs.filter(pk=pk).first() if qs is not None else None
    if doc is None:
        return Response({"success": False, "message": "Dokumentet findes ikke"}, status=404)
    return FileResponse(doc.file.open("rb"), as_attachment=True, filename=doc.filename)
