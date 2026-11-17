"""Admin-portalen for Ajan Partners (public-skemaet, /api/firm/).

Kundelisten viser stamdata for alle kunder, medarbejderen må se (partner og
revisor: alle; bogholder og assistent: tildelte). Tal fra kundens bøger
(status-endpointet) kræver en aktiv adgang fra kunden – stamdata gør ikke.
"""

from django.contrib.auth import get_user_model
from django.db import transaction
from django.db.models import Count, Q
from django_tenants.utils import schema_context
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response

from core.permissions import IsFirmPartner, IsFirmStaff
from tenancy.access import active_grant, staff_of
from tenancy.features import FEATURES
from tenancy.models import (
    AccessGrant, ClientCompany, ClientMembership, Firm, FirmAuditLog, FirmStaff, Package, StaffAssignment,
)
from tenancy.services import archive_client, create_client, invite_user
from tenancy.views import firm_dict, grant_dict, package_dict

User = get_user_model()

CLIENT_FIELDS = ("name", "cvr", "legal_form", "address", "zip_code", "city", "industry_code", "email",
                 "phone", "vat_period", "fiscal_year_start_month", "accounting_class", "agreement_reference")


def _ok(data=None, code=200, message=None):
    body = {"success": True, "data": data or {}}
    if message:
        body["message"] = message
    return Response(body, status=code)


def _err(message, code=400):
    return Response({"success": False, "message": message}, status=code)


def _log(request, action, client=None, **detail):
    FirmAuditLog.objects.create(user=request.user, client=client, action=action, detail=detail,
                                ip_address=request.META.get("REMOTE_ADDR"))


def _clients_for(staff):
    qs = ClientCompany.objects.exclude(schema_name="public").select_related("package", "responsible")
    if not staff.sees_all_clients:
        qs = qs.filter(assignments__staff=staff)
    return qs


def _client_or_404(request, slug):
    staff = staff_of(request.user)
    return _clients_for(staff).filter(slug=slug).first(), staff


def _password_error(password, username="", user=None):
    """Djangos validatorer (længde, almindelige koder, kun tal, ligner brugernavnet)."""
    from django.contrib.auth.password_validation import validate_password
    from django.core.exceptions import ValidationError
    try:
        validate_password(password, user or User(username=username, email=username))
    except ValidationError as e:
        return " ".join(e.messages)
    return None


def _user_name(u):
    return (u.get_full_name() or u.username) if u else None


def _next_deadline(client):
    from django.utils import timezone
    from .deadlines import deadline_dict, next_deadline, profile_of
    if client.status == "archived":
        return None
    d = next_deadline(profile_of(client), timezone.localdate())
    return deadline_dict(d) if d else None


def client_dict(client, staff=None):
    grant = active_grant(client, staff) if staff else None
    any_active = any(g.is_active for g in client.grants.all())
    return {
        "id": client.id, "slug": client.slug, "name": client.name, "cvr": client.cvr,
        "legal_form": client.legal_form, "address": client.address, "zip_code": client.zip_code,
        "city": client.city, "industry_code": client.industry_code,
        "industry_title": _industry_title(client.industry_code), "email": client.email,
        "phone": client.phone, "vat_period": client.vat_period,
        "fiscal_year_start_month": client.fiscal_year_start_month, "accounting_class": client.accounting_class,
        "package": client.package.code, "package_name": client.package.name,
        "extra_features": client.extra_features, "status": client.status,
        "responsible_id": client.responsible_id, "responsible_name": _user_name(client.responsible),
        # Revisorhusets adgang følger kundeaftalen: scope for denne medarbejder, "ended" når
        # adgangen er afsluttet, None når medarbejderen ikke er tildelt kunden.
        "access": grant.scope if grant else (None if any_active else "ended"),
        "agreement_reference": client.agreement_reference,
        "agreement_accepted_on": client.agreement_accepted_on.isoformat() if client.agreement_accepted_on else None,
        "retain_until": client.retain_until.isoformat() if client.retain_until else None,
        "created_at": client.created_at.isoformat(),
        "assigned_staff": list(client.assignments.values_list("staff_id", flat=True)),
        "chart_template": client.chart_template,
        "next_deadline": _next_deadline(client),
        "open_tasks": client.firm_tasks.exclude(status="closed").count(),
        "answered_tasks": client.firm_tasks.filter(status="answered").count(),
    }


