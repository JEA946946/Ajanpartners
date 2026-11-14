"""Journals, month closing, the lock on validated entries and reversals.

Run with: python manage.py test journals.tests_closing
"""

from datetime import date
from decimal import Decimal
from io import StringIO

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.db import DatabaseError, connection, transaction
from django.test import TestCase
from rest_framework.test import APIClient

from accounts.management.commands.seed_accounts import seed_chart
from accounts.models import Account
from core.models import BankReconciliation

from .closing import check_month, close_month, reverse_entry
from .models import Journal, JournalEntry, JournalEntryLine, Period, ValidatedEntryError
from .numbering import next_je_number


class ClosingTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        seed_chart()
        cls.acc = {a.code: a for a in Account.objects.all()}
        cls.j = {j.code: j for j in Journal.objects.all()}

    def setUp(self):
        self.api = APIClient()
        self.api.force_authenticate(get_user_model().objects.create_user("acc", password="x", is_staff=True))

    def entry(self, d, lines, journal="OD", posted=True):
        je = JournalEntry.objects.create(journal=self.j[journal], entry_number=next_je_number(), date=d,
                                         source="manual", is_posted=posted, description="t")
        for code, dr, cr in lines:
            JournalEntryLine.objects.create(journal_entry=je, account=self.acc[code],
                                            debit=Decimal(dr), credit=Decimal(cr))
        return je

    def reconcile(self, code, d):
        BankReconciliation.objects.create(bank_account=self.acc[code], date=d, statement_balance=0,
                                          status="completed")

    def test_journals_are_seeded_with_their_accounts(self):
        self.assertEqual(self.j["BQ1"].account.code, "51411")
        self.assertEqual((self.j["BQ3"].account.code, self.j["BQ3"].currency), ("51413", "EUR"))
        self.assertEqual(self.j["CA"].account.code, "51611")
        self.assertTrue({"AC", "VE", "PA", "OD", "AN"} <= set(self.j))
        self.assertEqual(JournalEntry(source="invoice").journal_id, None)
        self.assertEqual(self.entry(date(2026, 1, 5), [("61254", "10", "0"), ("4411", "0", "10")]).journal.code, "OD")

    def test_closing_numbers_each_journal_in_date_order(self):
        late = self.entry(date(2026, 1, 20), [("51411", "50", "0"), ("34971", "0", "50")], journal="BQ1")
        early = self.entry(date(2026, 1, 3), [("51411", "70", "0"), ("34971", "0", "70")], journal="BQ1")
        od = self.entry(date(2026, 1, 10), [("61254", "10", "0"), ("4411", "0", "10")])
        self.reconcile("51411", date(2026, 1, 31))
        period, check = close_month(2026, 1, "acc", confirm_warnings=True)
        self.assertIsNotNone(period, check)
        for e in (late, early, od):
            e.refresh_from_db()
        self.assertEqual((early.entry_number, late.entry_number), ("BQ1-2026-00001", "BQ1-2026-00002"))
        self.assertEqual(od.entry_number, "OD-2026-00001")
        self.assertEqual(early.status, "validated")

    def test_month_does_not_close_with_drafts_unreconciled_bank_or_out_of_order(self):
        self.entry(date(2026, 1, 3), [("61254", "10", "0"), ("4411", "0", "10")], posted=False)
        self.entry(date(2026, 1, 4), [("51411", "70", "0"), ("34971", "0", "70")], journal="BQ1")
        self.entry(date(2026, 2, 4), [("61254", "10", "0"), ("4411", "0", "10")])
        blockers = " | ".join(check_month(2026, 1)["blockers"])
        self.assertIn("draft", blockers)
        self.assertIn("BQ1", blockers)
        self.assertIn("Close 2026-01 first", " ".join(check_month(2026, 2)["blockers"]))
        self.assertIsNone(close_month(2026, 1, "acc")[0])
        self.assertFalse(Period.objects.exists())

    def test_suspense_balance_is_a_warning_to_confirm(self):
        self.entry(date(2026, 1, 4), [("51411", "70", "0"), ("34971", "0", "70")], journal="BQ1")
        self.reconcile("51411", date(2026, 1, 31))
        period, check = close_month(2026, 1, "acc")
        self.assertIsNone(period)
        self.assertIn("34971", check["warnings"][0])
        self.assertIsNotNone(close_month(2026, 1, "acc", confirm_warnings=True)[0])

    def closed_entry(self):
        e = self.entry(date(2026, 1, 10), [("61254", "10", "0"), ("4411", "0", "10")])
        close_month(2026, 1, "acc", confirm_warnings=True)  # warning: no document attached
        e.refresh_from_db()
        return e

    def test_a_validated_entry_cannot_change(self):
        e = self.closed_entry()
        e.description = "changed"
        with self.assertRaises(ValidatedEntryError):
            e.save()
        # Django deletes inside atomic(savepoint=False); give it a savepoint here.
        with self.assertRaises(ValidatedEntryError), transaction.atomic():
            e.delete()
        line = e.lines.first()
        line.debit = Decimal("11")
        with self.assertRaises(ValidatedEntryError):
            line.save()
        with self.assertRaises(ValidatedEntryError):
            JournalEntryLine.objects.create(journal_entry=e, account=self.acc["4411"], debit=1, credit=0)
        with self.assertRaises(ValidatedEntryError), transaction.atomic():
            e.lines.all().delete()

    def test_the_database_refuses_it_too(self):
        e = self.closed_entry()
        with self.assertRaises(DatabaseError), transaction.atomic(), connection.cursor() as cur:
            cur.execute("UPDATE journal_entries SET description = 'x' WHERE id = %s", [e.id])
        with self.assertRaises(DatabaseError), transaction.atomic(), connection.cursor() as cur:
            cur.execute("DELETE FROM journal_entry_lines WHERE journal_entry_id = %s", [e.id])

    def test_api_refuses_changes_in_a_closed_month(self):
        e = self.closed_entry()
        r = self.api.put(f"/api/v1/journal-entries/{e.id}", {"description": "x"}, format="json")
        self.assertEqual(r.status_code, 400)
        r = self.api.post("/api/v1/journal-entries", {"date": "2026-01-15", "lines": [
            {"account_id": str(self.acc["61254"].id), "debit": "5"},
            {"account_id": str(self.acc["4411"].id), "credit": "5"}]}, format="json")
        self.assertEqual(r.status_code, 400)
        self.assertIn("closed", r.json()["message"])

    def test_reversal_cancels_the_entry_once(self):
        e = self.closed_entry()
        self.assertIn("before", reverse_entry(e, date(2025, 12, 31), "acc")[1])
        self.assertIn("closed", reverse_entry(e, date(2026, 1, 20), "acc")[1])
        r = self.api.post(f"/api/v1/journal-entries/{e.id}/reverse", {"date": "2026-02-02"}, format="json")
        self.assertEqual(r.status_code, 200, r.content)
        rev = JournalEntry.objects.get(reversal_of=e)
        self.assertEqual((rev.journal.code, rev.source, rev.is_posted), ("OD", "reversal", True))
        bal = JournalEntryLine.objects.filter(account__code="4411").values_list("debit", "credit")
        self.assertEqual(sum(d - c for d, c in bal), 0)
        self.assertIn("already reversed", reverse_entry(e, date(2026, 2, 3), "acc")[1])

    def test_manual_entry_ignores_number_and_source_from_the_client(self):
        r = self.api.post("/api/v1/journal-entries", {
            "date": "2026-03-01", "entry_number": "X-1", "source": "bank", "journal_code": "CA",
            "piece_number": "TICKET 12", "lines": [
                {"account_id": str(self.acc["61254"].id), "debit": "5"},
                {"account_id": str(self.acc["51611"].id), "credit": "5"}]}, format="json")
        self.assertEqual(r.status_code, 201, r.content)
        je = r.json()["data"]["journal_entry"]
        self.assertTrue(je["entry_number"].startswith("BR-"))
        self.assertEqual((je["journal_code"], je["piece_number"], je["status"]), ("CA", "TICKET 12", "draft"))
        self.assertEqual(JournalEntry.objects.get(id=je["id"]).source, "manual")

    def test_close_endpoint_and_period_list(self):
        self.entry(date(2026, 1, 10), [("61254", "10", "0"), ("4411", "0", "10")])
        r = self.api.post("/api/v1/periods/close", {"year": 2026, "month": 1}, format="json")
        self.assertEqual(r.status_code, 400)
        self.assertIn("no document attached", r.json()["data"]["warnings"][0])
        r = self.api.post("/api/v1/periods/close", {"year": 2026, "month": 1, "confirm_warnings": True},
                          format="json")
        self.assertEqual(r.status_code, 200, r.content)
        months = self.api.get("/api/v1/periods?year=2026").json()["data"]["months"]
        self.assertTrue(months[0]["closed"])
        self.assertEqual(months[0]["validated"], 1)
        self.assertEqual(self.api.post("/api/v1/periods/close", {"year": 2026, "month": 1},
                                       format="json").status_code, 400)

    def test_reset_clears_validated_entries(self):
        self.closed_entry()
        call_command("reset_bookkeeping", "--confirm", stdout=StringIO())
        self.assertFalse(JournalEntry.objects.exists())
        self.assertFalse(Period.objects.exists())
        self.assertTrue(Journal.objects.filter(code="BQ1").exists())
