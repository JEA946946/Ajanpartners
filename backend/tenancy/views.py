"""Brugerens egne endpoints (public) og kundens styring af revisoradgang (i kunden).

/api/v1/me                    hvem er jeg, hvilke kunder kan jeg åbne
/api/v1/me/clients/<slug>     adgang, pakke og funktioner i én kunde
/api/v1/me/terms              betingelser, der skal accepteres; /me/terms/accept
/api/v1/access-grants         (X-Client) aftale og revisoradgang – kun oplysning
"""

from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from core.audit import log_action
from core.permissions import IsAdmin, RoleWriteAccess

from .access import resolve, staff_of, visible_clients
from .features import FEATURES
from .models import AccessGrant, ClientCompany, Firm, FirmAuditLog, FirmStaff
from .mfa import has_mfa, mfa_required_for


def firm_dict(firm):
    return {"name": firm.name, "cvr": firm.cvr, "address": firm.address, "zip_code": firm.zip_code,
            "city": firm.city, "email": firm.email, "phone": firm.phone, "website": firm.website,
            "logo": firm.logo, "primary_color": firm.primary_color}


def package_dict(p):
    return {"id": p.id, "code": p.code, "name": p.name, "description": p.description, "order": p.order,
            "features": p.features, "limits": p.limits, "is_active": p.is_active}


def client_summary(client, access=None):
    d = {
        "id": client.id, "slug": client.slug, "name": client.name, "cvr": client.cvr,
        "status": client.status, "package": client.package.code, "package_name": client.package.name,
    }
    if access is not None:
        d.update({"role": access.role, "via": access.via})
    return d


def grant_dict(g):
    return {
        "id": str(g.id), "client": g.client.slug, "scope": g.scope, "staff_scope": g.staff_scope,
        "staff": [{"id": s.id, "name": s.user.get_full_name() or s.user.username, "role": s.role}
                  for s in g.staff.select_related("user")],
        "valid_until": g.valid_until.isoformat() if g.valid_until else None,
        "state": g.state, "request_note": g.request_note,
        "requested_by": g.requested_by.get_full_name() or g.requested_by.username if g.requested_by else None,
        "requested_at": g.requested_at.isoformat() if g.requested_at else None,
        "accepted_at": g.accepted_at.isoformat() if g.accepted_at else None,
        "revoked_at": g.revoked_at.isoformat() if g.revoked_at else None,
    }


def doc_dict(d, body=False):
    out = {"id": d.id, "kind": d.kind, "kind_label": d.get_kind_display(), "version": d.version,
           "title": d.title, "sha256": d.sha256,
           "published_at": d.published_at.isoformat() if d.published_at else None}
    if body:
        out["body"] = d.body
    return out


def _terms_required(user):
    """Kunder, hvor brugeren (som kundens egen bruger) mangler at acceptere betingelserne."""
    from .models import ClientMembership
    from .terms import missing_for
    out = []
    for m in ClientMembership.objects.filter(user=user, is_active=True).select_related("client"):
        missing = missing_for(user, m.client)
        if missing:
            out.append({"client": m.client.slug, "client_name": m.client.name, "role": m.role,
                        "documents": [doc_dict(d) for d in missing]})
    return out


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def me(request):
    user = request.user
    staff = staff_of(user)
    clients = []
    for client in visible_clients(user):
        access = resolve(user, client)
        if access:
            clients.append(client_summary(client, access))
    return Response({"success": True, "data": {
        "user": {"id": str(user.id), "username": user.username, "email": user.email,
                 "first_name": user.first_name, "last_name": user.last_name},
        "firm_staff": {"role": staff.role, "title": staff.title} if staff else None,
        "mfa": {"enabled": has_mfa(user), "required": mfa_required_for(user)},
        "firm": firm_dict(Firm.current()),
        "clients": clients,
        "terms_required": _terms_required(user),
    }})


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def me_client(request, slug):
    client = ClientCompany.objects.select_related("package").filter(slug=slug).exclude(schema_name="public").first()
    access = resolve(request.user, client) if client else None
    if access is None:
        return Response({"success": False, "message": "Du har ikke adgang til denne kunde."},
                        status=status.HTTP_403_FORBIDDEN)
    if access.is_firm:
        FirmAuditLog.objects.create(user=request.user, client=client, action="open",
                                    detail={"scope": access.grant.scope})
    features = sorted(FEATURES) if access.is_firm else sorted(client.features())
    return Response({"success": True, "data": {
        "client": {**client_summary(client, access), "vat_period": client.vat_period,
                   "legal_form": client.legal_form, "fiscal_year_start_month": client.fiscal_year_start_month,
                   "accounting_class": client.accounting_class},
        "package": package_dict(client.package),
        "features": features,
        "package_features": sorted(client.features()),
        "limits": client.package.limits,
        "access": {"role": access.role, "via": access.via, "can_write": access.can_write,
                   "grant_scope": access.grant.scope if access.grant else None},
    }})


