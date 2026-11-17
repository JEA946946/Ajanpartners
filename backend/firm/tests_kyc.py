"""Kundekendskab (hvidvask): rettigheder, låsning ved godkendelse, forslag og opfølgning."""

import json
import tempfile
from datetime import date, timedelta
from io import StringIO

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.management import call_command
from django.test import Client, TransactionTestCase, override_settings

from firm.models import AmlReport, FirmTask, KycAssessment
from tenancy.models import Firm, FirmAuditLog, FirmStaff, StaffAssignment
from tenancy.services import create_client, ensure_public_tenant

User = get_user_model()
PW = "Test-1234567"


@override_settings(FIRM_MFA_REQUIRED=False, MEDIA_ROOT=tempfile.mkdtemp())
class KycTests(TransactionTestCase):
    def setUp(self):
        ensure_public_tenant("testserver")
        firm = Firm.current()
        self.partner = User.objects.create_user("partner@x.dk", "partner@x.dk", PW)
        FirmStaff.objects.create(user=self.partner, firm=firm, role="partner")
        self.bogholder = User.objects.create_user("bog@x.dk", "bog@x.dk", PW)
        self.bog_staff = FirmStaff.objects.create(user=self.bogholder, firm=firm, role="bogholder")
        self.co, (self.owner, _pw) = create_client(name="Café Alfa ApS", package_code="mini", owner_email="a@a.dk",
                                            created_by=self.partner, cvr="87654321", industry_code="561010")
        self.other, _ = create_client(name="Beta ApS", package_code="mini", owner_email="b@b.dk",
                                      created_by=self.partner, cvr="12345678", industry_code="620100")
        StaffAssignment.objects.create(staff=self.bog_staff, client=self.co)
        self.http = Client()

    def tearDown(self):
        from django.db import connection
        connection.set_schema_to_public()
        with connection.cursor() as cur:
            for c in (self.co, self.other):
                cur.execute(f'DROP SCHEMA IF EXISTS "{c.schema_name}" CASCADE')

    def call(self, method, path, user, data=None, **extra):
        from rest_framework_simplejwt.tokens import RefreshToken
        auth = {"HTTP_AUTHORIZATION": f"Bearer {RefreshToken.for_user(user).access_token}"}
        if data is not None and not extra.get("multipart"):
            return getattr(self.http, method)(path, data=json.dumps(data), content_type="application/json", **auth)
        if extra.get("multipart"):
            return getattr(self.http, method)(path, data=data, **auth)
        return getattr(self.http, method)(path, **auth)

    def _answer_all(self):
        r = self.call("get", f"/api/firm/clients/{self.co.slug}/kyc", self.bogholder)
        return {q["id"]: {"answer": "nej", "note": ""} for q in r.json()["data"]["checklist"]["questions"]}

    def _draft(self, user=None):
        r = self.call("post", f"/api/firm/clients/{self.co.slug}/kyc", user or self.bogholder, {})
        self.assertEqual(r.status_code, 201, r.content)
        return r.json()["data"]["assessment"]

    def _complete(self, a, **extra):
        data = {"answers": self._answer_all(), "purpose": "Bogføring og årsregnskab for café.",
                "reasons": "Kontantintensiv branche; ejer kendt og verificeret.", **extra}
        r = self.call("put", f"/api/firm/kyc/assessments/{a['id']}", self.bogholder, data)
        self.assertEqual(r.status_code, 200, r.content)

    def _owner(self, **extra):
        data = {"role": "reel_ejer", "name": "Anna Andersen", "birth_date": "1980-01-02",
                "ownership": "100 % af kapital og stemmer", "id_method": "Pas kontrolleret", **extra}
        r = self.call("post", f"/api/firm/clients/{self.co.slug}/kyc/persons", self.bogholder, data)
        self.assertEqual(r.status_code, 201, r.content)
        return r.json()["data"]["person"]

    def test_suggestion_uses_industry_and_status_missing(self):
        r = self.call("get", f"/api/firm/clients/{self.co.slug}/kyc", self.bogholder)
        d = r.json()["data"]
        self.assertEqual(d["status"], "missing")
        self.assertEqual(d["suggestion"]["risk_level"], "hoej")  # restauration = høj i husets vurdering
        self.assertTrue(d["suggestion"]["official_risk_industry"])  # 561010 (DB07) → restauration (DB25)
        self.assertFalse(d["can_approve"])

    def test_bogholder_cannot_see_unassigned_client(self):
        r = self.call("get", f"/api/firm/clients/{self.other.slug}/kyc", self.bogholder)
        self.assertEqual(r.status_code, 404)

    def test_full_flow_and_lock(self):
        self._owner()
        a = self._draft()
        self.assertEqual(a["version"], 1)
        # Kun én kladde ad gangen
        self.assertEqual(self.call("post", f"/api/firm/clients/{self.co.slug}/kyc", self.bogholder, {}).status_code, 400)
        # Ufuldstændig → kan ikke godkendes, og bogholder kan aldrig godkende
        self.assertEqual(self.call("post", f"/api/firm/kyc/assessments/{a['id']}/approve", self.bogholder).status_code, 403)
        r = self.call("post", f"/api/firm/kyc/assessments/{a['id']}/approve", self.partner)
        self.assertEqual(r.status_code, 400)
        self._complete(a, risk_level="hoej")
        r = self.call("post", f"/api/firm/kyc/assessments/{a['id']}/approve", self.partner)
        self.assertEqual(r.status_code, 200, r.content)
        ok = r.json()["data"]["assessment"]
        self.assertEqual(ok["status"], "godkendt")
        self.assertEqual(len(ok["sha256"]), 64)
        # Høj risiko → 12 måneder (husets standardpolitik)
        self.assertGreater(date.fromisoformat(ok["next_review_on"]), date.today() + timedelta(days=330))
        # Låst
        r = self.call("put", f"/api/firm/kyc/assessments/{a['id']}", self.bogholder, {"purpose": "x"})
        self.assertEqual(r.status_code, 409)
        # Ny version forudfyldes fra den forrige
        b = self._draft()
        self.assertEqual(b["version"], 2)
        self.assertEqual(b["purpose"], "Bogføring og årsregnskab for café.")
        self.assertTrue(FirmAuditLog.objects.filter(action="kyc_assessment_approved", client=self.co).exists())
        d = self.call("get", f"/api/firm/clients/{self.co.slug}/kyc", self.bogholder).json()["data"]
        self.assertEqual(d["status"], "ok")

    def test_pep_requires_source_of_funds(self):
        self._owner(is_pep=True, pep_note="Folketingsmedlem")
        a = self._draft()
        self._complete(a)
        r = self.call("post", f"/api/firm/kyc/assessments/{a['id']}/approve", self.partner)
        self.assertEqual(r.status_code, 400)
        self.assertIn("oprindelse", r.json()["message"])
        sug = self.call("get", f"/api/firm/clients/{self.co.slug}/kyc", self.bogholder).json()["data"]["suggestion"]
        self.assertTrue(any("PEP" in x for x in sug["reasons"]))

    def test_requires_beneficial_owner(self):
        a = self._draft()
        self._complete(a)
        r = self.call("post", f"/api/firm/kyc/assessments/{a['id']}/approve", self.partner)
        self.assertEqual(r.status_code, 400)
        self.assertIn("reel ejer", r.json()["message"])

    def test_person_is_never_deleted_and_document_upload(self):
        f = SimpleUploadedFile("pas.pdf", b"%PDF-1.4 test", content_type="application/pdf")
        r = self.call("post", f"/api/firm/clients/{self.co.slug}/kyc/persons", self.bogholder,
                      {"role": "ledelse", "name": "Bo Direktør", "id_document": f}, multipart=True)
        self.assertEqual(r.status_code, 201, r.content)
        p = r.json()["data"]["person"]
        self.assertTrue(p["has_document"])
        r = self.call("get", f"/api/firm/kyc/persons/{p['id']}/document", self.bogholder)
        self.assertEqual(r.status_code, 200)
        r = self.call("delete", f"/api/firm/kyc/persons/{p['id']}", self.bogholder)
        self.assertFalse(r.json()["data"]["person"]["active"])
        d = self.call("get", f"/api/firm/clients/{self.co.slug}/kyc", self.bogholder).json()["data"]
        self.assertEqual(len(d["persons"]), 1)

    def test_client_users_cannot_reach_kyc(self):
        r = self.call("get", f"/api/firm/clients/{self.co.slug}/kyc", self.owner)
        self.assertEqual(r.status_code, 403)
        r = self.call("get", "/api/firm/aml-reports", self.owner)
        self.assertEqual(r.status_code, 403)

    def test_aml_reports_partner_only(self):
        r = self.call("post", "/api/firm/aml-reports", self.bogholder, {"client": self.co.slug, "summary": "x"})
        self.assertEqual(r.status_code, 403)
        r = self.call("post", "/api/firm/aml-reports", self.partner,
                      {"client": self.co.slug, "summary": "Usædvanlige kontantindskud"})
        self.assertEqual(r.status_code, 201)
        self.assertEqual(AmlReport.objects.count(), 1)
        log = FirmAuditLog.objects.get(action="aml_report_created")
        self.assertIsNone(log.client)  # ingen kobling til kunden i den fælles log
        self.assertNotIn("summary", log.detail)

    def test_review_report_creates_tasks_once(self):
        out = StringIO()
        call_command("kyc_review_report", stdout=out)
        self.assertEqual(FirmTask.objects.filter(client=self.co, visible_to_client=False).count(), 1)
        call_command("kyc_review_report", stdout=out)
        self.assertEqual(FirmTask.objects.filter(client=self.co).count(), 1)
        # Forfalden godkendt vurdering → "skal opdateres"
        KycAssessment.objects.create(client=self.other, version=1, status="godkendt",
                                     next_review_on=date.today() - timedelta(days=1))
        call_command("kyc_review_report", stdout=out)
        self.assertTrue(FirmTask.objects.filter(client=self.other, title__contains="opdateres").exists())

    def test_policy_editable_by_partner(self):
        r = self.call("put", "/api/firm/settings", self.partner, {"kyc_review_months": {"lav": 36, "normal": 18, "hoej": 6}})
        self.assertEqual(r.status_code, 200, r.content)
        self.assertEqual(r.json()["data"]["firm"]["kyc_review_months"]["hoej"], 6)
        r = self.call("put", "/api/firm/settings", self.partner, {"kyc_review_months": {"lav": 0}})
        self.assertEqual(r.status_code, 400)
