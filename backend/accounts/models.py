"""Chart of Accounts and Fiscal Year models."""

import uuid

from django.db import models


class AccountType(models.Model):
    """Asset, Liability, Equity, Revenue, Expense."""

    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=50, unique=True)
    normal_balance = models.CharField(
        max_length=6,
        choices=[("debit", "Debit"), ("credit", "Credit")],
    )
    display_order = models.IntegerField(default=0)

    class Meta:
        db_table = "account_types"
        ordering = ["display_order"]

    def __str__(self):
        return self.name


class Account(models.Model):
    """General ledger account (hierarchical via parent)."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    code = models.CharField(max_length=20, unique=True)
    name = models.CharField(max_length=200)
    account_type = models.ForeignKey(
        AccountType,
        on_delete=models.PROTECT,
        related_name="accounts",
    )
    parent = models.ForeignKey(
        "self",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="children",
    )
    currency = models.CharField(max_length=3, default="DKK")
    # Erhvervsstyrelsens standardkontoplan: nummeret, kontoen svarer til (SAF-T
    # GroupingCode/StandardAccountID), og linjen i årsregnskabslovens skema.
    standard_code = models.CharField(max_length=10, blank=True, default="", db_index=True)
    arl_line = models.CharField(max_length=40, blank=True, default="", db_index=True)
    # Overskrift (hovedkonto/gruppekonto): kan ikke bogføres på.
    is_header = models.BooleanField(default=False)
    description = models.TextField(blank=True, default="")
    is_active = models.BooleanField(default=True)
    manager_io_id = models.CharField(max_length=100, blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "accounts"
        ordering = ["code"]

    def __str__(self):
        return f"{self.code} — {self.name}"


class FiscalYear(models.Model):
    """Fiscal year for closing periods."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100)
    start_date = models.DateField()
    end_date = models.DateField()
    is_closed = models.BooleanField(default=False)
    closed_at = models.DateTimeField(null=True, blank=True)
    closed_by = models.CharField(max_length=200, blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "fiscal_years"
        ordering = ["-start_date"]

    def __str__(self):
        return self.name
