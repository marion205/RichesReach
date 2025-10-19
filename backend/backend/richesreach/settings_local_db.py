"""
Local Development Settings with Local PostgreSQL Database
This file configures Django to use a local PostgreSQL database that matches production schema
"""

import os
from .settings import *  # Import base settings

# Override database settings to use local PostgreSQL
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'richesreach_local',
        'USER': os.getenv('USER', 'marioncollins'),  # Use current user
        'PASSWORD': '',  # No password for local development
        'HOST': 'localhost',
        'PORT': '5432',
        'OPTIONS': {
            'sslmode': 'disable',  # No SSL for local development
        },
    }
}

# Debug mode for local development
DEBUG = True

# Allow all hosts for local development
ALLOWED_HOSTS = ['*']

# CORS settings for local development
CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://192.168.1.236:3000",  # Your local IP
    "http://localhost:19006",  # Expo dev server
    "http://192.168.1.236:19006",  # Expo dev server on your IP
    "http://localhost:8081",  # Metro bundler
    "http://192.168.1.236:8081",  # Metro bundler on your IP
    "http://localhost:8082",  # Alternative Metro port
    "http://192.168.1.236:8082",  # Alternative Metro port on your IP
]

CORS_ALLOW_CREDENTIALS = True

# Disable HTTPS redirect for local development
SECURE_SSL_REDIRECT = False

# CSRF settings for local development
CSRF_TRUSTED_ORIGINS = [
    "http://localhost:8000",
    "http://127.0.0.1:8000",
    "http://192.168.1.236:8000",
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://192.168.1.236:3000",
    "http://localhost:8081",
    "http://192.168.1.236:8081",
    "http://localhost:8082",
    "http://192.168.1.236:8082",
]

# Enable GraphiQL for local development
GRAPHENE['GRAPHIQL'] = True

# =============================================================================
# MARKET DATA CONFIGURATION (MOCK MODE)
# =============================================================================
# Enable mock market data for local development
USE_MARKET_MOCK = True
USE_REAL_MARKET_DATA = False
USE_ALPHA_MOCK = True
USE_POLYGON_MOCK = True
USE_FINNHUB_MOCK = True

# Disable real API keys for local development
ALPHA_VANTAGE_API_KEY = None
POLYGON_API_KEY = None
FINNHUB_API_KEY = None

# Print a clear message when these settings are used
print("[BOOT] Using LOCAL DATABASE SETTINGS (settings_local_db.py)")
print(f"[BOOT] Database: localhost:5432/richesreach_local")
print(f"[BOOT] Debug mode: {DEBUG}")
print(f"[BOOT] CORS enabled for local development")
print(f"[BOOT] Market data: MOCK MODE ENABLED")
