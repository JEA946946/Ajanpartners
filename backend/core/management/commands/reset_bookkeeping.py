"""Start the books over on the PCGM chart.

Deletes every number (journal entries, invoices, bills, expenses, payments,
payroll runs, bank reconciliations and receipts, audit log), seeds the PCGM
chart, re-points master data (suppliers, employees, tax codes, rules) from the
old Manager.io accounts to PCGM accounts, and deletes the old accounts.

Kept: users and roles, company settings, customers, suppliers, employees,
leave, public holidays, projects, journals, fiscal years (reopened). Closed
months and journal number series start over.

    python manage.py reset_bookkeeping            # dry run, shows what would go
    python manage.py reset_bookkeeping --confirm  # does it, in one transaction
"""

from datetime import date

from django.core.management.base import BaseCommand
from django.db import transaction

from accounts import chart
from accounts.management.commands.seed_accounts import seed_chart
from accounts.models import Account, FiscalYear, SupplierAccountMapping
from accounts.pcgm import all_accounts
from core.models import (AuditLog, BankReconciliation, BankReconciliationLine, BankRule, Document, Payment,
                         PaymentAllocation, ProjectTransaction, TaxCode)
from journals.models import (BankDescriptionMapping, BankStatementUpload, InvoiceReceipt, JournalEntry,
                             JournalEntryLine, JournalSequence, Period)
from journals.signals import allow_reset
from payroll.models import Employee, PayrollLine, PayrollRun
from purchases.models import (BankTransactionCategorization, Bill, BillLine, BillPaymentLink, Expense,
                              ExpenseLine, Supplier)
from sales.models import CreditNote, Invoice, InvoiceLine

# Children before parents, so no PROTECT link blocks a delete.
TRANSACTIONAL = [
    InvoiceReceipt, BillPaymentLink, BankTransactionCategorization,
    PaymentAllocation, Payment,
    BankReconciliationLine, BankReconciliation,
    ProjectTransaction, Document,
    ExpenseLine, Expense,
    BillLine, Bill,
    CreditNote, InvoiceLine, Invoice,
    PayrollLine, PayrollRun,
    JournalEntryLine, JournalEntry,
    JournalSequence, Period,
    BankStatementUpload, AuditLog,
]

# Old Manager.io code → PCGM code. Exact codes first, then the longest prefix.
OLD_EXACT = {
    "101001": chart.BANK_CIH300, "101002": chart.BANK_CIH600, "101003": chart.BANK_CIH600_EUR,
    "101004": chart.BANK_BP09,
    "120000": chart.RECEIVABLE, "200000": chart.PAYABLE, "210000": chart.TVA_MARGIN,
    "220000": chart.CNSS_PAYABLE, "230000": "4488", "240000": chart.CLIENT_ADVANCES,
    "300000": "1111", "310000": "1161",
    "420000": chart.REVENUE, "471000": chart.SUSPENSE, "471100": chart.EUR_UNEXCHANGED,
    "533500": chart.COST_TRANSPORT,   # flight tickets
    "533550": chart.COST_OTHER,       # visa
    "563900": chart.COST_ACTIVITIES,  # golf
    "572210": chart.SOCIAL_CHARGES,   # CNSS
    "592301": "61448",                # ONMT
    "592302": "61254",                # office supplies
    "592303": "61312",                # rent
    "592304": "61348",                # insurance
    "592305": "61455", "592308": "61455",  # Maroc Telecom, Inwi
    "592306": "61251",                # Amendis (water, electricity)
    "592307": chart.FEES,             # accountant
    "598000": chart.INTEREST,
    "598501": "61612",                # patente
    "598503": chart.TVA_DUE,
}
OLD_PREFIX = [
    ("100", chart.CASH),
    ("510", chart.COST_OTHER), ("513", chart.COST_OTHER),
    ("514", chart.COST_ACTIVITIES),
    ("523", chart.COST_HOTELS),
    ("5331", chart.COST_RESTAURANTS),
    ("5336", chart.COST_GUIDES), ("5436", chart.COST_GUIDES),
    ("5538", chart.COST_TRANSPORT),
    ("5722", chart.SALARIES),
    ("5980", chart.BANK_FEES),
    ("5985", "61678"),
]


