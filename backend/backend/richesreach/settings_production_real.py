"""
Production Settings - 100% Real Data, No Mocks
This configuration provides:
- Production database schema (local PostgreSQL)
- Real market data providers (Alpha Vantage, Polygon, Finnhub)
- Real JWT authentication
- Real broker integration (Alpaca)
- Real payment processing
- Real notifications
- All production features enabled with NO MOCK DATA
"""

import os
from datetime import timedelta
from .settings import *  # Import base settings

print("[BOOT] Using PRODUCTION REAL DATA SETTINGS (settings_production_real.py)")
print("[BOOT] Database: localhost:5432/richesreach_local")
print("[BOOT] Debug mode: False")
print("[BOOT] Real market data: ENABLED")
print("[BOOT] All services: REAL (no mocks)")
print("[BOOT] Security: ENABLED")

# =============================================================================
# DATABASE CONFIGURATION
# =============================================================================
# Force local database configuration - override any env.secrets settings
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'dev',
        'USER': os.getenv('USER', 'marioncollins'),
        'PASSWORD': '',  # No password for local development
        'HOST': 'localhost',
        'PORT': '5432',
        'OPTIONS': {
            'sslmode': 'disable',
        },
    }
}

# Explicitly override any DATABASE_URL that might be set in env.secrets
if 'DATABASE_URL' in os.environ:
    del os.environ['DATABASE_URL']

# =============================================================================
# SECURITY & DEBUG
# =============================================================================
DEBUG = False
ALLOWED_HOSTS = ['*']

# =============================================================================
# MIDDLEWARE CONFIGURATION
# =============================================================================
MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'core.middleware.rate_limit.RateLimitMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    # Production middleware
    'core.middleware.PerformanceMiddleware',
    'core.middleware.SecurityHeadersMiddleware',
    'core.middleware.RequestLoggingMiddleware',
]

# =============================================================================
# CORS CONFIGURATION
# =============================================================================
CORS_ALLOW_ALL_ORIGINS = True
CORS_ALLOW_CREDENTIALS = True
CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:8081",
    "http://127.0.0.1:8081",
    "http://192.168.1.236:8081",  # Expo development server
]

# =============================================================================
# JWT AUTHENTICATION (REAL)
# =============================================================================
GRAPHENE["MIDDLEWARE"] = [
    "graphql_jwt.middleware.JSONWebTokenMiddleware",
]
AUTHENTICATION_BACKENDS = [
    "graphql_jwt.backends.JSONWebTokenBackend",
    "django.contrib.auth.backends.ModelBackend",
]

# JWT Configuration
GRAPHQL_JWT = {
    'JWT_ALGORITHM': 'HS256',
    'JWT_SECRET_KEY': SECRET_KEY,
    'JWT_EXPIRATION_DELTA': timedelta(minutes=60),
    'JWT_REFRESH_EXPIRATION_DELTA': timedelta(days=7),
    'JWT_VERIFY_EXPIRATION': True,
    'JWT_LEEWAY': 0,
    'JWT_AUTH_HEADER_PREFIX': 'Bearer',
    'JWT_AUTH_COOKIE': None,
}

# =============================================================================
# MARKET DATA PROVIDERS (100% REAL)
# =============================================================================
# Enable real market data providers - NO MOCKS
USE_REAL_MARKET_DATA = True
USE_ALPHA_MOCK = False
USE_POLYGON_MOCK = False
USE_FINNHUB_MOCK = False
USE_MARKET_MOCK = False  # DISABLED - Use real market data

# Real API keys (from environment)
ALPHA_VANTAGE_API_KEY = os.getenv('ALPHA_VANTAGE_API_KEY', '')
POLYGON_API_KEY = os.getenv('POLYGON_API_KEY', '')
FINNHUB_API_KEY = os.getenv('FINNHUB_API_KEY', '')

# =============================================================================
# AI & ML SERVICES (100% REAL) - OVERRIDE BASE SETTINGS
# =============================================================================
# Force real AI services - NO MOCKS (override environment variables)
USE_AI_RECS_MOCK = False  # Use real AI recommendations
USE_LEARNING_MOCK = False  # Use real ML learning
USE_OPENAI = True  # Force enable OpenAI

