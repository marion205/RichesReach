"""
Production settings for RichesReach
"""
import os
from pathlib import Path
from datetime import timedelta
from dotenv import load_dotenv
from django.core.exceptions import ImproperlyConfigured

print("[BOOT] settings file =", __file__)

# Load environment variables
load_dotenv()

# Build paths inside the project
BASE_DIR = Path(__file__).resolve().parent.parent

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.getenv('SECRET_KEY', 'your-production-secret-key-here')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = False

# SBLOC Configuration
USE_SBLOC_MOCK = os.getenv('USE_SBLOC_MOCK', 'true').lower() == 'true'
USE_SBLOC_AGGREGATOR = os.getenv('USE_SBLOC_AGGREGATOR', 'false').lower() == 'true'

# JWT Configuration (using correct GRAPHQL_JWT settings for django-graphql-jwt)
GRAPHQL_JWT = {
    'JWT_VERIFY_EXPIRATION': True,
    'JWT_EXPIRATION_DELTA': timedelta(minutes=60),   # access token
    'JWT_REFRESH_EXPIRATION_DELTA': timedelta(days=7),
    'JWT_LONG_RUNNING_REFRESH_TOKEN': True,          # persisted refresh pattern
    'JWT_ALGORITHM': 'HS256',
    'JWT_SECRET_KEY': SECRET_KEY,
    'JWT_LEEWAY': 0,
    'JWT_AUTH_HEADER_PREFIX': 'Bearer',
    'JWT_AUTH_COOKIE': None,
}

# Authentication backends
AUTHENTICATION_BACKENDS = [
    'graphql_jwt.backends.JSONWebTokenBackend',
    'django.contrib.auth.backends.ModelBackend',
]

# Host / CSRF
ALLOWED_HOSTS = os.getenv("ALLOWED_HOSTS","riches-reach-alb-1199497064.us-east-1.elb.amazonaws.com,localhost,127.0.0.1").split(",")
# Add wildcard support for ALB internal IPs
ALLOWED_HOSTS.append("*")
CSRF_TRUSTED_ORIGINS = [f"http://{h}" for h in ALLOWED_HOSTS if h != "*"] + [f"https://{h}" for h in ALLOWED_HOSTS if h != "*"]

# If you do NOT have a 443 listener yet:
SECURE_SSL_REDIRECT = False  # flip to True only when 443 is live

# Correct client IP/host when behind ALB
USE_X_FORWARDED_HOST = True
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

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
    'graphql_jwt.refresh_token',  # Required for persisted refresh tokens
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

# GraphQL Configuration
GRAPHENE = {
    'SCHEMA': 'core.schema.schema',
    'MIDDLEWARE': [
        'graphql_jwt.middleware.JSONWebTokenMiddleware',
    ],
}

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

# Database - Production Configuration
def get_env_variable(var_name, default=None):
    """Get environment variable or raise error if required"""
    try:
        return os.environ[var_name]
    except KeyError:
        if default is not None:
            return default
        error_msg = f"Set the {var_name} environment variable"
        raise ImproperlyConfigured(error_msg)

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': get_env_variable('DJANGO_DB_NAME', 'appdb'),
        'USER': get_env_variable('DJANGO_DB_USER', 'appuser'),
        'PASSWORD': get_env_variable('DJANGO_DB_PASSWORD'),
        'HOST': get_env_variable('DJANGO_DB_HOST'),
        'PORT': get_env_variable('DJANGO_DB_PORT', '5432'),
        'OPTIONS': {
            'sslmode': os.getenv('SSLMODE', 'require'),
        },
        'CONN_MAX_AGE': 600,  # Reuse connections for 10 minutes
    }
}

# Yodlee Configuration
YODLEE_BASE_URL = os.getenv('YODLEE_BASE_URL', 'https://api.yodlee.com/ysl')
YODLEE_CLIENT_ID = os.getenv('YODLEE_CLIENT_ID', '')
YODLEE_CLIENT_SECRET = os.getenv('YODLEE_CLIENT_SECRET', '')
YODLEE_SECRET = YODLEE_CLIENT_SECRET  # Alias for compatibility
YODLEE_LOGIN_NAME = os.getenv('YODLEE_LOGIN_NAME', 'test-login-name')
YODLEE_FASTLINK_URL = os.getenv('YODLEE_FASTLINK_URL', 'https://test.fastlink.yodlee.com')

# GraphQL Configuration - FORCE PRODUCTION MODE
GRAPHQL_MODE = 'full'  # Force full schema for real ML/AI data

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
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

# Media files
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# CORS settings
CORS_ALLOWED_ORIGINS = [
    "https://your-frontend-domain.com",
    "https://www.your-frontend-domain.com",
]

CORS_ALLOW_CREDENTIALS = True

# Security settings
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True

# HTTPS settings (uncomment when using HTTPS)
# SECURE_SSL_REDIRECT = True
# SESSION_COOKIE_SECURE = True
# CSRF_COOKIE_SECURE = True

# Redis configuration for caching and Celery
# For now, disable Redis in production until we set up ElastiCache
# REDIS_URL = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
REDIS_URL = None  # Disable Redis until ElastiCache is configured

# Cache configuration - Use local memory cache if Redis is not available
if REDIS_URL:
    CACHES = {
        'default': {
            'BACKEND': 'django_redis.cache.RedisCache',
            'LOCATION': REDIS_URL,
            'OPTIONS': {
                'CLIENT_CLASS': 'django_redis.client.DefaultClient',
            }
        }
    }
else:
    # Fallback to local memory cache for production
    CACHES = {
        'default': {
            'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
            'LOCATION': 'unique-snowflake',
        }
    }

