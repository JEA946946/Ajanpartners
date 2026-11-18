"""Admin-portalen: fuldmagter pr. kunde og forsidens overblik.

/api/firm/clients/<slug>/powers      GET / POST {kind, scope, holder_id, given_on, expires_on, reference, note}
/api/firm/powers/<id>                PUT (felter, {revoke: true})
/api/firm/powers                     GET ?expiring=<dage> – alle fuldmagter, medarbejderen kan se
/api/firm/dashboard                  GET – frister, opdrag, KYC, uafhængighed, fuldmagter, ufaktureret, betingelser

Overblikket samler kun data, der allerede findes i de andre moduler; der beregnes ingen nye frister.
"""

from collections import Counter
from datetime import datetime, timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework.decorators import api_view, permission_classes

from core.permissions import IsFirmStaff
from tenancy.access import staff_of
from tenancy.models import ClientMembership, Firm, FirmStaff, TermsAcceptance

from .deadlines import deadline_dict, deadlines_for, profile_of
from .models import (Engagement, FirmTask, IndependenceDeclaration, PowerOfAttorney, QualityLog)
from .views import _client_or_404, _clients_for, _err, _log, _ok, _user_name

User = get_user_model()
EXPIRY_WARNING_DAYS = 30


def _date(v):
    try:
        return datetime.strptime(str(v)[:10], "%Y-%m-%d").date() if v else None
    except ValueError:
        return None


# ─── Fuldmagter ───────────────────────────────────────────────────────────────

def poa_status(p, today=None):
    today = today or timezone.localdate()
    if p.revoked_on:
        return "revoked"
    if p.expires_on and p.expires_on < today:
        return "expired"
    if p.expires_on and p.expires_on <= today + timedelta(days=EXPIRY_WARNING_DAYS):
        return "expiring"
    return "active"


STATUS_LABEL = {"active": "Aktiv", "expiring": "Udløber snart", "expired": "Udløbet", "revoked": "Tilbagekaldt"}


def poa_dict(p):
    st = poa_status(p)
    return {"id": str(p.id), "client": p.client.slug, "client_name": p.client.name, "kind": p.kind,
            "kind_label": p.get_kind_display(), "scope": p.scope, "holder_id": p.holder_id,
            "holder": _user_name(p.holder), "given_on": p.given_on.isoformat() if p.given_on else None,
            "expires_on": p.expires_on.isoformat() if p.expires_on else None, "reference": p.reference,
            "document": str(p.document_id) if p.document_id else None, "note": p.note,
            "revoked_on": p.revoked_on.isoformat() if p.revoked_on else None, "status": st,
            "status_label": STATUS_LABEL[st]}


def _apply_poa(p, d, client):
    if "kind" in d or p.pk is None:
        if d.get("kind") not in dict(PowerOfAttorney.KINDS):
            return "Vælg type"
        p.kind = d["kind"]
    if "scope" in d or p.pk is None:
        p.scope = str(d.get("scope") or "").strip()[:255]
        if not p.scope:
            return "Beskriv, hvad fuldmagten omfatter"
    if "holder_id" in d:
        p.holder = User.objects.filter(id=d["holder_id"], firm_staff__isnull=False).first() if d["holder_id"] else None
    for f in ("given_on", "expires_on"):
        if f in d:
            setattr(p, f, _date(d[f]))
    if p.given_on and p.expires_on and p.expires_on < p.given_on:
        return "Udløbsdatoen ligger før datoen for fuldmagten"
    for f in ("reference", "note"):
        if f in d:
            setattr(p, f, str(d[f] or "").strip()[:255 if f == "reference" else 4000])
    if "document" in d:
        from .models import ClientDocument
        p.document = ClientDocument.objects.filter(pk=d["document"], client=client).first() if d["document"] else None
    return None


