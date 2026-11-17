"""Admin-portalen: kundekendskab efter hvidvaskloven (KYC).

/api/firm/kyc/checklist                         spørgsmålene (firm/checklists/kyc.json)
/api/firm/kyc/overview                          status pr. kunde (forfaldne, høj risiko, mangler)
/api/firm/clients/<slug>/kyc                    GET samlet; POST ny vurdering (kladde)
/api/firm/clients/<slug>/kyc/persons            POST person (multipart: id_document)
/api/firm/kyc/persons/<id>                      PUT/DELETE (sletning = markeres inaktiv)
/api/firm/kyc/persons/<id>/document             hent ID-dokument
/api/firm/kyc/assessments/<id>                  PUT kladde
/api/firm/kyc/assessments/<id>/approve          partner godkender → låst
/api/firm/aml-reports                           kun partnere

Data ligger i public-skemaet og vises aldrig for kunden. Systemet foreslår (branche, PEP-svar),
revisoren tager stilling og en partner godkender.
"""

import calendar
import hashlib
import json
from datetime import date, datetime
from functools import lru_cache
from pathlib import Path

from django.http import FileResponse
from django.utils import timezone
from rest_framework.decorators import api_view, parser_classes, permission_classes
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser

from core.permissions import IsFirmStaff
from tenancy.access import staff_of
from tenancy.models import Firm

from . import branche
from .deadlines import add_months
from .models import AmlReport, KycAssessment, KycPerson
from .views import _client_or_404, _clients_for, _err, _log, _ok, _user_name

CHECKLIST = Path(__file__).resolve().parent / "checklists" / "kyc.json"
ANSWERS = ("ja", "nej", "ikke_relevant")


@lru_cache(maxsize=1)
def checklist():
    return json.loads(CHECKLIST.read_text(encoding="utf-8"))


def _date(value):
    if not value:
        return None
    try:
        return datetime.strptime(str(value)[:10], "%Y-%m-%d").date()
    except ValueError:
        return None


def review_months(level):
    months = Firm.current().kyc_review_months or {}
    return int(months.get(level) or {"lav": 36, "normal": 24, "hoej": 12}[level])


def next_review(level, from_date=None):
    d = from_date or timezone.localdate()
    y, m = add_months(d.year, d.month, review_months(level))
    return date(y, m, min(d.day, calendar.monthrange(y, m)[1]))


def person_dict(p):
    return {
        "id": str(p.id), "role": p.role, "role_label": p.get_role_display(), "name": p.name,
        "birth_date": p.birth_date.isoformat() if p.birth_date else None, "country": p.country,
        "ownership": p.ownership, "is_pep": p.is_pep, "pep_note": p.pep_note, "id_method": p.id_method,
        "has_document": bool(p.id_document), "verified_on": p.verified_on.isoformat() if p.verified_on else None,
        "verified_by": _user_name(p.verified_by), "active": p.active,
    }


def assessment_dict(a):
    return {
        "id": str(a.id), "version": a.version, "risk_level": a.risk_level, "risk_label": a.get_risk_level_display(),
        "purpose": a.purpose, "source_of_funds": a.source_of_funds, "reasons": a.reasons, "answers": a.answers,
        "industry_snapshot": a.industry_snapshot,
        "next_review_on": a.next_review_on.isoformat() if a.next_review_on else None,
        "status": a.status, "created_by": _user_name(a.created_by), "created_at": a.created_at.isoformat(),
        "approved_by": _user_name(a.approved_by),
        "approved_at": a.approved_at.isoformat() if a.approved_at else None, "sha256": a.sha256,
    }


def suggestion(client, persons=None):
    """Systemets forslag – revisoren tager selv stilling."""
    ctx = branche.context(client.industry_code)
    persons = persons if persons is not None else list(client.kyc_persons.filter(active=True))
    # Husets branchevurdering har fire trin; kunderisikoen tre (lempede/normale/skærpede procedurer,
    # HVL §§ 21, 11, 17). "Forhøjet" foreslås som normal – med branchens grunde som opmærksomhedspunkter.
    level = "hoej" if ctx.get("hvidvask_risiko") == "høj" else "normal"
    reasons = list(ctx.get("hvidvask_grunde") or [])
    if any(p.is_pep for p in persons):
        level = "hoej"
        reasons.append("En registreret person er markeret som PEP (HVL § 18).")
    return {
        "risk_level": level, "reasons": reasons, "focus": list(ctx.get("hvidvask_fokus") or []),
        "industry": ctx.get("titel") or "", "industry_risk": ctx.get("hvidvask_risiko"),
        "official_risk_industry": bool(ctx.get("risikobranche")),
        "note": "Forslaget bygger på husets interne branchevurdering og registrerede PEP'er – ikke en officiel klassificering.",
    }


