"""Admin-portalen: kundeaccept/fortsættelse og medarbejdernes uafhængighed.

/api/firm/checklists/<id>                         acceptance | independence
/api/firm/clients/<slug>/acceptances              GET liste; POST ny (kladde)
/api/firm/acceptances/<id>                        PUT kladde
/api/firm/acceptances/<id>/approve                partner: {"decision": "godkendt"|"afvist"}
/api/firm/independence                            GET egen erklæring for året (+ partner: oversigt)
/api/firm/independence/sign                       POST underskriv årets erklæring
/api/firm/independence/conflicts                  POST nyt forhold (også efter underskrift)
/api/firm/independence/conflicts/<id>/resolve     partner afklarer

Kilder: BEK nr. 512/2024 § 3, stk. 1, nr. 3-4; BEK nr. 520/2024 §§ 2-4 og 7; RL §§ 16, 18, 24, 26.
"""

import hashlib
import json
from functools import lru_cache
from pathlib import Path

from django.db.models import Q
from django.utils import timezone
from rest_framework.decorators import api_view, permission_classes

from core.permissions import IsFirmStaff
from tenancy.access import staff_of
from tenancy.models import FirmStaff, StaffAssignment

from .models import ClientAcceptance, IndependenceConflict, IndependenceDeclaration
from .views import _client_or_404, _clients_for, _err, _log, _ok, _user_name
from .views_kyc import status_of as kyc_status

DIR = Path(__file__).resolve().parent / "checklists"
ANSWERS = ("ja", "nej", "ikke_relevant")
BLOCKING = ("", "fjernet")  # uafklaret eller fjernet fra opgaven → kan ikke tildeles kunden


@lru_cache(maxsize=4)
def checklist(name):
    return json.loads((DIR / f"{name}.json").read_text(encoding="utf-8"))


def _sha(payload):
    return hashlib.sha256(json.dumps(payload, sort_keys=True, ensure_ascii=False, default=str).encode()).hexdigest()


def _clean_answers(name, raw):
    if not isinstance(raw, dict):
        return None, "Ugyldige svar"
    ids = {q["id"] for q in checklist(name)["questions"]}
    out = {}
    for k, a in raw.items():
        if k not in ids or not isinstance(a, dict):
            continue
        if a.get("answer") not in (*ANSWERS, None, ""):
            return None, "Ugyldigt svar"
        out[k] = {"answer": a.get("answer") or "", "note": str(a.get("note") or "")[:4000]}
        if name == "independence":
            out[k]["clients"] = [str(s) for s in (a.get("clients") or [])][:200]
    return out, None


@api_view(["GET"])
@permission_classes([IsFirmStaff])
def checklist_view(request, name):
    if name not in ("acceptance", "independence"):
        return _err("Ukendt tjekliste", 404)
    return _ok({"checklist": checklist(name)})


# ─── Uafhængighed: blokering af tildeling ─────────────────────────────────────

def open_conflicts(staff=None, client=None):
    qs = IndependenceConflict.objects.filter(resolution__in=BLOCKING).select_related(
        "declaration__staff__user", "client")
    if staff is not None:
        qs = qs.filter(declaration__staff=staff)
    if client is not None:
        qs = qs.filter(client=client)
    return qs


def assignment_block(staff_id, client):
    """Fejltekst, hvis medarbejderen ikke må tildeles kunden pga. et uafklaret uafhængighedsforhold."""
    c = open_conflicts(client=client).filter(declaration__staff_id=staff_id).first()
    if c is None:
        return None
    who = _user_name(c.declaration.staff.user)
    return (f"{who} kan ikke tildeles {client.name}: der er registreret et forhold, der kan true "
            "uafhængigheden, og som ikke er afklaret af en partner (BEK nr. 520/2024 § 3, stk. 3).")


# ─── Kundeaccept ──────────────────────────────────────────────────────────────

def acceptance_dict(a):
    return {
        "id": str(a.id), "kind": a.kind, "kind_label": a.get_kind_display(), "engagement_text": a.engagement_text,
        "answers": a.answers, "conclusion": a.conclusion, "checklist_version": a.checklist_version,
        "status": a.status, "status_label": a.get_status_display(), "created_by": _user_name(a.created_by),
        "created_at": a.created_at.isoformat(), "approved_by": _user_name(a.approved_by),
        "approved_at": a.approved_at.isoformat() if a.approved_at else None, "sha256": a.sha256,
    }


