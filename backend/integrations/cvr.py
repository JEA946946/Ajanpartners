"""CVR-opslag (Det Centrale Virksomhedsregister).

Adaptere (vælges med ``CVR_PROVIDER``):
  mock    – deterministiske testdata (default)
  cvrapi  – cvrapi.dk (gratis med begrænset antal opslag; token via ``CVRAPI_TOKEN``)
  virk    – Erhvervsstyrelsens System-til-system-adgang (stub, kræver aftale)

Resultatet er altid et ``CvrCompany`` med de felter, admin-portalen bruger, når
en kunde oprettes.
"""

import hashlib
import re
from dataclasses import asdict, dataclass, field
from datetime import date, datetime

from .base import AgreementRequired, IntegrationError, select, setting, user_agent

CVR_RE = re.compile(r"^\d{8}$")

# Virksomhedsform fra CVR → ClientCompany.LEGAL_FORMS
LEGAL_FORM_MAP = {
    "anpartsselskab": "aps",
    "aktieselskab": "as",
    "iværksætterselskab": "ivs",
    "enkeltmandsvirksomhed": "enk",
    "interessentskab": "is",
    "personligt ejet mindre virksomhed": "pmv",
    "forening med begrænset ansvar": "fmba",
    "andelsselskab med begrænset ansvar": "fmba",
    "forening": "forening",
    "frivillig forening": "forening",
}


@dataclass
class CvrCompany:
    cvr: str
    name: str
    address: str = ""
    zip_code: str = ""
    city: str = ""
    legal_form_text: str = ""          # fx "Anpartsselskab"
    legal_form: str = "andet"          # kode i ClientCompany.LEGAL_FORMS
    industry_code: str = ""            # DB07, 6 cifre
    industry_text: str = ""
    founded: date | None = None
    fiscal_year_start: str = ""        # "MM-DD", tom hvis ukendt
    fiscal_year_end: str = ""          # "MM-DD"
    email: str = ""
    phone: str = ""
    status: str = ""                   # fx "NORMAL", "OPHØRT"
    source: str = ""
    extra: dict = field(default_factory=dict)

    @property
    def fiscal_year_start_month(self):
        try:
            return int(self.fiscal_year_start.split("-")[0])
        except (ValueError, IndexError):
            return 1

    def as_dict(self):
        d = asdict(self)
        d["founded"] = self.founded.isoformat() if self.founded else None
        d["fiscal_year_start_month"] = self.fiscal_year_start_month
        d.pop("extra", None)
        return d


def normalize_cvr(value):
    cvr = re.sub(r"\D", "", str(value or ""))  # "DK 12 34 56 78" → "12345678"
    if not CVR_RE.match(cvr):
        raise IntegrationError("Et CVR-nummer har 8 cifre.")
    return cvr


def legal_form_code(text):
    return LEGAL_FORM_MAP.get((text or "").strip().lower(), "andet")


class CVRClient:
    """Interface."""

    name = "base"

    def lookup(self, cvr: str) -> CvrCompany:  # pragma: no cover - interface
        raise NotImplementedError


