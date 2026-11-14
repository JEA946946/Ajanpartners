"""CVR-opslag (Det Centrale Virksomhedsregister).

Adaptere (vælges med ``CVR_PROVIDER``):
  mock    – deterministiske testdata (default)
  cvrapi  – cvrapi.dk (gratis med begrænset antal opslag; token via ``CVRAPI_TOKEN``)
  virk    – Erhvervsstyrelsens CVR System-til-system (gratis; kræver brugernavn/adgangskode)

Flere kan angives i rækkefølge: ``CVR_PROVIDER=virk,cvrapi``.

Resultatet er altid et ``CvrCompany`` med de felter, admin-portalen bruger, når
en kunde oprettes.
"""

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
    industry_code: str = ""            # DB25 (fra 2025), 6 cifre
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


class QuotaExceeded(IntegrationError):
    """Udbyderen afviser flere opslag lige nu (prøv næste udbyder i kæden)."""


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
    def lookup(self, cvr):
        cvr = normalize_cvr(cvr)
        if cvr in self.KNOWN:
            return self.KNOWN[cvr]
        # Opfind aldrig en virksomhed: et forkert firma, der ser rigtigt ud, er værre end ingen.
        raise IntegrationError(
            "CVR-opslag kører i testtilstand og kender kun testnumrene 12345678 og 87654321. "
            "Udfyld oplysningerne manuelt, eller slå rigtigt opslag til (CVR_PROVIDER=virk eller cvrapi).")


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
        try:
            error = (resp.json() or {}).get("error", "")
        except ValueError:
            error = ""
        if resp.status_code == 429 or error == "QUOTA_EXCEEDED":
            raise QuotaExceeded("cvrapi.dk: den gratis kvote er brugt op for denne internetforbindelse. "
                                "Prøv igen i morgen, brug en CVRAPI_TOKEN, eller slå CVR_PROVIDER=virk til.")
        if error == "NOT_FOUND":
            raise IntegrationError("CVR-nummeret findes ikke.")
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
    """Erhvervsstyrelsens CVR System-til-system (Elasticsearch på distribution.virk.dk).

    Adgangen er gratis, men kræver brugernavn og adgangskode fra Erhvervsstyrelsen
    (ansøg via virk.dk: "Adgang til CVR-data – System-til-system"). Sættes i
    CVR_VIRK_USER og CVR_VIRK_PASSWORD.
    """

    name = "virk"
    URL = "http://distribution.virk.dk/cvr-permanent/virksomhed/_search"
    TIMEOUT = 15

    def lookup(self, cvr):
        import requests

        cvr = normalize_cvr(cvr)
        user, password = setting("CVR_VIRK_USER"), setting("CVR_VIRK_PASSWORD")
        if not user or not password:
            raise AgreementRequired(
                "CVR System-til-system",
                "brugernavn og adgangskode fra Erhvervsstyrelsen (gratis; ansøg på virk.dk under "
                "'Adgang til CVR-data – System-til-system'). Sæt CVR_VIRK_USER og CVR_VIRK_PASSWORD.")
        body = {"_source": ["Vrvirksomhed"], "size": 1,
                "query": {"term": {"Vrvirksomhed.cvrNummer": int(cvr)}}}
        try:
            resp = requests.post(self.URL, json=body, auth=(user, password), timeout=self.TIMEOUT,
                                 headers={"User-Agent": user_agent()})
        except requests.RequestException as e:
            raise IntegrationError(f"CVR-opslag fejlede: {e}") from e
        if resp.status_code in (401, 403):
            raise IntegrationError("Erhvervsstyrelsen afviste CVR-brugernavn eller adgangskode.")
        if resp.status_code == 429:
            raise QuotaExceeded("Erhvervsstyrelsen: for mange CVR-opslag lige nu. Prøv igen om lidt.")
        if resp.status_code >= 400:
            raise IntegrationError(f"CVR-opslag fejlede (HTTP {resp.status_code}).")
        hits = (resp.json().get("hits") or {}).get("hits") or []
        if not hits:
            raise IntegrationError("CVR-nummeret findes ikke.")
        return self.parse(hits[0]["_source"]["Vrvirksomhed"])

    @staticmethod
    def parse(v):
        meta = v.get("virksomhedMetadata") or {}
        adr = meta.get("nyesteBeliggenhedsadresse") or {}
        street = " ".join(str(x) for x in (adr.get("vejnavn"), adr.get("husnummerFra")) if x)
        if adr.get("bogstavFra"):
            street += str(adr["bogstavFra"])
        if adr.get("husnummerTil"):
            street += f"-{adr['husnummerTil']}"
        floor = ", ".join(str(x) for x in (adr.get("etage"), adr.get("sidedoer")) if x)
        if floor:
            street += f", {floor}"
        if adr.get("conavn"):
            street = f"c/o {adr['conavn']}, {street}"
        branche = meta.get("nyesteHovedbranche") or {}
        form = meta.get("nyesteVirksomhedsform") or {}
        form_text = form.get("langBeskrivelse") or form.get("kortBeskrivelse") or ""

        def attr(name):
            for a in v.get("attributter") or []:
                if a.get("type") == name:
                    vals = [x for x in a.get("vaerdier") or [] if not (x.get("periode") or {}).get("gyldigTil")]
                    if vals:
                        return vals[-1].get("vaerdi") or ""
            return ""

        start = attr("REGNSKABSÅR_START").lstrip("-")  # "--01-01" → "01-01"
        end = attr("REGNSKABSÅR_SLUT").lstrip("-")
        emails = v.get("elektroniskPost") or []
        phones = v.get("telefonNummer") or []
        founded = meta.get("stiftelsesDato")
        return CvrCompany(
            cvr=str(v.get("cvrNummer") or ""), name=(meta.get("nyesteNavn") or {}).get("navn") or "",
            address=street, zip_code=str(adr.get("postnummer") or ""), city=adr.get("postdistrikt") or "",
            legal_form_text=form_text, legal_form=legal_form_code(form_text),
            industry_code=str(branche.get("branchekode") or ""), industry_text=branche.get("branchetekst") or "",
            founded=date.fromisoformat(founded) if founded else None,
            fiscal_year_start=start, fiscal_year_end=end,
            email=(emails[-1].get("kontaktoplysning") if emails else "") or "",
            phone=(phones[-1].get("kontaktoplysning") if phones else "") or "",
            status=meta.get("sammensatStatus") or "", source="virk")


CLIENTS = {"mock": MockCVRClient, "cvrapi": CvrApiClient, "virk": VirkSystemToSystemClient}


def get_client():
    return select("CVR_PROVIDER", CLIENTS)


def lookup(cvr):
    """Slå op hos udbyderen i CVR_PROVIDER. En kommasepareret liste (fx "virk,cvrapi") prøves
    i rækkefølge: næste udbyder bruges, når en mangler aftale eller har brugt sin kvote."""
    names = [n.strip() for n in str(setting("CVR_PROVIDER", "mock") or "mock").split(",") if n.strip()]
    last = None
    for i, name in enumerate(names):
        if name not in CLIENTS:
            raise IntegrationError(f"Ukendt CVR-udbyder: {name}")
        try:
            return CLIENTS[name]().lookup(cvr)
        except (QuotaExceeded, AgreementRequired) as e:
            last = e
            if i == len(names) - 1:
                raise
    raise last
