"""Tiers and lettrage — run with: python manage.py test journals.tests_lettrage"""

from datetime import date
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.db import transaction
from django.test import TestCase
from rest_framework.test import APIClient

from accounts.management.commands.seed_accounts import seed_chart
from accounts.models import Account
from purchases.models import Bill, BillLine, Supplier
from purchases.views import _apply_bill_payment, _approve_bill

from .closing import close_month
from .lettrage import _code, _index
from .models import Journal, JournalEntry, JournalEntryLine
from .numbering import next_je_number


class LettrageTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        seed_chart()
        cls.acc = {a.code: a for a in Account.objects.all()}
        cls.supplier = Supplier.objects.create(code="SUP-0001", name="Riad Atlas")

    def setUp(self):
        self.api = APIClient()
        self.api.force_authenticate(get_user_model().objects.create_user("acc", password="x", is_staff=True))

    def tiers(self):
        return {"partner_type": "supplier", "partner_id": str(self.supplier.id), "partner_name": self.supplier.name}

    def entry(self, d, lines, journal="OD"):
        je = JournalEntry.objects.create(journal=Journal.objects.get(code=journal), entry_number=next_je_number(),
                                         date=d, source="manual", is_posted=True, description="t")
        out = []
        for code, dr, cr in lines:
            extra = self.tiers() if code == "4411" else {}
            out.append(JournalEntryLine.objects.create(journal_entry=je, account=self.acc[code],
                                                       debit=Decimal(dr), credit=Decimal(cr), **extra))
        return out

    def test_codes_run_aa_to_zz_then_aaa(self):
        self.assertEqual([_code(0), _code(1), _code(675), _code(676)], ["AA", "AB", "ZZ", "AAA"])
        for n in (0, 25, 26, 675, 676, 1000):
            self.assertEqual(_index(_code(n)), n)

    def test_manual_lettrage_needs_balance_and_can_be_undone(self):
        bill = self.entry(date(2026, 1, 5), [("61263", "1000", "0"), ("4411", "0", "1000")])[1]
        part = self.entry(date(2026, 1, 9), [("4411", "600", "0"), ("34971", "0", "600")])[0]
        rest = self.entry(date(2026, 1, 20), [("4411", "400", "0"), ("34971", "0", "400")])[0]
        r = self.api.post("/api/v1/lettrage", {"line_ids": [str(bill.id), str(part.id)]}, format="json")
        self.assertEqual(r.status_code, 400)
        r = self.api.post("/api/v1/lettrage", {"line_ids": [str(bill.id), str(part.id), str(rest.id)]}, format="json")
        self.assertEqual(r.status_code, 200, r.content)
        for l in (bill, part, rest):
            l.refresh_from_db()
            self.assertEqual(l.lettrage, "AA")
        open_ = self.api.get(f"/api/v1/tiers/lines?account=4411&partner_id={self.supplier.id}").json()["data"]["lines"]
        self.assertEqual(open_, [])
        r = self.api.post("/api/v1/lettrage/undo", {"account": "4411", "partner_id": str(self.supplier.id),
                                                    "code": "AA"}, format="json")
        self.assertEqual(r.status_code, 200)
        bill.refresh_from_db()
        self.assertEqual(bill.lettrage, "")

    def test_lines_of_a_closed_month_can_still_be_lettered_but_not_changed(self):
        bill = self.entry(date(2026, 1, 5), [("61263", "1000", "0"), ("4411", "0", "1000")])[1]
        close_month(2026, 1, "acc", confirm_warnings=True)
        pay = self.entry(date(2026, 2, 3), [("4411", "1000", "0"), ("34971", "0", "1000")])[0]
        r = self.api.post("/api/v1/lettrage", {"line_ids": [str(bill.id), str(pay.id)]}, format="json")
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
                                amount=Decimal("500"), account=self.acc["612631"])
        ok, err = _approve_bill(bill, "acc")
        self.assertTrue(ok, err)
        bank = self.entry(date(2026, 3, 10), [("34971", "500", "0"), ("51411", "0", "500")], journal="BQ1")[1]
        bill.refresh_from_db()
        with transaction.atomic():
            link, err = _apply_bill_payment(Bill.objects.select_for_update().get(id=bill.id), bank, Decimal("500"), "acc")
        self.assertIsNone(err)
        ap = JournalEntryLine.objects.filter(account__code="4411")
        self.assertEqual(ap.count(), 2)
        self.assertEqual({l.lettrage for l in ap}, {"AA"})
        self.assertEqual({l.partner_id for l in ap}, {str(self.supplier.id)})

    def test_manual_line_on_4411_needs_a_supplier(self):
        payload = {"date": "2026-04-01", "journal_code": "AC", "lines": [
            {"account_id": str(self.acc["61263"].id), "debit": "100"},
            {"account_id": str(self.acc["4411"].id), "credit": "100"}]}
        r = self.api.post("/api/v1/journal-entries", payload, format="json")
        self.assertEqual(r.status_code, 400)
        payload["lines"][1]["partner_id"] = str(self.supplier.id)
        r = self.api.post("/api/v1/journal-entries", payload, format="json")
        self.assertEqual(r.status_code, 201, r.content)
        line = JournalEntryLine.objects.get(account__code="4411")
        self.assertEqual((line.partner_type, line.partner_name), ("supplier", "Riad Atlas"))

    def test_aging_comes_from_open_ledger_lines(self):
        self.entry(date(2026, 1, 5), [("61263", "1000", "0"), ("4411", "0", "1000")])
        self.entry(date(2026, 1, 9), [("4411", "300", "0"), ("34971", "0", "300")])
        data = self.api.get("/api/v1/reports/aging-payable?as_of=2026-05-01").json()["data"]
        row = data["rows"][0]
        self.assertEqual((row["supplier_name"], Decimal(row["total"])), ("Riad Atlas", Decimal("700")))
        # 116 days old, 60 days term → 56 days overdue
        self.assertEqual(Decimal(row["days_31_60"]), Decimal("700"))


