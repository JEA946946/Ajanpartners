"""Opret public-tenant, pakker og (valgfrit) den første partner.

    python manage.py bootstrap_firm --partner-email jamal@ajanpartners.dk --partner-password ...
"""

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

from tenancy.models import Firm, FirmStaff
from tenancy.services import ensure_public_tenant


class Command(BaseCommand):
    help = "Opret public-tenant, standardpakker og den første partner i Ajan Partners."

    def add_arguments(self, parser):
        parser.add_argument("--domain", default="localhost")
        parser.add_argument("--partner-email")
        parser.add_argument("--partner-password")
        parser.add_argument("--partner-name", default="")

    def handle(self, *args, **opts):
        ensure_public_tenant(opts["domain"])
        firm = Firm.current()
        self.stdout.write(f"Firma: {firm.name}")
        email = opts.get("partner_email")
        if email:
            User = get_user_model()
            user = User.objects.filter(email__iexact=email).first()
            if user is None:
                first, _, last = opts["partner_name"].partition(" ")
                user = User.objects.create_user(username=email.lower(), email=email.lower(),
                                                password=opts.get("partner_password") or None,
                                                first_name=first, last_name=last)
            FirmStaff.objects.update_or_create(user=user, defaults={"firm": firm, "role": "partner"})
            self.stdout.write(f"Partner: {user.username}")
