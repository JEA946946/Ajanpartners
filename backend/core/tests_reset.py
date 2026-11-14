"""Standardkontoplanen (seed) og reset_bookkeeping pr. kunde — kør: manage.py test core.tests_reset"""

from datetime import date
from io import StringIO

from django.core.management import call_command
from django.core.management.base import CommandError
from django.db import connection

from accounts import chart
from accounts.management.commands.seed_accounts import seed_chart
from accounts.models import Account
from core.models import TaxCode
from core.testing import LedgerTestCase
from journals.models import JournalEntry
from sales.models import Customer


class SeedTests(LedgerTestCase):
    def test_seed_builds_the_standard_chart_and_is_idempotent(self):
        self.assertEqual(seed_chart("standard"), 0)
        self.assertEqual(Account.objects.count(), 605)
        acc = Account.objects.get(code=chart.REVENUE)
        self.assertEqual((acc.standard_code, acc.arl_line, acc.account_type.name, acc.parent.code),
                         ("1010", "nettoomsaetning", "Revenue", "1001"))
        self.assertTrue(Account.objects.get(code="1001").is_header)
        susp = Account.objects.get(code=chart.SUSPENSE)
        self.assertEqual((susp.standard_code, susp.parent.code), (chart.SUSPENSE_STANDARD, "6301"))
        self.assertEqual(Account.objects.get(code="6510").account_type.name, "Equity")
        self.assertEqual(Account.objects.get(code=chart.VAT_SETTLEMENT).account_type.name, "Liability")
        # Klasse A-konti er oprettet, men ikke aktive for et selskab.
        self.assertFalse(Account.objects.get(code=chart.OWNER_RESULT).is_active)
        self.assertTrue(Account.objects.get(code=chart.RETAINED_EARNINGS).is_active)
        for name in ("DK_SALARIES", "DK_A_TAX_PAYABLE", "DK_AM_PAYABLE", "DK_ATP_PAYABLE",
                     "DK_HOLIDAY_PAY_PAYABLE", "DK_SALARIES_PAYABLE"):
            self.assertTrue(Account.objects.get(code=getattr(chart, name)).is_active, name)
        self.assertFalse(Account.objects.filter(currency="MAD").exists())

    def test_tax_codes_follow_the_official_list(self):
        codes = {t.code: t for t in TaxCode.objects.select_related("account", "input_account")}
        self.assertTrue({"S01", "S21", "S22", "S23", "S41", "K010", "K070", "K210", "K260", "K660", "E-EL"} <= set(codes))
        self.assertEqual((codes["S01"].rate, codes["S01"].account.code), (25, chart.VAT_OUTPUT))
        self.assertEqual((codes["K070"].deduction_rate, codes["K070"].account.code), (25, chart.VAT_INPUT))
        self.assertEqual((codes["K260"].reverse_charge, codes["K260"].rubrik, codes["K260"].input_account.code),
                         ("eu_services", "A_services", chart.VAT_INPUT))
        self.assertEqual(codes["S21"].rubrik, "B_goods")
        self.assertEqual(codes["E-EL"].standard_code, "")


class SoleTraderTests(LedgerTestCase):
    template = "enkeltmand"

    @classmethod
    def get_test_schema_name(cls):
        return "test_enkeltmand"

    @classmethod
    def get_test_tenant_domain(cls):
        return "enk.test.com"

    def test_owner_equity_accounts_are_active(self):
        for code in (chart.OWNER_RESULT, chart.OWNER_DRAWINGS, chart.OWNER_EQUITY_OPENING):
            self.assertTrue(Account.objects.get(code=code).is_active, code)
        self.assertFalse(Account.objects.get(code=chart.SHARE_CAPITAL).is_active)
        from journals.closing import result_account_code
        self.assertEqual(result_account_code(), chart.OWNER_RESULT)


class ResetTests(LedgerTestCase):
    def setUp(self):
        super().setUp()
        Customer.objects.create(code="K-1", name="Kunde")
        self.entry([("2810", "100", "0"), (chart.CASH, "0", "100")], d=date(2026, 3, 1))

    def run_reset(self, *args):
        connection.set_schema_to_public()
        try:
            call_command("reset_bookkeeping", "--client", self.tenant.slug, *args, stdout=StringIO())
        finally:
            connection.set_tenant(self.tenant)

    def test_dry_run_changes_nothing(self):
        self.run_reset("--force")
        self.assertEqual(JournalEntry.objects.count(), 1)

    def test_active_client_needs_force(self):
        with self.assertRaises(CommandError):
            self.run_reset("--confirm")

    def test_confirm_empties_the_books_and_keeps_master_data(self):
        self.run_reset("--confirm", "--force")
        self.assertEqual(JournalEntry.objects.count(), 0)
        self.assertEqual(Customer.objects.count(), 1)
        self.assertEqual(Account.objects.count(), 605)
