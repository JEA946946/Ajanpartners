from django.contrib import admin

from .models import AccessGrant, ClientCompany, ClientMembership, Firm, FirmAuditLog, FirmStaff, Package

for model in (Firm, Package, ClientCompany, ClientMembership, FirmStaff, AccessGrant, FirmAuditLog):
    admin.site.register(model)
