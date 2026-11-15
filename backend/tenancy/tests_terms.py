"""Forretningsbetingelser og databehandleraftale: accept ved første login."""

import json

from django.contrib.auth import get_user_model
from django.test import Client, TransactionTestCase, override_settings
from rest_framework_simplejwt.tokens import RefreshToken

from tenancy.models import Firm, FirmStaff, TermsAcceptance, TermsDocument
from tenancy.services import create_client, ensure_public_tenant

User = get_user_model()


@override_settings(FIRM_MFA_REQUIRED=False)
class TermsTests(TransactionTestCase):
    def setUp(self):
        ensure_public_tenant("testserver")  # publicerer udkastene
        self.partner = User.objects.create_user("partner@x.dk", "partner@x.dk", "Rimelig-lang-kode-77")
        FirmStaff.objects.create(user=self.partner, firm=Firm.current(), role="partner")
        self.c, (self.owner, _) = create_client(name="Delta ApS", owner_email="d@d.dk", created_by=self.partner)
        self.http = Client()

    def tearDown(self):
        from django.db import connection
        connection.set_schema_to_public()
        with connection.cursor() as cur:
            cur.execute(f'DROP SCHEMA IF EXISTS "{self.c.schema_name}" CASCADE')

    def call(self, method, path, user=None, slug=None, data=None, **extra):
        headers = dict(extra)
        if user:
            headers["HTTP_AUTHORIZATION"] = f"Bearer {RefreshToken.for_user(user).access_token}"
        if slug:
            headers["HTTP_X_CLIENT"] = slug
        return getattr(self.http, method)(path, data=json.dumps(data) if data is not None else None,
                                          content_type="application/json", **headers)

    def accept(self, user=None):
        user = user or self.owner
        req = self.call("get", "/api/v1/me/terms", user).json()["data"]["required"]
        shas = [d["sha256"] for r in req for d in r["documents"]]
        return self.call("post", "/api/v1/me/terms/accept", user,
                         data={"client": self.c.slug, "confirm": True, "sha256": shas},
                         HTTP_USER_AGENT="Testbrowser")

    def test_client_user_must_accept_but_firm_need_not(self):
        r = self.call("get", "/api/v1/accounts", self.owner, self.c.slug)
        self.assertEqual(r.json()["code"], "terms_acceptance_required")
        self.assertEqual(self.call("get", "/api/v1/accounts", self.partner, self.c.slug).status_code, 200)
        me = self.call("get", "/api/v1/me", self.owner).json()["data"]
        self.assertEqual({d["kind"] for d in me["terms_required"][0]["documents"]}, {"terms", "dpa"})
        self.assertEqual(self.accept().status_code, 200)
        self.assertEqual(self.call("get", "/api/v1/accounts", self.owner, self.c.slug).status_code, 200)

    def test_acceptance_is_evidence(self):
        self.call("post", "/api/v1/me/terms/accept", self.owner, data={"client": self.c.slug})  # uden flueben
        self.assertFalse(TermsAcceptance.objects.exists())
        self.accept()
        rows = TermsAcceptance.objects.filter(user=self.owner, client=self.c)
        self.assertEqual(rows.count(), 2)
        for a in rows:
            self.assertEqual(a.sha256, a.document.sha256)
            self.assertEqual((a.ip_address, a.user_agent, a.method), ("127.0.0.1", "Testbrowser", "click"))
        self.c.refresh_from_db()
        self.assertIsNotNone(self.c.agreement_accepted_on)

    def test_new_version_requires_new_acceptance(self):
        self.accept()
        self.call("post", "/api/firm/terms", self.partner, data={
            "kind": "terms", "version": "2027-01", "title": "Forretningsbetingelser", "body": "Ny tekst"})
        r = self.call("get", "/api/v1/accounts", self.owner, self.c.slug)
        self.assertEqual(r.json()["code"], "terms_acceptance_required")
        self.accept()
        self.assertEqual(self.call("get", "/api/v1/accounts", self.owner, self.c.slug).status_code, 200)

    def test_published_version_cannot_be_overwritten(self):
        current = TermsDocument.current("terms")
        r = self.call("post", "/api/firm/terms", self.partner, data={
            "kind": "terms", "version": current.version, "body": "Ændret"})
        self.assertEqual(r.status_code, 400)

    def test_stale_text_is_rejected(self):
        r = self.call("post", "/api/v1/me/terms/accept", self.owner,
                      data={"client": self.c.slug, "confirm": True, "sha256": ["forældet"]})
        self.assertEqual(r.status_code, 409)

    def test_public_terms_readable_without_login(self):
        r = self.call("get", "/api/v1/public/terms/dpa")
        self.assertEqual(r.status_code, 200)
        self.assertIn("Databehandleraftale", r.json()["data"]["document"]["title"])

    def test_export_allowed_without_acceptance(self):
        # Retten til at få sine data udleveret afhænger ikke af accept af nye betingelser.
        self.assertEqual(self.call("get", "/api/v1/export-all", self.owner, self.c.slug).status_code, 200)


    @override_settings(TERMS_SIGNATURE_METHOD="mitid", ESIGN_PROVIDER="mock")
    def test_mitid_signature_with_mock_provider(self):
        r = self.call("post", "/api/v1/me/terms/accept", self.owner, data={"client": self.c.slug, "confirm": True})
        self.assertEqual(r.status_code, 400)  # afkrydsning er slået fra
        start = self.call("post", "/api/v1/me/terms/sign", self.owner,
                          data={"client": self.c.slug, "return_url": "/onboarding"}).json()["data"]
        self.assertIn("signed=", start["url"])
        r = self.call("post", "/api/v1/me/terms/sign/complete", self.owner,
                      data={"client": self.c.slug, "reference": start["reference"]})
        self.assertEqual(r.status_code, 200)
        self.assertEqual(set(TermsAcceptance.objects.filter(user=self.owner).values_list("method", flat=True)), {"mitid"})
        self.assertEqual(self.call("get", "/api/v1/accounts", self.owner, self.c.slug).status_code, 200)

    @override_settings(TERMS_SIGNATURE_METHOD="mitid", ESIGN_PROVIDER="penneo")
    def test_real_provider_explains_agreement(self):
        r = self.call("post", "/api/v1/me/terms/sign", self.owner, data={"client": self.c.slug})
        self.assertEqual(r.status_code, 501)
        self.assertIn("Penneo", r.json()["message"])