# ─── Betingelser ─────────────────────────────────────────────────────────────

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def me_terms(request):
    """Teksterne, brugeren skal acceptere (pr. virksomhed), med fuld tekst."""
    from .models import TermsDocument
    docs = {d.id: d for d in TermsDocument.objects.filter(published_at__isnull=False)}
    required = _terms_required(request.user)
    for r in required:
        r["documents"] = [doc_dict(docs[d["id"]], body=True) for d in r["documents"]]
    privacy = TermsDocument.current("privacy")
    from integrations.esign import signature_method
    return Response({"success": True, "data": {"required": required, "signature_method": signature_method(),
                                               "privacy": doc_dict(privacy, body=True) if privacy else None}})


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def me_terms_accept(request):
    """Accepter de gældende versioner for én virksomhed. Logges med tid, IP, browser og sha256."""
    from .models import ClientMembership
    from .terms import accept, missing_for
    slug = request.data.get("client")
    m = ClientMembership.objects.filter(user=request.user, client__slug=slug, is_active=True) \
        .select_related("client").first()
    if m is None:
        return Response({"success": False, "message": "Du er ikke bruger i den virksomhed."},
                        status=status.HTTP_403_FORBIDDEN)
    from integrations.esign import signature_method
    if signature_method() == "mitid":
        return Response({"success": False, "message": "Betingelserne skal underskrives med MitID."},
                        status=status.HTTP_400_BAD_REQUEST)
    if not request.data.get("confirm"):
        return Response({"success": False, "message": "Sæt flueben for at acceptere."},
                        status=status.HTTP_400_BAD_REQUEST)
    missing = missing_for(request.user, m.client)
    shown = set(request.data.get("sha256") or [])
    if shown and {d.sha256 for d in missing} - shown:
        return Response({"success": False, "message": "Betingelserne er ændret, mens du læste dem. Genindlæs siden."},
                        status=status.HTTP_409_CONFLICT)
    fwd = request.META.get("HTTP_X_FORWARDED_FOR")
    ip = fwd.split(",")[-1].strip() if fwd else request.META.get("REMOTE_ADDR")
    rows = accept(request.user, m.client, missing, ip=ip, user_agent=request.META.get("HTTP_USER_AGENT", ""))
    FirmAuditLog.objects.create(user=request.user, client=m.client, action="terms_accepted", ip_address=ip,
                                detail={"documents": [f"{r.document.kind} {r.document.version}" for r in rows],
                                        "role": m.role})
    return Response({"success": True, "message": "Tak – betingelserne er accepteret."})


