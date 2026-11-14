"""Debitorer/kreditorer og udligning — kør: manage.py test journals.tests_lettrage"""

from datetime import date
from decimal import Decimal

from django.db import transaction

from accounts import chart
from core.testing import LedgerTestCase
from purchases.models import Bill, BillLine, Supplier
from purchases.views import _apply_bill_payment, _approve_bill

from .closing import close_month
from .lettrage import _code, _index
from .models import Journal, JournalEntry, JournalEntryLine
from .numbering import next_je_number


AP, COST, SUSP = chart.PAYABLE, "2810", chart.SUSPENSE


class LettrageTests(LedgerTestCase):
    def setUp(self):
        super().setUp()
        self.supplier = Supplier.objects.create(code="L-0001", name="Kontorland ApS")

    def tiers(self):
        return {"partner_type": "supplier", "partner_id": str(self.supplier.id), "partner_name": self.supplier.name}

    def lentry(self, d, lines, journal="DIV"):
        je = JournalEntry.objects.create(journal=Journal.objects.get(code=journal), entry_number=next_je_number(),
                                         date=d, source="manual", is_posted=True, description="t")
        out = []
        for code, dr, cr in lines:
            extra = self.tiers() if code == AP else {}
            out.append(JournalEntryLine.objects.create(journal_entry=je, account=self.acc(code),
                                                       debit=Decimal(dr), credit=Decimal(cr), **extra))
        return out

    def test_codes_run_aa_to_zz_then_aaa(self):
        self.assertEqual([_code(0), _code(1), _code(675), _code(676)], ["AA", "AB", "ZZ", "AAA"])
        for n in (0, 25, 26, 675, 676, 1000):
            self.assertEqual(_index(_code(n)), n)

    def test_manual_lettrage_needs_balance_and_can_be_undone(self):
        bill = self.lentry(date(2026, 1, 5), [(COST, "1000", "0"), (AP, "0", "1000")])[1]
        part = self.lentry(date(2026, 1, 9), [(AP, "600", "0"), (SUSP, "0", "600")])[0]
        rest = self.lentry(date(2026, 1, 20), [(AP, "400", "0"), (SUSP, "0", "400")])[0]
        r = self.post("/api/v1/lettrage", {"line_ids": [str(bill.id), str(part.id)]})
        self.assertEqual(r.status_code, 400)
        r = self.post("/api/v1/lettrage", {"line_ids": [str(bill.id), str(part.id), str(rest.id)]})
        self.assertEqual(r.status_code, 200, r.content)
        for l in (bill, part, rest):
            l.refresh_from_db()
            self.assertEqual(l.lettrage, "AA")
        open_ = self.get("/api/v1/tiers/lines", {"account": AP, "partner_id": str(self.supplier.id)}).json()["data"]["lines"]
        self.assertEqual(open_, [])
        r = self.post("/api/v1/lettrage/undo", {"account": AP, "partner_id": str(self.supplier.id),
                                                    "code": "AA"})
        self.assertEqual(r.status_code, 200)
        bill.refresh_from_db()
        self.assertEqual(bill.lettrage, "")

    def test_lines_of_a_closed_month_can_still_be_lettered_but_not_changed(self):
        bill = self.lentry(date(2026, 1, 5), [(COST, "1000", "0"), (AP, "0", "1000")])[1]
        close_month(2026, 1, "test", confirm_warnings=True)
        pay = self.lentry(date(2026, 2, 3), [(AP, "1000", "0"), (SUSP, "0", "1000")])[0]
        r = self.post("/api/v1/lettrage", {"line_ids": [str(bill.id), str(pay.id)]})
        self.assertEqual(r.status_code, 200, r.content)
        bill.refresh_from_db()
        self.assertEqual((bill.lettrage, bill.journal_entry.status), ("AA", "validated"))
        bill.debit = Decimal("1")
        with self.assertRaises(Exception), transaction.atomic():
            bill.save()

    def test_a_paid_bill_is_lettered_with_its_payment(self):
        bill = Bill.objects.create(bill_number="B-1", supplier=self.supplier, date=date(2026, 3, 1),
                                   due_date=date(2026, 3, 31), total=Decimal("500"), subtotal=Decimal("500"))
        BillLine.objects.create(bill=bill, description="Nuits", quantity=1, unit_price=Decimal("500"),
                                amount=Decimal("500"), account=self.acc(COST))
        ok, err = _approve_bill(bill, "acc")
        self.assertTrue(ok, err)
        bank = self.lentry(date(2026, 3, 10), [(SUSP, "500", "0"), (chart.BANK, "0", "500")], journal="BANK")[1]
        bill.refresh_from_db()
        with transaction.atomic():
            link, err = _apply_bill_payment(Bill.objects.select_for_update().get(id=bill.id), bank, Decimal("500"), "acc")
        self.assertIsNone(err)
        ap = JournalEntryLine.objects.filter(account__code=AP)
        self.assertEqual(ap.count(), 2)
        self.assertEqual({l.lettrage for l in ap}, {"AA"})
        self.assertEqual({l.partner_id for l in ap}, {str(self.supplier.id)})

    def test_manual_line_on_payables_needs_a_supplier(self):
        payload = {"date": "2026-04-01", "journal_code": "KØB", "lines": [
            {"account_id": str(self.acc(COST).id), "debit": "100"},
            {"account_id": str(self.acc(AP).id), "credit": "100"}]}
        r = self.post("/api/v1/journal-entries", payload)
        self.assertEqual(r.status_code, 400)
        payload["lines"][1]["partner_id"] = str(self.supplier.id)
        r = self.post("/api/v1/journal-entries", payload)
        self.assertEqual(r.status_code, 201, r.content)
        line = JournalEntryLine.objects.get(account__code=AP)
        self.assertEqual((line.partner_type, line.partner_name), ("supplier", "Kontorland ApS"))

    def test_aging_comes_from_open_ledger_lines(self):
        self.lentry(date(2026, 1, 5), [(COST, "1000", "0"), (AP, "0", "1000")])
        self.lentry(date(2026, 1, 9), [(AP, "300", "0"), (SUSP, "0", "300")])
        data = self.get("/api/v1/reports/aging-payable", {"as_of": "2026-05-01"}).json()["data"]
        row = data["rows"][0]
        self.assertEqual((row["supplier_name"], Decimal(row["total"])), ("Kontorland ApS", Decimal("700")))
        # 116 dage gammel, 30 dages frist (renteloven § 3) → 86 dage over forfald
        self.assertEqual(Decimal(row["days_61_90"]), Decimal("700"))
