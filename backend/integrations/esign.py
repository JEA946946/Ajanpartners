"""Underskrift med MitID (Erhverv) af forretningsbetingelser og databehandleraftale.

Slås til med ``TERMS_SIGNATURE_METHOD=mitid`` (default ``click`` = afkrydsning i
programmet). Udbyderen vælges med ``ESIGN_PROVIDER``:
  mock     – testversion: "underskriften" gennemføres straks (default)
  penneo   – Penneo (stub; kræver aftale og API-nøgle)
  criipto  – Criipto Signatures (stub; kræver aftale, client id og secret)

Interface: ``send_for_signature(title, documents, signer_email, signer_name, return_url)``
→ {"reference", "url"}; ``status(reference)`` → "pending" | "signed" | "rejected";
``fetch_signed_pdf(reference)`` → bytes (det underskrevne dokument med MitID-bevis).
"""

import secrets

from .base import AgreementRequired, select, setting

_MOCK = {}


class ESignProvider:
    name = "base"

    def send_for_signature(self, title, documents, signer_email, signer_name, return_url):  # pragma: no cover
        raise NotImplementedError

    def status(self, reference):  # pragma: no cover
        raise NotImplementedError

    def fetch_signed_pdf(self, reference):  # pragma: no cover
        raise NotImplementedError


class MockESign(ESignProvider):
    """Testversion uden rigtig MitID: returnerer straks til programmet som "underskrevet"."""

    name = "mock"

    def send_for_signature(self, title, documents, signer_email, signer_name, return_url):
        ref = "mock-" + secrets.token_hex(8)
        _MOCK[ref] = "signed"
        sep = "&" if "?" in return_url else "?"
        return {"reference": ref, "url": f"{return_url}{sep}signed={ref}"}

    def status(self, reference):
        return _MOCK.get(reference, "signed" if reference.startswith("mock-") else "pending")

    def fetch_signed_pdf(self, reference):
        return b"%PDF-1.4\n% Testunderskrift (ingen rigtig MitID)\n"


class PenneoESign(ESignProvider):
    name = "penneo"

    def send_for_signature(self, *a, **kw):
        raise AgreementRequired("Penneo", "en aftale med Penneo og API-nøgle/secret (PENNEO_KEY, PENNEO_SECRET). "
                                "Implementér oprettelse af en signeringssag med MitID Erhverv.")

    status = fetch_signed_pdf = send_for_signature


class CriiptoESign(ESignProvider):
    name = "criipto"

    def send_for_signature(self, *a, **kw):
        raise AgreementRequired("Criipto Signatures", "en aftale med Criipto og client id/secret "
                                "(CRIIPTO_CLIENT_ID, CRIIPTO_CLIENT_SECRET). Implementér createSignatureOrder "
                                "med MitID-evidence provider.")

    status = fetch_signed_pdf = send_for_signature


PROVIDERS = {"mock": MockESign, "penneo": PenneoESign, "criipto": CriiptoESign}


def signature_method():
    return (setting("TERMS_SIGNATURE_METHOD", "click") or "click").lower()


def provider():
    return select("ESIGN_PROVIDER", PROVIDERS)
