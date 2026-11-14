"""Base settings for Ajan Partners Bogføring (multi-tenant, ét skema pr. kunde)."""

from datetime import timedelta
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent

SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY", "django-insecure-ajanpartners-dev-key")

DEBUG = False

ALLOWED_HOSTS = []

SHARED_APPS = [
    "django_tenants",
    "tenancy",
    "firm",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "rest_framework",
    "corsheaders",
]

# Hver kundes bøger (ét Postgres-skema pr. kunde).
TENANT_APPS = [
    "django.contrib.contenttypes",
    "accounts",
    "journals",
    "sales",
    "purchases",
    "core",
    "payroll",
]

INSTALLED_APPS = list(SHARED_APPS) + [app for app in TENANT_APPS if app not in SHARED_APPS]

TENANT_MODEL = "tenancy.ClientCompany"
TENANT_DOMAIN_MODEL = "tenancy.Domain"
PUBLIC_SCHEMA_NAME = "public"
DATABASE_ROUTERS = ("django_tenants.routers.TenantSyncRouter",)
# Bilag gemmes pr. kunde: MEDIA_ROOT/<schema>/...
STORAGES = {
    "default": {"BACKEND": "django_tenants.files.storage.TenantFileSystemStorage"},
    "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"},
}
MULTITENANT_RELATIVE_MEDIA_ROOT = "%s"

MEDIA_URL = "media/"
MEDIA_ROOT = BASE_DIR / "media"

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "tenancy.middleware.ClientTenantMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"

DATABASES = {
    "default": {
        "ENGINE": "django_tenants.postgresql_backend",
        "NAME": "ajanpartners",
        "USER": "postgres",
        "PASSWORD": os.environ.get("DB_PASSWORD", "localdev-only"),  # prod overrides via .env.server
        "HOST": "localhost",
        "PORT": "5432",
    }
}

AUTH_PASSWORD_VALIDATORS = []

LANGUAGE_CODE = "da"
TIME_ZONE = "Europe/Copenhagen"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# DRF
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ),
    "DEFAULT_PERMISSION_CLASSES": (
        "rest_framework.permissions.IsAuthenticated",
    ),
    "DEFAULT_PAGINATION_CLASS": None,
    "EXCEPTION_HANDLER": "journals.exceptions.exception_handler",
    "DEFAULT_THROTTLE_RATES": {
        "auth": "10/min",
    },
    # Throttling is per-IP, and every request reaches Django through the shared
    # nginx container — so without this DRF reads REMOTE_ADDR, sees nginx's own
    # address for everyone, and the auth rate limit above becomes a single global
    # bucket that any one client can exhaust for all users. With one proxy in
    # front, DRF takes the last entry of X-Forwarded-For, which nginx appends
    # itself from its view of the peer, so it cannot be spoofed by the client.
    "NUM_PROXIES": 1,
}

# SimpleJWT
SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(hours=12),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=7),
    "ROTATE_REFRESH_TOKENS": True,
    "ALGORITHM": "HS256",
    "SIGNING_KEY": SECRET_KEY,
    "USER_ID_FIELD": "id",
    "USER_ID_CLAIM": "userId",
    "TOKEN_OBTAIN_SERIALIZER": "rest_framework_simplejwt.serializers.TokenObtainPairSerializer",
}


# Google Places API
GOOGLE_PLACES_API_KEY = ""
