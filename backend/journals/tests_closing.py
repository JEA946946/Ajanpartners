"""Månedslukning, lås, tilbageføring og årsafslutning.

Kør: manage.py test journals.tests_closing
"""

from datetime import date
from io import StringIO

from django.core.management import call_command
from django.db import DatabaseError, connection, transaction

from accounts import chart
from accounts.models import FiscalYear
from core.models import BankReconciliation
from core.testing import D, LedgerTestCase
from journals.closing import check_month, check_year, close_month, close_year, reverse_entry
from journals.models import Journal, JournalEntry, JournalEntryLine, Period, ValidatedEntryError

COST = "2810"


class ClosingTests(LedgerTestCase):
    def reconcile(self, code, d):
        BankReconciliation.objects.create(bank_account=self.acc(code), date=d, statement_balance=0,
                                          status="completed")

    def test_journals_are_danish_and_bank_has_its_account(self):
        j = {x.code: x for x in Journal.objects.all()}
        self.assertTrue({"BANK", "KAS", "KØB", "SALG", "LØN", "DIV", "PRIMO", "ÅA"} <= set(j))
        self.assertEqual(j["BANK"].account.code, chart.BANK)
        self.assertEqual(j["KAS"].account.code, chart.CASH)
        self.assertEqual(self.entry([(COST, "10", "0"), (chart.PAYABLE, "0", "10")]).journal.code, "DIV")

    def test_new_bank_account_gets_its_own_journal(self):
        from accounts.models import Account
        from journals.journal_for import journal_for_account, seed_journals
        bank = self.acc(chart.BANK)
        acc2 = Account.objects.create(code="6481", name="Bank 2", account_type=bank.account_type,
                                      parent=bank.parent, standard_code=chart.BANK, arl_line=bank.arl_line)
        seed_journals()
        j = journal_for_account(acc2)
        self.assertEqual((j.code, j.type), ("BANK2", "bank"))

    def test_closing_numbers_each_journal_in_date_order(self):
        late = self.entry([(chart.BANK, "50", "0"), (chart.SUSPENSE, "0", "50")], d=date(2026, 1, 20), journal="BANK")
        early = self.entry([(chart.BANK, "70", "0"), (chart.SUSPENSE, "0", "70")], d=date(2026, 1, 3), journal="BANK")
        div = self.entry([(COST, "10", "0"), (chart.PAYABLE, "0", "10")], d=date(2026, 1, 10))
        self.reconcile(chart.BANK, date(2026, 1, 31))
        period, check = close_month(2026, 1, "test", confirm_warnings=True)
        self.assertIsNotNone(period, check)
        for e in (late, early, div):
            e.refresh_from_db()
        self.assertEqual((early.entry_number, late.entry_number), ("BANK-2026-00001", "BANK-2026-00002"))
        self.assertEqual(div.entry_number, "DIV-2026-00001")
        self.assertEqual(early.status, "validated")

    def test_month_does_not_close_with_drafts_unreconciled_bank_or_out_of_order(self):
        self.entry([(COST, "10", "0"), (chart.PAYABLE, "0", "10")], d=date(2026, 1, 3), posted=False)
        self.entry([(chart.BANK, "70", "0"), (chart.SUSPENSE, "0", "70")], d=date(2026, 1, 4), journal="BANK")
        self.entry([(COST, "10", "0"), (chart.PAYABLE, "0", "10")], d=date(2026, 2, 4))
        blockers = " | ".join(check_month(2026, 1)["blockers"])
        self.assertIn("kladde", blockers)
        self.assertIn("BANK", blockers)
        self.assertIn("Luk 2026-01 først", " ".join(check_month(2026, 2)["blockers"]))
        self.assertIsNone(close_month(2026, 1, "test")[0])
        self.assertFalse(Period.objects.exists())

    def test_suspense_balance_is_a_warning_to_confirm(self):
        self.entry([(chart.BANK, "70", "0"), (chart.SUSPENSE, "0", "70")], d=date(2026, 1, 4), journal="BANK")
        self.reconcile(chart.BANK, date(2026, 1, 31))
        period, check = close_month(2026, 1, "test")
        self.assertIsNone(period)
        self.assertIn(chart.SUSPENSE, check["warnings"][0])
        self.assertIsNotNone(close_month(2026, 1, "test", confirm_warnings=True)[0])

    def closed_entry(self):
        e = self.entry([(COST, "10", "0"), (chart.PAYABLE, "0", "10")], d=date(2026, 1, 10))
        close_month(2026, 1, "test", confirm_warnings=True)  # advarsel: intet bilag
        e.refresh_from_db()
        return e

    def test_a_validated_entry_cannot_change(self):
        e = self.closed_entry()
        e.description = "ændret"
        with self.assertRaises(ValidatedEntryError):
            e.save()
        with self.assertRaises(ValidatedEntryError), transaction.atomic():
            e.delete()
        line = e.lines.first()
        line.debit = D("11")
        with self.assertRaises(ValidatedEntryError):
            line.save()
        with self.assertRaises(ValidatedEntryError):
            JournalEntryLine.objects.create(journal_entry=e, account=self.acc(COST), debit=1, credit=0)

    def test_the_database_refuses_it_too_also_for_the_new_columns(self):
        e = self.closed_entry()
        line = e.lines.first()
        for sql in ("UPDATE journal_entries SET description = 'x' WHERE id = %s",
                    "DELETE FROM journal_entry_lines WHERE journal_entry_id = %s"):
            with self.assertRaises(DatabaseError), transaction.atomic(), connection.cursor() as cur:
                cur.execute(sql, [e.id])
        for sql in ("UPDATE journal_entry_lines SET amount_currency = 5 WHERE id = %s",
                    "UPDATE journal_entry_lines SET vat_code = 'S01' WHERE id = %s"):
            with self.assertRaises(DatabaseError), transaction.atomic(), connection.cursor() as cur:
                cur.execute(sql, [line.id])
        # Udligningsfelterne må stadig ændres.
        with connection.cursor() as cur:
            cur.execute("UPDATE journal_entry_lines SET lettrage = 'AA' WHERE id = %s", [line.id])

    def test_api_refuses_changes_in_a_closed_month(self):
        e = self.closed_entry()
        r = self.put(f"/api/v1/journal-entries/{e.id}", {"description": "x"})
        self.assertEqual(r.status_code, 400)
        r = self.post("/api/v1/journal-entries", {"date": "2026-01-15", "lines": [
            {"account_id": str(self.acc(COST).id), "debit": "5"},
            {"account_id": str(self.acc(chart.BANK).id), "credit": "5"}]})
        self.assertEqual(r.status_code, 400)
        self.assertIn("lukket", r.json()["message"])

    def test_reversal_cancels_the_entry_once(self):
        e = self.closed_entry()
        self.assertIn("før", reverse_entry(e, date(2025, 12, 31), "test")[1])
        self.assertIn("lukket", reverse_entry(e, date(2026, 1, 20), "test")[1])
        r = self.post(f"/api/v1/journal-entries/{e.id}/reverse", {"date": "2026-02-02"})
        self.assertEqual(r.status_code, 200, r.content)
        rev = JournalEntry.objects.get(reversal_of=e)
        self.assertEqual((rev.journal.code, rev.source, rev.is_posted), ("DIV", "reversal", True))
        bal = JournalEntryLine.objects.filter(account__code=chart.PAYABLE).values_list("debit", "credit")
        self.assertEqual(sum(d - c for d, c in bal), 0)
        self.assertIn("allerede tilbageført", reverse_entry(e, date(2026, 2, 3), "test")[1])

    def test_manual_entry_ignores_number_and_source_from_the_client(self):
        r = self.post("/api/v1/journal-entries", {
            "date": "2026-03-01", "entry_number": "X-1", "source": "bank", "journal_code": "KAS",
            "piece_number": "KVITTERING 12", "lines": [
                {"account_id": str(self.acc(COST).id), "debit": "5", "vat_code": "K010"},
                {"account_id": str(self.acc(chart.CASH).id), "credit": "5"}]})
        self.assertEqual(r.status_code, 201, r.content)
        je = r.json()["data"]["journal_entry"]
        self.assertTrue(je["entry_number"].startswith("KL-"))
        self.assertEqual((je["journal_code"], je["piece_number"], je["status"]), ("KAS", "KVITTERING 12", "draft"))
        self.assertEqual(JournalEntry.objects.get(id=je["id"]).source, "manual")
        self.assertEqual(je["lines"][0]["vat_code"], "K010")

    def test_foreign_currency_line_keeps_dkk_and_currency_amount(self):
        r = self.post("/api/v1/journal-entries", {"date": "2026-03-01", "lines": [
            {"account_id": str(self.acc(COST).id), "debit": "746.00", "currency": "EUR",
             "exchange_rate": "7.46", "amount_currency": "100"},
            {"account_id": str(self.acc(chart.BANK).id), "credit": "746.00"}]})
        self.assertEqual(r.status_code, 201, r.content)
        line = JournalEntryLine.objects.get(account__code=COST)
        self.assertEqual((line.debit, line.currency, line.amount_currency, line.base_debit),
                         (D("746.00"), "EUR", D("100.00"), D("746.00")))
        dkk = JournalEntryLine.objects.get(account__code=chart.BANK)
        self.assertEqual((dkk.currency, dkk.exchange_rate, dkk.amount_currency), ("DKK", 1, None))

    def test_close_endpoint_and_period_list(self):
        self.entry([(COST, "10", "0"), (chart.PAYABLE, "0", "10")], d=date(2026, 1, 10))
        r = self.post("/api/v1/periods/close", {"year": 2026, "month": 1})
        self.assertEqual(r.status_code, 400)
        self.assertIn("bilag", r.json()["data"]["warnings"][0])
        r = self.post("/api/v1/periods/close", {"year": 2026, "month": 1, "confirm_warnings": True})
        self.assertEqual(r.status_code, 200, r.content)
        months = self.get("/api/v1/periods", {"year": 2026}).json()["data"]["months"]
        self.assertTrue(months[0]["closed"])
        self.assertEqual(months[0]["validated"], 1)

    def test_reset_clears_validated_entries_for_one_client(self):
        self.closed_entry()
        connection.set_schema_to_public()
        call_command("reset_bookkeeping", "--client", self.tenant.slug, "--confirm", "--force", stdout=StringIO())
        connection.set_tenant(self.tenant)
        self.assertFalse(JournalEntry.objects.exists())
        self.assertFalse(Period.objects.exists())
        self.assertTrue(Journal.objects.filter(code="BANK").exists())


