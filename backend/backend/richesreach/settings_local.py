"""
Local Development Settings - Production Schema with Real Data + Mock Fallbacks
This configuration provides:
- Production database schema (local PostgreSQL)
- Real market data providers (Alpha Vantage, Polygon, Finnhub)
- Real JWT authentication
- Mock fallbacks for portfolio data to ensure functionality
- All production features enabled
"""

import os
from datetime import timedelta
from .settings import *  # Import base settings

print("[BOOT] Using LOCAL DEVELOPMENT SETTINGS (settings_local.py)")
print("[BOOT] Database: localhost:5432/richesreach_local")
print("[BOOT] Debug mode: True")
print("[BOOT] Real market data: ENABLED")
print("[BOOT] JWT middleware: DISABLED (attach_user middleware disabled for local dev)")
print("[BOOT] CORS enabled for local development")

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
DEBUG = True
ALLOWED_HOSTS = ['*']

# =============================================================================
# MIDDLEWARE CONFIGURATION (Override base settings)
# =============================================================================
# Disable attach_user middleware for local development to fix GraphQL auth issues
MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'core.middleware.rate_limit.RateLimitMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'graphql_jwt.middleware.JSONWebTokenMiddleware',  # JWT authentication for GraphQL
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
GRAPHENE["MIDDLEWARE"] = []  # Temporarily disable JWT middleware for development
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
# MARKET DATA PROVIDERS (REAL)
# =============================================================================
# Enable real market data providers
USE_REAL_MARKET_DATA = True
USE_ALPHA_MOCK = False
USE_POLYGON_MOCK = False
USE_FINNHUB_MOCK = False
USE_MARKET_MOCK = True

# Real API keys (from environment)
ALPHA_VANTAGE_API_KEY = os.getenv('ALPHA_VANTAGE_API_KEY', '')
POLYGON_API_KEY = os.getenv('POLYGON_API_KEY', '')
FINNHUB_API_KEY = os.getenv('FINNHUB_API_KEY', '')

# =============================================================================
# AI & ML SERVICES (REAL WITH FALLBACKS)
# =============================================================================
# Use real AI services but with fallbacks for portfolio data
USE_AI_RECS_MOCK = False  # Use real AI recommendations
USE_LEARNING_MOCK = False  # Use real ML learning
USE_OPENAI = True  # Enable OpenAI

# Mock fallbacks for portfolio-specific data to ensure functionality
USE_BROKER_MOCK = True  # Mock broker data for portfolio
USE_PAYMENTS_MOCK = True  # Mock payment processing

# =============================================================================
# EXTERNAL SERVICES
# =============================================================================
# Disable external services that require production setup
USE_YODLEE = False  # Disable Yodlee (requires production setup)
USE_SBLOC_AGGREGATOR = False  # Disable SBLOC (requires production setup)
USE_SBLOC_MOCK = True  # Use mock SBLOC for testing

# =============================================================================
# NOTIFICATIONS & OTHER SERVICES
# =============================================================================
USE_NOTIF_MOCK = True  # Mock notifications for local development

# =============================================================================
# GRAPHIQL (GraphQL Playground)
# =============================================================================
GRAPHENE['GRAPHIQL'] = True

# =============================================================================
# LOGGING
# =============================================================================
LOGGING['handlers']['console']['level'] = 'DEBUG'
LOGGING['loggers']['django']['level'] = 'INFO'
LOGGING['loggers']['core']['level'] = 'DEBUG'