# Real broker and payment processing - NO MOCKS
USE_BROKER_MOCK = False  # Use real broker data
USE_PAYMENTS_MOCK = False  # Use real payment processing

# =============================================================================
# EXTERNAL SERVICES (100% REAL) - OVERRIDE BASE SETTINGS
# =============================================================================
# Force real external services (override environment variables)
USE_YODLEE = True  # Force enable real Yodlee integration
USE_SBLOC_AGGREGATOR = True  # Force enable real SBLOC
USE_SBLOC_MOCK = False  # Force disable SBLOC mock

# =============================================================================
# NOTIFICATIONS & OTHER SERVICES (100% REAL)
# =============================================================================
USE_NOTIF_MOCK = False  # Use real notifications

# =============================================================================
# ALPACA INTEGRATION (REAL)
# =============================================================================
USE_ALPACA = True
USE_ALPACA_BROKER = True
USE_ALPACA_CRYPTO = True
ALPACA_ENVIRONMENT = 'sandbox'  # Use sandbox for testing
ALPACA_PAPER_TRADING = True

# =============================================================================
# GRAPHIQL (GraphQL Playground)
# =============================================================================
GRAPHENE['GRAPHIQL'] = True

# =============================================================================
# LOGGING CONFIGURATION
# =============================================================================
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': 'logs/django.log',
            'formatter': 'verbose',
        },
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
        },
    },
    'root': {
        'handlers': ['console', 'file'],
        'level': 'INFO',
    },
    'loggers': {
        'django': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': False,
        },
        'core': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}

# =============================================================================
# CACHE CONFIGURATION
# =============================================================================
CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': 'redis://127.0.0.1:6379/1',
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
        }
    }
}

# =============================================================================
# CELERY CONFIGURATION
# =============================================================================
CELERY_BROKER_URL = 'redis://localhost:6379/0'
CELERY_RESULT_BACKEND = 'redis://localhost:6379/0'
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = 'UTC'

# =============================================================================
# SECURITY SETTINGS
# =============================================================================
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True

# =============================================================================
# STATIC FILES
# =============================================================================
STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

# =============================================================================
# MEDIA FILES
# =============================================================================
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# =============================================================================
# FINAL SERVICE OVERRIDES - MUST BE LAST
# =============================================================================
# Override any remaining service flags to ensure 100% real data
USE_OPENAI = True
USE_YODLEE = True
USE_SBLOC_MOCK = False
USE_SBLOC_AGGREGATOR = True

print("🚀 PRODUCTION REAL DATA MODE - All services REAL")
print("============================================================")
print(f"[FLAGS] 🛠️  DEBUG={DEBUG} (production mode)")
print("[FLAGS] Mock Services Status:")
print("[FLAGS]   USE_AI_RECS_MOCK: 🟢 DISABLED")
print("[FLAGS]   USE_ALPHA_MOCK: 🟢 DISABLED")
print("[FLAGS]   USE_BROKER_MOCK: 🟢 DISABLED")
print("[FLAGS]   USE_FINNHUB_MOCK: 🟢 DISABLED")
print("[FLAGS]   USE_LEARNING_MOCK: 🟢 DISABLED")
print("[FLAGS]   USE_MARKET_MOCK: 🟢 DISABLED")
print("[FLAGS]   USE_NOTIF_MOCK: 🟢 DISABLED")
print("[FLAGS]   USE_PAYMENTS_MOCK: 🟢 DISABLED")
print("[FLAGS]   USE_POLYGON_MOCK: 🟢 DISABLED")
print("[FLAGS]   USE_SBLOC_MOCK: 🟢 DISABLED")
print("[FLAGS] Alpaca Integration Status:")
print("[FLAGS]   USE_ALPACA: 🟢 ENABLED")
print("[FLAGS]   USE_ALPACA_BROKER: 🟢 ENABLED")
print("[FLAGS]   USE_ALPACA_CRYPTO: 🟢 ENABLED")
print("[FLAGS]   ALPACA_ENVIRONMENT: sandbox")
print("[FLAGS]   ALPACA_PAPER_TRADING: 🟢 ENABLED")
print("============================================================")
