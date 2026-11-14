"""Account codes the code books to. All codes are PCGM (see accounts/pcgm.py);
never hardcode an account code anywhere else."""

from decimal import ROUND_HALF_UP, Decimal

# The books are in dirham. Euros on the EUR account (51413) and its 34972
# "not yet exchanged" leg have no dirham value until they are exchanged into a
# MAD account (CIH 300); until then their lines stay in EUR and are left out of
# every dirham total (reports, TVA, margin).
BASE_CURRENCY = "MAD"

# Treasury
BANK_CIH300 = "51411"
BANK_CIH600 = "51412"
BANK_CIH600_EUR = "51413"
BANK_BP09 = "51414"
CASH = "51611"
TREASURY_PREFIXES = ("514", "516")

# Third parties
RECEIVABLE = "3421"            # Clients
CLIENT_ADVANCES = "4421"       # Clients - avances et acomptes reçus
PAYABLE = "4411"               # Fournisseurs
SUSPENSE = "34971"             # Banque - opérations à classer
EUR_UNEXCHANGED = "34972"      # Devises reçues non encore changées

# TVA (Art. 125 bis CGI: margin regime)
TVA_MARGIN = "4455"            # Etat - TVA facturée (TVA on margin)
TVA_DUE = "4456"               # Etat - TVA due (suivant déclarations)
TVA_RECOVERABLE = "34552"      # Etat - TVA récupérable sur charges
TVA_RATE = 20

# Results
REVENUE = "71243"              # Prestations de services (gross, TTC)
COST_OF_SALES = "61263"        # Achats des prestations de service (TTC, no deduction)
COST_HOTELS = "612631"
COST_TRANSPORT = "612632"
COST_GUIDES = "612633"
COST_RESTAURANTS = "612634"
COST_ACTIVITIES = "612635"
COST_OTHER = "612639"
BANK_FEES = "61473"            # Frais et commissions sur services bancaires
INTEREST = "63115"             # Intérêts bancaires
FEES = "61365"                 # Honoraires (comptable, avocat)

# Payroll
SALARIES = "61711"
SOCIAL_CHARGES = "61741"
SALARIES_PAYABLE = "4432"
CNSS_PAYABLE = "4441"
IR_PAYABLE = "44525"

# Accounts that are booked by the system and never offered as a counterpart.
SYSTEM_ACCOUNTS = (RECEIVABLE, CLIENT_ADVANCES, PAYABLE, TVA_MARGIN, TVA_DUE)


def is_treasury(code):
    """True for bank and cash accounts (514x, 516x)."""
    return bool(code) and code.startswith(TREASURY_PREFIXES)


def is_cash(code):
    """True for cash accounts (516x, caisse)."""
    return bool(code) and code.startswith("516")


def is_cost_of_sales(code):
    return bool(code) and code.startswith(COST_OF_SALES)


def margin_tva(margin_ttc):
    """TVA on a margin that includes TVA: margin / 1.2 * 20 %."""
    margin_ttc = Decimal(margin_ttc)
    rate = Decimal(TVA_RATE) / 100
    return (margin_ttc / (1 + rate) * rate).quantize(Decimal("0.01"), ROUND_HALF_UP)


def treasury_q(field="code"):
    """Q matching treasury account codes on `field` (e.g. "account__code")."""
    from django.db.models import Q

    q = Q()
    for p in TREASURY_PREFIXES:
        q |= Q(**{f"{field}__startswith": p})
    return q


def treasury_accounts():
    """Active bank and cash accounts that can hold money (leaf accounts only)."""
    from accounts.models import Account

    return Account.objects.filter(treasury_q(), is_active=True, children__isnull=True)
