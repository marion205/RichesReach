# syntax=docker/dockerfile:1
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends build-essential curl && rm -rf /var/lib/apt/lists/*

# Install deps first for better caching
COPY requirements.txt /app/requirements.txt
RUN pip install --upgrade pip && pip install -r requirements.txt

# Copy app
COPY . /app

# Static dir (even if not using yet)
RUN mkdir -p /app/static

# Collect static without touching DB (skip if you don't have static yet)
# RUN python manage.py collectstatic --noinput || true

# Healthcheck endpoint friendly port
EXPOSE 8001

# Start via Daphne (ASGI)
CMD ["sh", "-c", "python manage.py migrate && daphne -b 0.0.0.0 -p 8001 richesreach.asgi:application"]