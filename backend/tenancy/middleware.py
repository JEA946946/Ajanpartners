"""Vælg kundens skema ud fra headeren X-Client.

- /api/v1/auth/*, /api/v1/me/* og /api/firm/* kører i public-skemaet.
- Alle andre /api/v1/-kald kræver X-Client: <slug>. Brugeren skal have adgang
  til kunden (tenancy.access.resolve), ellers 403. Kaldet kører derefter i
  kundens skema, og request.client_access fortæller rolle og vej ind.
- Kundens pakke begrænser kundens egne brugere (tenancy.features).
- En arkiveret kunde er read-only.
- Medarbejdere fra revisorhuset, der skriver i en kunde, logges i FirmAuditLog.
"""

from django.db import connection
from django.http import JsonResponse
from rest_framework_simplejwt.authentication import JWTAuthentication

from .access import resolve
from .context import current_access
from .features import FEATURES, feature_for_path
from .models import ClientCompany, FirmAuditLog

API_PREFIX = "/api/v1/"
PUBLIC_API = ("auth/", "me/", "public/")
SAFE = ("GET", "HEAD", "OPTIONS")


def _error(status, message, code):
    return JsonResponse({"success": False, "message": message, "code": code}, status=status)


def _jwt_user(request):
    try:
        result = JWTAuthentication().authenticate(request)
    except Exception:
        return None
    return result[0] if result else None


def _ip(request):
    fwd = request.META.get("HTTP_X_FORWARDED_FOR")
    return fwd.split(",")[-1].strip() if fwd else request.META.get("REMOTE_ADDR")


class ClientTenantMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        connection.set_schema_to_public()
        request.tenant = None
        request.client_access = None
        token = current_access.set(None)
        try:
            early = self._select(request)
            if early is not None:
                return early
            response = self.get_response(request)
            self._log_firm_write(request, response)
            return response
        finally:
            current_access.reset(token)
            connection.set_schema_to_public()

    def _select(self, request):
        path = request.path
        if not path.startswith(API_PREFIX):
            return None
        sub = path[len(API_PREFIX):]
        if sub == "me" or sub.startswith(PUBLIC_API):
            return None
        slug = request.headers.get("X-Client", "").strip()
        if not slug:
            return _error(400, "Vælg en kunde (headeren X-Client mangler).", "client_required")
        user = _jwt_user(request)
        if user is None:
            return _error(401, "Log ind igen.", "not_authenticated")
        client = (ClientCompany.objects.select_related("package")
                  .filter(slug=slug).exclude(schema_name="public").first())
        access = resolve(user, client) if client else None
        if access is None:
            # Samme svar for "findes ikke" og "ingen adgang": afslører ikke kundelisten.
            return _error(403, "Du har ikke adgang til denne kunde.", "no_client_access")
        if access.is_firm:
            from .mfa import has_mfa, mfa_required_for
            if mfa_required_for(user) and not has_mfa(user):
                return _error(403, "Slå to-faktor-login til, før du åbner en kundes bøger.", "mfa_setup_required")
        if client.status == "archived" and request.method not in SAFE:
            return _error(403, "Kunden er arkiveret og kan kun læses.", "client_archived")
        feature = feature_for_path(sub, request.method)
        if feature and not access.has_feature(feature):
            return _error(403, f"{FEATURES[feature]} indgår ikke i jeres pakke ({client.package.name}). "
                               "Kontakt Ajan Partners for at opgradere.", "feature_not_in_package")
        connection.set_tenant(client)
        request.tenant = client
        request.client_access = access
        current_access.set(access)
        return None

    def _log_firm_write(self, request, response):
        access = getattr(request, "client_access", None)
        if access is None or not access.is_firm:
            return
        connection.set_schema_to_public()
        if request.method in SAFE:
            self._log_firm_read(request, access)
            return
        FirmAuditLog.objects.create(
            user=access.staff.user, client=access.client, action="write",
            detail={"method": request.method, "path": request.path, "status": response.status_code},
            ip_address=_ip(request),
        )

    def _log_firm_read(self, request, access):
        """Læseadgang fra revisorhuset: én post pr. medarbejder, kunde og time
        (med den første sti), så loggen viser hvem der har set hvad hvornår."""
        from datetime import timedelta
        from django.utils import timezone
        since = timezone.now() - timedelta(hours=1)
        if FirmAuditLog.objects.filter(user=access.staff.user, client=access.client, action="read",
                                       timestamp__gte=since).exists():
            return
        FirmAuditLog.objects.create(user=access.staff.user, client=access.client, action="read",
                                    detail={"first_path": request.path}, ip_address=_ip(request))
