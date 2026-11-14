"""Branchekoder (DB25): opslag, søgning, DB07-omregning, oversigt og endpoint."""

from django.contrib.auth import get_user_model
from django.test import SimpleTestCase, TestCase, override_settings
from rest_framework.test import APIClient

from integrations import industry
from tenancy.models import Firm, FirmStaff


class IndustryTests(SimpleTestCase):
    def test_lookup_and_path(self):
        d = industry.describe("69.20.00")
        self.assertEqual(d["code"], "692000")
        self.assertEqual(d["title"], "Bogføring og revision; skatterådgivning")
        self.assertEqual(d["path"][0]["display"], "N")

    def test_search_by_word_code_and_description(self):
        self.assertEqual(industry.search("frisør")[0]["code"], "962100")
        self.assertTrue(all(r["code"].startswith("692") for r in industry.search("69.2")))
        # Ord, der kun står i beskrivelsen, findes også (med et uddrag som forklaring).
        hits = industry.search("lønbogholderi")
        self.assertIn("692000", [h["code"] for h in hits])

    def test_db07_is_converted(self):
        code, converted = industry.normalize_code("620100")  # DB07 computerprogrammering
        self.assertTrue(converted)
        self.assertEqual(code, "621000")
        self.assertEqual(industry.normalize_code("999999"), (None, False))

    def test_tree_has_all_sections(self):
        t = industry.tree()
        self.assertEqual(len(t["sections"]), 22)
        self.assertEqual(sum(len(g["codes"]) for s in t["sections"] for g in s["groups"]), 738)


@override_settings(FIRM_MFA_REQUIRED=False)
class IndustryEndpointTests(TestCase):
    def test_endpoint_requires_staff(self):
        api = APIClient()
        user = get_user_model().objects.create_user("x@x.dk", "x@x.dk", "Rimelig-lang-kode-77")
        api.force_authenticate(user)
        self.assertEqual(api.get("/api/firm/industry-codes", {"q": "frisør"}).status_code, 403)
        FirmStaff.objects.create(user=user, firm=Firm.current(), role="bogholder")
        r = api.get("/api/firm/industry-codes", {"q": "frisør"})
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json()["data"]["results"][0]["display"], "96.21.00")
        self.assertEqual(api.get("/api/firm/industry-codes", {"code": "1"}).status_code, 404)
