"""Endpoints for integrationer.

/api/firm/cvr/<cvr>          CVR-opslag til admin-portalen (kun medarbejdere)
/api/v1/bank-feeds/...       kundens bankkoblinger (funktionen bank_feed)
"""

from django.utils import timezone
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response

from core.permissions import IsFirmStaff, RoleWriteAccess

from . import bank_feeds, cvr
from .base import AgreementRequired, IntegrationError
from .models import RENEW_WARNING_DAYS, BankFeedConnection


def _ok(data=None, code=200, message=None):
    body = {"success": True, "data": data if data is not None else {}}
    if message:
        body["message"] = message
    return Response(body, status=code)


def _err(message, code=400, error_code=None):
    body = {"success": False, "message": message}
    if error_code:
        body["code"] = error_code
    return Response(body, status=code)


def _integration_error(e):
    if isinstance(e, AgreementRequired):
        return _err(str(e), 501, "agreement_required")
    return _err(str(e), 502 if "fejlede" in str(e) else 400)


# --- CVR (admin-portalen, public) -----------------------------------------

@api_view(["GET"])
@permission_classes([IsFirmStaff])
def cvr_lookup(request, number):
    try:
        company = cvr.lookup(number)
    except (IntegrationError, AgreementRequired) as e:
        return _integration_error(e)
    return _ok(company.as_dict())


# --- Bankkobling (kunden) ---------------------------------------------------

def _conn_dict(c):
    return {
        "id": str(c.id), "provider": c.provider, "institution_id": c.institution_id,
        "institution_name": c.institution_name, "bank_account_id": str(c.bank_account_id),
        "iban": c.iban, "status": c.status, "status_display": c.get_status_display(),
        "authorization_url": c.authorization_url or None,
        "consent_expires_at": c.consent_expires_at.isoformat() if c.consent_expires_at else None,
        "renewal_due": c.renewal_due, "last_fetched_at": c.last_fetched_at.isoformat() if c.last_fetched_at else None,
        "last_booked_date": c.last_booked_date.isoformat() if c.last_booked_date else None,
        "last_error": c.last_error, "last_result": c.last_result,
    }


def _connections(request):
    return BankFeedConnection.objects.filter(client=request.tenant)


def _get(request, pk):
    return _connections(request).filter(pk=pk).first()


@api_view(["GET"])
@permission_classes([RoleWriteAccess])
def institutions(request):
    from journals.models import Journal

    accounts = [{"id": str(j.account_id), "code": j.account.code, "name": j.account.name or j.name,
                 "journal": j.code, "currency": j.currency}
                for j in Journal.objects.filter(type="bank", account__isnull=False, is_active=True)
                .select_related("account").order_by("code")]
    try:
        return _ok({"provider": bank_feeds.provider_name(), "institutions": bank_feeds.get_client().institutions(),
                    "bank_accounts": accounts})
    except (IntegrationError, AgreementRequired) as e:
        return _integration_error(e)


@api_view(["GET", "POST"])
@permission_classes([RoleWriteAccess])
def connections(request):
    if request.method == "GET":
        return _ok({"connections": [_conn_dict(c) for c in _connections(request)],
                    "renew_warning_days": RENEW_WARNING_DAYS})
    from accounts.models import Account

    data = request.data
    account = Account.objects.filter(id=data.get("bank_account_id")).first() if data.get("bank_account_id") else None
    if account is None:
        return _err("Vælg den bankkonto i kontoplanen, transaktionerne skal bogføres på.")
    institution_id = data.get("institution_id") or ""
    adapter = bank_feeds.get_client()
    try:
        names = {i["id"]: i["name"] for i in adapter.institutions()}
        conn = BankFeedConnection(client=request.tenant, provider=adapter.name, institution_id=institution_id,
                                  institution_name=names.get(institution_id, institution_id),
                                  bank_account_id=account.id, created_by=request.user)
        consent = adapter.connect(institution_id, data.get("redirect_url") or "", str(conn.id))
    except (IntegrationError, AgreementRequired) as e:
        return _integration_error(e)
    _apply_consent(conn, consent, data.get("iban"))
    conn.save()
    return _ok(_conn_dict(conn), 201)


def _apply_consent(conn, consent, iban=None):
    conn.consent_id = consent.consent_id
    if consent.accounts:
        match = next((a for a in consent.accounts if iban and a.iban == iban), consent.accounts[0])
        conn.external_account_id = match.external_id
        conn.iban = match.iban
    if consent.granted:
        conn.grant_consent()
    else:
        conn.status = "pending"
        conn.authorization_url = consent.authorization_url


@api_view(["POST"])
@permission_classes([RoleWriteAccess])
def connection_callback(request, pk):
    """Kunden er sendt tilbage fra banken efter godkendelse."""
    conn = _get(request, pk)
    if conn is None:
        return _err("Bankkoblingen findes ikke.", 404)
    try:
        consent = bank_feeds.get_client(conn.provider).complete(conn.consent_id, dict(request.data))
    except (IntegrationError, AgreementRequired) as e:
        return _integration_error(e)
    _apply_consent(conn, consent, request.data.get("iban"))
    conn.save()
    return _ok(_conn_dict(conn))


@api_view(["POST"])
@permission_classes([RoleWriteAccess])
def connection_renew(request, pk):
    conn = _get(request, pk)
    if conn is None:
        return _err("Bankkoblingen findes ikke.", 404)
    try:
        consent = bank_feeds.get_client(conn.provider).renew(conn)
    except (IntegrationError, AgreementRequired) as e:
        return _integration_error(e)
    _apply_consent(conn, consent)
    conn.last_error = ""
    conn.save()
    return _ok(_conn_dict(conn), message="Samtykket er fornyet." if conn.status == "active" else None)


@api_view(["POST"])
@permission_classes([RoleWriteAccess])
def connection_sync(request, pk):
    conn = _get(request, pk)
    if conn is None:
        return _err("Bankkoblingen findes ikke.", 404)
    try:
        result = bank_feeds.sync_connection(conn)
    except (IntegrationError, AgreementRequired) as e:
        return _integration_error(e)
    conn.refresh_from_db()
    return _ok({"connection": _conn_dict(conn), "result": result})


@api_view(["DELETE"])
@permission_classes([RoleWriteAccess])
def connection_delete(request, pk):
    conn = _get(request, pk)
    if conn is None:
        return _err("Bankkoblingen findes ikke.", 404)
    try:
        bank_feeds.get_client(conn.provider).revoke(conn)
    except AgreementRequired:
        pass  # samtykket kan altid trækkes tilbage hos banken; vi stopper hentningen
    except IntegrationError as e:
        return _integration_error(e)
    conn.status = "revoked"
    conn.consent_expires_at = timezone.now()
    conn.save(update_fields=["status", "consent_expires_at"])
    return _ok(_conn_dict(conn))

