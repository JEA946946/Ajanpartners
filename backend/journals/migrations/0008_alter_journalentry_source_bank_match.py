"""Add the bank_match source: the clearing entry (DR AP / CR Client Funds) posted
when a bank transaction is matched to a bill. State-only (choices), no SQL."""

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("journals", "0007_alter_journalentry_source"),
    ]

    operations = [
        migrations.AlterField(
            model_name="journalentry",
            name="source",
            field=models.CharField(
                choices=[
                    ("manual", "Manual"),
                    ("cmr_invoice", "CMR Invoice"),
                    ("cmr_payment", "CMR Payment"),
                    ("invoice", "Invoice"),
                    ("credit_note", "Credit Note"),
                    ("expense", "Expense"),
                    ("bank", "Bank"),
                    ("margin_recognition", "Margin Recognition"),
                    ("tva_margin", "TVA on Margin"),
                    ("payroll", "Payroll"),
                    ("reclass", "Reclassification"),
                    ("bank_match", "Bank Match"),
                ],
                default="manual",
                max_length=20,
            ),
        ),
    ]
