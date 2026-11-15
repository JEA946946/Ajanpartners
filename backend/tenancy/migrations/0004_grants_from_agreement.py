"""Revisorhusets adgang følger nu kundeaftalen: ventende anmodninger accepteres, kunder
under oprettelse bliver aktive, og udkast til betingelserne publiceres."""

from django.db import migrations
from django.utils import timezone


def forwards(apps, schema_editor):
    if schema_editor.connection.schema_name != "public":
        return
    AccessGrant = apps.get_model("tenancy", "AccessGrant")
    ClientCompany = apps.get_model("tenancy", "ClientCompany")
    TermsDocument = apps.get_model("tenancy", "TermsDocument")
    now = timezone.now()
    for g in AccessGrant.objects.filter(accepted_at__isnull=True, revoked_at__isnull=True):
        g.accepted_at = now
        g.accepted_by_id = g.requested_by_id
        g.request_note = (g.request_note + " – iht. kundeaftale").strip(" –")
        g.save(update_fields=["accepted_at", "accepted_by", "request_note"])
    ClientCompany.objects.filter(status="onboarding").update(status="active")

    import hashlib
    from tenancy.terms_drafts import DRAFTS, VERSION
    for kind, title, body in DRAFTS:
        if TermsDocument.objects.filter(kind=kind, published_at__isnull=False).exists():
            continue
        sha = hashlib.sha256(f"{kind}|{VERSION}|{title}|{body}".encode()).hexdigest()
        TermsDocument.objects.get_or_create(kind=kind, version=VERSION, defaults={
            "title": title, "body": body, "published_at": now, "sha256": sha})


class Migration(migrations.Migration):
    dependencies = [("tenancy", "0003_terms_and_agreement")]
    operations = [migrations.RunPython(forwards, migrations.RunPython.noop)]
