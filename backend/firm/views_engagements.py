"""Admin-portalen: opdrag, tjeklister, sign-off og kvalitetslog.

/api/firm/engagements                         GET (filtre) / POST
/api/firm/engagements/meta                    opdragstyper, foreslåede tjeklister, opdragsbreve, tjeklisteskabeloner
/api/firm/engagements/<id>                    GET / PUT
/api/firm/engagements/<id>/checklists         POST {template_id, values}
/api/firm/checklist-runs/<id>/items/<item>    PUT {status, note}
/api/firm/engagements/<id>/signoff            POST {step, note}
/api/firm/engagements/<id>/reopen             POST {note} (partner)
/api/firm/quality-log                         GET / POST
/api/firm/quality-log/<id>                    PUT {follow_up, close}

Tjeklistepunkterne trækkes ud af de verificerede skabeloner (firm/doc_templates) – linjer med "- [ ]" –
flettet for kunden og regnskabsåret, så branche- og klasseafhængige punkter kommer med.
"""

import hashlib
import json
import re
from datetime import datetime
from decimal import Decimal, InvalidOperation

from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework.decorators import api_view, permission_classes

from core.permissions import IsFirmStaff
from tenancy.access import active_grant, staff_of
from tenancy.models import Firm

from . import templating
from .deadlines import annual_report_due, company_tax_return_due
from .models import ChecklistRun, Engagement, QualityLog, Signoff
from .views import _client_or_404, _clients_for, _err, _log, _ok, _user_name
from .views_kyc import status_of as kyc_status
from .views_quality import acceptance_status, open_conflicts

User = get_user_model()

ASSURANCE = ("revision", "udvidet_gennemgang", "review", "opstilling", "aftalte_handlinger")
ANNUAL = ("revision", "udvidet_gennemgang", "review", "opstilling")
# Forslag (husets valg – kan fravælges/suppleres). Kun skabeloner, der findes, vises.
SUGGESTED = {
    "revision": ["revisionsplanlaegning-strategi", "vaesentlighedsberegning", "risikovurdering-isa-315",
                 "regnskabsmaessige-skoen-isa-540", "naertstaaende-parter", "going-concern-vurdering",
                 "efterfoelgende-begivenheder", "afslutningstjekliste-aarsrapport-klasse-b"],
    "udvidet_gennemgang": ["materialeliste-aarsafslutning", "going-concern-vurdering", "efterfoelgende-begivenheder",
                           "afslutningstjekliste-aarsrapport-klasse-b"],
    "review": ["materialeliste-aarsafslutning", "going-concern-vurdering", "afslutningstjekliste-aarsrapport-klasse-b"],
    "opstilling": ["materialeliste-aarsafslutning", "afstemning-moms", "afstemning-loen-eindkomst",
                   "afslutningstjekliste-aarsrapport-klasse-b"],
    "bogfoering": ["afstemning-moms"],
    "loen": ["afstemning-loen-eindkomst"],
}
LETTERS = {
    "revision": "opdragsbrev-revision", "udvidet_gennemgang": "opdragsbrev-udvidet-gennemgang",
    "review": "opdragsbrev-review", "opstilling": "opdragsbrev-opstilling",
    "aftalte_handlinger": "opdragsbrev-aftalte-arbejdshandlinger", "skat": "opdragsbrev-skat-selskab",
    "loen": "aftale-bogfoering-loen-moms", "bogfoering": "aftale-bogfoering-loen-moms",
}
ITEM = re.compile(r"^\s*[-*]\s*\[ \]\s*(.+?)\s*$")
HEAD = re.compile(r"^#{2,3}\s+(.+?)\s*$")
ITEM_STATUS = ("", "ok", "ikke_relevant", "bemaerkning")


def _date(v):
    try:
        return datetime.strptime(str(v)[:10], "%Y-%m-%d").date() if v else None
    except ValueError:
        return None


def _templates_with_items():
    out = []
    for t in templating.load_all()[0]:
        if ITEM.search(t["body"]) or any(ITEM.match(line) for line in t["body"].splitlines()):
            out.append({"id": t["id"], "title": t["title"], "category": t["category"]})
    return out


