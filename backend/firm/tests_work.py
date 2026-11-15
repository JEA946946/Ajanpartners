"""Admin-portalen: frister, opgaver/indbakke og revisorværktøjer.

Kør: DB_NAME=… TEST_DB_NAME=test_ap_admin manage.py test firm
"""

import json

from django.contrib.auth import get_user_model
from django.test import Client, TransactionTestCase, override_settings

from firm.models import AccountComment, FirmTask, TaskMessage
from tenancy.models import AccessGrant, Firm, FirmAuditLog, FirmStaff
from tenancy.services import accept_grant, create_client, ensure_public_tenant

User = get_user_model()
PW = "Test-1234567"


@override_settings(FIRM_MFA_REQUIRED=False)  # MFA testes i tenancy.tests_security
class FirmWorkTests(TransactionTestCase):
    def setUp(self):
        ensure_public_tenant("testserver")
        self.partner = User.objects.create_user("partner@x.dk", "partner@x.dk", PW)
        FirmStaff.objects.create(user=self.partner, firm=Firm.current(), role="partner")
        self.bogholder = User.objects.create_user("bog@x.dk", "bog@x.dk", PW)
        FirmStaff.objects.create(user=self.bogholder, firm=Firm.current(), role="bogholder")
        self.a, (self.owner_a, _) = create_client(name="Alfa ApS", package_code="mini", owner_email="a@a.dk",
                                                  created_by=self.partner, vat_period="quarter")
        self.b, (self.owner_b, _) = create_client(name="Beta ApS", package_code="pro", owner_email="b@b.dk",
                                                  created_by=self.partner, legal_form="enk", accounting_class="A")
        from tenancy.terms import accept, required_documents
        for owner, client in ((self.owner_a, self.a), (self.owner_b, self.b)):
            accept(owner, client, required_documents())
        self.http = Client()

    def tearDown(self):
        from django.db import connection
        connection.set_schema_to_public()
        for c in (self.a, self.b):
            with connection.cursor() as cur:
                cur.execute(f'DROP SCHEMA IF EXISTS "{c.schema_name}" CASCADE')

    def call(self, method, path, user, slug=None, data=None):
        from rest_framework_simplejwt.tokens import RefreshToken
        headers = {"HTTP_AUTHORIZATION": f"Bearer {RefreshToken.for_user(user).access_token}"}
        if slug:
            headers["HTTP_X_CLIENT"] = slug
        return getattr(self.http, method)(path, data=json.dumps(data) if data is not None else None,
                                          content_type="application/json", **headers)

    # ─── Frister ──────────────────────────────────────────────────────────────

    def test_deadlines_endpoint(self):
        r = self.call("get", "/api/firm/deadlines?from=2026-01-01&to=2026-12-31", self.partner)
        self.assertEqual(r.status_code, 200)
        rows = r.json()["data"]["deadlines"]
        alfa = [d for d in rows if d["client"] == self.a.slug]
        self.assertIn("2026-06-01", [d["date"] for d in alfa if d["kind"] == "moms"])
        self.assertIn("aarsrapport", {d["kind"] for d in alfa})
        beta = {d["kind"] for d in rows if d["client"] == self.b.slug}
        self.assertNotIn("aarsrapport", beta)  # personlig virksomhed, klasse A
        # Bogholderen uden tildelte kunder ser ingen
        r = self.call("get", "/api/firm/deadlines", self.bogholder)
        self.assertEqual(r.json()["data"]["deadlines"], [])

    def test_client_list_has_next_deadline(self):
        r = self.call("get", "/api/firm/clients", self.partner)
        c = next(c for c in r.json()["data"]["clients"] if c["slug"] == self.a.slug)
        self.assertIsNotNone(c["next_deadline"])
        self.assertEqual(c["access"], "full")  # adgang fra oprettelsen iht. kundeaftalen

    # ─── Opgaver og indbakke ──────────────────────────────────────────────────

    def test_task_flow_and_isolation(self):
        accept_grant(AccessGrant.objects.get(client=self.a), self.owner_a)
        r = self.call("post", "/api/firm/tasks", self.partner, data={
            "client": self.a.slug, "kind": "bilag_mangler", "title": "Mangler bilag",
            "message": "Kan du sende kvitteringen?", "reference_type": "bank_line", "reference_id": "abc"})
        self.assertEqual(r.status_code, 201, r.content)
        task_id = r.json()["data"]["task"]["id"]
        self.call("post", "/api/firm/tasks", self.partner, data={
            "client": self.a.slug, "kind": "opgave", "title": "Intern", "visible_to_client": False})

        # Kunden ser kun sin synlige opgave
        r = self.call("get", "/api/v1/inbox", self.owner_a, self.a.slug)
        self.assertEqual(r.status_code, 200, r.content)
        self.assertEqual([t["id"] for t in r.json()["data"]["tasks"]], [task_id])
        # Kunde B ser intet, heller ikke ved at gætte id'et
        self.assertEqual(self.call("get", "/api/v1/inbox", self.owner_b, self.b.slug).json()["data"]["tasks"], [])
        self.assertEqual(self.call("get", f"/api/v1/inbox/{task_id}", self.owner_b, self.b.slug).status_code, 404)
        self.assertEqual(self.call("post", f"/api/v1/inbox/{task_id}/reply", self.owner_b, self.b.slug,
                                   {"body": "hack"}).status_code, 404)
        # Kunde A kan ikke sætte X-Client til B
        self.assertEqual(self.call("get", "/api/v1/inbox", self.owner_a, self.b.slug).status_code, 403)

        r = self.call("post", f"/api/v1/inbox/{task_id}/reply", self.owner_a, self.a.slug, {"body": "Vedhæftet"})
        self.assertEqual(r.status_code, 201, r.content)
        task = FirmTask.objects.get(pk=task_id)
        self.assertEqual(task.status, "answered")
        self.assertFalse(TaskMessage.objects.filter(task=task).order_by("-created_at").first().from_firm)

        # Revisoren svarer → afventer kunden igen; lukker sagen
        r = self.call("post", f"/api/firm/tasks/{task_id}/messages", self.partner, data={"body": "Tak"})
        self.assertEqual(r.json()["data"]["task"]["status"], "open")
        r = self.call("put", f"/api/firm/tasks/{task_id}", self.partner, data={"status": "closed"})
        self.assertIsNotNone(r.json()["data"]["task"]["closed_at"])
        self.assertEqual(self.call("post", f"/api/v1/inbox/{task_id}/reply", self.owner_a, self.a.slug,
                                   {"body": "igen"}).status_code, 400)
        # Med kundens svar kan opgaven ikke slettes
        self.assertEqual(self.call("delete", f"/api/firm/tasks/{task_id}", self.partner).status_code, 400)
        self.assertTrue(FirmAuditLog.objects.filter(action="task_created", client=self.a).exists())

    def test_bogholder_only_assigned_tasks(self):
        FirmTask.objects.create(client=self.a, title="x")
        r = self.call("get", "/api/firm/tasks", self.bogholder)
        self.assertEqual(r.json()["data"]["tasks"], [])
        r = self.call("post", "/api/firm/tasks", self.bogholder, data={"client": self.a.slug, "title": "y"})
        self.assertEqual(r.status_code, 404)

    def test_inbox_reply_rejects_bad_document(self):
        task = FirmTask.objects.create(client=self.a, title="x")
        r = self.call("post", f"/api/v1/inbox/{task.id}/reply", self.owner_a, self.a.slug,
                      {"body": "", "document_id": "ikke-et-id"})
        self.assertEqual(r.status_code, 400)

    # ─── Revisorværktøjer ─────────────────────────────────────────────────────

    def test_tools_need_grant(self):
        from tenancy.services import end_access, open_access
        end_access(self.a, self.partner)  # aftalen ophørt → ingen tal fra bøgerne
        self.assertEqual(self.call("get", f"/api/firm/clients/{self.a.slug}/trial-balance", self.partner).status_code, 403)
        self.assertEqual(self.call("get", f"/api/firm/clients/{self.a.slug}/account-comments", self.partner).status_code, 403)
        open_access(self.a, self.partner)
        r = self.call("get", f"/api/firm/clients/{self.a.slug}/trial-balance", self.partner)
        self.assertEqual(r.status_code, 200, r.content)
        r = self.call("get", f"/api/firm/clients/{self.a.slug}/trial-balance?export=csv&from=2026-01-01&to=2026-12-31",
                      self.partner)
        self.assertEqual(r.status_code, 200)
        self.assertTrue(r.content.decode("utf-8").lstrip("﻿").startswith("Kontonr;Kontonavn"))
        r = self.call("post", f"/api/firm/clients/{self.a.slug}/account-comments", self.partner,
                      data={"account_code": "1000", "body": "Afstem mod årsopgørelse", "fiscal_year": 2026})
        self.assertEqual(r.status_code, 201)
        self.assertEqual(AccountComment.objects.filter(client=self.a).count(), 1)

    def test_packages_show_client_count(self):
        r = self.call("get", "/api/firm/packages", self.partner)
        counts = {p["code"]: p["client_count"] for p in r.json()["data"]["packages"]}
        self.assertEqual(counts["mini"], 1)
        self.assertEqual(counts["pro"], 1)
