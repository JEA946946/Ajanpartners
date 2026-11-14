"""Påmind kunderne om at forny samtykket til bankkoblingen (PSD2: hver 180. dag).

    manage.py bank_feed_reminders [--days 14] [--dry-run]

Opretter én opgave til kunden (firm.FirmTask, kind="opgave", synlig for kunden) pr.
kobling, hvis samtykke udløber inden for --days dage eller allerede er udløbet. Der
oprettes højst én opgave pr. kobling pr. samtykkeperiode: opgaven kendes på
reference_id "bank_feed:<kobling>:<udløbsdato>", så et fornyet samtykke (ny udløbsdato)
giver en ny påmindelse næste gang. Køres dagligt af infra/worker.sh.
"""

from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from integrations.models import RENEW_WARNING_DAYS, BankFeedConnection


def reference_for(conn):
    return f"bank_feed:{conn.id}:{timezone.localtime(conn.consent_expires_at).date().isoformat()}"


def create_reminders(days=RENEW_WARNING_DAYS, dry_run=False):
    from firm.models import FirmTask

    limit = timezone.now() + timedelta(days=days)
    created = []
    qs = (BankFeedConnection.objects.select_related("client")
          .filter(status__in=("active", "expired"), consent_expires_at__isnull=False, consent_expires_at__lte=limit)
          .exclude(client__status="archived").exclude(client__schema_name="public"))
    for conn in qs:
        ref = reference_for(conn)
        if FirmTask.objects.filter(client=conn.client, reference_id=ref).exists():
            continue
        expires = timezone.localtime(conn.consent_expires_at).date()
        expired = conn.consent_expires_at <= timezone.now()
        bank = conn.institution_name or "banken"
        account = f" ({conn.iban})" if conn.iban else ""
        title = (f"Bankkoblingen til {bank} er udløbet – forny samtykket" if expired
                 else f"Forny samtykket til bankkoblingen ({bank}) senest {expires.strftime('%d-%m-%Y')}")
        description = (
            f"Jeres samtykke til, at bogføringen må hente kontooplysninger fra {bank}{account}, "
            f"{'udløb' if expired else 'udløber'} den {expires.strftime('%d-%m-%Y')}. Efter PSD2 skal samtykket "
            "fornyes hver 180. dag. Gå til Bank → Bankkobling og tryk 'Forny samtykke'. Indtil da hentes der "
            "ingen nye banktransaktioner automatisk.")
        if not dry_run:
            FirmTask.objects.create(client=conn.client, title=title[:255], description=description, kind="opgave",
                                    visible_to_client=True, reference_id=ref,
                                    reference_label=f"Bankkobling {bank}{account}"[:255], due_date=expires)
        created.append((conn, title))
    return created


class Command(BaseCommand):
    help = "Opret påmindelser til kunderne om bankkoblinger, hvis samtykke snart udløber."

    def add_arguments(self, parser):
        parser.add_argument("--days", type=int, default=RENEW_WARNING_DAYS)
        parser.add_argument("--dry-run", action="store_true")

    def handle(self, *args, **opts):
        created = create_reminders(opts["days"], opts["dry_run"])
        for conn, title in created:
            self.stdout.write(f"{conn.client.slug}: {title}")
        verb = "ville blive oprettet" if opts["dry_run"] else "oprettet"
        self.stdout.write(self.style.SUCCESS(f"{len(created)} påmindelser {verb}."))