def extract_items(text):
    section, items = "", []
    for line in text.splitlines():
        h = HEAD.match(line)
        if h:
            section = h.group(1).strip()
            continue
        m = ITEM.match(line)
        if m and m.group(1).strip():
            items.append({"id": str(len(items) + 1), "section": section, "text": m.group(1).strip(),
                          "status": "", "note": "", "by": None, "at": None})
    return items


def _year_dict(e):
    if not (e.year_start and e.year_end):
        return None
    return {"id": e.year_start.isoformat(), "start": e.year_start, "end": e.year_end, "closed": False}


def build_checklist(request, e, template_id, values=None):
    t = templating.get(template_id)
    if t is None:
        return None, "Skabelonen findes ikke"
    staff = staff_of(request.user)
    figures = active_grant(e.client, staff) is not None
    ctx = templating.build_context(Firm.current(), e.client, request.user, staff, _year_dict(e), with_figures=figures)
    text, vals = templating.render(t, ctx, values or {})
    items = extract_items(text)
    if not items:
        return None, "Skabelonen indeholder ingen tjeklistepunkter"
    sha = hashlib.sha256(json.dumps({"body": t["body"], "fields": t["fields"]}, sort_keys=True).encode()).hexdigest()
    run = ChecklistRun.objects.create(engagement=e, template_id=template_id, title=t["title"], template_sha256=sha,
                                      values={k: v for k, v in vals.items() if isinstance(v, (str, bool, int, float))},
                                      items=items)
    return run, None


def _active_signoffs(e):
    return [s for s in e.signoffs.all() if s.revoked_at is None]


def run_dict(r):
    done = sum(1 for i in r.items if i["status"])
    return {"id": str(r.id), "template_id": r.template_id, "title": r.title, "values": r.values, "items": r.items,
            "done": done, "total": len(r.items)}


def signoff_dict(s):
    return {"id": str(s.id), "step": s.step, "step_label": s.get_step_display(), "user": _user_name(s.user),
            "user_id": s.user_id, "note": s.note, "at": s.at.isoformat(),
            "revoked_at": s.revoked_at.isoformat() if s.revoked_at else None, "revoked_by": _user_name(s.revoked_by)}


def engagement_dict(e, full=False):
    runs = list(e.checklists.all())
    d = {
        "id": str(e.id), "client": e.client.slug, "client_name": e.client.name, "kind": e.kind,
        "kind_label": e.get_kind_display(), "title": e.title or e.get_kind_display(),
        "year_start": e.year_start.isoformat() if e.year_start else None,
        "year_end": e.year_end.isoformat() if e.year_end else None,
        "year_label": templating.year_label(e.year_start, e.year_end) if e.year_start and e.year_end else "",
        "partner_id": e.partner_id, "partner": _user_name(e.partner), "manager_id": e.manager_id,
        "manager": _user_name(e.manager), "status": e.status, "status_label": e.get_status_display(),
        "deadline": e.deadline.isoformat() if e.deadline else None,
        "budget_hours": str(e.budget_hours) if e.budget_hours is not None else None, "note": e.note,
        "progress": {"done": sum(sum(1 for i in r.items if i["status"]) for r in runs),
                     "total": sum(len(r.items) for r in runs)},
        "signoffs": [signoff_dict(s) for s in _active_signoffs(e)],
        "letter_template": LETTERS.get(e.kind),
    }
    if full:
        d["checklists"] = [run_dict(r) for r in runs]
        d["signoff_history"] = [signoff_dict(s) for s in e.signoffs.all()]
        d["acceptance_status"] = acceptance_status(e.client)
        d["kyc_status"] = kyc_status(e.client)
        d["open_conflicts"] = open_conflicts(client=e.client).count()
    return d


def _qs(staff):
    return Engagement.objects.filter(client__in=_clients_for(staff)).select_related(
        "client", "partner", "manager").prefetch_related("checklists", "signoffs__user", "signoffs__revoked_by")


def _get(request, pk):
    staff = staff_of(request.user)
    return _qs(staff).filter(pk=pk).first(), staff


def default_deadline(client, kind, year_end):
    if not year_end:
        return None
    if kind in ANNUAL:
        return annual_report_due(year_end, client.accounting_class or "B")
    if kind == "skat" and client.legal_form in ("aps", "as", "ivs", "holding"):
        return company_tax_return_due(year_end)
    return None


