"""Danske momskoder, som seed_accounts opretter.

Koderne og deres placering på momsangivelsen følger Erhvervsstyrelsens
"Momskoder – bruttoliste" (gyldig fra 2025-12-01, git.erst.dk
standard-filformater/Standardkontoplanen/JSON/2026-01-01-Momskoder-Bruttoliste.json),
kolonnerne "momskode NY" og "momsangivelse". Energiafgiftskoderne (E-…) er
systemets egne: de er ikke moms, men afgiftsgodtgørelse, der angives i
momsangivelsens afgiftsfelter.

Felter: (kode, navn, type, sats, momskonto, fradragskonto, fradrag %, omvendt
betalingspligt, rubrik, energiafgift, fakturatekst)
"""

from accounts import chart

# Fakturatekster. "Omvendt betalingspligt" er den tekst, momsbekendtgørelsens
# § 58, stk. 1, nr. 12 kræver ved EU-B2B-ydelser og indenlandsk omvendt
# betalingspligt (momslovens § 46).
REVERSE = "Omvendt betalingspligt"
EXEMPT = "Momsfritaget, jf. momslovens § 13"
EU_GOODS = "Omvendt betalingspligt – momsfri EU-levering af varer (momslovens § 34)"
EXPORT = "Eksport uden for EU – momsfri (momslovens § 34)"

