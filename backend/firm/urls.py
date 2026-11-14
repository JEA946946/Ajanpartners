from django.urls import path

from . import views

urlpatterns = [
    path("clients", views.clients),
    path("clients/<slug:slug>", views.client_detail),
    path("clients/<slug:slug>/archive", views.client_archive),
    path("clients/<slug:slug>/request-access", views.client_request_access),
    path("clients/<slug:slug>/invite", views.client_invite),
    path("clients/<slug:slug>/status", views.client_status),
    path("packages", views.packages),
    path("packages/<int:pk>", views.package_detail),
    path("staff", views.staff_list),
    path("staff/<int:pk>", views.staff_detail),
    path("settings", views.firm_settings),
    path("audit-log", views.audit_log),
]
