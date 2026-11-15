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
    path("me/terms", views.me_terms),
    path("me/terms/accept", views.me_terms_accept),
    path("me/terms/sign", views.me_terms_sign),
    path("me/terms/sign/complete", views.me_terms_sign_complete),
    path("public/terms/<str:kind>", views.public_terms),
    path("export-all", views.export_all),
    path("access-grants", views.access_grants),
]
