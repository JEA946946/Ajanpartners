"""eIndkomst: indberetning af en lønkørsel, og hentning af eSkattekort.

Begge går gennem en adapter. Indtil Ajan Partners er godkendt som dataleverandør
hos Skattestyrelsen (system-til-system), bruges mock-klienten: lønkørslen kan
eksporteres som en struktureret fil og indberettes manuelt i E-indkomst på
skat.dk. Klienten vælges med miljøvariablen EINDKOMST_CLIENT / ESKATTEKORT_CLIENT
("mock" eller "skat").

Feltnumre (felt 0013 osv.) er E-indkomsts feltnumre for lønmodtageroplysninger.
Kilde: skat.dk "Sådan indberetter du løn (eIndkomst)" og "Indberet feriepenge".
Usikre numre er markeret med TODO og skal efterprøves mod Skattestyrelsens
gældende "Vejledning til indberetning via lønsystemer" (indberetningsvejledningen).
"""

import hashlib
import os
from dataclasses import dataclass
from datetime import date
from decimal import Decimal

Z = Decimal("0")

FIELDS = {
    "0013": "A-indkomst, hvoraf der skal betales AM-bidrag",
    "0014": "A-indkomst, hvoraf der ikke skal betales AM-bidrag",
    "0015": "Indeholdt A-skat",
    "0016": "Indeholdt AM-bidrag",
    "0036": "B-indkomst, hvoraf der skal betales AM-bidrag",       # TODO(kilde: indberetningsvejledningen)
    "0038": "B-indkomst, hvoraf der ikke skal betales AM-bidrag",  # TODO(kilde: indberetningsvejledningen)
    "0046": "ATP-bidrag i alt (lønmodtager + arbejdsgiver)",
    "0068": "Fri bil, skattepligtig værdi",                         # TODO(kilde): angivet af opdragsgiver
    "0069": "Feriepenge",                                           # TODO(kilde): skat.dk nævner felt 0113 (bruttoferiepenge) ved udbetaling
    "0020": "Fri telefon/multimedier",                              # TODO(kilde: indberetningsvejledningen)
    "0021": "Andre skattepligtige personalegoder",                  # TODO(kilde: indberetningsvejledningen)
    "0147": "Arbejdsgiveradministreret pensionsbidrag i alt",        # TODO(kilde: indberetningsvejledningen)
    "0200": "Antal løntimer",
}


def _s(v):
    return f"{Decimal(v or 0):.2f}"


def build_export(run):
    """Struktureret indberetning af en lønkørsel (ét periodeadvis pr. medarbejder).

    Indeholder fulde CPR-numre, fordi Skat kræver dem. Må kun gives til brugere
    med skriveadgang og må ikke gemmes i logs.
    """
    from core.models import CompanySettings

    from .models import PayrollSettings

    company = CompanySettings.objects.first()
    ps = PayrollSettings.get()
    se = ps.se_number or (company.tax_id if company else "")
    employees = []
    for line in run.lines.select_related("employee").order_by("employee__employee_number"):
        emp = line.employee
        # 0013: kontant AM-indkomst efter ATP og eget pensionsbidrag. Personalegoder
        # indberettes i egne felter. TODO(kilde): bekræft, at goderne ikke også skal i 0013.
        am_cash = line.am_base - line.benefits
        fields = {
            "0013": am_cash,
            "0014": line.a_income_no_am,
            "0015": line.a_tax,
            "0016": line.am_contribution,
            "0036": line.b_income if line.b_income_am else Z,
            "0038": line.b_income if not line.b_income_am else Z,
            "0046": line.atp_employee + line.atp_employer,
            "0068": line.car_benefit,
            "0020": line.phone_benefit,
            "0021": line.other_benefits,
            "0069": line.holiday_pay_accrued,
            "0147": line.pension_employee + line.pension_employer,
            "0200": line.hours,
        }
        employees.append({
            "employee_number": emp.employee_number,
            "name": emp.name,
            "cpr": emp.cpr,
            "start_date": emp.start_date.isoformat() if emp.start_date else None,
            "end_date": emp.end_date.isoformat() if emp.end_date else None,
            "fields": {k: _s(v) for k, v in fields.items() if Decimal(v or 0) != 0},
        })
    return {
        "format": "ajanpartners-eindkomst-v1",
        "se_number": se,
        "company_name": company.company_name if company else "",
        "income_period": {"start": run.period_start.isoformat(), "end": run.period_end.isoformat()},
        "pay_date": run.pay_date.isoformat(),
        "run_id": str(run.id),
        "field_names": FIELDS,
        "employees": employees,
        "totals": {
            "0013": _s(sum(Decimal(e["fields"].get("0013", 0)) for e in employees)),
            "0015": _s(run.total_a_tax),
            "0016": _s(run.total_am),
            "0046": _s(run.total_atp_employee + run.total_atp_employer),
        },
    }