@api_view(["GET", "POST"])
@permission_classes([IsFirmStaff])
def client_powers(request, slug):
    client, _ = _client_or_404(request, slug)
    if client is None:
        return _err("Kunden findes ikke", 404)
    if request.method == "GET":
        qs = PowerOfAttorney.objects.filter(client=client).select_related("client", "holder")
        return _ok({"powers": [poa_dict(p) for p in qs],
                    "kinds": [{"value": k, "label": v} for k, v in PowerOfAttorney.KINDS]})
    p = PowerOfAttorney(client=client, created_by=request.user)
    msg = _apply_poa(p, request.data, client)
    if msg:
        return _err(msg)
    p.save()
    _log(request, "poa_created", client, poa=str(p.id), kind=p.kind)
    return _ok({"power": poa_dict(p)}, 201)


@api_view(["PUT"])
@permission_classes([IsFirmStaff])
def power_detail(request, pk):
    staff = staff_of(request.user)
    p = PowerOfAttorney.objects.filter(pk=pk, client__in=_clients_for(staff)).select_related("client", "holder").first()
    if p is None:
        return _err("Fuldmagten findes ikke", 404)
    if p.revoked_on:
        return _err("Fuldmagten er tilbagekaldt. Registrér en ny.", 409)
    if request.data.get("revoke"):
        p.revoked_on = _date(request.data.get("revoked_on")) or timezone.localdate()
        p.save()
        _log(request, "poa_revoked", p.client, poa=str(p.id))
        return _ok({"power": poa_dict(p)})
    msg = _apply_poa(p, request.data, p.client)
    if msg:
        return _err(msg)
    p.save()
    _log(request, "poa_updated", p.client, poa=str(p.id))
    return _ok({"power": poa_dict(p)})


@api_view(["GET"])
@permission_classes([IsFirmStaff])
def powers(request):
    staff = staff_of(request.user)
    qs = PowerOfAttorney.objects.filter(client__in=_clients_for(staff), revoked_on=None).select_related(
        "client", "holder")
    if request.query_params.get("expiring"):
        try:
            days = int(request.query_params["expiring"])
        except ValueError:
            days = EXPIRY_WARNING_DAYS
        qs = qs.filter(expires_on__lte=timezone.localdate() + timedelta(days=days))
    return _ok({"powers": [poa_dict(p) for p in qs]})


# ─── Overblik ─────────────────────────────────────────────────────────────────

def _terms_pending(clients):
    """Kunder, hvor mindst én aktiv bruger mangler at acceptere de gældende betingelser."""
    from tenancy.terms import required_documents
    shas = {d.sha256 for d in required_documents()}
    if not shas:
        return []
    ids = [c.id for c in clients]
    accepted = {}
    for uid, cid, sha in TermsAcceptance.objects.filter(client_id__in=ids, sha256__in=shas).values_list(
            "user_id", "client_id", "sha256"):
        accepted.setdefault((uid, cid), set()).add(sha)
    pending = Counter()
    for uid, cid in ClientMembership.objects.filter(client_id__in=ids, is_active=True).values_list("user_id",
                                                                                                    "client_id"):
        if accepted.get((uid, cid), set()) != shas:
            pending[cid] += 1
    by_id = {c.id: c for c in clients}
    return [{"client": by_id[cid].slug, "client_name": by_id[cid].name, "users": n} for cid, n in pending.items()]


