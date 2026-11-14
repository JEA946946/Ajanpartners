"""Incoming money matched to CRM invoices — run with: python manage.py test journals.tests_receipts"""

from datetime import date
from decimal import Decimal
from unittest import mock

from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient

from accounts.management.commands.seed_accounts import seed_chart
from accounts.models import Account
from journals.cmr_sync import run_sync
from journals.models import InvoiceReceipt, JournalEntry, JournalEntryLine

EUR_INV = {"id": "aaaaaaaa-0000-0000-0000-000000000001", "invoice_number": "INV-31", "currency": "EUR",
           "total": "1000.00", "status": "issued", "customer_name": "Nordic Travel", "trip_reference": "VFNT1010",
           "opportunity_title": "Nordic Travel", "invoice_date": "2026-09-01", "line_items": [],
           "updated_at": "2026-09-01T10:00:00+00:00"}
MAD_INV = {**EUR_INV, "id": "aaaaaaaa-0000-0000-0000-000000000002", "invoice_number": "INV-32",
           "currency": "MAD", "total": "5000.00", "customer_name": "Atlas Agency", "trip_reference": "VFAA2020"}


class ReceiptTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        seed_chart()

    def setUp(self):
        self.api = APIClient()
        self.api.force_authenticate(get_user_model().objects.create_user("a", password="x", is_staff=True))
        self.crm = mock.patch("journals.cmr_client.CMRClient")
        client = self.crm.start().return_value
        client.get_invoices.return_value = [EUR_INV, MAD_INV]
        client.get_invoice.side_effect = lambda i: next((x for x in (EUR_INV, MAD_INV) if x["id"] == i), None)
        self.addCleanup(self.crm.stop)

    def bank_line(self, amount, text="RECEPTION RAPATRIEMENT EN FAVEUR DE NORDIC TRAVEL VFNT1010", bank="51411"):
        n = JournalEntry.objects.count() + 1
        je = JournalEntry.objects.create(entry_number=f"JE-{n:04d}", date=date(2026, 9, 20), source="bank",
                                         is_posted=True, description=text)
        line = JournalEntryLine.objects.create(journal_entry=je, account=Account.objects.get(code=bank),
                                               debit=Decimal(amount), credit=0)
        JournalEntryLine.objects.create(journal_entry=je, account=Account.objects.get(code="34971"),
                                        debit=0, credit=Decimal(amount))
        return line

    def legs(self, line):
        return {(x.account.code, x.debit, x.credit) for x in line.journal_entry.lines.all()}

    def test_eur_invoice_is_worth_the_mad_received(self):
        line = self.bank_line("10870.00")
        sug = self.api.get(f"/api/v1/transactions/{line.id}/invoice-suggestions").json()["data"]["suggestions"]
        self.assertEqual(sug[0]["invoice_number"], "INV-31")  # name + trip reference in the text
        r = self.api.post(f"/api/v1/transactions/{line.id}/match-invoice",
                          {"cmr_invoice_id": EUR_INV["id"]}, format="json")
        self.assertEqual(r.status_code, 201, r.content)
        self.assertEqual(r.json()["data"]["rate"], "10.8700")
        self.assertEqual(self.legs(line), {("51411", Decimal("10870.00"), Decimal("0")),
                                           ("71243", Decimal("0"), Decimal("10870.00"))})

    def test_deposit_and_balance_each_at_their_own_mad(self):
        a, b = self.bank_line("3240.00"), self.bank_line("7700.00")
        self.api.post(f"/api/v1/transactions/{a.id}/match-invoice",
                      {"cmr_invoice_id": EUR_INV["id"], "covered_amount": "300"}, format="json")
        r = self.api.post(f"/api/v1/transactions/{b.id}/match-invoice",
                          {"cmr_invoice_id": EUR_INV["id"]}, format="json")
        self.assertEqual(r.json()["data"]["covered_amount"], "700.00")
        self.assertEqual(sum(x.amount_mad for x in InvoiceReceipt.objects.all()), Decimal("10940.00"))
        # Fully paid: no more suggestions for it, and no more matching.
        c = self.bank_line("100.00")
        r = self.api.post(f"/api/v1/transactions/{c.id}/match-invoice",
                          {"cmr_invoice_id": EUR_INV["id"], "covered_amount": "10"}, format="json")
        self.assertEqual(r.status_code, 400)

    def test_mad_invoice_clears_the_receivable_and_needs_the_sync_first(self):
        line = self.bank_line("5000.00", text="VIREMENT RECU ATLAS AGENCY")
        r = self.api.post(f"/api/v1/transactions/{line.id}/match-invoice",
                          {"cmr_invoice_id": MAD_INV["id"]}, format="json")
        self.assertEqual(r.status_code, 400)  # not booked yet
        run_sync([MAD_INV], [], "t")
        r = self.api.post(f"/api/v1/transactions/{line.id}/match-invoice",
                          {"cmr_invoice_id": MAD_INV["id"]}, format="json")
        self.assertEqual(r.status_code, 201, r.content)
        self.assertIn(("3421", Decimal("0"), Decimal("5000.00")), self.legs(line))

    def split_payment(self):
        # 30 % arrives exchanged on CIH300, 70 % stays in euros on CIH600 Euro.
        mad = self.bank_line("3261.00")
        eur = self.bank_line("700.00", bank="51413")
        r = self.api.post(f"/api/v1/transactions/{mad.id}/match-invoice",
                          {"cmr_invoice_id": EUR_INV["id"], "covered_amount": "300"}, format="json")
        self.assertEqual(r.json()["data"]["rate"], "10.8700")
        sug = self.api.get(f"/api/v1/transactions/{eur.id}/invoice-suggestions").json()["data"]
        self.assertTrue(sug["eur_account"])
        self.assertEqual(sug["suggestions"][0]["invoice_number"], "INV-31")
        self.assertIn("euros = the open amount", sug["suggestions"][0]["why"])
        r = self.api.post(f"/api/v1/transactions/{eur.id}/match-invoice",
                          {"cmr_invoice_id": EUR_INV["id"]}, format="json")
        self.assertEqual(r.status_code, 201, r.content)
        self.assertTrue(r.json()["data"]["awaiting_exchange"])
        # The euros are held, not valued: nothing on client funds from them.
        self.assertEqual(self.legs(eur), {("51413", Decimal("700.00"), Decimal("0")),
                                          ("34972", Decimal("0"), Decimal("700.00"))})
        # The invoice is fully covered now — nothing more can be matched to it.
        extra = self.bank_line("100.00")
        self.assertEqual(self.api.post(f"/api/v1/transactions/{extra.id}/match-invoice",
                                       {"cmr_invoice_id": EUR_INV["id"], "covered_amount": "1"},
                                       format="json").status_code, 400)
        return eur

    def test_30_percent_exchanged_and_70_percent_kept_in_euros(self):
        self.split_payment()

    def test_waiting_euros_are_booked_when_exchanged(self):
        eur = self.split_payment()
        conv = self.bank_line("7630.00", text="CESSION DEVISES")
        waiting = self.api.get(f"/api/v1/transactions/{conv.id}/invoice-suggestions").json()["data"]["waiting_exchange"]
        self.assertEqual((waiting[0]["invoice_number"], waiting[0]["waiting"]), ("INV-31", "700.00"))
        r = self.api.post(f"/api/v1/transactions/{conv.id}/match-invoice",
                          {"exchanged_from": waiting[0]["id"], "euros": "700"}, format="json")
        self.assertEqual(r.status_code, 201, r.content)
        self.assertEqual(r.json()["data"]["rate"], "10.9000")
        self.assertIn(("71243", Decimal("0"), Decimal("7630.00")), self.legs(conv))
        # The EUR line cannot be unmatched while its euros are exchanged.
        self.assertEqual(self.api.delete(f"/api/v1/transactions/{eur.id}/reconciliation").status_code, 400)
        self.assertEqual(self.api.delete(f"/api/v1/transactions/{conv.id}/reconciliation").status_code, 200)
        self.assertEqual(self.api.delete(f"/api/v1/transactions/{eur.id}/reconciliation").status_code, 200)

    def test_eur_account_cannot_pay_a_mad_invoice(self):
        run_sync([MAD_INV], [], "t")
        eur = self.bank_line("1000.00", bank="51413")
        self.assertEqual(self.api.post(f"/api/v1/transactions/{eur.id}/match-invoice",
                                       {"cmr_invoice_id": MAD_INV["id"]}, format="json").status_code, 400)

    def test_undo_puts_the_money_back_on_suspense(self):
        line = self.bank_line("10870.00")
        self.api.post(f"/api/v1/transactions/{line.id}/match-invoice",
                      {"cmr_invoice_id": EUR_INV["id"]}, format="json")
        self.assertEqual(self.api.get(f"/api/v1/transactions/{line.id}/reconciliation").json()["data"]["type"],
                         "invoice")
        self.assertEqual(self.api.delete(f"/api/v1/transactions/{line.id}/reconciliation").status_code, 200)
        self.assertEqual(self.legs(line), {("51411", Decimal("10870.00"), Decimal("0")),
                                           ("34971", Decimal("0"), Decimal("10870.00"))})
        self.assertFalse(InvoiceReceipt.objects.exists())

    def test_matched_line_cannot_be_categorised_or_deleted(self):
        line = self.bank_line("10870.00")
        self.api.post(f"/api/v1/transactions/{line.id}/match-invoice",
                      {"cmr_invoice_id": EUR_INV["id"]}, format="json")
        je = line.journal_entry
        self.api.post(f"/api/v1/journal-entries/{je.id}/unpost")
        self.assertEqual(self.api.delete(f"/api/v1/journal-entries/{je.id}").status_code, 400)
