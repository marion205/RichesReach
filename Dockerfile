FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# 1) deps first (path is RELATIVE TO REPO ROOT)
COPY backend/backend/backend/requirements.txt /tmp/requirements.txt
RUN apt-get update && apt-get install -y --no-install-recommends \
      build-essential gcc libpq-dev \
    && rm -rf /var/lib/apt/lists/* \
 && pip install --no-cache-dir --upgrade pip setuptools wheel \
 && pip install --no-cache-dir -r /tmp/requirements.txt

# 2) app code (copy the actual Django project folder)
COPY backend/backend/backend/ /app/

# 3) sanity guards (fail early if paths are wrong)
RUN test -f /app/manage.py || (echo "❌ /app/manage.py missing. Check COPY path backend/backend/ → /app"; ls -al /app; exit 3)
RUN test -f /app/richesreach/settings.py || (echo "❌ /app/richesreach/settings.py missing"; ls -al /app/richesreach; exit 3)

# 4) build-safe static collection (no DB/S3)
ENV DJANGO_SETTINGS_MODULE=richesreach.settings_build
RUN mkdir -p /app/staticfiles && python manage.py collectstatic --noinput

# 5) runtime settings
ENV DJANGO_SETTINGS_MODULE=richesreach.settings_production

EXPOSE 8000
CMD ["gunicorn","richesreach.wsgi:application","--bind","0.0.0.0:8000","--workers","3"]
