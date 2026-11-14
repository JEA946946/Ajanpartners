"""Find arkiverede kunder, hvis opbevaringspligt (5 år, Bogføringsloven § 10) er udløbet.

Intet slettes automatisk. For hver kunde oprettes én intern opgave til en partner,
som skal tage stilling til sletning (og sikre, at der ikke er verserende sager,
fx skattesager eller konkursbo, der kræver længere opbevaring).

    manage.py retention_report [--dry-run]
"""

from django.core.management.base import BaseCommand
from django.utils import timezone

from firm.models import FirmTask
from tenancy.models import ClientCompany, FirmStaff

TITLE = "Opbevaringsperioden er udløbet – tag stilling til sletning"


class Command(BaseCommand):
    help = "Opret opgaver for arkiverede kunder, hvis 5-årige opbevaringspligt er udløbet."

    def add_arguments(self, parser):
        parser.add_argument("--dry-run", action="store_true")

    def handle(self, *args, **opts):
        today = timezone.localdate()
        partner = FirmStaff.objects.filter(role="partner", is_active=True).select_related("user").first()
        due = ClientCompany.objects.filter(status="archived", retain_until__isnull=False, retain_until__lte=today)
        created = 0
        for client in due:
            if FirmTask.objects.filter(client=client, title=TITLE).exclude(status="closed").exists():
                continue
            self.stdout.write(f"{client.slug}: opbevaring udløb {client.retain_until:%d-%m-%Y}")
            if opts["dry_run"]:
                continue
            FirmTask.objects.create(
                client=client, title=TITLE, kind="opgave", visible_to_client=False,
                assigned_to=partner.user if partner else None, due_date=today,
                description=(
                    f"{client.name} blev arkiveret {timezone.localtime(client.archived_at):%d-%m-%Y} "
                    f"og skulle opbevares til {client.retain_until:%d-%m-%Y}.\n"
                    "Tjek, at der ikke er verserende sager, der kræver længere opbevaring, og at kunden "
                    "har fået sin eksport (Eksportér alt). Sletning af skema og bilag sker manuelt og "
                    "skal godkendes af en partner."),
            )
            created += 1
        self.stdout.write(self.style.SUCCESS(f"{created} nye opgaver"))