CHART_TEMPLATES = ("standard", "holding", "enkeltmand")


def _industry_title(code):
    if not code:
        return ""
    from integrations.industry import describe
    item = describe(code)
    return item["title"] if item else ""


def _validate_client_fields(data):
    if "name" in data and not (data.get("name") or "").strip():
        return "Navn skal udfyldes"
    cvr = (data.get("cvr") or "").strip()
    if cvr and (len(cvr) != 8 or not cvr.isdigit()):
        return "CVR-nummeret skal være 8 cifre"
    if (data.get("industry_code") or "").strip():
        from integrations.industry import normalize_code
        code, _converted = normalize_code(data["industry_code"])
        if code is None:
            return "Ukendt branchekode. Vælg en kode fra listen (Dansk Branchekode DB25)."
        data["industry_code"] = code  # gemmes som 6 cifre i DB25, også hvis en DB07-kode blev indtastet
    if "legal_form" in data and data["legal_form"] not in dict(ClientCompany.LEGAL_FORMS):
        return "Ukendt virksomhedsform"
    if "vat_period" in data and data["vat_period"] not in dict(ClientCompany.VAT_PERIODS):
        return "Ukendt momsperiode"
    if "accounting_class" in data and data["accounting_class"] not in ("A", "B", "C", "D"):
        return "Regnskabsklassen skal være A, B, C eller D"
    if "fiscal_year_start_month" in data:
        try:
            if not 1 <= int(data["fiscal_year_start_month"]) <= 12:
                raise ValueError
        except (TypeError, ValueError):
            return "Regnskabsårets startmåned skal være 1-12"
    return None


# ─── Kunder ───────────────────────────────────────────────────────────────────

@api_view(["GET", "POST"])
@permission_classes([IsFirmStaff])
def clients(request):
    staff = staff_of(request.user)
    if request.method == "GET":
        qs = _clients_for(staff)
        q = request.query_params.get("q", "").strip()
        if q:
            qs = qs.filter(Q(name__icontains=q) | Q(cvr__icontains=q) | Q(slug__icontains=q))
        for key in ("status", "package__code", "vat_period"):
            value = request.query_params.get(key.replace("__code", ""))
            if value:
                qs = qs.filter(**{key: value})
        if request.query_params.get("mine") == "1":
            qs = qs.filter(Q(responsible=request.user) | Q(assignments__staff=staff)).distinct()
        return _ok({"clients": [client_dict(c, staff) for c in qs]})

    if staff.role == "assistent":
        return _err("Assistenter kan ikke oprette kunder.", 403)
    data = request.data
    if not (data.get("name") or "").strip():
        return _err("Navn skal udfyldes")
    cvr = (data.get("cvr") or "").strip()
    if cvr and (len(cvr) != 8 or not cvr.isdigit()):
        return _err("CVR-nummeret skal være 8 cifre")
    if cvr and ClientCompany.objects.filter(cvr=cvr).exists():
        return _err("Der findes allerede en kunde med dette CVR-nummer")
    package_code = data.get("package", "standard")
    if not Package.objects.filter(code=package_code).exists():
        return _err("Ukendt pakke")
    error = _validate_client_fields(data)
    if error:
        return _err(error)
    if data.get("chart_template", "standard") not in CHART_TEMPLATES:
        return _err("Ukendt kontoplanskabelon")
    fields = {f: data[f] for f in CLIENT_FIELDS if f in data and f != "name"}
    fields["chart_template"] = data.get("chart_template", "standard")
    responsible = User.objects.filter(id=data.get("responsible_id")).first() if data.get("responsible_id") else None
    fields["responsible"] = responsible or request.user
    client, owner = create_client(name=data["name"].strip(), package_code=package_code, created_by=request.user,
                                  grant_scope=data.get("grant_scope", "full"),
                                  owner_email=data.get("owner_email", ""), owner_name=data.get("owner_name", ""),
                                  **fields)
    if not staff.sees_all_clients:
        StaffAssignment.objects.get_or_create(staff=staff, client=client)
    _log(request, "client_created", client, package=package_code)
    result = {"client": client_dict(client, staff)}
    if owner:
        user, temp_password = owner
        result["owner"] = {"username": user.username, "temporary_password": temp_password}
    return _ok(result, 201, "Kunden er oprettet. Kunden skal godkende adgangen ved første login.")


