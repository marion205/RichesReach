"""
Production settings for RichesReach
"""
import os
from .settings import *

# Production environment
DEBUG = False
ALLOWED_HOSTS = ['api.richesreach.com', 'www.richesreach.com', 'process.env.API_HOST || "localhost"', 'localhost']

# Database - PostgreSQL for production
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.getenv('DB_NAME', 'richesreach_prod'),
        'USER': os.getenv('DB_USER', 'postgres'),
        'PASSWORD': os.getenv('DB_PASSWORD', ''),
        'HOST': os.getenv('DB_HOST', 'localhost'),
        'PORT': os.getenv('DB_PORT', '5432'),
    }
}

# Redis for Celery
CELERY_BROKER_URL = os.getenv('REDIS_URL', 'redis://process.env.REDIS_HOST || "localhost:6379"/0')
CELERY_RESULT_BACKEND = os.getenv('REDIS_URL', 'redis://process.env.REDIS_HOST || "localhost:6379"/0')

# Security settings
SECRET_KEY = os.getenv('SECRET_KEY', 'your-production-secret-key-here')
SECURE_SSL_REDIRECT = True
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True

# CORS settings for production
CORS_ALLOWED_ORIGINS = [
    "https://www.richesreach.com",
    "https://richesreach.com",
    "https://app.richesreach.com",
]

# Static files
STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# Logging
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': '/var/log/richesreach/django.log',
            'formatter': 'verbose',
        },
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
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

# Cache settings
CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': os.getenv('REDIS_URL', 'redis://process.env.REDIS_HOST || "localhost:6379"/1'),
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
        }
    }
}

# Email settings for production
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = os.getenv('EMAIL_HOST', 'smtp.gmail.com')
EMAIL_PORT = int(os.getenv('EMAIL_PORT', '587'))
EMAIL_USE_TLS = True
EMAIL_HOST_USER = os.getenv('EMAIL_HOST_USER', '')
EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD', '')

# API Keys for production - use environment variables only
ALPHA_VANTAGE_API_KEY = os.getenv('ALPHA_VANTAGE_API_KEY')
FINNHUB_API_KEY = os.getenv('FINNHUB_API_KEY')
NEWS_API_KEY = os.getenv('NEWS_API_KEY')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')

# Real-time data update settings - disable during startup to prevent 403 errors
REALTIME_UPDATE_ENABLED = os.getenv('REALTIME_UPDATE_ENABLED', 'False').lower() == 'true'
REALTIME_UPDATE_INTERVAL = 300  # 5 minutes
PRIORITY_UPDATE_INTERVAL = 60   # 1 minute

# Performance settings
CONN_MAX_AGE = 60
DATA_UPLOAD_MAX_MEMORY_SIZE = 10485760  # 10MB
FILE_UPLOAD_MAX_MEMORY_SIZE = 10485760  # 10MB