class MockCVRClient(CVRClient):
    """Deterministiske testdata: samme CVR giver altid samme virksomhed."""

    name = "mock"
    KNOWN = {
        "12345678": CvrCompany(
            cvr="12345678", name="Testfirma ApS", address="Testvej 1", zip_code="2100", city="København Ø",
            legal_form_text="Anpartsselskab", legal_form="aps", industry_code="692000",
            industry_text="Bogføring og revision; skatterådgivning", founded=date(2015, 3, 1),
            fiscal_year_start="01-01", fiscal_year_end="12-31", status="NORMAL", source="mock"),
        "87654321": CvrCompany(
            cvr="87654321", name="Leverandør A/S", address="Industrivej 42", zip_code="8000", city="Aarhus C",
            legal_form_text="Aktieselskab", legal_form="as", industry_code="465000",
            industry_text="Engroshandel med it-udstyr", founded=date(1998, 7, 1),
            fiscal_year_start="07-01", fiscal_year_end="06-30", status="NORMAL", source="mock"),
    }
    FORMS = ["Anpartsselskab", "Aktieselskab", "Enkeltmandsvirksomhed", "Interessentskab"]
    CITIES = [("1050", "København K"), ("5000", "Odense C"), ("8000", "Aarhus C"), ("9000", "Aalborg")]

    def lookup(self, cvr):
        cvr = normalize_cvr(cvr)
        if cvr in self.KNOWN:
            return self.KNOWN[cvr]
        if cvr == "00000000":
            raise IntegrationError("CVR-nummeret findes ikke.")
        h = int(hashlib.sha256(cvr.encode()).hexdigest(), 16)
        form = self.FORMS[h % len(self.FORMS)]
        zip_code, city = self.CITIES[(h // 7) % len(self.CITIES)]
        suffix = {"Anpartsselskab": " ApS", "Aktieselskab": " A/S"}.get(form, "")
        return CvrCompany(
            cvr=cvr, name=f"Virksomhed {cvr}{suffix}", address=f"Mockvej {h % 200 + 1}",
            zip_code=zip_code, city=city, legal_form_text=form, legal_form=legal_form_code(form),
            industry_code="620100", industry_text="Computerprogrammering",
            founded=date(2000 + h % 25, h % 12 + 1, 1), fiscal_year_start="01-01", fiscal_year_end="12-31",
            status="NORMAL", source="mock")


class CvrApiClient(CVRClient):
    """cvrapi.dk. Regnskabsår leveres ikke af den gratis tjeneste."""

    name = "cvrapi"
    URL = "https://cvrapi.dk/api"
    TIMEOUT = 10

    def lookup(self, cvr):
        import requests

        cvr = normalize_cvr(cvr)
        params = {"search": cvr, "country": "dk"}
        token = setting("CVRAPI_TOKEN")
        if token:
            params["token"] = token
        try:
            resp = requests.get(self.URL, params=params, timeout=self.TIMEOUT,
                                headers={"User-Agent": user_agent(), "Accept": "application/json"})
        except requests.RequestException as e:
            raise IntegrationError(f"CVR-opslag fejlede: {e}") from e
        if resp.status_code == 404:
            raise IntegrationError("CVR-nummeret findes ikke.")
        if resp.status_code == 429:
            raise IntegrationError("For mange CVR-opslag. Prøv igen senere.")
        if resp.status_code >= 400:
            raise IntegrationError(f"CVR-opslag fejlede (HTTP {resp.status_code}).")
        return self.parse(resp.json())

    @staticmethod
    def parse(data):
        if data.get("error"):
            raise IntegrationError(f"CVR-opslag: {data['error']}")
        form = data.get("companydesc") or ""
        return CvrCompany(
            cvr=str(data.get("vat") or ""), name=data.get("name") or "",
            address=data.get("address") or "", zip_code=str(data.get("zipcode") or ""),
            city=data.get("city") or "", legal_form_text=form, legal_form=legal_form_code(form),
            industry_code=str(data.get("industrycode") or ""), industry_text=data.get("industrydesc") or "",
            founded=_parse_cvrapi_date(data.get("startdate")), email=data.get("email") or "",
            phone=str(data.get("phone") or ""), status="OPHØRT" if data.get("enddate") else "NORMAL",
            source="cvrapi")


def _parse_cvrapi_date(value):
    # cvrapi.dk: "01/03 - 2015"
    if not value:
        return None
    for fmt in ("%d/%m - %Y", "%Y-%m-%d", "%d/%m/%Y"):
        try:
            return datetime.strptime(value.strip(), fmt).date()
        except ValueError:
            continue
    return None


class VirkSystemToSystemClient(CVRClient):
    """Erhvervsstyrelsens CVR System-til-system (Elasticsearch på distribution.virk.dk)."""

    name = "virk"

    def lookup(self, cvr):
        raise AgreementRequired(
            "CVR System-til-system",
            "en aftale med Erhvervsstyrelsen om adgang til CVR-data (System-til-system). Når "
            "brugernavn og adgangskode er udstedt, sættes CVR_VIRK_USER/CVR_VIRK_PASSWORD, og "
            "klienten implementeres mod http://distribution.virk.dk/cvr-permanent/virksomhed/_search "
            "(felterne Vrvirksomhed.virksomhedMetadata.nyesteNavn, nyesteBeliggenhedsadresse, "
            "nyesteHovedbranche, nyesteVirksomhedsform, stiftelsesDato og regnskabsår).")


CLIENTS = {"mock": MockCVRClient, "cvrapi": CvrApiClient, "virk": VirkSystemToSystemClient}


def get_client():
    return select("CVR_PROVIDER", CLIENTS)


def lookup(cvr):
    return get_client().lookup(cvr)
