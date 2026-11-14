from django.contrib import admin

from .models import (
    TaxCode, Payment, PaymentAllocation, BankRule,
    BankReconciliation, BankReconciliationLine, Project,
    ProjectTransaction, Document, AuditLog, CompanySettings, UserRole,
)

admin.site.register(TaxCode)
admin.site.register(Payment)
admin.site.register(PaymentAllocation)
admin.site.register(BankRule)
admin.site.register(BankReconciliation)
admin.site.register(BankReconciliationLine)
admin.site.register(Project)
admin.site.register(ProjectTransaction)
admin.site.register(Document)


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    """Read-only: the audit log is append-only and hash-chained."""

    list_display = ("seq", "timestamp", "user", "action", "model_name", "record_id")

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

admin.site.register(CompanySettings)
admin.site.register(UserRole)
