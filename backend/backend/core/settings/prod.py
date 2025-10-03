"""
Production Django settings for RichesReach project.
"""
from .base import *
import os

# Production Security Settings
DEBUG = False
ALLOWED_HOSTS = [
    'app.richesreach.net',
    'riches-reach-alb-1199497064.us-east-1.elb.amazonaws.com',
    'localhost',
    '127.0.0.1',
]

# Security Headers
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True

# CORS Configuration
CORS_ALLOWED_ORIGINS = [
    'https://app.richesreach.net',
    'https://riches-reach-alb-1199497064.us-east-1.elb.amazonaws.com',
]
CORS_ALLOW_CREDENTIALS = True

# CSRF Configuration
CSRF_TRUSTED_ORIGINS = [
    'https://app.richesreach.net',
    'https://riches-reach-alb-1199497064.us-east-1.elb.amazonaws.com',
]

# Database Configuration (Production)
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.getenv('DB_NAME', 'richesreach_prod'),
        'USER': os.getenv('DB_USER', 'postgres'),
        'PASSWORD': os.getenv('DB_PASSWORD', ''),
        'HOST': os.getenv('DB_HOST', 'localhost'),
        'PORT': os.getenv('DB_PORT', '5432'),
        'OPTIONS': {
            'sslmode': 'require',
        },
    }
}

# Redis Configuration (Production)
REDIS_URL = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': REDIS_URL,
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
            'CONNECTION_POOL_KWARGS': {
                'max_connections': 50,
                'retry_on_timeout': True,
            },
        }
    }
}

# Celery Configuration (Production)
CELERY_BROKER_URL = REDIS_URL
CELERY_RESULT_BACKEND = 'django-db'
CELERY_WORKER_PREFETCH_MULTIPLIER = 1
CELERY_TASK_ACKS_LATE = True
CELERY_WORKER_DISABLE_RATE_LIMITS = False

# API Keys (Production)
ALPHA_VANTAGE_API_KEY = os.getenv('ALPHA_VANTAGE_API_KEY')
FINNHUB_API_KEY = os.getenv('FINNHUB_API_KEY')
NEWS_API_KEY = os.getenv('NEWS_API_KEY')
POLYGON_API_KEY = os.getenv('POLYGON_API_KEY')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')

# Feature Flags (Production)
USE_OPENAI = os.getenv('USE_OPENAI', 'true').lower() == 'true'
USE_YODLEE = os.getenv('USE_YODLEE', 'false').lower() == 'true'
USE_FINNHUB = os.getenv('USE_FINNHUB', 'true').lower() == 'true'
DISABLE_ALPHA_VANTAGE = os.getenv('DISABLE_ALPHA_VANTAGE', 'false').lower() == 'true'

# Logging Configuration (Production)
LOGGING['handlers']['file']['filename'] = '/var/log/richesreach/django.log'
LOGGING['handlers']['file']['class'] = 'logging.handlers.RotatingFileHandler'
LOGGING['handlers']['file']['maxBytes'] = 1024 * 1024 * 10  # 10MB
LOGGING['handlers']['file']['backupCount'] = 5

# Add Sentry for error tracking
if os.getenv('SENTRY_DSN'):
    import sentry_sdk
    from sentry_sdk.integrations.django import DjangoIntegration
    from sentry_sdk.integrations.celery import CeleryIntegration
    
    sentry_sdk.init(
        dsn=os.getenv('SENTRY_DSN'),
        integrations=[
            DjangoIntegration(),
            CeleryIntegration(),
        ],
        traces_sample_rate=0.1,
        send_default_pii=True,
    )

# Rate Limiting
RATELIMIT_ENABLE = True
RATELIMIT_USE_CACHE = 'default'

# Performance Settings
CONN_MAX_AGE = 60
DATA_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024  # 10MB
FILE_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024  # 10MB

# Static Files (Production)
STATIC_ROOT = '/var/www/richesreach/static/'
MEDIA_ROOT = '/var/www/richesreach/media/'

# Email Configuration (Production)
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = os.getenv('EMAIL_HOST', 'smtp.gmail.com')
EMAIL_PORT = int(os.getenv('EMAIL_PORT', '587'))
EMAIL_USE_TLS = True
EMAIL_HOST_USER = os.getenv('EMAIL_HOST_USER', '')
EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD', '')
DEFAULT_FROM_EMAIL = os.getenv('DEFAULT_FROM_EMAIL', 'noreply@richesreach.net')

# Health Check Configuration
HEALTH_CHECK = {
    'DISK_USAGE_MAX': 90,  # percent
    'MEMORY_MIN': 100,     # in MB
}

print(f"[PROD] Production settings loaded - DEBUG={DEBUG}")
print(f"[PROD] Database: {DATABASES['default']['NAME']}")
print(f"[PROD] Redis: {REDIS_URL}")
print(f"[PROD] Allowed hosts: {ALLOWED_HOSTS}")
