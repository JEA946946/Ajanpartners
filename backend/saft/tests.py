"""SAF-T Financial DK-eksport: velformet, debet = kredit, alle konti med, og gyldig
mod Erhvervsstyrelsens XSD (v1.0 og v2.1, vendored i saft/xsd/).

Kør: manage.py test saft
"""

import xml.etree.ElementTree as ET
from datetime import date
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import SimpleTestCase
from django_tenants.test.cases import TenantTestCase

from .export import NS, build_saft, split_street, validate

User = get_user_model()
N = {"s": NS}


class HelperTests(SimpleTestCase):
    def test_split_street(self):
        self.assertEqual(split_street("Testvej 12 st. tv\n2100 København Ø"),
                         ("Testvej", "12 st. tv", "2100", "København Ø"))


class SaftExportTests(TenantTestCase):
    @classmethod
    def get_test_schema_name(cls):
        return "c_safttest"

    @classmethod
    def setup_tenant(cls, tenant):
        from tenancy.models import Firm, Package
        from tenancy.services import seed_packages
        seed_packages()
        tenant.firm = Firm.current()
        tenant.package = Package.objects.get(code="standard")
        tenant.name = "Revision ApS"
        tenant.slug = "safttest"
        tenant.cvr = "12345678"
        tenant.address = "Revisorvej 3"
        tenant.zip_code = "8000"
        tenant.city = "Aarhus C"

    def setUp(self):
        from accounts.models import Account, AccountType
        from core.models import TaxCode
        from journals.models import Journal, JournalEntry, JournalEntryLine
        from purchases.models import Supplier
        from sales.models import Customer

        asset, _ = AccountType.objects.get_or_create(name="Asset", defaults={"normal_balance": "debit"})
        rev, _ = AccountType.objects.get_or_create(name="Revenue", defaults={"normal_balance": "credit"})
        liab, _ = AccountType.objects.get_or_create(name="Liability", defaults={"normal_balance": "credit"})
        self.bank = Account.objects.create(code="S5800", name="Bank", account_type=asset)
        self.revenue = Account.objects.create(code="S1010", name="Salg", account_type=rev)
        self.vat = Account.objects.create(code="S7680", name="Salgsmoms", account_type=liab)
        self.unused = Account.objects.create(code="S9999", name="Ubrugt konto", account_type=asset)
        if hasattr(self.revenue, "standard_code"):
            self.revenue.standard_code = "1010"
            self.revenue.save()
        TaxCode.objects.create(code="S25", name="Salgsmoms 25 %", rate=Decimal("25"), type="sales", account=self.vat,
                               **({"standard_code": "S1"} if hasattr(TaxCode, "standard_code") else {}))
        self.customer = Customer.objects.create(code="K1", name="Kunde ApS", tax_id="87654321",
                                                address="Kundevej 9\n5000 Odense C")
        Supplier.objects.create(code="L1", name="Leverandør A/S", tax_id="11223344", address="Lagervej 2")
        j = Journal.objects.create(code="SVE", name="Salg", type="sales")

        def entry(number, d, lines, posted=True):
            e = JournalEntry.objects.create(journal=j, entry_number=number, date=d, description=f"Bilag {number}",
                                            is_posted=posted)
            for acct, debit, credit, extra in lines:
                JournalEntryLine.objects.create(journal_entry=e, account=acct, debit=Decimal(debit),
                                                credit=Decimal(credit), currency="DKK", **extra)
            return e

        partner = {"partner_type": "customer", "partner_id": str(self.customer.id), "partner_name": "Kunde ApS"}
        entry("S-1", date(2025, 12, 20), [(self.bank, "500", "0", {}), (self.revenue, "0", "500", {})])  # primo
        entry("S-2", date(2026, 1, 10), [(self.bank, "1250", "0", partner), (self.revenue, "0", "1000", {}),
                                        (self.vat, "0", "250", {})])
        entry("S-3", date(2026, 2, 1), [(self.bank, "0", "100", {}), (self.revenue, "100", "0", {})])
        entry("S-4", date(2026, 2, 2), [(self.bank, "999", "0", {}), (self.revenue, "0", "999", {})], posted=False)

    def _export(self, version="1.0"):
        xml, stats = build_saft(date(2026, 1, 1), date(2026, 12, 31), version)
        return xml, ET.fromstring(xml), stats

    def test_wellformed_and_balanced(self):
        xml, root, stats = self._export()
        self.assertEqual(root.tag, f"{{{NS}}}AuditFile")
        self.assertEqual(root.findtext("s:Header/s:AuditFileVersion", namespaces=N), "1.0")
        self.assertEqual(root.findtext("s:Header/s:Company/s:RegistrationNumber", namespaces=N), "12345678")
        debit = sum(Decimal(x.text) for x in root.iterfind(".//s:Line/s:DebitAmount/s:Amount", N))
        credit = sum(Decimal(x.text) for x in root.iterfind(".//s:Line/s:CreditAmount/s:Amount", N))
        self.assertEqual(debit, credit)
        self.assertEqual(debit, Decimal("1350.00"))
        gle = root.find("s:GeneralLedgerEntries", N)
        self.assertEqual(Decimal(gle.findtext("s:TotalDebit", namespaces=N)), debit)
        self.assertEqual(Decimal(gle.findtext("s:TotalCredit", namespaces=N)), credit)
        self.assertEqual(gle.findtext("s:NumberOfEntries", namespaces=N), "2")  # kladden S-4 er ikke med
        self.assertEqual(stats["entries"], 2)

    def test_all_accounts_and_balances(self):
        from accounts.models import Account

        _, root, _ = self._export()
        ids = {a.findtext("s:AccountID", namespaces=N) for a in root.iterfind(".//s:GeneralLedgerAccounts/s:Account", N)}
        self.assertEqual(ids, set(Account.objects.values_list("code", flat=True)))
        bank = next(a for a in root.iterfind(".//s:GeneralLedgerAccounts/s:Account", N)
                    if a.findtext("s:AccountID", namespaces=N) == "S5800")
        self.assertEqual(bank.findtext("s:OpeningDebitBalance", namespaces=N), "500.00")
        self.assertEqual(bank.findtext("s:ClosingDebitBalance", namespaces=N), "1650.00")
        revenue = next(a for a in root.iterfind(".//s:GeneralLedgerAccounts/s:Account", N)
                       if a.findtext("s:AccountID", namespaces=N) == "S1010")
        self.assertEqual(revenue.findtext("s:AccountType", namespaces=N), "Sale")
        if hasattr(Account, "standard_code"):
            self.assertEqual(revenue.findtext("s:StandardAccountID", namespaces=N), "1010")
        line_customer = root.find(".//s:Line/s:CustomerID", N)
        self.assertEqual(line_customer.text, "K1")
        self.assertIsNotNone(root.find(".//s:MasterFiles/s:Customers/s:Customer", N))
        self.assertIsNotNone(root.find(".//s:MasterFiles/s:Suppliers/s:Supplier", N))
        self.assertIsNotNone(root.find(".//s:MasterFiles/s:TaxTable/s:TaxTableEntry/s:TaxCodeDetails", N))

    def test_valid_against_xsd_v1_0(self):
        xml, _, _ = self._export("1.0")
        self.assertEqual(validate(xml, "1.0"), [])

    def test_valid_against_xsd_v2_1(self):
        xml, root, _ = self._export("2.1")
        self.assertEqual(root.findtext("s:Header/s:Company/s:CVR", namespaces=N), "12345678")
        self.maxDiff = None
        self.assertEqual(validate(xml, "2.1"), [])

    def test_endpoint_download(self):
        from rest_framework.test import APIRequestFactory, force_authenticate

        from tenancy.access import ClientAccess

        from .views import export

        user = User.objects.create_user("a@x.dk", "a@x.dk", "x")
        req = APIRequestFactory().get("/api/v1/saft/export", {"from": "2026-01-01", "to": "2026-12-31"})
        force_authenticate(req, user)
        req.client_access = ClientAccess(self.tenant, "viewer", "member")
        req.tenant = self.tenant
        resp = export(req)
        self.assertEqual(resp.status_code, 200)
        self.assertIn("attachment", resp["Content-Disposition"])
        ET.fromstring(resp.content)
        bad = APIRequestFactory().get("/api/v1/saft/export", {"from": "x"})
        force_authenticate(bad, user)
        bad.client_access = req.client_access
        self.assertEqual(export(bad).status_code, 400)