@api_view(["GET", "PUT"])
@permission_classes([IsFirmStaff])
def client_detail(request, slug):
    client, staff = _client_or_404(request, slug)
    if client is None:
        return _err("Kunden findes ikke", 404)
    if request.method == "GET":
        members = ClientMembership.objects.filter(client=client).select_related("user")
        return _ok({
            "client": client_dict(client, staff),
            "grants": [grant_dict(g) for g in client.grants.select_related("client", "requested_by")],
            "members": [{"id": str(m.id), "user_id": m.user_id, "username": m.user.username,
                         "name": _user_name(m.user), "email": m.user.email, "role": m.role,
                         "is_active": m.is_active} for m in members],
        })
    if staff.role in ("assistent",):
        return _err("Din rolle kan ikke ændre kunder.", 403)
    data = request.data
    error = _validate_client_fields(data)
    if error:
        return _err(error)
    if "cvr" in data and data["cvr"] and ClientCompany.objects.filter(cvr=data["cvr"]).exclude(pk=client.pk).exists():
        return _err("Der findes allerede en kunde med dette CVR-nummer")
    changes = {}
    for f in CLIENT_FIELDS:
        if f in data and getattr(client, f) != data[f]:
            changes[f] = [getattr(client, f), data[f]]
            setattr(client, f, data[f])
    if "package" in data and data["package"] != client.package.code:
        package = Package.objects.filter(code=data["package"]).first()
        if package is None:
            return _err("Ukendt pakke")
        changes["package"] = [client.package.code, package.code]
        client.package = package
    if "extra_features" in data:
        extra = [f for f in data["extra_features"] if f in FEATURES]
        changes["extra_features"] = [client.extra_features, extra]
        client.extra_features = extra
    if "responsible_id" in data:
        client.responsible = User.objects.filter(id=data["responsible_id"]).first()
        changes["responsible_id"] = data["responsible_id"]
    if "assigned_staff" in data and staff.sees_all_clients:
        ids = set(int(i) for i in data["assigned_staff"])
        from .views_quality import assignment_block
        existing = set(StaffAssignment.objects.filter(client=client).values_list("staff_id", flat=True))
        for sid in ids - existing:
            msg = assignment_block(sid, client)
            if msg:
                return _err(msg, 409)
        StaffAssignment.objects.filter(client=client).exclude(staff_id__in=ids).delete()
        for sid in ids:
            StaffAssignment.objects.get_or_create(client=client, staff_id=sid)
        changes["assigned_staff"] = sorted(ids)
    client.save()
    _log(request, "client_updated", client, changes=changes)
    return _ok({"client": client_dict(client, staff)})


@api_view(["POST"])
@permission_classes([IsFirmPartner])
def client_archive(request, slug):
    client, staff = _client_or_404(request, slug)
    if client is None:
        return _err("Kunden findes ikke", 404)
    archive_client(client)
    _log(request, "client_archived", client)
    return _ok({"client": client_dict(client, staff)},
               message="Kunden er arkiveret. Bøgerne gemmes read-only i mindst 5 år.")


