"""
Local development settings that connect to production database
This allows you to test fixes locally with real production data
"""

import os
from pathlib import Path
from datetime import timedelta
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Build paths inside the project
BASE_DIR = Path(__file__).resolve().parent.parent

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.getenv('SECRET_KEY', 'your-production-secret-key-here')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True  # Enable debug for local development

# Host / CSRF
ALLOWED_HOSTS = ['localhost', 'process.env.API_HOST || "localhost"', '0.0.0.0', '*']

# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'channels',
    'core',
    'graphene_django',
    'corsheaders',
    'django_celery_results',
    'rest_framework',
    'rest_framework.authtoken',
]

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

WSGI_APPLICATION = 'richesreach.wsgi.application'

# Database - CONNECT TO PRODUCTION DATABASE
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.getenv('DJANGO_DB_NAME', 'appdb'),
        'USER': os.getenv('DJANGO_DB_USER', 'appuser'),
        'PASSWORD': os.getenv('DJANGO_DB_PASSWORD', 'AppPass2025Simple'),
        'HOST': os.getenv('DJANGO_DB_HOST', 'riches-reach-postgres.cmhsue8oy30k.us-east-1.rds.amazonaws.com'),
        'PORT': os.getenv('DJANGO_DB_PORT', '5432'),
        'OPTIONS': {
            'sslmode': os.getenv('SSLMODE', 'require'),
        },
        'CONN_MAX_AGE': 600,
    }
}

# GraphQL Configuration - Use full schema
GRAPHQL_MODE = 'full'
GRAPHENE = {
    'SCHEMA': 'core.schema.schema',
    'MIDDLEWARE': [
        'graphql_jwt.middleware.JSONWebTokenMiddleware',
    ],
}

# JWT configuration
GRAPHQL_JWT = {
    'JWT_VERIFY_EXPIRATION': True,
    'JWT_LONG_RUNNING_REFRESH_TOKEN': True,
    'JWT_EXPIRATION_DELTA': timedelta(minutes=60),
    'JWT_REFRESH_EXPIRATION_DELTA': timedelta(days=7),
}

# CORS settings for local development
CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://localhost:3000",
    "http://localhost:8081",  # Expo dev server
    "http://localhost:8081",
]

CORS_ALLOW_CREDENTIALS = True

# Security settings (relaxed for local development)
SECURE_SSL_REDIRECT = False
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False

# Static files
STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

# Media files
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# Internationalization
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Logging configuration for local development
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO',
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        },
        'core': {
            'handlers': ['console'],
            'level': 'DEBUG',
            'propagate': False,
        },
    },
}

print("🔧 Local development mode with production database")
print(f"📊 Database: {DATABASES['default']['HOST']}:{DATABASES['default']['PORT']}/{DATABASES['default']['NAME']}")
print(f"🌐 Debug mode: {DEBUG}")
print(f"🔗 CORS enabled for local development")
