"""Kundeaccept og uafhængighed: spærringer efter BEK 520/2024, partnergodkendelse og låsning."""

import json
from datetime import date, timedelta

from django.contrib.auth import get_user_model
from django.test import Client, TransactionTestCase, override_settings

from firm.models import IndependenceConflict, KycAssessment
from firm.views_quality import checklist
from tenancy.models import Firm, FirmStaff, StaffAssignment
from tenancy.services import create_client, ensure_public_tenant

User = get_user_model()
PW = "Test-1234567"


@override_settings(FIRM_MFA_REQUIRED=False)
class QualityTests(TransactionTestCase):
    def setUp(self):
        ensure_public_tenant("testserver")
        firm = Firm.current()
        self.partner = User.objects.create_user("p1@x.dk", "p1@x.dk", PW)
        self.p1 = FirmStaff.objects.create(user=self.partner, firm=firm, role="partner")
        self.partner2 = User.objects.create_user("p2@x.dk", "p2@x.dk", PW)
        FirmStaff.objects.create(user=self.partner2, firm=firm, role="partner")
        self.bog = User.objects.create_user("bog@x.dk", "bog@x.dk", PW)
        self.bog_staff = FirmStaff.objects.create(user=self.bog, firm=firm, role="bogholder")
        self.co, _ = create_client(name="Alfa ApS", package_code="mini", created_by=self.partner,
                                   cvr="87654321", industry_code="620100")
        StaffAssignment.objects.create(staff=self.bog_staff, client=self.co)
        self.http = Client()

    def tearDown(self):
        from django.db import connection
        connection.set_schema_to_public()
        with connection.cursor() as cur:
            cur.execute(f'DROP SCHEMA IF EXISTS "{self.co.schema_name}" CASCADE')

    def call(self, method, path, user, data=None):
        from rest_framework_simplejwt.tokens import RefreshToken
        kw = {"HTTP_AUTHORIZATION": f"Bearer {RefreshToken.for_user(user).access_token}"}
        if data is not None:
            kw.update(data=json.dumps(data), content_type="application/json")
        return getattr(self.http, method)(path, **kw)

    def _answers(self, name, **override):
        out = {q["id"]: {"answer": "nej", "note": ""} for q in checklist(name)["questions"]}
        if name == "acceptance":
            for k in ("kyc", "skift_revisor", "kompetence", "god_revisorskik", "vederlag"):
                out[k]["answer"] = "ja"
        for k, v in override.items():
            out[k] = v
        return out

    def _kyc_ok(self):
        KycAssessment.objects.create(client=self.co, version=1, status="godkendt",
                                     next_review_on=date.today() + timedelta(days=300))

    def _accept_draft(self, user=None, **answers):
        user = user or self.bog
        r = self.call("post", f"/api/firm/clients/{self.co.slug}/acceptances", user, {"engagement_text": "Opstilling 2026"})
        self.assertEqual(r.status_code, 201, r.content)
        a = r.json()["data"]["acceptance"]
        r = self.call("put", f"/api/firm/acceptances/{a['id']}", user,
                      {"answers": self._answers("acceptance", **answers), "conclusion": "Kunden accepteres."})
        self.assertEqual(r.status_code, 200, r.content)
        return a

    def test_acceptance_requires_kyc_and_partner_and_locks(self):
        a = self._accept_draft()
        self.assertEqual(self.call("post", f"/api/firm/acceptances/{a['id']}/approve", self.bog, {"decision": "godkendt"}).status_code, 403)
        r = self.call("post", f"/api/firm/acceptances/{a['id']}/approve", self.partner, {"decision": "godkendt"})
        self.assertEqual(r.status_code, 400)
        self.assertIn("Hvidvask", r.json()["message"])
        self._kyc_ok()
        r = self.call("post", f"/api/firm/acceptances/{a['id']}/approve", self.partner, {"decision": "godkendt"})
        self.assertEqual(r.status_code, 200, r.content)
        self.assertEqual(len(r.json()["data"]["acceptance"]["sha256"]), 64)
        self.assertEqual(self.call("put", f"/api/firm/acceptances/{a['id']}", self.bog, {"conclusion": "x"}).status_code, 409)
        d = self.call("get", f"/api/firm/clients/{self.co.slug}/acceptances", self.bog).json()["data"]
        self.assertEqual(d["status"], "approved")

    def test_threat_under_section_2_blocks_approval_but_rejection_allowed(self):
        self._kyc_ok()
        a = self._accept_draft(trussel_altid={"answer": "ja", "note": "Ejer er partners ægtefælle"})
        r = self.call("post", f"/api/firm/acceptances/{a['id']}/approve", self.partner, {"decision": "godkendt"})
        self.assertEqual(r.status_code, 400)
        self.assertIn("afstå", r.json()["message"])
        r = self.call("post", f"/api/firm/acceptances/{a['id']}/approve", self.partner, {"decision": "afvist"})
        self.assertEqual(r.status_code, 200)

    def test_other_threats_require_documentation(self):
        self._kyc_ok()
        a = self._accept_draft(trussel_oevrige={"answer": "ja", "note": ""})
        r = self.call("post", f"/api/firm/acceptances/{a['id']}/approve", self.partner, {"decision": "godkendt"})
        self.assertEqual(r.status_code, 400)
        self.assertIn("§ 24, stk. 5", r.json()["message"])

    def test_declaration_conflict_removes_assignment_and_blocks_reassignment(self):
        answers = self._answers("independence", oekonomisk={"answer": "ja", "note": "Ejer 5 % af Alfa ApS", "clients": [self.co.slug]})
        r = self.call("post", "/api/firm/independence/sign", self.bog, {"answers": answers})
        self.assertEqual(r.status_code, 400)  # skal bekræftes
        r = self.call("post", "/api/firm/independence/sign", self.bog, {"answers": answers, "confirm": True})
        self.assertEqual(r.status_code, 200, r.content)
        self.assertFalse(StaffAssignment.objects.filter(staff=self.bog_staff, client=self.co).exists())
        # Kan ikke tildeles igen, før en partner har afklaret
        r = self.call("put", f"/api/firm/staff/{self.bog_staff.id}", self.partner, {"clients": [self.co.slug]})
        self.assertEqual(r.status_code, 409)
        r = self.call("put", f"/api/firm/clients/{self.co.slug}", self.partner, {"assigned_staff": [self.bog_staff.id]})
        self.assertEqual(r.status_code, 409)
        # Accept af kunden er spærret, mens forholdet er uafklaret
        self._kyc_ok()
        a = self._accept_draft(self.partner)
        r = self.call("post", f"/api/firm/acceptances/{a['id']}/approve", self.partner, {"decision": "godkendt"})
        self.assertIn("uafhængighed", r.json()["message"])
        # Sikkerhedsforanstaltninger kan ikke afhjælpe en § 2-trussel
        c = IndependenceConflict.objects.get()
        r = self.call("post", f"/api/firm/independence/conflicts/{c.id}/resolve", self.partner,
                      {"resolution": "sikkerhed", "note": "Review"})
        self.assertEqual(r.status_code, 400)
        r = self.call("post", f"/api/firm/independence/conflicts/{c.id}/resolve", self.partner,
                      {"resolution": "afhaendet", "note": "Anparterne er solgt 3/12"})
        self.assertEqual(r.status_code, 200, r.content)
        r = self.call("put", f"/api/firm/staff/{self.bog_staff.id}", self.partner, {"clients": [self.co.slug]})
        self.assertEqual(r.status_code, 200, r.content)
        # Underskrevet erklæring er låst
        r = self.call("post", "/api/firm/independence/sign", self.bog, {"answers": answers, "confirm": True})
        self.assertEqual(r.status_code, 409)

    def test_partner_cannot_resolve_own_conflict_and_overview(self):
        r = self.call("post", "/api/firm/independence/conflicts", self.partner,
                      {"client": self.co.slug, "question_id": "gaver", "note": "Vingave"})
        self.assertEqual(r.status_code, 201, r.content)
        cid = r.json()["data"]["conflict"]["id"]
        r = self.call("post", f"/api/firm/independence/conflicts/{cid}/resolve", self.partner,
                      {"resolution": "fjernet", "note": "x"})
        self.assertEqual(r.status_code, 403)
        r = self.call("post", f"/api/firm/independence/conflicts/{cid}/resolve", self.partner2,
                      {"resolution": "fjernet", "note": "Fjernet fra teamet"})
        self.assertEqual(r.status_code, 200)
        # "fjernet" spærrer fortsat tildeling
        r = self.call("put", f"/api/firm/staff/{self.p1.id}", self.partner2, {"clients": [self.co.slug]})
        self.assertEqual(r.status_code, 409)
        d = self.call("get", "/api/firm/independence", self.partner2).json()["data"]
        self.assertEqual(len(d["staff"]), 3)
        self.assertEqual(len(d["conflicts"]), 1)
        d = self.call("get", "/api/firm/independence", self.bog).json()["data"]
        self.assertNotIn("staff", d)
