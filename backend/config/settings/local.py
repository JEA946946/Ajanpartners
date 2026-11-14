"""Local development settings."""

import os

from .base import *  # noqa: F401,F403

DEBUG = True

ALLOWED_HOSTS = ["*"]

# Lokal Postgres (Homebrew) eller docker-compose (DB_HOST=db).
DATABASES["default"]["HOST"] = os.environ.get("DB_HOST", "localhost")  # noqa: F405
DATABASES["default"]["USER"] = os.environ.get("DB_USER", os.environ.get("USER", "postgres"))  # noqa: F405
DATABASES["default"]["PASSWORD"] = os.environ.get("DB_PASSWORD", "")  # noqa: F405
DATABASES["default"]["NAME"] = os.environ.get("DB_NAME", "ajanpartners")  # noqa: F405

# CORS — allow frontend dev server
CORS_ALLOW_ALL_ORIGINS = True
from corsheaders.defaults import default_headers  # noqa: E402
CORS_ALLOW_HEADERS = (*default_headers, "x-client")
