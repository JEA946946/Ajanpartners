"""Fuldmagter, der udløber inden for 30 dage (eller er udløbet): en intern opgave til fuldmagtshaveren
eller kundens ansvarlige, så fuldmagten kan fornyes i tide.

    manage.py poa_expiry_report [--dry-run]
"""

from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from firm.models import FirmTask, PowerOfAttorney
from firm.views_dashboard import EXPIRY_WARNING_DAYS


class Command(BaseCommand):
    help = "Opret opgaver for fuldmagter, der snart udløber."

    def add_arguments(self, parser):
        parser.add_argument("--dry-run", action="store_true")

    def handle(self, *args, **opts):
        today = timezone.localdate()
        created = 0
        qs = PowerOfAttorney.objects.filter(revoked_on=None, expires_on__isnull=False,
                                            expires_on__lte=today + timedelta(days=EXPIRY_WARNING_DAYS)) \
            .exclude(client__status="archived").select_related("client", "holder")
        for p in qs:
            title = f"Fuldmagt udløber {p.expires_on:%d-%m-%Y}: {p.get_kind_display()}"[:255]
            if FirmTask.objects.filter(client=p.client, title=title, visible_to_client=False).exists():
                continue
            self.stdout.write(f"{p.client.slug}: {title}")
            if opts["dry_run"]:
                continue
            FirmTask.objects.create(
                client=p.client, title=title, kind="opgave", visible_to_client=False,
                assigned_to=p.holder or p.client.responsible, due_date=p.expires_on,
                description=f"Fuldmagten ({p.scope}) udløber {p.expires_on:%d-%m-%Y}. Forny den hos "
                            f"{p.get_kind_display()} sammen med kunden, og registrér den nye under kunden → Fuldmagter.")
            created += 1
        self.stdout.write(self.style.SUCCESS(f"{created} nye opgaver"))
