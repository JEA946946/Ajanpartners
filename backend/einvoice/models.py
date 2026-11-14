"""E-fakturaer sendt og modtaget gennem et access point (tenant-skema).

XML'en gemmes uændret sammen med dens SHA-256, så det dokument, der blev sendt
eller modtaget, kan fremvises i hele opbevaringsperioden (Bogføringsloven § 10).
"""

import hashlib
import uuid

from django.db import models


def sha256(text):
    return hashlib.sha256((text or "").encode("utf-8")).hexdigest()


class OutgoingEInvoice(models.Model):
    DOCUMENT_TYPES = [("invoice", "Faktura"), ("credit_note", "Kreditnota")]
    FORMATS = [("peppol", "Peppol BIS Billing 3.0"), ("oioubl", "OIOUBL 2.1")]
    STATUS = [
        ("generated", "Dannet"),
        ("sent", "Sendt til access point"),
        ("delivered", "Leveret til modtager"),
        ("failed", "Fejlet"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    document_type = models.CharField(max_length=20, choices=DOCUMENT_TYPES, default="invoice")
    format = models.CharField(max_length=10, choices=FORMATS, default="peppol")
    invoice = models.ForeignKey("sales.Invoice", on_delete=models.PROTECT, null=True, blank=True,
                                related_name="+")
    credit_note = models.ForeignKey("sales.CreditNote", on_delete=models.PROTECT, null=True, blank=True,
                                    related_name="+")
    document_number = models.CharField(max_length=50, default="")
    receiver_scheme = models.CharField(max_length=10, blank=True, default="")   # 0184 (CVR) / 0088 (GLN)
    receiver_endpoint = models.CharField(max_length=50, blank=True, default="")
    receiver_name = models.CharField(max_length=255, blank=True, default="")
    xml = models.TextField()
    sha256 = models.CharField(max_length=64, default="")
    status = models.CharField(max_length=20, choices=STATUS, default="generated")
    access_point = models.CharField(max_length=30, blank=True, default="")
    access_point_id = models.CharField(max_length=200, blank=True, default="")  # udbyderens besked-id
    error = models.TextField(blank=True, default="")
    sent_at = models.DateTimeField(null=True, blank=True)
    created_by = models.CharField(max_length=200, blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "einvoice_outgoing"
        ordering = ["-created_at"]

    def save(self, *args, **kwargs):
        self.sha256 = sha256(self.xml)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.document_number} → {self.receiver_scheme}:{self.receiver_endpoint} ({self.status})"


class IncomingEInvoice(models.Model):
    STATUS = [
        ("new", "Ny"),
        ("converted", "Oprettet som regning"),
        ("rejected", "Afvist"),
        ("failed", "Kunne ikke læses"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    document_type = models.CharField(max_length=20, default="invoice")
    format = models.CharField(max_length=10, blank=True, default="")
    document_number = models.CharField(max_length=100, blank=True, default="")
    issue_date = models.DateField(null=True, blank=True)
    due_date = models.DateField(null=True, blank=True)
    currency = models.CharField(max_length=3, blank=True, default="DKK")
    total = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    tax_amount = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    sender_scheme = models.CharField(max_length=10, blank=True, default="")
    sender_endpoint = models.CharField(max_length=50, blank=True, default="")
    sender_name = models.CharField(max_length=255, blank=True, default="")
    xml = models.TextField()
    sha256 = models.CharField(max_length=64, default="", db_index=True)
    parsed = models.JSONField(default=dict, blank=True)      # læst indhold + forslag til regning
    status = models.CharField(max_length=20, choices=STATUS, default="new")
    access_point = models.CharField(max_length=30, blank=True, default="")
    access_point_id = models.CharField(max_length=200, blank=True, default="")
    error = models.TextField(blank=True, default="")
    bill = models.ForeignKey("purchases.Bill", on_delete=models.SET_NULL, null=True, blank=True, related_name="+")
    converted_by = models.CharField(max_length=200, blank=True, default="")
    converted_at = models.DateTimeField(null=True, blank=True)
    received_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "einvoice_incoming"
        ordering = ["-received_at"]

    def save(self, *args, **kwargs):
        self.sha256 = sha256(self.xml)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.sender_name} {self.document_number} ({self.status})"
