"""Chain the audit rows written before the chain existed."""

from django.db import migrations


def chain_existing(apps, schema_editor):
    from core.audit import _plain, row_hash

    AuditLog = apps.get_model("core", "AuditLog")
    prev, seq = "", 0
    for log in AuditLog.objects.filter(seq=None).order_by("timestamp", "id"):
        seq += 1
        log.changes = _plain(log.changes)
        log.seq, log.prev_hash = seq, prev
        log.hash = row_hash(seq, prev, log.timestamp, log.user_id, log.action, log.model_name,
                            log.record_id, log.changes, log.ip_address)
        log.save(update_fields=["seq", "prev_hash", "hash", "changes"])
        prev = log.hash


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0008_audit_chain"),
    ]

    operations = [
        migrations.RunPython(chain_existing, migrations.RunPython.noop),
    ]
