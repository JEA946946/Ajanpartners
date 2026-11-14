"""E-faktura: dannelse (Peppol BIS 3.0/OIOUBL 2.1), læsning og indbakke → regning.

Testene tjekker velformethed og de obligatoriske Peppol-elementer.
Officiel validering (XSD + schematron) ligger i einvoice/tests_schematron.py.

Kør: manage.py test einvoice
"""

import tempfile
import xml.etree.ElementTree as ET
from datetime import date
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import SimpleTestCase, override_settings
from django_tenants.test.cases import TenantTestCase

from integrations.base import AgreementRequired

from . import services
from .parse import ParseError, parse_ubl, suggest_bill
from .ubl import NS_CAC, NS_CBC, NS_CREDIT_NOTE, NS_INVOICE, endpoint_for, split_address

User = get_user_model()
C = {"cac": NS_CAC, "cbc": NS_CBC}


def fixtures(tenant):
    from accounts.models import Account, AccountType
    from core.models import CompanySettings, TaxCode
    from sales.models import Customer, CreditNote, Invoice, InvoiceLine

    cs = CompanySettings.objects.first() or CompanySettings()
    cs.company_name, cs.address, cs.city, cs.tax_id = "Sælger ApS", "Sælgervej 1\n2100 København Ø", "København Ø", "12345678"
    cs.email = "faktura@saelger.dk"
    cs.save()
    rev, _ = AccountType.objects.get_or_create(name="Revenue", defaults={"normal_balance": "credit"})
    exp, _ = AccountType.objects.get_or_create(name="Expense", defaults={"normal_balance": "debit"})
    sales_acct = Account.objects.create(code="T1000", name="Salg", account_type=rev)
    cost_acct = Account.objects.create(code="T2000", name="Varekøb", account_type=exp)
    liab, _ = AccountType.objects.get_or_create(name="Liability", defaults={"normal_balance": "credit"})
    vat_acct = Account.objects.create(code="T7680", name="Moms", account_type=liab)
    vat25 = TaxCode.objects.create(code="T25", name="Moms 25 %", rate=Decimal("25"), type="both", account=vat_acct)
    free = TaxCode.objects.create(code="T0", name="Momsfri", rate=Decimal("0"), type="both", account=vat_acct)
    customer = Customer.objects.create(code="K001", name="Køber A/S", address="Købervej 7\n8000 Aarhus C",
                                       tax_id="87654321", email="ap@koeber.dk")
    inv = Invoice.objects.create(invoice_number="F-1001", customer=customer, date=date(2026, 11, 1),
                                 due_date=date(2026, 11, 15), status="sent", currency="DKK",
                                 subtotal=Decimal("1500"), tax_amount=Decimal("250"), total=Decimal("1750"))
    InvoiceLine.objects.create(invoice=inv, description="Rådgivning", quantity=Decimal("2"),
                               unit_price=Decimal("500"), tax_code=vat25, account=sales_acct, position=1)
    InvoiceLine.objects.create(invoice=inv, description="Gebyr (momsfrit)", quantity=Decimal("1"),
                               unit_price=Decimal("500"), tax_code=free, account=sales_acct, position=2)
    InvoiceLine.objects.create(invoice=inv, description="Tak for handlen", is_text=True, position=3)
    cn = CreditNote.objects.create(credit_note_number="KN-1", customer=customer, invoice=inv,
                                   date=date(2026, 11, 3), subtotal=Decimal("100"), tax_amount=Decimal("25"),
                                   total=Decimal("125"))
    return {"invoice": inv, "credit_note": cn, "customer": customer, "vat25": vat25, "cost": cost_acct}


