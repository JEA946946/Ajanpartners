"""PCGM seed and reset_bookkeeping — run with: python manage.py test core.tests_reset"""

from datetime import date
from decimal import Decimal
from io import StringIO

from django.core.management import call_command
from django.test import TestCase

from accounts.management.commands.seed_accounts import seed_chart
from accounts.models import Account, AccountType
from core.models import TaxCode
from journals.models import JournalEntry, JournalEntryLine
from purchases.models import Supplier
from sales.models import Customer


class SeedTests(TestCase):
    def test_seed_builds_the_tree_and_is_idempotent(self):
        created = seed_chart()
        self.assertGreater(created, 1000)
        self.assertEqual(seed_chart(), 0)
        acc = Account.objects.get(code="612631")
        self.assertEqual(acc.parent.code, "61263")
        self.assertEqual(acc.account_type.name, "Expense")
        self.assertEqual(Account.objects.get(code="4455").account_type.name, "Liability")
        self.assertEqual(Account.objects.get(code="1111").account_type.name, "Equity")
        self.assertEqual(Account.objects.get(code="5541").account_type.name, "Liability")
        self.assertEqual(Account.objects.get(code="51413").currency, "EUR")
        self.assertFalse(Account.objects.get(code="8100").is_active)
        self.assertFalse(Account.objects.filter(code__startswith="9").exists())


class ResetTests(TestCase):
    def setUp(self):
        exp = AccountType.objects.create(name="Expense", normal_balance="debit")
        liab = AccountType.objects.create(name="Liability", normal_balance="credit")
        asset = AccountType.objects.create(name="Asset", normal_balance="debit")
        self.hotel = Account.objects.create(code="523311", name="Hotel Oum Palace", account_type=exp)
        bank = Account.objects.create(code="101001", name="Bank CIH300", account_type=asset)
        vat = Account.objects.create(code="210000", name="VAT Payable", account_type=liab)
        self.supplier = Supplier.objects.create(code="SUP-0001", name="Oum Palace", default_account=self.hotel)
        Customer.objects.create(code="CUS-0001", name="Agency")
        TaxCode.objects.create(code="TVA-10", name="TVA 10", rate=Decimal("10"), type="purchase", account=vat)
        je = JournalEntry.objects.create(entry_number="JE-0001", date=date(2026, 3, 1), source="manual",
                                         is_posted=True, description="old")
        JournalEntryLine.objects.create(journal_entry=je, account=self.hotel, debit=Decimal("100"), credit=0)
        JournalEntryLine.objects.create(journal_entry=je, account=bank, debit=0, credit=Decimal("100"))

    def test_dry_run_changes_nothing(self):
        call_command("reset_bookkeeping", stdout=StringIO())
        self.assertEqual(JournalEntry.objects.count(), 1)
        self.assertTrue(Account.objects.filter(code="523311").exists())

    def test_confirm_empties_the_books_and_keeps_master_data_on_pcgm(self):
        call_command("reset_bookkeeping", "--confirm", stdout=StringIO())
        self.assertEqual(JournalEntry.objects.count(), 0)
        self.assertFalse(Account.objects.filter(code__in=["523311", "101001", "210000"]).exists())
        self.supplier.refresh_from_db()
        self.assertEqual(self.supplier.default_account.code, "612631")
        self.assertEqual(TaxCode.objects.get().account.code, "34552")
        self.assertEqual(Customer.objects.count(), 1)
