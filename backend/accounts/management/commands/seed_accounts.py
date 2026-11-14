"""Opret kontoplan (Erhvervsstyrelsens standardkontoplan), momskoder og journaler
i den aktuelle kundes skema. Kaldes af tenancy/services.py: create_client.

    manage.py tenant_command seed_accounts --template=standard --schema=c_kunde

Opretter aldrig brugere.
"""

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from accounts.models import Account, AccountType
from accounts.standardkontoplan import TEMPLATES, active_codes, all_accounts


ACCOUNT_TYPES = [
    {"name": "Asset", "normal_balance": "debit", "display_order": 1},
    {"name": "Liability", "normal_balance": "credit", "display_order": 2},
    {"name": "Equity", "normal_balance": "credit", "display_order": 3},
    {"name": "Revenue", "normal_balance": "credit", "display_order": 4},
    {"name": "Expense", "normal_balance": "debit", "display_order": 5},
]


def seed_chart(template="standard"):
    """Opret manglende kontotyper og konti, sæt overkonti, standardnummer og
    ÅRL-linje. Eksisterende konti omdøbes ikke, og deres aktiv-status ændres ikke.
    Returnerer antallet af nye konti."""
    active = active_codes(template)
    type_map = {}
    for t in ACCOUNT_TYPES:
        obj, _ = AccountType.objects.get_or_create(
            name=t["name"],
            defaults={"normal_balance": t["normal_balance"], "display_order": t["display_order"]},
        )
        type_map[t["name"]] = obj

    rows = all_accounts()
    created_count = 0
    with transaction.atomic():
        by_code = {a.code: a for a in Account.objects.all()}
        for row in rows:
            header = row["kind"] != "K"
            acc = by_code.get(row["code"])
            if acc is None:
                acc = Account.objects.create(
                    code=row["code"], name=row["name"], account_type=type_map[row["type"]],
                    currency="DKK", standard_code=row["standard_code"], arl_line=row["arl_line"],
                    is_header=header, is_active=header or row["code"] in active,
                )
                by_code[acc.code] = acc
                created_count += 1
            else:
                changed = []
                for field, value in (("standard_code", row["standard_code"]), ("arl_line", row["arl_line"]),
                                     ("is_header", header)):
                    if not getattr(acc, field) and value:
                        setattr(acc, field, value)
                        changed.append(field)
                if changed:
                    acc.save(update_fields=changed)
        for row in rows:
            acc = by_code[row["code"]]
            parent_id = by_code[row["parent"]].id if row["parent"] else None
            if acc.parent_id != parent_id:
                acc.parent_id = parent_id
                acc.save(update_fields=["parent"])

    from core.vat_codes import seed_tax_codes
    from journals.journal_for import seed_journals
    seed_tax_codes()
    seed_journals()
    return created_count


class Command(BaseCommand):
    help = "Opret kontoplan, momskoder og journaler i den aktuelle kundes skema"

    def add_arguments(self, parser):
        parser.add_argument("--template", default="standard",
                            help="Kontoplanskabelon: " + " | ".join(TEMPLATES))

    def handle(self, *args, **options):
        template = options["template"] or "standard"
        if template not in TEMPLATES:
            raise CommandError(f"Ukendt skabelon '{template}'. Vælg en af: {', '.join(TEMPLATES)}")
        created_count = seed_chart(template)
        self.stdout.write(self.style.SUCCESS(f"Kontoplan ({template}) oprettet, {created_count} nye konti"))
