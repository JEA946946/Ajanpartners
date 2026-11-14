"""Officiel validering af de dannede e-fakturaer:

  UBL 2.1 XSD (OASIS) for begge formater
  Peppol BIS 3.0: CEN EN 16931-reglerne + Peppol-reglerne (flag="fatal")
  OIOUBL 2.1:     Erhvervsstyrelsens OIOUBL-schematron v1.17.2 (F-regler)

Artefakterne ligger i einvoice/validation/ (kilde og licens i SOURCES.txt). Testene springes
over, hvis saxonche ikke er installeret eller filerne mangler.

Kør: manage.py test einvoice.tests_schematron
"""

import unittest
from django_tenants.test.cases import TenantTestCase

from .tests import fixtures
from .ubl import build_credit_note, build_invoice
from .validation import validate

SKIP = not validate.available()


@unittest.skipIf(SKIP, "saxonche eller schematron-filerne mangler (se einvoice/validation/SOURCES.txt)")
class SchematronTests(TenantTestCase):
    @classmethod
    def get_test_schema_name(cls):
        return "c_einvoicesch"

    @classmethod
    def setup_tenant(cls, tenant):
        from tenancy.models import Firm, Package
        from tenancy.services import seed_packages
        seed_packages()
        tenant.firm = Firm.current()
        tenant.package = Package.objects.get(code="standard")
        tenant.name = "Sælger ApS"
        tenant.slug = "einvoicesch"
        tenant.cvr = "12345678"
        tenant.zip_code = "2100"
        tenant.city = "København Ø"
        tenant.address = "Sælgervej 1"

    def setUp(self):
        from core.models import CompanySettings

        self.f = fixtures(self.tenant)
        c = self.f["customer"]
        c.address, c.postal_code, c.city, c.phone = "Købervej 7", "8000", "Aarhus C", "12345678"
        c.save()
        cs = CompanySettings.objects.first()
        cs.bank_reg_no, cs.bank_account_no, cs.iban, cs.bic = "1234", "0012345678", "DK5000400440116243", "DABADKKK"
        cs.save()

    def test_peppol_invoice_passes_cen_and_peppol_rules(self):
        self.maxDiff = None
        self.assertEqual(validate.validate_peppol(build_invoice(self.f["invoice"], "peppol")), [])

    def test_peppol_credit_note(self):
        self.maxDiff = None
        self.assertEqual(validate.validate_peppol(build_credit_note(self.f["credit_note"], "peppol")), [])

    def test_peppol_gln_receiver(self):
        c = self.f["customer"]
        c.ean = "5790000123452"
        c.save()
        self.assertEqual(validate.validate_peppol(build_invoice(self.f["invoice"], "peppol")), [])

    def test_oioubl_invoice(self):
        self.maxDiff = None
        self.assertEqual(validate.validate_oioubl(build_invoice(self.f["invoice"], "oioubl"), "invoice"), [])

    def test_oioubl_credit_note(self):
        self.maxDiff = None
        self.assertEqual(validate.validate_oioubl(build_credit_note(self.f["credit_note"], "oioubl"),
                                                  "credit_note"), [])

    def test_ubl_xsd(self):
        self.maxDiff = None
        for fmt in ("peppol", "oioubl"):
            self.assertEqual(validate.validate_ubl_xsd(build_invoice(self.f["invoice"], fmt), "invoice"), [], fmt)
            self.assertEqual(validate.validate_ubl_xsd(build_credit_note(self.f["credit_note"], fmt), "credit_note"),
                             [], fmt)

    def test_validator_catches_errors(self):
        xml = build_invoice(self.f["invoice"], "peppol").replace(
            '<cbc:PayableAmount currencyID="DKK">1750.00', '<cbc:PayableAmount currencyID="DKK">1751.00')
        self.assertTrue(any("BR-CO-16" in e for e in validate.validate_peppol(xml)))
        bad_order = build_invoice(self.f["invoice"], "peppol").replace("<cbc:IssueDate>", "<cbc:Note>x</cbc:Note><cbc:IssueDate>", 1)
        self.assertTrue(validate.validate_ubl_xsd(bad_order, "invoice"))
