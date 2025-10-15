FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# ---- system deps first (psycopg2, cryptography, etc.)
RUN apt-get update && apt-get install -y --no-install-recommends \
      build-essential gcc \
      libpq-dev \
      libssl-dev \
    && rm -rf /var/lib/apt/lists/*

# ---- copy requirements only (better cache), then install
COPY backend/backend/requirements.txt /app/requirements.txt
RUN python -V && pip -V && \
    pip install --no-cache-dir --upgrade pip setuptools wheel && \
    pip install --no-cache-dir -r /app/requirements.txt

# ---- copy the app code
COPY backend/backend/ /app/

# ensure prod settings ends up in image (explicit!)
COPY backend/backend/richesreach/settings_production.py /app/richesreach/settings_production.py

# optional: fail fast if file missing
RUN test -f /app/richesreach/settings_production.py || (echo "settings_production.py missing!" && ls -R /app && exit 3)

ENV DJANGO_SETTINGS_MODULE=richesreach.settings_production

# default command (adjust to yours)
CMD ["gunicorn", "richesreach.wsgi:application", "-b", "0.0.0.0:8000", "--workers", "3"]
