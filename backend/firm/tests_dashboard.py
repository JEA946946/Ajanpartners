"""Fuldmagter og overblik: registrering, tilbagekaldelse, udløbsopgaver, rettigheder og dashboardets tal."""

import io
import json
from datetime import date, timedelta

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import Client, TransactionTestCase, override_settings

from firm.models import Engagement, FirmTask, PowerOfAttorney
from tenancy.models import Firm, FirmStaff, StaffAssignment
from tenancy.services import create_client, ensure_public_tenant

User = get_user_model()
PW = "Test-1234567"


@override_settings(FIRM_MFA_REQUIRED=False)
class DashboardTests(TransactionTestCase):
    def setUp(self):
        ensure_public_tenant("testserver")
        firm = Firm.current()
        self.partner = User.objects.create_user("p@x.dk", "p@x.dk", PW)
        FirmStaff.objects.create(user=self.partner, firm=firm, role="partner")
        self.bog = User.objects.create_user("b@x.dk", "b@x.dk", PW)
        bs = FirmStaff.objects.create(user=self.bog, firm=firm, role="bogholder")
        self.co, _ = create_client(name="Kunde ApS", package_code="mini", created_by=self.partner, cvr="87654321",
                                   owner_email="ejer@kunde.dk")
        self.other, _ = create_client(name="Anden ApS", package_code="mini", created_by=self.partner, cvr="11223344")
        StaffAssignment.objects.create(staff=bs, client=self.co)
        self.http = Client()

    def tearDown(self):
        from django.db import connection
        connection.set_schema_to_public()
        with connection.cursor() as cur:
            for s in (self.co.schema_name, self.other.schema_name):
                cur.execute(f'DROP SCHEMA IF EXISTS "{s}" CASCADE')

    def call(self, method, path, user, data=None):
        from rest_framework_simplejwt.tokens import RefreshToken
        kw = {"HTTP_AUTHORIZATION": f"Bearer {RefreshToken.for_user(user).access_token}"}
        if data is not None:
            kw.update(data=json.dumps(data), content_type="application/json")
        return getattr(self.http, method)(path, **kw)

    def test_powers_of_attorney(self):
        soon = (date.today() + timedelta(days=10)).isoformat()
        r = self.call("post", f"/api/firm/clients/{self.co.slug}/powers", self.bog,
                      {"kind": "skat", "scope": "Moms og A-skat", "holder_id": self.bog.id, "expires_on": soon})
        self.assertEqual(r.status_code, 201, r.content)
        p = r.json()["data"]["power"]
        self.assertEqual(p["status"], "expiring")
        self.assertEqual(self.call("post", f"/api/firm/clients/{self.other.slug}/powers", self.bog,
                                   {"kind": "bank", "scope": "x"}).status_code, 404)
        r = self.call("post", f"/api/firm/clients/{self.co.slug}/powers", self.bog, {"kind": "skat", "scope": ""})
        self.assertEqual(r.status_code, 400)
        # Udløbsopgave én gang
        call_command("poa_expiry_report", stdout=io.StringIO())
        call_command("poa_expiry_report", stdout=io.StringIO())
        t = FirmTask.objects.get(client=self.co, title__startswith="Fuldmagt udløber")
        self.assertEqual((t.assigned_to, t.visible_to_client), (self.bog, False))
        # Tilbagekaldes – slettes ikke, kan ikke ændres bagefter
        r = self.call("put", f"/api/firm/powers/{p['id']}", self.bog, {"revoke": True})
        self.assertEqual(r.json()["data"]["power"]["status"], "revoked")
        self.assertEqual(self.call("put", f"/api/firm/powers/{p['id']}", self.bog, {"scope": "y"}).status_code, 409)
        self.assertEqual(PowerOfAttorney.objects.count(), 1)

    def test_dashboard(self):
        Engagement.objects.create(client=self.co, kind="opstilling", deadline=date.today() - timedelta(days=3))
        Engagement.objects.create(client=self.co, kind="skat", deadline=date.today() + timedelta(days=5))
        Engagement.objects.create(client=self.other, kind="skat", deadline=date.today() + timedelta(days=5))
        PowerOfAttorney.objects.create(client=self.co, kind="virk", scope="x", expires_on=date.today() + timedelta(days=3))
        r = self.call("get", "/api/firm/dashboard", self.bog)
        self.assertEqual(r.status_code, 200, r.content)
        d = r.json()["data"]
        self.assertEqual(d["clients"], 1)  # kun tildelte kunder
        self.assertEqual(len(d["engagements"]["overdue"]), 1)
        self.assertTrue(any(x.get("kind") == "opdrag" for x in d["deadlines"]))
        self.assertEqual(d["kyc"]["missing"], 1)
        self.assertEqual(len(d["powers"]), 1)
        self.assertNotIn("unbilled", d)          # kun partnere
        self.assertNotIn("missing", d["independence"])
        self.assertEqual([t["client"] for t in d["terms_pending"]], [self.co.slug])  # ejeren har ikke accepteret
        d = self.call("get", "/api/firm/dashboard", self.partner).json()["data"]
        self.assertEqual(d["clients"], 2)
        self.assertIn("unbilled", d)
        self.assertEqual(len(d["independence"]["missing"]), 2)
        self.assertTrue(d["evaluation_missing"])
