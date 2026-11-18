"""Revisorhusets egne data (public-skemaet): opgaver, bilagsforespørgsler og
kommentarer pr. konto. Kunden ser kun opgaver, der er markeret som synlige
for kunden, og kun sine egne (via request.tenant)."""

import uuid

from django.conf import settings
from django.db import models


class FirmTask(models.Model):
    KINDS = [
        ("bilag_mangler", "Bilag mangler"),
        ("spoergsmaal", "Spørgsmål"),
        ("opgave", "Opgave"),
    ]
    STATUS = [
        ("open", "Afventer kunden"),
        ("answered", "Kunden har svaret"),
        ("in_progress", "Under behandling"),
        ("closed", "Lukket"),
    ]
    REF_TYPES = [("", "Ingen"), ("entry", "Postering"), ("bank_line", "Banklinje"), ("document", "Bilag")]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    client = models.ForeignKey("tenancy.ClientCompany", on_delete=models.CASCADE, related_name="firm_tasks")
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, default="")
    kind = models.CharField(max_length=20, choices=KINDS, default="spoergsmaal")
    reference_type = models.CharField(max_length=20, choices=REF_TYPES, blank=True, default="")
    reference_id = models.CharField(max_length=100, blank=True, default="")  # id i kundens skema
    reference_label = models.CharField(max_length=255, blank=True, default="")  # fx "Bilag 123, 1.250,00 kr."
    status = models.CharField(max_length=20, choices=STATUS, default="open")
    visible_to_client = models.BooleanField(default=True)
    assigned_to = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
                                    related_name="firm_tasks")
    due_date = models.DateField(null=True, blank=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
                                   related_name="+")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    closed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "firm_tasks"
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["client", "status"])]

    def __str__(self):
        return f"{self.client.slug}: {self.title}"


class TaskMessage(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    task = models.ForeignKey(FirmTask, on_delete=models.CASCADE, related_name="messages")
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name="+")
    from_firm = models.BooleanField(default=True)
    body = models.TextField()
    document_id = models.CharField(max_length=100, blank=True, default="")  # core.Document i kundens skema
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "firm_task_messages"
        ordering = ["created_at"]


class AccountComment(models.Model):
    """Revisorens arbejdspapir: en kommentar til en konto i kundens kontoplan."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    client = models.ForeignKey("tenancy.ClientCompany", on_delete=models.CASCADE, related_name="account_comments")
    account_code = models.CharField(max_length=20)
    fiscal_year = models.IntegerField(null=True, blank=True)  # regnskabsåret, der slutter i dette kalenderår
    body = models.TextField()
    resolved = models.BooleanField(default=False)
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name="+")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "firm_account_comments"
        ordering = ["account_code", "-created_at"]
        indexes = [models.Index(fields=["client", "account_code"])]


# ─── Hvidvask: kundekendskab (KYC) ───────────────────────────────────────────
# Revisorhusets egen dokumentation efter hvidvaskloven. Ligger i public-skemaet og
# vises aldrig for kunden (heller ikke i kundens eksport). Hjemmel er kontrolleret
# i docs/skabeloner-verifikation/opdrag-hvidvask.md.

def kyc_upload_to(instance, filename):
    return f"kyc/{instance.client.slug}/{filename}"


class KycPerson(models.Model):
    """Reel ejer, ledelsesmedlem, tegningsberettiget eller person, der handler på kundens vegne
    (HVL § 2, nr. 9; § 11, stk. 1-2). Der gemmes ikke CPR-nummer – kun fødselsdato."""

    ROLES = [
        ("reel_ejer", "Reel ejer"),
        ("ledelse", "Ledelse"),
        ("tegningsberettiget", "Tegningsberettiget"),
        ("fuldmagt", "Handler på kundens vegne"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    client = models.ForeignKey("tenancy.ClientCompany", on_delete=models.CASCADE, related_name="kyc_persons")
    role = models.CharField(max_length=20, choices=ROLES)
    name = models.CharField(max_length=255)
    birth_date = models.DateField(null=True, blank=True)
    country = models.CharField(max_length=100, blank=True, default="")  # bopælsland
    ownership = models.CharField(max_length=100, blank=True, default="")  # fx "60 % af kapital og stemmer"
    is_pep = models.BooleanField(default=False)
    pep_note = models.TextField(blank=True, default="")
    id_method = models.CharField(max_length=255, blank=True, default="")  # fx "Pas kontrolleret ved møde"
    id_document = models.FileField(upload_to=kyc_upload_to, blank=True)
    verified_on = models.DateField(null=True, blank=True)
    verified_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
                                    related_name="+")
    active = models.BooleanField(default=True)  # False = ikke længere ejer/leder (bevares som historik)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "firm_kyc_persons"
        ordering = ["role", "name"]


class KycAssessment(models.Model):
    """Kundens risikovurdering. En godkendt vurdering er låst; en ny vurdering er en ny version."""

    LEVELS = [("lav", "Lav"), ("normal", "Normal"), ("hoej", "Høj")]
    STATUS = [("kladde", "Kladde"), ("godkendt", "Godkendt")]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    client = models.ForeignKey("tenancy.ClientCompany", on_delete=models.CASCADE, related_name="kyc_assessments")
    version = models.IntegerField()
    risk_level = models.CharField(max_length=10, choices=LEVELS, default="normal")
    purpose = models.TextField(blank=True, default="")          # formål og tilsigtet beskaffenhed (§ 11, stk. 1, nr. 4)
    source_of_funds = models.TextField(blank=True, default="")  # midlernes oprindelse (krav ved PEP, § 18)
    reasons = models.TextField(blank=True, default="")          # revisorens begrundelse
    answers = models.JSONField(default=dict, blank=True)        # svar på spørgsmålene i KYC_QUESTIONS
    industry_snapshot = models.JSONField(default=dict, blank=True)  # brancheforslag på vurderingstidspunktet
    next_review_on = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=10, choices=STATUS, default="kladde")
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name="+")
    created_at = models.DateTimeField(auto_now_add=True)
    approved_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
                                    related_name="+")
    approved_at = models.DateTimeField(null=True, blank=True)
    sha256 = models.CharField(max_length=64, blank=True, default="")  # af indholdet ved godkendelse

    class Meta:
        db_table = "firm_kyc_assessments"
        ordering = ["-version"]
        unique_together = [("client", "version")]


class AmlReport(models.Model):
    """Intern registrering af en underretning til Hvidvasksekretariatet (HVL § 26).
    Kun partnere kan se dem. Kunden må ikke orienteres (HVL § 38, stk. 1)."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    client = models.ForeignKey("tenancy.ClientCompany", on_delete=models.PROTECT, related_name="+")
    summary = models.TextField()
    reported_on = models.DateField(null=True, blank=True)  # tom = under overvejelse
    reference = models.CharField(max_length=200, blank=True, default="")  # sekretariatets journalnr.
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name="+")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "firm_aml_reports"
        ordering = ["-created_at"]


