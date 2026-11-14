# Ajan Partners Bogføring – backend (Django + DRF, django-tenants)
#
# Byg fra repo-roden (worker-billedet skal bruge infra/):
#   docker build -f backend/Dockerfile --target app    -t bogforing-app    .
#   docker build -f backend/Dockerfile --target worker -t bogforing-worker .
FROM python:3.13-slim AS app

ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1
WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends libpq5 && \
    rm -rf /var/lib/apt/lists/*

COPY backend/requirements.txt .
RUN pip install -r requirements.txt

COPY backend/ .
RUN useradd --system --uid 1000 --home /app app && mkdir -p /app/media /app/staticfiles && \
    chown -R app /app/media /app/staticfiles
USER app

EXPOSE 8001

# Opstart: migrér public + alle kundeskemaer, opret revisorhuset første gang
# (kun hvis BOOTSTRAP_PARTNER_EMAIL/PASSWORD er sat) og start gunicorn.
CMD ["sh", "-c", "\
    python manage.py migrate_schemas --shared --noinput && \
    python manage.py migrate_schemas --noinput && \
    if [ -n \"${BOOTSTRAP_PARTNER_EMAIL:-}\" ] && [ -n \"${BOOTSTRAP_PARTNER_PASSWORD:-}\" ]; then \
        python manage.py bootstrap_firm --domain \"${BOOTSTRAP_DOMAIN:-localhost}\" \
            --partner-email \"$BOOTSTRAP_PARTNER_EMAIL\" --partner-password \"$BOOTSTRAP_PARTNER_PASSWORD\"; \
    fi && \
    python manage.py collectstatic --noinput && \
    exec gunicorn config.wsgi:application --bind 0.0.0.0:8001 --workers ${GUNICORN_WORKERS:-3} --timeout 120 \
        --access-logfile - --error-logfile -"]

# Worker: samme kode + værktøjer til backup (pg_dump, age, aws-cli).
FROM app AS worker
USER root
RUN apt-get update && apt-get install -y --no-install-recommends postgresql-client age gnupg curl && \
    rm -rf /var/lib/apt/lists/* && pip install awscli
COPY --chmod=0755 infra/backup.sh /usr/local/bin/backup.sh
COPY --chmod=0755 infra/worker.sh /usr/local/bin/worker.sh
USER app
CMD ["/usr/local/bin/worker.sh"]
