"""Integrationer: CVR, valuta, moms til Skat og bankkobling. Ingen netværkskald.

Kør: manage.py test integrations
"""

from datetime import date, timedelta
from decimal import Decimal
from io import StringIO
from unittest import mock

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import SimpleTestCase, TestCase, override_settings
from django.utils import timezone
from django_tenants.test.cases import TenantTestCase
from rest_framework.test import APIRequestFactory, force_authenticate

from . import bank_feeds, currency, cvr, skat_vat
from .base import AgreementRequired, IntegrationError

User = get_user_model()

NB_XML = b"""<?xml version="1.0" encoding="utf-8"?>
<exchangerates type="Valutakurser" author="Danmarks Nationalbank" refcur="DKK" refamt="1">
  <dailyrates id="2026-11-13">
    <currency code="EUR" desc="Euro" rate="746,12" />
    <currency code="USD" desc="Amerikanske dollar" rate="642,50" />
  </dailyrates>
  <dailyrates id="2026-11-12">
    <currency code="EUR" desc="Euro" rate="746,00" />
  </dailyrates>
</exchangerates>"""


@override_settings(CVR_PROVIDER="mock")  # local.py bruger rigtige opslag; testene må ikke gå på nettet
class CvrTests(SimpleTestCase):
    def test_mock_known_and_deterministic(self):
        c = cvr.MockCVRClient().lookup("DK 12 34 56 78")
        self.assertEqual(c.name, "Testfirma ApS")
        self.assertEqual(c.legal_form, "aps")
        self.assertEqual(c.industry_code, "692000")
        self.assertEqual(c.fiscal_year_start_month, 1)
        # Ukendte numre giver en fejl – testtilstanden må aldrig opfinde et firma.
        with self.assertRaises(IntegrationError) as cm:
            cvr.MockCVRClient().lookup("39815206")
        self.assertIn("testtilstand", str(cm.exception))

    def test_invalid_cvr(self):
        with self.assertRaises(IntegrationError):
            cvr.lookup("1234")

    @override_settings(CVR_PROVIDER="")
    def test_default_is_mock(self):
        self.assertIsInstance(cvr.get_client(), cvr.MockCVRClient)

    @override_settings(CVR_PROVIDER="virk", CVR_VIRK_USER="", CVR_VIRK_PASSWORD="")
    def test_virk_without_credentials_explains_agreement(self):
        with self.assertRaises(AgreementRequired) as cm:
            cvr.lookup("12345678")
        self.assertIn("Erhvervsstyrelsen", str(cm.exception))

    @override_settings(CVR_PROVIDER="apicvr")
    def test_apicvr_parses_live_format(self):
        resp = mock.Mock(status_code=200)
        resp.json.return_value = {
            "vat": 39815206, "name": "Stork Line ApS", "address": "Smedeholm 10", "zipcode": 2730,
            "city": "Herlev", "protected": True, "phone": None, "email": None, "startdate": "2018-08-28",
            "enddate": None, "industrycode": 464420, "industrydesc": "Engroshandel med rengøringsmidler",
            "companydesc": "Anpartsselskab", "bankrupt": False, "status": "NORMAL"}
        with mock.patch("requests.get", return_value=resp) as get:
            c = cvr.lookup("39815206")
        self.assertEqual(get.call_args.args[0], "https://apicvr.dk/api/v1/39815206")
        self.assertEqual((c.name, c.address, c.zip_code, c.city), ("Stork Line ApS", "Smedeholm 10", "2730", "Herlev"))
        self.assertEqual((c.legal_form, c.industry_code, c.founded), ("aps", "464420", date(2018, 8, 28)))
        self.assertTrue(c.as_dict()["advertising_protected"])

    @override_settings(CVR_PROVIDER="apicvr,cvrapi")
    def test_chain_falls_back_on_network_error(self):
        import requests
        ok = mock.Mock(status_code=200)
        ok.json.return_value = {"vat": 39815206, "name": "Fra cvrapi ApS", "companydesc": "Anpartsselskab"}
        with mock.patch("requests.get", side_effect=[requests.ConnectionError("nede"), ok]):
            self.assertEqual(cvr.lookup("39815206").name, "Fra cvrapi ApS")

    @override_settings(CVR_PROVIDER="cvrapi")
    def test_cvrapi_quota_is_explained(self):
        resp = mock.Mock(status_code=403)
        resp.json.return_value = {"error": "QUOTA_EXCEEDED", "message": "Your quota has been exceeded."}
        with mock.patch("requests.get", return_value=resp):
            with self.assertRaises(cvr.QuotaExceeded) as cm:
                cvr.lookup("39815206")
        self.assertIn("kvote", str(cm.exception))

    @override_settings(CVR_PROVIDER="virk,cvrapi", CVR_VIRK_USER="", CVR_VIRK_PASSWORD="")
    def test_chain_falls_back_when_virk_has_no_agreement(self):
        resp = mock.Mock(status_code=200)
        resp.json.return_value = {"vat": 39815206, "name": "Rigtigt Firma ApS", "companydesc": "Anpartsselskab"}
        with mock.patch("requests.get", return_value=resp):
            self.assertEqual(cvr.lookup("39815206").name, "Rigtigt Firma ApS")

    @override_settings(CVR_PROVIDER="virk", CVR_VIRK_USER="u", CVR_VIRK_PASSWORD="p")
    def test_virk_parses_elasticsearch_hit(self):
        hit = {"cvrNummer": 39815206,
               "virksomhedMetadata": {
                   "nyesteNavn": {"navn": "Eksempel ApS"},
                   "nyesteBeliggenhedsadresse": {"vejnavn": "Strandvejen", "husnummerFra": 12, "bogstavFra": "B",
                                                 "etage": "2", "sidedoer": "tv", "postnummer": 2900,
                                                 "postdistrikt": "Hellerup"},
                   "nyesteHovedbranche": {"branchekode": "692000", "branchetekst": "Bogføring og revision"},
                   "nyesteVirksomhedsform": {"kortBeskrivelse": "APS", "langBeskrivelse": "Anpartsselskab"},
                   "stiftelsesDato": "2018-08-01", "sammensatStatus": "Normal"},
               "attributter": [
                   {"type": "REGNSKABSÅR_START", "vaerdier": [{"vaerdi": "--07-01", "periode": {"gyldigTil": None}}]},
                   {"type": "REGNSKABSÅR_SLUT", "vaerdier": [{"vaerdi": "--06-30", "periode": {"gyldigTil": None}}]}],
               "elektroniskPost": [{"kontaktoplysning": "info@eksempel.dk"}]}
        resp = mock.Mock(status_code=200)
        resp.json.return_value = {"hits": {"hits": [{"_source": {"Vrvirksomhed": hit}}]}}
        with mock.patch("requests.post", return_value=resp) as post:
            c = cvr.lookup("39815206")
        self.assertEqual(post.call_args.kwargs["auth"], ("u", "p"))
        self.assertEqual((c.name, c.address, c.zip_code, c.city),
                         ("Eksempel ApS", "Strandvejen 12B, 2, tv", "2900", "Hellerup"))
        self.assertEqual((c.legal_form, c.industry_code, c.fiscal_year_start_month), ("aps", "692000", 7))
        self.assertEqual(c.founded, date(2018, 8, 1))
        self.assertEqual(c.email, "info@eksempel.dk")

    @override_settings(CVR_PROVIDER="cvrapi")
    def test_cvrapi_parses_and_sends_generic_user_agent(self):
        resp = mock.Mock(status_code=200)
        resp.json.return_value = {
            "vat": 87654321, "name": "Leverandør A/S", "address": "Industrivej 42", "zipcode": "8000",
            "city": "Aarhus C", "companydesc": "Aktieselskab", "industrycode": 465000,
            "industrydesc": "Engros", "startdate": "01/07 - 1998", "enddate": None}
        with mock.patch("requests.get", return_value=resp) as get:
            c = cvr.lookup("87654321")
        self.assertEqual((c.legal_form, c.founded, c.zip_code), ("as", date(1998, 7, 1), "8000"))
        ua = get.call_args.kwargs["headers"]["User-Agent"]
        self.assertNotIn("@", ua)
        self.assertEqual(ua, "bogforingssystem-integration/1.0")


