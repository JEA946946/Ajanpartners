"""Open banking (PSD2/AIS): automatisk hentning af banktransaktioner.

Interface (``BankFeedClient``):
  institutions()                         – banker, der kan kobles på
  connect(institution_id, redirect_url, reference) → Consent
  complete(consent_id, params)           – efter kundens godkendelse i banken → Consent med konti
  fetch_transactions(account, since)     → [FeedTransaction] (kun bogførte transaktioner)
  renew(account)                         → Consent (samtykke fornyes hver 180. dag)
  revoke(account)

Adaptere (``BANK_FEED_PROVIDER``):
  mock           – testbank med deterministiske transaktioner (default)
  aiia           – Mastercard Open Banking (Aiia), stub
  tink           – Tink, stub
  enablebanking  – Enable Banking, stub

Transaktionerne lægges i kundens bøger med bankimportens egen kode i
``journals`` (``bank_statement_confirm``): samme dublet-kontrol, samme
låste-perioder-kontrol og samme parkering på "bank – til afstemning", som når
kunden selv uploader et kontoudtog. Transaktions-id'et fra banken bruges som
reference, så en transaktion aldrig importeres to gange.
"""

import hashlib
from dataclasses import dataclass, field
from datetime import date, timedelta
from decimal import Decimal

from django.utils import timezone

from .base import AgreementRequired, IntegrationError, select, setting

CONSENT_DAYS = 180


@dataclass
class FeedAccount:
    external_id: str
    iban: str = ""
    name: str = ""
    currency: str = "DKK"


@dataclass
class Consent:
    consent_id: str
    authorization_url: str = ""          # tom: samtykket er givet (mock)
    accounts: list = field(default_factory=list)
    granted: bool = False


@dataclass
class FeedTransaction:
    transaction_id: str
    booking_date: date
    amount: Decimal                      # positiv: indbetaling, negativ: udbetaling
    description: str = ""
    currency: str = "DKK"
    counterparty: str = ""

    def as_bank_line(self):
        """Dict i det format, journals' bankimport bruger (debit = ud, credit = ind)."""
        amount = Decimal(str(self.amount)).quantize(Decimal("0.01"))
        text = self.description or self.counterparty or "Banktransaktion"
        return {
            "date": self.booking_date.isoformat(),
            "description": text[:500],
            "reference": self.transaction_id[:200],
            "debit": str(-amount if amount < 0 else Decimal("0")),
            "credit": str(amount if amount > 0 else Decimal("0")),
            "account_id": None,
        }


class BankFeedClient:
    name = "base"

    def institutions(self, country="DK"):  # pragma: no cover - interface
        raise NotImplementedError

    def connect(self, institution_id, redirect_url, reference):  # pragma: no cover
        raise NotImplementedError

    def complete(self, consent_id, params=None):  # pragma: no cover
        raise NotImplementedError

    def fetch_transactions(self, account, since):  # pragma: no cover
        raise NotImplementedError

    def renew(self, account):  # pragma: no cover
        raise NotImplementedError

    def revoke(self, account):  # pragma: no cover
        raise NotImplementedError


class MockBankFeedClient(BankFeedClient):
    """Testbank. Samtykket gives straks, og hver hverdag har 0–2 transaktioner,
    der kun afhænger af konto og dato (samme kald giver altid samme resultat)."""

    name = "mock"
    INSTITUTIONS = [
        {"id": "MOCK_DANSKE", "name": "Testbank (Danske Bank-format)", "country": "DK"},
        {"id": "MOCK_NORDEA", "name": "Testbank (Nordea-format)", "country": "DK"},
    ]
    TEXTS = [("Dankort-køb Netto", -1), ("Overførsel fra kunde", 1), ("Husleje", -1),
             ("MobilePay indbetaling", 1), ("Gebyr", -1)]

    def institutions(self, country="DK"):
        return [i for i in self.INSTITUTIONS if i["country"] == country]

    def connect(self, institution_id, redirect_url, reference):
        if institution_id not in {i["id"] for i in self.INSTITUTIONS}:
            raise IntegrationError("Ukendt bank.")
        consent_id = "MOCKCONSENT-" + hashlib.sha256(f"{institution_id}:{reference}".encode()).hexdigest()[:12]
        return self.complete(consent_id)

    def complete(self, consent_id, params=None):
        acct = "MOCKACCT-" + consent_id[-8:]
        return Consent(consent_id=consent_id, granted=True, accounts=[
            FeedAccount(external_id=acct, iban="DK5000400440116243", name="Erhvervskonto")])

    def fetch_transactions(self, account, since):
        today = timezone.localdate()
        out = []
        day = since
        while day <= today:
            if day.weekday() < 5:
                seed = int(hashlib.sha256(f"{account.external_account_id}:{day}".encode()).hexdigest(), 16)
                for n in range(seed % 3):
                    text, sign = self.TEXTS[(seed >> (n + 3)) % len(self.TEXTS)]
                    amount = Decimal((seed >> (8 * n + 5)) % 500000) / 100 + Decimal("1")
                    out.append(FeedTransaction(
                        transaction_id=f"MOCK-{account.external_account_id}-{day:%Y%m%d}-{n}",
                        booking_date=day, amount=amount * sign, description=text))
            day += timedelta(days=1)
        return out

    def renew(self, account):
        return Consent(consent_id=account.consent_id, granted=True)

    def revoke(self, account):
        return None


class _AggregatorStub(BankFeedClient):
    service = ""
    requirement = ""

    def _no(self, *args, **kwargs):
        raise AgreementRequired(self.service, self.requirement)

    institutions = connect = complete = fetch_transactions = renew = revoke = _no