# Celery configuration - Disable if Redis is not available
if REDIS_URL:
    CELERY_BROKER_URL = REDIS_URL
    CELERY_RESULT_BACKEND = REDIS_URL
    CELERY_ACCEPT_CONTENT = ['json']
    CELERY_TASK_SERIALIZER = 'json'
    CELERY_RESULT_SERIALIZER = 'json'
    CELERY_TIMEZONE = TIME_ZONE
else:
    # Disable Celery if Redis is not available
    CELERY_TASK_ALWAYS_EAGER = True  # Execute tasks synchronously
    CELERY_TASK_EAGER_PROPAGATES = True

# Channels configuration - Disable if Redis is not available
if REDIS_URL:
    CHANNEL_LAYERS = {
        'default': {
            'BACKEND': 'channels_redis.core.RedisChannelLayer',
            'CONFIG': {
                'hosts': [REDIS_URL],
            },
        },
    }
else:
    # Use in-memory channel layer if Redis is not available
    CHANNEL_LAYERS = {
        'default': {
            'BACKEND': 'channels.layers.InMemoryChannelLayer',
        },
    }

# GraphQL configuration
GRAPHENE = {
    'SCHEMA': 'core.schema_simple.schema' if GRAPHQL_MODE == 'simple' else 'core.schema.schema',
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

# API Keys
FINNHUB_API_KEY = os.getenv('FINNHUB_API_KEY', '')
ALPHA_VANTAGE_API_KEY = os.getenv('ALPHA_VANTAGE_API_KEY', '')
POLYGON_API_KEY = os.getenv('POLYGON_API_KEY', '')
NEWS_API_KEY = os.getenv('NEWS_API_KEY', '')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY', '')
ALCHEMY_API_KEY = os.getenv('ALCHEMY_API_KEY', '')
WALLETCONNECT_PROJECT_ID = os.getenv('WALLETCONNECT_PROJECT_ID', '')
SEPOLIA_ETH_URL = os.getenv('SEPOLIA_ETH_URL', '')

# API Service Configuration
DISABLE_ALPHA_VANTAGE = os.getenv('DISABLE_ALPHA_VANTAGE', 'false').lower() == 'true'
DISABLE_FINNHUB = os.getenv('DISABLE_FINNHUB', 'false').lower() == 'true'
DISABLE_POLYGON = os.getenv('DISABLE_POLYGON', 'false').lower() == 'true'

# AI Service Configuration
USE_OPENAI = bool(OPENAI_API_KEY)
OPENAI_MODEL = os.getenv('OPENAI_MODEL', 'gpt-4')
OPENAI_ENABLE_FALLBACK = os.getenv('OPENAI_ENABLE_FALLBACK', 'true').lower() == 'true'
OPENAI_MAX_TOKENS = int(os.getenv('OPENAI_MAX_TOKENS', '4000'))
OPENAI_TEMPERATURE = float(os.getenv('OPENAI_TEMPERATURE', '0.7'))

# ML Service Configuration
ML_SERVICE_CONFIG = {
    'ENABLED': True,
    'MODEL_PATH': os.getenv('ML_MODEL_PATH', '/app/models/'),
    'REDIS_URL': REDIS_URL,
    'BATCH_SIZE': int(os.getenv('ML_BATCH_SIZE', '32')),
    'MAX_WORKERS': int(os.getenv('ML_MAX_WORKERS', '4')),
}

# Email configuration
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = os.getenv('EMAIL_HOST', 'smtp.gmail.com')
EMAIL_PORT = int(os.getenv('EMAIL_PORT', '587'))
EMAIL_USE_TLS = True
EMAIL_HOST_USER = os.getenv('EMAIL_HOST_USER', '')
EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD', '')
DEFAULT_FROM_EMAIL = os.getenv('DEFAULT_FROM_EMAIL', 'noreply@richesreach.com')

# Logging configuration - bulletproof with directory creation
import os
from pathlib import Path

LOG_DIR = Path(os.getenv("LOG_DIR", "/app/logs"))
try:
    LOG_DIR.mkdir(parents=True, exist_ok=True)  # Ensure directory exists
except (OSError, PermissionError):
    # Fallback to current directory if /app/logs can't be created
    LOG_DIR = Path(os.getcwd()) / "logs"
    LOG_DIR.mkdir(parents=True, exist_ok=True)

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {"console": {"class": "logging.StreamHandler"}},
    "root": {"handlers": ["console"], "level": "INFO"},
    "loggers": {
        "django.request": {"handlers": ["console"], "level": "WARNING"},
        "richesreach": {"handlers": ["console"], "level": "INFO", "propagate": False},
        "core": {"handlers": ["console"], "level": "INFO", "propagate": False},
    },
}

# AWS Configuration
AWS_ACCESS_KEY_ID = os.getenv('AWS_ACCESS_KEY_ID', '')
AWS_SECRET_ACCESS_KEY = os.getenv('AWS_SECRET_ACCESS_KEY', '')
AWS_STORAGE_BUCKET_NAME = os.getenv('AWS_STORAGE_BUCKET_NAME', '')
AWS_S3_REGION_NAME = os.getenv('AWS_S3_REGION_NAME', 'us-east-1')
AWS_S3_CUSTOM_DOMAIN = f'{AWS_STORAGE_BUCKET_NAME}.s3.amazonaws.com'

# Monitoring
SENTRY_DSN = os.getenv('SENTRY_DSN', '')

# Rate limiting
RATELIMIT_ENABLE = True
RATELIMIT_USE_CACHE = 'default'

# Custom user model
AUTH_USER_MODEL = 'core.User'

# Build SHA logging for deployment verification
import logging
logger = logging.getLogger(__name__)
logger.info(
    "Booting backend: sha=%s settings=%s",
    os.getenv("GIT_SHA", "unknown"),
    os.getenv("DJANGO_SETTINGS_MODULE", "unknown"),
)