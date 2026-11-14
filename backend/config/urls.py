"""URL configuration for Ajan Partners Bogføring.

/api/v1/...   kundens bøger (headeren X-Client vælger kunden, se tenancy/middleware.py)
/api/v1/me    brugerens kunder (public)
/api/firm/... admin-portalen for revisorhuset (public)
"""

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/firm/", include("integrations.firm_urls")),
    path("api/firm/", include("firm.urls")),
    path("api/v1/", include("tenancy.urls")),
    path("api/v1/", include("firm.client_urls")),
    path("api/v1/", include("accounts.urls")),
    path("api/v1/", include("journals.urls")),
    path("api/v1/", include("sales.urls")),
    path("api/v1/", include("purchases.urls")),
    path("api/v1/", include("core.urls")),
    path("api/v1/", include("payroll.urls")),
    path("api/v1/", include("integrations.client_urls")),
    path("api/v1/", include("einvoice.urls")),
    path("api/v1/", include("saft.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