@api_view(["POST"])
@permission_classes([IsFirmStaff])
def client_access(request, slug):
    """Afslut eller genåbn revisorhusets adgang (kun partner). Adgangen følger kundeaftalen,
    så det bruges kun, når aftalen er ophørt, eller hvis adgangen er afsluttet ved en fejl."""
    from tenancy.services import end_access, open_access
    client, staff = _client_or_404(request, slug)
    if client is None:
        return _err("Kunden findes ikke", 404)
    if not staff.is_partner:
        return _err("Kun partnere kan ændre revisorhusets adgang.", 403)
    action = request.data.get("action")
    if action == "end":
        n = end_access(client, request.user)
        _log(request, "access_ended", client, grants=n)
        return _ok({"client": client_dict(client, staff)}, message="Revisorhusets adgang er afsluttet.")
    if action == "open":
        scope = request.data.get("scope", "full")
        if scope not in dict(AccessGrant.SCOPES):
            return _err("Ugyldigt omfang")
        open_access(client, request.user, scope, request.data.get("note") or "Adgang genåbnet iht. kundeaftale")
        _log(request, "access_opened", client, scope=scope)
        return _ok({"client": client_dict(client, staff)}, message="Revisorhusets adgang er genåbnet.")
    return _err("action skal være 'end' eller 'open'")


@api_view(["POST"])
@permission_classes([IsFirmStaff])
def client_invite(request, slug):
    client, staff = _client_or_404(request, slug)
    if client is None:
        return _err("Kunden findes ikke", 404)
    email = (request.data.get("email") or "").strip()
    if "@" not in email:
        return _err("Angiv en gyldig e-mail")
    role = request.data.get("role", "admin")
    if role not in dict(ClientMembership.ROLES):
        return _err("Ugyldig rolle")
    limit = client.limit("users")
    if limit is not None and ClientMembership.objects.filter(client=client, is_active=True).count() >= limit:
        return _err(f"Pakken {client.package.name} har plads til {limit} bruger(e).", 403)
    user, temp_password = invite_user(client, email, request.data.get("name", ""), role)
    _log(request, "user_invited", client, email=email, role=role)
    return _ok({"username": user.username, "temporary_password": temp_password}, 201)


@api_view(["GET"])
@permission_classes([IsFirmStaff])
def client_export_all(request, slug):
    """Alt regnskabsmateriale for kunden som zip. Kræver kundens samtykke – undtagen for en
    partner, når kunden er arkiveret (udlevering ved ophør, til kurator eller myndigheder)."""
    from tenancy.views import export_response
    client, staff = _client_or_404(request, slug)
    if client is None:
        return _err("Kunden findes ikke", 404)
    if staff.role not in ("partner", "revisor"):
        return _err("Kun partnere og revisorer kan eksportere alt.", 403)
    if active_grant(client, staff) is None and not (staff.is_partner and client.status == "archived"):
        return _err("Kunden har ikke givet adgang.", 403)
    _log(request, "export_all", client)
    return export_response(client, request.user)


