"""
Development Django settings for RichesReach project.
"""
from .base import *

# Development Security Settings
DEBUG = True
ALLOWED_HOSTS = ["*"]  # dev only - includes current LAN IP

# CORS Configuration (Development)
CORS_ALLOW_ALL_ORIGINS = True
CORS_ALLOW_CREDENTIALS = True

# CSRF Configuration (Development)
CSRF_TRUSTED_ORIGINS = [
    "http://172.20.10.8:8000",
    "http://localhost:8000", 
    "http://127.0.0.1:8000",
    "http://192.168.1.151:8000"
]

# Development Database
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'dev',
        'USER': 'postgres',
        'PASSWORD': '',
        'HOST': 'localhost',
        'PORT': '5432',
    }
}

# Development Redis
REDIS_URL = 'redis://localhost:6379/0'
CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': REDIS_URL,
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
        }
    }
}

# Development API Keys (from environment or defaults)
ALPHA_VANTAGE_API_KEY = os.getenv('ALPHA_VANTAGE_API_KEY', 'OHYSFF1AE446O7CR')
FINNHUB_API_KEY = os.getenv('FINNHUB_API_KEY', 'd2rnitpr01qv11lfegugd2rnitpr01qv11lfegv0')
NEWS_API_KEY = os.getenv('NEWS_API_KEY', '94a335c7316145f79840edd62f77e11e')
POLYGON_API_KEY = os.getenv('POLYGON_API_KEY', 'uuKmy9dPAjaSVXVEtCumQPga1dqEPDS2')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY', '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')

# Development Feature Flags
USE_OPENAI = os.getenv('USE_OPENAI', 'false').lower() == 'true'
USE_YODLEE = os.getenv('USE_YODLEE', 'false').lower() == 'true'
USE_FINNHUB = os.getenv('USE_FINNHUB', 'true').lower() == 'true'
DISABLE_ALPHA_VANTAGE = os.getenv('DISABLE_ALPHA_VANTAGE', 'true').lower() == 'true'

# Development Logging
LOGGING['handlers']['console']['level'] = 'DEBUG'
LOGGING['loggers']['django']['level'] = 'DEBUG'
LOGGING['loggers']['core']['level'] = 'DEBUG'

# Development Email (Console backend)
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# Development Static Files
STATICFILES_DIRS = [
    BASE_DIR / 'static',
]

print(f"[DEV] Development settings loaded - DEBUG={DEBUG}")
print(f"[DEV] Database: {DATABASES['default']['NAME']}")
print(f"[DEV] Redis: {REDIS_URL}")
print(f"[DEV] API Keys configured: Alpha Vantage={bool(ALPHA_VANTAGE_API_KEY)}, Finnhub={bool(FINNHUB_API_KEY)}")