# ─── Kundeaccept og uafhængighed (BEK 512/2024 § 3, stk. 1, nr. 3-4; BEK 520/2024) ──

class ClientAcceptance(models.Model):
    """Accept eller fortsættelse af klientforhold/opgave. Godkendt = låst (sha256)."""

    KINDS = [("accept", "Accept af ny kunde/opgave"), ("fortsaettelse", "Fortsættelse")]
    STATUS = [("kladde", "Kladde"), ("godkendt", "Godkendt"), ("afvist", "Afvist")]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    client = models.ForeignKey("tenancy.ClientCompany", on_delete=models.CASCADE, related_name="acceptances")
    kind = models.CharField(max_length=15, choices=KINDS, default="accept")
    engagement_text = models.CharField(max_length=255, blank=True, default="")  # fx "Opstilling 2026"
    answers = models.JSONField(default=dict, blank=True)
    conclusion = models.TextField(blank=True, default="")
    checklist_version = models.CharField(max_length=20, blank=True, default="")
    status = models.CharField(max_length=10, choices=STATUS, default="kladde")
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name="+")
    created_at = models.DateTimeField(auto_now_add=True)
    approved_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
                                    related_name="+")
    approved_at = models.DateTimeField(null=True, blank=True)
    sha256 = models.CharField(max_length=64, blank=True, default="")

    class Meta:
        db_table = "firm_client_acceptances"
        ordering = ["-created_at"]


