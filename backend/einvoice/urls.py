"""E-faktura (/api/v1/). Stierne skal ligge under einvoice/send og einvoice/inbox,
som tenancy.features.FEATURE_PATHS bruger til pakke-tjekket."""

from django.urls import path

from . import views

urlpatterns = [
    path("einvoice/send", views.outgoing_list),
    path("einvoice/send/outgoing/<uuid:pk>/xml", views.outgoing_xml),
    path("einvoice/send/<uuid:pk>", views.send_document),
    path("einvoice/inbox", views.inbox),
    path("einvoice/inbox/<uuid:pk>", views.inbox_detail),
    path("einvoice/inbox/<uuid:pk>/to-bill", views.inbox_to_bill),
]