class PayrollTests(TestCase):
    def test_net_pay_is_owed_on_4432_and_not_paid_from_a_bank(self):
        from payroll.models import Employee, PayrollLine, PayrollRun
        seed_chart()
        api = APIClient()
        api.force_authenticate(get_user_model().objects.create_user("acc", password="x", is_staff=True))
        emp = Employee.objects.create(employee_number="E1", first_name="Sara", last_name="B",
                                      gross_salary=Decimal("10000"), salary_account=Account.objects.get(code="61711"))
        run = PayrollRun.objects.create(year=2026, month=3, run_date=date(2026, 3, 31), total_gross=Decimal("10000"),
                                        total_cnss_employee=Decimal("448"), total_cnss_employer=Decimal("2100"),
                                        total_ir=Decimal("900"), total_net=Decimal("8652"))
        PayrollLine.objects.create(payroll_run=run, employee=emp, gross_salary=Decimal("10000"),
                                   cnss_employee=Decimal("448"), cnss_employer=Decimal("2100"),
                                   ir_amount=Decimal("900"), net_salary=Decimal("8652"))
        r = api.post(f"/api/v1/payroll/runs/{run.id}/approve")
        self.assertEqual(r.status_code, 200, r.content)
        je = JournalEntry.objects.get(source="payroll")
        self.assertEqual(je.journal.code, "PA")
        codes = {l.account.code: (l.debit, l.credit) for l in je.lines.all()}
        self.assertEqual(codes["4432"], (Decimal("0"), Decimal("8652")))
        self.assertFalse(any(c.startswith(("514", "516")) for c in codes))
        self.assertEqual(sum(d for d, _ in codes.values()), sum(c for _, c in codes.values()))
