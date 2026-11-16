"""Dokumentskabeloner: branchegrupper, fletning, alle skabelonfiler og endpoints."""

import json
import tempfile
from datetime import date
from pathlib import Path
from unittest import mock

from django.contrib.auth import get_user_model
from django.test import Client, SimpleTestCase, TransactionTestCase, override_settings

from firm import branche, templating
from tenancy.models import ClientCompany, Firm, FirmAuditLog, FirmStaff
from tenancy.services import create_client, ensure_public_tenant

User = get_user_model()
PW = "Test-1234567"
YEAR = {"id": "2025-01-01", "start": date(2025, 1, 1), "end": date(2025, 12, 31), "closed": False}


def _client(form="aps", code="", cls="B", name="Testkunde ApS"):
    return ClientCompany(name=name, cvr="12345678", legal_form=form, industry_code=code, address="Vej 1",
                         zip_code="1000", city="København K", accounting_class=cls, vat_period="quarter")


def _ctx(client=None, **kw):
    return templating.build_context(Firm(name="Ajan Partners", cvr="11223344"), client, None, None,
                                    YEAR if client else None, **kw)


class BrancheTests(SimpleTestCase):
    def test_groups(self):
        self.assertTrue(branche.context("561010")["restauration"])
        self.assertEqual(branche.context("561010")["hvidvask_risiko"], "høj")
        self.assertTrue(branche.context("412000")["igangvaerende_arbejder"])
        self.assertTrue(branche.context("478100")["bilhandel"])
        holding = branche.context("642120")
        self.assertTrue(holding["holding"])
        self.assertFalse(holding["finans"])
        self.assertEqual(branche.context("620100")["hvidvask_risiko"], "normal")

    def test_db07_code_and_unknown(self):
        self.assertEqual(branche.context("")["grupper"], [])
        self.assertEqual(branche.context("999999")["hvidvask_risiko"], "normal")


class RenderTests(SimpleTestCase):
    def _template(self, body, fields=None, name="test"):
        tmp = Path(tempfile.mkdtemp())
        (tmp / "opdrag").mkdir()
        meta = {"title": "Test", "fields": fields or []}
        (tmp / "opdrag" / f"{name}.md").write_text(f"---\n{json.dumps(meta)}\n---\n{body}", encoding="utf-8")
        return mock.patch.object(templating, "ROOT", tmp)

    def test_merge_fields_and_missing(self):
        body = "{{ kunde.navn }} ({{ kunde.cvr }}) – {{ kunde.email }}{% if kunde.email %}JA{% endif %} {{ regnskab.slut }}"
        with self._template(body):
            text, _ = templating.render(templating.get("test"), _ctx(_client()))
        self.assertIn("Testkunde ApS (12345678) – […]", text)
        self.assertNotIn("JA", text)
        self.assertIn("31. december 2025", text)

    def test_industry_and_legal_form_branches(self):
        body = ("{% if branche.restauration %}KASSE{% endif %}{% if kunde.selskabsform_kode == 'as' %}BESTYRELSE{% endif %}"
                " {{ kunde.ledelsesorgan }}")
        with self._template(body):
            t = templating.get("test")
            self.assertIn("KASSE", templating.render(t, _ctx(_client(code="561010")))[0])
            self.assertNotIn("KASSE", templating.render(t, _ctx(_client(code="620100")))[0])
            self.assertIn("BESTYRELSE bestyrelsen og direktionen", templating.render(t, _ctx(_client(form="as")))[0])

    def test_field_defaults_and_values(self):
        fields = [{"name": "aar", "label": "År", "default": "{{ regnskab.aar }}"},
                  {"name": "honorar", "label": "Honorar", "type": "number"},
                  {"name": "bestyrelse", "label": "Bestyrelse", "type": "checkbox"}]
        body = "{{ felt.aar }} / {{ felt.honorar }}{% if felt.bestyrelse %} B{% endif %}"
        with self._template(body, fields):
            t = templating.get("test")
            text, vals = templating.render(t, _ctx(_client()))
            self.assertEqual(text.strip(), "2025 / […]")
            self.assertEqual(vals["aar"], "2025")
            text, _ = templating.render(t, _ctx(_client()), {"honorar": "25.000", "bestyrelse": True, "ukendt": "x"})
            self.assertEqual(text.strip(), "2025 / 25.000 B")

    def test_only_safe_tags(self):
        for body in ("{% load static %}", "{% include 'x.html' %}", "{% debug %}"):
            with self._template(body):
                items, errors = templating.load_all()
                self.assertEqual(items, [])
                self.assertEqual(len(errors), 1)

    def test_amount_format(self):
        self.assertEqual(templating.da_amount(1234567.4), "1.234.567 kr.")
        self.assertEqual(templating.da_amount(-500), "-500 kr.")


