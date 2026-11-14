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
