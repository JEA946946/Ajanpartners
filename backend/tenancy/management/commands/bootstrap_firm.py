"""Opret public-tenant, pakker, revisorhusets stamdata og (valgfrit) den første partner.

    python manage.py bootstrap_firm --firm-name "Ajan & Partners" --cvr 46922514 \
        --address "Vej 1" --zip-code 1000 --city "København K" --email info@ajanpartners.dk --phone "+45 12 34 56 78" \
        --partner-email jamal@ajanpartners.dk --partner-password ...

Kan køres igen: kun de stamdata, der angives, opdateres.
"""

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError

from integrations.cvr import normalize_cvr
from integrations.base import IntegrationError
from tenancy.models import Firm, FirmStaff
from tenancy.services import ensure_public_tenant

FIRM_FIELDS = {"firm_name": "name", "cvr": "cvr", "address": "address", "zip_code": "zip_code", "city": "city",
               "email": "email", "phone": "phone", "website": "website"}


class Command(BaseCommand):
    help = "Opret public-tenant, standardpakker, revisorhusets stamdata og den første partner i Ajan Partners."

    def add_arguments(self, parser):
        parser.add_argument("--domain", default="localhost")
        parser.add_argument("--firm-name", help="Revisorhusets navn")
        parser.add_argument("--cvr", help="Revisorhusets CVR-nummer (8 cifre)")
        parser.add_argument("--address", help="Vej og nr.")
        parser.add_argument("--zip-code", help="Postnr.")
        parser.add_argument("--city", help="By")
        parser.add_argument("--website", help="Hjemmeside")
        parser.add_argument("--email", help="Revisorhusets e-mail")
        parser.add_argument("--phone", help="Revisorhusets telefon")
        parser.add_argument("--partner-email")
        parser.add_argument("--partner-password")
        parser.add_argument("--partner-name", default="")

    def handle(self, *args, **opts):
        values = {field: opts[arg].strip() for arg, field in FIRM_FIELDS.items() if opts.get(arg) is not None}
        if "cvr" in values:
            try:
                values["cvr"] = normalize_cvr(values["cvr"])
            except IntegrationError as e:
                raise CommandError(f"--cvr: {e}") from e

        ensure_public_tenant(opts["domain"])
        firm = Firm.current()
        for field, value in values.items():
            setattr(firm, field, value)
        if values:
            firm.save(update_fields=list(values))
        self.stdout.write(f"Firma: {firm.name}" + (f" (CVR {firm.cvr})" if firm.cvr else " – CVR ikke angivet"))

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
