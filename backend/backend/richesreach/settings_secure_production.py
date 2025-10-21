"""
Secure Production Settings for RichesReach
Implements comprehensive security hardening for production deployment
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
SECRET_KEY = os.getenv('SECRET_KEY')
if not SECRET_KEY:
    raise ValueError("SECRET_KEY environment variable is required")

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = False

# Host / CSRF Configuration
ALLOWED_HOSTS = os.getenv("ALLOWED_HOSTS", "localhost").split(",")
CSRF_TRUSTED_ORIGINS = [f"https://{h}" for h in ALLOWED_HOSTS] + [f"http://{h}" for h in ALLOWED_HOSTS]

# HTTPS Security Settings
SECURE_SSL_REDIRECT = True  # Redirect HTTP to HTTPS
SECURE_HSTS_SECONDS = 31536000  # 1 year
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_BROWSER_XSS_FILTER = True
X_FRAME_OPTIONS = 'DENY'
SECURE_REFERRER_POLICY = 'strict-origin-when-cross-origin'

# Correct client IP/host when behind ALB
USE_X_FORWARDED_HOST = True

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
    'graphql_jwt.refresh_token.apps.RefreshTokenConfig',
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
    # Custom security middleware
    'core.security.graphql_security.GraphQLSecurityMiddleware',
    'core.security.jwt_security.SecureGraphQLJWTMiddleware',
    'core.security.jwt_security.CSRFProtectionMiddleware',
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
ASGI_APPLICATION = 'richesreach.asgi.application'

# Database Configuration
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.getenv('DB_NAME'),
        'USER': os.getenv('DB_USER'),
        'PASSWORD': os.getenv('DB_PASSWORD'),
        'HOST': os.getenv('DB_HOST'),
        'PORT': os.getenv('DB_PORT', '5432'),
        'OPTIONS': {
            'sslmode': 'require',
        },
        'CONN_MAX_AGE': 60,  # Connection pooling
    }
}

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
        'OPTIONS': {
            'min_length': 12,  # Stronger password requirement
        }
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
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

# Media files
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# CORS Configuration - Restrictive for production
CORS_ALLOWED_ORIGINS = [
    "https://app.richesreach.com",
    "https://richesreach.com",
    # Add your production frontend URLs here
]

CORS_ALLOW_CREDENTIALS = True
CORS_ALLOW_ALL_ORIGINS = False  # Security: Don't allow all origins in production

# CORS Headers
CORS_ALLOW_HEADERS = [
    'accept',
    'accept-encoding',
    'authorization',
    'content-type',
    'dnt',
    'origin',
    'user-agent',
    'x-csrftoken',
    'x-requested-with',
    'x-csrf-token',  # For GraphQL mutations
]

# Redis Configuration
REDIS_URL = os.getenv('REDIS_URL', 'redis://localhost:6379/0')

# Cache Configuration
CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': REDIS_URL,
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
            'CONNECTION_POOL_KWARGS': {
                'max_connections': 50,
                'retry_on_timeout': True,
            }
        },
        'KEY_PREFIX': 'richesreach',
        'TIMEOUT': 300,  # 5 minutes default
    }
}

# Session Configuration
SESSION_ENGINE = 'django.contrib.sessions.backends.cache'
SESSION_CACHE_ALIAS = 'default'
SESSION_COOKIE_AGE = 3600  # 1 hour
SESSION_COOKIE_SECURE = True
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'Strict'

# CSRF Configuration
CSRF_COOKIE_SECURE = True
CSRF_COOKIE_HTTPONLY = True
CSRF_COOKIE_SAMESITE = 'Strict'
CSRF_USE_SESSIONS = True

# Celery Configuration
CELERY_BROKER_URL = REDIS_URL
CELERY_RESULT_BACKEND = REDIS_URL
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = TIME_ZONE
CELERY_TASK_ALWAYS_EAGER = False
CELERY_TASK_EAGER_PROPAGATES = True

# Channels Configuration
CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels_redis.core.RedisChannelLayer',
        'CONFIG': {
            'hosts': [REDIS_URL],
        },
    },
}

# GraphQL Security Configuration
GRAPHENE = {
    'SCHEMA': 'core.schema.schema',
    'MIDDLEWARE': [
        'graphql_jwt.middleware.JSONWebTokenMiddleware',
    ],
}

# GraphQL Security Settings
GRAPHQL_MAX_DEPTH = 10
GRAPHQL_MAX_COMPLEXITY = 1000
GRAPHQL_RATE_LIMIT_PER_MINUTE = 60
GRAPHQL_BLOCK_INTROSPECTION = True

# JWT Configuration - Enhanced Security
GRAPHQL_JWT = {
    'JWT_VERIFY_EXPIRATION': True,
    'JWT_LONG_RUNNING_REFRESH_TOKEN': True,
    'JWT_EXPIRATION_DELTA': timedelta(minutes=15),  # Short-lived access tokens
    'JWT_REFRESH_EXPIRATION_DELTA': timedelta(days=7),  # Longer-lived refresh tokens
    'JWT_ALGORITHM': 'HS256',
    'JWT_AUTH_HEADER_PREFIX': 'Bearer',
    'JWT_AUTH_COOKIE': None,  # Don't use cookies for JWT
    'JWT_VERIFY': True,
    'JWT_VERIFY_EXPIRATION': True,
    'JWT_LEEWAY': 0,
    'JWT_ISSUER': 'richesreach-api',
    'JWT_AUDIENCE': 'richesreach-client',
}

# API Keys
FINNHUB_API_KEY = os.getenv('FINNHUB_API_KEY', '')
ALPHA_VANTAGE_API_KEY = os.getenv('ALPHA_VANTAGE_API_KEY', '')
POLYGON_API_KEY = os.getenv('POLYGON_API_KEY', '')
NEWS_API_KEY = os.getenv('NEWS_API_KEY', '')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY', '')

# API Service Configuration
DISABLE_ALPHA_VANTAGE = os.getenv('DISABLE_ALPHA_VANTAGE', 'false').lower() == 'true'
DISABLE_FINNHUB = os.getenv('DISABLE_FINNHUB', 'false').lower() == 'true'
DISABLE_POLYGON = os.getenv('DISABLE_POLYGON', 'false').lower() == 'true'

# AI Service Configuration
USE_OPENAI = bool(OPENAI_API_KEY)
OPENAI_MODEL = os.getenv('OPENAI_MODEL', 'gpt-4')
OPENAI_MAX_TOKENS = int(os.getenv('OPENAI_MAX_TOKENS', '4000'))
OPENAI_TEMPERATURE = float(os.getenv('OPENAI_TEMPERATURE', '1.0'))  # GPT-5 compatible

# Email Configuration
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = os.getenv('EMAIL_HOST', 'smtp.gmail.com')
EMAIL_PORT = int(os.getenv('EMAIL_PORT', '587'))
EMAIL_USE_TLS = True
EMAIL_HOST_USER = os.getenv('EMAIL_HOST_USER')
EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD')
DEFAULT_FROM_EMAIL = os.getenv('DEFAULT_FROM_EMAIL')

# Custom user model
AUTH_USER_MODEL = 'core.User'

# Logging Configuration
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'json': {
            '()': 'core.security.secure_logging.SecureJSONFormatter',
        },
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'json',
        },
        'security_file': {
            'class': 'logging.FileHandler',
            'filename': '/var/log/richesreach/security.log',
            'formatter': 'json',
        },
        'error_file': {
            'class': 'logging.FileHandler',
            'filename': '/var/log/richesreach/error.log',
            'formatter': 'json',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        },
        'django.security': {
            'handlers': ['security_file'],
            'level': 'WARNING',
            'propagate': False,
        },
        'security_audit': {
            'handlers': ['security_file'],
            'level': 'INFO',
            'propagate': False,
        },
        'graphql_audit': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        },
        'slow_queries': {
            'handlers': ['console'],
            'level': 'WARNING',
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

# Security Headers
SECURE_CROSS_ORIGIN_OPENER_POLICY = 'same-origin'
SECURE_REFERRER_POLICY = 'strict-origin-when-cross-origin'

# File Upload Security
FILE_UPLOAD_MAX_MEMORY_SIZE = 5242880  # 5MB
DATA_UPLOAD_MAX_MEMORY_SIZE = 5242880  # 5MB
DATA_UPLOAD_MAX_NUMBER_FIELDS = 1000

# Admin Security
ADMIN_URL = os.getenv('ADMIN_URL', 'admin/')  # Change default admin URL

# Performance Settings
CONN_MAX_AGE = 60  # Database connection pooling
