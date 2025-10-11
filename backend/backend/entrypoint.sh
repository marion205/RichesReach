#!/usr/bin/env sh
set -e

# Optional but useful diagnostics
echo "ENV: DJANGO_SETTINGS_MODULE=$DJANGO_SETTINGS_MODULE PORT=$PORT"
python - <<'PY' || true
import os, django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", os.environ.get("DJANGO_SETTINGS_MODULE","richesreach.settings_production"))
try:
    django.setup()
    print("django.setup() OK")
except Exception as e:
    print("django.setup() FAILED:", e)
PY

exec "$@"