def _staff_user(uid):
    return User.objects.filter(id=uid, firm_staff__isnull=False).first() if uid else None


@api_view(["GET"])
@permission_classes([IsFirmStaff])
def engagements_meta(request):
    existing = {t["id"] for t in _templates_with_items()}
    return _ok({
        "kinds": [{"value": k, "label": v, "suggested": [t for t in SUGGESTED.get(k, []) if t in existing],
                   "letter": LETTERS.get(k), "assurance": k in ASSURANCE} for k, v in Engagement.KINDS],
        "statuses": [{"value": k, "label": v} for k, v in Engagement.STATUS],
        "checklist_templates": _templates_with_items(),
    })


@api_view(["GET", "POST"])
@permission_classes([IsFirmStaff])
def engagements(request):
    staff = staff_of(request.user)
    if request.method == "GET":
        qs = _qs(staff)
        qp = request.query_params
        if qp.get("client"):
            qs = qs.filter(client__slug=qp["client"])
        if qp.get("status"):
            qs = qs.filter(status__in=qp["status"].split(","))
        if qp.get("mine"):
            from django.db.models import Q
            qs = qs.filter(Q(partner=request.user) | Q(manager=request.user))
        if qp.get("open"):
            qs = qs.exclude(status="leveret")
        return _ok({"engagements": [engagement_dict(e) for e in qs]})

    d = request.data
    client, _ = _client_or_404(request, d.get("client") or "")
    if client is None:
        return _err("Vælg en kunde")
    if d.get("kind") not in dict(Engagement.KINDS):
        return _err("Vælg opdragstype")
    year = None
    if d.get("year"):
        year = next((y for y in templating.fiscal_years(client) if y["id"] == str(d["year"])), None)
        if year is None:
            return _err("Ukendt regnskabsår")
    try:
        budget = Decimal(str(d["budget_hours"])) if d.get("budget_hours") not in (None, "") else None
    except InvalidOperation:
        return _err("Ugyldigt timebudget")
    e = Engagement.objects.create(
        client=client, kind=d["kind"], title=(d.get("title") or "").strip()[:255],
        year_start=year["start"] if year else None, year_end=year["end"] if year else None,
        partner=_staff_user(d.get("partner_id")), manager=_staff_user(d.get("manager_id")) or request.user,
        deadline=_date(d.get("deadline")) or default_deadline(client, d["kind"], year["end"] if year else None),
        budget_hours=budget, note=(d.get("note") or "").strip(), created_by=request.user,
        acceptance=client.acceptances.filter(status="godkendt").first(),
    )
    errors = []
    for tid in d.get("checklists") or []:
        _, msg = build_checklist(request, e, tid)
        if msg:
            errors.append(f"{tid}: {msg}")
    _log(request, "engagement_created", client, engagement=str(e.id), kind=e.kind)
    e = _qs(staff).get(pk=e.pk)
    return _ok({"engagement": engagement_dict(e, full=True), "warnings": errors}, 201)


@api_view(["GET", "PUT"])
@permission_classes([IsFirmStaff])
def engagement_detail(request, pk):
    e, staff = _get(request, pk)
    if e is None:
        return _err("Opdraget findes ikke", 404)
    if request.method == "PUT":
        d = request.data
        for f in ("title", "note"):
            if f in d:
                setattr(e, f, (d[f] or "").strip())
        if "deadline" in d:
            e.deadline = _date(d["deadline"])
        if "budget_hours" in d:
            try:
                e.budget_hours = Decimal(str(d["budget_hours"])) if d["budget_hours"] not in (None, "") else None
            except InvalidOperation:
                return _err("Ugyldigt timebudget")
        if "partner_id" in d:
            e.partner = _staff_user(d["partner_id"])
        if "manager_id" in d:
            e.manager = _staff_user(d["manager_id"])
        if "status" in d:
            st = d["status"]
            if st not in dict(Engagement.STATUS):
                return _err("Ugyldig status")
            if st in ("afsluttet", "review") and st != e.status:
                return _err("Status sættes ved sign-off.")
            if st == "leveret" and e.status != "afsluttet":
                return _err("Opdraget skal være godkendt, før det kan markeres som leveret.")
            if st in ("planlagt", "i_gang") and _active_signoffs(e):
                return _err("Opdraget er signeret. En partner skal genåbne det.")
            e.status = st
        e.save()
        _log(request, "engagement_updated", e.client, engagement=str(e.id))
        e = _qs(staff).get(pk=e.pk)
    return _ok({"engagement": engagement_dict(e, full=True)})


