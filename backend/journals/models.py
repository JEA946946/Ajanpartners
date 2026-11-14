"""Journaler, posteringer og linjer (dobbelt bogholderi, Bogføringsloven).

En postering ligger i én journal (BANK pr. bankkonto, KAS, KØB, SALG, LØN, DIV,
PRIMO, ÅA). Den har tre tilstande:

- kladde     is_posted=False: en manuel postering under udarbejdelse; ikke i bøgerne.
- bogført    is_posted=True, validated_at tom: i bøgerne, kan stadig rettes.
- valideret  validated_at sat: nummereret fortløbende pr. journal og år, når
             måneden lukkes (journals/closing.py), og ændres aldrig igen.
             Rettelser sker med en tilbageføring i en åben måned.

Låsen håndhæves her (signaler) og af en databasetrigger (migration 0013/0015/0017).

Beløb: debit/credit er altid i DKK (funktionel valuta). Er bilaget i fremmed
valuta, står valutaen i `currency`, kursen i `exchange_rate` (DKK pr. 1 enhed)
og beløbet i valutaen i `amount_currency` (fortegn som debet − kredit).
"""

import uuid
from decimal import Decimal

from django.db import models

from accounts.models import Account


class Journal(models.Model):
    """Journal. Bank- og kassejournaler har deres likvidkonto."""

    TYPE_CHOICES = [
        ("bank", "Bank"),
        ("cash", "Kasse"),
        ("purchases", "Køb"),
        ("sales", "Salg"),
        ("payroll", "Løn"),
        ("misc", "Diverse"),
        ("opening", "Primo"),
        ("closing", "Årsafslutning"),
    ]

    code = models.CharField(max_length=10, unique=True)
    name = models.CharField(max_length=100)
    type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    account = models.OneToOneField(
        Account, on_delete=models.PROTECT, null=True, blank=True, related_name="journal",
    )
    currency = models.CharField(max_length=3, default="DKK")
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
        ("manual", "Manuel"),
        ("invoice", "Faktura"),
        ("credit_note", "Kreditnota"),
        ("reminder", "Rykker"),
        ("expense", "Regning/udgift"),
        ("bank", "Bank"),
        ("payroll", "Løn"),
        ("reclass", "Omposteringer"),
        ("bank_match", "Bankafstemning"),
        ("vat_settlement", "Momsafregning"),
        ("fx", "Kursdifference"),
        ("reversal", "Tilbageføring"),
        ("opening", "Primo"),
        ("closing", "Årsafslutning"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    journal = models.ForeignKey(Journal, on_delete=models.PROTECT, related_name="entries")
    # Kladdenummer (KL-000001) indtil valideret, derefter JOURNAL-ÅR-00001.
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
        return "posted" if self.is_posted else "draft"

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
    def in_base(self):
        """Linjer, der tæller i DKK-totaler: alle (debit/credit er altid DKK)."""
        return self.all()

    def foreign(self):
        """Linjer, hvis bilag er i fremmed valuta."""
        return self.exclude(currency="DKK")


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
    currency = models.CharField(max_length=3, default="DKK")
    # DKK pr. 1 enhed af `currency` (1 for DKK).
    exchange_rate = models.DecimalField(max_digits=12, decimal_places=6, default=1)
    # Beløbet i bilagets valuta, med fortegn (debet positiv, kredit negativ).
    # Tomt for DKK-linjer.
    amount_currency = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    # Kopi af debit/credit (DKK). Bevares for SAF-T og bagudkompatibilitet.
    base_debit = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    base_credit = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    # Momskode (core.TaxCode.code), som linjen er bogført med. Bruges til
    # momsangivelsens rubrikker og til SAF-T.
    vat_code = models.CharField(max_length=20, blank=True, default="", db_index=True)
    description = models.CharField(max_length=500, blank=True, default="")
    # Debitor/kreditor på debitor- og kreditorkontoen: Customer- eller Supplier-id.
    partner_type = models.CharField(max_length=10, blank=True, default="",
                                    choices=[("", ""), ("customer", "Debitor"), ("supplier", "Kreditor")])
    partner_id = models.CharField(max_length=64, blank=True, default="", db_index=True)
    partner_name = models.CharField(max_length=255, blank=True, default="")
    # Udligning: linjer på samme konto og debitor/kreditor, der udligner
    # hinanden, deler en kode. De eneste felter, der må ændres på en valideret linje.
    lettrage = models.CharField(max_length=10, blank=True, default="", db_index=True)
    lettrage_date = models.DateField(null=True, blank=True)

    LETTRAGE_FIELDS = {"lettrage", "lettrage_date"}

    class Meta:
        db_table = "journal_entry_lines"
        ordering = ["line_no", "id"]

    def __str__(self):
        return f"{self.account.code}: DR {self.debit} / CR {self.credit}"

    def save(self, *args, **kwargs):
        # debit/credit er DKK; base_* er en kopi (beholdt for triggerens rækkesammenligning).
        if not self.currency:
            self.currency = "DKK"
        if self.currency == "DKK":
            self.exchange_rate = 1
            self.amount_currency = None
        self.base_debit = self.debit
        self.base_credit = self.credit
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
