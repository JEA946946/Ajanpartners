"""Which journal an entry goes in. The only place journal codes are spelled out."""

BANK_JOURNALS = {  # code: (name, treasury account, currency)
    "BQ1": ("Banque CIH 300", "51411", "MAD"),
    "BQ2": ("Banque CIH 600", "51412", "MAD"),
    "BQ3": ("Banque CIH 600 EUR", "51413", "EUR"),
    "BQ4": ("Banque BP 09", "51414", "MAD"),
}
CASH = "CA"
PURCHASES = "AC"
SALES = "VE"
PAYROLL = "PA"
MISC = "OD"
OPENING = "AN"

JOURNALS = [
    *[(code, name, "bank", account, currency) for code, (name, account, currency) in BANK_JOURNALS.items()],
    (CASH, "Caisse", "cash", "51611", "MAD"),
    (PURCHASES, "Achats", "purchases", None, "MAD"),
    (SALES, "Ventes", "sales", None, "MAD"),
    (PAYROLL, "Paie", "payroll", None, "MAD"),
    (MISC, "Opérations diverses", "misc", None, "MAD"),
    (OPENING, "À-nouveaux", "opening", None, "MAD"),
]

# Entry source → journal, for entries that are not tied to a treasury account.
SOURCE_JOURNAL = {
    "invoice": SALES,
    "credit_note": SALES,
    "cmr_invoice": SALES,
    "expense": PURCHASES,
    "cmr_payment": PURCHASES,
    "payroll": PAYROLL,
    "opening": OPENING,
}


def journal_by_code(code):
    from .models import Journal
    journal = Journal.objects.filter(code=code).first()
    if journal is None:  # a fresh database before seed_accounts has run
        seed_journals()
        journal = Journal.objects.get(code=code)
    return journal


def journal_for_source(source):
    """Journal for a source; manual, TVA, reversal and closing entries go in OD."""
    return journal_by_code(SOURCE_JOURNAL.get(source, MISC))


def journal_for_account(account):
    """The bank or cash journal of a treasury account, or None."""
    from .models import Journal
    if account is None:
        return None
    return Journal.objects.filter(account=account).first()


def seed_journals():
    """Create missing journals and link bank and cash journals to their account.
    Returns the number created."""
    from accounts.models import Account
    from .models import Journal
    created = 0
    for code, name, type_, account_code, currency in JOURNALS:
        account = Account.objects.filter(code=account_code).first() if account_code else None
        journal, new = Journal.objects.get_or_create(
            code=code, defaults={"name": name, "type": type_, "account": account, "currency": currency})
        created += new
        if journal.account_id is None and account is not None:
            # Created before the chart was seeded (migration 0012 on a fresh database).
            journal.account = account
            journal.save(update_fields=["account"])
    return created
