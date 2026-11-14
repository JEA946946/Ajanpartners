"""Pure-logic tests (no DB) — run with: python manage.py test core.tests_pure

The app's models are managed=False, so DB-backed tests can't create tables. These cover
the pure money/numbering/escaping helpers where the real bugs lived.
"""

from decimal import Decimal

from django.test import SimpleTestCase

from core.csv_utils import csv_safe
from core.permissions import get_role
from journals.numbering import next_number


class _FakeModel:
    """Stands in for a Django model exposing values_list(field, flat=True)."""

    def __init__(self, values):
        self._values = values

    class _Objects:
        def __init__(self, values):
            self._values = values

        def values_list(self, field, flat=True):
            return self._values

    @property
    def objects(self):
        return self._Objects(self._values)


class NumberingTests(SimpleTestCase):
    def test_empty_starts_at_one(self):
        self.assertEqual(next_number(_FakeModel([]), "x", "JE"), "JE-0001")

    def test_increments_max(self):
        self.assertEqual(next_number(_FakeModel(["JE-0001", "JE-0007", "JE-0003"]), "x", "JE"), "JE-0008")

    def test_numeric_not_lexical_after_9999(self):
        # The old lexical bug: "JE-9999" > "JE-10000" as strings → stuck. Numeric wins.
        self.assertEqual(next_number(_FakeModel(["JE-9999", "JE-10000"]), "x", "JE"), "JE-10001")

    def test_ignores_garbage(self):
        self.assertEqual(next_number(_FakeModel(["", None, "weird", "JE-0002"]), "x", "JE"), "JE-0003")


class CsvSafeTests(SimpleTestCase):
    def test_neutralises_formula_prefixes(self):
        for bad in ("=SUM(A1)", "+1", "-1", "@cmd", "\ttab", "\rcr"):
            self.assertTrue(csv_safe(bad).startswith("'"), bad)

    def test_leaves_plain_text(self):
        self.assertEqual(csv_safe("Acme Ltd"), "Acme Ltd")
        self.assertEqual(csv_safe("2026-01-01"), "2026-01-01")

    def test_handles_non_strings(self):
        self.assertEqual(csv_safe(None), "")
        self.assertEqual(csv_safe(Decimal("12.50")), "12.50")
        self.assertEqual(csv_safe(42), "42")


class BankDescNormalizeTests(SimpleTestCase):
    """Normalization used by bank-import duplicate detection (pure string logic)."""

    def _norm(self, value):
        from journals.views import _normalize_bank_desc
        return _normalize_bank_desc(value)

    def test_casefolds(self):
        self.assertEqual(self._norm("VIREMENT EMIS"), "virement emis")

    def test_collapses_whitespace(self):
        self.assertEqual(self._norm("  Virement \t EMIS \n de   X  "), "virement emis de x")

    def test_equal_after_normalization(self):
        self.assertEqual(self._norm("PAIEMENT  PRLV\tMAROC TELECOM"),
                         self._norm("paiement prlv maroc telecom"))

    def test_empty_and_none(self):
        self.assertEqual(self._norm(""), "")
        self.assertEqual(self._norm(None), "")
        self.assertEqual(self._norm("   "), "")

    def test_non_string_input(self):
        self.assertEqual(self._norm(123), "123")


class ClosedPeriodDateCoercionTests(SimpleTestCase):
    """_to_date is the pure half of closed_period_error (the FY lookup is DB-bound)."""

    def test_parses_iso_string(self):
        from datetime import date
        from journals.periods import _to_date
        self.assertEqual(_to_date("2025-03-31"), date(2025, 3, 31))
        self.assertEqual(_to_date("2025-03-31T10:00:00"), date(2025, 3, 31))

    def test_passes_through_date_and_datetime(self):
        from datetime import date, datetime
        from journals.periods import _to_date
        self.assertEqual(_to_date(date(2024, 1, 1)), date(2024, 1, 1))
        self.assertEqual(_to_date(datetime(2024, 1, 1, 12, 30)), date(2024, 1, 1))

    def test_invalid_returns_none(self):
        from journals.periods import _to_date
        self.assertIsNone(_to_date(None))
        self.assertIsNone(_to_date("not-a-date"))
        self.assertIsNone(_to_date(""))


class RoleTests(SimpleTestCase):
    class _User:
        def __init__(self, role=None, staff=False, superuser=False, auth=True):
            self.is_authenticated = auth
            self.is_staff = staff
            self.is_superuser = superuser
            if role is not None:
                self.role = type("R", (), {"role": role})()

    def test_anonymous_has_no_role(self):
        self.assertIsNone(get_role(self._User(auth=False)))

    def test_staff_is_admin(self):
        self.assertEqual(get_role(self._User(staff=True)), "admin")

    def test_missing_role_defaults_viewer(self):
        u = self._User()  # no .role attribute
        self.assertEqual(get_role(u), "viewer")

    def test_explicit_role(self):
        self.assertEqual(get_role(self._User(role="accountant")), "accountant")


class LoginLookupTests(SimpleTestCase):
    """_find_login_user: username first, then a unique email."""

    def _lookup(self, identifier, by_username=None, by_email=()):
        from unittest import mock

        from accounts import views

        def fake_filter(**kw):
            qs = mock.MagicMock()
            if "username__iexact" in kw:
                qs.first.return_value = by_username
            else:
                qs.__getitem__.return_value = list(by_email)[:2]
            return qs

        with mock.patch.object(views.User.objects, "filter", side_effect=fake_filter):
            return views._find_login_user(identifier)

    def test_username_wins(self):
        self.assertEqual(self._lookup("Chaimae", by_username="u1", by_email=["u2"]), "u1")

    def test_unique_email_matches(self):
        self.assertEqual(self._lookup(" accounting@vmmorocco.com ", by_email=["u2"]), "u2")

    def test_shared_email_does_not_match(self):
        self.assertIsNone(self._lookup("team@vmmorocco.com", by_email=["u2", "u3"]))

    def test_unknown_returns_none(self):
        self.assertIsNone(self._lookup("nobody"))
        self.assertIsNone(self._lookup("nobody@vmmorocco.com"))


class MarginTvaTests(SimpleTestCase):
    def test_guide_example(self):
        # Law/guide_fiscal_complet_agence.pdf §6A: margin TTC 2,000 → TVA 333.33
        from accounts import chart

        self.assertEqual(chart.margin_tva(Decimal("2000")), Decimal("333.33"))
        self.assertEqual(chart.margin_tva(Decimal("134000")), Decimal("22333.33"))
