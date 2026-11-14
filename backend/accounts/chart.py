"""De kontonumre, koden bogfører på. Eneste sted, hvor kontonumre står i koden.

Numrene følger Erhvervsstyrelsens standardkontoplan (accounts/standardkontoplan.py,
version gyldig fra 2026-01-01). Egne underkonti (fx flere bankkonti eller
mellemregningskontoen) har deres eget nummer, men `Account.standard_code` peger
på standardkontoplanens konto, som SAF-T bruger.

Spejles i frontend/src/utils/chart.ts.
"""

# Bøgerne føres i danske kroner. Debet/kredit på en linje er altid DKK; et
# beløb i fremmed valuta står i currency/exchange_rate/amount_currency.
BASE_CURRENCY = "DKK"

# ─── Likvider ───
CASH = "6470"                  # Kasse (std. 6470 Likvide beholdninger)
BANK = "6480"                  # Bankkonto
# Standardkontoplanens konti for likvider: en konto med en af disse som
# standard_code er en bank- eller kassekonto (egne bankkonti fx 6481 → 6480).
TREASURY_STANDARD_CODES = ("6470", "6480")
CASH_STANDARD_CODES = ("6470",)

# ─── Debitorer og kreditorer ───
RECEIVABLE = "6190"            # Debitorer (tilgodehavender fra salg og tjenesteydelser)
CUSTOMER_PREPAYMENTS = "7410"  # Modtagne forudbetalinger fra kunder
PAYABLE = "7440"               # Kreditorer (leverandører af varer og tjenesteydelser)
SUSPENSE = "6335"              # Uafklarede poster / mellemregning (egen konto, std. 6330)
SUSPENSE_STANDARD = "6330"
OTHER_RECEIVABLES = "6330"     # Øvrige tilgodehavender
PREPAID_EXPENSES = "6390"      # Periodeafgrænsningsposter (aktiv)
ACCRUED_LIABILITIES = "8070"   # Periodeafgrænsningsposter (passiv)
OTHER_PAYABLES = "8040"        # Øvrig anden gæld
CORPORATE_TAX_PAYABLE = "8042" # Skyldig selskabsskat (egen konto, std. 8040)
BANK_DEBT = "7330"             # Gæld til banker (kortfristet)

# ─── Moms og afgifter (std. 7680-7840) ───
VAT_OUTPUT = "7680"            # Salgsmoms
VAT_EU_GOODS = "7700"          # Moms af varekøb udland (EU og ikke-EU)
VAT_EU_SERVICES = "7720"       # Moms af ydelseskøb udland med omvendt betalingspligt
VAT_INPUT = "7740"             # Købsmoms
TAX_OIL = "7760"               # Olie- og flaskegasafgift (godtgørelse)
TAX_ELECTRICITY = "7780"       # Elafgift
TAX_GAS = "7800"               # Naturgas- og bygasafgift
TAX_COAL = "7810"              # Kulafgift
TAX_WATER = "7820"             # Vandafgift
TAX_CO2 = "7830"               # CO2-afgift
VAT_SETTLEMENT = "7840"        # Momsafregning (skyldig moms)
VAT_ACCOUNTS = (VAT_OUTPUT, VAT_EU_GOODS, VAT_EU_SERVICES, VAT_INPUT,
                TAX_OIL, TAX_ELECTRICITY, TAX_GAS, TAX_COAL, TAX_WATER, TAX_CO2)
VAT_RATE = 25                  # Momslovens § 33

# ─── Resultat ───
REVENUE = "1010"               # Salg af varer og ydelser (DK, med moms)
REVENUE_EU_GOODS = "1050"      # Salg af varer udland, EU
REVENUE_NON_EU_GOODS = "1100"  # Salg af varer udland, ikke-EU
REVENUE_EU_SERVICES = "1150"   # Salg af ydelser udland, EU
REVENUE_NON_EU_SERVICES = "1200"  # Salg af ydelser udland, ikke-EU
PURCHASES = "1610"             # Varekøb
PURCHASES_EU_GOODS = "1630"    # Varekøb udland, EU
SERVICES_PURCHASED = "1660"    # Ydelseskøb
SERVICES_EU = "1710"           # Ydelseskøb udland, EU
REPRESENTATION = "1910"        # Repræsentation (skattemæssigt begrænset fradrag)
OTHER_EXTERNAL = "2810"        # Andre eksterne omkostninger
BANK_FEES = "2390"             # Porto og gebyrer (bankgebyrer)
FEES = "2670"                  # Revision og regnskabsmæssig assistance
ROUNDING = "2720"              # Øreafrunding/kassedifferencer
BAD_DEBTS = "2280"             # Tab på debitorer
INTEREST_INCOME = "3470"       # Renter fra banker
REMINDER_FEES = "3490"         # Renter og rykkergebyrer vedr. debitorer
INTEREST = "3670"              # Renter til banker og realkreditinstitutter
FX_GAIN = "3535"               # Valutakursregulering (gevinst)
FX_LOSS = "3610"               # Valutakursregulering (tab)
CORPORATE_TAX = "3740"         # Årets skat

