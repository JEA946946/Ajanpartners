"""Audit-log (hash-kæde) og bilag — kør: manage.py test core.tests_audit"""

import hashlib
import shutil
import tempfile
from datetime import date
from decimal import Decimal

from django.core.files.uploadedfile import SimpleUploadedFile
from django.db import DatabaseError, connection, transaction
from django.test import override_settings

from accounts import chart
from core.testing import LedgerTestCase
from core.audit import log_action, verify_chain
from core.models import AuditLog, AuditLogChangedError, Document
from journals.closing import close_month
from journals.models import Journal, JournalEntry, JournalEntryLine
from journals.numbering import next_je_number

MEDIA = tempfile.mkdtemp()


class AuditChainTests(LedgerTestCase):
    def test_chain_verifies_and_detects_a_changed_row(self):
        for i in range(3):
            log_action(None, "create", "Thing", i, {"amount": Decimal("1.50"), "day": date(2026, 1, i + 1)})
        self.assertEqual(verify_chain(), {"ok": True, "count": 3, "broken_at": None})
        second = AuditLog.objects.get(seq=2)
        self.assertEqual(second.prev_hash, AuditLog.objects.get(seq=1).hash)
        with self.assertRaises(AuditLogChangedError):
            second.save()
        with self.assertRaises(AuditLogChangedError):
            second.delete()
        with self.assertRaises(DatabaseError), transaction.atomic(), connection.cursor() as cur:
            cur.execute("UPDATE audit_logs SET record_id = 'x' WHERE seq = 2")
        # Nogen med triggeren slået fra retter en række: kæden viser det.
        with transaction.atomic(), connection.cursor() as cur:
            cur.execute("SET LOCAL bookkeeping.allow_reset = 'on'")
            cur.execute("UPDATE audit_logs SET record_id = 'x' WHERE seq = 2")
        self.assertEqual(verify_chain(), {"ok": False, "count": 2, "broken_at": 2})


@override_settings(MEDIA_ROOT=MEDIA)
class DocumentTests(LedgerTestCase):
    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(MEDIA, ignore_errors=True)

    def setUp(self):
        super().setUp()
        self.je = JournalEntry.objects.create(journal=Journal.objects.get(code="DIV"), entry_number=next_je_number(),
                                              date=date(2026, 1, 10), source="manual", is_posted=True)
        JournalEntryLine.objects.create(journal_entry=self.je, account=self.acc("2450"), debit=10, credit=0)
        JournalEntryLine.objects.create(journal_entry=self.je, account=self.acc(chart.CASH), debit=0, credit=10)

    def upload(self):
        content = b"%PDF-1.4 faktura 12"
        try:
            r = self.api.post("/api/v1/documents", {
                "file": SimpleUploadedFile("faktura.pdf", content, content_type="application/pdf"),
                "journal_entry_id": str(self.je.id), "piece_number": "F-12"}, format="multipart")
        finally:
            connection.set_tenant(self.tenant)
        self.assertEqual(r.status_code, 201, r.content)
        doc = Document.objects.get()
        self.assertEqual((doc.sha256, doc.size, doc.piece_number),
                         (hashlib.sha256(content).hexdigest(), len(content), "F-12"))
        return doc, content

    def test_upload_download_and_lock_after_closing(self):
        doc, content = self.upload()
        r = self.get(f"/api/v1/documents/{doc.id}/download")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(b"".join(r.streaming_content), content)
        self.assertEqual(self.get(f"/api/v1/journal-entries/{self.je.id}").json()["data"]["journal_entry"]
                         ["documents"], 1)
        period, check = close_month(2026, 1, "test")
        self.assertIsNotNone(period, check)  # posteringen har sit bilag: ingen advarsel
        r = self.delete(f"/api/v1/documents/{doc.id}")
        self.assertEqual(r.status_code, 400)
        r = self.post(f"/api/v1/documents/{doc.id}/link", {"journal_entry_id": ""})
        self.assertEqual(r.status_code, 400)
        self.assertTrue(Document.objects.filter(id=doc.id).exists())

    def test_document_of_an_open_month_can_be_deleted(self):
        doc, _ = self.upload()
        self.assertEqual(self.delete(f"/api/v1/documents/{doc.id}").status_code, 200)
        self.assertFalse(Document.objects.exists())
