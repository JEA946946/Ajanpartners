"""Moms: bogføring pr. momskode, momsangivelsens felter, afregning og lås.

Kør: manage.py test core.tests_vat
"""

from datetime import date

from accounts import chart
from core import vat
from core.testing import D, LedgerTestCase, balanced
from journals.models import JournalEntry, JournalEntryLine
from purchases.models import Supplier
from sales.models import Customer

COST = "2810"


class VatTests(LedgerTestCase):
    def setUp(self):
        super().setUp()
        self.dk = Customer.objects.create(code="K1", name="Dansk Kunde ApS", address="Vej 1, 8000 Aarhus C",
                                          tax_id="87654321")
        self.eu = Customer.objects.create(code="K2", name="German GmbH", address="Strasse 1, Berlin",
                                          country="DE", vat_zone="eu", tax_id="DE123456789")
        self.supplier = Supplier.objects.create(code="L1", name="Leverandør A/S")

    def invoice(self, customer, lines, d="2026-02-10"):
        r = self.post("/api/v1/invoices", {"customer_id": str(customer.id), "date": d, "lines": [
            {"description": desc, "quantity": "1", "unit_price": price, "tax_code_id": str(self.tax(code).id)}
            for desc, price, code in lines]})
        self.assertEqual(r.status_code, 201, r.content)
        inv = r.json()["invoice"]
        r = self.post(f"/api/v1/invoices/{inv['id']}/post")
        self.assertEqual(r.status_code, 200, r.content)
        return r.json()["invoice"]

    def bill(self, lines, d="2026-02-12"):
        r = self.post("/api/v1/bills", {"supplier_id": str(self.supplier.id), "date": d, "due_date": d,
                                        "bill_number": f"R-{len(lines)}-{d}", "lines": [
            {"description": "køb", "quantity": "1", "unit_price": price, "account_id": str(self.acc(account).id),
             "tax_code_id": str(self.tax(code).id)} for price, code, account in lines]})
        self.assertEqual(r.status_code, 201, r.content)
        b = r.json()["data"]["bill"]
        r = self.post(f"/api/v1/bills/{b['id']}/approve")
        self.assertEqual(r.status_code, 200, r.content)
        return b

    def test_invoice_number_is_given_when_posted_and_lines_carry_vat_codes(self):
        inv = self.invoice(self.dk, [("Rådgivning", "1000", "S01")])
        self.assertEqual(inv["invoice_number"], "1")
        self.assertEqual((D(inv["subtotal"]), D(inv["tax_amount"]), D(inv["total"])), (D(1000), D(250), D(1250)))
        je = JournalEntry.objects.get(source="invoice")
        self.assertTrue(balanced(je))
        self.assertEqual(je.journal.code, "SALG")
        b = self.balances(je)
        self.assertEqual(b[(chart.REVENUE, "S01")], (0, D(1000)))
        self.assertEqual(b[(chart.VAT_OUTPUT, "S01")], (0, D(250)))
        self.assertEqual(b[(chart.RECEIVABLE, "")], (D(1250), 0))
        self.assertEqual(self.invoice(self.dk, [("Mere", "10", "S01")])["invoice_number"], "2")

    def test_posted_invoice_cannot_be_edited(self):
        inv = self.invoice(self.dk, [("Rådgivning", "1000", "S01")])
        r = self.put(f"/api/v1/invoices/{inv['id']}", {"notes": "x"})
        self.assertEqual(r.status_code, 400)
        self.assertIn("kreditnota", r.json()["message"])

    def test_eu_b2b_needs_vat_number_and_says_reverse_charge(self):
        no_vat = Customer.objects.create(code="K3", name="EU uden nr", address="Rue 1, Paris", vat_zone="eu")
        r = self.post("/api/v1/invoices", {"customer_id": str(no_vat.id), "date": "2026-02-10", "lines": [
            {"description": "Ydelse", "quantity": "1", "unit_price": "100", "tax_code_id": str(self.tax("S23").id)}]})
        r = self.post(f"/api/v1/invoices/{r.json()['invoice']['id']}/post")
        self.assertEqual(r.status_code, 400)
        self.assertIn("momsnummer", r.json()["message"])
        inv = self.invoice(self.eu, [("Ydelse", "2000", "S23")])
        self.assertTrue(inv["print"]["reverse_charge"])
        self.assertIn("Omvendt betalingspligt", inv["print"]["legal_notes"])
        self.assertEqual(D(inv["tax_amount"]), 0)
        line = JournalEntryLine.objects.get(vat_code="S23")
        self.assertEqual((line.account.code, line.credit), (chart.REVENUE_EU_SERVICES, D(2000)))

    def test_public_customer_needs_ean(self):
        pub = Customer.objects.create(code="K4", name="Kommune", address="Rådhuset", is_public=True)
        r = self.post("/api/v1/invoices", {"customer_id": str(pub.id), "date": "2026-02-10", "lines": [
            {"description": "Ydelse", "quantity": "1", "unit_price": "100", "tax_code_id": str(self.tax("S01").id)}]})
        r = self.post(f"/api/v1/invoices/{r.json()['invoice']['id']}/post")
        self.assertIn("EAN", r.json()["message"])

    def test_purchase_codes(self):
        self.bill([("400", "K010", COST)])
        self.bill([("1000", "K070", "1910")])                  # restaurant/repræsentation: 25 % fradrag
        self.bill([("1000", "K260", "1710")])                  # EU-ydelseskøb, omvendt betalingspligt
        self.bill([("300", "E-EL", "2050")])                   # elafgift (godtgørelse)
        bal = lambda code: sum((l.debit - l.credit for l in JournalEntryLine.objects.filter(account__code=code)), D(0))
        self.assertEqual(bal(chart.VAT_INPUT), D("100") + D("62.50") + D("250"))
        self.assertEqual(bal("1910"), D("1187.50"))
        self.assertEqual(bal(chart.VAT_EU_SERVICES), D("-250"))
        self.assertEqual(bal(chart.TAX_ELECTRICITY), D("300"))
        self.assertEqual(bal(chart.PAYABLE), -(D("500") + D("1250") + D("1000") + D("300")))
        for je in JournalEntry.objects.filter(source="expense"):
            self.assertTrue(balanced(je))

    def test_vat_return_fields_settlement_and_lock(self):
        self.invoice(self.dk, [("Salg", "1000", "S01")])
        self.invoice(self.eu, [("Ydelse", "2000", "S23"), ("Varer", "300", "S21")])
        self.invoice(self.dk, [("Eksport", "500", "S41")])
        self.bill([("400", "K010", COST)])
        self.bill([("1000", "K070", "1910")])
        self.bill([("1000", "K260", "1710")])
        self.bill([("800", "K210", "1630")])
        self.bill([("300.40", "E-EL", "2050")])
        r = self.get("/api/v1/vat/report", {"start": "2026-01-01", "end": "2026-03-31"})
        self.assertEqual(r.status_code, 200, r.content)
        f = {x["key"]: D(x["amount"]) for x in r.json()["data"]["fields"]}
        self.assertEqual(f["salgsmoms"], D(250))
        self.assertEqual(f["moms_ydelseskoeb_udland"], D(250))
        self.assertEqual(f["moms_varekoeb_udland"], D(200))
        self.assertEqual(f["koebsmoms"], D(100) + D("62.50") + D(250) + D(200))
        self.assertEqual(f["elafgift"], D("300.40"))
        self.assertEqual(f["rubrik_a_ydelser"], D(1000))
        self.assertEqual(f["rubrik_a_varer"], D(800))
        self.assertEqual(f["rubrik_b_ydelser"], D(2000))
        self.assertEqual(f["rubrik_b_varer_indberettes"], D(300))
        self.assertEqual(f["rubrik_c"], D(500))
        self.assertEqual(f["momstilsvar"], D(250) + D(250) + D(200) - D("612.50") - D("300.40"))
        recon = r.json()["data"]["reconciliation"]
        self.assertTrue(all(D(x["manual"]) == 0 for x in recon), recon)

        self.assertEqual(self.post("/api/v1/vat/file", {"start": "2026-01-01", "end": "2026-03-31"}).status_code, 400)
        r = self.post("/api/v1/vat/settle", {"start": "2026-01-01", "end": "2026-03-31"})
        self.assertEqual(r.status_code, 200, r.content)
        je = JournalEntry.objects.get(source="vat_settlement")
        self.assertTrue(balanced(je))
        for code in chart.VAT_ACCOUNTS:
            self.assertEqual(sum((l.debit - l.credit for l in JournalEntryLine.objects.filter(account__code=code)),
                                 D(0)), 0, code)
        settle = je.lines.get(account__code=chart.VAT_SETTLEMENT)
        self.assertEqual(settle.debit - settle.credit, D(213))  # tilgode, hele kroner (−212,90 → −213)
        self.assertEqual(self.post("/api/v1/vat/settle", {"start": "2026-01-01", "end": "2026-03-31"}).status_code, 400)

        r = self.post("/api/v1/vat/file", {"start": "2026-01-01", "end": "2026-03-31", "receipt_number": "123"})
        self.assertEqual(r.status_code, 200, r.content)
        r = self.post("/api/v1/journal-entries", {"date": "2026-02-01", "lines": [
            {"account_id": str(self.acc(COST).id), "debit": "5"},
            {"account_id": str(self.acc(chart.CASH).id), "credit": "5"}]})
        self.assertEqual(r.status_code, 400)
        self.assertIn("Momsperioden", r.json()["message"])

    def test_periods_follow_client_vat_period_with_deadlines(self):
        r = self.get("/api/v1/vat/periods", {"year": 2026}).json()["data"]
        self.assertEqual([p["deadline"] for p in r["periods"]], ["2026-06-01", "2026-09-01", "2026-12-01", "2027-03-01"])
        self.assertEqual(vat.deadline(date(2026, 1, 31), "month"), date(2026, 2, 25))
        self.assertEqual([p[0].month for p in vat.periods_for(2026, "half")], [1, 7])
        self.assertEqual(self.get("/api/v1/vat/report", {"start": "2026-01-01", "end": "2026-01-31"}).status_code, 400)
