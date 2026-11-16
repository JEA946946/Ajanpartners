"""bootstrap_firm: revisorhusets stamdata kan angives og opdateres."""

from io import StringIO

from django.core.management import CommandError, call_command
from django.test import TestCase

from tenancy.models import Firm, FirmStaff


class BootstrapFirmTests(TestCase):
    def run_cmd(self, *args):
        out = StringIO()
        call_command("bootstrap_firm", "--domain", "testserver", *args, stdout=out)
        return out.getvalue()

    def test_sets_firm_details(self):
        out = self.run_cmd("--firm-name", "Ajan Partners", "--cvr", "DK 46 92 25 14", "--email", "info@ap.dk")
        firm = Firm.current()
        self.assertEqual((firm.name, firm.cvr, firm.email), ("Ajan Partners", "46922514", "info@ap.dk"))
        self.assertIn("CVR 46922514", out)

    def test_rerun_keeps_unspecified_fields(self):
        self.run_cmd("--cvr", "46922514", "--phone", "12345678")
        self.run_cmd("--partner-email", "p@ap.dk", "--partner-password", "Test-1234567")
        firm = Firm.current()
        self.assertEqual((firm.cvr, firm.phone), ("46922514", "12345678"))
        self.assertTrue(FirmStaff.objects.filter(user__email="p@ap.dk", role="partner").exists())

    def test_invalid_cvr(self):
        with self.assertRaises(CommandError):
            self.run_cmd("--cvr", "1234")
