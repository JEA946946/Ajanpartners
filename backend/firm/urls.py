from django.urls import path

from . import views, views_templates, views_work

urlpatterns = [
    path("clients", views.clients),
    path("clients/<slug:slug>", views.client_detail),
    path("clients/<slug:slug>/archive", views.client_archive),
    path("clients/<slug:slug>/access", views.client_access),
    path("clients/<slug:slug>/invite", views.client_invite),
    path("clients/<slug:slug>/status", views.client_status),
    path("clients/<slug:slug>/export-all", views.client_export_all),
    path("packages", views.packages),
    path("packages/<int:pk>", views.package_detail),
    path("staff", views.staff_list),
    path("staff/<int:pk>", views.staff_detail),
    path("settings", views.firm_settings),
    path("terms", views.terms),
    path("terms/<int:pk>/acceptances", views.terms_acceptances),
    path("audit-log", views.audit_log),
    path("templates", views_templates.templates),
    path("industry-risk", views_templates.industry_risk),
    path("templates/<slug:template_id>/render", views_templates.template_render),
    path("templates/<slug:template_id>/docx", views_templates.template_docx),
    path("deadlines", views_work.deadlines),
    path("tasks", views_work.tasks),
    path("tasks/<uuid:pk>", views_work.task_detail),
    path("tasks/<uuid:pk>/messages", views_work.task_message),
    path("tasks/<uuid:pk>/messages/<uuid:mid>/document", views_work.task_document),
    path("clients/<slug:slug>/trial-balance", views_work.trial_balance),
    path("clients/<slug:slug>/account-comments", views_work.account_comments),
    path("clients/<slug:slug>/account-comments/<uuid:pk>", views_work.account_comment_detail),
]