def status_of(client, latest=None, today=None):
    """missing | draft | due | ok – ud fra seneste godkendte vurdering."""
    today = today or timezone.localdate()
    approved = latest if latest is not None else client.kyc_assessments.filter(status="godkendt").first()
    if approved is None:
        return "draft" if client.kyc_assessments.filter(status="kladde").exists() else "missing"
    if approved.next_review_on and approved.next_review_on <= today:
        return "due"
    return "ok"


@api_view(["GET"])
@permission_classes([IsFirmStaff])
def kyc_checklist(request):
    return _ok({"checklist": checklist(), "review_months": Firm.current().kyc_review_months})


@api_view(["GET"])
@permission_classes([IsFirmStaff])
def kyc_overview(request):
    staff = staff_of(request.user)
    today = timezone.localdate()
    rows = []
    for c in _clients_for(staff).exclude(status="archived").prefetch_related("kyc_assessments"):
        assessments = list(c.kyc_assessments.all())
        approved = next((a for a in assessments if a.status == "godkendt"), None)
        st = "ok"
        if approved is None:
            st = "draft" if assessments else "missing"
        elif approved.next_review_on and approved.next_review_on <= today:
            st = "due"
        rows.append({
            "slug": c.slug, "name": c.name, "industry_code": c.industry_code, "status": st,
            "risk_level": approved.risk_level if approved else None,
            "approved_at": approved.approved_at.isoformat() if approved and approved.approved_at else None,
            "next_review_on": approved.next_review_on.isoformat() if approved and approved.next_review_on else None,
        })
    order = {"due": 0, "missing": 1, "draft": 2, "ok": 3}
    rows.sort(key=lambda r: (order[r["status"]], r["next_review_on"] or "", r["name"]))
    return _ok({"clients": rows})


def _client(request, slug):
    client, staff = _client_or_404(request, slug)
    if client is None:
        return None, staff, _err("Kunden findes ikke", 404)
    return client, staff, None


@api_view(["GET", "POST"])
@permission_classes([IsFirmStaff])
def client_kyc(request, slug):
    client, staff, err = _client(request, slug)
    if err:
        return err
    if request.method == "POST":
        # Ny vurdering (kladde), forudfyldt fra den seneste og systemets forslag.
        if client.kyc_assessments.filter(status="kladde").exists():
            return _err("Der er allerede en kladde. Ret den, eller få den godkendt.")
        prev = client.kyc_assessments.first()
        sug = suggestion(client)
        a = KycAssessment.objects.create(
            client=client, version=(prev.version + 1) if prev else 1,
            risk_level=prev.risk_level if prev else sug["risk_level"],
            purpose=prev.purpose if prev else "", source_of_funds=prev.source_of_funds if prev else "",
            reasons=prev.reasons if prev else "", answers=dict(prev.answers) if prev else {},
            industry_snapshot=sug, created_by=request.user,
        )
        _log(request, "kyc_assessment_created", client, version=a.version)
        return _ok({"assessment": assessment_dict(a)}, 201)

    persons = list(client.kyc_persons.select_related("verified_by"))
    assessments = list(client.kyc_assessments.select_related("created_by", "approved_by"))
    approved = next((a for a in assessments if a.status == "godkendt"), None)
    return _ok({
        "status": status_of(client, approved) if approved else status_of(client),
        "persons": [person_dict(p) for p in persons],
        "assessments": [assessment_dict(a) for a in assessments],
        "suggestion": suggestion(client, [p for p in persons if p.active]),
        "checklist": checklist(),
        "can_approve": staff.is_partner,
    })


PERSON_FIELDS = ("role", "name", "birth_date", "country", "ownership", "is_pep", "pep_note", "id_method",
                 "verified_on", "active")


def _bool(v):
    return v in (True, "true", "True", "1", 1, "on")


