"""Momsangivelse system-til-system hos Skattestyrelsen.

Adaptere (``SKAT_VAT_PROVIDER``):
  mock – validerer angivelsen og returnerer en kvittering (default)
  skat – Skattestyrelsens system-til-system-snitflade for moms (stub, kræver aftale)

Uden aftale vises angivelsen med feltværdierne, så den kan tastes i TastSelv/
E-tast (det gør moms-modulet).

``vat_return`` er en dict:
  cvr, period_start, period_end (ISO-datoer),
  output_vat (salgsmoms), input_vat (købsmoms),
  eu_goods_purchase_vat, foreign_services_purchase_vat (moms af varekøb i EU / ydelseskøb i udlandet),
  rubrik_a_goods, rubrik_a_services, rubrik_b_goods, rubrik_b_services, rubrik_c,
  electricity_tax, gas_tax, coal_tax, oil_tax, water_tax, co2_tax (afgifter til godtgørelse)
Ukendte nøgler ignoreres; manglende beløb er 0.
"""

import hashlib
import json
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation

from django.utils import timezone

from .base import AgreementRequired, IntegrationError, select

AMOUNT_FIELDS = (
    "output_vat", "input_vat", "eu_goods_purchase_vat", "foreign_services_purchase_vat",
    "rubrik_a_goods", "rubrik_a_services", "rubrik_b_goods", "rubrik_b_services", "rubrik_c",
    "electricity_tax", "gas_tax", "coal_tax", "oil_tax", "water_tax", "co2_tax",
)
TAX_REFUND_FIELDS = ("electricity_tax", "gas_tax", "coal_tax", "oil_tax", "water_tax", "co2_tax")


@dataclass
class VatSubmission:
    status: str            # accepted | rejected | pending
    receipt_id: str
    payable: Decimal       # positiv: skal betales; negativ: tilgodehavende
    message: str = ""
    submitted_at: object = None

    def as_dict(self):
        return {"status": self.status, "receipt_id": self.receipt_id, "payable": str(self.payable),
                "message": self.message,
                "submitted_at": self.submitted_at.isoformat() if self.submitted_at else None}


def normalize(vat_return):
    if not vat_return.get("cvr") or len(str(vat_return["cvr"])) != 8:
        raise IntegrationError("Momsangivelsen mangler et gyldigt CVR-nummer.")
    if not vat_return.get("period_start") or not vat_return.get("period_end"):
        raise IntegrationError("Momsangivelsen mangler perioden.")
    out = {"cvr": str(vat_return["cvr"]), "period_start": str(vat_return["period_start"]),
           "period_end": str(vat_return["period_end"])}
    for f in AMOUNT_FIELDS:
        try:
            out[f] = Decimal(str(vat_return.get(f) or 0)).quantize(Decimal("1"))  # hele kroner
        except InvalidOperation:
            raise IntegrationError(f"Ugyldigt beløb i {f}.") from None
    return out


def payable(v):
    """Momstilsvar: salgsmoms + moms af køb i udlandet − købsmoms − afgifter."""
    return (v["output_vat"] + v["eu_goods_purchase_vat"] + v["foreign_services_purchase_vat"]
            - v["input_vat"] - sum(v[f] for f in TAX_REFUND_FIELDS))


class VatClient:
    name = "base"

    def submit(self, vat_return) -> VatSubmission:  # pragma: no cover - interface
        raise NotImplementedError


class MockVatClient(VatClient):
    name = "mock"

    def submit(self, vat_return):
        v = normalize(vat_return)
        if v["period_end"] < v["period_start"]:
            return VatSubmission("rejected", "", Decimal("0"), "Perioden slutter før den starter.")
        digest = hashlib.sha256(json.dumps(v, default=str, sort_keys=True).encode()).hexdigest()[:16]
        return VatSubmission("accepted", f"MOCK-{digest.upper()}", payable(v),
                             "Testkvittering – intet er sendt til Skattestyrelsen.", timezone.now())


class SkatSystemToSystemClient(VatClient):
    name = "skat"

    def submit(self, vat_return):
        normalize(vat_return)
        raise AgreementRequired(
            "Moms system-til-system",
            "godkendelse som systemleverandør hos Skattestyrelsen til momsangivelse system-til-system "
            "(ModtagMomsangivelseForeloebig/ModtagMomsangivelse), et OCES3-virksomhedscertifikat "
            "(MitID Erhverv) til signering, og at kunden har givet systemet fuldmagt i TastSelv Erhverv. "
            "Indtil da: indtast felterne i TastSelv Erhverv.")


CLIENTS = {"mock": MockVatClient, "skat": SkatSystemToSystemClient}


def get_client():
    return select("SKAT_VAT_PROVIDER", CLIENTS)


def submit(vat_return):
    return get_client().submit(vat_return)
