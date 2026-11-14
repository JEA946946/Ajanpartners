"""Public-skemaet: revisorhuset, kunderne, pakker, brugeradgang og samtykker.

Hver kunde (ClientCompany) har sit eget Postgres-skema med hele bogføringen
(accounts, journals, sales, purchases, core, payroll). Her ligger kun det, der
går på tværs: hvem der må hvad i hvilken kunde.
"""

import uuid

from django.conf import settings
from django.db import models
from django.utils import timezone
from django_tenants.models import DomainMixin, TenantMixin


class Firm(models.Model):
    """Revisorhuset (Ajan Partners). Én række i dag; modellen gør white-label muligt."""

    name = models.CharField(max_length=200)
    cvr = models.CharField(max_length=8, blank=True, default="")
    address = models.TextField(blank=True, default="")
    email = models.EmailField(blank=True, default="")
    phone = models.CharField(max_length=50, blank=True, default="")
    logo = models.TextField(blank=True, default="")  # base64 data-URL
    primary_color = models.CharField(max_length=20, default="#0B3D5C")

    class Meta:
        db_table = "firm"

    def __str__(self):
        return self.name

    @classmethod
    def current(cls):
        firm = cls.objects.order_by("id").first()
        if firm is None:
            firm = cls.objects.create(name="Ajan Partners")
        return firm


class Package(models.Model):
    """En pakke (Mini, Standard, Pro). Alle er gratis; pakken følger kundens aftale."""

    code = models.SlugField(max_length=30, unique=True)
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, default="")
    order = models.IntegerField(default=0)
    features = models.JSONField(default=list)  # navne fra tenancy.features.FEATURES
    limits = models.JSONField(default=dict)    # {"invoices_per_month": 10, "users": 1}
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "packages"
        ordering = ["order"]

    def __str__(self):
        return self.name


class ClientCompany(TenantMixin):
    """En kunde hos revisorhuset = ét skema med egne bøger."""

    LEGAL_FORMS = [
        ("aps", "ApS"), ("as", "A/S"), ("ivs", "IVS"), ("enk", "Enkeltmandsvirksomhed"),
        ("is", "I/S"), ("pmv", "Personligt ejet mindre virksomhed"), ("fmba", "F.m.b.a."),
        ("forening", "Forening"), ("holding", "Holding"), ("andet", "Andet"),
    ]
    VAT_PERIODS = [("none", "Ikke momsregistreret"), ("month", "Måned"),
                   ("quarter", "Kvartal"), ("half", "Halvår")]
    STATUS = [("onboarding", "Under oprettelse"), ("active", "Aktiv"),
              ("archived", "Arkiveret (read-only, 5 års opbevaring)")]

    firm = models.ForeignKey(Firm, on_delete=models.PROTECT, related_name="clients")
    slug = models.SlugField(max_length=63, unique=True)
    name = models.CharField(max_length=255)
    cvr = models.CharField(max_length=8, blank=True, default="", db_index=True)
    legal_form = models.CharField(max_length=20, choices=LEGAL_FORMS, default="aps")
    address = models.TextField(blank=True, default="")
    zip_code = models.CharField(max_length=10, blank=True, default="")
    city = models.CharField(max_length=100, blank=True, default="")
    industry_code = models.CharField(max_length=10, blank=True, default="")  # DB07
    email = models.EmailField(blank=True, default="")
    phone = models.CharField(max_length=50, blank=True, default="")
    package = models.ForeignKey(Package, on_delete=models.PROTECT, related_name="clients")
    extra_features = models.JSONField(default=list, blank=True)
    vat_period = models.CharField(max_length=10, choices=VAT_PERIODS, default="quarter")
    fiscal_year_start_month = models.IntegerField(default=1)
    accounting_class = models.CharField(max_length=2, default="B")  # ÅRL regnskabsklasse
    chart_template = models.CharField(max_length=20, default="standard")
    responsible = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="responsible_for",
    )
    status = models.CharField(max_length=20, choices=STATUS, default="onboarding")
    archived_at = models.DateTimeField(null=True, blank=True)
    retain_until = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    auto_create_schema = True
    auto_drop_schema = False  # Bogføringsloven: bøgerne skal gemmes i 5 år

    class Meta:
        db_table = "client_companies"
        ordering = ["name"]

    def __str__(self):
        return self.name

    @property
    def is_public(self):
        return self.schema_name == "public"

    def features(self):
        return set(self.package.features or []) | set(self.extra_features or [])

    def has_feature(self, feature):
        return feature in self.features()

    def limit(self, name):
        return (self.package.limits or {}).get(name)


class Domain(DomainMixin):
    """Kræves af django-tenants. Vi vælger kunden med headeren X-Client, ikke domænet,
    så her står kun public-domænet."""

    class Meta:
        db_table = "domains"


