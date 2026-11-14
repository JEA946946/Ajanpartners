"""Ledger integrity — every write keeps DR = CR and follows the document.

Run with: python manage.py test core.tests_ledger
"""

from datetime import date
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient

from accounts.management.commands.seed_accounts import seed_chart
from accounts.models import Account, FiscalYear
from core.models import Payment, TaxCode
from journals.models import JournalEntry, JournalEntryLine
from journals.numbering import next_number
from purchases.models import Expense, Supplier
from sales.models import CreditNote, Customer, Invoice, InvoiceLine


def balanced(entry):
    lines = entry.lines.all()
    return sum(x.debit for x in lines) == sum(x.credit for x in lines)


class LedgerTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        seed_chart()
        cls.acc = {a.code: a for a in Account.objects.all()}
        cls.vat = TaxCode.objects.create(code="TVA20", name="TVA 20", rate=Decimal("20"), type="both",
                                         account=cls.acc["4455"])
        cls.customer = Customer.objects.create(code="CUS-0001", name="Agency")
        cls.supplier = Supplier.objects.create(code="SUP-0001", name="Hotel")

    def setUp(self):
        self.api = APIClient()
        self.api.force_authenticate(get_user_model().objects.create_user("acc", password="x", is_staff=True))

    def entry(self, lines, d=date(2026, 9, 1), source="manual"):
        je = JournalEntry.objects.create(entry_number=next_number(JournalEntry, "entry_number", "JE"),
                                         date=d, source=source, is_posted=True, description="t")
        for code, dr, cr in lines:
            JournalEntryLine.objects.create(journal_entry=je, account=self.acc[code],
                                            debit=Decimal(dr), credit=Decimal(cr))
        return je

    def invoice(self, lines=(("1.5", "10.33"), ("1.5", "10.33")), tax=None):
        inv = Invoice.objects.create(invoice_number=next_number(Invoice, "invoice_number", "INV"),
                                     customer=self.customer, date=date(2026, 9, 1), due_date=date(2026, 10, 1))
        for q, p in lines:
            InvoiceLine.objects.create(invoice=inv, quantity=Decimal(q), unit_price=Decimal(p),
                                       account=self.acc["71243"], tax_code=tax)
        inv.refresh_from_db()
        inv.subtotal = sum((Decimal(q) * Decimal(p) for q, p in lines), Decimal("0"))
        inv.total = inv.subtotal
        inv.save()
        return inv

    # 1. Tax report
    def test_both_type_tax_is_not_counted_twice(self):
        self.entry([("3421", "1200", "0"), ("71243", "0", "1000"), ("4455", "0", "200")])
        data = self.api.get("/api/v1/reports/tax", {"date_from": "2026-01-01", "date_to": "2026-12-31"}).json()["data"]
        self.assertEqual(Decimal(data["net_tax_payable"]), Decimal("200"))

    # 2. Payments come from the bank statement only
    def test_payments_are_not_booked_from_the_payments_page(self):
        r = self.api.post("/api/v1/payments", {"type": "outgoing", "date": "2026-09-05", "amount": "500",
                                               "bank_account_id": str(self.acc["51411"].id),
                                               "supplier_id": str(self.supplier.id)}, format="json")
        self.assertEqual(r.status_code, 400)
        self.assertIn("bank statement", r.json()["message"])
        self.assertFalse(Payment.objects.exists())
        self.assertFalse(JournalEntry.objects.exists())

    # 5 + 7. Posting balances after rounding; editing a posted invoice re-posts it
    def test_invoice_posting_balances_and_follows_edits(self):
        inv = self.invoice()
        self.assertEqual(self.api.post(f"/api/v1/invoices/{inv.id}/post").status_code, 200)
        inv.refresh_from_db()
        self.assertTrue(balanced(inv.journal_entry))
        self.assertEqual(inv.total, inv.journal_entry.lines.get(debit__gt=0).debit)
        r = self.api.put(f"/api/v1/invoices/{inv.id}", {"lines": [
            {"description": "x", "quantity": "1", "unit_price": "800", "account_id": str(self.acc["71243"].id)}]},
            format="json")
        self.assertEqual(r.status_code, 200, r.content)
        inv.refresh_from_db()
        self.assertEqual(inv.journal_entry.lines.get(debit__gt=0).debit, Decimal("800"))
        self.assertEqual(JournalEntry.objects.filter(source="invoice").count(), 1)

    def test_posted_invoice_in_closed_year_cannot_be_edited(self):
        inv = self.invoice(lines=(("1", "100"),))
        self.api.post(f"/api/v1/invoices/{inv.id}/post")
        FiscalYear.objects.create(name="2026", start_date=date(2026, 1, 1), end_date=date(2026, 12, 31),
                                  is_closed=True)
        r = self.api.put(f"/api/v1/invoices/{inv.id}", {"notes": "x"}, format="json")
        self.assertEqual(r.status_code, 400)

    # 7. Credit note uses its own tax and balances
    def test_credit_note_without_invoice_entry_balances(self):
        inv = self.invoice(lines=(("1", "1000"),), tax=self.vat)
        inv.tax_amount, inv.total = Decimal("200"), Decimal("1200")
        inv.save()
        cn = CreditNote.objects.create(credit_note_number="CN-0001", customer=self.customer, invoice=inv,
                                       date=date(2026, 9, 10), subtotal=Decimal("100"), tax_amount=Decimal("20"),
                                       total=Decimal("120"))
        r = self.api.post(f"/api/v1/credit-notes/{cn.id}/apply", {}, format="json")
        self.assertEqual(r.status_code, 200, r.content)
        cn.refresh_from_db()
        self.assertTrue(balanced(cn.journal_entry))
        self.assertEqual(cn.journal_entry.lines.get(account=self.acc["4455"]).debit, Decimal("20"))

    # 6. TVA on margin once per period
    def test_margin_cannot_be_recognised_twice(self):
        self.entry([("3421", "1200", "0"), ("71243", "0", "1200")], source="invoice")
        body = {"date_from": "2026-09-01", "date_to": "2026-09-30", "entry_date": "2026-09-30"}
        self.assertEqual(self.api.post("/api/v1/margin-recognition/create", body, format="json").status_code, 201)
        tva = JournalEntry.objects.get(source="tva_margin")
        self.assertEqual(tva.lines.get(account__code="4455").credit, Decimal("200.00"))
        self.assertEqual(tva.lines.get(account__code="71243").debit, Decimal("200.00"))
        self.assertEqual(self.api.post("/api/v1/margin-recognition/create", body, format="json").status_code, 400)
        overlap = {"date_from": "2026-09-15", "date_to": "2026-10-15", "entry_date": "2026-10-15"}
        self.assertEqual(self.api.post("/api/v1/margin-recognition/create", overlap, format="json").status_code, 400)

    # 3 + 10. Expenses: right bank/cash account, rounded, status not editable
    def test_expense_accounts_rounding_and_status(self):
        bank = Expense.objects.create(date=date(2026, 9, 3), description="Taxi", amount=Decimal("10.33"),
                                      tax_code=self.vat, account=self.acc["61254"], payment_method="bank_transfer")
        cash = Expense.objects.create(date=date(2026, 9, 3), description="Water", amount=Decimal("50"),
                                      account=self.acc["61254"], payment_method="cash")
        self.assertEqual(self.api.put(f"/api/v1/expenses/{cash.id}", {"status": "approved"},
                                      format="multipart").status_code, 200)
        cash.refresh_from_db()
        self.assertEqual(cash.status, "pending")
        # A bank-paid expense is booked from the bank statement, not here.
        r = self.api.post(f"/api/v1/expenses/{bank.id}/approve", {"bank_account_id": str(self.acc["51411"].id)},
                          format="json")
        self.assertEqual(r.status_code, 400)
        self.assertEqual(self.api.post(f"/api/v1/expenses/{bank.id}/approve").status_code, 200)
        self.assertEqual(self.api.post(f"/api/v1/expenses/{cash.id}/approve").status_code, 200)
        for e in (bank, cash):
            e.refresh_from_db()
            self.assertTrue(balanced(e.journal_entry))
            self.assertEqual(e.journal_entry.lines.get(credit__gt=0).account.code, "51611")
            self.assertEqual(e.journal_entry.journal.code, "CA")

    # 9. An entry with dependents cannot be deleted
    def test_entry_belonging_to_an_invoice_cannot_be_deleted(self):
        inv = self.invoice(lines=(("1", "100"),))
        self.api.post(f"/api/v1/invoices/{inv.id}/post")
        inv.refresh_from_db()
        je = inv.journal_entry
        self.api.post(f"/api/v1/journal-entries/{je.id}/unpost")
        self.assertEqual(self.api.delete(f"/api/v1/journal-entries/{je.id}").status_code, 400)
        self.assertTrue(JournalEntry.objects.filter(id=je.id).exists())

    # 11. Numbering and amounts
    def test_numbering_ignores_other_series_and_thousands_parse(self):
        Invoice.objects.create(invoice_number="VMM-2026-0150", customer=self.customer,
                               date=date(2026, 9, 1), due_date=date(2026, 9, 1))
        Invoice.objects.create(invoice_number="INV-0007", customer=self.customer,
                               date=date(2026, 9, 1), due_date=date(2026, 9, 1))
        from sales.views import _next_invoice_number
        self.assertEqual(_next_invoice_number(), "INV-0008")
        from journals.views import _safe_decimal
        self.assertEqual(_safe_decimal("1,234,567"), Decimal("1234567"))
        self.assertEqual(_safe_decimal("1.500,50"), Decimal("1500.50"))


