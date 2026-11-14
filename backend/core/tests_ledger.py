"""Bøgerne følger dokumenterne, og hver postering balancerer.

Kør: manage.py test core.tests_ledger
"""

from datetime import date

from django.core.files.uploadedfile import SimpleUploadedFile
from django.db import connection

from accounts import chart
from core.testing import D, LedgerTestCase, balanced
from journals.models import JournalEntry, JournalEntryLine
from purchases.models import Supplier
from sales.models import Customer, Invoice, Reminder


class LedgerTests(LedgerTestCase):
    def setUp(self):
        super().setUp()
        self.customer = Customer.objects.create(code="K1", name="Kunde ApS", address="Vej 1, 8000 Aarhus C",
                                                tax_id="87654321")
        self.supplier = Supplier.objects.create(code="L1", name="Leverandør GmbH", country="DE")

    def issue(self, price="1000", d="2026-02-10", **extra):
        r = self.post("/api/v1/invoices", {"customer_id": str(self.customer.id), "date": d, **extra, "lines": [
            {"description": "Rådgivning", "quantity": "1", "unit_price": price,
             "tax_code_id": str(self.tax("S01").id)}]})
        self.assertEqual(r.status_code, 201, r.content)
        inv = r.json()["invoice"]
        self.assertTrue(inv["is_draft_number"])
        r = self.post(f"/api/v1/invoices/{inv['id']}/post")
        self.assertEqual(r.status_code, 200, r.content)
        return r.json()["invoice"]

    def test_draft_invoice_gets_due_date_from_terms(self):
        r = self.post("/api/v1/invoices", {"customer_id": str(self.customer.id), "date": "2026-02-10",
                                           "payment_terms_code": "lm30", "lines": [
            {"description": "x", "quantity": "2", "unit_price": "10.005", "tax_code_id": str(self.tax("S01").id)}]})
        inv = r.json()["invoice"]
        self.assertEqual(inv["due_date"], "2026-03-30")
        self.assertEqual(self.delete(f"/api/v1/invoices/{inv['id']}").status_code, 200)

    def test_credit_note_mirrors_the_invoice_with_vat(self):
        inv = self.issue("1000")
        r = self.post("/api/v1/credit-notes", {"customer_id": str(self.customer.id), "invoice_id": inv["id"],
                                               "date": "2026-02-20", "total": "625"})
        self.assertEqual(r.status_code, 201, r.content)
        cn = r.json()["credit_note"]
        r = self.post(f"/api/v1/credit-notes/{cn['id']}/apply")
        self.assertEqual(r.status_code, 200, r.content)
        je = JournalEntry.objects.get(source="credit_note")
        self.assertTrue(balanced(je))
        b = self.balances(je)
        self.assertEqual(b[(chart.REVENUE, "S01")], (D(500), 0))
        self.assertEqual(b[(chart.VAT_OUTPUT, "S01")], (D(125), 0))
        self.assertEqual(b[(chart.RECEIVABLE, "")], (0, D(625)))
        self.assertEqual(r.json()["credit_note"]["credit_note_number"], "1")

    def test_quote_becomes_draft_invoice(self):
        r = self.post("/api/v1/quotes", {"customer_id": str(self.customer.id), "date": "2026-02-01", "lines": [
            {"description": "Opgave", "quantity": "3", "unit_price": "500", "tax_code_id": str(self.tax("S01").id)}]})
        self.assertEqual(r.status_code, 201, r.content)
        q = r.json()["quote"]
        self.assertEqual((D(q["total"]), q["valid_until"]), (D("1875"), "2026-03-03"))
        r = self.post(f"/api/v1/quotes/{q['id']}/invoice", {"date": "2026-02-05"})
        self.assertEqual(r.status_code, 201, r.content)
        inv = Invoice.objects.get(id=r.json()["invoice_id"])
        self.assertEqual((inv.total, str(inv.quote_id), inv.status), (D("1875"), q["id"], "draft"))
        self.assertEqual(self.post(f"/api/v1/quotes/{q['id']}/invoice").status_code, 400)

    def test_reminders_follow_renteloven(self):
        inv = self.issue("1000", d="2026-01-05")  # netto 14 → forfald 19/1
        self.assertEqual(self.post("/api/v1/reminders", {"invoice_id": inv["id"], "date": "2026-01-15"}).status_code,
                         400)  # ikke forfalden
        self.assertEqual(self.post("/api/v1/reminders", {"invoice_id": inv["id"], "date": "2026-01-25",
                                                         "fee": "150"}).status_code, 400)  # over 100 kr.
        r = self.post("/api/v1/reminders", {"invoice_id": inv["id"], "date": "2026-01-25"})
        self.assertEqual(r.status_code, 201, r.content)
        je = JournalEntry.objects.get(source="reminder")
        self.assertEqual(self.balances(je)[(chart.REMINDER_FEES, "")], (0, D(100)))
        self.assertEqual(self.post("/api/v1/reminders", {"invoice_id": inv["id"], "date": "2026-01-30"}).status_code,
                         400)  # under 10 dage
        for d in ("2026-02-04", "2026-02-14"):
            self.assertEqual(self.post("/api/v1/reminders", {"invoice_id": inv["id"], "date": d}).status_code, 201)
        r = self.post("/api/v1/reminders", {"invoice_id": inv["id"], "date": "2026-03-01"})
        self.assertIn("3 rykkere", r.json()["message"])
        self.assertEqual(Reminder.objects.count(), 3)
        cands = self.get("/api/v1/reminders/candidates", {"date": "2026-03-01"}).json()["candidates"]
        self.assertEqual((cands[0]["reminders_sent"], cands[0]["can_remind"]), (3, False))

    def test_bill_in_euro_is_booked_in_dkk_with_currency_amount(self):
        r = self.post("/api/v1/bills", {"supplier_id": str(self.supplier.id), "date": "2026-02-12",
                                        "due_date": "2026-03-12", "bill_number": "DE-77", "currency": "EUR",
                                        "exchange_rate": "7.4600", "lines": [
            {"description": "Software", "quantity": "1", "unit_price": "100", "account_id": str(self.acc("2310").id),
             "tax_code_id": str(self.tax("K260").id)}]})
        self.assertEqual(r.status_code, 201, r.content)
        bill = r.json()["data"]["bill"]
        self.assertEqual(D(bill["total"]), D(100))  # EU-ydelse: leverandøren fakturerer uden moms
        self.assertEqual(self.post(f"/api/v1/bills/{bill['id']}/approve").status_code, 200)
        je = JournalEntry.objects.get(source="expense")
        self.assertTrue(balanced(je))
        cost = je.lines.get(account__code="2310")
        self.assertEqual((cost.debit, cost.currency, cost.amount_currency), (D("746.00"), "EUR", D("100.00")))
        ap = je.lines.get(account__code=chart.PAYABLE)
        self.assertEqual((ap.credit, ap.partner_id), (D("746.00"), str(self.supplier.id)))
        self.assertEqual(je.lines.get(account__code=chart.VAT_EU_SERVICES).credit, D("186.50"))
        self.assertEqual(je.lines.get(account__code=chart.VAT_INPUT).debit, D("186.50"))

    def upload_bank(self, content):
        try:
            return self.api.post("/api/v1/bank-statements/upload", {
                "file": SimpleUploadedFile("kontoudtog.csv", content.encode("utf-8"), content_type="text/csv"),
                "bank_account_id": str(self.acc(chart.BANK).id)}, format="multipart")
        finally:
            connection.set_tenant(self.tenant)

    def test_danish_bank_csv_import_and_categorise_with_vat(self):
        csv = ("Dato;Tekst;Beløb;Saldo\n"
               "03-02-2026;Dankort-køb OFFICE SHOP 1234;-1.250,00;8.750,00\n"
               "05-02-2026;Overførsel fra Kunde ApS;2.500,00;11.250,00\n")
        r = self.upload_bank(csv)
        self.assertEqual(r.status_code, 200, r.content)
        txns = r.json()["data"]["transactions"]
        self.assertEqual([(t["date"], D(t["debit"]), D(t["credit"])) for t in txns],
                         [("2026-02-03", D("1250"), 0), ("2026-02-05", 0, D("2500"))])
        r = self.post("/api/v1/bank-statements/confirm", {"bank_account_id": str(self.acc(chart.BANK).id),
                                                          "transactions": txns, "filename": "kontoudtog.csv"})
        self.assertEqual(r.status_code, 201, r.content)
        out = JournalEntryLine.objects.get(account__code=chart.BANK, credit=D("1250"))
        self.assertEqual(out.journal_entry.journal.code, "BANK")
        r = self.post(f"/api/v1/transactions/{out.id}/categorize", {"lines": [
            {"account_id": str(self.acc("2450").id), "amount": "1250", "tax_code_id": str(self.tax("K010").id)}]})
        self.assertEqual(r.status_code, 201, r.content)
        je = out.journal_entry
        self.assertTrue(balanced(je))
        b = self.balances(je)
        self.assertEqual(b[("2450", "K010")], (D("1000.00"), 0))
        self.assertEqual(b[(chart.VAT_INPUT, "K010")], (D("250.00"), 0))
        self.assertFalse(je.lines.filter(account__code=chart.SUSPENSE).exists())
        # Samme fil igen: dubletter springes over.
        r = self.post("/api/v1/bank-statements/confirm", {"bank_account_id": str(self.acc(chart.BANK).id),
                                                          "transactions": txns})
        self.assertEqual(r.json()["data"]["skipped"], 2)

    def test_reports_follow_arl(self):
        self.issue("1000")
        self.entry([("2845", "400", "0"), (chart.BANK, "0", "400")], d=date(2026, 2, 28))
        pnl = self.get("/api/v1/reports/profit-and-loss", {"date_from": "2026-01-01", "date_to": "2026-12-31"})
        data = pnl.json()["data"]
        lines = {s["key"]: D(s["amount"]) for s in data["sections"]}
        self.assertEqual((lines["nettoomsaetning"], lines["personaleomkostninger"]), (D(1000), D(-400)))
        self.assertEqual((lines["bruttofortjeneste"], lines["aarets_resultat"]), (D(1000), D(600)))
        tb = self.get("/api/v1/reports/trial-balance", {"date_from": "2026-02-01", "date_to": "2026-02-28"})
        self.assertTrue(tb.json()["data"]["is_balanced"])
        bs = self.get("/api/v1/reports/balance-sheet", {"date": "2026-12-31"}).json()["data"]
        self.assertTrue(bs["is_balanced"], bs)
        self.assertEqual(D(bs["unallocated_result"]), D(600))
        card = self.get("/api/v1/reports/account-card", {"account": chart.RECEIVABLE, "date_from": "2026-01-01",
                                                         "date_to": "2026-12-31"}).json()["data"]
        self.assertEqual(D(card["closing"]), D(1250))

    def test_bank_receipt_pays_invoice_and_letters_it(self):
        inv = self.issue("1000")
        je = self.entry([(chart.BANK, "1250", "0"), (chart.SUSPENSE, "0", "1250")], d=date(2026, 2, 20),
                        journal="BANK", source="bank")
        bank_line = je.lines.get(account__code=chart.BANK)
        r = self.post(f"/api/v1/transactions/{bank_line.id}/categorize",
                      {"lines": [{"invoice_id": inv["id"], "amount": "1250"}]})
        self.assertEqual(r.status_code, 201, r.content)
        invoice = Invoice.objects.get(id=inv["id"])
        self.assertEqual((invoice.paid_amount, invoice.status), (D("1250"), "paid"))
        ar = JournalEntryLine.objects.filter(account__code=chart.RECEIVABLE)
        self.assertEqual({l.lettrage for l in ar}, {"AA"})
        self.assertEqual(sum((l.debit - l.credit for l in ar), D(0)), 0)
