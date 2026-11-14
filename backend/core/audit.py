"""Audit-trail helper.

Lives in its own module so other apps (journals, purchases, sales, payroll,
accounts) can log actions without importing core.views (which pulls in every
core endpoint and their cross-app imports).

The log is hash-chained: row n stores sha256 of its own content plus the hash
of row n-1. Rows are written one at a time under an advisory lock, and
verify_chain() recomputes the chain to show nothing was changed or removed.
"""

import hashlib
import json
from datetime import timezone as dt_timezone

from django.db import connection, transaction

CHAIN_LOCK = 7_461_001  # pg_advisory_xact_lock key for writing the chain


def _plain(changes):
    """The changes as stored in JSON (Decimals and dates as text)."""
    return json.loads(json.dumps(changes or {}, default=str))


def row_hash(seq, prev_hash, timestamp, user_id, action, model_name, record_id, changes, ip):
    payload = json.dumps(
        [seq, prev_hash, timestamp.astimezone(dt_timezone.utc).isoformat(), user_id, action, model_name,
         record_id, changes, ip],
        sort_keys=True, separators=(",", ":"), default=str,
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _hash_of(log):
    return row_hash(log.seq, log.prev_hash, log.timestamp, log.user_id, log.action, log.model_name,
                    log.record_id, log.changes, log.ip_address)


def log_action(user, action, model_name, record_id, changes=None, ip=None):
    """Append an audit log entry to the chain."""
    from django.utils import timezone
    from core.models import AuditLog

    from tenancy.context import current_access

    access = current_access.get()
    if access is not None and access.is_firm:
        # Medarbejder fra revisorhuset: står i hash-kæden sammen med ændringen.
        changes = {**(changes or {}), "_via": "firm", "_firm_role": access.staff.role,
                   "_grant_scope": access.grant.scope if access.grant else ""}
    with transaction.atomic():
        with connection.cursor() as cur:
            # One chain per client schema: lock on the schema, not globally.
            cur.execute("SELECT pg_advisory_xact_lock(%s, hashtext(current_schema()))", [CHAIN_LOCK])
        last = AuditLog.objects.exclude(seq=None).order_by("-seq").values("seq", "hash").first()
        log = AuditLog(
            user=user if user and user.is_authenticated else None,
            action=action[:10],
            model_name=model_name,
            record_id=str(record_id),
            changes=_plain(changes),
            ip_address=ip,
            timestamp=timezone.now(),
            seq=(last["seq"] if last else 0) + 1,
            prev_hash=last["hash"] if last else "",
        )
        log.hash = _hash_of(log)
        log.save()
        return log


def verify_chain():
    """Recompute the chain. Returns {"ok", "count", "broken_at"} where broken_at is
    the first sequence number whose row was changed, removed or reordered."""
    from core.models import AuditLog

    prev, expected_seq, count = "", 1, 0
    for log in AuditLog.objects.exclude(seq=None).order_by("seq").iterator():
        count += 1
        if log.seq != expected_seq or log.prev_hash != prev or _hash_of(log) != log.hash:
            return {"ok": False, "count": count, "broken_at": log.seq}
        prev, expected_seq = log.hash, expected_seq + 1
    return {"ok": True, "count": count, "broken_at": None}
