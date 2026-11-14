"""Journals, journal entries and lines (double-entry bookkeeping, Loi 9-88).

An entry lives in one journal (journaux auxiliaires: BQ1..BQ4, CA, AC, VE, PA,
OD, AN). It has three states:

- draft      is_posted=False: a manual entry being written; not in the books.
- brouillard is_posted=True, validated_at empty: in the books, still editable.
- validée    validated_at set: numbered per journal and year when its month is
             closed (journals/closing.py) and never changed again. Corrections
             are made with a reversal entry (contre-passation) in an open month.

The lock is enforced here (signals) and by a database trigger (migration 0013).
"""

import uuid
from decimal import Decimal

from django.db import models

from accounts.models import Account


class Journal(models.Model):
    """Journal auxiliaire. Bank and cash journals carry their treasury account."""

    TYPE_CHOICES = [
        ("bank", "Banque"),
        ("cash", "Caisse"),
        ("purchases", "Achats"),
        ("sales", "Ventes"),
        ("payroll", "Paie"),
        ("misc", "Opérations diverses"),
        ("opening", "À-nouveaux"),
    ]

    code = models.CharField(max_length=10, unique=True)
    name = models.CharField(max_length=100)
    type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    account = models.OneToOneField(
        Account, on_delete=models.PROTECT, null=True, blank=True, related_name="journal",
    )
    currency = models.CharField(max_length=3, default="MAD")
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "journals"
        ordering = ["code"]

    def __str__(self):
        return f"{self.code} — {self.name}"


class JournalSequence(models.Model):
    """Last validated number per journal and year (no gaps; locked while numbering)."""

    journal = models.ForeignKey(Journal, on_delete=models.PROTECT, related_name="sequences")
    year = models.IntegerField()
    last_number = models.IntegerField(default=0)

    class Meta:
        db_table = "journal_sequences"
        unique_together = [("journal", "year")]


class Period(models.Model):
    """A closed month. Closing validates and numbers every entry in it."""

    year = models.IntegerField()
    month = models.IntegerField()
    closed_at = models.DateTimeField()
    closed_by = models.CharField(max_length=200, blank=True, default="")

    class Meta:
        db_table = "periods"
        unique_together = [("year", "month")]
        ordering = ["year", "month"]

    def __str__(self):
        return f"{self.year}-{self.month:02d}"


class ValidatedEntryError(Exception):
    """Raised when something tries to change a validated entry."""


