"""Låsetriggeren sammenligner også de nye kolonner amount_currency og vat_code,
så kun udligningsfelterne kan ændres på en valideret linje."""

from django.db import migrations

LOCK_SQL = """
CREATE OR REPLACE FUNCTION bk_refuse_validated() RETURNS trigger AS $$
DECLARE
    entry_id uuid;
BEGIN
    IF current_setting('bookkeeping.allow_reset', true) = 'on' THEN
        RETURN COALESCE(NEW, OLD);
    END IF;
    IF TG_TABLE_NAME = 'journal_entries' THEN
        IF OLD.validated_at IS NOT NULL THEN
            RAISE EXCEPTION 'Entry % is validated and cannot be changed', OLD.entry_number;
        END IF;
        RETURN COALESCE(NEW, OLD);
    END IF;
    -- Udligning af en valideret linje: alt andet end udligningskolonnerne uændret.
    IF TG_OP = 'UPDATE' AND
       ROW(NEW.journal_entry_id, NEW.account_id, NEW.debit, NEW.credit, NEW.currency, NEW.exchange_rate,
           NEW.amount_currency, NEW.base_debit, NEW.base_credit, NEW.vat_code, NEW.description, NEW.line_no,
           NEW.partner_type, NEW.partner_id, NEW.partner_name)
       IS NOT DISTINCT FROM
       ROW(OLD.journal_entry_id, OLD.account_id, OLD.debit, OLD.credit, OLD.currency, OLD.exchange_rate,
           OLD.amount_currency, OLD.base_debit, OLD.base_credit, OLD.vat_code, OLD.description, OLD.line_no,
           OLD.partner_type, OLD.partner_id, OLD.partner_name) THEN
        RETURN NEW;
    END IF;
    IF TG_OP = 'INSERT' THEN entry_id := NEW.journal_entry_id; ELSE entry_id := OLD.journal_entry_id; END IF;
    IF EXISTS (SELECT 1 FROM journal_entries WHERE id = entry_id AND validated_at IS NOT NULL) THEN
        RAISE EXCEPTION 'Lines of a validated entry cannot be changed';
    END IF;
    IF TG_OP = 'UPDATE' AND NEW.journal_entry_id <> OLD.journal_entry_id
       AND EXISTS (SELECT 1 FROM journal_entries WHERE id = NEW.journal_entry_id AND validated_at IS NOT NULL) THEN
        RAISE EXCEPTION 'Lines of a validated entry cannot be changed';
    END IF;
    RETURN COALESCE(NEW, OLD);
END;
$$ LANGUAGE plpgsql;
"""


class Migration(migrations.Migration):

    dependencies = [
        ("journals", "0016_danish_ledger"),
    ]

    operations = [
        migrations.RunSQL(LOCK_SQL, migrations.RunSQL.noop),
    ]
