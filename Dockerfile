# syntax=docker/dockerfile:1.7

# ---- base with build deps ----
FROM python:3.12-slim AS base
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=on \
    PIP_NO_CACHE_DIR=1

# Install system deps (psycopg2, Pillow, etc. adjust as needed)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential gcc libpq-dev libjpeg62-turbo-dev zlib1g-dev \
    && rm -rf /var/lib/apt/lists/*

# ---- deps layer (better cache) ----
FROM base AS deps
# This ARG lets us avoid hardcoding the weird path
ARG APP_DIR=backend/backend/backend/backend
WORKDIR /opt/app
# Copy only requirements first for caching
COPY ${APP_DIR}/requirements.txt ./requirements.txt
RUN python -m pip install --upgrade pip && pip install -r requirements.txt

# ---- runtime image ----
FROM base AS runtime
# Create a non-root user
RUN useradd -m appuser
WORKDIR /app
# Copy installed packages from deps
COPY --from=deps /usr/local/lib/python3.12 /usr/local/lib/python3.12
COPY --from=deps /usr/local/bin /usr/local/bin

# Copy application source
ARG APP_DIR=backend/backend/backend/backend
COPY ${APP_DIR}/ /app/

# Sanity guards (fail early if paths are wrong)
RUN test -f /app/manage.py || (echo "❌ /app/manage.py missing. Check COPY path ${APP_DIR} → /app"; ls -al /app; exit 3)
RUN test -f /app/richesreach/settings.py || (echo "❌ /app/richesreach/settings.py missing"; ls -al /app/richesreach; exit 3)

# Configure Django for build-time operations (if needed)
ENV DJANGO_SETTINGS_MODULE=richesreach.settings \
    PYTHONPATH=/app \
    SECRET_KEY=dummy

# Optional: collect static in image build (default OFF to avoid build failures)
ARG RUN_COLLECTSTATIC=false
RUN if [ "$RUN_COLLECTSTATIC" = "true" ]; then \
      python manage.py check --deploy && \
      python manage.py collectstatic --noinput; \
    else \
      echo "Skipping collectstatic during build (set RUN_COLLECTSTATIC=true to enable)"; \
    fi

# Runtime settings
ENV DJANGO_SETTINGS_MODULE=richesreach.settings_production

# Security: run as non-root
USER appuser

# Healthcheck: exec form, no heredoc
ENV HEALTHCHECK_URL=http://127.0.0.1:8000/healthz
HEALTHCHECK --interval=30s --timeout=3s --start-period=30s --retries=3 \
  CMD python -c "import os,sys,urllib.request; u=os.getenv('HEALTHCHECK_URL','http://127.0.0.1:8000/healthz'); urllib.request.urlopen(u, timeout=2); print('OK')" || exit 1

# Expose port
EXPOSE 8000

# Default command; override in compose/k8s as needed
# For prod, prefer gunicorn:
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "3", "richesreach.wsgi:application"]