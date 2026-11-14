"""Eksportér alt for én virksomhed (ved ophør, kurator eller myndigheder).

Én zip med:
  saft/SAF-T_<år>.xml    SAF-T Financial DK 2.1 pr. regnskabsår (alle posteringer)
  saldobalance_<år>.csv  saldobalance pr. regnskabsår
  bilag/<nr>_<navn>      alle bilag, som de blev uploadet
  bilag.csv              bilagsliste med SHA-256 og kobling til postering/faktura/regning
  audit_log.json         kundens hash-kædede audit-log og resultatet af kædekontrollen
  MANIFEST.txt           SHA-256 af hver fil i zip'en

Bygges i kundens skema til en midlertidig fil, så store bilagsmængder ikke
ligger i hukommelsen.
"""

import csv
import hashlib
import io
import json
import os
import tempfile
import zipfile
from datetime import date

from django.utils import timezone
from django_tenants.utils import schema_context


def _years(first, last, start_month):
    """(start, slut) for hvert regnskabsår, der dækker first..last."""
    y = first.year if first.month >= start_month else first.year - 1
    out = []
    while True:
        start = date(y, start_month, 1)
        end = date(y + 1, start_month, 1) if start_month > 1 else date(y + 1, 1, 1)
        end = date.fromordinal(end.toordinal() - 1)
        out.append((start, end))
        if end >= last:
            return out
        y += 1


def _label(start, end):
    return str(end.year) if (start.month, start.day) == (1, 1) else f"{start.year}-{end.year}"


def build_export(client, user=None):
    """Returnerer stien til en midlertidig zip-fil (kalderen sletter den)."""
    fd, path = tempfile.mkstemp(prefix=f"eksport_{client.slug}_", suffix=".zip")
    os.close(fd)
    manifest = []

    with schema_context(client.schema_name), zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as zf:
        def put(name, data):
            if isinstance(data, str):
                data = data.encode("utf-8")
            zf.writestr(name, data)
            manifest.append((hashlib.sha256(data).hexdigest(), name))

        from core.audit import verify_chain
        from core.models import AuditLog, Document
        from journals.models import JournalEntry

        dates = JournalEntry.objects.filter(is_posted=True).order_by("date").values_list("date", flat=True)
        first, last = dates.first(), JournalEntry.objects.filter(is_posted=True).order_by("-date") \
            .values_list("date", flat=True).first()
        if first:
            from saft.export import build_saft
            for start, end in _years(first, last, client.fiscal_year_start_month or 1):
                xml, _stats = build_saft(start, end, "2.1", user)
                put(f"saft/SAF-T_{_label(start, end)}.xml", xml)
                put(f"saldobalance_{_label(start, end)}.csv", _trial_balance_csv(start, end))

        rows = io.StringIO()
        w = csv.writer(rows, delimiter=";")
        w.writerow(["nummer", "filnavn", "fil_i_eksporten", "sha256", "bytes", "uploadet",
                    "postering", "faktura", "regning", "udgift"])
        for doc in Document.objects.all().order_by("created_at" if hasattr(Document, "created_at") else "id"):
            number = getattr(doc, "number", "") or ""
            safe = os.path.basename(doc.filename or (doc.file.name if doc.file else "fil"))
            arcname = f"bilag/{number or str(doc.id)[:8]}_{safe}"
            if doc.file:
                try:
                    with doc.file.open("rb") as fh:
                        content = fh.read()
                    put(arcname, content)
                except (FileNotFoundError, OSError):
                    arcname = f"MANGLER: {safe}"
            w.writerow([number, doc.filename, arcname, doc.sha256, doc.size,
                        getattr(doc, "created_at", "") or "",
                        _ref(doc, "journal_entry", "entry_number"), _ref(doc, "invoice", "invoice_number"),
                        _ref(doc, "bill", "bill_number"), _ref(doc, "expense", "id")])
        put("bilag.csv", "﻿" + rows.getvalue())

        logs = [{"seq": a.seq, "timestamp": a.timestamp.isoformat(), "user_id": a.user_id, "action": a.action,
                 "model": a.model_name, "record_id": a.record_id, "changes": a.changes, "ip": a.ip_address,
                 "prev_hash": a.prev_hash, "hash": a.hash}
                for a in AuditLog.objects.exclude(seq=None).order_by("seq").iterator()]
        put("audit_log.json", json.dumps({"chain": verify_chain(), "entries": logs}, ensure_ascii=False,
                                         indent=1, default=str))

        put("LÆS_MIG.txt", (
            f"Eksport af regnskabsmateriale for {client.name} (CVR {client.cvr or '–'})\n"
            f"Dannet {timezone.localtime():%d-%m-%Y %H:%M} af {getattr(user, 'username', 'system')}.\n\n"
            "SAF-T-filerne følger Erhvervsstyrelsens skema (Danish SAF-T Financial 2.1) og kan læses af\n"
            "andre bogføringssystemer. Bilagene er de oprindelige filer; SHA-256 i bilag.csv kan bruges\n"
            "til at kontrollere, at de ikke er ændret. MANIFEST.txt har SHA-256 for alle filer.\n"
            "Materialet skal opbevares i 5 år fra udgangen af det regnskabsår, det vedrører\n"
            "(Bogføringsloven § 10).\n"))
        zf.writestr("MANIFEST.txt", "\n".join(f"{h}  {n}" for h, n in manifest) + "\n")
    return path


def _ref(doc, field, attr):
    obj = getattr(doc, field, None) if hasattr(doc, field) else None
    return str(getattr(obj, attr, "") or "") if obj is not None else ""


def _trial_balance_csv(start, end):
    """Saldobalance (primo, bevægelser, ultimo) i DKK for perioden."""
    from django.db.models import Q, Sum
    from accounts.models import Account
    from journals.models import JournalEntryLine

    posted = JournalEntryLine.objects.filter(journal_entry__is_posted=True)
    before = {r["account_id"]: (r["d"] or 0) - (r["c"] or 0) for r in posted.filter(
        journal_entry__date__lt=start).values("account_id").annotate(d=Sum("debit"), c=Sum("credit"))}
    during = {r["account_id"]: (r["d"] or 0, r["c"] or 0) for r in posted.filter(
        journal_entry__date__gte=start, journal_entry__date__lte=end).values("account_id")
        .annotate(d=Sum("debit"), c=Sum("credit"))}
    out = io.StringIO()
    w = csv.writer(out, delimiter=";")
    w.writerow(["konto", "navn", "primo", "debet", "kredit", "ultimo"])
    fmt = lambda v: f"{v:.2f}".replace(".", ",")  # noqa: E731
    for a in Account.objects.filter(Q(id__in=before) | Q(id__in=during)).order_by("code"):
        p = before.get(a.id, 0)
        d, c = during.get(a.id, (0, 0))
        w.writerow([a.code, a.name, fmt(p), fmt(d), fmt(c), fmt(p + d - c)])
    return "﻿" + out.getvalue()