def pcgm_for(old_code):
    """The PCGM code an old account's links move to, or None."""
    if old_code in OLD_EXACT:
        return OLD_EXACT[old_code]
    for prefix, new in sorted(OLD_PREFIX, key=lambda p: -len(p[0])):
        if old_code.startswith(prefix):
            return new
    return None


class Command(BaseCommand):
    help = "Delete all numbers and move the books to the PCGM chart (needs --confirm)"

    def add_arguments(self, parser):
        parser.add_argument("--confirm", action="store_true", help="Actually delete; without it nothing changes")

    def handle(self, *args, **options):
        confirm = options["confirm"]
        with transaction.atomic(), allow_reset():
            self.run()
            if not confirm:
                transaction.set_rollback(True)
                self.stdout.write(self.style.WARNING("Dry run — nothing changed. Run with --confirm to do it."))
            else:
                self.stdout.write(self.style.SUCCESS("Done. The books start empty on the PCGM chart."))

    def run(self):
        out = self.stdout.write

        out("1. Deleting numbers")
        InvoiceReceipt.objects.update(exchanged_from=None)
        for model in TRANSACTIONAL:
            n, _ = model.objects.all().delete()
            out(f"   {model.__name__}: {n} rows")

        out("2. Seeding PCGM")
        out(f"   {seed_chart()} new accounts")
        keep = {code for code, *_ in all_accounts()}
        by_code = {a.code: a for a in Account.objects.filter(code__in=keep)}

        def target(account):
            if account is None or account.code in keep:
                return account
            new = pcgm_for(account.code)
            return by_code.get(new) if new else None

        out("3. Moving master data to PCGM accounts")
        moved = cleared = 0
        for s in Supplier.objects.select_related("default_account"):
            new = target(s.default_account)
            if new != s.default_account:
                s.default_account = new
                s.save(update_fields=["default_account"])
                moved += new is not None
                cleared += new is None
        out(f"   Suppliers: {moved} moved, {cleared} cleared")

        n = 0
        for e in Employee.objects.select_related("salary_account"):
            new = target(e.salary_account) or by_code[chart.SALARIES]
            if new != e.salary_account:
                e.salary_account = new
                e.save(update_fields=["salary_account"])
                n += 1
        out(f"   Employees: {n} moved")

        n = 0
        for t in TaxCode.objects.select_related("account"):
            if t.account.code in keep:
                continue
            t.account = by_code[chart.TVA_RECOVERABLE if t.type == "purchase" else chart.TVA_MARGIN]
            t.save(update_fields=["account"])
            n += 1
        out(f"   Tax codes: {n} moved")

        for model in (SupplierAccountMapping, BankRule, BankDescriptionMapping):
            moved = dropped = 0
            for row in model.objects.select_related("account"):
                new = target(row.account)
                if new is None:
                    row.delete()
                    dropped += 1
                elif new != row.account:
                    row.account = new
                    row.save(update_fields=["account"])
                    moved += 1
            out(f"   {model.__name__}: {moved} moved, {dropped} deleted")

        out("4. Deleting old accounts")
        old = Account.objects.exclude(code__in=keep)
        old.update(parent=None)
        n, _ = old.delete()
        out(f"   {n} old accounts deleted, {Account.objects.count()} PCGM accounts")

        n = FiscalYear.objects.filter(is_closed=True).update(is_closed=False)
        _, created = FiscalYear.objects.get_or_create(
            start_date=date(2026, 1, 1), defaults={"name": "2026", "end_date": date(2026, 12, 31)})
        out(f"5. Fiscal years reopened: {n}{', 2026 created' if created else ''}")