class HelperTests(SimpleTestCase):
    def test_endpoint_scheme(self):
        self.assertEqual(endpoint_for("DK12345678", ""), ("0184", "12345678"))
        self.assertEqual(endpoint_for("12345678", "5790000123452"), ("0088", "5790000123452"))
        self.assertEqual(endpoint_for("", ""), (None, None))
        self.assertEqual(endpoint_for("12345678", "5790000123456"), ("0184", "12345678"))  # forkert kontrolciffer

    def test_split_address(self):
        self.assertEqual(split_address("Testvej 1\n2100 København Ø"), ("Testvej 1", "2100", "København Ø"))

    def test_parse_rejects_garbage_and_entities(self):
        with self.assertRaises(ParseError):
            parse_ubl("<nope")
        bomb = '<?xml version="1.0"?><!DOCTYPE x [<!ENTITY a "aaaa">]><Invoice>&a;</Invoice>'
        with self.assertRaises(ParseError):
            parse_ubl(bomb)


_MEDIA = tempfile.mkdtemp(prefix="einvoice-test-media-")


@override_settings(MEDIA_ROOT=_MEDIA)
class EInvoiceTests(TenantTestCase):
    @classmethod
    def get_test_schema_name(cls):
        return "c_einvoicetest"

    @classmethod
    def setup_tenant(cls, tenant):
        from tenancy.models import Firm, Package
        from tenancy.services import seed_packages
        seed_packages()
        tenant.firm = Firm.current()
        tenant.package = Package.objects.get(code="standard")
        tenant.name = "Sælger ApS"
        tenant.slug = "einvoicetest"
        tenant.cvr = "12345678"
        tenant.zip_code = "2100"
        tenant.city = "København Ø"
        tenant.address = "Sælgervej 1"

    def setUp(self):
        self.f = fixtures(self.tenant)
        self.user = User.objects.create_user("bog@x.dk", "bog@x.dk", "x")

    def _root(self, xml):
        self.assertTrue(xml.startswith('<?xml version="1.0" encoding="UTF-8"?>'))
        return ET.fromstring(xml)  # velformet

    def _assert_mandatory(self, root, kind):
        for path in ("cbc:CustomizationID", "cbc:ProfileID", "cbc:ID", "cbc:IssueDate", "cbc:DocumentCurrencyCode",
                     "cbc:BuyerReference",
                     "cac:AccountingSupplierParty/cac:Party/cbc:EndpointID",
                     "cac:AccountingSupplierParty/cac:Party/cac:PartyLegalEntity/cbc:RegistrationName",
                     "cac:AccountingCustomerParty/cac:Party/cbc:EndpointID",
                     "cac:TaxTotal/cbc:TaxAmount", "cac:TaxTotal/cac:TaxSubtotal/cac:TaxCategory/cbc:ID",
                     "cac:LegalMonetaryTotal/cbc:LineExtensionAmount",
                     "cac:LegalMonetaryTotal/cbc:TaxExclusiveAmount",
                     "cac:LegalMonetaryTotal/cbc:TaxInclusiveAmount",
                     "cac:LegalMonetaryTotal/cbc:PayableAmount",
                     f"cac:{kind}Line/cac:Item/cbc:Name", f"cac:{kind}Line/cac:Price/cbc:PriceAmount"):
            self.assertIsNotNone(root.find(path, C), path)

    def test_peppol_invoice(self):
        from .ubl import build_invoice

        root = self._root(build_invoice(self.f["invoice"], "peppol"))
        self.assertEqual(root.tag, f"{{{NS_INVOICE}}}Invoice")
        self._assert_mandatory(root, "Invoice")
        self.assertEqual(root.findtext("cbc:CustomizationID", namespaces=C),
                         "urn:cen.eu:en16931:2017#compliant#urn:fdc:peppol.eu:2017:poacc:billing:3.0")
        self.assertEqual(root.findtext("cbc:ProfileID", namespaces=C), "urn:fdc:peppol.eu:2017:poacc:billing:01:1.0")
        self.assertEqual(root.findtext("cbc:InvoiceTypeCode", namespaces=C), "380")
        sup = root.find("cac:AccountingSupplierParty/cac:Party/cbc:EndpointID", C)
        self.assertEqual((sup.get("schemeID"), sup.text), ("0184", "12345678"))
        cus = root.find("cac:AccountingCustomerParty/cac:Party/cbc:EndpointID", C)
        self.assertEqual((cus.get("schemeID"), cus.text), ("0184", "87654321"))
        self.assertEqual(root.findtext("cac:AccountingSupplierParty/cac:Party/cac:PartyTaxScheme/cbc:CompanyID",
                                       namespaces=C), "DK12345678")
        # 2 × 500 à 25 % + 500 momsfrit; tekstlinjen er ikke en fakturalinje
        self.assertEqual(len(root.findall("cac:InvoiceLine", C)), 2)
        self.assertEqual(root.findtext("cac:TaxTotal/cbc:TaxAmount", namespaces=C), "250.00")
        self.assertEqual(root.find("cac:TaxTotal/cbc:TaxAmount", C).get("currencyID"), "DKK")
        cats = {s.findtext("cac:TaxCategory/cbc:ID", namespaces=C): s.findtext("cbc:TaxableAmount", namespaces=C)
                for s in root.findall("cac:TaxTotal/cac:TaxSubtotal", C)}
        self.assertEqual(cats, {"S": "1000.00", "E": "500.00"})
        self.assertIsNotNone(root.find("cac:TaxTotal/cac:TaxSubtotal/cac:TaxCategory/cbc:TaxExemptionReason", C))
        lmt = {e.tag.split("}")[1]: e.text for e in root.find("cac:LegalMonetaryTotal", C)}
        self.assertEqual(lmt, {"LineExtensionAmount": "1500.00", "TaxExclusiveAmount": "1500.00",
                               "TaxInclusiveAmount": "1750.00", "PayableAmount": "1750.00"})

    def test_gln_endpoint(self):
        from .ubl import build_invoice

        c = self.f["customer"]
        c.ean = "5790000123452"
        c.save()
        root = self._root(build_invoice(self.f["invoice"], "peppol"))
        cus = root.find("cac:AccountingCustomerParty/cac:Party/cbc:EndpointID", C)
        self.assertEqual((cus.get("schemeID"), cus.text), ("0088", "5790000123452"))

    def test_oioubl_and_credit_note(self):
        from .ubl import build_credit_note, build_invoice

        xml = build_invoice(self.f["invoice"], "oioubl")
        root = self._root(xml)
        self.assertEqual(root.findtext("cbc:UBLVersionID", namespaces=C), "2.1")
        self.assertEqual(root.findtext("cbc:CustomizationID", namespaces=C), "OIOUBL-2.1")
        sup = root.find("cac:AccountingSupplierParty/cac:Party/cbc:EndpointID", C)
        self.assertEqual((sup.get("schemeID"), sup.text), ("DK:CVR", "DK12345678"))
        # OIOUBL: TaxExclusiveAmount er momsbeløbet, og hver linje har en TaxTotal
        self.assertEqual(root.findtext("cac:LegalMonetaryTotal/cbc:TaxExclusiveAmount", namespaces=C), "250.00")
        self.assertEqual(len(root.findall("cac:InvoiceLine/cac:TaxTotal", C)), 2)
        parsed = parse_ubl(xml)  # indgående OIOUBL kan også læses
        self.assertEqual((parsed["format"], parsed["supplier"]["cvr"], parsed["payable"]),
                         ("oioubl", "12345678", "1750.00"))
        root = self._root(build_credit_note(self.f["credit_note"], "peppol"))
        self.assertEqual(root.tag, f"{{{NS_CREDIT_NOTE}}}CreditNote")
        self._assert_mandatory(root, "CreditNote")
        self.assertEqual(root.findtext("cbc:CreditNoteTypeCode", namespaces=C), "381")
        self.assertEqual(root.findtext("cac:BillingReference/cac:InvoiceDocumentReference/cbc:ID",
                                       namespaces=C), "F-1001")
        self.assertEqual(root.findtext("cac:LegalMonetaryTotal/cbc:PayableAmount", namespaces=C), "125.00")

    def test_missing_endpoint(self):
        from .ubl import EInvoiceError

        c = self.f["customer"]
        c.tax_id = ""
        c.save()
        with self.assertRaises(EInvoiceError):
            services.generate(self.f["invoice"], "invoice", "peppol", self.user)

    def test_draft_cannot_be_sent(self):
        from .ubl import EInvoiceError

        inv = self.f["invoice"]
        inv.status = "draft"
        inv.save()
        with self.assertRaises(EInvoiceError):
            services.generate(inv, "invoice", "peppol", self.user)

    def test_round_trip_send_mock_inbox_to_bill(self):
        from purchases.models import Bill, Supplier

        from .models import IncomingEInvoice

        out = services.send(services.generate(self.f["invoice"], "invoice", "peppol", self.user), self.user)
        self.assertEqual(out.status, "delivered")
        self.assertTrue(out.access_point_id.startswith("MOCK-"))
        self.assertEqual(len(out.sha256), 64)
        incoming = IncomingEInvoice.objects.get()
        self.assertEqual((incoming.document_number, incoming.total, incoming.tax_amount),
                         ("F-1001", Decimal("1750.00"), Decimal("250.00")))
        self.assertEqual((incoming.sender_scheme, incoming.sender_endpoint), ("0184", "12345678"))
        # samme XML igen giver ikke en ny post
        self.assertEqual(services.receive(out.xml).pk, incoming.pk)
        # leverandøren findes på CVR
        supplier = Supplier.objects.create(code="SUP-0001", name="Sælger ApS", tax_id="DK12345678",
                                           default_account=self.f["cost"])
        incoming.parsed["suggestion"] = suggest_bill(incoming.parsed)
        incoming.save()
        sug = incoming.parsed["suggestion"]
        self.assertEqual(sug["supplier_id"], str(supplier.id))
        self.assertEqual(sug["lines"][0]["tax_code"], "T25")
        bill = services.to_bill(incoming, self.user)
        self.assertEqual(bill.status, "draft")
        self.assertEqual((bill.subtotal, bill.tax_amount, bill.total),
                         (Decimal("1500.00"), Decimal("250.00"), Decimal("1750.00")))
        self.assertEqual(bill.reference, "F-1001")
        self.assertEqual(bill.lines.count(), 2)
        self.assertEqual(bill.lines.first().account_id, self.f["cost"].id)
        self.assertEqual(Bill.objects.count(), 1)
        doc = bill.documents.get()
        self.assertEqual(doc.sha256, incoming.sha256)  # samme bytes som den modtagne XML
        self.assertTrue(doc.filename.endswith(".xml"))
        with doc.file.open("rb") as fh:
            self.assertEqual(fh.read().decode("utf-8"), incoming.xml)
        incoming.refresh_from_db()
        self.assertEqual(incoming.status, "converted")
        from .ubl import EInvoiceError
        with self.assertRaises(EInvoiceError):
            services.to_bill(incoming, self.user)

    def test_unknown_supplier_is_created(self):
        from purchases.models import Supplier

        out = services.send(services.generate(self.f["invoice"], "invoice", "peppol", self.user), self.user)
        incoming = services.receive(out.xml)
        bill = services.to_bill(incoming, self.user)
        self.assertEqual(bill.supplier.name, "Sælger ApS")
        self.assertEqual(Supplier.objects.get().tax_id, "12345678")

    @override_settings(EINVOICE_ACCESS_POINT="storecove")
    def test_stub_access_point(self):
        out = services.generate(self.f["invoice"], "invoice", "peppol", self.user)
        with self.assertRaises(AgreementRequired):
            services.send(out, self.user)
        out.refresh_from_db()
        self.assertEqual(out.status, "failed")