TAX_CODES = [
    # ─── Salg ───
    ("S01", "Salg med moms 25 % (DK)", "sales", 25, chart.VAT_OUTPUT, None, 100, "", "", False, ""),
    ("S02", "Salg 0 % moms i DK (indenlandsk omvendt betalingspligt m.m.)", "sales", 0, chart.VAT_OUTPUT,
     None, 100, "", "C", False, REVERSE),
    ("S82", "Momsfritaget salg (momslovens § 13)", "sales", 0, chart.VAT_OUTPUT, None, 100, "", "", False, EXEMPT),
    ("S21", "EU-salg af varer B2B (rubrik B, indberettes)", "sales", 0, chart.VAT_OUTPUT, None, 100, "",
     "B_goods", False, EU_GOODS),
    ("S22", "EU-salg af varer B2B (rubrik B, indberettes ikke til EU-salg uden moms)", "sales", 0,
     chart.VAT_OUTPUT, None, 100, "", "B_goods_other", False, EU_GOODS),
    ("S23", "EU-salg af ydelser B2B (rubrik B)", "sales", 0, chart.VAT_OUTPUT, None, 100, "", "B_services",
     False, REVERSE),
    ("S41", "Eksport af varer uden for EU (rubrik C)", "sales", 0, chart.VAT_OUTPUT, None, 100, "", "C",
     False, EXPORT),
    ("S42", "Salg af ydelser uden for EU (rubrik C)", "sales", 0, chart.VAT_OUTPUT, None, 100, "", "C",
     False, "Ydelsen er ikke momspligtig i Danmark (leveringssted uden for EU)"),
    # ─── Køb (DK) ───
    ("K010", "Køb med moms 25 %, fuldt fradrag", "purchase", 25, chart.VAT_INPUT, None, 100, "", "", False, ""),
    ("K030", "Køb uden moms / momsfritaget køb", "purchase", 0, chart.VAT_INPUT, None, 0, "", "", False, ""),
    ("K070", "Restaurant og repræsentation, 25 % af momsen fratrækkes", "purchase", 25, chart.VAT_INPUT, None,
     25, "", "", False, ""),
    # Delvis fradrag: fradragsprocenten (pro rata) sættes pr. kunde på koden.
    # TODO(revisor): sæt den foreløbige fradragsprocent for kunder med blandede aktiviteter.
    ("K110", "Køb med delvis fradrag (pro rata)", "purchase", 25, chart.VAT_INPUT, None, 100, "", "", False, ""),
    ("K040", "Fastnettelefon m.m., lovbestemt 50 % fradrag", "purchase", 25, chart.VAT_INPUT, None, 50, "", "",
     False, ""),
    ("K660", "Byggeydelser m.m. med indenlandsk omvendt betalingspligt, fuldt fradrag", "purchase", 25,
     chart.VAT_OUTPUT, chart.VAT_INPUT, 100, "domestic", "", False, ""),
    # ─── Køb fra EU ───
    ("K210", "EU-varekøb (erhvervelsesmoms), fuldt fradrag – rubrik A varer", "purchase", 25,
     chart.VAT_EU_GOODS, chart.VAT_INPUT, 100, "eu_goods", "A_goods", False, ""),
    ("K260", "EU-ydelseskøb (omvendt betalingspligt), fuldt fradrag – rubrik A ydelser", "purchase", 25,
     chart.VAT_EU_SERVICES, chart.VAT_INPUT, 100, "eu_services", "A_services", False, ""),
    ("K340", "Momsfritaget køb fra EU", "purchase", 0, chart.VAT_INPUT, None, 0, "", "", False, ""),
    # ─── Køb uden for EU ───
    ("K410", "Varekøb uden for EU (importmoms), fuldt fradrag", "purchase", 25, chart.VAT_EU_GOODS,
     chart.VAT_INPUT, 100, "eu_goods", "", False, ""),
    ("K460", "Ydelseskøb uden for EU (omvendt betalingspligt), fuldt fradrag", "purchase", 25,
     chart.VAT_EU_SERVICES, chart.VAT_INPUT, 100, "eu_services", "", False, ""),
    # ─── Energiafgifter (godtgørelse). Linjens beløb er den afgift, der kan
    # godtgøres, og bogføres på afgiftskontoen i stedet for omkostningen.
    # TODO(revisor): kun afgift af energi til momspligtig proces kan godtgøres
    # (fx ikke rumvarme for kontorvirksomheder); brugeren angiver selv beløbet.
    ("E-EL", "Elafgift (godtgørelse)", "purchase", 0, chart.TAX_ELECTRICITY, None, 100, "", "", True, ""),
    ("E-OLIE", "Olie- og flaskegasafgift (godtgørelse)", "purchase", 0, chart.TAX_OIL, None, 100, "", "", True, ""),
    ("E-GAS", "Naturgas- og bygasafgift (godtgørelse)", "purchase", 0, chart.TAX_GAS, None, 100, "", "", True, ""),
    ("E-KUL", "Kulafgift (godtgørelse)", "purchase", 0, chart.TAX_COAL, None, 100, "", "", True, ""),
    ("E-CO2", "CO2-afgift (godtgørelse)", "purchase", 0, chart.TAX_CO2, None, 100, "", "", True, ""),
    ("E-VAND", "Vandafgift (godtgørelse)", "purchase", 0, chart.TAX_WATER, None, 100, "", "", True, ""),
]

# Koder, hvis standardkode (SAF-T) er en anden end koden selv: ingen; E-koderne
# har ingen standardkode.
NON_STANDARD = {code for code, *_ in TAX_CODES if code.startswith("E-")}


def seed_tax_codes():
    """Opret manglende momskoder. Eksisterende koder ændres ikke (kunden kan have
    rettet fradragsprocenten). Returnerer antallet oprettede."""
    from accounts.models import Account
    from core.models import TaxCode

    accounts = {a.code: a for a in Account.objects.all()}
    created = 0
    for (code, name, type_, rate, account, input_account, deduction, reverse, rubrik, energy,
         text) in TAX_CODES:
        _, new = TaxCode.objects.get_or_create(code=code, defaults={
            "name": name, "type": type_, "rate": rate, "account": accounts[account],
            "input_account": accounts[input_account] if input_account else None,
            "deduction_rate": deduction, "reverse_charge": reverse, "rubrik": rubrik,
            "energy_tax": energy, "invoice_text": text,
            "standard_code": "" if code in NON_STANDARD else code,
        })
        created += new
    return created
