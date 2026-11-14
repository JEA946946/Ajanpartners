"""Adapter til et Peppol/NemHandel access point.

Interface (``AccessPoint``):
  send(outgoing)            → SendResult (udbyderens besked-id, status)
  lookup(scheme, endpoint)  → True/False: er modtageren registreret i Peppol/NemHandel (SMP)
  fetch_incoming()          → [ReceivedDocument] (til polling; push-webhooks kalder services.receive)

Adaptere (``EINVOICE_ACCESS_POINT``):
  mock      – "sender" ved at gemme dokumentet og lægge en kopi i kundens egen
              indbakke, så modtagelse kan testes (default)
  nemhandel – NemHandel (Digitaliseringsstyrelsen) via eDelivery/NemHandel-klient, stub
  storecove – Storecove REST API, stub
  pagero    – Pagero Online, stub
"""

import hashlib
from dataclasses import dataclass

from integrations.base import AgreementRequired, select


@dataclass
class SendResult:
    message_id: str
    status: str = "sent"      # sent | delivered | failed
    error: str = ""


@dataclass
class ReceivedDocument:
    xml: str
    message_id: str = ""


class AccessPoint:
    name = "base"

    def send(self, outgoing) -> SendResult:  # pragma: no cover - interface
        raise NotImplementedError

    def lookup(self, scheme, endpoint) -> bool:  # pragma: no cover
        raise NotImplementedError

    def fetch_incoming(self):  # pragma: no cover
        raise NotImplementedError


class MockAccessPoint(AccessPoint):
    name = "mock"

    def send(self, outgoing):
        from . import services

        message_id = "MOCK-" + hashlib.sha256(outgoing.xml.encode()).hexdigest()[:20].upper()
        # Kopi i indbakken, så hele kæden send → modtag → regning kan testes.
        services.receive(outgoing.xml, access_point=self.name, access_point_id=message_id)
        return SendResult(message_id=message_id, status="delivered")

    def lookup(self, scheme, endpoint):
        return bool(scheme and endpoint)

    def fetch_incoming(self):
        return []


class _Stub(AccessPoint):
    service = ""
    requirement = ""

    def _no(self, *args, **kwargs):
        raise AgreementRequired(self.service, self.requirement)

    send = lookup = fetch_incoming = _no


class NemHandelAccessPoint(_Stub):
    name = "nemhandel"
    service = "NemHandel"
    requirement = ("tilslutning til NemHandel hos Digitaliseringsstyrelsen: registrering af kundernes "
                   "CVR/GLN i NemHandelsregistret (SMP), et OCES3-virksomhedscertifikat (MitID Erhverv) "
                   "til eDelivery/AS4 og enten egen AS4-gateway eller en certificeret access point-udbyder.")


class StorecoveAccessPoint(_Stub):
    name = "storecove"
    service = "Storecove"
    requirement = ("en aftale med Storecove (certificeret Peppol access point), API-nøgle "
                   "(EINVOICE_API_KEY) og oprettelse af hver kunde som 'legal entity' med Peppol-id 0184:<CVR>; "
                   "webhook til modtagelse sættes op mod /api/v1/einvoice/inbox.")


class PageroAccessPoint(_Stub):
    name = "pagero"
    service = "Pagero"
    requirement = ("en aftale med Pagero (Peppol og NemHandel), OAuth-klient (client id/secret) og "
                   "registrering af kunderne som afsendere/modtagere i Pagero Online.")


ACCESS_POINTS = {"mock": MockAccessPoint, "nemhandel": NemHandelAccessPoint,
                 "storecove": StorecoveAccessPoint, "pagero": PageroAccessPoint}


def get_access_point():
    return select("EINVOICE_ACCESS_POINT", ACCESS_POINTS)
