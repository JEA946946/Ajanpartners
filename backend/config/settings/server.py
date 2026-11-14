"""Server settings for production deployment."""

import os

from .base import *  # noqa: F401,F403

DEBUG = False

# Required secrets — fail hard at boot if unset (no insecure fallbacks).
SECRET_KEY = os.environ["DJANGO_SECRET_KEY"]
# CPR-numre og MFA-hemmeligheder krypteres med denne nøgle; ingen dev-default i produktion.
FIELD_ENCRYPTION_KEY = os.environ["FIELD_ENCRYPTION_KEY"]

ALLOWED_HOSTS = os.environ.get(
    "DJANGO_ALLOWED_HOSTS", "bogfoering.ajanpartners.dk"
).split(",")

DATABASES["default"]["HOST"] = os.environ.get("DB_HOST", "db")  # noqa: F405
DATABASES["default"]["PASSWORD"] = os.environ["DB_PASSWORD"]  # noqa: F405

CORS_ALLOWED_ORIGINS = os.environ.get(
    "CORS_ALLOWED_ORIGINS", "https://bogfoering.ajanpartners.dk"
).split(",")
CORS_ALLOW_CREDENTIALS = True

from corsheaders.defaults import default_headers  # noqa: E402
CORS_ALLOW_HEADERS = (*default_headers, "x-client")
DATABASES["default"]["NAME"] = os.environ.get("DB_NAME", "ajanpartners")  # noqa: F405
DATABASES["default"]["USER"] = os.environ.get("DB_USER", "postgres")  # noqa: F405

GOOGLE_PLACES_API_KEY = os.environ.get("GOOGLE_PLACES_API_KEY", "")

# Security (SSL handled by Nginx/Certbot)
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

# SimpleJWT — use production secret key for signing
SIMPLE_JWT["SIGNING_KEY"] = SECRET_KEY  # noqa: F405
