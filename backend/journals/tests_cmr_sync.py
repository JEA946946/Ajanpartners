"""CRM sync rules (journals/cmr_sync.py) — run with: python manage.py test journals.tests_cmr_sync"""

from datetime import date
from decimal import Decimal

from django.test import TestCase

from accounts.management.commands.seed_accounts import seed_chart
from accounts.models import Account, SupplierAccountMapping
from journals.cmr_sync import audit, parse_paid_date, run_sync
from journals.models import JournalEntry, JournalEntryLine

OPP = "11111111-1111-1111-1111-111111111111"


def row(supplier, amount, paid, idx=0, sent=True, paid_date="05/10/2026 14:30", category="Accommodation",
        supplier_id=None):
    return {
        "opportunity_id": OPP, "opportunity_title": "Trip", "trip_reference": "VFAB051026",
        "category": category, "entry_index": idx, "supplier_name": supplier, "supplier_id": supplier_id,
        "amount": str(amount), "paid": str(paid), "remaining": str(Decimal(amount) - Decimal(paid)),
        "paid_date": paid_date, "sent_to_finance": sent, "bank_account": "RIB 123", "notes": "",
    }


def invoice(status="issued", payment_date=None, total="5000.00", currency="MAD"):
    return {
        "id": "22222222-2222-2222-2222-222222222222", "invoice_number": "INV-7", "invoice_date": "2026-09-01",
        "currency": currency, "total": total, "status": status, "payment_date": payment_date,
        "bank_account": "CIH300", "line_items": [], "customer_name": "Agency", "opportunity_title": "Trip",
        "trip_reference": "VFAB051026", "updated_at": "2026-09-01T10:00:00+00:00",
    }


class CmrSyncTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        seed_chart()

    def booked(self, source="cmr_payment"):
        return [(e.date, e.lines.get(credit=0).debit, e.lines.get(credit=0).account.code)
                for e in JournalEntry.objects.filter(source=source).order_by("entry_number")]

    def test_every_supplier_row_is_booked_not_just_the_first(self):
        run_sync([], [row("Hotel A", 3000, 3000, 0), row("Hotel B", 2000, 2000, 1), row("Riad C", 1000, 1000, 2)], "t")
        self.assertEqual(sorted(a for _, a, _ in self.booked()), [Decimal("1000"), Decimal("2000"), Decimal("3000")])

    def test_only_paid_and_sent_to_finance_money_is_booked(self):
        run_sync([], [row("Hotel A", 10000, 0), row("Hotel B", 4000, 1500), row("Hotel C", 900, 900, sent=False)], "t")
        self.assertEqual([a for _, a, _ in self.booked()], [Decimal("1500")])

    def test_paid_date_is_the_crm_date_in_either_format(self):
        run_sync([], [row("Hotel A", 100, 100, paid_date="05/10/2026 14:30"),
                      row("Hotel B", 100, 100, paid_date="2026-10-07")], "t")
        self.assertEqual(sorted(d for d, _, _ in self.booked()), [date(2026, 10, 5), date(2026, 10, 7)])
        self.assertIsNone(parse_paid_date("not a date"))

    def test_rerun_books_nothing_and_a_second_payment_books_the_increase(self):
        run_sync([], [row("Hotel A", 4000, 1000)], "t")
        run_sync([], [row("Hotel A", 4000, 1000)], "t")
        self.assertEqual(len(self.booked()), 1)
        run_sync([], [row("Hotel A", 4000, 4000, paid_date="20/10/2026 09:00")], "t")
        self.assertEqual([a for _, a, _ in self.booked()], [Decimal("1000"), Decimal("3000")])

    def test_reordered_rows_do_not_double_book(self):
        run_sync([], [row("Hotel A", 3000, 3000, 0), row("Hotel B", 2000, 2000, 1)], "t")
        run_sync([], [row("Hotel B", 2000, 2000, 0), row("Hotel A", 3000, 3000, 1)], "t")
        self.assertEqual(len(self.booked()), 2)

    def test_old_position_keyed_entry_counts_as_booked_and_is_flagged_when_too_high(self):
        # What the old sync left behind: the planned 10,000 booked as paid, keyed by position.
        je = JournalEntry.objects.create(
            entry_number="JE-0001", date=date(2026, 10, 17), source="cmr_payment",
            source_id=f"{OPP}:Accommodation:0", is_posted=True,
            description="Supplier payment — Hotel A —  — Opp: Trip")
        JournalEntryLine.objects.create(journal_entry=je, account=Account.objects.get(code="612631"),
                                        debit=Decimal("10000"), credit=0)
        JournalEntryLine.objects.create(journal_entry=je, account=Account.objects.get(code="51411"),
                                        debit=0, credit=Decimal("10000"))
        result = run_sync([], [row("Hotel A", 10000, 2500)], "t")
        self.assertEqual(result["payments_created"], 0)
        self.assertTrue(any(n["kind"] == "payment_overbooked" and "JE-0001" in n["entries"] for n in result["notes"]))

    def test_supplier_mapping_decides_the_cost_account(self):
        SupplierAccountMapping.objects.create(cmr_supplier_id="sup-1", cmr_supplier_name="Guide X",
                                              account=Account.objects.get(code="612633"))
        run_sync([], [row("Guide X", 800, 800, category="Accommodation", supplier_id="sup-1"),
                      row("Majorelle", 300, 300, category="Entrees")], "t")
        self.assertEqual(sorted(c for _, _, c in self.booked()), ["612633", "612635"])

    def test_crm_paid_flag_books_no_bank_entry(self):
        # Money in comes from the bank statement and is matched there; booking the
        # CRM's "paid" too counted the receipt twice.
        run_sync([invoice()], [], "t")
        result = run_sync([invoice(status="paid", payment_date="2026-09-20")], [], "t")
        self.assertFalse(JournalEntry.objects.filter(source_id__endswith=":payment").exists())
        self.assertIn("invoice_paid_unmatched", {n["kind"] for n in result["notes"]})

    def test_foreign_invoice_is_not_booked_at_face_value(self):
        result = run_sync([invoice(total="1000.00", currency="EUR")], [], "t")
        self.assertEqual(result["invoices_created"], 0)
        self.assertFalse(JournalEntry.objects.filter(source="cmr_invoice").exists())
        self.assertIn("invoice_on_receipt", {n["kind"] for n in result["notes"]})

    def test_changed_invoice_total_is_reported(self):
        run_sync([invoice()], [], "t")
        result = run_sync([invoice(total="4500.00")], [], "t")
        self.assertIn("invoice_total_changed", {n["kind"] for n in result["notes"]})

    def test_dry_run_and_audit_write_nothing(self):
        result = run_sync([invoice()], [row("Hotel A", 100, 100)], "t", dry_run=True)
        self.assertEqual((result["invoices_created"], result["payments_created"]), (1, 1))
        self.assertEqual(JournalEntry.objects.count(), 0)
        report = audit([invoice()], [row("Hotel A", 100, 100)])
        self.assertEqual(len(report["pending"]), 2)  # the invoice and the supplier payment
        self.assertEqual(JournalEntry.objects.count(), 0)

    def test_every_entry_balances(self):
        run_sync([invoice()],
                 [row("Hotel A", 3000, 1234.56), row("Hotel B", 10, 10)], "t")
        for e in JournalEntry.objects.all():
            lines = e.lines.all()
            self.assertEqual(sum(x.debit for x in lines), sum(x.credit for x in lines), e.description)