@api_view(["GET"])
@permission_classes([IsFirmStaff])
def client_status(request, slug):
    """Nøgletal fra kundens bøger – kun med kundens samtykke."""
    client, staff = _client_or_404(request, slug)
    if client is None:
        return _err("Kunden findes ikke", 404)
    if active_grant(client, staff) is None:
        return _err("Kunden har ikke givet adgang.", 403)
    from datetime import timedelta
    from django.utils import timezone
    if not FirmAuditLog.objects.filter(user=request.user, client=client, action="read",
                                       timestamp__gte=timezone.now() - timedelta(hours=1)).exists():
        _log(request, "read", client, first_path=request.path)
    from journals.models import JournalEntry, Period
    from core.models import BankReconciliation, Document
    from accounts.chart import SUSPENSE
    from journals.models import JournalEntryLine
    from django.db.models import Sum
    with schema_context(client.schema_name):
        last_entry = JournalEntry.objects.order_by("-date").values_list("date", flat=True).first()
        last_period = Period.objects.order_by("-year", "-month").first()
        suspense = JournalEntryLine.objects.filter(account__code=SUSPENSE, journal_entry__is_posted=True) \
            .aggregate(d=Sum("debit"), c=Sum("credit"))
        data = {
            "drafts": JournalEntry.objects.filter(is_posted=False).count(),
            "unvalidated": JournalEntry.objects.filter(is_posted=True, validated_at__isnull=True).count(),
            "documents_unlinked": Document.objects.filter(journal_entry__isnull=True, bill__isnull=True,
                                                          invoice__isnull=True, expense__isnull=True).count(),
            "suspense_balance": str((suspense["d"] or 0) - (suspense["c"] or 0)),
            "open_reconciliations": BankReconciliation.objects.exclude(status="completed").count(),
            "last_entry_date": last_entry.isoformat() if last_entry else None,
            "last_closed_period": str(last_period) if last_period else None,
        }
    return _ok({"status": data})


# ─── Pakker ───────────────────────────────────────────────────────────────────

@api_view(["GET", "POST"])
@permission_classes([IsFirmStaff])
def packages(request):
    if request.method == "GET":
        packs = Package.objects.annotate(
            n=Count("clients", filter=~Q(clients__schema_name="public") & ~Q(clients__status="archived")))
        return _ok({"packages": [{**package_dict(p), "client_count": p.n} for p in packs],
                    "features": FEATURES})
    if not staff_of(request.user).is_partner:
        return _err("Kun partnere kan oprette pakker.", 403)
    data = request.data
    if Package.objects.filter(code=data.get("code")).exists():
        return _err("Koden findes allerede")
    p = Package.objects.create(code=data["code"], name=data.get("name", data["code"]),
                               description=data.get("description", ""), order=data.get("order", 0),
                               features=[f for f in data.get("features", []) if f in FEATURES],
                               limits=data.get("limits", {}))
    _log(request, "package_created", code=p.code)
    return _ok({"package": package_dict(p)}, 201)


@api_view(["PUT"])
@permission_classes([IsFirmPartner])
def package_detail(request, pk):
    p = Package.objects.filter(pk=pk).first()
    if p is None:
        return _err("Pakken findes ikke", 404)
    data = request.data
    for f in ("name", "description", "order", "limits", "is_active"):
        if f in data:
            setattr(p, f, data[f])
    if "features" in data:
        p.features = [f for f in data["features"] if f in FEATURES]
    p.save()
    _log(request, "package_updated", code=p.code)
    return _ok({"package": package_dict(p)})


# ─── Medarbejdere ─────────────────────────────────────────────────────────────

def staff_dict(s):
    return {"id": s.id, "user_id": s.user_id, "username": s.user.username, "email": s.user.email,
            "first_name": s.user.first_name, "last_name": s.user.last_name, "role": s.role,
            "title": s.title, "is_active": s.is_active,
            "clients": list(s.assignments.values_list("client__slug", flat=True))}


@api_view(["GET", "POST"])
@permission_classes([IsFirmStaff])
def staff_list(request):
    firm = Firm.current()
    if request.method == "GET":
        return _ok({"staff": [staff_dict(s) for s in FirmStaff.objects.filter(firm=firm).select_related("user")]})
    if not staff_of(request.user).is_partner:
        return _err("Kun partnere kan oprette medarbejdere.", 403)
    data = request.data
    email = (data.get("email") or "").strip().lower()
    if "@" not in email or not data.get("password"):
        return _err("E-mail og adgangskode skal udfyldes")
    pw_error = _password_error(data["password"], email)
    if pw_error:
        return _err(pw_error)
    if data.get("role") not in dict(FirmStaff.ROLES):
        return _err("Ugyldig rolle")
    with transaction.atomic():
        user = User.objects.filter(email__iexact=email).first()
        if user is None:
            user = User.objects.create_user(username=email, email=email, password=data["password"],
                                            first_name=data.get("first_name", ""),
                                            last_name=data.get("last_name", ""))
        s, _ = FirmStaff.objects.update_or_create(user=user, defaults={
            "firm": firm, "role": data["role"], "title": data.get("title", ""), "is_active": True})
        for c in ClientCompany.objects.filter(slug__in=data.get("clients") or []):
            StaffAssignment.objects.get_or_create(staff=s, client=c)
    _log(request, "staff_created", email=email, role=s.role)
    return _ok({"staff": staff_dict(s)}, 201)