def acceptance_status(client):
    """none | draft | approved | rejected – ud fra den seneste afgjorte vurdering."""
    latest = client.acceptances.exclude(status="kladde").first()
    if latest is None:
        return "draft" if client.acceptances.exists() else "none"
    return "approved" if latest.status == "godkendt" else "rejected"


@api_view(["GET", "POST"])
@permission_classes([IsFirmStaff])
def client_acceptances(request, slug):
    client, staff = _client_or_404(request, slug)
    if client is None:
        return _err("Kunden findes ikke", 404)
    if request.method == "POST":
        if client.acceptances.filter(status="kladde").exists():
            return _err("Der er allerede en kladde. Ret den, eller få den afgjort.")
        prev = client.acceptances.exclude(status="kladde").first()
        kind = request.data.get("kind") or ("fortsaettelse" if prev else "accept")
        if kind not in dict(ClientAcceptance.KINDS):
            return _err("Ugyldig type")
        a = ClientAcceptance.objects.create(
            client=client, kind=kind, engagement_text=(request.data.get("engagement_text") or "").strip()[:255],
            checklist_version=checklist("acceptance")["version"], created_by=request.user)
        _log(request, "acceptance_created", client, kind=kind)
        return _ok({"acceptance": acceptance_dict(a)}, 201)
    rows = client.acceptances.select_related("created_by", "approved_by")
    conflicts = [{"staff": _user_name(c.declaration.staff.user), "question": c.question_id, "note": c.note}
                 for c in open_conflicts(client=client)]
    return _ok({
        "status": acceptance_status(client), "acceptances": [acceptance_dict(a) for a in rows],
        "checklist": checklist("acceptance"), "kyc_status": kyc_status(client),
        "open_conflicts": conflicts, "can_approve": staff.is_partner,
    })


def _acceptance(request, pk):
    staff = staff_of(request.user)
    a = ClientAcceptance.objects.filter(pk=pk, client__in=_clients_for(staff)).select_related("client").first()
    return a, staff


@api_view(["PUT"])
@permission_classes([IsFirmStaff])
def acceptance_detail(request, pk):
    a, _ = _acceptance(request, pk)
    if a is None:
        return _err("Findes ikke", 404)
    if a.status != "kladde":
        return _err("En afgjort vurdering kan ikke ændres. Opret en ny.", 409)
    d = request.data
    if "answers" in d:
        answers, msg = _clean_answers("acceptance", d["answers"])
        if msg:
            return _err(msg)
        a.answers = answers
    for f in ("conclusion", "engagement_text"):
        if f in d:
            setattr(a, f, (d[f] or "").strip())
    if d.get("kind") in dict(ClientAcceptance.KINDS):
        a.kind = d["kind"]
    a.save()
    _log(request, "acceptance_updated", a.client)
    return _ok({"acceptance": acceptance_dict(a)})


@api_view(["POST"])
@permission_classes([IsFirmStaff])
def acceptance_approve(request, pk):
    a, staff = _acceptance(request, pk)
    if a is None:
        return _err("Findes ikke", 404)
    if not staff.is_partner:
        return _err("Kun en partner kan afgøre accept og fortsættelse.", 403)
    if a.status != "kladde":
        return _err("Vurderingen er allerede afgjort.", 409)
    decision = request.data.get("decision")
    if decision not in ("godkendt", "afvist"):
        return _err("Vælg godkend eller afvis.")
    if not a.conclusion.strip():
        return _err("Skriv en konklusion.")
    if decision == "godkendt":
        qs = checklist("acceptance")["questions"]
        missing = [q for q in qs if not (a.answers.get(q["id"]) or {}).get("answer")]
        if missing:
            return _err(f"Besvar alle spørgsmål først ({len(missing)} mangler).")
        for q in qs:
            ans = a.answers[q["id"]]
            if q.get("block_if") and ans["answer"] == q["block_if"]:
                return _err(q["block_text"])
            if q.get("note_if") and ans["answer"] == q["note_if"] and not ans["note"].strip():
                return _err("Dokumentér truslerne og sikkerhedsforanstaltningerne (RL § 24, stk. 5).")
            if ans["answer"] == "ikke_relevant" and not q.get("allow_na"):
                return _err(f"Spørgsmålet kan ikke besvares med \"ikke relevant\": {q['text'][:60]}…")
        if kyc_status(a.client) != "ok":
            return _err("Kundekendskabet (fanen Hvidvask) skal være godkendt og opdateret først (HVL § 14, stk. 1).")
        if open_conflicts(client=a.client).exists():
            return _err("Der er uafklarede uafhængighedsforhold for kunden. De skal afklares under Uafhængighed først.")
    a.status = decision
    a.approved_by = request.user
    a.approved_at = timezone.now()
    a.sha256 = _sha({"client": a.client.cvr or a.client.slug, **acceptance_dict(a), "sha256": None})
    a.save()
    _log(request, f"acceptance_{decision}", a.client, sha256=a.sha256)
    return _ok({"acceptance": acceptance_dict(a)})


