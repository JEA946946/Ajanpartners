"""Nulstil én kundes bøger (kun til opstart og test – kunderne har ingen rigtige tal endnu).

Sletter alle tal i kundens skema (posteringer, fakturaer, tilbud, rykkere,
regninger, udgifter, betalinger, lønkørsler, bankafstemninger, momsangivelser,
lukkede perioder, nummerserier og kundens audit-log), genåbner regnskabsårene og
opretter standardkontoplanen, momskoderne og journalerne igen.

Bevares: brugere, virksomhedsindstillinger, debitorer, kreditorer, medarbejdere,
projekter, journaler, bankregler, regnskabsår (genåbnes) og konti.

    manage.py reset_bookkeeping --client <slug>            # prøvekørsel, ændrer intet
    manage.py reset_bookkeeping --client <slug> --confirm  # gør det, i én transaktion

En kunde, der er i drift (status "active"), kræver også --force. Bogføringsloven
kræver, at regnskabsmateriale opbevares i 5 år: brug aldrig kommandoen på en
kunde, der har bogført rigtige tal.
"""

from django.apps import apps
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django_tenants.utils import schema_context

# Børn før forældre, så ingen PROTECT-relation blokerer.
TRANSACTIONAL = [
    "purchases.BillPaymentLink", "purchases.BankTransactionCategorization",
    "core.PaymentAllocation", "core.Payment",
    "core.BankReconciliationLine", "core.BankReconciliation",
    "core.ProjectTransaction", "core.Document",
    "core.VatReturn",
    "purchases.ExpenseLine", "purchases.Expense",
    "purchases.BillLine", "purchases.Bill",
    "sales.Reminder", "sales.CreditNote", "sales.InvoiceLine", "sales.Invoice",
    "sales.QuoteLine", "sales.Quote",
    # Løn (payroll/): kun kørsler og deres linjer; medarbejderne bevares.
    "payroll.PayrollLine", "payroll.PayrollRun",
    "journals.JournalEntryLine", "journals.JournalEntry",
    "journals.JournalSequence", "journals.Period",
    "journals.BankStatementUpload", "core.AuditLog",
]


def _model(label):
    try:
        return apps.get_model(label)
    except LookupError:  # en app har omdøbt eller fjernet modellen
        return None


class Command(BaseCommand):
    help = "Slet alle tal i én kundes bøger og opret kontoplanen igen (kræver --client og --confirm)"

    def add_arguments(self, parser):
        parser.add_argument("--client", required=True, help="Kundens slug (tenancy.ClientCompany.slug)")
        parser.add_argument("--confirm", action="store_true", help="Slet faktisk; uden den ændres intet")
        parser.add_argument("--force", action="store_true", help="Også for en aktiv kunde")

    def handle(self, *args, **options):
        from tenancy.models import ClientCompany

        client = ClientCompany.objects.filter(slug=options["client"]).first()
        if client is None:
            raise CommandError(f"Kunden '{options['client']}' findes ikke")
        if client.status == "archived":
            raise CommandError("Kunden er arkiveret (read-only i 5 år) og kan ikke nulstilles")
        if client.status == "active" and not options["force"]:
            raise CommandError("Kunden er i drift. Brug --force, hvis bøgerne kun indeholder testdata")
        with schema_context(client.schema_name):
            from journals.signals import allow_reset
            with transaction.atomic(), allow_reset():
                self.run(client)
                if not options["confirm"]:
                    transaction.set_rollback(True)
                    self.stdout.write(self.style.WARNING("Prøvekørsel – intet er ændret. Brug --confirm."))
                else:
                    self.stdout.write(self.style.SUCCESS(f"{client.name}: bøgerne starter forfra."))

    def run(self, client):
        from accounts.management.commands.seed_accounts import seed_chart
        from accounts.models import FiscalYear

        out = self.stdout.write
        out(f"Kunde: {client.name} (skema {client.schema_name})")
        out("1. Sletter tal")
        for label in TRANSACTIONAL:
            model = _model(label)
            if model is None:
                continue
            n, _ = model.objects.all().delete()
            out(f"   {label}: {n} rækker")

        out("2. Genåbner regnskabsår")
        n = FiscalYear.objects.filter(is_closed=True).update(is_closed=False, closed_at=None, closed_by="")
        out(f"   {n} genåbnet")

        out(f"3. Kontoplan ({client.chart_template}), momskoder og journaler")
        out(f"   {seed_chart(client.chart_template or 'standard')} nye konti")
