"""Integrationer i admin-portalen (/api/firm/, public-skemaet)."""

from django.urls import path

from . import views

urlpatterns = [
    path("cvr/<str:number>", views.cvr_lookup),
]