@api_view(["POST"])
@permission_classes([IsFirmStaff])
def engagement_checklist(request, pk):
    e, staff = _get(request, pk)
    if e is None:
        return _err("Opdraget findes ikke", 404)
    if _active_signoffs(e):
        return _err("Opdraget er signeret. En partner skal genåbne det.", 409)
    run, msg = build_checklist(request, e, request.data.get("template_id") or "", request.data.get("values"))
    if msg:
        return _err(msg)
    _log(request, "checklist_added", e.client, engagement=str(e.id), template=run.template_id)
    return _ok({"checklist": run_dict(run)}, 201)


@api_view(["PUT", "DELETE"])
@permission_classes([IsFirmStaff])
def checklist_item(request, pk, item):
    staff = staff_of(request.user)
    run = ChecklistRun.objects.filter(pk=pk, engagement__client__in=_clients_for(staff)).select_related(
        "engagement__client").first()
    if run is None:
        return _err("Tjeklisten findes ikke", 404)
    if _active_signoffs(run.engagement):
        return _err("Opdraget er signeret. En partner skal genåbne det.", 409)
    if request.method == "DELETE":  # item = "all": fjern en ubesvaret tjekliste
        if any(i["status"] for i in run.items):
            return _err("Tjeklisten er påbegyndt og kan ikke fjernes.")
        run.delete()
        return _ok({})
    it = next((i for i in run.items if i["id"] == item), None)
    if it is None:
        return _err("Punktet findes ikke", 404)
    st = request.data.get("status", it["status"])
    if st not in ITEM_STATUS:
        return _err("Ugyldig status")
    note = str(request.data.get("note", it["note"]) or "")[:4000]
    if st == "bemaerkning" and not note.strip():
        return _err("Skriv bemærkningen (eller henvis til arbejdspapir).")
    it.update(status=st, note=note, by=_user_name(request.user) if st else None,
              at=timezone.now().isoformat() if st else None)
    run.save(update_fields=["items"])
    if run.engagement.status == "planlagt":
        Engagement.objects.filter(pk=run.engagement_id).update(status="i_gang")
    return _ok({"checklist": run_dict(run)})


@api_view(["POST"])
@permission_classes([IsFirmStaff])
def engagement_signoff(request, pk):
    e, staff = _get(request, pk)
    if e is None:
        return _err("Opdraget findes ikke", 404)
    step = request.data.get("step")
    active = {s.step: s for s in _active_signoffs(e)}
    if step not in dict(Signoff.STEPS) or step in active:
        return _err("Ugyldigt trin")
    if step == "udfoert":
        missing = sum(1 for r in e.checklists.all() for i in r.items if not i["status"])
        if missing:
            return _err(f"{missing} tjeklistepunkter er ikke besvaret.")
    elif step == "gennemgaaet":
        if "udfoert" not in active:
            return _err("Opdraget skal først signeres som udført.")
        if active["udfoert"].user_id == request.user.id:
            return _err("Gennemgangen skal foretages af en anden end den, der har udført arbejdet.")
        if staff.role not in ("partner", "revisor"):
            return _err("Gennemgang foretages af en revisor eller partner.", 403)
    elif step == "godkendt":
        if "gennemgaaet" not in active:
            return _err("Opdraget skal først gennemgås.")
        if not staff.is_partner:
            return _err("Kun en partner kan godkende opdraget.", 403)
        if e.kind in ASSURANCE:
            if acceptance_status(e.client) != "approved":
                return _err("Kunden/opgaven er ikke accepteret (fanen Kundeaccept).")
            if kyc_status(e.client) != "ok":
                return _err("Kundekendskabet er ikke godkendt og opdateret (fanen Hvidvask).")
            if open_conflicts(client=e.client).exists():
                return _err("Der er uafklarede uafhængighedsforhold for kunden.")
    Signoff.objects.create(engagement=e, step=step, user=request.user, note=(request.data.get("note") or "").strip())
    e.status = {"udfoert": "review", "gennemgaaet": "review", "godkendt": "afsluttet"}[step]
    e.save(update_fields=["status", "updated_at"])
    _log(request, f"engagement_{step}", e.client, engagement=str(e.id))
    return _ok({"engagement": engagement_dict(_qs(staff).get(pk=e.pk), full=True)})


