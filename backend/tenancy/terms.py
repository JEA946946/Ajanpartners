"""Accept af forretningsbetingelser og databehandleraftale."""

from django.utils import timezone

from .models import TermsAcceptance, TermsDocument


def required_documents():
    return [d for d in (TermsDocument.current(k) for k in TermsDocument.REQUIRED_KINDS) if d]


def missing_for(user, client):
    """De gældende versioner, som brugeren endnu ikke har accepteret for kunden."""
    accepted = set(TermsAcceptance.objects.filter(user=user, client=client).values_list("sha256", flat=True))
    return [d for d in required_documents() if d.sha256 not in accepted]


def accept(user, client, documents, ip=None, user_agent="", method="click", signature_reference=""):
    rows = [TermsAcceptance.objects.create(
        user=user, client=client, document=d, sha256=d.sha256, method=method, ip_address=ip,
        user_agent=(user_agent or "")[:300], signature_reference=signature_reference) for d in documents]
    if client.agreement_accepted_on is None:
        client.agreement_accepted_on = timezone.now()
        client.save(update_fields=["agreement_accepted_on"])
    return rows
