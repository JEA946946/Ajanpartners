"""Tid og fakturering: rettigheder, satser, låsning, fakturaudkast i husets egen bogføring og aconto."""

import json
from datetime import date
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import Client, TransactionTestCase, override_settings
from django_tenants.utils import schema_context

from firm.models import Engagement, FeeInstallment, TimeEntry
from tenancy.models import Firm, FirmStaff, StaffAssignment
from tenancy.services import create_client, ensure_public_tenant

User = get_user_model()
PW = "Test-1234567"


@override_settings(FIRM_MFA_REQUIRED=False)
class TimeBillingTests(TransactionTestCase):
    def setUp(self):
        ensure_public_tenant("testserver")
        self.firm = Firm.current()
        self.firm.cvr, self.firm.name, self.firm.address = "46922514", "Ajan & Partners", "Revisorvej 1"
        self.firm.zip_code, self.firm.city, self.firm.default_hourly_rate = "2100", "København Ø", Decimal("800")
        self.firm.save()
        self.partner = User.objects.create_user("p@x.dk", "p@x.dk", PW)
        FirmStaff.objects.create(user=self.partner, firm=self.firm, role="partner", hourly_rate=Decimal("1200"))
        self.bog = User.objects.create_user("b@x.dk", "b@x.dk", PW)
        bs = FirmStaff.objects.create(user=self.bog, firm=self.firm, role="bogholder")
        self.co, _ = create_client(name="Kunde ApS", package_code="mini", created_by=self.partner, cvr="87654321",
                                   address="Vej 1", zip_code="8000", city="Aarhus C")
        self.other, _ = create_client(name="Anden ApS", package_code="mini", created_by=self.partner, cvr="11223344")
        StaffAssignment.objects.create(staff=bs, client=self.co)
        self.eng = Engagement.objects.create(client=self.co, kind="bogfoering", title="Bogføring")
        self.schemas = [self.co.schema_name, self.other.schema_name]
        self.http = Client()

    def tearDown(self):
        from django.db import connection
        connection.set_schema_to_public()
        own = Firm.current().own_client
        if own:
            self.schemas.append(own.schema_name)
        with connection.cursor() as cur:
            for s in self.schemas:
                cur.execute(f'DROP SCHEMA IF EXISTS "{s}" CASCADE')

    def call(self, method, path, user, data=None):
        from rest_framework_simplejwt.tokens import RefreshToken
        kw = {"HTTP_AUTHORIZATION": f"Bearer {RefreshToken.for_user(user).access_token}"}
        if data is not None:
            kw.update(data=json.dumps(data), content_type="application/json")
        return getattr(self.http, method)(path, **kw)

    def log(self, user, minutes=90, client=None, engagement=None, **extra):
        r = self.call("post", "/api/firm/time", user, {
            "client": (client or self.co).slug, "engagement": str(engagement.id) if engagement else None,
            "date": "2026-11-02", "minutes": minutes, **extra})
        self.assertEqual(r.status_code, 201, r.content)
        return r.json()["data"]["entry"]

    def test_rates_access_and_visibility(self):
        e = self.log(self.bog, engagement=self.eng)
        self.assertEqual(e["rate"], "800.00")      # husets standardsats
        self.assertEqual(e["value"], "1200.00")    # 1,5 t × 800
        self.assertEqual(self.log(self.partner)["rate"], "1200.00")  # medarbejderens sats
        # Bogholderen kan ikke registrere på en kunde, hun ikke er tildelt
        r = self.call("post", "/api/firm/time", self.bog, {"client": self.other.slug, "date": "2026-11-02", "minutes": 30})
        self.assertEqual(r.status_code, 400)
        # Ser kun egne registreringer; kan ikke ændre timeprisen
        r = self.call("get", "/api/firm/time?user=all", self.bog)
        self.assertEqual(len(r.json()["data"]["entries"]), 1)
        r = self.call("put", f"/api/firm/time/{e['id']}", self.bog, {"rate": "5000"})
        self.assertEqual(r.json()["data"]["entry"]["rate"], "800.00")
        # Honoraraftalens sats går forud
        self.assertEqual(self.call("put", f"/api/firm/engagements/{self.eng.id}/fee", self.bog,
                                   {"hourly_rate": "950"}).status_code, 403)
        self.call("put", f"/api/firm/engagements/{self.eng.id}/fee", self.partner, {"hourly_rate": "950"})
        self.assertEqual(self.log(self.bog, engagement=self.eng)["rate"], "950.00")
        # Fakturering og rapporter kun for partnere
        self.assertEqual(self.call("get", "/api/firm/billing", self.bog).status_code, 403)
        self.assertEqual(self.call("get", "/api/firm/time/report", self.bog).status_code, 403)

    def test_draft_in_own_books_locks_and_releases(self):
        from sales.models import Invoice
        e1 = self.log(self.bog, engagement=self.eng)
        e2 = self.log(self.partner, minutes=60, engagement=self.eng)
        r = self.call("post", f"/api/firm/billing/clients/{self.co.slug}/draft", self.partner, {"entries": [e1["id"]]})
        self.assertEqual(r.status_code, 400)  # husets bogføring er ikke valgt
        r = self.call("post", "/api/firm/billing/own-client", self.partner, {"create": True})
        self.assertEqual(r.status_code, 200, r.content)
        own = Firm.current().own_client
        self.assertEqual(own.cvr, "46922514")
        # Intern tid på husets egen bogføring er ikke fakturerbar
        self.assertFalse(self.log(self.bog, client=own)["billable"])

        r = self.call("get", "/api/firm/billing", self.partner)
        row = next(c for c in r.json()["data"]["clients"] if c["client"] == self.co.slug)
        self.assertEqual(row["total"], "2400.00")  # 1,5 × 800 + 1 × 1200

        r = self.call("post", f"/api/firm/billing/clients/{self.co.slug}/draft", self.partner,
                      {"entries": [e1["id"], e2["id"]], "date": "2026-11-17"})
        self.assertEqual(r.status_code, 201, r.content)
        inv = r.json()["data"]["invoice"]
        self.assertEqual(inv["subtotal"], "2400.00")
        self.assertEqual(inv["total"], "3000.00")  # + 25 % moms (S01)
        with schema_context(own.schema_name):
            i = Invoice.objects.get(pk=inv["id"])
            self.assertEqual(i.status, "draft")
            self.assertEqual(i.customer.tax_id, "87654321")
            self.assertEqual([l.is_text for l in i.lines.all()], [True, False, False])
        # Låst, og kan ikke faktureres igen
        self.assertEqual(self.call("delete", f"/api/firm/time/{e1['id']}", self.bog).status_code, 409)
        r = self.call("post", f"/api/firm/billing/clients/{self.co.slug}/draft", self.partner, {"entries": [e1["id"]]})
        self.assertEqual(r.status_code, 409)
        # Slettes udkastet i husets bøger, frigives timerne
        with schema_context(own.schema_name):
            Invoice.objects.filter(pk=inv["id"]).delete()
        self.call("get", "/api/firm/billing", self.partner)
        self.assertIsNone(TimeEntry.objects.get(pk=e1["id"]).invoice_id)

    def test_fixed_price_and_aconto(self):
        self.call("post", "/api/firm/billing/own-client", self.partner, {"create": True})
        fast = Engagement.objects.create(client=self.co, kind="opstilling", title="Årsrapport")
        self.call("put", f"/api/firm/engagements/{fast.id}/fee", self.partner, {"kind": "fast", "fixed_amount": "15000"})
        r = self.call("post", f"/api/firm/engagements/{fast.id}/installments", self.partner,
                      {"due_on": "2026-11-01", "amount": "15000"})
        self.assertEqual(r.status_code, 201, r.content)
        self.log(self.bog, engagement=fast)  # indeholdt i fast pris – faktureres ikke som tid
        r = self.call("get", f"/api/firm/billing/clients/{self.co.slug}", self.partner).json()["data"]
        self.assertEqual(r["entries"], [])
        self.assertEqual(len(r["installments"]), 1)

        # Aconto: rate faktureres først, modregnes når tiden faktureres
        self.call("put", f"/api/firm/engagements/{self.eng.id}/fee", self.partner, {"kind": "aconto"})
        self.call("post", f"/api/firm/engagements/{self.eng.id}/installments", self.partner,
                  {"due_on": "2026-10-01", "amount": "1000"})
        a = FeeInstallment.objects.get(engagement=self.eng)
        r = self.call("post", f"/api/firm/billing/clients/{self.co.slug}/draft", self.partner, {"installments": [str(a.id)]})
        self.assertEqual(r.json()["data"]["invoice"]["subtotal"], "1000.00")
        e = self.log(self.bog, minutes=180, engagement=self.eng)  # 3 × 800 = 2400
        r = self.call("post", f"/api/firm/billing/clients/{self.co.slug}/draft", self.partner, {"entries": [e["id"]]})
        self.assertEqual(r.json()["data"]["invoice"]["subtotal"], "1400.00")  # 2400 − 1000 aconto
        a.refresh_from_db()
        self.assertIsNotNone(a.offset_invoice_id)

    def test_report(self):
        self.log(self.bog, engagement=self.eng)
        self.log(self.bog, minutes=30, billable=False)
        self.eng.budget_hours = Decimal("10")
        self.eng.save()
        r = self.call("get", "/api/firm/time/report?from=2026-11-01&to=2026-11-30", self.partner).json()["data"]
        s = next(x for x in r["staff"] if x["user_id"] == self.bog.id)
        self.assertEqual(s["hours"], "2.00")
        self.assertEqual(s["billable_pct"], "75.0")
        eng = next(x for x in r["engagements"] if x["id"] == str(self.eng.id))
        self.assertEqual(eng["used_hours"], "1.50")
        self.assertEqual(date.fromisoformat(r["from"]), date(2026, 11, 1))