class FirmStaff(models.Model):
    """En medarbejder i revisorhuset."""

    ROLES = [
        ("partner", "Partner"),        # alt, også pakker, medarbejdere og sletning
        ("revisor", "Revisor"),        # alle kunder, årsafslutning, låsning af år
        ("bogholder", "Bogholder"),    # tildelte kunder, bogføring og moms
        ("assistent", "Assistent"),    # tildelte kunder, kun bilag og forespørgsler
    ]

    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="firm_staff")
    firm = models.ForeignKey(Firm, on_delete=models.PROTECT, related_name="staff")
    role = models.CharField(max_length=20, choices=ROLES, default="bogholder")
    title = models.CharField(max_length=100, blank=True, default="")
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "firm_staff"

    def __str__(self):
        return f"{self.user.username} ({self.role})"

    @property
    def sees_all_clients(self):
        return self.role in ("partner", "revisor")

    @property
    def is_partner(self):
        return self.role == "partner"


class StaffAssignment(models.Model):
    """Hvilke kunder en bogholder eller assistent arbejder på."""

    staff = models.ForeignKey(FirmStaff, on_delete=models.CASCADE, related_name="assignments")
    client = models.ForeignKey(ClientCompany, on_delete=models.CASCADE, related_name="assignments")

    class Meta:
        db_table = "staff_assignments"
        unique_together = [("staff", "client")]


class ClientMembership(models.Model):
    """En af kundens egne brugere og dens rolle i kundens bøger."""

    ROLES = [
        ("admin", "Administrator"),   # alt, også brugere og revisoradgang
        ("accountant", "Bogholder"),  # læse og skrive
        ("viewer", "Læser"),          # kun læse
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="memberships")
    client = models.ForeignKey(ClientCompany, on_delete=models.CASCADE, related_name="memberships")
    role = models.CharField(max_length=20, choices=ROLES, default="admin")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "client_memberships"
        unique_together = [("user", "client")]

    def __str__(self):
        return f"{self.user.username} @ {self.client.slug} ({self.role})"


class AccessGrant(models.Model):
    """Kundens samtykke til, at revisorhuset arbejder i bøgerne.

    scope: read = kun læse, bookkeeping = bogføre (ikke brugere/adgang),
    full = som kundens administrator. staff_scope "all" giver alle relevante
    medarbejdere adgang; "named" kun dem i `staff`.
    En grant uden `accepted_at` er en anmodning, kunden endnu ikke har godkendt.
    """

    SCOPES = [("read", "Læse"), ("bookkeeping", "Bogføre"), ("full", "Fuld adgang")]
    STAFF_SCOPES = [("all", "Alle i Ajan Partners"), ("named", "Kun navngivne medarbejdere")]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    client = models.ForeignKey(ClientCompany, on_delete=models.CASCADE, related_name="grants")
    firm = models.ForeignKey(Firm, on_delete=models.PROTECT, related_name="grants")
    scope = models.CharField(max_length=20, choices=SCOPES, default="bookkeeping")
    staff_scope = models.CharField(max_length=10, choices=STAFF_SCOPES, default="all")
    staff = models.ManyToManyField(FirmStaff, blank=True, related_name="named_grants")
    valid_until = models.DateField(null=True, blank=True)
    requested_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True,
                                     blank=True, related_name="+")
    requested_at = models.DateTimeField(default=timezone.now)
    request_note = models.TextField(blank=True, default="")
    accepted_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True,
                                    blank=True, related_name="+")
    accepted_at = models.DateTimeField(null=True, blank=True)
    revoked_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True,
                                   blank=True, related_name="+")
    revoked_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "access_grants"
        ordering = ["-requested_at"]

    def __str__(self):
        return f"{self.client.slug}: {self.scope} ({self.state})"

    @property
    def state(self):
        if self.revoked_at:
            return "revoked"
        if not self.accepted_at:
            return "pending"
        if self.valid_until and self.valid_until < timezone.localdate():
            return "expired"
        return "active"

    @property
    def is_active(self):
        return self.state == "active"

    def covers(self, staff):
        if not self.is_active or staff is None or not staff.is_active:
            return False
        if self.staff_scope == "named":
            return self.staff.filter(pk=staff.pk).exists()
        if staff.sees_all_clients:
            return True
        return StaffAssignment.objects.filter(staff=staff, client=self.client).exists()


class FirmAuditLog(models.Model):
    """Hvem i revisorhuset var inde hos hvilken kunde, og hvad de gjorde.
    Kundens egen audit-log (core.AuditLog, hash-kædet) har detaljerne."""

    id = models.BigAutoField(primary_key=True)
    timestamp = models.DateTimeField(default=timezone.now, db_index=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name="+")
    client = models.ForeignKey(ClientCompany, on_delete=models.SET_NULL, null=True, blank=True, related_name="+")
    action = models.CharField(max_length=50)
    detail = models.JSONField(default=dict, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)

    class Meta:
        db_table = "firm_audit_log"
        ordering = ["-timestamp"]


class MFADevice(models.Model):
    """To-faktor-login (TOTP, RFC 6238) for en bruger. Hemmeligheden er krypteret
    med FIELD_ENCRYPTION_KEY; gendannelseskoder gemmes kun som hash."""

    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="mfa_device")
    secret_encrypted = models.TextField()
    confirmed_at = models.DateTimeField(null=True, blank=True)
    recovery_codes = models.JSONField(default=list, blank=True)  # sha256-hashes, fjernes når brugt
    last_used_step = models.BigIntegerField(default=0)  # forhindrer genbrug af samme kode
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "mfa_devices"

    @property
    def is_confirmed(self):
        return self.confirmed_at is not None