# ─── Uafhængighedserklæringer ─────────────────────────────────────────────────

def conflict_dict(c):
    return {
        "id": str(c.id), "staff": _user_name(c.declaration.staff.user), "staff_id": c.declaration.staff_id,
        "year": c.declaration.year, "client": c.client.slug, "client_name": c.client.name,
        "question_id": c.question_id, "note": c.note, "created_at": c.created_at.isoformat(),
        "resolution": c.resolution, "resolution_label": c.get_resolution_display() if c.resolution else "",
        "resolution_note": c.resolution_note, "resolved_by": _user_name(c.resolved_by),
        "resolved_at": c.resolved_at.isoformat() if c.resolved_at else None,
        "is_responsible": c.client.responsible_id == c.declaration.staff.user_id,
    }


def declaration_dict(d):
    return {"id": str(d.id), "year": d.year, "answers": d.answers, "checklist_version": d.checklist_version,
            "signed_at": d.signed_at.isoformat() if d.signed_at else None, "sha256": d.sha256,
            "conflicts": [conflict_dict(c) for c in d.conflicts.select_related("client", "resolved_by")]}


def _year(request):
    try:
        return int(request.query_params.get("year") or request.data.get("year") or timezone.localdate().year)
    except (TypeError, ValueError):
        return timezone.localdate().year


def _declaration(staff, year):
    d, _ = IndependenceDeclaration.objects.get_or_create(staff=staff, year=year)
    return d


def _register_conflict(request, decl, client, question_id, note):
    c = IndependenceConflict.objects.create(declaration=decl, client=client, question_id=question_id, note=note)
    # Personen skal straks fjernes fra opgaveteamet (BEK nr. 520/2024 § 3, stk. 3, og § 4, stk. 2).
    removed = StaffAssignment.objects.filter(staff=decl.staff, client=client).delete()[0]
    _log(request, "independence_conflict", client, staff=decl.staff.user.username, question=question_id,
         assignment_removed=bool(removed))
    return c


@api_view(["GET"])
@permission_classes([IsFirmStaff])
def independence(request):
    staff = staff_of(request.user)
    year = _year(request)
    mine = IndependenceDeclaration.objects.filter(staff=staff, year=year).first()
    data = {"year": year, "checklist": checklist("independence"),
            "declaration": declaration_dict(mine) if mine else None,
            "clients": [{"slug": c.slug, "name": c.name} for c in _clients_for(staff).exclude(status="archived")
                        .order_by("name")],
            "is_partner": staff.is_partner}
    if staff.is_partner:
        signed = {d.staff_id: d for d in IndependenceDeclaration.objects.filter(year=year, signed_at__isnull=False)}
        data["staff"] = [{
            "id": s.id, "name": _user_name(s.user), "role": s.role,
            "signed_at": signed[s.id].signed_at.isoformat() if s.id in signed else None,
        } for s in FirmStaff.objects.filter(is_active=True).select_related("user").order_by("user__first_name")]
        data["conflicts"] = [conflict_dict(c) for c in IndependenceConflict.objects.filter(
            Q(resolution__in=BLOCKING) | Q(declaration__year=year)).select_related(
            "declaration__staff__user", "client", "resolved_by")]
    return _ok(data)