@override_settings(CVR_PROVIDER="mock")
class CvrEndpointTests(TestCase):
    @override_settings(FIRM_MFA_REQUIRED=False)  # MFA testes i tenancy; her kun rollen
    def test_firm_staff_only(self):
        from tenancy.models import Firm, FirmStaff

        from .views import cvr_lookup

        staff = User.objects.create_user("staff@x.dk", "staff@x.dk", "x")
        FirmStaff.objects.create(user=staff, firm=Firm.current(), role="bogholder")
        outsider = User.objects.create_user("kunde@x.dk", "kunde@x.dk", "x")
        rf = APIRequestFactory()
        req = rf.get("/api/firm/cvr/12345678")
        force_authenticate(req, staff)
        r = cvr_lookup(req, number="12345678")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.data["data"]["name"], "Testfirma ApS")
        req = rf.get("/api/firm/cvr/12345678")
        force_authenticate(req, outsider)
        self.assertEqual(cvr_lookup(req, number="12345678").status_code, 403)


class CurrencyTests(SimpleTestCase):
    def test_parse_nationalbank_xml(self):
        rates = currency.parse_nationalbank_xml(NB_XML)
        self.assertEqual(rates[date(2026, 11, 13)]["EUR"], Decimal("7.461200"))

    def test_weekend_uses_previous_banking_day(self):
        rates = currency.parse_nationalbank_xml(NB_XML)
        value, day = currency.pick(rates, "EUR", date(2026, 11, 15))  # søndag
        self.assertEqual((value, day), (Decimal("7.461200"), date(2026, 11, 13)))
        with self.assertRaises(IntegrationError):
            currency.pick(rates, "EUR", date(2026, 11, 1))

    def test_rate_mock_and_dkk(self):
        self.assertEqual(currency.rate("DKK", date(2026, 1, 2)), Decimal("1"))
        self.assertEqual(currency.rate("eur", date(2026, 1, 2)), Decimal("7.4600"))
        self.assertEqual(currency.convert("100", "EUR", date(2026, 1, 2)), Decimal("746.00"))

    @override_settings(CURRENCY_PROVIDER="nationalbank")
    def test_nationalbank_client(self):
        from django.core.cache import cache

        cache.clear()
        resp = mock.Mock(content=NB_XML)
        resp.raise_for_status.return_value = None
        with mock.patch("requests.get", return_value=resp):
            self.assertEqual(currency.rate("USD", date(2026, 11, 13)), Decimal("6.425000"))