class AiiaClient(_AggregatorStub):
    name = "aiia"
    service = "Mastercard Open Banking (Aiia)"
    requirement = ("en kundeaftale med Mastercard Open Banking (tidl. Aiia) om kontoinformation (AIS), "
                   "client_id/client_secret (BANK_FEED_CLIENT_ID/BANK_FEED_CLIENT_SECRET) og en godkendt "
                   "redirect-URL. Aiia er licenseret kontooplysningstjeneste; vi optræder som deres agent.")


class TinkClient(_AggregatorStub):
    name = "tink"
    service = "Tink"
    requirement = ("en aftale med Tink (Visa) om Account Check/Transactions, client_id/client_secret og "
                   "redirect-URL i Tink Console. Tink står som licenseret AIS-udbyder over for bankerne.")


class EnableBankingClient(_AggregatorStub):
    name = "enablebanking"
    service = "Enable Banking"
    requirement = ("en aftale med Enable Banking, en registreret applikation (application id + RSA-nøgle "
                   "til JWT-signering, BANK_FEED_PRIVATE_KEY) og redirect-URL.")


CLIENTS = {"mock": MockBankFeedClient, "aiia": AiiaClient, "tink": TinkClient,
           "enablebanking": EnableBankingClient}


def get_client(provider=None):
    if provider:
        try:
            return CLIENTS[provider]()
        except KeyError:
            raise IntegrationError(f"Ukendt bankkoblingsudbyder: {provider}") from None
    return select("BANK_FEED_PROVIDER", CLIENTS)


def provider_name():
    return (setting("BANK_FEED_PROVIDER", "mock") or "mock").lower()


# ---------------------------------------------------------------------------
# Import i kundens bøger (genbruger journals' bankimport)
# ---------------------------------------------------------------------------

class _SystemAccess:
    """Adgang for et systemjob, der skriver banklinjer i kundens bøger."""

    def __init__(self, client):
        self.client = client
        self.role = "accountant"
        self.via = "system"
        self.staff = None
        self.grant = None
        self.is_firm = False
        self.can_write = True

    def has_feature(self, feature):
        return True


def _system_user():
    from django.contrib.auth import get_user_model

    User = get_user_model()
    user, created = User.objects.get_or_create(
        username="system:bankkobling", defaults={"first_name": "Bankkobling", "is_active": False})
    if created:
        user.set_unusable_password()
        user.save(update_fields=["password"])
    return user


def import_bank_lines(client, bank_account_id, lines, user=None):
    """Læg banklinjer i kundens bøger via journals.views.bank_statement_confirm.

    Skal kaldes i kundens skema. Returnerer {"created": n, "skipped": n} eller
    rejser IntegrationError med bankimportens fejlbesked.
    """
    if not lines:
        return {"created": 0, "skipped": 0}
    from rest_framework.test import APIRequestFactory, force_authenticate

    from journals.views import bank_statement_confirm
    from tenancy.context import current_access

    user = user if (user is not None and getattr(user, "pk", None)) else _system_user()
    request = APIRequestFactory().post(
        "/api/v1/bank-statements/confirm",
        {"bank_account_id": str(bank_account_id), "transactions": lines,
         "filename": "bankkobling"}, format="json")
    force_authenticate(request, user=user)
    access = _SystemAccess(client)
    request.client_access = access
    request.tenant = client
    token = current_access.set(access)
    try:
        response = bank_statement_confirm(request)
    finally:
        current_access.reset(token)
    body = getattr(response, "data", {}) or {}
    if response.status_code >= 400 or not body.get("success", False):
        raise IntegrationError(body.get("message") or f"Bankimporten fejlede (HTTP {response.status_code}).")
    data = body.get("data") or {}
    return {"created": int(data.get("count", data.get("created", 0)) or 0),
            "skipped": int(data.get("skipped", 0) or 0)}


def sync_connection(conn, since=None, adapter=None):
    """Hent og importér nye transaktioner for én kobling. Kører selv i kundens skema."""
    from django_tenants.utils import schema_context

    now = timezone.now()
    if conn.status == "revoked":
        return {"skipped_reason": "revoked"}
    if conn.consent_expired:
        conn.status = "expired"
        conn.last_error = "Samtykket er udløbet. Kunden skal forny det i banken."
        conn.save(update_fields=["status", "last_error"])
        return {"skipped_reason": "consent_expired"}
    if conn.status != "active":
        return {"skipped_reason": conn.status}
    adapter = adapter or get_client(conn.provider)
    if since is None:
        # 3 dages overlap: banker bogfører med forsinkelse; dubletter fanges på referencen.
        since = (conn.last_booked_date - timedelta(days=3)) if conn.last_booked_date \
            else timezone.localdate() - timedelta(days=90)
    try:
        txns = adapter.fetch_transactions(conn, since)
        lines = [t.as_bank_line() for t in txns]
        with schema_context(conn.client.schema_name):
            result = import_bank_lines(conn.client, conn.bank_account_id, lines, conn.created_by)
    except (IntegrationError, AgreementRequired) as e:
        conn.last_error = str(e)
        conn.last_fetched_at = now
        conn.last_result = {"error": str(e)}
        conn.save(update_fields=["last_error", "last_fetched_at", "last_result"])
        raise
    result["fetched"] = len(lines)
    result["since"] = since.isoformat()
    conn.last_fetched_at = now
    if txns:
        conn.last_booked_date = max(t.booking_date for t in txns)
    conn.last_error = ""
    conn.last_result = result
    conn.save(update_fields=["last_fetched_at", "last_booked_date", "last_error", "last_result"])
    return result
