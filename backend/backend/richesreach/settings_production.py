"""
Production settings for RichesReach
"""
import os
from .settings import *

# Override database configuration for production
# This ensures we use the correct environment variables and SSL settings

def _env(name, default=None):
    v = os.getenv(name, default)
    return v

def _req(name):
    v = os.getenv(name)
    if not v:
        raise RuntimeError(f"Missing required env var: {name}")
    return v

# Accept DATABASE_URL (postgres://) or PG*/POSTGRES*/DJANGO_DB_* variants.
def _db_cfg():
    url = _env("DATABASE_URL")
    if url:
        import urllib.parse as _urlparse
        parsed = _urlparse.urlparse(url)
        return {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": parsed.path.lstrip("/") or "postgres",
            "USER": parsed.username,
            "PASSWORD": parsed.password,
            "HOST": parsed.hostname,
            "PORT": parsed.port or "5432",
            "OPTIONS": {"sslmode": _env("SSLMODE", "require")},
        }

    # Normalize keys from multiple naming conventions
    def pick(*names, default=None, required=False):
        for n in names:
            v = os.getenv(n)
            if v:
                return v
        if required:
            raise RuntimeError(f"No production database configuration found. "
                               f"Set PG*/POSTGRES*/DJANGO_DB_* or DATABASE_URL.")
        return default

    host = pick("PGHOST","POSTGRES_HOST","DJANGO_DB_HOST", required=True)
    port = pick("PGPORT","POSTGRES_PORT","DJANGO_DB_PORT", default="5432")
    user = pick("PGUSER","POSTGRES_USER","DJANGO_DB_USER", required=True)
    pwd  = pick("PGPASSWORD","POSTGRES_PASSWORD","DJANGO_DB_PASSWORD", required=True)
    name = pick("PGDATABASE","POSTGRES_DB","DJANGO_DB_NAME", required=True)
    
    # CRITICAL: Use PGSSLMODE if available, fallback to SSLMODE, then default to require
    sslm = pick("PGSSLMODE","SSLMODE","DJANGO_DB_SSLMODE", default="require")

    return {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": name, "USER": user, "PASSWORD": pwd,
        "HOST": host, "PORT": port,
        "OPTIONS": {"sslmode": sslm},
    }

# Override the database configuration
DATABASES = {"default": _db_cfg()}

# Ensure we're using PostgreSQL in production
if DATABASES["default"]["ENGINE"] != "django.db.backends.postgresql":
    raise RuntimeError("Production must use PostgreSQL")

# Log database configuration for debugging
import logging
logging.getLogger(__name__).warning("PRODUCTION DB_ENGINE=%s, DB_NAME=%s, SSL_MODE=%s", 
                                   DATABASES["default"]["ENGINE"], 
                                   DATABASES["default"]["NAME"],
                                   DATABASES["default"]["OPTIONS"].get("sslmode", "not_set"))

print(f"[PRODUCTION] Database configuration loaded: {DATABASES['default']['HOST']} with SSL mode: {DATABASES['default']['OPTIONS'].get('sslmode', 'not_set')}", flush=True)