class AllTemplatesTests(SimpleTestCase):
    """Hver skabelon i repoet kan indlæses og flettes for forskellige kunder uden fejl."""

    CLIENTS = [
        _client("aps", "561010"), _client("as", "412000", "C", "Byg A/S"), _client("enk", "960210", "A", "Frisør"),
        _client("holding", "642120", name="Holding ApS"), _client("aps", "682040"), _client("is", ""),
        _client("forening", "949900", name="Foreningen"),
    ]

    def test_all_load(self):
        items, errors = templating.load_all()
        self.assertEqual(errors, [], errors)
        self.assertGreater(len(items), 0)
        cats = {c for c, _ in templating.CATEGORIES}
        for t in items:
            self.assertIn(t["category"], cats)
            self.assertIn(t["kind"], templating.KINDS, t["id"])
            for f in t["fields"]:
                self.assertIn("name", f, t["id"])
                self.assertIn(f.get("type", "text"), {"text", "textarea", "number", "date", "select", "checkbox"}, t["id"])
                if f.get("type") == "select":
                    self.assertTrue(f.get("options"), f"{t['id']}: {f['name']} mangler options")

    def test_all_render(self):
        items, _ = templating.load_all()
        for t in items:
            for c in [None, *self.CLIENTS]:
                text, _ = templating.render(t, _ctx(c))
                self.assertNotIn("{{", text, t["id"])
                self.assertNotIn("{%", text, t["id"])
                if c is not None:
                    self.assertNotIn(f"{c.name} {c.get_legal_form_display()}", text, t["id"])


@override_settings(FIRM_MFA_REQUIRED=False)
class TemplateEndpointTests(TransactionTestCase):
    def setUp(self):
        ensure_public_tenant("testserver")
        self.partner = User.objects.create_user("partner@x.dk", "partner@x.dk", PW, first_name="Pia", last_name="Partner")
        FirmStaff.objects.create(user=self.partner, firm=Firm.current(), role="partner")
        self.bogholder = User.objects.create_user("bog@x.dk", "bog@x.dk", PW)
        FirmStaff.objects.create(user=self.bogholder, firm=Firm.current(), role="bogholder")
        self.client_co, _ = create_client(name="Café Alfa ApS", package_code="mini", owner_email="a@a.dk",
                                          created_by=self.partner, cvr="87654321", industry_code="561010")
        self.http = Client()

    def tearDown(self):
        from django.db import connection
        connection.set_schema_to_public()
        with connection.cursor() as cur:
            cur.execute(f'DROP SCHEMA IF EXISTS "{self.client_co.schema_name}" CASCADE')

    def call(self, method, path, user, data=None):
        from rest_framework_simplejwt.tokens import RefreshToken
        return getattr(self.http, method)(path, data=json.dumps(data) if data is not None else None,
                                          content_type="application/json",
                                          HTTP_AUTHORIZATION=f"Bearer {RefreshToken.for_user(user).access_token}")

    def _any_template(self):
        return templating.load_all()[0][0]["id"]

    def test_list_and_render(self):
        r = self.call("get", "/api/firm/templates", self.partner)
        self.assertEqual(r.status_code, 200)
        self.assertTrue(r.json()["data"]["templates"])
        tid = self._any_template()
        r = self.call("post", f"/api/firm/templates/{tid}/render", self.partner, {"client": self.client_co.slug})
        self.assertEqual(r.status_code, 200, r.content)
        d = r.json()["data"]
        self.assertEqual(d["client"]["aml_risk"], "høj")
        self.assertIn("restauration", d["client"]["industry_groups"])
        self.assertTrue(d["years"])
        self.assertEqual(d["client_missing"], ["adresse"])  # CVR og branchekode er udfyldt
        self.assertIn("CVR-nr.", d["firm_missing"]) if not Firm.current().cvr else None
        self.assertFalse(FirmAuditLog.objects.filter(action="template_render").exists())
        self.call("post", f"/api/firm/templates/{tid}/render", self.partner, {"client": self.client_co.slug, "final": True})
        self.assertTrue(FirmAuditLog.objects.filter(action="template_render", client=self.client_co).exists())

    def test_unassigned_bookkeeper_cannot_use_client(self):
        r = self.call("post", f"/api/firm/templates/{self._any_template()}/render", self.bogholder,
                      {"client": self.client_co.slug})
        self.assertEqual(r.status_code, 404)
        r = self.call("post", f"/api/firm/templates/{self._any_template()}/render", self.bogholder, {})
        self.assertEqual(r.status_code, 200)

    def test_docx(self):
        r = self.call("post", f"/api/firm/templates/{self._any_template()}/docx", self.partner,
                      {"client": self.client_co.slug, "text": "# Overskrift\n\n- [ ] punkt\n\n| a | b |\n|---|---|\n| 1 | 2 |\n"})
        self.assertEqual(r.status_code, 200)
        self.assertTrue(r["Content-Type"].startswith("application/vnd.openxmlformats"))
        self.assertEqual(r.content[:2], b"PK")
        self.assertTrue(FirmAuditLog.objects.filter(action="template_download").exists())

    def test_unknown_template_and_client_user(self):
        self.assertEqual(self.call("post", "/api/firm/templates/findes-ikke/render", self.partner, {}).status_code, 404)
        owner = User.objects.get(email="a@a.dk")
        self.assertEqual(self.call("get", "/api/firm/templates", owner).status_code, 403)