class IndependenceDeclaration(models.Model):
    """Medarbejderens årlige erklæring. Underskrevet = låst; nye forhold registreres som IndependenceConflict."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    staff = models.ForeignKey("tenancy.FirmStaff", on_delete=models.CASCADE, related_name="declarations")
    year = models.IntegerField()
    answers = models.JSONField(default=dict, blank=True)
    checklist_version = models.CharField(max_length=20, blank=True, default="")
    signed_at = models.DateTimeField(default=None, null=True, blank=True)
    sha256 = models.CharField(max_length=64, blank=True, default="")

    class Meta:
        db_table = "firm_independence_declarations"
        unique_together = [("staff", "year")]
        ordering = ["-year"]


class IndependenceConflict(models.Model):
    """Et konkret forhold mellem en medarbejder og en kunde. Mens det er uafklaret, kan medarbejderen
    ikke tildeles kunden (BEK 520/2024 § 3, stk. 3, og § 4, stk. 2)."""

    RESOLUTIONS = [
        ("fjernet", "Fjernet fra opgaven / udelukket fra beslutninger"),
        ("afhaendet", "Økonomisk interesse afhændet / forhold ophørt"),
        ("sikkerhed", "Sikkerhedsforanstaltninger truffet (andre trusler, § 7)"),
        ("afstaa", "Huset afstår fra opgaven"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    declaration = models.ForeignKey(IndependenceDeclaration, on_delete=models.CASCADE, related_name="conflicts")
    client = models.ForeignKey("tenancy.ClientCompany", on_delete=models.CASCADE, related_name="independence_conflicts")
    question_id = models.CharField(max_length=40)
    note = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)
    resolution = models.CharField(max_length=15, choices=RESOLUTIONS, blank=True, default="")
    resolution_note = models.TextField(blank=True, default="")
    resolved_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
                                    related_name="+")
    resolved_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "firm_independence_conflicts"
        ordering = ["-created_at"]


# ─── Opdrag og kvalitetsstyring (BEK 512/2024 § 3, stk. 1, nr. 5 og 8) ─────────

class Engagement(models.Model):
    """Et opdrag for en kunde og et regnskabsår (eller en periode)."""

    KINDS = [
        ("revision", "Revision"),
        ("udvidet_gennemgang", "Udvidet gennemgang"),
        ("review", "Review"),
        ("opstilling", "Opstilling (assistance)"),
        ("aftalte_handlinger", "Aftalte arbejdshandlinger"),
        ("skat", "Skat (selvangivelse)"),
        ("loen", "Løn"),
        ("bogfoering", "Bogføring"),
        ("raadgivning", "Rådgivning"),
    ]
    STATUS = [
        ("planlagt", "Planlagt"),
        ("i_gang", "I gang"),
        ("review", "Til gennemgang"),
        ("afsluttet", "Godkendt"),
        ("leveret", "Leveret"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    client = models.ForeignKey("tenancy.ClientCompany", on_delete=models.CASCADE, related_name="engagements")
    kind = models.CharField(max_length=20, choices=KINDS)
    title = models.CharField(max_length=255, blank=True, default="")
    year_start = models.DateField(null=True, blank=True)
    year_end = models.DateField(null=True, blank=True)
    partner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
                                related_name="+")
    manager = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
                                related_name="+")
    status = models.CharField(max_length=12, choices=STATUS, default="planlagt")
    deadline = models.DateField(null=True, blank=True)
    budget_hours = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    acceptance = models.ForeignKey(ClientAcceptance, on_delete=models.SET_NULL, null=True, blank=True,
                                   related_name="engagements")
    note = models.TextField(blank=True, default="")
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name="+")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "firm_engagements"
        ordering = ["deadline", "client__name"]
        indexes = [models.Index(fields=["client", "status"])]


class ChecklistRun(models.Model):
    """En udfyldt tjekliste til et opdrag. Punkterne er trukket ud af en verificeret skabelon
    (linjer med "- [ ]"), flettet for kunden og året – systemet tilføjer ikke selv punkter."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    engagement = models.ForeignKey(Engagement, on_delete=models.CASCADE, related_name="checklists")
    template_id = models.CharField(max_length=100)
    title = models.CharField(max_length=255)
    template_sha256 = models.CharField(max_length=64, blank=True, default="")  # af skabelonfilen ved oprettelse
    values = models.JSONField(default=dict, blank=True)  # skabelonens felter (fx mikro)
    items = models.JSONField(default=list, blank=True)   # [{id, section, text, status, note, by, at}]
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "firm_checklist_runs"
        ordering = ["created_at"]


class Signoff(models.Model):
    """Udført af / gennemgået af / godkendt af (BEK 512/2024 § 3, stk. 1, nr. 5)."""

    STEPS = [("udfoert", "Udført"), ("gennemgaaet", "Gennemgået"), ("godkendt", "Godkendt")]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    engagement = models.ForeignKey(Engagement, on_delete=models.CASCADE, related_name="signoffs")
    step = models.CharField(max_length=12, choices=STEPS)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="+")
    note = models.TextField(blank=True, default="")
    at = models.DateTimeField(auto_now_add=True)
    revoked_at = models.DateTimeField(null=True, blank=True)  # fortrydes ved genåbning – slettes ikke
    revoked_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
                                   related_name="+")

    class Meta:
        db_table = "firm_signoffs"
        ordering = ["at"]


class QualityLog(models.Model):
    """Konsultationer, klager, hændelser og den årlige evaluering af kvalitetsstyringssystemet
    (BEK 512/2024 § 3, stk. 1, nr. 8, og stk. 3-4)."""

    KINDS = [
        ("konsultation", "Konsultation"),
        ("klage", "Klage"),
        ("haendelse", "Hændelse / mulig overtrædelse"),
        ("evaluering", "Årlig evaluering af kvalitetsstyringssystemet"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    kind = models.CharField(max_length=15, choices=KINDS)
    client = models.ForeignKey("tenancy.ClientCompany", on_delete=models.SET_NULL, null=True, blank=True, related_name="+")
    engagement = models.ForeignKey(Engagement, on_delete=models.SET_NULL, null=True, blank=True, related_name="+")
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, default="")
    follow_up = models.TextField(blank=True, default="")  # opfølgning/afhjælpning (§ 3, stk. 4)
    closed_at = models.DateTimeField(null=True, blank=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name="+")
    created_at = models.DateTimeField(auto_now_add=True)
    closed_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
                                  related_name="+")

    class Meta:
        db_table = "firm_quality_log"
        ordering = ["-created_at"]
