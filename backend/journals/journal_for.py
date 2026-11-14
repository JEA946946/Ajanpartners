"""Hvilken journal en postering hører i. Eneste sted, hvor journalkoderne står.

Bank: én journal pr. bankkonto (BANK for standardkontoen 6480; en ekstra
bankkonto, fx 6481, får sin egen journal BANK2, BANK3 … første gang, den bruges
eller når seed_journals kører).
"""

from accounts import chart

BANK = "BANK"
CASH = "KAS"
PURCHASES = "KØB"
SALES = "SALG"
PAYROLL = "LØN"
MISC = "DIV"
OPENING = "PRIMO"
CLOSING = "ÅA"

JOURNALS = [  # (kode, navn, type, likvidkonto, valuta)
    (BANK, "Bank", "bank", chart.BANK, "DKK"),
    (CASH, "Kasse", "cash", chart.CASH, "DKK"),
    (PURCHASES, "Køb", "purchases", None, "DKK"),
    (SALES, "Salg", "sales", None, "DKK"),
    (PAYROLL, "Løn", "payroll", None, "DKK"),
    (MISC, "Diverse", "misc", None, "DKK"),
    (OPENING, "Primo", "opening", None, "DKK"),
    (CLOSING, "Årsafslutning", "closing", None, "DKK"),
]

# Kilde → journal for posteringer, der ikke hører til en likvidkonto.
SOURCE_JOURNAL = {
    "invoice": SALES,
    "credit_note": SALES,
    "reminder": SALES,
    "expense": PURCHASES,
    "payroll": PAYROLL,
    "opening": OPENING,
    "closing": CLOSING,
}


def journal_by_code(code):
    from .models import Journal
    journal = Journal.objects.filter(code=code).first()
    if journal is None:  # en frisk database, før seed_accounts har kørt
        seed_journals()
        journal = Journal.objects.get(code=code)
    return journal


def journal_for_source(source):
    """Journal for en kilde; manuelle, moms-, tilbageførings- og kursposteringer går i DIV."""
    return journal_by_code(SOURCE_JOURNAL.get(source, MISC))


def journal_for_account(account):
    """Bank- eller kassejournalen for en likvidkonto (oprettes ved behov), eller None."""
    from .models import Journal
    if account is None:
        return None
    journal = Journal.objects.filter(account=account).first()
    if journal is None and chart.is_treasury_account(account):
        journal = _bank_journal_for(account)
    return journal


def _bank_journal_for(account):
    """Opret en journal til en ny bank- eller kassekonto."""
    from .models import Journal
    is_cash = account.code in chart.CASH_STANDARD_CODES or account.standard_code in chart.CASH_STANDARD_CODES
    base = CASH if is_cash else BANK
    code, n = base, 2
    while Journal.objects.filter(code=code).exists():
        code, n = f"{base}{n}", n + 1
    return Journal.objects.create(code=code, name=f"{'Kasse' if is_cash else 'Bank'} {account.code} {account.name}"[:100],
                                  type="cash" if is_cash else "bank", account=account,
                                  currency=account.currency or "DKK")


def seed_journals():
    """Opret manglende journaler, knyt bank og kasse til deres konto, og giv hver
    ekstra bankkonto sin egen journal. Returnerer antallet oprettede."""
    from accounts.models import Account
    from .models import Journal
    created = 0
    for code, name, type_, account_code, currency in JOURNALS:
        account = Account.objects.filter(code=account_code).first() if account_code else None
        journal, new = Journal.objects.get_or_create(
            code=code, defaults={"name": name, "type": type_, "account": account, "currency": currency})
        created += new
        if journal.account_id is None and account is not None and not Journal.objects.filter(account=account).exists():
            # Oprettet før kontoplanen (migration 0012 på en frisk database).
            journal.account = account
            journal.save(update_fields=["account"])
    for account in chart.treasury_accounts().filter(journal__isnull=True):
        _bank_journal_for(account)
        created += 1
    return created
