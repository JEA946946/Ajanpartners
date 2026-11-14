"""The audit log is append-only in the database: UPDATE and DELETE are refused
unless reset_bookkeeping set bookkeeping.allow_reset."""

from django.db import migrations

LOCK_SQL = """
CREATE OR REPLACE FUNCTION bk_audit_append_only() RETURNS trigger AS $$
BEGIN
    IF current_setting('bookkeeping.allow_reset', true) = 'on' THEN
        RETURN COALESCE(NEW, OLD);
    END IF;
    RAISE EXCEPTION 'The audit log is append-only';
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER bk_audit_lock BEFORE UPDATE OR DELETE ON audit_logs
    FOR EACH ROW EXECUTE FUNCTION bk_audit_append_only();
"""

UNLOCK_SQL = """
DROP TRIGGER IF EXISTS bk_audit_lock ON audit_logs;
DROP FUNCTION IF EXISTS bk_audit_append_only();
"""


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0010_document_fingerprint"),
    ]

    operations = [
        migrations.RunSQL(LOCK_SQL, UNLOCK_SQL),
    ]