# ─── Egenkapital og årsafslutning ───
SHARE_CAPITAL = "6510"         # Registreret kapital
RETAINED_EARNINGS_OPENING = "6935"  # Overført resultat, primo
RETAINED_EARNINGS = "6940"     # Overført resultat, jf. resultatdisponering
PROPOSED_DIVIDEND = "6960"     # Foreslået udbytte
# Enkeltmandsvirksomhed (klasse A)
OWNER_EQUITY_OPENING = "6915"  # Egenkapital primo
OWNER_RESULT = "6916"          # Årets resultat
OWNER_DRAWINGS = "6923"        # Privat hævet
OWNER_CONTRIBUTIONS = "6924"   # Privat indskud

# Konti, som systemet selv bogfører på og aldrig tilbyder som modkonto.
SYSTEM_ACCOUNTS = (RECEIVABLE, CUSTOMER_PREPAYMENTS, PAYABLE, VAT_OUTPUT, VAT_EU_GOODS,
                   VAT_EU_SERVICES, VAT_INPUT, VAT_SETTLEMENT)

# Resultatkonti (std. 1000-4999) og balancekonti (5000-).
RESULT_RANGE = (1000, 4999)


def is_result_code(code):
    """True for a result account (resultatopgørelse) by its standard code."""
    try:
        return RESULT_RANGE[0] <= int(str(code)[:4]) <= RESULT_RANGE[1]
    except (TypeError, ValueError):
        return False


def is_treasury(code):
    """True for a bank or cash account (by its own number or its standard code)."""
    if not code:
        return False
    from accounts.models import Account
    if code in TREASURY_STANDARD_CODES:
        return True
    return Account.objects.filter(code=code, standard_code__in=TREASURY_STANDARD_CODES).exists()


def is_treasury_account(account):
    return bool(account) and (account.code in TREASURY_STANDARD_CODES
                              or account.standard_code in TREASURY_STANDARD_CODES)


def is_cash(code):
    """True for a cash account (kasse)."""
    if not code:
        return False
    from accounts.models import Account
    if code in CASH_STANDARD_CODES:
        return True
    return Account.objects.filter(code=code, standard_code__in=CASH_STANDARD_CODES).exists()


def treasury_q(field="code"):
    """Q for treasury accounts on `field` (e.g. "account__code"): matches the
    account's standard code (6470/6480)."""
    from django.db.models import Q

    prefix = field[: -len("code")] if field.endswith("code") else ""
    return Q(**{f"{prefix}standard_code__in": TREASURY_STANDARD_CODES}) | Q(
        **{f"{field}__in": TREASURY_STANDARD_CODES})


def treasury_accounts():
    """Active bank and cash accounts that can hold money (postable accounts only)."""
    from accounts.models import Account

    return Account.objects.filter(treasury_q(), is_active=True, is_header=False)


# ─── Dansk løn (navnene er faste og bruges af payroll/). Numrene er
# standardkontoplanens (accounts/standardkontoplan.py). ───
DK_SALARIES = "2845"               # Lønninger, AM-bidragspligtig A-indkomst
DK_HOLIDAY_PAY_EXPENSE = "2860"    # Feriepenge og SH-tillæg
DK_PENSION_EXPENSE = "2910"        # Pensioner, arbejdsgiver
DK_ATP_EXPENSE = "2898"            # ATP, arbejdsgiver
DK_BENEFITS_EXPENSE = "2887"       # Personalegoder (fri bil, telefon m.m.)
DK_SALARY_REFUNDS = "2885"         # Lønrefusioner (sygedagpenge, barsel)
DK_SALARIES_PAYABLE = "7860"       # Skyldig løn og gager (netto)
DK_A_TAX_PAYABLE = "7920"          # Skyldig A-skat
DK_AM_PAYABLE = "7940"             # Skyldigt AM-bidrag
DK_ATP_PAYABLE = "7960"            # Skyldigt ATP-bidrag
DK_PENSION_PAYABLE = "8000"        # Anden skyldig pension
DK_HOLIDAY_PAY_PAYABLE = "7900"    # Skyldige feriepenge (Feriekonto/feriepengeforpligtelse)
DK_OTHER_PAYROLL_PAYABLE = "8010"  # Skyldige arbejdsgiverbidrag (samlet betaling: AUB, barsel m.m.)
