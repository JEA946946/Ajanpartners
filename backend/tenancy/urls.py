from django.urls import path

from . import auth_views, views

urlpatterns = [
    # Login med to-faktor (overtager accounts' auth/login, fordi tenancy inkluderes først)
    path("auth/login", auth_views.login),
    path("auth/mfa/verify", auth_views.mfa_verify),
    path("me/mfa", auth_views.mfa_status),
    path("me/mfa/setup", auth_views.mfa_setup),
    path("me/mfa/confirm", auth_views.mfa_confirm),
    path("me/mfa/disable", auth_views.mfa_disable),
    path("me/password", auth_views.change_password),
    path("me", views.me),
    path("me/clients/<slug:slug>", views.me_client),
    path("export-all", views.export_all),
    path("access-grants", views.access_grants),
    path("access-grants/create", views.access_grant_create),
    path("access-grants/<uuid:pk>/accept", views.access_grant_accept),
    path("access-grants/<uuid:pk>/revoke", views.access_grant_revoke),
]
