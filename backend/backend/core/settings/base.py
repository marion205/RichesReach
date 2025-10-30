"""
Base Django settings for RichesReach project.
"""
from pathlib import Path
import os
from datetime import timedelta
import environ

# Load environment variables from .env file
env = environ.Env()
environ.Env.read_env()

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = env('SECRET_KEY', default='django-insecure-wk_qy339*l)1xg=(f6_e@9+d7sgi7%#0t!e17a3nkeu&p#@zq9')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = env.bool('DEBUG', default=True)

# Application definition
DJANGO_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
]

THIRD_PARTY_APPS = [
    'corsheaders',
    'graphene_django',
    'rest_framework',
    'channels',
    'django_celery_results',
]

LOCAL_APPS = [
    'core',
]

INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'richesreach.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'core.wsgi.application'
ASGI_APPLICATION = 'core.asgi.application'

# Database
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': env('DB_NAME', default='dev'),
        'USER': env('DB_USER', default='postgres'),
        'PASSWORD': env('DB_PASSWORD', default=''),
        'HOST': env('DB_HOST', default='localhost'),
        'PORT': env('DB_PORT', default='5432'),
    }
}

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# Internationalization
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Custom User Model
AUTH_USER_MODEL = 'core.User'

# GraphQL Configuration
GRAPHENE = {
    'SCHEMA': 'core.schema.schema',
    'MIDDLEWARE': [
        'graphql_jwt.middleware.JSONWebTokenMiddleware',
    ],
}

# JWT Configuration
GRAPHQL_JWT = {
    'JWT_VERIFY_EXPIRATION': True,
    'JWT_LONG_RUNNING_REFRESH_TOKEN': True,
    'JWT_EXPIRATION_DELTA': timedelta(minutes=60),
    'JWT_REFRESH_EXPIRATION_DELTA': timedelta(days=7),
}

# Django Channels
CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels_redis.core.RedisChannelLayer',
        'CONFIG': {
            "hosts": [env('REDIS_URL', default='redis://process.env.REDIS_HOST || "localhost:6379"/1')],
        },
    },
}

# Celery Configuration
CELERY_BROKER_URL = env('REDIS_URL', default='redis://process.env.REDIS_HOST || "localhost:6379"/0')
CELERY_RESULT_BACKEND = 'django-db'
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = TIME_ZONE

# API Keys Configuration
ALPHA_VANTAGE_API_KEY = env('ALPHA_VANTAGE_API_KEY', default=None)
FINNHUB_API_KEY = env('FINNHUB_API_KEY', default=None)
NEWS_API_KEY = env('NEWS_API_KEY', default=None)
POLYGON_API_KEY = env('POLYGON_API_KEY', default=None)
OPENAI_API_KEY = env('OPENAI_API_KEY', default=None)

# Yodlee Configuration
YODLEE_BASE_URL = env('YODLEE_BASE_URL', default='https://sandbox.api.yodlee.com/ysl')
YODLEE_CLIENT_ID = env('YODLEE_CLIENT_ID', default='')
YODLEE_CLIENT_SECRET = env('YODLEE_CLIENT_SECRET', default='')
YODLEE_SECRET = env('YODLEE_SECRET', default='')
YODLEE_LOGIN_NAME = env('YODLEE_LOGIN_NAME', default='')
YODLEE_FASTLINK_URL = env('YODLEE_FASTLINK_URL', default='https://sandbox.api.yodlee.com/ysl/fastlink')

# Feature Flags
USE_OPENAI = env.bool('USE_OPENAI', default=False)
USE_YODLEE = env.bool('USE_YODLEE', default=False)
USE_FINNHUB = env.bool('USE_FINNHUB', default=True)
DISABLE_ALPHA_VANTAGE = env.bool('DISABLE_ALPHA_VANTAGE', default=True)

# GraphQL Configuration
GRAPHQL_MODE = env('GRAPHQL_MODE', default='standard')

# Logging Configuration
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
        'json': {
            'format': '{"level": "%(levelname)s", "time": "%(asctime)s", "module": "%(module)s", "message": "%(message)s"}',
        },
    },
    'filters': {
        'redact_secrets': {
            '()': 'core.logging.RedactSecretsFilter',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
            'filters': ['redact_secrets'],
        },
        'file': {
            'class': 'logging.FileHandler',
            'filename': BASE_DIR / 'logs' / 'django.log',
            'formatter': 'json',
            'filters': ['redact_secrets'],
        },
    },
    'root': {
        'handlers': ['console'],
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

# Cache Configuration
CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': env('REDIS_URL', default='redis://process.env.REDIS_HOST || "localhost:6379"/2'),
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
        }
    }
}

# Session Configuration
SESSION_ENGINE = 'django.contrib.sessions.backends.cache'
SESSION_CACHE_ALIAS = 'default'
SESSION_COOKIE_AGE = 86400  # 24 hours

# Stock Analysis Configuration
STOCK_ANALYSIS_CONFIG = {
    'CACHE_TIMEOUT': {
        'QUOTE_DATA': 300,  # 5 minutes for real-time quotes
        'OVERVIEW_DATA': 3600,  # 1 hour for company overview
        'HISTORICAL_DATA': 1800,  # 30 minutes for historical data
        'BENCHMARK_DATA': 600,  # 10 minutes for benchmark data
    },
    'RATE_LIMITS': {
        'ALPHA_VANTAGE': {'limit': 5, 'window': 60},  # 5 requests per minute
        'FINNHUB': {'limit': 60, 'window': 60},  # 60 requests per minute
        'POLYGON': {'limit': 5, 'window': 60},  # 5 requests per minute
    }
}
