"""Hent banktransaktioner for alle aktive bankkoblinger (køres dagligt af cron).

    manage.py fetch_bank_feeds [--client <slug>] [--since ÅÅÅÅ-MM-DD]

Går alle kunder igennem; hver kobling importeres i kundens eget skema med
journals' bankimport. Arkiverede kunder springes over (read-only). Samtykker,
der udløber inden for 14 dage, nævnes, så kunden kan bedes om at forny dem.
"""

from datetime import date

from django.core.management.base import BaseCommand

from integrations import bank_feeds
from integrations.base import AgreementRequired, IntegrationError
from integrations.models import BankFeedConnection


class Command(BaseCommand):
    help = "Hent banktransaktioner via open banking for alle kunder."

    def add_arguments(self, parser):
        parser.add_argument("--client", help="Kun denne kunde (slug).")
        parser.add_argument("--since", type=date.fromisoformat, help="Hent fra denne dato (ÅÅÅÅ-MM-DD).")

    def handle(self, *args, **opts):
        qs = (BankFeedConnection.objects.select_related("client", "created_by")
              .exclude(status="revoked").exclude(client__status="archived")
              .exclude(client__schema_name="public"))
        if opts.get("client"):
            qs = qs.filter(client__slug=opts["client"])
        totals = {"connections": 0, "created": 0, "skipped": 0, "errors": 0}
        for conn in qs.order_by("client__slug", "created_at"):
            totals["connections"] += 1
            label = f"{conn.client.slug} / {conn.institution_name or conn.provider} {conn.iban}"
            try:
                result = bank_feeds.sync_connection(conn, since=opts.get("since"))
            except (IntegrationError, AgreementRequired) as e:
                totals["errors"] += 1
                self.stderr.write(f"{label}: FEJL {e}")
                continue
            if "skipped_reason" in result:
                self.stdout.write(f"{label}: sprunget over ({result['skipped_reason']})")
                continue
            totals["created"] += result["created"]
            totals["skipped"] += result["skipped"]
            note = "  – samtykket skal fornyes snart" if conn.renewal_due else ""
            self.stdout.write(f"{label}: {result['created']} nye, {result['skipped']} dubletter{note}")
        self.stdout.write(self.style.SUCCESS(
            f"Bankkobling: {totals['connections']} koblinger, {totals['created']} nye linjer, "
            f"{totals['skipped']} dubletter, {totals['errors']} fejl."))
        if totals["errors"]:
            # Ikke-nul exit, så cron/overvågning ser fejlen; de øvrige kunder er hentet.
            raise SystemExit(1)
