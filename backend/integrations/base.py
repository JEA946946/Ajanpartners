"""Fælles mekanik for adaptere til eksterne tjenester.

Hver integration har et interface, en mock-implementering (default) og en eller
flere rigtige klienter. Hvilken der bruges, vælges med en indstilling i
settings eller miljøet, fx ``CVR_PROVIDER=cvrapi``. Uden indstilling bruges
mock, så alt kan køres og testes uden aftaler med tredjeparter.

Rigtige klienter, der kræver en aftale, som endnu ikke er på plads, er stubs og
rejser ``NotImplementedError`` med en forklaring på, hvad der mangler.
"""

import os

from django.conf import settings

# Generisk User-Agent til udgående kald. Må ikke indeholde personoplysninger
# (navne, e-mails, telefonnumre) – kun produkt og version.
DEFAULT_USER_AGENT = "bogforingssystem-integration/1.0"


class IntegrationError(Exception):
    """Fejl fra en ekstern tjeneste, som kan vises for brugeren."""


class AgreementRequired(NotImplementedError):
    """Den rigtige klient kræver en aftale/certificering, der ikke er på plads."""

    def __init__(self, service, requirement):
        self.service = service
        self.requirement = requirement
        super().__init__(f"{service}: ikke slået til. Kræver: {requirement}")


def setting(name, default=""):
    """Læs en indstilling fra settings og derefter miljøet."""
    value = getattr(settings, name, None)
    if value in (None, ""):
        value = os.environ.get(name, default)
    return value


def user_agent():
    return setting("INTEGRATIONS_USER_AGENT", DEFAULT_USER_AGENT)


def select(setting_name, registry, default="mock"):
    """Instans af den adapter, indstillingen peger på."""
    key = (setting(setting_name, default) or default).strip().lower()
    try:
        cls = registry[key]
    except KeyError:
        raise IntegrationError(
            f"Ukendt værdi {key!r} for {setting_name}. Gyldige: {', '.join(sorted(registry))}.") from None
    return cls()
