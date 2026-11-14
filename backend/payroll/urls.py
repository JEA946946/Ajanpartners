from django.urls import path

from . import views

urlpatterns = [
    path("payroll/employees", views.employees_list_create, name="payroll-employees"),
    path("payroll/employees/<uuid:pk>", views.employees_detail, name="payroll-employee"),
    path("payroll/employees/<uuid:pk>/fetch-tax-card", views.employee_fetch_tax_card,
         name="payroll-employee-tax-card"),
    path("payroll/settings", views.payroll_settings, name="payroll-settings"),
    path("payroll/holidays", views.holidays_list, name="payroll-holidays"),
    path("payroll/rates", views.rates_view, name="payroll-rates"),
    path("payroll/runs", views.runs_list_create, name="payroll-runs"),
    path("payroll/runs/<uuid:pk>", views.runs_detail, name="payroll-run"),
    path("payroll/runs/<uuid:pk>/lines/<uuid:line_pk>", views.run_line_update, name="payroll-run-line"),
    path("payroll/runs/<uuid:pk>/calculate", views.run_calculate, name="payroll-run-calculate"),
    path("payroll/runs/<uuid:pk>/approve", views.run_approve, name="payroll-run-approve"),
    path("payroll/runs/<uuid:pk>/reopen", views.run_reopen, name="payroll-run-reopen"),
    path("payroll/runs/<uuid:pk>/post", views.run_post, name="payroll-run-post"),
    path("payroll/runs/<uuid:pk>/payslips.pdf", views.run_payslips, name="payroll-run-payslips"),
    path("payroll/runs/<uuid:pk>/payroll-list.pdf", views.run_payroll_list, name="payroll-run-list"),
    path("payroll/runs/<uuid:pk>/eindkomst", views.run_eindkomst_export, name="payroll-run-eindkomst"),
    path("payroll/runs/<uuid:pk>/eindkomst/submit", views.run_eindkomst_submit,
         name="payroll-run-eindkomst-submit"),
]
