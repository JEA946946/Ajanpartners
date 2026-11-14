"""Rollebaseret adgang i en kundes bøger.

Rollen kommer fra tenancy.access: kundens egen bruger (ClientMembership) eller en
medarbejder i revisorhuset med en aktiv AccessGrant. Middleware'en
(tenancy.middleware) har allerede valgt kundens skema og lagt adgangen på
request.client_access.

  admin      — alt, også kundens brugere og revisoradgang
  accountant — læse og skrive
  viewer     — kun læse
"""

from rest_framework.permissions import SAFE_METHODS, BasePermission


def get_access(request):
    access = getattr(request, "client_access", None)
    if access is None:
        access = getattr(getattr(request, "_request", None), "client_access", None)
    return access


def get_role(request):
    """Effective role in the current client, or None without access."""
    user = getattr(request, "user", None)
    if not user or not user.is_authenticated:
        return None
    access = get_access(request)
    return access.role if access else None


class RoleWriteAccess(BasePermission):
    """Alle med adgang til kunden må læse; admin og accountant må skrive."""

    message = "Din rolle må kun læse. Bed kundens administrator om skriveadgang."

    def has_permission(self, request, view):
        user = request.user
        if not user or not user.is_authenticated:
            return False
        access = get_access(request)
        if access is None:
            self.message = "Du har ikke adgang til denne virksomhed."
            return False
        if request.method in SAFE_METHODS:
            return True
        return access.can_write


class IsAdmin(BasePermission):
    """Kundens administrator (brugere, revisoradgang, indstillinger)."""

    message = "Kræver administratorrollen i virksomheden."

    def has_permission(self, request, view):
        access = get_access(request)
        return bool(access and access.role == "admin" and access.can_write)


def _firm_staff_with_mfa(request, perm):
    """FirmStaff, hvis brugeren er medarbejder og har to-faktor (når det kræves)."""
    from tenancy.access import staff_of
    from tenancy.mfa import has_mfa, mfa_required_for
    staff = staff_of(request.user)
    if staff is None:
        return None
    if mfa_required_for(request.user) and not has_mfa(request.user):
        perm.message = {"success": False,
                        "message": "Slå to-faktor-login til under Min profil, før du bruger admin-portalen.",
                        "code": "mfa_setup_required"}
        return None
    return staff


class IsFirmStaff(BasePermission):
    """Medarbejder i revisorhuset (admin-portalen, public-skemaet)."""

    message = "Kun for medarbejdere i Ajan Partners."

    def has_permission(self, request, view):
        return _firm_staff_with_mfa(request, self) is not None


class IsFirmPartner(BasePermission):
    message = "Kræver partnerrollen i Ajan Partners."

    def has_permission(self, request, view):
        staff = _firm_staff_with_mfa(request, self)
        return bool(staff and staff.is_partner)