class SkatVatTests(SimpleTestCase):
    RETURN = {"cvr": "12345678", "period_start": "2026-07-01", "period_end": "2026-09-30",
              "output_vat": "25000", "input_vat": "10000", "eu_goods_purchase_vat": "500",
              "electricity_tax": "200"}

    def test_mock_submit(self):
        r = skat_vat.submit(self.RETURN)
        self.assertEqual(r.status, "accepted")
        self.assertTrue(r.receipt_id.startswith("MOCK-"))
        self.assertEqual(r.payable, Decimal("15300"))
        self.assertEqual(skat_vat.submit(self.RETURN).receipt_id, r.receipt_id)

    def test_validation(self):
        with self.assertRaises(IntegrationError):
            skat_vat.submit({**self.RETURN, "cvr": "1"})

    @override_settings(SKAT_VAT_PROVIDER="skat")
    def test_stub(self):
        with self.assertRaises(AgreementRequired) as cm:
            skat_vat.submit(self.RETURN)
        self.assertIn("Skattestyrelsen", str(cm.exception))


class BankFeedTests(TenantTestCase):
    @classmethod
    def get_test_schema_name(cls):
        return "c_bankfeedtest"

    @classmethod
    def setup_tenant(cls, tenant):
        from tenancy.models import Firm, Package
        from tenancy.services import seed_packages
        seed_packages()
        tenant.firm = Firm.current()
        tenant.package = Package.objects.get(code="standard")
        tenant.name = "Bankfeed ApS"
        tenant.slug = "bankfeed"

    def setUp(self):
        from accounts import chart
        from accounts.models import Account, AccountType
        from journals.models import Journal

        asset, _ = AccountType.objects.get_or_create(name="Asset", defaults={"normal_balance": "debit"})
        self.bank = Account.objects.create(code="TESTBANK", name="Bank", account_type=asset, currency="DKK")
        Account.objects.get_or_create(code=chart.SUSPENSE, defaults={
            "name": "Bank til afstemning", "account_type": asset, "currency": "DKK"})
        Journal.objects.create(code="TB", name="Testbank", type="bank", account=self.bank, currency="DKK")
        self.user = User.objects.create_user("bog@x.dk", "bog@x.dk", "x", first_name="Bo")

    def _connection(self, **kw):
        from .models import BankFeedConnection

        conn = BankFeedConnection(client=self.tenant, provider="mock", institution_id="MOCK_DANSKE",
                                  bank_account_id=self.bank.id, external_account_id="MOCKACCT-1",
                                  created_by=self.user, **kw)
        conn.grant_consent()
        conn.save()
        return conn

    def test_feed_line_format(self):
        t = bank_feeds.FeedTransaction("T1", date(2026, 1, 5), Decimal("-120.50"), "Netto")
        line = t.as_bank_line()
        self.assertEqual((line["debit"], line["credit"], line["reference"]), ("120.50", "0", "T1"))

    def test_sync_imports_via_journals_and_is_idempotent(self):
        from journals.models import JournalEntry, JournalEntryLine

        conn = self._connection()
        since = timezone.localdate() - timedelta(days=20)
        expected = len(bank_feeds.MockBankFeedClient().fetch_transactions(conn, since))
        self.assertGreater(expected, 0)
        first = bank_feeds.sync_connection(conn, since=since)
        self.assertEqual(first["created"], expected)
        self.assertEqual(JournalEntry.objects.filter(source="bank").count(), expected)
        # Hver linje er balanceret mod banken
        self.assertEqual(JournalEntryLine.objects.filter(account=self.bank).count(), expected)
        second = bank_feeds.sync_connection(conn, since=since)
        self.assertEqual((second["created"], second["skipped"]), (0, expected))
        conn.refresh_from_db()
        self.assertIsNotNone(conn.last_booked_date)

    def test_expired_consent_is_skipped(self):
        conn = self._connection()
        conn.consent_expires_at = timezone.now() - timedelta(days=1)
        conn.save()
        self.assertEqual(bank_feeds.sync_connection(conn)["skipped_reason"], "consent_expired")
        conn.refresh_from_db()
        self.assertEqual(conn.status, "expired")

    def test_consent_is_180_days(self):
        conn = self._connection()
        self.assertEqual((conn.consent_expires_at - conn.consent_granted_at).days, 180)

    def test_command(self):
        self._connection()
        out = StringIO()
        call_command("fetch_bank_feeds", "--client", self.tenant.slug,
                     "--since", (timezone.localdate() - timedelta(days=10)).isoformat(), stdout=out)
        self.assertIn("Bankkobling: 1 koblinger", out.getvalue())

    def test_stub_providers_explain_agreement(self):
        for name in ("aiia", "tink", "enablebanking"):
            with self.assertRaises(AgreementRequired):
                bank_feeds.get_client(name).institutions()

    def test_reminders_once_per_consent_period(self):
        from firm.models import FirmTask

        from .management.commands.bank_feed_reminders import create_reminders

        conn = self._connection(iban="DK5000400440116243")
        self.assertEqual(create_reminders(), [])  # 180 dage tilbage: ingen påmindelse
        conn.consent_expires_at = timezone.now() + timedelta(days=5)
        conn.save()
        self.assertEqual(len(create_reminders()), 1)
        self.assertEqual(create_reminders(), [])  # højst én pr. periode
        task = FirmTask.objects.get(client=self.tenant)
        self.assertEqual((task.kind, task.visible_to_client), ("opgave", True))
        self.assertIn("Forny samtykket", task.title)
        # fornyet samtykke → ny periode → ny påmindelse, når den nærmer sig udløb
        conn.grant_consent()
        conn.consent_expires_at = timezone.now() + timedelta(days=2)
        conn.save()
        self.assertEqual(len(create_reminders()), 1)
        out = StringIO()
        call_command("bank_feed_reminders", "--dry-run", stdout=out)
        self.assertIn("0 påmindelser", out.getvalue())

