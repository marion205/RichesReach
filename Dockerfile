# syntax=docker/dockerfile:1.7

FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Where your Django app actually lives:
ARG APP_DIR=backend/backend/backend/backend

WORKDIR /app

# Install OS deps as needed
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential gcc libpq-dev libjpeg62-turbo-dev zlib1g-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Python deps with cache-friendly layering
COPY ${APP_DIR}/requirements.txt /tmp/requirements.txt
RUN python -m pip install --upgrade pip && pip install --no-cache-dir -r /tmp/requirements.txt

# ✅ Copy ONLY the Django app (so manage.py is at /app/manage.py)
COPY ${APP_DIR}/ /app/

# Sanity guards (fail early if paths are wrong)
RUN test -f /app/manage.py || (echo "❌ /app/manage.py missing. Check COPY path ${APP_DIR} → /app"; ls -al /app; exit 3)
RUN test -f /app/richesreach/settings.py || (echo "❌ /app/richesreach/settings.py missing"; ls -al /app/richesreach; exit 3)

# Create a non-root user
RUN useradd -m appuser
USER appuser

# Runtime settings
ENV DJANGO_SETTINGS_MODULE=richesreach.settings_production

# Healthcheck: simple and reliable
HEALTHCHECK --interval=30s --timeout=3s --start-period=30s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/healthz', timeout=2)" || exit 1

# Expose port
EXPOSE 8000

# For prod, prefer gunicorn; dev server shown for simplicity
# CMD ["gunicorn", "--bind", "0.0.0.0:8000", "richesreach.wsgi:application"]
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]