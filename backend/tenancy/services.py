"""Oprettelse af kunder, pakker og adgange."""

import re

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.db import transaction
from django.utils import timezone
from django.utils.text import slugify
from django_tenants.utils import schema_context

from .features import DEFAULT_PACKAGES
from .models import AccessGrant, ClientCompany, ClientMembership, Domain, Firm, Package

User = get_user_model()


def seed_packages():
    """Opret de standardpakker, der mangler. Ændrer aldrig eksisterende pakker."""
    created = 0
    for p in DEFAULT_PACKAGES:
        _, new = Package.objects.get_or_create(code=p["code"], defaults={
            "name": p["name"], "description": p["description"], "order": p["order"],
            "features": p["features"], "limits": p["limits"],
        })
        created += new
    return created


def ensure_public_tenant(domain="localhost"):
    """django-tenants kræver en tenant for public-skemaet."""
    seed_packages()
    firm = Firm.current()
    public = ClientCompany.objects.filter(schema_name="public").first()
    if public is None:
        public = ClientCompany(schema_name="public", slug="public", name=firm.name, firm=firm,
                               package=Package.objects.order_by("-order").first(), status="active")
        public.auto_create_schema = False
        public.save()
    Domain.objects.get_or_create(domain=domain, defaults={"tenant": public, "is_primary": True})
    return public


def unique_slug(name):
    base = slugify(name)[:40] or "kunde"
    slug, n = base, 2
    while ClientCompany.objects.filter(slug=slug).exists():
        slug, n = f"{base}-{n}", n + 1
    return slug


def schema_for(slug):
    return "c_" + re.sub(r"[^a-z0-9_]", "_", slug.lower())[:55]


def seed_client_books(client):
    """Kontoplan, momskoder og journaler i kundens skema."""
    with schema_context(client.schema_name):
        call_command("seed_accounts", template=client.chart_template, verbosity=0)
        from core.models import CompanySettings
        settings_obj = CompanySettings.objects.first() or CompanySettings()
        settings_obj.company_name = client.name
        settings_obj.tax_id = client.cvr
        settings_obj.address = client.address
        settings_obj.city = client.city
        settings_obj.email = client.email
        settings_obj.phone = client.phone
        settings_obj.country = "Danmark"
        settings_obj.currency = "DKK"
        settings_obj.fiscal_year_start_month = client.fiscal_year_start_month
        settings_obj.save()


def create_client(*, name, package_code="standard", created_by=None, grant_scope="bookkeeping",
                  owner_email="", owner_name="", **fields):
    """Opret en kunde med eget skema, kontoplan og en anmodning om revisoradgang.

    Adgangen er en anmodning, indtil kunden accepterer den i onboarding. Uden en
    ejer (owner_email) kan ingen acceptere, så huset kan intet se endnu – det er
    bevidst: kunden ejer sine bøger.
    """
    firm = Firm.current()
    package = Package.objects.get(code=package_code)
    slug = fields.pop("slug", None) or unique_slug(name)
    client = ClientCompany(firm=firm, slug=slug, schema_name=schema_for(slug), name=name,
                           package=package, **fields)
    client.save()  # opretter og migrerer skemaet (auto_create_schema)
    seed_client_books(client)
    with transaction.atomic():
        AccessGrant.objects.create(client=client, firm=firm, scope=grant_scope, requested_by=created_by,
                                   request_note="Adgang til at levere bogføring og regnskab.")
        owner = None
        if owner_email:
            owner = invite_user(client, owner_email, owner_name, role="admin")
    return client, owner


def invite_user(client, email, name="", role="admin"):
    """Opret (eller find) en bruger og giv den adgang til kunden. Returnerer
    (user, midlertidig_adgangskode eller None for en eksisterende bruger)."""
    email = email.strip().lower()
    user = User.objects.filter(email__iexact=email).first()
    temp_password = None
    if user is None:
        first, _, last = (name or "").partition(" ")
        temp_password = User.objects.make_random_password(length=14) if hasattr(
            User.objects, "make_random_password") else _random_password()
        user = User.objects.create_user(username=email, email=email, password=temp_password,
                                        first_name=first, last_name=last)
    ClientMembership.objects.update_or_create(user=user, client=client,
                                              defaults={"role": role, "is_active": True})
    return user, temp_password


def _random_password(length=14):
    import secrets
    import string
    alphabet = string.ascii_letters + string.digits
    return "".join(secrets.choice(alphabet) for _ in range(length))


def accept_grant(grant, user):
    grant.accepted_at = timezone.now()
    grant.accepted_by = user
    grant.save(update_fields=["accepted_at", "accepted_by"])
    if grant.client.status == "onboarding":
        grant.client.status = "active"
        grant.client.save(update_fields=["status"])
    return grant


def revoke_grant(grant, user):
    grant.revoked_at = timezone.now()
    grant.revoked_by = user
    grant.save(update_fields=["revoked_at", "revoked_by"])
    return grant


def archive_client(client):
    """Kunden ophører: bøgerne bliver read-only og gemmes i 5 år (Bogføringsloven § 10)."""
    today = timezone.localdate()
    client.status = "archived"
    client.archived_at = timezone.now()
    client.retain_until = today.replace(year=today.year + 6, month=1, day=1)
    client.save(update_fields=["status", "archived_at", "retain_until"])
    return client
