"""The journal is required; validated entries are locked in the database too.

The trigger refuses UPDATE/DELETE of a validated entry and any change to its
lines, unless the transaction set `bookkeeping.allow_reset` (reset_bookkeeping).
"""

import django.db.models.deletion
from django.db import migrations, models

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

CREATE TRIGGER bk_entries_lock BEFORE UPDATE OR DELETE ON journal_entries
    FOR EACH ROW EXECUTE FUNCTION bk_refuse_validated();
CREATE TRIGGER bk_lines_lock BEFORE INSERT OR UPDATE OR DELETE ON journal_entry_lines
    FOR EACH ROW EXECUTE FUNCTION bk_refuse_validated();
"""

UNLOCK_SQL = """
DROP TRIGGER IF EXISTS bk_lines_lock ON journal_entry_lines;
DROP TRIGGER IF EXISTS bk_entries_lock ON journal_entries;
DROP FUNCTION IF EXISTS bk_refuse_validated();
"""


class Migration(migrations.Migration):

    dependencies = [
        ("journals", "0012_assign_journals"),
    ]

    operations = [
        migrations.AlterField(
            model_name="journalentry",
            name="journal",
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="entries",
                                    to="journals.journal"),
        ),
        migrations.RunSQL(LOCK_SQL, UNLOCK_SQL),
    ]