def _apply_person(p, data, user):
    for f in PERSON_FIELDS:
        if f not in data:
            continue
        v = data[f]
        if f in ("birth_date", "verified_on"):
            v = _date(v)
        elif f in ("is_pep", "active"):
            v = _bool(v)
        else:
            v = (v or "").strip()
        setattr(p, f, v)
    if p.role not in dict(KycPerson.ROLES):
        return "Ugyldig rolle"
    if not p.name:
        return "Angiv navn"
    if "verified_on" in data and p.verified_on:
        p.verified_by = user
    return None


@api_view(["POST"])
@permission_classes([IsFirmStaff])
@parser_classes([MultiPartParser, FormParser, JSONParser])
def kyc_person_create(request, slug):
    client, _, err = _client(request, slug)
    if err:
        return err
    p = KycPerson(client=client)
    msg = _apply_person(p, request.data, request.user)
    if msg:
        return _err(msg)
    if request.FILES.get("id_document"):
        p.id_document = request.FILES["id_document"]
    p.save()
    _log(request, "kyc_person_created", client, person=str(p.id), role=p.role)
    return _ok({"person": person_dict(p)}, 201)


def _person(request, pk):
    staff = staff_of(request.user)
    return KycPerson.objects.filter(pk=pk, client__in=_clients_for(staff)).select_related("client").first()


@api_view(["PUT", "POST", "DELETE"])
@permission_classes([IsFirmStaff])
@parser_classes([MultiPartParser, FormParser, JSONParser])
def kyc_person_detail(request, pk):
    p = _person(request, pk)
    if p is None:
        return _err("Personen findes ikke", 404)
    if request.method == "DELETE":
        # Slettes ikke: oplysningerne skal opbevares (HVL § 30). Markeres som ikke længere aktuel.
        p.active = False
        p.save(update_fields=["active", "updated_at"])
        _log(request, "kyc_person_inactivated", p.client, person=str(p.id))
        return _ok({"person": person_dict(p)})
    msg = _apply_person(p, request.data, request.user)
    if msg:
        return _err(msg)
    if request.FILES.get("id_document"):
        p.id_document = request.FILES["id_document"]
    p.save()
    _log(request, "kyc_person_updated", p.client, person=str(p.id))
    return _ok({"person": person_dict(p)})


@api_view(["GET"])
@permission_classes([IsFirmStaff])
def kyc_person_document(request, pk):
    p = _person(request, pk)
    if p is None or not p.id_document:
        return _err("Dokumentet findes ikke", 404)
    _log(request, "kyc_document_viewed", p.client, person=str(p.id))
    return FileResponse(p.id_document.open("rb"), as_attachment=True,
                        filename=Path(p.id_document.name).name)


def _assessment(request, pk):
    staff = staff_of(request.user)
    a = KycAssessment.objects.filter(pk=pk, client__in=_clients_for(staff)).select_related("client").first()
    return a, staff


ASSESSMENT_FIELDS = ("risk_level", "purpose", "source_of_funds", "reasons", "answers", "next_review_on")


@api_view(["PUT"])
@permission_classes([IsFirmStaff])
def kyc_assessment_detail(request, pk):
    a, _ = _assessment(request, pk)
    if a is None:
        return _err("Vurderingen findes ikke", 404)
    if a.status == "godkendt":
        return _err("En godkendt vurdering kan ikke ændres. Opret en ny vurdering.", 409)
    data = request.data
    for f in ASSESSMENT_FIELDS:
        if f not in data:
            continue
        v = data[f]
        if f == "risk_level" and v not in dict(KycAssessment.LEVELS):
            return _err("Ugyldigt risikoniveau")
        if f == "answers":
            ids = {q["id"] for q in checklist()["questions"]}
            if not isinstance(v, dict):
                return _err("Ugyldige svar")
            clean = {}
            for k, ans in v.items():
                if k not in ids or not isinstance(ans, dict):
                    continue
                if ans.get("answer") not in (*ANSWERS, None, ""):
                    return _err("Ugyldigt svar")
                clean[k] = {"answer": ans.get("answer") or "", "note": str(ans.get("note") or "")[:2000]}
            v = clean
        elif f == "next_review_on":
            v = _date(v)
        else:
            v = (v or "").strip() if isinstance(v, str) else v
        setattr(a, f, v)
    a.save()
    _log(request, "kyc_assessment_updated", a.client, version=a.version)
    return _ok({"assessment": assessment_dict(a)})