# =============================================================================
# DEVELOPMENT FLAGS
# =============================================================================
print("[FLAGS] 🛠️  DEBUG=True (development mode)")
print("[FLAGS] Mock Services Status:")
print(f"[FLAGS]   USE_AI_RECS_MOCK: {'🟢 DISABLED' if not USE_AI_RECS_MOCK else '🔴 ENABLED'}")
print(f"[FLAGS]   USE_ALPHA_MOCK: {'🟢 DISABLED' if not USE_ALPHA_MOCK else '🔴 ENABLED'}")
print(f"[FLAGS]   USE_BROKER_MOCK: {'🟢 DISABLED' if not USE_BROKER_MOCK else '🔴 ENABLED'}")
print(f"[FLAGS]   USE_FINNHUB_MOCK: {'🟢 DISABLED' if not USE_FINNHUB_MOCK else '🔴 ENABLED'}")
print(f"[FLAGS]   USE_LEARNING_MOCK: {'🟢 DISABLED' if not USE_LEARNING_MOCK else '🔴 ENABLED'}")
print(f"[FLAGS]   USE_MARKET_MOCK: {'🟢 DISABLED' if not USE_MARKET_MOCK else '🔴 ENABLED'}")
print(f"[FLAGS]   USE_NOTIF_MOCK: {'🟢 DISABLED' if not USE_NOTIF_MOCK else '🔴 ENABLED'}")
print(f"[FLAGS]   USE_PAYMENTS_MOCK: {'🟢 DISABLED' if not USE_PAYMENTS_MOCK else '🔴 ENABLED'}")
print(f"[FLAGS]   USE_POLYGON_MOCK: {'🟢 DISABLED' if not USE_POLYGON_MOCK else '🔴 ENABLED'}")
print(f"[FLAGS]   USE_SBLOC_MOCK: {'🟢 DISABLED' if not USE_SBLOC_MOCK else '🔴 ENABLED'}")

# =============================================================================
# ALPACA API CONFIGURATION
# =============================================================================
ALPACA_API_KEY = os.getenv('ALPACA_API_KEY', '')
ALPACA_SECRET_KEY = os.getenv('ALPACA_SECRET_KEY', '')
ALPACA_BASE_URL = os.getenv('ALPACA_BASE_URL', 'https://broker-api.sandbox.alpaca.markets')
ALPACA_DATA_URL = os.getenv('ALPACA_DATA_URL', 'https://data.sandbox.alpaca.markets')
ALPACA_CRYPTO_URL = os.getenv('ALPACA_CRYPTO_URL', 'https://api.sandbox.alpaca.markets')
ALPACA_PAPER_TRADING = os.getenv('ALPACA_PAPER_TRADING', 'true').lower() == 'true'
ALPACA_ENVIRONMENT = os.getenv('ALPACA_ENVIRONMENT', 'sandbox')

# Alpaca Integration Flags - ENABLED for real trading
USE_ALPACA = os.getenv('USE_ALPACA', 'true').lower() == 'true'
USE_ALPACA_BROKER = os.getenv('USE_ALPACA_BROKER', 'true').lower() == 'true'
USE_ALPACA_CRYPTO = os.getenv('USE_ALPACA_CRYPTO', 'true').lower() == 'true'

# Disable broker mock for real trading
USE_BROKER_MOCK = False

print(f"[FLAGS] Alpaca Integration Status:")
print(f"[FLAGS]   USE_ALPACA: {'🟢 ENABLED' if USE_ALPACA else '🔴 DISABLED'}")
print(f"[FLAGS]   USE_ALPACA_BROKER: {'🟢 ENABLED' if USE_ALPACA_BROKER else '🔴 DISABLED'}")
print(f"[FLAGS]   USE_ALPACA_CRYPTO: {'🟢 ENABLED' if USE_ALPACA_CRYPTO else '🔴 DISABLED'}")
print(f"[FLAGS]   ALPACA_ENVIRONMENT: {ALPACA_ENVIRONMENT}")
print(f"[FLAGS]   ALPACA_PAPER_TRADING: {'🟢 ENABLED' if ALPACA_PAPER_TRADING else '🔴 DISABLED'}")
print("=" * 60)

# =============================================================================
# SANITY CHECKS - DEBUGGING INFO
# =============================================================================
print(f"[BOOT] Using settings: {os.environ.get('DJANGO_SETTINGS_MODULE')}")
print(f"[BOOT] DB NAME: {DATABASES['default'].get('NAME')}")
print(f"[BOOT] DB HOST: {DATABASES['default'].get('HOST')}")
print(f"[BOOT] DB PORT: {DATABASES['default'].get('PORT')}")
print(f"[BOOT] AUTH_USER_MODEL: {AUTH_USER_MODEL}")
print("=" * 60)
