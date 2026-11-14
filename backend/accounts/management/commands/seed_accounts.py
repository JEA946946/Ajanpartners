"""Seed account types and the Moroccan chart of accounts (PCGM)."""

from django.core.management.base import BaseCommand

from accounts.models import Account, AccountType
from accounts.pcgm import OWN_ACCOUNTS, all_accounts, parent_code


ACCOUNT_TYPES = [
    {"name": "Asset", "normal_balance": "debit", "display_order": 1},
    {"name": "Liability", "normal_balance": "credit", "display_order": 2},
    {"name": "Equity", "normal_balance": "credit", "display_order": 3},
    {"name": "Revenue", "normal_balance": "credit", "display_order": 4},
    {"name": "Expense", "normal_balance": "debit", "display_order": 5},
    # Class 8 (result accounts) and class 0 (off-balance) are kept inactive.
    {"name": "Result", "normal_balance": "credit", "display_order": 6},
    {"name": "Special", "normal_balance": "debit", "display_order": 7},
]


def seed_chart():
    """Create missing account types and PCGM accounts and set parents. Returns
    the number of new accounts. Existing accounts are never renamed; our own
    accounts get their currency (51413 and 34972 are EUR)."""
    type_map = {}
    for t in ACCOUNT_TYPES:
        obj, _ = AccountType.objects.get_or_create(
            name=t["name"],
            defaults={"normal_balance": t["normal_balance"], "display_order": t["display_order"]},
        )
        type_map[t["name"]] = obj

    rows = all_accounts()
    created_count = 0
    for code, name, type_name, currency, is_active in rows:
        _, created = Account.objects.get_or_create(
            code=code,
            defaults={
                "name": name,
                "account_type": type_map[type_name],
                "currency": currency,
                "is_active": is_active,
            },
        )
        created_count += created

    known = {code for code, *_ in rows}
    by_code = {a.code: a for a in Account.objects.filter(code__in=known)}
    for code in known:
        parent = parent_code(code, known)
        child = by_code[code]
        parent_id = by_code[parent].id if parent else None
        if child.parent_id != parent_id:
            child.parent_id = parent_id
            child.save(update_fields=["parent"])
    for code, _, currency in OWN_ACCOUNTS:
        if by_code[code].currency != currency:
            by_code[code].currency = currency
            by_code[code].save(update_fields=["currency"])
    from journals.journal_for import seed_journals
    seed_journals()
    return created_count


class Command(BaseCommand):
    help = "Opret kontoplan, momskoder og journaler i den aktuelle kundes skema"

    def add_arguments(self, parser):
        parser.add_argument("--template", default="standard",
                            help="Kontoplanskabelon: standard | holding | enkeltmand")

    def handle(self, *args, **options):
        created_count = seed_chart()
        self.stdout.write(self.style.SUCCESS(f"Kontoplan oprettet, {created_count} nye konti"))