def _ip(request):
    fwd = request.META.get("HTTP_X_FORWARDED_FOR")
    return fwd.split(",")[-1].strip() if fwd else request.META.get("REMOTE_ADDR")


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def me_terms_sign(request):
    """Start MitID-underskrift (TERMS_SIGNATURE_METHOD=mitid). Returnerer udbyderens URL."""
    from integrations.base import AgreementRequired
    from integrations.esign import provider
    from .models import ClientMembership
    from .terms import missing_for
    m = ClientMembership.objects.filter(user=request.user, client__slug=request.data.get("client"),
                                        is_active=True).select_related("client").first()
    if m is None:
        return Response({"success": False, "message": "Du er ikke bruger i den virksomhed."},
                        status=status.HTTP_403_FORBIDDEN)
    docs = missing_for(request.user, m.client)
    try:
        result = provider().send_for_signature(
            f"Aftale med {m.client.firm.name}: {m.client.name}", docs, request.user.email,
            request.user.get_full_name() or request.user.username,
            request.data.get("return_url") or "/onboarding")
    except AgreementRequired as e:
        return Response({"success": False, "message": str(e)}, status=status.HTTP_501_NOT_IMPLEMENTED)
    return Response({"success": True, "data": result})


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def me_terms_sign_complete(request):
    """Udbyderen har sendt brugeren tilbage: tjek status og registrér accepten som MitID."""
    from integrations.esign import provider
    from .models import ClientMembership
    from .terms import accept, missing_for
    m = ClientMembership.objects.filter(user=request.user, client__slug=request.data.get("client"),
                                        is_active=True).select_related("client").first()
    ref = request.data.get("reference") or ""
    if m is None or not ref:
        return Response({"success": False, "message": "Ugyldig underskrift"}, status=status.HTTP_400_BAD_REQUEST)
    p = provider()
    if p.status(ref) != "signed":
        return Response({"success": False, "message": "Underskriften er ikke gennemført."},
                        status=status.HTTP_409_CONFLICT)
    rows = accept(request.user, m.client, missing_for(request.user, m.client), ip=_ip(request),
                  user_agent=request.META.get("HTTP_USER_AGENT", ""), method="mitid", signature_reference=ref)
    FirmAuditLog.objects.create(user=request.user, client=m.client, action="terms_signed", ip_address=_ip(request),
                                detail={"reference": ref, "provider": p.name,
                                        "documents": [f"{r.document.kind} {r.document.version}" for r in rows]})
    return Response({"success": True, "message": "Tak – betingelserne er underskrevet."})


@api_view(["GET"])
@permission_classes([AllowAny])
def public_terms(request, kind):
    """Gældende tekst uden login (til link i kundeaftale og invitationsmail)."""
    from .models import TermsDocument
    d = TermsDocument.current(kind)
    if d is None:
        return Response({"success": False, "message": "Findes ikke"}, status=status.HTTP_404_NOT_FOUND)
    return Response({"success": True, "data": {"document": doc_dict(d, body=True)}})


# ─── I kunden: aftale og revisoradgang (kun oplysning) ───────────────────────

@api_view(["GET"])
@permission_classes([RoleWriteAccess])
def access_grants(request):
    """Hvem i revisorhuset der har adgang, og hvilke betingelser virksomhedens brugere har accepteret.
    Adgangen følger kundeaftalen og kan ikke ændres her."""
    from .models import TermsAcceptance
    client = request.tenant
    grants = AccessGrant.objects.filter(client=client).select_related("client", "requested_by")
    active = [g for g in grants if g.is_active]
    staff = [s for s in FirmStaff.objects.filter(firm=client.firm, is_active=True).select_related("user")
             if any(g.covers(s) for g in active)]
    acceptances = TermsAcceptance.objects.filter(client=client).select_related("user", "document")
    return Response({"success": True, "data": {
        "firm": firm_dict(client.firm),
        "agreement_reference": client.agreement_reference,
        "agreement_accepted_on": client.agreement_accepted_on.isoformat() if client.agreement_accepted_on else None,
        "access_active": bool(active),
        "access_since": min((g.accepted_at for g in active), default=None),
        "staff": [{"id": s.id, "name": s.user.get_full_name() or s.user.username, "role": s.role,
                   "title": s.title} for s in staff],
        "acceptances": [{"user": a.user.get_full_name() or a.user.username, "document": a.document.title,
                         "kind": a.document.kind, "version": a.document.version, "method": a.method,
                         "accepted_at": a.accepted_at.isoformat()} for a in acceptances],
    }})


# ─── Eksportér alt ────────────────────────────────────────────────────────────

def export_response(client, user):
    import os

    from django.http import FileResponse

    from .export import build_export
    path = build_export(client, user)
    fh = open(path, "rb")
    os.unlink(path)  # filen forsvinder, når svaret er sendt (fh holder den åben)
    name = f"regnskabsmateriale_{client.cvr or client.slug}_{timezone.localdate():%Y%m%d}.zip"
    return FileResponse(fh, as_attachment=True, filename=name, content_type="application/zip")


@api_view(["GET"])
@permission_classes([RoleWriteAccess])
def export_all(request):
    """Kundens administrator henter alt regnskabsmateriale (SAF-T, bilag, audit-log).
    Virker også, når virksomheden er arkiveret (read-only)."""
    access = request.client_access
    if access.role != "admin":
        return Response({"success": False, "message": "Kræver administratorrollen i virksomheden."},
                        status=status.HTTP_403_FORBIDDEN)
    log_action(request.user, "export", "ExportAll", request.tenant.slug)
    return export_response(request.tenant, request.user)
