"""Public-modeller for integrationer.

Kun bankkoblingerne har brug for at blive gemt: samtykket til at hente
kontooplysninger (PSD2/AIS) tilhører kunden, men administreres af systemet på
tværs af kunder (cron-jobbet fetch_bank_feeds går alle koblinger igennem).
Selve transaktionerne lægges i kundens eget skema som banklinjer.
"""

import uuid
from datetime import timedelta

from django.conf import settings
from django.db import models
from django.utils import timezone

CONSENT_DAYS = 180          # PSD2 RTS art. 10a: kunden skal forny samtykket hver 180. dag
RENEW_WARNING_DAYS = 14


class BankFeedConnection(models.Model):
    STATUS = [
        ("pending", "Afventer kundens samtykke i banken"),
        ("active", "Aktiv"),
        ("expired", "Samtykket er udløbet – skal fornyes"),
        ("revoked", "Afbrudt"),
        ("error", "Fejl"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    client = models.ForeignKey("tenancy.ClientCompany", on_delete=models.CASCADE, related_name="bank_feeds")
    provider = models.CharField(max_length=30)
    institution_id = models.CharField(max_length=100, blank=True, default="")
    institution_name = models.CharField(max_length=200, blank=True, default="")
    # accounts.Account.id i kundens skema (kan ikke være en FK på tværs af skemaer)
    bank_account_id = models.UUIDField()
    external_account_id = models.CharField(max_length=200, blank=True, default="")
    iban = models.CharField(max_length=34, blank=True, default="")
    consent_id = models.CharField(max_length=200, blank=True, default="")
    authorization_url = models.TextField(blank=True, default="")
    consent_granted_at = models.DateTimeField(null=True, blank=True)
    consent_expires_at = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS, default="pending")
    last_fetched_at = models.DateTimeField(null=True, blank=True)
    last_booked_date = models.DateField(null=True, blank=True)
    last_error = models.TextField(blank=True, default="")
    last_result = models.JSONField(default=dict, blank=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
                                   related_name="+")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "integrations_bank_feed_connections"
        ordering = ["client_id", "created_at"]

    def __str__(self):
        return f"{self.client_id} {self.institution_name} {self.iban or self.external_account_id}"

    def grant_consent(self, when=None):
        when = when or timezone.now()
        self.consent_granted_at = when
        self.consent_expires_at = when + timedelta(days=CONSENT_DAYS)
        self.status = "active"
        self.authorization_url = ""

    @property
    def consent_expired(self):
        return bool(self.consent_expires_at and self.consent_expires_at <= timezone.now())

    @property
    def renewal_due(self):
        return bool(self.consent_expires_at and
                    self.consent_expires_at <= timezone.now() + timedelta(days=RENEW_WARNING_DAYS))
