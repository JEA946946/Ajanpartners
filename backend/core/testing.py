"""Fælles testbase for bogføringen: én testkunde (eget skema) med standardkontoplan.

    class MinTest(LedgerTestCase):
        def test_x(self):
            r = self.post("/api/v1/journal-entries", {...})

Kaldene går gennem middleware'en med X-Client og en JWT for en
administrator hos kunden. Efter hvert kald sættes forbindelsen tilbage til
kundens skema (middleware'en slutter i public).
"""

from datetime import date
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.db import connection
from django_tenants.test.cases import TenantTestCase
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

D = Decimal


class LedgerTestCase(TenantTestCase):
    template = "standard"
    vat_period = "quarter"
    package = "pro"

    @classmethod
    def get_test_schema_name(cls):
        return "test_ledger"

    @classmethod
    def get_test_tenant_domain(cls):
        return "ledger.test.com"

    @classmethod
    def setup_tenant(cls, tenant):
        from tenancy.models import Firm, Package
        from tenancy.services import seed_packages
        seed_packages()
        tenant.firm = Firm.current()
        tenant.package = Package.objects.get(code=cls.package)
        tenant.slug = "testkunde"
        tenant.name = "Testkunde ApS"
        tenant.cvr = "12345678"
        tenant.vat_period = cls.vat_period
        tenant.chart_template = cls.template
        tenant.status = "active"

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        from accounts.management.commands.seed_accounts import seed_chart
        from core.models import CompanySettings
        seed_chart(cls.template)
        CompanySettings.objects.create(company_name="Testkunde ApS", address="Testvej 1, 2100 København Ø",
                                       tax_id="12345678", country="Danmark", currency="DKK")

    def setUp(self):
        from tenancy.models import ClientMembership
        connection.set_schema_to_public()
        self.user = get_user_model().objects.create_user("bogholder@test.dk", "bogholder@test.dk", "x")
        ClientMembership.objects.create(user=self.user, client=self.tenant, role="admin")
        from tenancy.terms import accept, required_documents
        from tenancy.terms_drafts import seed_terms
        seed_terms()
        accept(self.user, self.tenant, required_documents())
        connection.set_tenant(self.tenant)
        self.api = APIClient()
        self.api.credentials(HTTP_AUTHORIZATION=f"Bearer {RefreshToken.for_user(self.user).access_token}",
                             HTTP_X_CLIENT=self.tenant.slug)

    def _call(self, method, path, data=None):
        try:
            return getattr(self.api, method)(path, data, format="json")
        finally:
            connection.set_tenant(self.tenant)

    def get(self, path, params=None):
        try:
            return self.api.get(path, params or {})
        finally:
            connection.set_tenant(self.tenant)

    def post(self, path, data=None):
        return self._call("post", path, data or {})

    def put(self, path, data=None):
        return self._call("put", path, data or {})

    def delete(self, path):
        return self._call("delete", path)

    # ─── Byggeklodser ───
    def acc(self, code):
        from accounts.models import Account
        return Account.objects.get(code=code)

    def tax(self, code):
        from core.models import TaxCode
        return TaxCode.objects.get(code=code)

    def entry(self, lines, d=date(2026, 1, 15), journal=None, source="manual", posted=True, **kw):
        """Postering med linjer [(konto, debet, kredit, ekstra-felter?)]."""
        from journals.journal_for import journal_by_code
        from journals.models import JournalEntry, JournalEntryLine
        from journals.numbering import next_je_number
        je = JournalEntry.objects.create(entry_number=next_je_number(), date=d, source=source, is_posted=posted,
                                         description="test", journal=journal_by_code(journal) if journal else None,
                                         **kw)
        for line in lines:
            code, dr, cr, *extra = line
            JournalEntryLine.objects.create(journal_entry=je, account=self.acc(code), debit=D(dr), credit=D(cr),
                                            **(extra[0] if extra else {}))
        return je

    def balances(self, entry):
        return {(l.account.code, l.vat_code): (l.debit, l.credit) for l in entry.lines.select_related("account")}


def balanced(entry):
    lines = list(entry.lines.all())
    return sum(x.debit for x in lines) == sum(x.credit for x in lines)
