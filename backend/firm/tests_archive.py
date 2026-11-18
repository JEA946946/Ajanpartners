"""Materialelister (PBC) og dokumentarkiv: punkter fra skabelon, kundens indbakke, versioner, deling og eksport."""

import io
import json
import zipfile
from datetime import date, timedelta

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.management import call_command
from django.test import Client, TransactionTestCase, override_settings

from firm import templating
from firm.models import ClientDocument, Engagement, FirmTask
from tenancy.models import Firm, FirmStaff, StaffAssignment
from tenancy.services import create_client, ensure_public_tenant

User = get_user_model()
PW = "Test-1234567"


@override_settings(FIRM_MFA_REQUIRED=False)
class ArchivePbcTests(TransactionTestCase):
    def setUp(self):
        ensure_public_tenant("testserver")
        firm = Firm.current()
        self.partner = User.objects.create_user("p@x.dk", "p@x.dk", PW)
        FirmStaff.objects.create(user=self.partner, firm=firm, role="partner")
        self.bog = User.objects.create_user("b@x.dk", "b@x.dk", PW)
        self.bs = FirmStaff.objects.create(user=self.bog, firm=firm, role="bogholder")
        self.co, (self.owner, _pw) = create_client(name="Kunde ApS", package_code="mini", created_by=self.partner,
                                                   cvr="87654321", owner_email="ejer@kunde.dk")
        self.other, _ = create_client(name="Anden ApS", package_code="mini", created_by=self.partner, cvr="11223344")
        from tenancy.terms import accept, required_documents
        accept(self.owner, self.co, required_documents())
        StaffAssignment.objects.create(staff=self.bs, client=self.co)
        y = templating.default_year(templating.fiscal_years(self.co))
        self.eng = Engagement.objects.create(client=self.co, kind="opstilling", year_start=y["start"],
                                             year_end=y["end"], manager=self.bog)
        self.http = Client()

    def tearDown(self):
        from django.db import connection
        connection.set_schema_to_public()
        with connection.cursor() as cur:
            for s in (self.co.schema_name, self.other.schema_name):
                cur.execute(f'DROP SCHEMA IF EXISTS "{s}" CASCADE')

    def call(self, method, path, user, data=None, client_slug=None, multipart=False):
        from rest_framework_simplejwt.tokens import RefreshToken
        kw = {"HTTP_AUTHORIZATION": f"Bearer {RefreshToken.for_user(user).access_token}"}
        if client_slug:
            kw["HTTP_X_CLIENT"] = client_slug
        if data is not None:
            kw.update(data=data) if multipart else kw.update(data=json.dumps(data), content_type="application/json")
        return getattr(self.http, method)(path, **kw)

    def test_pbc_from_template_to_client_inbox(self):
        r = self.call("get", f"/api/firm/engagements/{self.eng.id}/pbc/preview?template=materialeliste-aarsafslutning",
                      self.bog)
        self.assertEqual(r.status_code, 200, r.content)
        items = r.json()["data"]["items"]
        self.assertGreater(len(items), 20)
        due = (date.today() - timedelta(days=1)).isoformat()
        r = self.call("post", f"/api/firm/engagements/{self.eng.id}/pbc", self.bog, {
            "list_name": "Materialeliste 2026", "due_date": due,
            "items": [{"title": i["text"], "section": i["section"]} for i in items[:3]]})
        self.assertEqual(r.status_code, 201, r.content)
        lst = r.json()["data"]["lists"][0]
        self.assertEqual((lst["name"], len(lst["items"]), lst["overdue"]), ("Materialeliste 2026", 3, 3))
        # Kunden ser punkterne i sin indbakke
        r = self.call("get", "/api/v1/inbox", self.owner, client_slug=self.co.slug)
        self.assertEqual(r.status_code, 200, r.content)
        tasks = r.json()["data"]["tasks"]
        self.assertEqual(len(tasks), 3)
        self.assertTrue(all(t["list_name"] == "Materialeliste 2026" for t in tasks))
        # Påmindelse: én intern opgave pr. liste, ikke dubleret
        call_command("pbc_reminders", stdout=io.StringIO())
        call_command("pbc_reminders", stdout=io.StringIO())
        internal = FirmTask.objects.filter(engagement=self.eng, visible_to_client=False)
        self.assertEqual(internal.count(), 1)
        self.assertEqual(internal.first().assigned_to, self.bog)

    def test_archive_versions_sharing_and_export(self):
        url = f"/api/firm/clients/{self.co.slug}/documents"
        up = lambda content: self.call("post", url, self.bog, {
            "file": SimpleUploadedFile("aarsrapport.pdf", content, content_type="application/pdf"),
            "kind": "aarsrapport", "title": "Årsrapport 2025", "engagement": str(self.eng.id)}, multipart=True)
        r1, r2 = up(b"%PDF v1"), up(b"%PDF v2")
        self.assertEqual(r1.status_code, 201, r1.content)
        self.assertEqual([r1.json()["data"]["document"]["version"], r2.json()["data"]["document"]["version"]], [1, 2])
        d2 = r2.json()["data"]["document"]
        # Bogholderen har ikke adgang til en anden kundes arkiv
        self.assertEqual(self.call("get", f"/api/firm/clients/{self.other.slug}/documents", self.bog).status_code, 404)
        # Kunden ser kun delte dokumenter
        r = self.call("get", "/api/v1/firm-documents", self.owner, client_slug=self.co.slug)
        self.assertEqual(r.json()["data"]["documents"], [])
        r = self.call("put", f"/api/firm/documents/{d2['id']}", self.bog,
                      {"visible_to_client": True, "signed_on": "2026-05-20", "signed_note": "Direktøren"})
        self.assertTrue(r.json()["data"]["document"]["visible_to_client"])
        docs = self.call("get", "/api/v1/firm-documents", self.owner, client_slug=self.co.slug).json()["data"]["documents"]
        self.assertEqual([d["version"] for d in docs], [2])
        self.assertNotIn("note", docs[0])
        r = self.call("get", f"/api/v1/firm-documents/{d2['id']}", self.owner, client_slug=self.co.slug)
        self.assertEqual(b"".join(r.streaming_content), b"%PDF v2")
        # Eksporten indeholder kun det delte dokument
        from tenancy.export import build_export
        path = build_export(self.co, self.partner)
        with zipfile.ZipFile(path) as zf:
            names = [n for n in zf.namelist() if n.startswith("revisor_dokumenter/")]
            self.assertEqual(len(names), 1)
            self.assertEqual(zf.read(names[0]), b"%PDF v2")
        # Skabelon gemmes direkte i arkivet
        r = self.call("post", "/api/firm/templates/opdragsbrev-opstilling/archive", self.bog,
                      {"client": self.co.slug, "kind": "opdragsbrev", "engagement": str(self.eng.id)})
        self.assertEqual(r.status_code, 201, r.content)
        self.assertTrue(r.json()["data"]["document"]["filename"].endswith(".docx"))
        self.assertEqual(ClientDocument.objects.filter(client=self.co).count(), 3)
