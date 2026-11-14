from django.urls import path

from . import views

urlpatterns = [
    path("saft/export", views.export),
]
