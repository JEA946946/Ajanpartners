"""Integrationer i kundens bøger (/api/v1/, kræver X-Client).

bank-feeds/... er gated af funktionen bank_feed (tenancy.features.FEATURE_PATHS).
"""

from django.urls import path

from . import views

urlpatterns = [
    path("bank-feeds/institutions", views.institutions),
    path("bank-feeds", views.connections),
    path("bank-feeds/<uuid:pk>", views.connection_delete),
    path("bank-feeds/<uuid:pk>/callback", views.connection_callback),
    path("bank-feeds/<uuid:pk>/renew", views.connection_renew),
    path("bank-feeds/<uuid:pk>/sync", views.connection_sync),
]
