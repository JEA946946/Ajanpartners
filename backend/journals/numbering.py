"""Shared sequential document-number generator.

Replaces the ~8 copy-pasted `_next_*_number` helpers. Two bugs the old copies had:
  1. Lexical ordering — `order_by("-entry_number")` sorts strings, so after "JE-9999"
     the next max is "JE-9999" again ("JE-9999" > "JE-10000" as strings) → permanent
     collision. This computes the max by the NUMERIC suffix instead.
  2. `.count() + 1` variants re-issue a number after any row is deleted → collision.

Residual note: there is still a small read-then-insert race under true concurrency.
Callers that create inside `transaction.atomic()` and whose number column is UNIQUE
will surface a duplicate as an IntegrityError (retryable) rather than silently
double-issuing; low-concurrency SMB usage makes this rare.
"""

import re


def next_number(model, field, prefix, width=4):
    """Return the next number like ``PREFIX-0001`` for model.field.

    The next value is 1 + the maximum numeric suffix currently stored (so it survives
    both the >9999 lexical bug and mid-sequence deletions).
    """
    values = model.objects.values_list(field, flat=True)
    max_num = 0
    pat = re.compile(r"-(\d+)\s*$")
    for v in values:
        # Kun denne serie: et importeret nummer i en anden serie må ikke flytte den.
        if not v or not str(v).startswith(f"{prefix}-"):
            continue
        m = pat.search(str(v))
        if m:
            n = int(m.group(1))
            if n > max_num:
                max_num = n
    return f"{prefix}-{max_num + 1:0{width}d}"


def next_je_number(width=6):
    """Kladdenummer (KL-000001) for en ny postering. Det endelige nummer gives, når
    måneden lukkes (validated_number)."""
    from journals.models import JournalEntry
    return next_number(JournalEntry, "entry_number", "KL", width)


def validated_number(journal, year):
    """Næste nummer i journalens fortløbende serie for året, fx BANK-2026-00001.
    The caller holds transaction.atomic(); the sequence row is locked until commit."""
    from journals.models import JournalSequence
    JournalSequence.objects.get_or_create(journal=journal, year=year)
    seq = JournalSequence.objects.select_for_update().get(journal=journal, year=year)
    seq.last_number += 1
    seq.save(update_fields=["last_number"])
    return f"{journal.code}-{year}-{seq.last_number:05d}"
