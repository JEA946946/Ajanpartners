"""A validated entry and its lines are never changed or deleted (Bogføringsloven).
The database trigger in migration 0013 enforces the same for raw SQL."""

from contextlib import contextmanager
from contextvars import ContextVar

from django.db import connection
from django.db.models.signals import pre_delete, pre_save
from django.dispatch import receiver

from .models import JournalEntry, JournalEntryLine, ValidatedEntryError


_RESETTING = ContextVar("bookkeeping_resetting", default=False)


@contextmanager
def allow_reset():
    """Only for reset_bookkeeping: lift the lock (here and in the trigger) for the
    current transaction."""
    token = _RESETTING.set(True)
    try:
        with connection.cursor() as cur:
            cur.execute("SET LOCAL bookkeeping.allow_reset = 'on'")
        yield
    finally:
        _RESETTING.reset(token)


def _refuse(entry_number):
    if _RESETTING.get():
        return
    raise ValidatedEntryError(
        f"Entry {entry_number} is validated (its month is closed) and cannot be changed. "
        "Correct it with a reversal entry in an open month.")


@receiver(pre_save, sender=JournalEntry)
def entry_pre_save(sender, instance, raw=False, **kwargs):
    if raw or instance._state.adding:
        return
    old = JournalEntry.objects.filter(pk=instance.pk).values_list("validated_at", "entry_number").first()
    if old and old[0]:
        _refuse(old[1])


@receiver(pre_delete, sender=JournalEntry)
def entry_pre_delete(sender, instance, **kwargs):
    if instance.validated_at:
        _refuse(instance.entry_number)


@receiver(pre_save, sender=JournalEntryLine)
@receiver(pre_delete, sender=JournalEntryLine)
def line_lock(sender, instance, raw=False, update_fields=None, **kwargs):
    if raw:
        return
    # Lettrage happens after the month is closed (a bill paid next month), so a
    # save of only the lettrage fields is allowed on a validated line.
    if update_fields is not None and set(update_fields) <= JournalEntryLine.LETTRAGE_FIELDS:
        return
    number = (JournalEntry.objects.filter(pk=instance.journal_entry_id, validated_at__isnull=False)
              .values_list("entry_number", flat=True).first())
    if number:
        _refuse(number)
