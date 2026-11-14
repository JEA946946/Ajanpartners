from django.urls import path

from . import views

urlpatterns = [
    path("me", views.me),
    path("me/clients/<slug:slug>", views.me_client),
    path("access-grants", views.access_grants),
    path("access-grants/create", views.access_grant_create),
    path("access-grants/<uuid:pk>/accept", views.access_grant_accept),
    path("access-grants/<uuid:pk>/revoke", views.access_grant_revoke),
]