@dataclass
class SubmitResult:
    status: str        # accepted | rejected | pending
    reference: str
    message: str = ""


class EIndkomstClient:
    def submit(self, run) -> SubmitResult:  # pragma: no cover - interface
        raise NotImplementedError


class MockEIndkomstClient(EIndkomstClient):
    """Indberetter ikke noget; validerer filen og giver en kvittering."""

    def submit(self, run):
        data = build_export(run)
        problems = [e["name"] for e in data["employees"] if not e["cpr"]]
        if not data["se_number"]:
            return SubmitResult("rejected", "", "SE-nummer mangler (Løn → Indstillinger).")
        if problems:
            return SubmitResult("rejected", "", "CPR-nummer mangler for: " + ", ".join(problems))
        digest = hashlib.sha256(str(data).encode()).hexdigest()[:12].upper()
        return SubmitResult("accepted", f"MOCK-{digest}",
                            "Testindberetning – intet er sendt til Skattestyrelsen.")


class SkatSystemToSystemClient(EIndkomstClient):
    def submit(self, run):
        raise NotImplementedError(
            "Indberetning direkte til eIndkomst (system-til-system) kræver, at Ajan Partners er godkendt "
            "som dataleverandør hos Skattestyrelsen og har et OCES/virksomhedscertifikat og en "
            "testgodkendt snitflade. Indtil da: eksportér filen og indberet manuelt i E-indkomst."
        )


def eindkomst_client():
    return SkatSystemToSystemClient() if os.environ.get("EINDKOMST_CLIENT") == "skat" else MockEIndkomstClient()


def submit(run):
    """Adapterens indgang: indberet lønkørslen med den konfigurerede klient."""
    return eindkomst_client().submit(run)


# ─── eSkattekort ──────────────────────────────────────────────────────────────

@dataclass
class TaxCardData:
    year: int
    card_type: str          # main | secondary | free
    rate: Decimal
    deduction_month: Decimal
    deduction_fortnight: Decimal
    free_card_amount: Decimal


class ESkattekortClient:
    def fetch(self, cpr, year) -> TaxCardData:  # pragma: no cover - interface
        raise NotImplementedError


class MockESkattekortClient(ESkattekortClient):
    """Faste testdata: hovedkort 37 % med 4.600 kr. i månedsfradrag
    (CPR, der ender på et lige ciffer), ellers bikort 38 %."""

    def fetch(self, cpr, year):
        if not cpr:
            raise ValueError("Medarbejderen har intet CPR-nummer.")
        if int(cpr[-1]) % 2 == 0:
            return TaxCardData(year, "main", Decimal("37"), Decimal("4600"), Decimal("2123"), Z)
        return TaxCardData(year, "secondary", Decimal("38"), Z, Z, Z)


class SkatESkattekortClient(ESkattekortClient):
    def fetch(self, cpr, year):
        raise NotImplementedError(
            "Hentning af eSkattekort (system-til-system) kræver godkendelse som dataleverandør hos "
            "Skattestyrelsen. Indtil da: indtast trækprocent og fradrag fra skattekortet manuelt."
        )


def eskattekort_client():
    return SkatESkattekortClient() if os.environ.get("ESKATTEKORT_CLIENT") == "skat" else MockESkattekortClient()


def fetch_tax_card(cpr, year=None):
    return eskattekort_client().fetch(cpr, year or date.today().year)