class JournalEntry(models.Model):
    """Header for a double-entry journal entry."""

    SOURCE_CHOICES = [
        ("manual", "Manual"),
        ("cmr_invoice", "CMR Invoice"),
        ("cmr_payment", "CMR Payment"),
        ("invoice", "Invoice"),
        ("credit_note", "Credit Note"),
        ("expense", "Expense"),
        ("bank", "Bank"),
        ("margin_recognition", "Margin Recognition"),
        ("tva_margin", "TVA on Margin"),
        ("payroll", "Payroll"),
        ("reclass", "Reclassification"),
        ("bank_match", "Bank Match"),
        ("reversal", "Contre-passation"),
        ("opening", "À-nouveaux"),
        ("closing", "Clôture"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    journal = models.ForeignKey(Journal, on_delete=models.PROTECT, related_name="entries")
    # Draft number (BR-000001) until validated, then JOURNAL-YEAR-00001.
    entry_number = models.CharField(max_length=30, unique=True)
    piece_number = models.CharField(max_length=100, blank=True, default="")
    date = models.DateField()
    description = models.TextField(blank=True, default="")
    reference = models.CharField(max_length=200, blank=True, default="")
    source = models.CharField(max_length=20, choices=SOURCE_CHOICES, default="manual")
    source_id = models.CharField(max_length=100, blank=True, default="")
    is_posted = models.BooleanField(default=False)
    validated_at = models.DateTimeField(null=True, blank=True)
    validated_by = models.CharField(max_length=200, blank=True, default="")
    reversal_of = models.OneToOneField(
        "self", on_delete=models.PROTECT, null=True, blank=True, related_name="reversed_by",
    )
    created_by = models.CharField(max_length=200, blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "journal_entries"
        ordering = ["-date", "-entry_number"]

    def __str__(self):
        return f"{self.entry_number} — {self.date}"

    @property
    def status(self):
        if self.validated_at:
            return "validated"
        return "brouillard" if self.is_posted else "draft"

    def save(self, *args, **kwargs):
        if self.journal_id is None:
            from .journal_for import journal_for_source
            self.journal = journal_for_source(self.source)
        super().save(*args, **kwargs)

    @property
    def total_debit(self):
        return self.lines.aggregate(total=models.Sum("debit"))["total"] or Decimal("0")

    @property
    def total_credit(self):
        return self.lines.aggregate(total=models.Sum("credit"))["total"] or Decimal("0")

    @property
    def is_balanced(self):
        return self.total_debit == self.total_credit


class JournalEntryLineQuerySet(models.QuerySet):
    def in_mad(self):
        """Lines that count in dirham totals (see accounts.chart.BASE_CURRENCY)."""
        return self.filter(currency="MAD")

    def foreign(self):
        """Lines in another currency (euros not exchanged yet)."""
        return self.exclude(currency="MAD")


class JournalEntryLine(models.Model):
    """Individual debit or credit line within a journal entry."""

    objects = JournalEntryLineQuerySet.as_manager()

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    journal_entry = models.ForeignKey(
        JournalEntry,
        on_delete=models.CASCADE,
        related_name="lines",
    )
    line_no = models.PositiveIntegerField(default=0)
    account = models.ForeignKey(
        Account,
        on_delete=models.PROTECT,
        related_name="journal_lines",
    )
    debit = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    credit = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    currency = models.CharField(max_length=3, default="MAD")
    exchange_rate = models.DecimalField(max_digits=10, decimal_places=4, default=1)
    base_debit = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    base_credit = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    description = models.CharField(max_length=500, blank=True, default="")
    # Tiers (compte auxiliaire) on 3421 Clients / 4411 Fournisseurs: the local
    # Customer or Supplier id. The name is kept for statements and the CRM.
    partner_type = models.CharField(max_length=10, blank=True, default="",
                                    choices=[("", ""), ("customer", "Client"), ("supplier", "Fournisseur")])
    partner_id = models.CharField(max_length=64, blank=True, default="", db_index=True)
    partner_name = models.CharField(max_length=255, blank=True, default="")
    # Lettrage: lines of one account and tiers that settle each other share a
    # code. The only fields that may still change on a validated line.
    lettrage = models.CharField(max_length=10, blank=True, default="", db_index=True)
    lettrage_date = models.DateField(null=True, blank=True)

    LETTRAGE_FIELDS = {"lettrage", "lettrage_date"}

    class Meta:
        db_table = "journal_entry_lines"
        ordering = ["line_no", "id"]

    def __str__(self):
        return f"{self.account.code}: DR {self.debit} / CR {self.credit}"

    def save(self, *args, **kwargs):
        # Auto-compute base amounts
        self.base_debit = self.debit * self.exchange_rate
        self.base_credit = self.credit * self.exchange_rate
        if not self.line_no:
            last = (JournalEntryLine.objects.filter(journal_entry_id=self.journal_entry_id)
                    .aggregate(m=models.Max("line_no"))["m"])
            self.line_no = (last or 0) + 1
        super().save(*args, **kwargs)


class BankStatementUpload(models.Model):
    """Record of a bank statement file upload."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    filename = models.CharField(max_length=500, default="")
    bank_account = models.ForeignKey(
        Account,
        on_delete=models.CASCADE,
        related_name="statement_uploads",
    )
    date_from = models.DateField(null=True, blank=True)
    date_to = models.DateField(null=True, blank=True)
    transaction_count = models.IntegerField(default=0)
    uploaded_by = models.CharField(max_length=200, blank=True, default="")
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "bank_statement_uploads"
        ordering = ["-uploaded_at"]

    def __str__(self):
        return f"{self.filename} ({self.uploaded_at})"


class BankDescriptionMapping(models.Model):
    """Learned mapping: bank description → account.

    Saved when the user confirms bank statement transactions so that
    future uploads auto-map the same descriptions.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    description_key = models.CharField(max_length=500, unique=True, db_index=True)
    account = models.ForeignKey(
        Account,
        on_delete=models.CASCADE,
        related_name="bank_mappings",
    )
    example_description = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "bank_description_mappings"

    def __str__(self):
        return f"{self.description_key} → {self.account.code}"


class InvoiceReceipt(models.Model):
    """Money in the bank matched to a CRM invoice.

    The MAD that arrived is what the invoice is worth in the books: a foreign
    currency invoice is only booked when its money is matched here (DR bank /
    CR 71243 at the MAD received), and a MAD invoice's receivable (3421) is
    cleared by it. One bank line may pay several invoices, one invoice may be paid
    by several lines (deposit + balance); `covered_amount` is the part of the
    invoice, in the invoice's currency, that this receipt settles.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    journal_entry_line = models.ForeignKey(
        JournalEntryLine, on_delete=models.CASCADE, related_name="invoice_receipts",
    )
    cmr_invoice_id = models.CharField(max_length=36, db_index=True)
    invoice_number = models.CharField(max_length=50, blank=True, default="")
    customer_name = models.CharField(max_length=255, blank=True, default="")
    trip_reference = models.CharField(max_length=50, blank=True, default="")
    currency = models.CharField(max_length=3, default="MAD")
    invoice_total = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    covered_amount = models.DecimalField(max_digits=15, decimal_places=2)
    # Empty while the money sits in euros on the EUR account (51413): it is
    # booked at the MAD it fetches when it is exchanged. An exchange is its own
    # receipt on the MAD line, pointing back here with `exchanged_from`.
    amount_mad = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    exchanged_from = models.ForeignKey(
        "self", on_delete=models.PROTECT, null=True, blank=True, related_name="exchanges",
    )
    matched_by = models.CharField(max_length=200, blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "invoice_receipts"
        ordering = ["created_at"]

    @property
    def awaiting_exchange(self):
        return self.amount_mad is None

    @property
    def rate(self):
        if self.amount_mad is None or not self.covered_amount:
            return None
        return self.amount_mad / self.covered_amount

    def __str__(self):
        return f"{self.invoice_number}: {self.covered_amount} {self.currency} = {self.amount_mad} MAD"
