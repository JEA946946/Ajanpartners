"""Create the journals and put every existing entry in one."""

from django.db import migrations


def assign_journals(apps, schema_editor):
    """Create the journals and put every existing entry in one: a bank line or a
    paid expense in the journal of its bank or cash account, the rest by source."""
    from journals.journal_for import JOURNALS, MISC, SOURCE_JOURNAL

    Account = apps.get_model("accounts", "Account")
    Journal = apps.get_model("journals", "Journal")
    JournalEntry = apps.get_model("journals", "JournalEntry")
    JournalEntryLine = apps.get_model("journals", "JournalEntryLine")

    for code, name, type_, account_code, currency in JOURNALS:
        account = Account.objects.filter(code=account_code).first() if account_code else None
        Journal.objects.get_or_create(code=code, defaults={
            "name": name, "type": type_, "account": account, "currency": currency})
    by_code = {j.code: j for j in Journal.objects.all()}
    by_account = {j.account_id: j for j in by_code.values() if j.account_id}

    for entry in JournalEntry.objects.filter(journal__isnull=True):
        journal = None
        if entry.source in ("bank", "expense"):
            for account_id in JournalEntryLine.objects.filter(journal_entry=entry).values_list("account_id", flat=True):
                if account_id in by_account:
                    journal = by_account[account_id]
                    break
        if journal is None:
            journal = by_code[SOURCE_JOURNAL.get(entry.source, MISC)]
        entry.journal = journal
        entry.piece_number = entry.piece_number or entry.reference[:100]
        entry.save(update_fields=["journal", "piece_number"])


class Migration(migrations.Migration):

    dependencies = [
        ("journals", "0011_journals_and_validation"),
        ("accounts", "0002_supplieraccountmapping"),
    ]

    operations = [
        migrations.RunPython(assign_journals, migrations.RunPython.noop),
    ]