class EuroAccountTests(TestCase):
    """Euros on CIH 600 EUR (51413) have no dirham value until exchanged into CIH 300."""

    @classmethod
    def setUpTestData(cls):
        seed_chart()
        cls.acc = {a.code: a for a in Account.objects.all()}

    setUp = LedgerTests.setUp
    entry = LedgerTests.entry

    def euro_receipt(self):
        je = JournalEntry.objects.create(entry_number=next_number(JournalEntry, "entry_number", "JE"),
                                         date=date(2026, 9, 1), source="bank", is_posted=True, description="eur")
        for code, dr, cr in (("51413", "7000", "0"), ("34972", "0", "7000")):
            JournalEntryLine.objects.create(journal_entry=je, account=self.acc[code], currency="EUR",
                                            debit=Decimal(dr), credit=Decimal(cr))
        return je

    def test_eur_accounts_are_eur(self):
        self.assertEqual(self.acc["51413"].currency, "EUR")
        self.assertEqual(self.acc["34972"].currency, "EUR")
        self.assertEqual(self.acc["51411"].currency, "MAD")

    def test_euros_stay_out_of_dirham_reports(self):
        self.euro_receipt()
        self.entry([("51411", "1000", "0"), ("71243", "0", "1000")])
        tb = self.api.get("/api/v1/reports/trial-balance").json()["data"]
        codes = {r["account_code"]: r for r in tb["rows"]}
        self.assertNotIn("51413", codes)
        self.assertEqual(Decimal(tb["total_debit"]), Decimal("1000"))
        self.assertTrue(tb["is_balanced"])
        foreign = {r["account_code"]: r for r in tb["foreign_rows"]}
        self.assertEqual((foreign["51413"]["currency"], Decimal(foreign["51413"]["balance"])), ("EUR", Decimal("7000")))
        bs = self.api.get("/api/v1/reports/balance-sheet").json()["data"]
        self.assertNotIn("51413", {r["account_code"] for r in bs["assets"]["rows"]})
        self.assertIn("51413", {r["account_code"] for r in bs["foreign_rows"]})

    def test_eur_ledger_balance_is_in_euros(self):
        self.euro_receipt()
        data = self.api.get(f"/api/v1/accounts/{self.acc['51413'].id}/ledger").json()["data"]
        self.assertEqual(data["account"]["currency"], "EUR")
        self.assertEqual(Decimal(data["lines"][-1]["running_balance"]), Decimal("7000"))
