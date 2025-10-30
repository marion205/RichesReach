"""
Development Settings with Real JWT Authentication
This file configures Django to use real JWT authentication instead of mock users
"""
from .settings import *  # Import base settings
from datetime import timedelta
import os
from pathlib import Path
from core.feature_flags import env_bool, assert_no_mocks_in_prod, print_feature_flags_banner

# Load secrets from env.secrets file
secrets_file = Path(__file__).parent.parent / 'env.secrets'
if secrets_file.exists():
    with open(secrets_file) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                os.environ[key] = value

DEBUG = True

# 🔐 Enable JWT middleware + backend
GRAPHENE["MIDDLEWARE"] = ["graphql_jwt.middleware.JSONWebTokenMiddleware"]
AUTHENTICATION_BACKENDS = [
    "graphql_jwt.backends.JSONWebTokenBackend",
    "django.contrib.auth.backends.ModelBackend",
]

# Use Bearer (works well with mobile)
GRAPHQL_JWT = {
    "JWT_AUTH_HEADER_PREFIX": "Bearer",
    'JWT_ALGORITHM': 'HS256',
    'JWT_SECRET_KEY': SECRET_KEY,
    'JWT_EXPIRATION_DELTA': timedelta(minutes=60),
    'JWT_REFRESH_EXPIRATION_DELTA': timedelta(days=7),
    'JWT_VERIFY_EXPIRATION': True,
    'JWT_LEEWAY': 0,
    'JWT_AUTH_COOKIE': None,
}

# 🚫 PRODUCTION-READY: All mocks disabled
# Single source of truth for all mock flags
USE_MOCK_USER = False
USE_MOCK_DATA = False
USE_SBLOC_MOCK = env_bool("USE_SBLOC_MOCK", False)
USE_MARKET_MOCK = env_bool("USE_MARKET_MOCK", False)
USE_ALPHA_MOCK = env_bool("USE_ALPHA_MOCK", False)
USE_POLYGON_MOCK = env_bool("USE_POLYGON_MOCK", False)
USE_FINNHUB_MOCK = env_bool("USE_FINNHUB_MOCK", False)
USE_AI_RECS_MOCK = env_bool("USE_AI_RECS_MOCK", False)
USE_NOTIF_MOCK = env_bool("USE_NOTIF_MOCK", False)
USE_BROKER_MOCK = env_bool("USE_BROKER_MOCK", False)
USE_PAYMENTS_MOCK = env_bool("USE_PAYMENTS_MOCK", False)
USE_LEARNING_MOCK = env_bool("USE_LEARNING_MOCK", False)

# Enable real services
USE_OPENAI = env_bool("USE_OPENAI", True)  # Enable real OpenAI (if API key available)
USE_YODLEE = env_bool("USE_YODLEE", True)  # Enable real Yodlee (if configured)
DEV_ALLOW_ANON_GRAPHQL = False  # no anonymous fallbacks

# 🚨 PRODUCTION GUARDRAIL: Hard fail if any mock is enabled in production
assert_no_mocks_in_prod(DEBUG)

# CORS/CSRF for Expo dev
CORS_ALLOW_CREDENTIALS = True
CORS_ALLOWED_ORIGINS = [
    "process.env.API_BASE_URL || "http://localhost":19006",
    "http://localhost:19006",
    "http://localhost:19006",  # Your local IP
    "http://localhost:8081",  # Metro bundler
    "http://localhost:8081",  # Metro bundler on your IP
    "process.env.API_BASE_URL || "http://localhost":8082",  # Alternative Metro port
    "http://localhost:8082",  # Alternative Metro port on your IP
]
CSRF_TRUSTED_ORIGINS = CORS_ALLOWED_ORIGINS
ALLOWED_HOSTS = ["*", "localhost", "localhost", "localhost"]

# Database settings (use local database)
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

# Disable HTTPS redirect for local development
SECURE_SSL_REDIRECT = False
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False

# Log to console in local development
LOGGING['handlers']['console']['level'] = 'DEBUG'
LOGGING['loggers']['django']['level'] = 'INFO'
LOGGING['loggers']['core']['level'] = 'DEBUG'

# Enable GraphiQL for local development
GRAPHENE['GRAPHIQL'] = True

# 📊 Enable real market data providers
ALPHA_VANTAGE_API_KEY = os.getenv('ALPHA_VANTAGE_API_KEY', '')
POLYGON_API_KEY = os.getenv('POLYGON_API_KEY', '')
FINNHUB_API_KEY = os.getenv('FINNHUB_API_KEY', '')
NEWS_API_KEY = os.getenv('NEWS_API_KEY', '')

# Enable market data providers
DISABLE_ALPHA_VANTAGE = os.getenv('DISABLE_ALPHA_VANTAGE', 'false').lower() == 'true'
DISABLE_POLYGON = os.getenv('DISABLE_POLYGON', 'false').lower() == 'true'
DISABLE_FINNHUB = os.getenv('DISABLE_FINNHUB', 'false').lower() == 'true'

# Enable real market data
USE_REAL_MARKET_DATA = os.getenv('USE_REAL_MARKET_DATA', 'true').lower() == 'true'

# 🚀 PRODUCTION-READY STARTUP BANNER
print("=" * 60)
print("🚀 RICHESREACH - PRODUCTION-READY BACKEND")
print("=" * 60)
print(f"[BOOT] Settings: REAL AUTHENTICATION (settings_dev_real.py)")
print(f"[BOOT] Database: {DATABASES['default']['HOST']}:{DATABASES['default']['PORT']}/{DATABASES['default']['NAME']}")
print(f"[BOOT] Debug mode: {DEBUG}")
print(f"[BOOT] JWT middleware: ENABLED")
print(f"[BOOT] Real market data: {'ENABLED' if USE_REAL_MARKET_DATA else 'DISABLED'}")
print(f"[BOOT] Alpha Vantage: {'ENABLED' if ALPHA_VANTAGE_API_KEY and not DISABLE_ALPHA_VANTAGE else 'DISABLED'}")
print(f"[BOOT] Polygon: {'ENABLED' if POLYGON_API_KEY and not DISABLE_POLYGON else 'DISABLED'}")
print(f"[BOOT] Finnhub: {'ENABLED' if FINNHUB_API_KEY and not DISABLE_FINNHUB else 'DISABLED'}")
print(f"[BOOT] CORS enabled for local development")

# Print feature flags status
print_feature_flags_banner(DEBUG)
print("=" * 60)
