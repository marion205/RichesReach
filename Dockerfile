# syntax=docker/dockerfile:1.7

FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DJANGO_SETTINGS_MODULE=richesreach.settings_production

# Where your Django app actually lives:
ARG APP_DIR=backend/backend/backend/backend

WORKDIR /app

# Install OS deps for production
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential gcc libpq-dev libjpeg62-turbo-dev zlib1g-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python deps with cache-friendly layering
COPY ${APP_DIR}/requirements.txt /tmp/requirements.txt
RUN python -m pip install --upgrade pip && pip install --no-cache-dir -r /tmp/requirements.txt

# ✅ Copy ONLY the Django app (so manage.py is at /app/manage.py)
COPY ${APP_DIR}/ /app/

# Sanity guards (fail early if paths are wrong)
RUN test -f /app/manage.py || (echo "❌ /app/manage.py missing. Check COPY path ${APP_DIR} → /app"; ls -al /app; exit 3)
RUN test -f /app/richesreach/settings.py || (echo "❌ /app/richesreach/settings.py missing"; ls -al /app/richesreach; exit 3)

# Create a non-root user for security
RUN useradd -m appuser && chown -R appuser:appuser /app
USER appuser

# Healthcheck for production
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
  CMD curl -f http://localhost:8000/healthz || exit 1

# Expose port
EXPOSE 8000

# Production command with gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "3", "--timeout", "120", "--keep-alive", "2", "--max-requests", "1000", "--max-requests-jitter", "100", "richesreach.wsgi:application"]