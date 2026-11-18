"""Kundens side af revisorhusets opgaver (/api/v1/, X-Client)."""

from django.urls import path

from . import client_views, views_archive

urlpatterns = [
    path("inbox", client_views.inbox),
    path("inbox/<uuid:pk>", client_views.inbox_detail),
    path("inbox/<uuid:pk>/reply", client_views.inbox_reply),
    path("firm-documents", views_archive.client_firm_documents),
    path("firm-documents/<uuid:pk>", views_archive.client_firm_document),
]
