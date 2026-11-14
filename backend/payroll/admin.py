from django.contrib import admin

from .models import Employee, PayrollRun


@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    list_display = ("employee_number", "first_name", "last_name", "pay_form", "is_active")
    exclude = ("cpr",)  # CPR vises aldrig i klartekst


@admin.register(PayrollRun)
class PayrollRunAdmin(admin.ModelAdmin):
    list_display = ("period_start", "period_end", "frequency", "status", "total_net")
