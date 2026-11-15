"""Kunderne er adskilt, og revisorhuset kommer kun ind med kundens samtykke.

Kør: DB_NAME=… TEST_DB_NAME=test_ap_main manage.py test tenancy.tests_isolation
"""

import json

from django.contrib.auth import get_user_model
from django.test import Client, TransactionTestCase, override_settings
from django_tenants.utils import schema_context

from tenancy.models import AccessGrant, FirmAuditLog, FirmStaff, Firm
from tenancy.services import accept_grant, archive_client, create_client, end_access, ensure_public_tenant
from tenancy.terms import accept, required_documents

User = get_user_model()
PW = "Test-1234567"


@override_settings(FIRM_MFA_REQUIRED=False)  # MFA testes i tests_security
class IsolationTests(TransactionTestCase):
    reset_sequences = False

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

    def setUp(self):
        ensure_public_tenant("testserver")
        self.partner = User.objects.create_user("partner@x.dk", "partner@x.dk", PW)
        FirmStaff.objects.create(user=self.partner, firm=Firm.current(), role="partner")
        self.bogholder = User.objects.create_user("bog@x.dk", "bog@x.dk", PW)
        FirmStaff.objects.create(user=self.bogholder, firm=Firm.current(), role="bogholder")
        self.a, (self.owner_a, _) = create_client(name="Alfa ApS", package_code="mini", owner_email="a@a.dk",
                                                  created_by=self.partner)
        self.b, (self.owner_b, _) = create_client(name="Beta ApS", package_code="pro", owner_email="b@b.dk",
                                                  created_by=self.partner)
        for u, c in ((self.owner_a, self.a), (self.owner_b, self.b)):
            u.set_password(PW)
            u.save()
            accept(u, c, required_documents())  # betingelserne accepteres ved første login
        self.http = Client()

    def tearDown(self):
        from django.db import connection
        connection.set_schema_to_public()
        for c in (self.a, self.b):
            with connection.cursor() as cur:
                cur.execute(f'DROP SCHEMA IF EXISTS "{c.schema_name}" CASCADE')

    def token(self, user):
        # Login er throttlet (10/min); en token pr. bruger rækker.
        from rest_framework_simplejwt.tokens import RefreshToken
        return str(RefreshToken.for_user(user).access_token)

    def call(self, method, path, user, slug=None, data=None):
        headers = {"HTTP_AUTHORIZATION": f"Bearer {self.token(user)}"}
        if slug:
            headers["HTTP_X_CLIENT"] = slug
        return getattr(self.http, method)(path, data=json.dumps(data) if data else None,
                                          content_type="application/json", **headers)

    def test_member_only_sees_own_client(self):
        self.assertEqual(self.call("get", "/api/v1/accounts", self.owner_a, self.a.slug).status_code, 200)
        self.assertEqual(self.call("get", "/api/v1/accounts", self.owner_a, self.b.slug).status_code, 403)
        self.assertEqual(self.call("get", "/api/v1/accounts", self.owner_a, "findes-ikke").status_code, 403)
        self.assertEqual(self.call("get", "/api/v1/accounts", self.owner_a).status_code, 400)

    def test_schemas_are_separate(self):
        from accounts.models import Account
        with schema_context(self.a.schema_name):
            Account.objects.filter(is_active=True).update(description="kun-alfa")
        with schema_context(self.b.schema_name):
            self.assertFalse(Account.objects.filter(description="kun-alfa").exists())

    def test_firm_has_access_from_creation(self):
        # Adgangen følger kundeaftalen: ingen godkendelse fra kunden i systemet.
        self.assertEqual(self.call("get", "/api/v1/accounts", self.partner, self.a.slug).status_code, 200)
        end_access(self.a, self.partner)  # aftalen er ophørt
        self.assertEqual(self.call("get", "/api/v1/accounts", self.partner, self.a.slug).status_code, 403)

    def test_archived_client_is_read_only_for_firm(self):
        archive_client(self.b)
        self.assertEqual(self.call("get", "/api/v1/accounts", self.partner, self.b.slug).status_code, 200)
        r = self.call("post", "/api/v1/customers", self.partner, self.b.slug, {"name": "Ny A/S"})
        self.assertEqual(r.json()["code"], "client_archived")

    def test_client_cannot_change_firm_access(self):
        grant = AccessGrant.objects.get(client=self.a)
        for path in (f"/api/v1/access-grants/{grant.id}/revoke", "/api/v1/access-grants/create"):
            self.assertEqual(self.call("post", path, self.owner_a, self.a.slug).status_code, 404)
        r = self.call("get", "/api/v1/access-grants", self.owner_a, self.a.slug)
        self.assertEqual(r.status_code, 200)
        self.assertTrue(r.json()["data"]["access_active"])

    def test_bogholder_needs_assignment(self):
        accept_grant(AccessGrant.objects.get(client=self.a), self.owner_a)
        self.assertEqual(self.call("get", "/api/v1/accounts", self.bogholder, self.a.slug).status_code, 403)
        from tenancy.models import StaffAssignment
        StaffAssignment.objects.create(staff=self.bogholder.firm_staff, client=self.a)
        self.assertEqual(self.call("get", "/api/v1/accounts", self.bogholder, self.a.slug).status_code, 200)

    def test_read_grant_cannot_write(self):
        grant = AccessGrant.objects.get(client=self.a)
        grant.scope = "read"
        grant.save()
        accept_grant(grant, self.owner_a)
        r = self.call("post", "/api/v1/fiscal-years", self.partner, self.a.slug,
                      {"name": "Kunde A/S"})
        self.assertEqual(r.status_code, 403)

    def test_package_limits_client_users_not_firm(self):
        accept_grant(AccessGrant.objects.get(client=self.a), self.owner_a)
        r = self.call("get", "/api/v1/payroll/employees", self.owner_a, self.a.slug)
        self.assertEqual(r.status_code, 403)
        self.assertEqual(r.json()["code"], "feature_not_in_package")
        r = self.call("get", "/api/v1/bills", self.partner, self.a.slug)
        self.assertNotEqual(r.status_code, 403)

    def test_firm_write_is_logged(self):
        accept_grant(AccessGrant.objects.get(client=self.b), self.owner_b)
        self.call("post", "/api/v1/customers", self.partner, self.b.slug,
                  {"name": "Kunde A/S"})
        self.assertTrue(FirmAuditLog.objects.filter(client=self.b, action="write").exists())
        from core.models import AuditLog
        with schema_context(self.b.schema_name):
            log = AuditLog.objects.order_by("-seq").first()
            if log is not None:
                self.assertEqual(log.changes.get("_via"), "firm")

    def test_client_admin_cannot_touch_other_clients_users(self):
        r = self.call("post", f"/api/v1/users/{self.owner_b.id}/reset-password", self.owner_a, self.a.slug)
        self.assertEqual(r.status_code, 404)

    def test_firm_endpoints_require_staff(self):
        self.assertEqual(self.call("get", "/api/firm/clients", self.owner_a).status_code, 403)
        self.assertEqual(self.call("get", "/api/firm/clients", self.partner).status_code, 200)
        self.assertEqual(self.call("get", f"/api/firm/clients/{self.a.slug}/status", self.partner).status_code, 200)
        end_access(self.a, self.partner)
        r = self.call("get", f"/api/firm/clients/{self.a.slug}/status", self.partner)
        self.assertEqual(r.status_code, 403)  # stamdata ja, tal fra bøgerne kun med aktiv adgang
