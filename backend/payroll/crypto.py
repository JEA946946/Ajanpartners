"""Krypteret felt til CPR-numre (Fernet, nøgle fra settings.FIELD_ENCRYPTION_KEY).

Nøglen skal i produktion komme fra miljøet og opbevares uden for databasen og
backuppen; mistes den, kan CPR-numrene ikke læses igen. Flere nøgler (rotation)
kan angives kommasepareret – den første bruges til kryptering.
"""

import re

from cryptography.fernet import Fernet, InvalidToken, MultiFernet
from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models


def _fernet():
    keys = [k.strip() for k in str(settings.FIELD_ENCRYPTION_KEY).split(",") if k.strip()]
    return MultiFernet([Fernet(k.encode()) for k in keys])


def encrypt(value):
    return _fernet().encrypt(value.encode()).decode()


def decrypt(token):
    try:
        return _fernet().decrypt(token.encode()).decode()
    except InvalidToken:
        raise ValueError("CPR-nummeret kan ikke dekrypteres (forkert FIELD_ENCRYPTION_KEY?)") from None


class EncryptedTextField(models.TextField):
    """Gemmer værdien krypteret; Python-siden ser klarteksten."""

    def from_db_value(self, value, expression, connection):
        if not value:
            return value
        return decrypt(value)

    def get_prep_value(self, value):
        value = super().get_prep_value(value)
        if not value:
            return value
        return encrypt(value)


CPR_RE = re.compile(r"^(\d{6})-?(\d{4})$")


def normalize_cpr(value):
    """'010190-1234' / '0101901234' → '0101901234'. Rejser ValidationError ved fejl."""
    value = (value or "").strip().replace(" ", "")
    m = CPR_RE.match(value)
    if not m:
        raise ValidationError("CPR-nummeret skal have 10 cifre (DDMMÅÅ-XXXX).")
    digits = m.group(1) + m.group(2)
    dd, mm = int(digits[:2]), int(digits[2:4])
    if not (1 <= dd <= 31 and 1 <= mm <= 12):
        raise ValidationError("CPR-nummeret har en ugyldig dato.")
    return digits


def mask_cpr(digits):
    return f"XXXXXX-{digits[-4:]}" if digits else ""
