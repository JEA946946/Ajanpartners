"""Skabeloner i admin-portalen: liste, fletning med en kundes oplysninger og download som Word."""

import re

from django.http import HttpResponse
from rest_framework.decorators import api_view, permission_classes

from core.permissions import IsFirmStaff
from firm import templating
from firm.docx_export import markdown_to_docx
from firm.views import _client_or_404, _err, _log, _ok
from tenancy.access import active_grant, staff_of
from tenancy.models import Firm


def _meta(t):
    return {k: t[k] for k in ("id", "category", "title", "description", "kind", "references", "legal_forms",
                              "industry_aware")} | {"kind_label": templating.KINDS.get(t["kind"], t["kind"])}


@api_view(["GET"])
@permission_classes([IsFirmStaff])
def templates(request):
    items, errors = templating.load_all()
    staff = staff_of(request.user)
    return _ok({
        "categories": [{"id": c, "label": label} for c, label in templating.CATEGORIES],
        "templates": [_meta(t) for t in items],
        "errors": errors if staff and staff.role == "partner" else [],
    })


def _prepare(request, template_id):
    """(skabelon, kunde, kontekst, år, år-liste, fejl-svar)."""
    template = templating.get(template_id)
    if not template:
        return None, None, None, None, [], _err("Skabelonen findes ikke", 404)
    data = request.data if request.method == "POST" else request.query_params
    staff = staff_of(request.user)
    client, year, years, figures = None, None, [], False
    slug = data.get("client")
    if slug:
        client, staff = _client_or_404(request, slug)
        if not client:
            return template, None, None, None, [], _err("Kunden findes ikke", 404)
        years = templating.fiscal_years(client)
        wanted = str(data.get("year") or "")
        year = next((y for y in years if y["id"] == wanted), None) or templating.default_year(years)
        # Tal fra kundens bøger kræver aktiv adgang; stamdata gør ikke.
        figures = active_grant(client, staff) is not None
    firm = Firm.current()
    ctx = templating.build_context(firm, client, request.user, staff, year, with_figures=figures)
    return template, client, ctx, year, years, None


def _values(request):
    v = request.data.get("values") or {}
    return {str(k): ("" if val is None else val) for k, val in v.items()} if isinstance(v, dict) else {}


@api_view(["POST"])
@permission_classes([IsFirmStaff])
def template_render(request, template_id):
    """{client?, year?, values?, final?} → flettet tekst. `final` (ved download/udskrift) logges."""
    template, client, ctx, year, years, error = _prepare(request, template_id)
    if error:
        return error
    try:
        text, values = templating.render(template, ctx, _values(request))
    except ValueError as e:
        return _err(str(e), 500)
    if client and request.data.get("final"):
        _log(request, "template_render", client, template=template["id"], year=year["id"] if year else None)
    applicable = not template["legal_forms"] or not client or client.legal_form in template["legal_forms"]
    b = ctx["branche"]
    return _ok({
        "template": _meta(template) | {"fields": template["fields"]},
        "text": text,
        "values": values,
        "applicable": applicable,
        "missing": len(re.findall(re.escape(str(templating.MISSING)), text)),
        "client": {
            "slug": client.slug, "name": client.name, "legal_form": client.get_legal_form_display(),
            "industry_code": str(ctx["kunde"]["branchekode"]) if ctx["kunde"]["branchekode"] else "",
            "industry_title": str(ctx["kunde"]["branchetekst"]) if ctx["kunde"]["branchetekst"] else "",
            "industry_groups": b.get("grupper", []), "industry_label": b.get("navn") or "",
            "aml_risk": b.get("hvidvask_risiko"),
            "figures": bool(ctx["regnskab"].get("omsaetning")) if year else False,
        } if client else None,
        "firm_missing": [label for key, label in (("cvr", "CVR-nr."), ("adresse", "adresse"), ("email", "e-mail"),
                                                  ("telefon", "telefon")) if not ctx["firma"][key]],
        "client_missing": [label for key, label in (("cvr", "CVR-nr."), ("adresse", "adresse"), ("branchekode", "branchekode"))
                           if not ctx["kunde"][key]] if client else [],
        "years": [{"id": y["id"], "label": templating.year_label(y["start"], y["end"]),
                   "start": y["start"].isoformat(), "end": y["end"].isoformat()} for y in years],
        "year": year["id"] if year else None,
    })


@api_view(["POST"])
@permission_classes([IsFirmStaff])
def template_docx(request, template_id):
    """Word-fil af den flettede (evt. redigerede) tekst."""
    template, client, ctx, year, _years, error = _prepare(request, template_id)
    if error:
        return error
    text = request.data.get("text")
    if not isinstance(text, str) or not text.strip():
        text, _ = templating.render(template, ctx, _values(request))
    if client:
        _log(request, "template_download", client, template=template["id"], year=year["id"] if year else None)
    firm = Firm.current()
    data = markdown_to_docx(text, title=template["title"], firm_name=firm.name if firm else "")
    name = template["title"] + (f" – {client.name}" if client else "")
    safe = re.sub(r'[\\/:*?"<>|]+', "-", name)[:120]
    resp = HttpResponse(data, content_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document")
    resp["Content-Disposition"] = f"attachment; filename*=UTF-8''{_quote(safe)}.docx"
    return resp


def _quote(s):
    from urllib.parse import quote
    return quote(s)


