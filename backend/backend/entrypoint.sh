#!/usr/bin/env bash
set -euo pipefail

echo "[BOOT] GRAPHQL_MODE=${GRAPHQL_MODE:-simple}"

# Simple mode defaults to SQLite at /tmp/simple.sqlite3
if [ "${GRAPHQL_MODE:-simple}" = "simple" ]; then
  echo "[BOOT] Using SQLite (simple mode)"
else
  echo "[BOOT] Using Postgres (production mode)"
fi

# Run DB migrations and collect static (idempotent, works for SQLite and Postgres)
echo "[BOOT] Running migrations..."
python manage.py migrate --noinput

echo "[BOOT] Collecting static files..."
python manage.py collectstatic --noinput || true

# Start server
echo "[BOOT] Starting Gunicorn server..."
exec gunicorn richesreach.wsgi:application --bind 0.0.0.0:8000 --workers "${WEB_WORKERS:-3}" --timeout 90 --access-logfile - --error-logfile -