@api_view(["PUT"])
@permission_classes([IsFirmPartner])
def staff_detail(request, pk):
    s = FirmStaff.objects.filter(pk=pk).select_related("user").first()
    if s is None:
        return _err("Medarbejderen findes ikke", 404)
    data = request.data
    if s.user_id == request.user.id and (data.get("role", "partner") != "partner" or data.get("is_active") is False):
        return _err("Du kan ikke fjerne din egen partnerrolle")
    if data.get("password"):
        pw_error = _password_error(data["password"], s.user.username, s.user)
        if pw_error:
            return _err(pw_error)
    if "role" in data and data["role"] not in dict(FirmStaff.ROLES):
        return _err("Ugyldig rolle")
    if "clients" in data:  # tjek uafhængighed, før noget gemmes
        from .views_quality import assignment_block
        existing = set(StaffAssignment.objects.filter(staff=s).values_list("client__slug", flat=True))
        for c in ClientCompany.objects.filter(slug__in=set(data["clients"]) - existing):
            msg = assignment_block(s.id, c)
            if msg:
                return _err(msg, 409)
    for f in ("role", "title", "is_active"):
        if f in data:
            setattr(s, f, data[f])
    s.save()
    for f in ("first_name", "last_name"):
        if f in data:
            setattr(s.user, f, data[f])
    if data.get("password"):
        pw_error = _password_error(data["password"], s.user.username, s.user)
        if pw_error:
            return _err(pw_error)
        s.user.set_password(data["password"])
    s.user.save()
    if "clients" in data:
        slugs = set(data["clients"])
        StaffAssignment.objects.filter(staff=s).exclude(client__slug__in=slugs).delete()
        for c in ClientCompany.objects.filter(slug__in=slugs):
            StaffAssignment.objects.get_or_create(staff=s, client=c)
    _log(request, "staff_updated", staff=s.user.username)
    return _ok({"staff": staff_dict(s)})


# ─── Firma og log ─────────────────────────────────────────────────────────────

@api_view(["GET", "PUT"])
@permission_classes([IsFirmStaff])
def firm_settings(request):
    firm = Firm.current()
    if request.method == "PUT":
        if not staff_of(request.user).is_partner:
            return _err("Kun partnere kan ændre firmaoplysninger.", 403)
        data = {f: request.data[f] for f in ("name", "cvr", "address", "zip_code", "city", "email", "phone",
                                             "website", "logo", "primary_color") if f in request.data}
        for f, v in data.items():
            if isinstance(v, str) and f != "logo":
                data[f] = v.strip()
        if not data.get("name", firm.name):
            return _err("Revisorhuset skal have et navn.")
        if data.get("cvr"):
            from integrations.base import IntegrationError
            from integrations.cvr import normalize_cvr
            try:
                data["cvr"] = normalize_cvr(data["cvr"])
            except IntegrationError as e:
                return _err(str(e))
        if "kyc_review_months" in request.data:
            raw = request.data["kyc_review_months"] or {}
            try:
                months = {k: int(raw[k]) for k in ("lav", "normal", "hoej")}
            except (KeyError, TypeError, ValueError):
                return _err("Angiv antal måneder for lav, normal og høj risiko.")
            if any(not 1 <= m <= 60 for m in months.values()):
                return _err("Antal måneder skal være mellem 1 og 60.")
            data["kyc_review_months"] = months
        if data.get("email"):
            from django.core.exceptions import ValidationError
            from django.core.validators import validate_email
            try:
                validate_email(data["email"])
            except ValidationError:
                return _err("E-mailadressen er ikke gyldig.")
        for f, v in data.items():
            setattr(firm, f, v)
        firm.save()
        _log(request, "firm_updated")
    # Husets interne politik vises kun i admin-portalen (firm_dict bruges også over for kunderne).
    return _ok({"firm": {**firm_dict(firm), "kyc_review_months": firm.kyc_review_months}})


