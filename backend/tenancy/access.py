"""Hvem må hvad i en kunde.

En bruger kommer ind i en kundes bøger på én af to måder:
- som kundens egen bruger (ClientMembership) med rollen admin/accountant/viewer
- som medarbejder i revisorhuset (FirmStaff) gennem en aktiv AccessGrant,
  hvor grantens scope giver rollen: read → viewer, bookkeeping → accountant,
  full → admin.
"""

from dataclasses import dataclass

from .models import AccessGrant, ClientMembership, FirmStaff

SCOPE_ROLE = {"read": "viewer", "bookkeeping": "accountant", "full": "admin"}
ROLE_RANK = {"viewer": 0, "accountant": 1, "admin": 2}


@dataclass
class ClientAccess:
    client: object
    role: str                 # admin | accountant | viewer
    via: str                  # member | firm
    staff: object = None      # FirmStaff, når via == "firm"
    grant: object = None

    @property
    def is_firm(self):
        return self.via == "firm"

    @property
    def can_write(self):
        return self.role in ("admin", "accountant") and self.client.status != "archived"

    def has_feature(self, feature):
        # Revisorhuset leverer selv bogføringen, så pakken begrænser kun kundens brugere.
        return self.is_firm or self.client.has_feature(feature)


def staff_of(user):
    if not user or not user.is_authenticated:
        return None
    try:
        staff = user.firm_staff
    except FirmStaff.DoesNotExist:
        return None
    return staff if staff.is_active else None


def active_grant(client, staff):
    for grant in AccessGrant.objects.filter(client=client, revoked_at__isnull=True,
                                            accepted_at__isnull=False).order_by("-accepted_at"):
        if grant.covers(staff):
            return grant
    return None


def resolve(user, client):
    """ClientAccess for the user in the client, or None. A user who is both a
    member and staff gets the stronger of the two roles."""
    if not user or not user.is_authenticated or client is None:
        return None
    candidates = []
    membership = ClientMembership.objects.filter(user=user, client=client, is_active=True).first()
    if membership:
        candidates.append(ClientAccess(client, membership.role, "member"))
    staff = staff_of(user)
    if staff:
        grant = active_grant(client, staff)
        if grant:
            candidates.append(ClientAccess(client, SCOPE_ROLE[grant.scope], "firm", staff, grant))
    if not candidates:
        return None
    return max(candidates, key=lambda a: ROLE_RANK[a.role])


def visible_clients(user):
    """Kunder, brugeren kan åbne (til kundevælgeren)."""
    from .models import ClientCompany

    ids = set(ClientMembership.objects.filter(user=user, is_active=True).values_list("client_id", flat=True))
    staff = staff_of(user)
    if staff:
        for grant in AccessGrant.objects.filter(revoked_at__isnull=True, accepted_at__isnull=False,
                                                client__status__in=("onboarding", "active", "archived")):
            if grant.client_id not in ids and grant.covers(staff):
                ids.add(grant.client_id)
    return ClientCompany.objects.filter(id__in=ids).exclude(schema_name="public").select_related("package")
