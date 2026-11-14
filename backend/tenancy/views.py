"""Brugerens egne endpoints (public) og kundens styring af revisoradgang (i kunden).

/api/v1/me                    hvem er jeg, hvilke kunder kan jeg åbne
/api/v1/me/clients/<slug>     adgang, pakke og funktioner i én kunde
/api/v1/access-grants         (X-Client, admin) kundens samtykker til revisorhuset
"""

from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from core.audit import log_action
from core.permissions import IsAdmin, RoleWriteAccess

from .access import resolve, staff_of, visible_clients
from .features import FEATURES
from .models import AccessGrant, ClientCompany, Firm, FirmAuditLog, FirmStaff
from .mfa import has_mfa, mfa_required_for
from .services import accept_grant, revoke_grant


def firm_dict(firm):
    return {"name": firm.name, "cvr": firm.cvr, "email": firm.email, "phone": firm.phone,
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
        "pending_grants": [grant_dict(g) for g in AccessGrant.objects.filter(
            client__memberships__user=user, client__memberships__role="admin",
            accepted_at__isnull=True, revoked_at__isnull=True).select_related("client", "requested_by")],
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


# ─── I kunden: revisoradgang ──────────────────────────────────────────────────

@api_view(["GET"])
@permission_classes([RoleWriteAccess])
def access_grants(request):
    grants = AccessGrant.objects.filter(client=request.tenant).select_related("client", "requested_by")
    staff = FirmStaff.objects.filter(firm=request.tenant.firm, is_active=True).select_related("user")
    return Response({"success": True, "data": {
        "grants": [grant_dict(g) for g in grants],
        "firm": firm_dict(request.tenant.firm),
        "staff": [{"id": s.id, "name": s.user.get_full_name() or s.user.username, "role": s.role,
                   "title": s.title} for s in staff],
    }})


def _grant(request, pk):
    return AccessGrant.objects.filter(client=request.tenant, pk=pk).first()


@api_view(["POST"])
@permission_classes([IsAdmin])
def access_grant_create(request):
    """Kunden giver selv adgang (fx efter at have tilbagekaldt en tidligere)."""
    data = request.data
    scope = data.get("scope", "bookkeeping")
    if scope not in dict(AccessGrant.SCOPES):
        return Response({"success": False, "message": "Ugyldigt omfang"}, status=status.HTTP_400_BAD_REQUEST)
    grant = AccessGrant.objects.create(
        client=request.tenant, firm=request.tenant.firm, scope=scope,
        staff_scope=data.get("staff_scope", "all"), valid_until=data.get("valid_until") or None,
        requested_by=request.user, accepted_by=request.user, accepted_at=timezone.now(),
        request_note="Givet af virksomheden",
    )
    if grant.staff_scope == "named":
        grant.staff.set(FirmStaff.objects.filter(firm=request.tenant.firm, id__in=data.get("staff_ids", [])))
    log_action(request.user, "create", "AccessGrant", grant.id, changes={"scope": scope})
    return Response({"success": True, "data": {"grant": grant_dict(grant)}}, status=status.HTTP_201_CREATED)


@api_view(["POST"])
@permission_classes([IsAdmin])
def access_grant_accept(request, pk):
    grant = _grant(request, pk)
    if grant is None or grant.state != "pending":
        return Response({"success": False, "message": "Anmodningen findes ikke eller er allerede behandlet"},
                        status=status.HTTP_400_BAD_REQUEST)
    data = request.data
    if data.get("scope") in dict(AccessGrant.SCOPES):
        grant.scope = data["scope"]  # kunden kan give mindre (eller mere) end der blev bedt om
    if "valid_until" in data:
        grant.valid_until = data.get("valid_until") or None
    grant.save()
    accept_grant(grant, request.user)
    log_action(request.user, "update", "AccessGrant", grant.id,
               changes={"action": "accepted", "scope": grant.scope, "valid_until": str(grant.valid_until or "")})
    return Response({"success": True, "data": {"grant": grant_dict(grant)}})


@api_view(["POST"])
@permission_classes([IsAdmin])
def access_grant_revoke(request, pk):
    grant = _grant(request, pk)
    if grant is None or grant.revoked_at:
        return Response({"success": False, "message": "Adgangen findes ikke"}, status=status.HTTP_404_NOT_FOUND)
    revoke_grant(grant, request.user)
    log_action(request.user, "update", "AccessGrant", grant.id, changes={"action": "revoked"})
    return Response({"success": True, "data": {"grant": grant_dict(grant)}})


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
