"""BillPaymentLink.clearing_entry — the DR AP / CR Client-Funds entry posted when a
bank line is matched to a bill.

Before this, matching only bumped the bill's paid_amount memo: the import had put the
money on 240000 and approval had put the debt on 200000, and nothing ever cleared
either — the balance sheet overstated both, permanently. The FK lets the un-reconcile
endpoint find and remove the clearing entry again.
"""

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("purchases", "0008_banktransactioncategorization"),
        ("journals", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="billpaymentlink",
            name="clearing_entry",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="bill_clearing_links",
                to="journals.journalentry",
            ),
        ),
    ]
