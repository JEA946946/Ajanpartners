"""Opdrag: tjeklister fra verificerede skabeloner, sign-off-rækkefølge, krav før godkendelse, kvalitetslog."""

import json
from datetime import date, timedelta

from django.contrib.auth import get_user_model
from django.test import Client, TransactionTestCase, override_settings

from firm import templating
from firm.models import ClientAcceptance, KycAssessment
from tenancy.models import Firm, FirmStaff, StaffAssignment
from tenancy.services import create_client, ensure_public_tenant

User = get_user_model()
PW = "Test-1234567"


@override_settings(FIRM_MFA_REQUIRED=False)
class EngagementTests(TransactionTestCase):
    def setUp(self):
        ensure_public_tenant("testserver")
        firm = Firm.current()
        self.partner = User.objects.create_user("p@x.dk", "p@x.dk", PW)
        FirmStaff.objects.create(user=self.partner, firm=firm, role="partner")
        self.revisor = User.objects.create_user("r@x.dk", "r@x.dk", PW)
        FirmStaff.objects.create(user=self.revisor, firm=firm, role="revisor")
        self.bog = User.objects.create_user("b@x.dk", "b@x.dk", PW)
        bs = FirmStaff.objects.create(user=self.bog, firm=firm, role="bogholder")
        self.co, _ = create_client(name="Café Alfa ApS", package_code="mini", created_by=self.partner,
                                   cvr="87654321", industry_code="561010", accounting_class="B")
        StaffAssignment.objects.create(staff=bs, client=self.co)
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

    def _create(self, kind="opstilling", checklists=("afstemning-moms",)):
        year = templating.default_year(templating.fiscal_years(self.co))
        r = self.call("post", "/api/firm/engagements", self.bog, {
            "client": self.co.slug, "kind": kind, "year": year["id"], "partner_id": self.partner.id,
            "checklists": list(checklists)})
        self.assertEqual(r.status_code, 201, r.content)
        return r.json()["data"]["engagement"], year

    def _answer_all(self, e):
        for run in e["checklists"]:
            for it in run["items"]:
                r = self.call("put", f"/api/firm/checklist-runs/{run['id']}/items/{it['id']}", self.bog, {"status": "ok"})
                self.assertEqual(r.status_code, 200, r.content)

    def _compliance_ok(self):
        KycAssessment.objects.create(client=self.co, version=1, status="godkendt",
                                     next_review_on=date.today() + timedelta(days=300))
        ClientAcceptance.objects.create(client=self.co, status="godkendt")

    def test_checklist_items_come_from_template_and_deadline_default(self):
        e, year = self._create(checklists=["afslutningstjekliste-aarsrapport-klasse-b"])
        from firm.deadlines import annual_report_due
        self.assertEqual(e["deadline"], annual_report_due(year["end"], "B").isoformat())
        items = e["checklists"][0]["items"]
        self.assertGreater(len(items), 20)
        # Risikobranche-afsnittet er flettet ind for en restaurant (DB07 561010)
        self.assertTrue(any("risikobranche" in i["text"] for i in items))
        self.assertTrue(all(i["section"] for i in items))
        # Opdragsfrist vises i fristkalenderen
        r = self.call("get", f"/api/firm/deadlines?kind=opdrag&from={date.fromisoformat(e['deadline']) - timedelta(days=5)}&to={date.fromisoformat(e['deadline']) + timedelta(days=5)}", self.partner)
        self.assertTrue(any(row.get("engagement") == e["id"] for row in r.json()["data"]["deadlines"]))

    def test_signoff_order_and_segregation(self):
        e, _ = self._create()
        url = f"/api/firm/engagements/{e['id']}/signoff"
        self.assertEqual(self.call("post", url, self.bog, {"step": "udfoert"}).status_code, 400)  # ubesvarede punkter
        self._answer_all(e)
        self.assertEqual(self.call("post", url, self.bog, {"step": "gennemgaaet"}).status_code, 400)
        self.assertEqual(self.call("post", url, self.bog, {"step": "udfoert"}).status_code, 200)
        # Låst efter sign-off
        run = e["checklists"][0]
        r = self.call("put", f"/api/firm/checklist-runs/{run['id']}/items/1", self.bog, {"status": ""})
        self.assertEqual(r.status_code, 409)
        self.assertEqual(self.call("post", url, self.bog, {"step": "gennemgaaet"}).status_code, 400)  # samme person
        self.assertEqual(self.call("post", url, self.revisor, {"step": "gennemgaaet"}).status_code, 200)
        # Godkendelse kræver partner, accept og KYC ved erklæringsopgaver
        self.assertEqual(self.call("post", url, self.revisor, {"step": "godkendt"}).status_code, 403)
        r = self.call("post", url, self.partner, {"step": "godkendt"})
        self.assertEqual(r.status_code, 400)
        self.assertIn("accepteret", r.json()["message"])
        self._compliance_ok()
        r = self.call("post", url, self.partner, {"step": "godkendt"})
        self.assertEqual(r.status_code, 200, r.content)
        self.assertEqual(r.json()["data"]["engagement"]["status"], "afsluttet")
        # Leveret
        r = self.call("put", f"/api/firm/engagements/{e['id']}", self.bog, {"status": "leveret"})
        self.assertEqual(r.json()["data"]["engagement"]["status"], "leveret")

    def test_reopen_keeps_history(self):
        e, _ = self._create(kind="bogfoering")
        self._answer_all(e)
        self.call("post", f"/api/firm/engagements/{e['id']}/signoff", self.bog, {"step": "udfoert"})
        self.assertEqual(self.call("post", f"/api/firm/engagements/{e['id']}/reopen", self.revisor, {"note": "x"}).status_code, 403)
        r = self.call("post", f"/api/firm/engagements/{e['id']}/reopen", self.partner, {"note": "Ny momsafstemning"})
        d = r.json()["data"]["engagement"]
        self.assertEqual(d["status"], "i_gang")
        self.assertEqual(d["signoffs"], [])
        self.assertEqual(len(d["signoff_history"]), 1)
        self.assertIsNotNone(d["signoff_history"][0]["revoked_at"])

    def test_bemaerkning_requires_note_and_meta(self):
        e, _ = self._create()
        run = e["checklists"][0]
        r = self.call("put", f"/api/firm/checklist-runs/{run['id']}/items/1", self.bog, {"status": "bemaerkning"})
        self.assertEqual(r.status_code, 400)
        meta = self.call("get", "/api/firm/engagements/meta", self.bog).json()["data"]
        op = next(k for k in meta["kinds"] if k["value"] == "opstilling")
        self.assertIn("afstemning-moms", op["suggested"])
        self.assertEqual(op["letter"], "opdragsbrev-opstilling")

    def test_quality_log(self):
        r = self.call("post", "/api/firm/quality-log", self.bog, {"kind": "evaluering", "title": "x"})
        self.assertEqual(r.status_code, 403)
        r = self.call("post", "/api/firm/quality-log", self.bog, {"kind": "konsultation", "title": "Igangværende arbejder", "client": self.co.slug})
        self.assertEqual(r.status_code, 201)
        qid = r.json()["data"]["entry"]["id"]
        r = self.call("put", f"/api/firm/quality-log/{qid}", self.partner, {"close": True})
        self.assertEqual(r.status_code, 400)
        r = self.call("put", f"/api/firm/quality-log/{qid}", self.partner, {"follow_up": "Drøftet med partner", "close": True})
        self.assertIsNotNone(r.json()["data"]["entry"]["closed_at"])
