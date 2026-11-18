"""Opfølgning på materialelister (PBC): en intern opgave til den opgaveansvarlige, når kunden har
punkter, der er over fristen. Kunden ser selv fristen og de manglende punkter i sin indbakke.

    manage.py pbc_reminders [--dry-run]
"""

from collections import Counter

from django.core.management.base import BaseCommand
from django.utils import timezone

from firm.models import FirmTask

TITLE = "Materialeliste over frist: {list}"


class Command(BaseCommand):
    help = "Opret interne opgaver for materialelister med punkter over fristen."

    def add_arguments(self, parser):
        parser.add_argument("--dry-run", action="store_true")

    def handle(self, *args, **opts):
        today = timezone.localdate()
        overdue = Counter()
        owners = {}
        for t in FirmTask.objects.filter(kind="bilag_mangler", status="open", due_date__lt=today).exclude(
                engagement=None).exclude(client__status="archived").select_related("engagement", "client"):
            key = (t.engagement_id, t.list_name)
            overdue[key] += 1
            owners[key] = t
        created = 0
        for key, n in overdue.items():
            t = owners[key]
            title = TITLE.format(list=t.list_name or "materiale")[:255]
            if FirmTask.objects.filter(client=t.client, engagement=t.engagement, title=title,
                                       visible_to_client=False).exclude(status="closed").exists():
                continue
            self.stdout.write(f"{t.client.slug}: {title} ({n})")
            if opts["dry_run"]:
                continue
            FirmTask.objects.create(
                client=t.client, engagement=t.engagement, title=title, kind="opgave", visible_to_client=False,
                assigned_to=t.engagement.manager or t.assigned_to, due_date=today,
                description=f"{n} punkt(er) på materialelisten er ikke besvaret af kunden inden fristen "
                            f"{t.due_date:%d-%m-%Y}. Følg op med kunden (fx skabelonen 'Rykker for manglende materiale').")
            created += 1
        self.stdout.write(self.style.SUCCESS(f"{created} nye opgaver"))
