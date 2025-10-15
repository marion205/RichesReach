#!/usr/bin/env bash
set -euo pipefail

# Debug: verify consumers.py is correct (temporary)
python - <<'PY'
from pathlib import Path
p = Path("core/consumers.py")
print("BOOT: consumers exists:", p.exists())
if p.exists():
    lines = p.read_text().splitlines()[:3]
    print("BOOT: first 3 lines:")
    for i, line in enumerate(lines, 1):
        print(f"  {i}: {repr(line)}")
else:
    print("BOOT: ERROR: consumers.py not found!")
PY

# Wait for database (if using PostgreSQL)
if [ "${POSTGRES_HOST:-}" ]; then
    echo "Waiting for PostgreSQL..."
    python - <<'PY'
import os, time, psycopg2
for _ in range(60):
    try:
        psycopg2.connect(
            dbname=os.environ.get("POSTGRES_DB", "postgres"),
            user=os.environ.get("POSTGRES_USER", "postgres"),
            password=os.environ.get("POSTGRES_PASSWORD", ""),
            host=os.environ.get("POSTGRES_HOST", "localhost"),
            port=int(os.environ.get("POSTGRES_PORT", "5432")),
        ).close()
        print("DB is up.")
        break
    except Exception as e:
        print("DB not ready yet:", e)
        time.sleep(2)
else:
    raise SystemExit("Database not reachable after 120s")
PY
fi

# --- Auto-adopt existing schema if needed (state-only fix) ---
echo "Running auto-adoption checks..."
python - <<'PY'
import os
import sys
from django.conf import settings
from django.db import connection
import django
django.setup()

app = "core"  # the app that had the AIPortfolioRecommendation table
initial_migration = "0001_initial"
adopt_candidates = [
    # list tuples of (app, migration_name) that we know already exist physically
    ("core", "0026_add_dividend_score"),
    # add more if you've seen them physically present but not in history
]

def table_exists(table):
    with connection.cursor() as c:
        if settings.DATABASES['default']['ENGINE'] == 'django.db.backends.postgresql':
            c.execute("""
                SELECT EXISTS (
                   SELECT FROM information_schema.tables
                   WHERE table_schema = 'public' AND table_name = %s
                );
            """, [table])
        else:
            # SQLite fallback
            c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?;", [table])
        return c.fetchone()[0] if c.fetchone() else False

def migration_row_exists(app, name):
    with connection.cursor() as c:
        c.execute("""
            SELECT 1 FROM django_migrations WHERE app=%s AND name=%s
        """, [app, name])
        return c.fetchone() is not None

# If django_migrations itself is missing, create it by running "migrate" just up to contenttypes
try:
    _ = migration_row_exists("contenttypes", "0001_initial")  # will fail if table missing
except Exception:
    # Create the migrations machinery
    print("Creating django_migrations table...")
    os.system("python manage.py migrate --noinput --run-syncdb || true")

# If our target app's initial migration is not recorded but its main table exists, fake it.
if not migration_row_exists(app, initial_migration) and table_exists("core_aiportfoliorecommendation"):
    print(f"Auto-adopting {app} {initial_migration}...")
    exit_code = os.system(f"python manage.py migrate {app} {initial_migration} --fake --noinput")
    if exit_code != 0:
        sys.exit(exit_code)

# If specific later migrations are physically present (e.g., columns exist) but not recorded, fake them.
if settings.DATABASES['default']['ENGINE'] == 'django.db.backends.postgresql':
    with connection.cursor() as c:
        c.execute("""
            SELECT column_name FROM information_schema.columns
            WHERE table_name='core_stock';
        """)
        stock_cols = {r[0] for r in c.fetchall()}
else:
    # SQLite fallback
    with connection.cursor() as c:
        c.execute("PRAGMA table_info(core_stock);")
        stock_cols = {r[1] for r in c.fetchall()}

# Example: dividend_score column exists but migration not recorded
if "dividend_score" in stock_cols and not migration_row_exists("core", "0026_add_dividend_score"):
    print("Auto-adopting core 0026_add_dividend_score...")
    os.system("python manage.py migrate core 0026_add_dividend_score --fake --noinput || true")

print("Auto-adoption checks complete.")
PY
# --- End auto-adopt block ---

# Static files (make this no-op safe)
echo "Collecting static files..."
python manage.py collectstatic --noinput || true

# Now do normal, idempotent migrate (handles everything else)
echo "Running migrations..."
python manage.py migrate --noinput

# Start server (using Gunicorn for now - will switch to Daphne later)
echo "Starting server..."
exec gunicorn richesreach.wsgi:application --bind 0.0.0.0:8000 --workers 3 --timeout 120