@api_view(["GET"])
@permission_classes([IsFirmStaff])
def dashboard(request):
    staff = staff_of(request.user)
    today = timezone.localdate()
    firm = Firm.current()
    clients = list(_clients_for(staff).exclude(status="archived").exclude(pk=firm.own_client_id).select_related(
        "responsible"))
    mine = request.query_params.get("mine") == "1"
    if mine:
        assigned = set(staff.assignments.values_list("client_id", flat=True))
        clients = [c for c in clients if c.responsible_id == request.user.id or c.id in assigned]
    client_ids = [c.id for c in clients]

    # Frister de næste 14 dage (lovbestemte + opdrag), og overskredne opdrag
    horizon = today + timedelta(days=14)
    deadlines = []
    for c in clients:
        for dl in deadlines_for(profile_of(c), today, horizon):
            deadlines.append({**deadline_dict(dl), "client": c.slug, "client_name": c.name,
                              "responsible_name": _user_name(c.responsible)})
    engs = Engagement.objects.filter(client_id__in=client_ids).select_related("client", "partner")
    for e in engs.filter(deadline__gte=today, deadline__lte=horizon).exclude(status="leveret"):
        deadlines.append({"date": e.deadline.isoformat(), "kind": "opdrag",
                          "title": f"Opdrag: {e.title or e.get_kind_display()}", "client": e.client.slug,
                          "client_name": e.client.name, "engagement": str(e.id),
                          "responsible_name": _user_name(e.partner)})
    deadlines.sort(key=lambda r: (r["date"], r["client_name"]))
    overdue = [{"id": str(e.id), "title": e.title or e.get_kind_display(), "client_name": e.client.name,
                "deadline": e.deadline.isoformat(), "status_label": e.get_status_display()}
               for e in engs.filter(deadline__lt=today).exclude(status__in=("leveret", "afsluttet")).order_by("deadline")]
    open_engs = engs.exclude(status="leveret")
    status_counts = Counter(open_engs.values_list("status", flat=True))

    # Kundekendskab (samme regler som Hvidvask-siden)
    from .views_kyc import status_of as kyc_status
    kyc = Counter()
    kyc_rows = []
    for c in clients:
        st = kyc_status(c, today=today)
        kyc[st] += 1
        if st in ("due", "missing"):
            kyc_rows.append({"client": c.slug, "client_name": c.name, "status": st})

    # Uafhængighed (årets erklæringer) og uafklarede forhold
    from .views_quality import open_conflicts
    signed = set(IndependenceDeclaration.objects.filter(year=today.year, signed_at__isnull=False)
                 .values_list("staff_id", flat=True))
    active_staff = list(FirmStaff.objects.filter(is_active=True).select_related("user"))
    independence = {"year": today.year, "mine_signed": staff.id in signed,
                    "conflicts": open_conflicts().count() if staff.is_partner else open_conflicts(staff=staff).count()}
    if staff.is_partner:
        independence["missing"] = [_user_name(s.user) for s in active_staff if s.id not in signed]

    # Forespørgsler, kunden har svaret på (venter på huset)
    answered = FirmTask.objects.filter(client_id__in=client_ids, status="answered").count()
    my_tasks = FirmTask.objects.filter(assigned_to=request.user).exclude(status="closed").count()

    # Fuldmagter, der udløber inden for 30 dage eller er udløbet
    poas = [poa_dict(p) for p in PowerOfAttorney.objects.filter(
        client_id__in=client_ids, revoked_on=None, expires_on__lte=today + timedelta(days=EXPIRY_WARNING_DAYS))
        .select_related("client", "holder")]

    data = {
        "today": today.isoformat(), "mine": mine, "clients": len(clients),
        "deadlines": deadlines[:50], "deadlines_total": len(deadlines),
        "engagements": {"open": open_engs.count(), "by_status": [
            {"value": k, "label": v, "count": status_counts.get(k, 0)} for k, v in Engagement.STATUS if k != "leveret"],
            "overdue": overdue[:20]},
        "kyc": {"ok": kyc["ok"], "due": kyc["due"], "missing": kyc["missing"], "draft": kyc["draft"],
                "clients": kyc_rows[:20]},
        "independence": independence,
        "tasks": {"answered_by_client": answered, "mine_open": my_tasks},
        "powers": poas,
        "terms_pending": _terms_pending(clients),
        "evaluation_missing": not QualityLog.objects.filter(kind="evaluering", created_at__year=today.year).exists(),
    }
    if staff.is_partner:
        from .views_time import _billable_for_invoice, _entries_qs, _value
        total, oldest = Decimal("0"), None
        for e in _entries_qs().filter(invoice_id=None, billable=True, client_id__in=client_ids):
            if _billable_for_invoice(e):
                total += _value(e)
                oldest = min(oldest, e.date) if oldest else e.date
        from .models import FeeInstallment
        due_inst = FeeInstallment.objects.filter(invoice_id=None, due_on__lte=today,
                                                 engagement__client_id__in=client_ids)
        data["unbilled"] = {"time_value": str(total), "oldest": oldest.isoformat() if oldest else None,
                            "due_installments": due_inst.count(),
                            "due_installments_value": str(sum((i.amount for i in due_inst), Decimal("0")))}
    return _ok(data)
