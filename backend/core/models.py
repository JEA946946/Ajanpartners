"""Core models: TaxCode, Payment, BankRule, BankReconciliation, Project, Document, AuditLog, CompanySettings, UserRole."""

import uuid

from django.conf import settings
from django.db import models
from django.utils import timezone

from accounts.models import Account


class TaxCode(models.Model):
    """Momskode. Koderne følger Erhvervsstyrelsens momskodeliste (S01, K010 …),
    se core/vat_codes.py. Hvordan en kode bogføres, står i core/vat.py."""

    TYPE_CHOICES = [
        ("sales", "Salg"),
        ("purchase", "Køb"),
        ("both", "Begge"),
    ]
    # Rubrik på momsangivelsen for linjens beløb uden moms.
    RUBRIK_CHOICES = [
        ("", "Ingen"),
        ("A_goods", "Rubrik A – varer (køb i EU)"),
        ("A_services", "Rubrik A – ydelser (køb i EU)"),
        ("B_goods", "Rubrik B – varer (EU-salg, indberettes)"),
        ("B_goods_other", "Rubrik B – varer (indberettes ikke til EU-salg uden moms)"),
        ("B_services", "Rubrik B – ydelser (EU-salg)"),
        ("C", "Rubrik C – andre leverancer uden moms"),
    ]
    REVERSE_CHOICES = [
        ("", "Nej"),
        ("eu_goods", "Varekøb fra udlandet (erhvervelses-/importmoms)"),
        ("eu_services", "Ydelseskøb fra udlandet"),
        ("domestic", "Indenlandsk omvendt betalingspligt (fx byggeydelser)"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    code = models.CharField(max_length=20, unique=True)
    name = models.CharField(max_length=100)
    rate = models.DecimalField(max_digits=5, decimal_places=2, help_text="Procent")
    type = models.CharField(max_length=10, choices=TYPE_CHOICES, default="both")
    # Momskontoen: salgsmoms for salg, købsmoms for almindelige køb, og den
    # udgående side (7700/7720/7680) ved omvendt betalingspligt.
    account = models.ForeignKey(
        Account, on_delete=models.PROTECT, related_name="tax_codes"
    )
    # Ved omvendt betalingspligt: kontoen for den fradragsberettigede del (købsmoms).
    input_account = models.ForeignKey(
        Account, on_delete=models.PROTECT, null=True, blank=True, related_name="tax_codes_input"
    )
    # Andel af momsen, der kan fratrækkes (100 = fuldt fradrag, 25 = repræsentation).
    deduction_rate = models.DecimalField(max_digits=5, decimal_places=2, default=100)
    reverse_charge = models.CharField(max_length=12, choices=REVERSE_CHOICES, blank=True, default="")
    rubrik = models.CharField(max_length=16, choices=RUBRIK_CHOICES, blank=True, default="")
    # Energiafgift: hele linjens beløb bogføres på afgiftskontoen (godtgørelse).
    energy_tax = models.BooleanField(default=False)
    # Tekst på fakturaen (fx "Omvendt betalingspligt", momslovens henvisning).
    invoice_text = models.CharField(max_length=200, blank=True, default="")
    # Standardmomskode til SAF-T (Erhvervsstyrelsens liste); tom for egne koder.
    standard_code = models.CharField(max_length=20, blank=True, default="")
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "tax_codes"
        ordering = ["code"]

    def __str__(self):
        return f"{self.code} — {self.name} ({self.rate}%)"


class Payment(models.Model):
    """Payment record (incoming or outgoing)."""

    TYPE_CHOICES = [
        ("incoming", "Incoming"),
        ("outgoing", "Outgoing"),
    ]

    METHOD_CHOICES = [
        ("bank_transfer", "Bank Transfer"),
        ("cash", "Cash"),
        ("card", "Card"),
        ("check", "Check"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    payment_number = models.CharField(max_length=20, unique=True)
    type = models.CharField(max_length=10, choices=TYPE_CHOICES)
    date = models.DateField()
    amount = models.DecimalField(max_digits=15, decimal_places=2)
    currency = models.CharField(max_length=3, default="DKK")
    method = models.CharField(max_length=20, choices=METHOD_CHOICES, default="bank_transfer")
    reference = models.CharField(max_length=200, blank=True, default="")
    bank_account = models.ForeignKey(
        Account,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="payments_as_bank",
    )
    customer = models.ForeignKey(
        "sales.Customer",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="payments",
    )
    supplier = models.ForeignKey(
        "purchases.Supplier",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="payments",
    )
    journal_entry = models.ForeignKey(
        "journals.JournalEntry",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="payments",
    )
    notes = models.TextField(blank=True, default="")
    created_by = models.CharField(max_length=200, blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "payments"
        ordering = ["-date", "-payment_number"]

    def __str__(self):
        return f"{self.payment_number} — {self.type} {self.amount}"


class PaymentAllocation(models.Model):
    """Allocation of a payment to an invoice, bill, or credit note."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    payment = models.ForeignKey(
        Payment, on_delete=models.CASCADE, related_name="allocations"
    )
    content_type = models.CharField(
        max_length=20,
        choices=[
            ("invoice", "Invoice"),
            ("bill", "Bill"),
            ("credit_note", "Credit Note"),
        ],
    )
    object_id = models.UUIDField()
    amount = models.DecimalField(max_digits=15, decimal_places=2)

    class Meta:
        db_table = "payment_allocations"

    def __str__(self):
        return f"{self.payment.payment_number} → {self.content_type}:{self.object_id} ({self.amount})"


class BankRule(models.Model):
    """Rule for auto-matching bank statement transactions."""

    MATCH_TYPE_CHOICES = [
        ("contains", "Contains"),
        ("regex", "Regex"),
    ]
    MATCH_FIELD_CHOICES = [
        ("description", "Description"),
        ("reference", "Reference"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    pattern = models.CharField(max_length=500)
    match_type = models.CharField(max_length=10, choices=MATCH_TYPE_CHOICES, default="contains")
    match_field = models.CharField(max_length=20, choices=MATCH_FIELD_CHOICES, default="description")
    account = models.ForeignKey(
        Account, on_delete=models.PROTECT, related_name="bank_rules"
    )
    description_template = models.CharField(max_length=500, blank=True, default="")
    priority = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "bank_rules"
        ordering = ["-priority", "pattern"]

    def __str__(self):
        return f"{self.pattern} → {self.account.code}"


class BankReconciliation(models.Model):
    """Bank reconciliation session."""

    STATUS_CHOICES = [
        ("in_progress", "In Progress"),
        ("completed", "Completed"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    bank_account = models.ForeignKey(
        Account, on_delete=models.PROTECT, related_name="reconciliations"
    )
    date = models.DateField()
    statement_balance = models.DecimalField(max_digits=15, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="in_progress")
    completed_at = models.DateTimeField(null=True, blank=True)
    completed_by = models.CharField(max_length=200, blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "bank_reconciliations"
        ordering = ["-date"]

    def __str__(self):
        return f"Recon {self.bank_account.code} — {self.date}"


class BankReconciliationLine(models.Model):
    """Individual line within a bank reconciliation."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    reconciliation = models.ForeignKey(
        BankReconciliation, on_delete=models.CASCADE, related_name="lines"
    )
    journal_line = models.ForeignKey(
        "journals.JournalEntryLine",
        on_delete=models.CASCADE,
        related_name="reconciliation_lines",
    )
    is_matched = models.BooleanField(default=False)
    matched_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "bank_reconciliation_lines"

    def __str__(self):
        return f"Line {self.journal_line_id} — matched={self.is_matched}"


class Project(models.Model):
    """Project for tracking costs and revenue."""

    STATUS_CHOICES = [
        ("active", "Active"),
        ("completed", "Completed"),
        ("cancelled", "Cancelled"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    code = models.CharField(max_length=20, unique=True)
    name = models.CharField(max_length=255)
    customer = models.ForeignKey(
        "sales.Customer",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="projects",
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="active")
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    budget = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    notes = models.TextField(blank=True, default="")
    created_by = models.CharField(max_length=200, blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "projects"
        ordering = ["code"]

    def __str__(self):
        return f"{self.code} — {self.name}"


class ProjectTransaction(models.Model):
    """Links a journal entry line to a project."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    project = models.ForeignKey(
        Project, on_delete=models.CASCADE, related_name="transactions"
    )
    journal_line = models.ForeignKey(
        "journals.JournalEntryLine",
        on_delete=models.CASCADE,
        related_name="project_transactions",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "project_transactions"
        unique_together = [("project", "journal_line")]

    def __str__(self):
        return f"{self.project.code} — {self.journal_line_id}"


class Document(models.Model):
    """Uploaded document linked to various records."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    file = models.FileField(upload_to="documents/")
    filename = models.CharField(max_length=500)
    description = models.CharField(max_length=500, blank=True, default="")
    # Bilag: nummer og SHA-256 af filen som uploadet, så en udskiftet fil kan
    # kendes (opbevares i 5 år, Bogføringsloven § 10).
    piece_number = models.CharField(max_length=100, blank=True, default="")
    sha256 = models.CharField(max_length=64, blank=True, default="")
    size = models.BigIntegerField(default=0)
    journal_entry = models.ForeignKey(
        "journals.JournalEntry",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="documents",
    )
    invoice = models.ForeignKey(
        "sales.Invoice",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="documents",
    )
    bill = models.ForeignKey(
        "purchases.Bill",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="documents",
    )
    expense = models.ForeignKey(
        "purchases.Expense",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="documents",
    )
    uploaded_by = models.CharField(max_length=200, blank=True, default="")
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "documents"
        ordering = ["-uploaded_at"]

    def __str__(self):
        return self.filename


class AuditLogChangedError(Exception):
    """Raised when something tries to change or delete an audit log row."""


class AuditLog(models.Model):
    """Audit trail for all changes. Append-only and hash-chained: each row stores
    the hash of the row before it, so a changed or removed row breaks the chain
    (core/audit.py verify_chain). A database trigger refuses UPDATE and DELETE."""

    ACTION_CHOICES = [
        ("create", "Create"),
        ("update", "Update"),
        ("delete", "Delete"),
        ("post", "Post"),
        ("unpost", "Unpost"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="audit_logs",
    )
    action = models.CharField(max_length=10, choices=ACTION_CHOICES)
    model_name = models.CharField(max_length=50)
    record_id = models.CharField(max_length=100)
    changes = models.JSONField(default=dict, blank=True)
    timestamp = models.DateTimeField(default=timezone.now)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    seq = models.BigIntegerField(unique=True, null=True)
    prev_hash = models.CharField(max_length=64, blank=True, default="")
    hash = models.CharField(max_length=64, blank=True, default="")

    class Meta:
        db_table = "audit_logs"
        ordering = ["-timestamp"]

    def __str__(self):
        return f"{self.action} {self.model_name}:{self.record_id}"

    def save(self, *args, **kwargs):
        if not self._state.adding:
            raise AuditLogChangedError("Audit log rows cannot be changed")
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise AuditLogChangedError("Audit log rows cannot be deleted")


class CompanySettings(models.Model):
    """Company-wide settings (singleton)."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    company_name = models.CharField(max_length=255, default="")
    address = models.TextField(blank=True, default="")
    city = models.CharField(max_length=100, blank=True, default="")
    country = models.CharField(max_length=100, blank=True, default="Danmark")
    tax_id = models.CharField(max_length=50, blank=True, default="")
    phone = models.CharField(max_length=50, blank=True, default="")
    email = models.EmailField(blank=True, default="")
    currency = models.CharField(max_length=3, default="DKK")
    # Fakturaoplysninger (momsbekendtgørelsens § 58, FI-kort).
    bank_reg_no = models.CharField(max_length=4, blank=True, default="")
    bank_account_no = models.CharField(max_length=20, blank=True, default="")
    iban = models.CharField(max_length=34, blank=True, default="")
    bic = models.CharField(max_length=11, blank=True, default="")
    # FI-kreditornummer (8 cifre) til FI-kort type +71.
    fi_creditor_no = models.CharField(max_length=8, blank=True, default="")
    gln = models.CharField(max_length=13, blank=True, default="")
    default_payment_terms = models.CharField(max_length=20, blank=True, default="net14")
    invoice_footer = models.TextField(blank=True, default="")
    # Rykkere (renteloven § 9 b: højst 100 kr. pr. rykker, højst 3 rykkere,
    # mindst 10 dage mellem dem).
    reminder_fee = models.DecimalField(max_digits=10, decimal_places=2, default=100)
    reminder_interval_days = models.IntegerField(default=10)
    fiscal_year_start_month = models.IntegerField(default=1)
    date_format = models.CharField(max_length=20, default="DD-MM-YYYY")
    logo = models.FileField(upload_to="logos/", blank=True, null=True)
    # Base64 data-URL logos stored in the DB (survive container redeploys, no
    # media server needed). logo1 = site, logo2 = invoice, logo3 = reserved.
    logo1 = models.TextField(blank=True, default="")
    logo2 = models.TextField(blank=True, default="")
    logo3 = models.TextField(blank=True, default="")

    class Meta:
        db_table = "company_settings"

    def __str__(self):
        return self.company_name or "Company Settings"


class VatReturn(models.Model):
    """Momsangivelse for én periode. Angivet (filed) låser perioden: ingen
    postering må dateres i den (journals/periods.py)."""

    STATUS_CHOICES = [
        ("draft", "Kladde"),
        ("filed", "Angivet"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    period_start = models.DateField()
    period_end = models.DateField()
    period_type = models.CharField(max_length=10, default="quarter")  # month/quarter/half
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default="draft")
    # Felternes værdier, som de var ved bogføring/angivelse (core/vat.py FIELDS).
    fields = models.JSONField(default=dict, blank=True)
    settlement_entry = models.ForeignKey(
        "journals.JournalEntry", on_delete=models.PROTECT, null=True, blank=True,
        related_name="vat_returns",
    )
    filed_at = models.DateTimeField(null=True, blank=True)
    filed_by = models.CharField(max_length=200, blank=True, default="")
    # Kvitteringsnummer fra Skat (TastSelv eller system-til-system).
    receipt_number = models.CharField(max_length=100, blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "vat_returns"
        ordering = ["-period_start"]
        unique_together = [("period_start", "period_end")]

    def __str__(self):
        return f"Moms {self.period_start}–{self.period_end} ({self.status})"


class UserRole(models.Model):
    """User role assignment (one-to-one)."""

    ROLE_CHOICES = [
        ("admin", "Admin"),
        ("accountant", "Accountant"),
        ("viewer", "Viewer"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="role",
    )
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default="viewer")

    class Meta:
        db_table = "user_roles"

    def __str__(self):
        return f"{self.user.username} — {self.role}"
