"""
Production Settings for RichesReach
Clean production configuration with all real services enabled
"""

import os
from .settings import *  # Import base settings

print("[BOOT] Using PRODUCTION SETTINGS (settings_production_clean.py)")
print("[BOOT] Debug mode: False")
print("[BOOT] All services: REAL (no mocks)")
print("[BOOT] Security: ENABLED")

# =============================================================================
# SECURITY & DEBUG
# =============================================================================
DEBUG = False
SECRET_KEY = os.getenv('SECRET_KEY', 'your-production-secret-key-here')

# =============================================================================
# HOSTS & CORS
# =============================================================================
ALLOWED_HOSTS = os.getenv("ALLOWED_HOSTS", "riches-reach-alb-1199497064.us-east-1.elb.amazonaws.com,localhost,127.0.0.1").split(",")
CSRF_TRUSTED_ORIGINS = [f"http://{h}" for h in ALLOWED_HOSTS] + [f"https://{h}" for h in ALLOWED_HOSTS]

# =============================================================================
# DATABASE (PRODUCTION)
# =============================================================================
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.getenv('DJANGO_DB_NAME', 'appdb'),
        'USER': os.getenv('DJANGO_DB_USER', 'postgres'),
        'PASSWORD': os.getenv('DJANGO_DB_PASSWORD', ''),
        'HOST': os.getenv('DJANGO_DB_HOST', 'localhost'),
        'PORT': os.getenv('DJANGO_DB_PORT', '5432'),
        'OPTIONS': {
            'sslmode': 'require',
        },
    }
}

# =============================================================================
# SECURITY SETTINGS
# =============================================================================
SECURE_SSL_REDIRECT = True
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_BROWSER_XSS_FILTER = True
X_FRAME_OPTIONS = 'DENY'
SECURE_REFERRER_POLICY = 'same-origin'

# =============================================================================
# CORS (PRODUCTION)
# =============================================================================
CORS_ALLOW_ALL_ORIGINS = False
CORS_ALLOWED_ORIGINS = [
    "https://app.richesreach.net",
    "https://richesreach.net",
    # Add your production domains here
]

# =============================================================================
# JWT AUTHENTICATION (REAL)
# =============================================================================
GRAPHENE["MIDDLEWARE"] = ["graphql_jwt.middleware.JSONWebTokenMiddleware"]
AUTHENTICATION_BACKENDS = [
    "graphql_jwt.backends.JSONWebTokenBackend",
    "django.contrib.auth.backends.ModelBackend",
]

# =============================================================================
# ALL SERVICES REAL (NO MOCKS)
# =============================================================================
USE_REAL_MARKET_DATA = True
USE_ALPHA_MOCK = False
USE_POLYGON_MOCK = False
USE_FINNHUB_MOCK = False
USE_MARKET_MOCK = False
USE_AI_RECS_MOCK = False
USE_LEARNING_MOCK = False
USE_BROKER_MOCK = False
USE_PAYMENTS_MOCK = False
USE_NOTIF_MOCK = False
USE_YODLEE = True
USE_SBLOC_AGGREGATOR = True
USE_SBLOC_MOCK = False
USE_OPENAI = True

# =============================================================================
# API KEYS (REAL)
# =============================================================================
ALPHA_VANTAGE_API_KEY = os.getenv('ALPHA_VANTAGE_API_KEY', '')
POLYGON_API_KEY = os.getenv('POLYGON_API_KEY', '')
FINNHUB_API_KEY = os.getenv('FINNHUB_API_KEY', '')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY', '')

# =============================================================================
# GRAPHIQL (DISABLED IN PRODUCTION)
# =============================================================================
GRAPHENE['GRAPHIQL'] = False

# =============================================================================
# LOGGING (PRODUCTION)
# =============================================================================
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'standard': {
            'format': '%(asctime)s %(levelname)s %(name)s: %(message)s'
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'standard',
            'level': 'INFO',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        },
        'core': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO',
    },
}

print("[FLAGS] 🚀 PRODUCTION MODE - All services REAL")
print("=" * 60)