@api_view(["POST"])
@permission_classes([IsFirmStaff])
def independence_sign(request):
    staff = staff_of(request.user)
    year = _year(request)
    decl = _declaration(staff, year)
    if decl.signed_at:
        return _err("Årets erklæring er allerede underskrevet. Nye forhold registreres som et forhold.", 409)
    answers, msg = _clean_answers("independence", request.data.get("answers"))
    if msg:
        return _err(msg)
    qs = checklist("independence")["questions"]
    if any(not (answers.get(q["id"]) or {}).get("answer") in ("ja", "nej") for q in qs):
        return _err("Svar ja eller nej på alle spørgsmål.")
    if not request.data.get("confirm"):
        return _err("Bekræft erklæringen.")
    allowed = {c.slug: c for c in _clients_for(staff)}
    for q in qs:
        a = answers[q["id"]]
        if a["answer"] == "ja" and (not a["clients"] or not a["note"].strip()):
            return _err("Angiv kunde(r) og beskriv forholdet for hvert ja.")
        if any(s not in allowed for s in a["clients"]):
            return _err("Ukendt kunde")
    decl.answers = answers
    decl.checklist_version = checklist("independence")["version"]
    decl.signed_at = timezone.now()
    decl.sha256 = _sha({"staff": staff.user.username, "year": year, "answers": answers,
                        "version": decl.checklist_version, "signed_at": decl.signed_at})
    decl.save()
    for q in qs:
        a = answers[q["id"]]
        for slug in a["clients"] if a["answer"] == "ja" else []:
            _register_conflict(request, decl, allowed[slug], q["id"], a["note"])
    _log(request, "independence_signed", None, year=year, sha256=decl.sha256)
    return _ok({"declaration": declaration_dict(decl)})


@api_view(["POST"])
@permission_classes([IsFirmStaff])
def independence_conflict(request):
    """Et nyt forhold i løbet af året (medarbejderen selv – eller en partner på vegne af en medarbejder)."""
    staff = staff_of(request.user)
    target = staff
    if request.data.get("staff_id") and staff.is_partner:
        target = FirmStaff.objects.filter(pk=request.data["staff_id"]).select_related("user").first() or staff
    client = _clients_for(staff).filter(slug=request.data.get("client") or "").first()
    if client is None:
        return _err("Vælg en kunde")
    qid = request.data.get("question_id") or ""
    if qid not in {q["id"] for q in checklist("independence")["questions"]}:
        return _err("Vælg hvilket forhold der er tale om")
    note = (request.data.get("note") or "").strip()
    if not note:
        return _err("Beskriv forholdet")
    c = _register_conflict(request, _declaration(target, _year(request)), client, qid, note)
    return _ok({"conflict": conflict_dict(c)}, 201)


@api_view(["POST"])
@permission_classes([IsFirmStaff])
def independence_resolve(request, pk):
    staff = staff_of(request.user)
    if not staff.is_partner:
        return _err("Kun en partner kan afklare forholdet.", 403)
    c = IndependenceConflict.objects.filter(pk=pk).select_related("declaration__staff__user", "client").first()
    if c is None:
        return _err("Findes ikke", 404)
    if c.declaration.staff.user_id == request.user.id:
        return _err("Et forhold, der vedrører dig selv, skal afklares af en anden partner.", 403)
    res = request.data.get("resolution")
    if res not in dict(IndependenceConflict.RESOLUTIONS):
        return _err("Vælg en afklaring")
    note = (request.data.get("note") or "").strip()
    if not note:
        return _err("Begrund afklaringen (RL § 24, stk. 5).")
    if res == "sikkerhed" and c.question_id not in ("partsrepr", "familie_oevrig"):
        return _err("Sikkerhedsforanstaltninger kan kun afhjælpe de øvrige trusler (§ 7). Ved trusler efter § 2 "
                    "skal personen fjernes, interessen afhændes, eller huset afstå (BEK nr. 520/2024 §§ 2-4).")
    c.resolution, c.resolution_note = res, note
    c.resolved_by, c.resolved_at = request.user, timezone.now()
    c.save()
    _log(request, "independence_resolved", c.client, staff=c.declaration.staff.user.username, resolution=res)
    return _ok({"conflict": conflict_dict(c)})
