"""Salg: debitorer, tilbud, fakturaer, kreditnotaer og rykkere.

Fakturaen opfylder momsbekendtgørelsens § 58 (sales/invoice_rules.py): dato,
fortløbende nummer (gives ved bogføring), sælgers CVR/SE, købers navn og adresse
(og købers momsnummer ved EU-B2B), leveringsdato, mængde og art, pris uden moms,
momssats og momsbeløb, og "Omvendt betalingspligt", når køber skal betale momsen.
"""

import uuid
from decimal import Decimal

from django.db import models

from accounts.models import Account


PAYMENT_TERMS = [
    ("net8", "Netto 8 dage", "net", 8),
    ("net14", "Netto 14 dage", "net", 14),
    ("net30", "Netto 30 dage", "net", 30),
    ("lm15", "Løbende måned + 15 dage", "lm", 15),
    ("lm30", "Løbende måned + 30 dage", "lm", 30),
    ("cash", "Kontant", "net", 0),
]
PAYMENT_TERMS_CHOICES = [(code, name) for code, name, _, _ in PAYMENT_TERMS]


class Customer(models.Model):
    """Debitor."""

    VAT_ZONE_CHOICES = [
        ("dk", "Danmark"),
        ("eu", "EU (uden for Danmark)"),
        ("abroad", "Uden for EU"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    code = models.CharField(max_length=20, unique=True)
    name = models.CharField(max_length=255)
    email = models.EmailField(blank=True, default="")
    phone = models.CharField(max_length=50, blank=True, default="")
    address = models.TextField(blank=True, default="")
    postal_code = models.CharField(max_length=10, blank=True, default="")
    city = models.CharField(max_length=100, blank=True, default="")
    country = models.CharField(max_length=2, blank=True, default="DK", help_text="ISO 3166-1 alpha-2")
    # CVR/SE-nummer (DK) eller momsnummer (EU, fx DE123456789).
    tax_id = models.CharField(max_length=50, blank=True, default="")
    vat_zone = models.CharField(max_length=6, choices=VAT_ZONE_CHOICES, default="dk")
    is_business = models.BooleanField(default=True)
    # Offentlig kunde: EAN/GLN-nummer (13 cifre) til e-faktura (NemHandel).
    is_public = models.BooleanField(default=False)
    ean = models.CharField(max_length=13, blank=True, default="")
    currency = models.CharField(max_length=3, default="DKK")
    payment_terms = models.IntegerField(default=14, help_text="Dage til forfald (bruges ved netto)")
    payment_terms_code = models.CharField(max_length=10, choices=PAYMENT_TERMS_CHOICES, default="net14")
    credit_limit = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    notes = models.TextField(blank=True, default="")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "customers"
        ordering = ["code"]

    def __str__(self):
        return f"{self.code} — {self.name}"


class Invoice(models.Model):
    """Salgsfaktura. Et udkast har et midlertidigt nummer (UDK-…); det
    fortløbende fakturanummer gives, når fakturaen bogføres."""

    STATUS_CHOICES = [
        ("draft", "Draft"),
        ("sent", "Sent"),
        ("paid", "Paid"),
        ("overdue", "Overdue"),
        ("cancelled", "Cancelled"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    invoice_number = models.CharField(max_length=20, unique=True)
    customer = models.ForeignKey(
        Customer, on_delete=models.PROTECT, related_name="invoices"
    )
    date = models.DateField()
    # Leveringsdato (momsbekendtgørelsens § 58, stk. 1, nr. 6), hvis forskellig fra fakturadatoen.
    delivery_date = models.DateField(null=True, blank=True)
    due_date = models.DateField()
    payment_terms_code = models.CharField(max_length=10, choices=PAYMENT_TERMS_CHOICES, default="net14")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="draft")
    subtotal = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    tax_amount = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    total = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    paid_amount = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    currency = models.CharField(max_length=3, default="DKK")
    # DKK pr. 1 enhed af currency.
    exchange_rate = models.DecimalField(max_digits=12, decimal_places=6, default=1)
    # Købers reference og ordrenummer (kræves af OIOUBL til offentlige kunder).
    customer_reference = models.CharField(max_length=100, blank=True, default="")
    order_reference = models.CharField(max_length=100, blank=True, default="")
    quote = models.ForeignKey("sales.Quote", on_delete=models.SET_NULL, null=True, blank=True,
                              related_name="invoices")
    notes = models.TextField(blank=True, default="")
    journal_entry = models.ForeignKey(
        "journals.JournalEntry",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="invoices",
    )
    created_by = models.CharField(max_length=200, blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "invoices"
        ordering = ["-date", "-invoice_number"]

    def __str__(self):
        return f"{self.invoice_number} — {self.customer.name}"

    @property
    def balance_due(self):
        return self.total - self.paid_amount


class InvoiceLine(models.Model):
    """Individual line item on an invoice."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    invoice = models.ForeignKey(
        Invoice, on_delete=models.CASCADE, related_name="lines"
    )
    description = models.CharField(max_length=500)
    quantity = models.DecimalField(max_digits=10, decimal_places=2, default=1)
    unit = models.CharField(max_length=20, blank=True, default="stk.")
    unit_price = models.DecimalField(
        max_digits=15, decimal_places=2, default=0,
        help_text="Enhedspris uden moms i fakturaens valuta",
    )
    tax_code = models.ForeignKey(
        "core.TaxCode",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="invoice_lines",
    )
    account = models.ForeignKey(
        Account, on_delete=models.PROTECT, related_name="invoice_lines",
        null=True, blank=True,
    )
    amount = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    is_text = models.BooleanField(
        default=False, help_text="Tekstlinje (uden antal, pris og konto)"
    )
    position = models.IntegerField(default=0, help_text="Rækkefølge på fakturaen")

    class Meta:
        db_table = "invoice_lines"
        ordering = ["position", "id"]

    def save(self, *args, **kwargs):
        if self.is_text:
            self.amount = 0
        else:
            self.amount = self.quantity * self.unit_price
        super().save(*args, **kwargs)


class CreditNote(models.Model):
    """Credit note issued to a customer."""

    STATUS_CHOICES = [
        ("draft", "Draft"),
        ("applied", "Applied"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    credit_note_number = models.CharField(max_length=20, unique=True)
    customer = models.ForeignKey(
        Customer, on_delete=models.PROTECT, related_name="credit_notes"
    )
    invoice = models.ForeignKey(
        Invoice,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="credit_notes",
    )
    date = models.DateField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="draft")
    subtotal = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    tax_amount = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    total = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    notes = models.TextField(blank=True, default="")
    journal_entry = models.ForeignKey(
        "journals.JournalEntry",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="credit_notes",
    )
    created_by = models.CharField(max_length=200, blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "credit_notes"
        ordering = ["-date", "-credit_note_number"]

    def __str__(self):
        return f"{self.credit_note_number} — {self.customer.name}"


class Quote(models.Model):
    """Tilbud. Kan accepteres og laves om til en faktura."""

    STATUS_CHOICES = [
        ("draft", "Kladde"),
        ("sent", "Sendt"),
        ("accepted", "Accepteret"),
        ("rejected", "Afvist"),
        ("invoiced", "Faktureret"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    quote_number = models.CharField(max_length=20, unique=True)
    customer = models.ForeignKey(Customer, on_delete=models.PROTECT, related_name="quotes")
    date = models.DateField()
    valid_until = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="draft")
    currency = models.CharField(max_length=3, default="DKK")
    subtotal = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    tax_amount = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    total = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    notes = models.TextField(blank=True, default="")
    created_by = models.CharField(max_length=200, blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "quotes"
        ordering = ["-date", "-quote_number"]

    def __str__(self):
        return f"{self.quote_number} — {self.customer.name}"


class QuoteLine(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    quote = models.ForeignKey(Quote, on_delete=models.CASCADE, related_name="lines")
    description = models.CharField(max_length=500)
    quantity = models.DecimalField(max_digits=10, decimal_places=2, default=1)
    unit = models.CharField(max_length=20, blank=True, default="stk.")
    unit_price = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    tax_code = models.ForeignKey("core.TaxCode", on_delete=models.SET_NULL, null=True, blank=True,
                                 related_name="quote_lines")
    account = models.ForeignKey(Account, on_delete=models.PROTECT, null=True, blank=True,
                                related_name="quote_lines")
    amount = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    is_text = models.BooleanField(default=False)
    position = models.IntegerField(default=0)

    class Meta:
        db_table = "quote_lines"
        ordering = ["position", "id"]

    def save(self, *args, **kwargs):
        self.amount = 0 if self.is_text else self.quantity * self.unit_price
        super().save(*args, **kwargs)


class Reminder(models.Model):
    """Rykker for en forfalden faktura (renteloven § 9 b): højst 3 rykkere med
    gebyr, højst 100 kr. pr. rykker, mindst 10 dage mellem rykkerne. Gebyret
    bogføres (DR debitorer / CR rykkergebyrer) uden moms."""

    MAX_LEVEL = 3
    MAX_FEE = 100

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    invoice = models.ForeignKey(Invoice, on_delete=models.PROTECT, related_name="reminders")
    level = models.PositiveSmallIntegerField()
    date = models.DateField()
    due_date = models.DateField()
    fee = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    # Morarenter (renteloven § 5: referencesats + 8 procentpoint), beregnet til dato.
    interest = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    text = models.TextField(blank=True, default="")
    journal_entry = models.ForeignKey("journals.JournalEntry", on_delete=models.SET_NULL, null=True,
                                      blank=True, related_name="reminders")
    created_by = models.CharField(max_length=200, blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "reminders"
        ordering = ["invoice", "level"]
        unique_together = [("invoice", "level")]

    def __str__(self):
        return f"Rykker {self.level} for {self.invoice.invoice_number}"