@override_settings(FIRM_MFA_REQUIRED=False)
class FirmSettingsTests(TransactionTestCase):
    def setUp(self):
        ensure_public_tenant("testserver")
        self.partner = User.objects.create_user("p2@x.dk", "p2@x.dk", PW)
        FirmStaff.objects.create(user=self.partner, firm=Firm.current(), role="partner")
        self.http = Client()

    def put(self, data):
        from rest_framework_simplejwt.tokens import RefreshToken
        return self.http.put("/api/firm/settings", data=json.dumps(data), content_type="application/json",
                             HTTP_AUTHORIZATION=f"Bearer {RefreshToken.for_user(self.partner).access_token}")

    def test_address_fields_saved_and_merged(self):
        r = self.put({"name": "Ajan Partners", "cvr": "DK 46 92 25 14", "address": " Vej 1 ", "zip_code": "1000",
                      "city": "København K", "website": "www.ajanpartners.dk"})
        self.assertEqual(r.status_code, 200, r.content)
        f = r.json()["data"]["firm"]
        self.assertEqual((f["cvr"], f["address"], f["zip_code"], f["city"]), ("46922514", "Vej 1", "1000", "København K"))
        ctx = templating.build_context(Firm.current())
        self.assertEqual(ctx["firma"]["adresse"], "Vej 1, 1000 København K")
        self.assertEqual(ctx["firma"]["hjemmeside"], "www.ajanpartners.dk")

    def test_validation(self):
        self.assertEqual(self.put({"cvr": "123"}).status_code, 400)
        self.assertEqual(self.put({"email": "ikke-en-mail"}).status_code, 400)
        self.assertEqual(self.put({"name": " "}).status_code, 400)


class IndustryRiskTests(SimpleTestCase):
    def test_every_risk_group_has_reasons_and_prefixes(self):
        for row in branche.overview():
            self.assertIn(row["level"], {"høj", "forhøjet", "normal"})
            self.assertTrue(row["reasons"], row["group"])
            self.assertTrue(row["prefixes"], row["group"])

    def test_highest_level_wins_and_reasons_follow(self):
        ctx = branche.context("561010")  # restauration
        self.assertEqual(ctx["hvidvask_risiko"], "høj")
        self.assertTrue(any("kontant" in r.lower() for r in ctx["hvidvask_grunde"]))
        self.assertEqual(branche.context("473000")["hvidvask_risiko"], "forhøjet")  # tankstation: kontantintensiv
        self.assertEqual(branche.context("")["hvidvask_risiko"], "normal")


class OfficialRiskIndustryTests(SimpleTestCase):
    def test_official_list(self):
        from integrations.industry import describe
        self.assertEqual(len(branche.RISIKOBRANCHER), 15)
        for c in branche.RISIKOBRANCHER:
            self.assertIsNotNone(describe(c), c)
        self.assertTrue(branche.context("494100")["risikobranche"])   # vejgodstransport
        self.assertTrue(branche.context("561010")["risikobranche"])   # DB07 → DB25 561110
        self.assertFalse(branche.context("478100")["risikobranche"])  # bilhandel er ikke med
