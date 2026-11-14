"""Sync invoices and supplier payments from CMR into journal entries.

Usage:
    python manage.py sync_cmr                          # last 24h
    python manage.py sync_cmr --since=2020-01-01       # from specific date
    python manage.py sync_cmr --dry-run                # preview only
    python manage.py sync_cmr --audit                  # everything vs. the ledger, read-only

The rules are in journals/cmr_sync.py, shared with the CMR Sync page.
"""

from datetime import datetime, timedelta, timezone

from django.core.management.base import BaseCommand

from journals.cmr_client import CMRClient
from journals.cmr_sync import audit, run_sync


class Command(BaseCommand):
    help = "Sync invoices and supplier payments from CMR into journal entries"

    def add_arguments(self, parser):
        parser.add_argument("--since", help="ISO datetime to sync from (default: 24 hours ago)")
        parser.add_argument("--dry-run", action="store_true",
                            help="Preview what would be created without writing to the database")
        parser.add_argument("--audit", action="store_true",
                            help="Compare all CRM invoices and payments with the ledger; writes nothing")

    def handle(self, *args, **options):
        client = CMRClient()

        if options["audit"]:
            try:
                invoices = client.get_invoices(fetch_all=True)
                payments = client.get_supplier_payments(fetch_all=True)
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Failed to fetch CMR data: {e}"))
                return
            result = audit(invoices, payments)
            self.stdout.write(f"--- Would be booked by a full sync ({len(result['pending'])}) ---")
            for p in result["pending"]:
                self.stdout.write(f"  {p}")
            self.stdout.write(f"\n--- To check ({len(result['issues'])}) ---")
            for n in result["issues"]:
                self.stdout.write(f"  [{n['kind']}] {n['message']}")
            return

        since = options.get("since") or (datetime.now(timezone.utc) - timedelta(hours=24)).isoformat()
        dry_run = options["dry_run"]
        self.stdout.write(f"Syncing CMR events since {since}")
        if dry_run:
            self.stdout.write(self.style.WARNING("DRY RUN — no entries will be created"))
        try:
            invoices = client.get_invoices(since=since)
            payments = client.get_supplier_payments(since=since)
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Failed to fetch CMR events: {e}"))
            return
        self.stdout.write(f"  Fetched {len(invoices)} invoice(s), {len(payments)} supplier payment row(s)")

        result = run_sync(invoices, payments, created_by="sync_cmr", dry_run=dry_run)
        for line in result["details"]:
            self.stdout.write(f"  {line}")
        self.stdout.write("\n--- Summary ---")
        self.stdout.write(f"  Invoice/receipt entries: {result['invoices_created']}")
        self.stdout.write(f"  Supplier payment entries: {result['payments_created']}")
        self.stdout.write(f"  Skipped: {result['skipped']}")
        done = "DRY RUN complete — no entries were created" if dry_run else "Sync complete"
        self.stdout.write(self.style.SUCCESS(f"\n{done}"))