@api_view(["GET"])
@permission_classes([IsFirmStaff])
def audit_log(request):
    staff = staff_of(request.user)
    qs = FirmAuditLog.objects.select_related("user", "client")
    if not staff.sees_all_clients:
        qs = qs.filter(user=request.user)
    if request.query_params.get("client"):
        qs = qs.filter(client__slug=request.query_params["client"])
    if request.query_params.get("user"):
        qs = qs.filter(user_id=request.query_params["user"])
    rows = qs[: int(request.query_params.get("limit", 200))]
    return _ok({"entries": [{
        "id": r.id, "timestamp": r.timestamp.isoformat(), "user": _user_name(r.user),
        "client": r.client.slug if r.client else None, "client_name": r.client.name if r.client else None,
        "action": r.action, "detail": r.detail, "ip": r.ip_address,
    } for r in rows]})


# ─── Betingelser (forretningsbetingelser, databehandleraftale, privatlivspolitik) ──

@api_view(["GET", "POST"])
@permission_classes([IsFirmStaff])
def terms(request):
    from django.utils import timezone
    from tenancy.models import TermsAcceptance, TermsDocument
    from tenancy.views import doc_dict
    if request.method == "GET":
        docs = TermsDocument.objects.order_by("kind", "-created_at")
        current = {k: getattr(TermsDocument.current(k), "id", None) for k, _ in TermsDocument.KINDS}
        return _ok({"documents": [{**doc_dict(d, body=True), "is_current": current.get(d.kind) == d.id,
                                   "acceptances": TermsAcceptance.objects.filter(document=d).count()}
                                  for d in docs], "kinds": dict(TermsDocument.KINDS)})
    if not staff_of(request.user).is_partner:
        return _err("Kun partnere kan publicere betingelser.", 403)
    data = request.data
    if data.get("kind") not in dict(TermsDocument.KINDS):
        return _err("Ukendt dokumenttype")
    if not (data.get("version") or "").strip() or not (data.get("body") or "").strip():
        return _err("Version og tekst skal udfyldes")
    if TermsDocument.objects.filter(kind=data["kind"], version=data["version"].strip()).exists():
        return _err("Versionen findes allerede – en publiceret tekst kan ikke ændres; brug et nyt versionsnummer.")
    d = TermsDocument.objects.create(kind=data["kind"], version=data["version"].strip(),
                                     title=(data.get("title") or dict(TermsDocument.KINDS)[data["kind"]]).strip(),
                                     body=data["body"], published_at=timezone.now(), created_by=request.user)
    _log(request, "terms_published", kind=d.kind, version=d.version, sha256=d.sha256)
    return _ok({"document": doc_dict(d, body=True)}, 201,
               "Publiceret. Kundernes brugere skal acceptere den nye version ved næste login."
               if d.kind in TermsDocument.REQUIRED_KINDS else "Publiceret.")


@api_view(["GET"])
@permission_classes([IsFirmStaff])
def terms_acceptances(request, pk):
    from tenancy.models import TermsAcceptance
    rows = TermsAcceptance.objects.filter(document_id=pk).select_related("user", "client")
    return _ok({"acceptances": [{
        "client": a.client.slug, "client_name": a.client.name, "user": _user_name(a.user),
        "email": a.user.email, "accepted_at": a.accepted_at.isoformat(), "method": a.method,
        "ip": a.ip_address, "sha256": a.sha256} for a in rows]})