def _content_hash(a, persons):
    payload = {
        "client": a.client.cvr or a.client.slug, "version": a.version, "risk_level": a.risk_level,
        "purpose": a.purpose, "source_of_funds": a.source_of_funds, "reasons": a.reasons, "answers": a.answers,
        "next_review_on": a.next_review_on.isoformat() if a.next_review_on else None,
        "persons": [person_dict(p) for p in persons], "checklist_version": checklist()["version"],
    }
    return hashlib.sha256(json.dumps(payload, sort_keys=True, ensure_ascii=False).encode()).hexdigest()


@api_view(["POST"])
@permission_classes([IsFirmStaff])
def kyc_assessment_approve(request, pk):
    a, staff = _assessment(request, pk)
    if a is None:
        return _err("Vurderingen findes ikke", 404)
    if not staff.is_partner:
        return _err("Kun en partner kan godkende kundekendskabet.", 403)
    if a.status == "godkendt":
        return _err("Vurderingen er allerede godkendt.", 409)
    questions = checklist()["questions"]
    missing = [q["id"] for q in questions if not (a.answers.get(q["id"]) or {}).get("answer")]
    if missing:
        return _err(f"Besvar alle spørgsmål først ({len(missing)} mangler).")
    if not a.purpose.strip():
        return _err("Beskriv forretningsforbindelsens formål og tilsigtede beskaffenhed.")
    persons = list(a.client.kyc_persons.filter(active=True).select_related("verified_by"))
    if not any(p.role == "reel_ejer" for p in persons):
        return _err("Registrér mindst én reel ejer (eller den daglige ledelse, hvis ingen kan identificeres).")
    if any(p.is_pep for p in persons) and not a.source_of_funds.strip():
        return _err("Ved PEP skal midlernes og formuens oprindelse beskrives (HVL § 18).")
    if not a.reasons.strip():
        return _err("Begrund risikovurderingen.")
    a.next_review_on = a.next_review_on or next_review(a.risk_level)
    a.status = "godkendt"
    a.approved_by = request.user
    a.approved_at = timezone.now()
    a.sha256 = _content_hash(a, persons)
    a.save()
    _log(request, "kyc_assessment_approved", a.client, version=a.version, risk=a.risk_level, sha256=a.sha256)
    return _ok({"assessment": assessment_dict(a)})


# ─── Underretninger (kun partnere) ────────────────────────────────────────────

def report_dict(r):
    return {"id": str(r.id), "client": r.client.slug, "client_name": r.client.name, "summary": r.summary,
            "reported_on": r.reported_on.isoformat() if r.reported_on else None, "reference": r.reference,
            "created_by": _user_name(r.created_by), "created_at": r.created_at.isoformat()}


@api_view(["GET", "POST"])
@permission_classes([IsFirmStaff])
def aml_reports(request):
    staff = staff_of(request.user)
    if not staff.is_partner:
        return _err("Kun partnere har adgang til underretninger.", 403)
    if request.method == "GET":
        qs = AmlReport.objects.select_related("client", "created_by")
        return _ok({"reports": [report_dict(r) for r in qs]})
    client, _, err = _client(request, request.data.get("client") or "")
    if err:
        return err
    summary = (request.data.get("summary") or "").strip()
    if not summary:
        return _err("Beskriv forholdet.")
    r = AmlReport.objects.create(client=client, summary=summary, reported_on=_date(request.data.get("reported_on")),
                                 reference=(request.data.get("reference") or "").strip(), created_by=request.user)
    # Logges uden indhold – kun at der er registreret noget.
    _log(request, "aml_report_created", None, report=str(r.id))
    return _ok({"report": report_dict(r)}, 201)


@api_view(["PUT"])
@permission_classes([IsFirmStaff])
def aml_report_detail(request, pk):
    staff = staff_of(request.user)
    if not staff.is_partner:
        return _err("Kun partnere har adgang til underretninger.", 403)
    r = AmlReport.objects.filter(pk=pk).select_related("client").first()
    if r is None:
        return _err("Findes ikke", 404)
    if "reported_on" in request.data:
        r.reported_on = _date(request.data["reported_on"])
    if "reference" in request.data:
        r.reference = (request.data["reference"] or "").strip()
    r.save()
    _log(request, "aml_report_updated", None, report=str(r.id))
    return _ok({"report": report_dict(r)})
