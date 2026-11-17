"""Opret interne opgaver for kunder, hvis kundekendskab skal opdateres (eller mangler).

Fristen for næste opdatering sættes ved godkendelse ud fra risikoen og husets egen politik
(Firm.kyc_review_months). Kører fx månedligt sammen med retention_report.

    manage.py kyc_review_report [--dry-run]
"""

from django.core.management.base import BaseCommand
from django.utils import timezone

from firm.models import FirmTask
from firm.views_kyc import status_of
from tenancy.models import ClientCompany

TITLE = "Kundekendskab (hvidvask) skal opdateres"
TITLE_MISSING = "Kundekendskab (hvidvask) mangler"


class Command(BaseCommand):
    help = "Opret opgaver for kunder med forfaldent eller manglende kundekendskab."

    def add_arguments(self, parser):
        parser.add_argument("--dry-run", action="store_true")

    def handle(self, *args, **opts):
        today = timezone.localdate()
        created = 0
        for client in ClientCompany.objects.exclude(schema_name="public").exclude(status="archived"):
            st = status_of(client, today=today)
            if st not in ("due", "missing"):
                continue
            title = TITLE if st == "due" else TITLE_MISSING
            if FirmTask.objects.filter(client=client, title=title).exclude(status="closed").exists():
                continue
            self.stdout.write(f"{client.slug}: {title}")
            if opts["dry_run"]:
                continue
            FirmTask.objects.create(
                client=client, title=title, kind="opgave", visible_to_client=False,
                assigned_to=client.responsible, due_date=today,
                description="Opdatér kundekendskab og risikovurdering under kunden → Hvidvask, og få den "
                            "godkendt af en partner (HVL § 10, nr. 1; § 11, stk. 1, nr. 5).",
            )
            created += 1
        self.stdout.write(self.style.SUCCESS(f"{created} nye opgaver"))
