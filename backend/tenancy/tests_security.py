"""To-faktor, adgangskoder, læselogning, eksport af alt og opbevaringsjobbet."""

import io
import json
import zipfile

import pyotp
from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import Client, TransactionTestCase
from django.utils import timezone
from rest_framework_simplejwt.tokens import RefreshToken

from payroll.crypto import decrypt
from tenancy import mfa
from tenancy.models import AccessGrant, Firm, FirmAuditLog, FirmStaff
from tenancy.services import accept_grant, archive_client, create_client, ensure_public_tenant

User = get_user_model()
PW = "Rimelig-lang-kode-77"


class SecurityTests(TransactionTestCase):
    def setUp(self):
        ensure_public_tenant("testserver")
        self.partner = User.objects.create_user("partner@x.dk", "partner@x.dk", PW)
        FirmStaff.objects.create(user=self.partner, firm=Firm.current(), role="partner")
        self.client_co, (self.owner, _) = create_client(name="Gamma ApS", package_code="standard",
                                                        owner_email="g@g.dk", created_by=self.partner)
        self.owner.set_password(PW)
        self.owner.save()
        self.http = Client()

    def tearDown(self):
        from django.db import connection
        connection.set_schema_to_public()
        with connection.cursor() as cur:
            cur.execute(f'DROP SCHEMA IF EXISTS "{self.client_co.schema_name}" CASCADE')

    def call(self, method, path, user, slug=None, data=None):
        headers = {"HTTP_AUTHORIZATION": f"Bearer {RefreshToken.for_user(user).access_token}"}
        if slug:
            headers["HTTP_X_CLIENT"] = slug
        return getattr(self.http, method)(path, data=json.dumps(data) if data else None,
                                          content_type="application/json", **headers)

    def enable_mfa(self, user):
        secret = mfa.start_setup(user)["secret"]
        codes = mfa.confirm_setup(user, pyotp.TOTP(secret).now())
        self.assertEqual(len(codes), 10)
        return secret, codes

    # ── MFA ──
    def test_firm_staff_without_mfa_is_blocked(self):
        accept_grant(AccessGrant.objects.get(client=self.client_co), self.owner)
        r = self.call("get", "/api/firm/clients", self.partner)
        self.assertEqual(r.status_code, 403)
        self.assertEqual(r.json()["code"], "mfa_setup_required")
        r = self.call("get", "/api/v1/accounts", self.partner, self.client_co.slug)
        self.assertEqual(r.json()["code"], "mfa_setup_required")
        self.enable_mfa(self.partner)
        self.assertEqual(self.call("get", "/api/firm/clients", self.partner).status_code, 200)
        self.assertEqual(self.call("get", "/api/v1/accounts", self.partner, self.client_co.slug).status_code, 200)

    def test_two_step_login(self):
        secret, codes = self.enable_mfa(self.owner)
        r = self.http.post("/api/v1/auth/login", {"username": "g@g.dk", "password": PW},
                           content_type="application/json").json()
        self.assertTrue(r["data"]["mfa_required"])
        self.assertNotIn("token", r["data"])
        bad = self.http.post("/api/v1/auth/mfa/verify", {"mfa_token": r["data"]["mfa_token"], "code": "000000"},
                             content_type="application/json")
        self.assertEqual(bad.status_code, 401)
        # Gendannelseskode virker én gang (TOTP-koden fra confirm er allerede brugt).
        ok = self.http.post("/api/v1/auth/mfa/verify", {"mfa_token": r["data"]["mfa_token"], "code": codes[0]},
                            content_type="application/json")
        self.assertEqual(ok.status_code, 200)
        self.assertIn("token", ok.json()["data"])
        again = self.http.post("/api/v1/auth/mfa/verify", {"mfa_token": r["data"]["mfa_token"], "code": codes[0]},
                               content_type="application/json")
        self.assertEqual(again.status_code, 401)

    def test_totp_code_cannot_be_reused(self):
        secret = mfa.start_setup(self.owner)["secret"]
        code = pyotp.TOTP(secret).now()
        self.assertIsNotNone(mfa.confirm_setup(self.owner, code))
        self.assertFalse(mfa.verify_code(mfa.device_of(self.owner), code))

    def test_secret_is_encrypted(self):
        secret = mfa.start_setup(self.owner)["secret"]
        stored = mfa.device_of(self.owner).secret_encrypted
        self.assertNotIn(secret, stored)
        self.assertEqual(decrypt(stored), secret)

    def test_staff_cannot_disable_mfa(self):
        secret, _ = self.enable_mfa(self.partner)
        r = self.call("post", "/api/v1/me/mfa/disable", self.partner, data={"password": PW, "code": "123456"})
        self.assertEqual(r.status_code, 403)

    # ── Adgangskoder ──
    def test_password_validators(self):
        r = self.call("post", "/api/v1/me/password", self.owner,
                      data={"current_password": PW, "new_password": "1234567890"})
        self.assertEqual(r.status_code, 400)
        r = self.call("post", "/api/v1/me/password", self.owner,
                      data={"current_password": PW, "new_password": "Ny-og-meget-bedre-kode-42"})
        self.assertEqual(r.status_code, 200)

    # ── Læselogning ──
    def test_firm_read_is_logged_once_per_hour(self):
        self.enable_mfa(self.partner)
        accept_grant(AccessGrant.objects.get(client=self.client_co), self.owner)
        for _ in range(3):
            self.call("get", "/api/v1/accounts", self.partner, self.client_co.slug)
        reads = FirmAuditLog.objects.filter(client=self.client_co, action="read")
        self.assertEqual(reads.count(), 1)
        self.assertEqual(reads.first().detail["first_path"], "/api/v1/accounts")

    # ── Eksportér alt ──
    def _zip(self, response):
        return zipfile.ZipFile(io.BytesIO(b"".join(response.streaming_content)))

    def test_owner_exports_everything_also_when_archived(self):
        archive_client(self.client_co)
        r = self.call("get", "/api/v1/export-all", self.owner, self.client_co.slug)
        self.assertEqual(r.status_code, 200)
        names = self._zip(r).namelist()
        for required in ("bilag.csv", "audit_log.json", "MANIFEST.txt", "LÆS_MIG.txt"):
            self.assertIn(required, names)
        log = json.loads(self._zip(self.call("get", "/api/v1/export-all", self.owner, self.client_co.slug))
                         .read("audit_log.json"))
        self.assertTrue(log["chain"]["ok"])

    def test_firm_export_needs_grant_unless_archived_and_partner(self):
        self.enable_mfa(self.partner)
        slug = self.client_co.slug
        self.assertEqual(self.call("get", f"/api/firm/clients/{slug}/export-all", self.partner).status_code, 403)
        archive_client(self.client_co)
        r = self.call("get", f"/api/firm/clients/{slug}/export-all", self.partner)
        self.assertEqual(r.status_code, 200)
        self.assertTrue(FirmAuditLog.objects.filter(client=self.client_co, action="export_all").exists())

    # ── Opbevaring ──
    def test_retention_report_creates_one_task(self):
        from firm.models import FirmTask
        archive_client(self.client_co)
        self.client_co.retain_until = timezone.localdate()
        self.client_co.save()
        call_command("retention_report", verbosity=0)
        call_command("retention_report", verbosity=0)
        tasks = FirmTask.objects.filter(client=self.client_co)
        self.assertEqual(tasks.count(), 1)
        self.assertFalse(tasks.first().visible_to_client)