@api_view(["POST"])
@permission_classes([IsFirmStaff])
def engagement_reopen(request, pk):
    e, staff = _get(request, pk)
    if e is None:
        return _err("Opdraget findes ikke", 404)
    if not staff.is_partner:
        return _err("Kun en partner kan genåbne et opdrag.", 403)
    note = (request.data.get("note") or "").strip()
    if not note:
        return _err("Begrund genåbningen.")
    now = timezone.now()
    n = e.signoffs.filter(revoked_at__isnull=True).update(revoked_at=now, revoked_by=request.user)
    e.status = "i_gang"
    e.note = (e.note + f"\n[{timezone.localtime(now):%d-%m-%Y}] Genåbnet: {note}").strip()
    e.save(update_fields=["status", "note", "updated_at"])
    _log(request, "engagement_reopened", e.client, engagement=str(e.id), signoffs=n, note=note)
    return _ok({"engagement": engagement_dict(_qs(staff).get(pk=e.pk), full=True)})


# ─── Kvalitetslog ─────────────────────────────────────────────────────────────

def log_dict(q):
    return {"id": str(q.id), "kind": q.kind, "kind_label": q.get_kind_display(), "title": q.title,
            "description": q.description, "follow_up": q.follow_up,
            "client": q.client.slug if q.client else None, "client_name": q.client.name if q.client else None,
            "engagement": str(q.engagement_id) if q.engagement_id else None,
            "created_by": _user_name(q.created_by), "created_at": q.created_at.isoformat(),
            "closed_at": q.closed_at.isoformat() if q.closed_at else None, "closed_by": _user_name(q.closed_by)}


@api_view(["GET", "POST"])
@permission_classes([IsFirmStaff])
def quality_log(request):
    staff = staff_of(request.user)
    if request.method == "GET":
        qs = QualityLog.objects.select_related("client", "created_by", "closed_by")
        if not staff.sees_all_clients:
            qs = qs.filter(created_by=request.user)
        return _ok({"entries": [log_dict(q) for q in qs], "kinds": [{"value": k, "label": v} for k, v in QualityLog.KINDS]})
    d = request.data
    if d.get("kind") not in dict(QualityLog.KINDS):
        return _err("Vælg type")
    if d.get("kind") == "evaluering" and not staff.is_partner:
        return _err("Den årlige evaluering registreres af en partner.", 403)
    title = (d.get("title") or "").strip()
    if not title:
        return _err("Skriv en overskrift")
    client = None
    if d.get("client"):
        client, _ = _client_or_404(request, d["client"])
        if client is None:
            return _err("Kunden findes ikke", 404)
    q = QualityLog.objects.create(kind=d["kind"], client=client, title=title[:255],
                                  description=(d.get("description") or "").strip(),
                                  engagement_id=d.get("engagement") or None, created_by=request.user)
    _log(request, "quality_log_created", client, kind=q.kind)
    return _ok({"entry": log_dict(q)}, 201)


@api_view(["PUT"])
@permission_classes([IsFirmStaff])
def quality_log_detail(request, pk):
    staff = staff_of(request.user)
    q = QualityLog.objects.filter(pk=pk).select_related("client").first()
    if q is None or (not staff.sees_all_clients and q.created_by_id != request.user.id):
        return _err("Findes ikke", 404)
    if q.closed_at:
        return _err("Punktet er lukket.", 409)
    if "follow_up" in request.data:
        q.follow_up = (request.data["follow_up"] or "").strip()
    if request.data.get("close"):
        if not staff.is_partner:
            return _err("Kun en partner kan lukke et punkt.", 403)
        if not q.follow_up:
            return _err("Beskriv opfølgningen, før punktet lukkes (BEK 512/2024 § 3, stk. 4).")
        q.closed_at, q.closed_by = timezone.now(), request.user
    q.save()
    _log(request, "quality_log_updated", q.client, closed=bool(q.closed_at))
    return _ok({"entry": log_dict(q)})