class SourceDocumentsTests(TenantTestCase):
    """SalesInvoices (faktura + kreditnota), PurchaseInvoices og Payments, gyldige mod begge XSD'er."""

    @classmethod
    def get_test_schema_name(cls):
        return "c_safttest_sd"

    @classmethod
    def setup_tenant(cls, tenant):
        SaftExportTests.setup_tenant.__func__(cls, tenant)
        tenant.slug = "safttest-sd"

    def setUp(self):
        from accounts.models import Account, AccountType
        from core.models import CompanySettings, Payment, TaxCode
        from journals.models import Journal, JournalEntry, JournalEntryLine
        from purchases.models import Bill, BillLine, Supplier
        from sales.models import CreditNote, Customer, Invoice, InvoiceLine

        asset, _ = AccountType.objects.get_or_create(name="Asset", defaults={"normal_balance": "debit"})
        rev, _ = AccountType.objects.get_or_create(name="Revenue", defaults={"normal_balance": "credit"})
        liab, _ = AccountType.objects.get_or_create(name="Liability", defaults={"normal_balance": "credit"})
        exp, _ = AccountType.objects.get_or_create(name="Expense", defaults={"normal_balance": "debit"})
        A = lambda code, name, t: Account.objects.create(code=code, name=name, account_type=t)  # noqa: E731
        self.bank, rec, pay = A("D5800", "Bank", asset), A("D5600", "Debitorer", asset), A("D6800", "Kreditorer", liab)
        revenue, vat, cost, vat_in = (A("D1010", "Salg", rev), A("D7680", "Salgsmoms", liab),
                                      A("D2000", "Vareforbrug", exp), A("D7690", "Købsmoms", asset))
        s25 = TaxCode.objects.create(code="S25", name="Salgsmoms 25 %", rate=Decimal("25"), type="sales", account=vat)
        k25 = TaxCode.objects.create(code="K25", name="Købsmoms 25 %", rate=Decimal("25"), type="purchase",
                                     account=vat_in)
        cust = Customer.objects.create(code="K1", name="Kunde ApS", tax_id="87654321", address="Kundevej 9",
                                       postal_code="5000", city="Odense C")
        sup = Supplier.objects.create(code="L1", name="Leverandør A/S", tax_id="11223344", address="Lagervej 2\n8000 Aarhus C")
        sales_j = Journal.objects.create(code="DVE", name="Salg", type="sales")
        purch_j = Journal.objects.create(code="DAC", name="Køb", type="purchases")
        Journal.objects.create(code="DBK", name="Erhvervskonto", type="bank", account=self.bank)
        cs = CompanySettings.objects.first() or CompanySettings()
        cs.iban, cs.bank_reg_no, cs.bank_account_no = "DK5000400440116243", "", ""
        cs.save()
        cp = {"partner_type": "customer", "partner_id": str(cust.id)}
        sp = {"partner_type": "supplier", "partner_id": str(sup.id)}

        def entry(journal, number, d, lines):
            e = JournalEntry.objects.create(journal=journal, entry_number=number, date=d, is_posted=True,
                                            description=number)
            for acct, debit, credit, extra in lines:
                JournalEntryLine.objects.create(journal_entry=e, account=acct, debit=Decimal(debit),
                                                credit=Decimal(credit), currency="DKK", **extra)
            return e

        e1 = entry(sales_j, "D-1", date(2026, 3, 1), [(rec, "1250", "0", cp), (revenue, "0", "1000", {}),
                                                      (vat, "0", "250", {})])
        inv = Invoice.objects.create(invoice_number="F-1", customer=cust, date=date(2026, 3, 1),
                                     due_date=date(2026, 3, 15), status="sent", subtotal=1000, tax_amount=250,
                                     total=1250, currency="DKK", journal_entry=e1)
        InvoiceLine.objects.create(invoice=inv, description="Rådgivning", quantity=2, unit_price=500,
                                   tax_code=s25, account=revenue)
        e2 = entry(sales_j, "D-2", date(2026, 3, 5), [(revenue, "100", "0", {}), (vat, "25", "0", {}),
                                                      (rec, "0", "125", cp)])
        CreditNote.objects.create(credit_note_number="KN-1", customer=cust, invoice=inv, date=date(2026, 3, 5),
                                  subtotal=100, tax_amount=25, total=125, journal_entry=e2)
        e3 = entry(purch_j, "D-3", date(2026, 3, 10), [(cost, "400", "0", {}), (vat_in, "100", "0", {}),
                                                       (pay, "0", "500", sp)])
        bill = Bill.objects.create(bill_number="BILL-0001", supplier=sup, date=date(2026, 3, 10),
                                   due_date=date(2026, 4, 10), status="approved", subtotal=400, tax_amount=100,
                                   total=500, currency="DKK", reference="LEV-77", journal_entry=e3)
        BillLine.objects.create(bill=bill, description="Varer", quantity=4, unit_price=100, tax_code=k25,
                                account=cost)
        e4 = entry(sales_j, "D-4", date(2026, 3, 20), [(self.bank, "1125", "0", {}), (rec, "0", "1125", cp)])
        Payment.objects.create(payment_number="PAY-1", type="incoming", date=date(2026, 3, 20), amount=1125,
                               method="bank_transfer", bank_account=self.bank, customer=cust, journal_entry=e4)
        # En faktura uden bogført postering kommer ikke med
        Invoice.objects.create(invoice_number="F-KLADDE", customer=cust, date=date(2026, 3, 2),
                               due_date=date(2026, 3, 16), status="draft", subtotal=1, tax_amount=0, total=1)

    def _export(self, version):
        xml, stats = build_saft(date(2026, 1, 1), date(2026, 12, 31), version)
        return xml, ET.fromstring(xml), stats

    def test_source_documents_content(self):
        _, root, stats = self._export("2.1")
        sales = root.find("s:SourceDocuments/s:SalesInvoices", N)
        self.assertEqual(sales.findtext("s:NumberOfEntries", namespaces=N), "2")
        nos = [i.findtext("s:InvoiceNo", namespaces=N) for i in sales.iterfind("s:Invoice", N)]
        self.assertEqual(nos, ["F-1", "KN-1"])
        f1 = sales.find("s:Invoice", N)
        self.assertEqual(f1.findtext("s:TransactionID", namespaces=N), "D-1")
        self.assertEqual(f1.findtext("s:CustomerInfo/s:CustomerID", namespaces=N), "K1")
        self.assertEqual(f1.findtext("s:DocumentTotals/s:GrossTotal", namespaces=N), "1250.00")
        self.assertEqual(f1.findtext("s:Line/s:DebitCreditIndicator", namespaces=N), "C")
        self.assertEqual(Decimal(sales.findtext("s:TotalCredit", namespaces=N)), Decimal("1000.00"))
        self.assertEqual(Decimal(sales.findtext("s:TotalDebit", namespaces=N)), Decimal("100.00"))
        purchase = root.find("s:SourceDocuments/s:PurchaseInvoices/s:Invoice", N)
        self.assertEqual(purchase.findtext("s:SupplierInfo/s:SupplierID", namespaces=N), "L1")
        self.assertEqual(purchase.findtext("s:InvoiceNo", namespaces=N), "LEV-77")
        self.assertEqual(purchase.findtext("s:DocumentTotals/s:GrossTotal", namespaces=N), "500.00")
        payment = root.find("s:SourceDocuments/s:Payments/s:Payment", N)
        self.assertEqual(payment.findtext("s:TransactionID", namespaces=N), "D-4")
        self.assertEqual(payment.findtext("s:DocumentTotals/s:GrossTotal", namespaces=N), "1125.00")
        self.assertEqual((stats["sales_invoices"], stats["purchase_invoices"], stats["payments"]), (2, 1, 1))
        # IBAN fra CompanySettings står på bankkontoen; ingen advarsler
        self.assertEqual(root.findtext("s:Header/s:Company/s:BankAccount/s:IBANNumber", namespaces=N),
                         "DK5000400440116243")
        self.assertEqual(root.findtext("s:Header/s:Company/s:BankAccount/s:AccountID", namespaces=N), "D5800")
        self.assertEqual(stats["warnings"], [])

    def test_valid_against_xsd_v2_1(self):
        self.maxDiff = None
        xml, _, _ = self._export("2.1")
        self.assertEqual(validate(xml, "2.1"), [])

    def test_valid_against_xsd_v1_0(self):
        self.maxDiff = None
        xml, _, _ = self._export("1.0")
        self.assertEqual(validate(xml, "1.0"), [])

    def test_bank_iban_from_bank_feed_and_warning_when_missing(self):
        from core.models import CompanySettings
        from integrations.models import BankFeedConnection

        cs = CompanySettings.objects.first()
        cs.iban = ""
        cs.save()
        _, root, stats = self._export("2.1")
        self.assertEqual(root.findtext("s:Header/s:Company/s:BankAccount/s:BankAccountNumber", namespaces=N), "MANGLER")
        self.assertTrue(any("D5800" in w for w in stats["warnings"]))
        self.assertIn("ADVARSEL", root.findtext("s:Header/s:HeaderComment", namespaces=N))
        conn = BankFeedConnection(client=self.tenant, provider="mock", bank_account_id=self.bank.id,
                                  iban="DK1234567890123456")
        conn.grant_consent()
        conn.save()
        xml, root, stats = self._export("2.1")
        self.assertEqual(root.findtext("s:Header/s:Company/s:BankAccount/s:IBANNumber", namespaces=N),
                         "DK1234567890123456")
        self.assertEqual(stats["warnings"], [])
        self.assertEqual(validate(xml, "2.1"), [])