class YearEndTests(LedgerTestCase):
    def test_year_end_moves_result_to_equity_books_opening_and_locks(self):
        fy = FiscalYear.objects.create(name="2026", start_date=date(2026, 1, 1), end_date=date(2026, 12, 31))
        cust = __import__("sales.models", fromlist=["Customer"]).Customer.objects.create(code="K1", name="Kunde")
        tiers = {"partner_type": "customer", "partner_id": str(cust.id), "partner_name": cust.name}
        self.entry([(chart.RECEIVABLE, "1250", "0", tiers), (chart.REVENUE, "0", "1000"),
                    (chart.VAT_OUTPUT, "0", "250")], d=date(2026, 3, 1))
        self.entry([(COST, "300", "0"), (chart.CASH, "0", "300")], d=date(2026, 6, 1))
        self.assertIn("ikke lukket", " ".join(check_year(fy)["blockers"]))
        for m in (3, 6):
            close_month(2026, m, "test", confirm_warnings=True)
        result, check = close_year(fy, "test", confirm_warnings=True)
        self.assertIsNotNone(result, check)
        self.assertEqual(D(result["result"]), D("700"))
        self.assertEqual(result["result_account"], chart.RETAINED_EARNINGS)
        closing = JournalEntry.objects.get(source="closing")
        self.assertEqual((closing.journal.code, closing.date, closing.status), ("ÅA", date(2026, 12, 31), "validated"))
        eq = closing.lines.get(account__code=chart.RETAINED_EARNINGS)
        self.assertEqual((eq.debit, eq.credit), (0, D("700")))
        opening = JournalEntry.objects.get(source="opening")
        self.assertEqual((opening.journal.code, opening.date), ("PRIMO", date(2027, 1, 1)))
        lines = {l.account.code: (l.debit, l.credit, l.partner_id) for l in opening.lines.select_related("account")}
        self.assertEqual(lines[chart.RECEIVABLE], (D("1250"), 0, str(cust.id)))
        self.assertEqual(lines[chart.RETAINED_EARNINGS], (0, D("700"), ""))
        self.assertNotIn(chart.REVENUE, lines)
        fy.refresh_from_db()
        self.assertTrue(fy.is_closed)
        self.assertTrue(FiscalYear.objects.filter(name="2027", is_closed=False).exists())
        r = self.post("/api/v1/journal-entries", {"date": "2026-08-01", "lines": [
            {"account_id": str(self.acc(COST).id), "debit": "5"},
            {"account_id": str(self.acc(chart.CASH).id), "credit": "5"}]})
        self.assertIn("afsluttede regnskabsår", r.json()["message"])
        # Rapporterne: resultatet for 2026 er stadig 700, og balancen 2027 bygger på primo.
        pnl = self.get("/api/v1/reports/profit-and-loss", {"date_from": "2026-01-01", "date_to": "2026-12-31"})
        self.assertEqual(D(pnl.json()["data"]["net_result"]), D("700"))
        bs = self.get("/api/v1/reports/balance-sheet", {"date": "2027-01-31"}).json()["data"]
        self.assertTrue(bs["is_balanced"], bs)
        self.assertEqual(D(bs["total_assets"]), D("950"))

    def test_year_end_endpoint_refuses_open_months(self):
        fy = FiscalYear.objects.create(name="2026", start_date=date(2026, 1, 1), end_date=date(2026, 12, 31))
        self.entry([(COST, "300", "0"), (chart.CASH, "0", "300")], d=date(2026, 6, 1))
        r = self.post("/api/v1/year-end/close", {"fiscal_year_id": str(fy.id)})
        self.assertEqual(r.status_code, 400)
        self.assertEqual(self.get("/api/v1/year-end/status").status_code, 200)
