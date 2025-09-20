#!/usr/bin/env python3
"""
Production Environment Setup Script for RichesReach
Configures production environment with AWS PostgreSQL database
"""
import os
import sys
import secrets
import string
from pathlib import Path
from getpass import getpass
import subprocess

class ProductionEnvSetup:
    def __init__(self):
        self.project_root = Path(__file__).parent.parent
        self.backend_dir = self.project_root / "backend"
        self.mobile_dir = self.project_root / "mobile"
    
    def generate_secret_key(self):
        """Generate a secure Django secret key"""
        alphabet = string.ascii_letters + string.digits + "!@#$%^&*(-_=+)"
        return ''.join(secrets.choice(alphabet) for _ in range(50))
    
    def get_user_input(self, prompt, default=None, secret=False):
        """Get user input with optional default and secret mode"""
        if default:
            prompt += f" [{default}]: "
        else:
            prompt += ": "
        if secret:
            return getpass(prompt)
        else:
            return input(prompt) or default
    
    def setup_backend_env(self):
        """Setup backend production environment"""
        print("\n🔧 Setting up Backend Production Environment")
        print("=" * 50)
        
        # Generate secure secret key
        secret_key = self.generate_secret_key()
        
        # Get AWS RDS PostgreSQL details
        print("\n📊 AWS RDS PostgreSQL Configuration:")
        db_host = self.get_user_input("RDS Endpoint", "your-rds-endpoint.region.rds.amazonaws.com")
        db_name = self.get_user_input("Database Name", "richesreach_prod")
        db_user = self.get_user_input("Database User", "postgres")
        db_password = self.get_user_input("Database Password", secret=True)
        
        # Get Redis details
        print("\n🔴 Redis Configuration:")
        redis_host = self.get_user_input("Redis Host", "your-elasticache-endpoint.cache.amazonaws.com")
        redis_port = self.get_user_input("Redis Port", "6379")
        
        # Get API keys
        print("\n🔑 API Keys Configuration:")
        finnhub_key = self.get_user_input("Finnhub API Key", secret=True)
        alpha_vantage_key = self.get_user_input("Alpha Vantage API Key", secret=True)
        polygon_key = self.get_user_input("Polygon API Key", secret=True)
        
        # Get AWS credentials
        print("\n☁️ AWS Configuration:")
        aws_access_key = self.get_user_input("AWS Access Key ID", secret=True)
        aws_secret_key = self.get_user_input("AWS Secret Access Key", secret=True)
        s3_bucket = self.get_user_input("S3 Bucket Name", "your-s3-bucket")
        
        # Get domain configuration
        print("\n🌐 Domain Configuration:")
        domain = self.get_user_input("Domain Name", "yourdomain.com")
        allowed_hosts = f"{domain},www.{domain},api.{domain}"
        
        # Create production environment file
        env_content = f"""# Production Environment Variables for RichesReach
# Generated on {os.popen('date').read().strip()}

# Django Core Settings
SECRET_KEY={secret_key}
DEBUG=False
ENVIRONMENT=production
DOMAIN_NAME={domain}
ALLOWED_HOSTS={allowed_hosts}

# Database Configuration (AWS RDS PostgreSQL)
DB_NAME={db_name}
DB_USER={db_user}
DB_PASSWORD={db_password}
DB_HOST={db_host}
DB_PORT=5432

# Redis Configuration (AWS ElastiCache)
REDIS_HOST={redis_host}
REDIS_PORT={redis_port}
REDIS_DB=0

# API Keys
FINNHUB_API_KEY={finnhub_key}
ALPHA_VANTAGE_API_KEY={alpha_vantage_key}
POLYGON_API_KEY={polygon_key}

# AWS Configuration
AWS_ACCESS_KEY_ID={aws_access_key}
AWS_SECRET_ACCESS_KEY={aws_secret_key}
AWS_STORAGE_BUCKET_NAME={s3_bucket}
AWS_S3_REGION_NAME=us-east-1

# Email Configuration
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
DEFAULT_FROM_EMAIL=noreply@{domain}

# Frontend URL
FRONTEND_URL=https://{domain}

# Monitoring
SENTRY_DSN=your-sentry-dsn

# Security
SECURE_SSL_REDIRECT=True
SESSION_COOKIE_SECURE=True
CSRF_COOKIE_SECURE=True
SECURE_HSTS_SECONDS=31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS=True
SECURE_HSTS_PRELOAD=True
"""
        
        # Write environment file
        env_file = self.backend_dir / ".env"
        with open(env_file, 'w') as f:
            f.write(env_content)
        
        print(f"\n✅ Backend environment file created: {env_file}")
        
        # Create production settings file
        settings_content = """# Production settings for RichesReach with AWS PostgreSQL
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

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = False

ALLOWED_HOSTS = os.getenv('ALLOWED_HOSTS', 'localhost').split(',')

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
    \{
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': \{
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        \},
    \},
]

WSGI_APPLICATION = 'richesreach.wsgi.application'
ASGI_APPLICATION = 'richesreach.asgi.application'

# Database - AWS RDS PostgreSQL
DATABASES = \{
    'default': \{
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.getenv('DB_NAME'),
        'USER': os.getenv('DB_USER'),
        'PASSWORD': os.getenv('DB_PASSWORD'),
        'HOST': os.getenv('DB_HOST'),
        'PORT': os.getenv('DB_PORT', '5432'),
        'OPTIONS': \{
            'sslmode': 'require',
        \},
    \}
\}

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    \{
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    \},
    \{
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    \},
    \{
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    \},
    \{
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    \},
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
    f"https://{domain}",
    f"https://www.{domain}",
]

CORS_ALLOW_CREDENTIALS = True

# Security settings
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True

# HTTPS settings
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True

# Redis configuration for caching and Celery
REDIS_URL = f"redis://{redis_host}:{redis_port}/0"

# Cache configuration
CACHES = \{
    'default': \{
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': REDIS_URL,
        'OPTIONS': \{
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
        \}
    \}
\}

# Celery configuration
CELERY_BROKER_URL = REDIS_URL
CELERY_RESULT_BACKEND = REDIS_URL
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = TIME_ZONE

# Channels configuration
CHANNEL_LAYERS = \{
    'default': \{
        'BACKEND': 'channels_redis.core.RedisChannelLayer',
        'CONFIG': \{
            'hosts': [REDIS_URL],
        \},
    \},
\}

# GraphQL configuration
GRAPHENE = \{
    'SCHEMA': 'core.schema.schema',
    'MIDDLEWARE': [
        'graphql_jwt.middleware.JSONWebTokenMiddleware',
    ]},
\}

# JWT configuration
GRAPHQL_JWT = \{
    'JWT_VERIFY_EXPIRATION': True,
    'JWT_LONG_RUNNING_REFRESH_TOKEN': True,
    'JWT_EXPIRATION_DELTA': timedelta(minutes=60),
    'JWT_REFRESH_EXPIRATION_DELTA': timedelta(days=7),
\}

# API Keys
FINNHUB_API_KEY = os.getenv('FINNHUB_API_KEY')
ALPHA_VANTAGE_API_KEY = os.getenv('ALPHA_VANTAGE_API_KEY')
POLYGON_API_KEY = os.getenv('POLYGON_API_KEY')

# Email configuration
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = os.getenv('EMAIL_HOST', 'smtp.gmail.com')
EMAIL_PORT = int(os.getenv('EMAIL_PORT', '587'))
EMAIL_USE_TLS = True
EMAIL_HOST_USER = os.getenv('EMAIL_HOST_USER')
EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD')
DEFAULT_FROM_EMAIL = os.getenv('DEFAULT_FROM_EMAIL')

# Logging configuration
LOGGING = \{
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': \{
        'verbose': \{
            'format': '\{levelname\} \{asctime\} \{module\} \{process:d\} \{thread:d\} \{message\}',
            'style': '\{',
        \},
        'simple': \{
            'format': '\{levelname\} \{message\}',
            'style': '\{',
        \},
    \},
    'handlers': \{
        'file': \{
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': '/app/logs/django.log',
            'formatter': 'verbose',
        \},
        'console': \{
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
        \},
    \},
    'root': \{
        'handlers': ['console', 'file'],
        'level': 'INFO',
    \},
    'loggers': \{
        'django': \{
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': False,
        \},
        'core': \{
            'handlers': ['console', 'file'],
            'level': 'DEBUG',
            'propagate': False,
        \},
    \},
\}

# Custom user model
AUTH_USER_MODEL = 'core.User'
"""
        
        # Write production settings file
        settings_file = self.backend_dir / "richesreach" / "settings_aws.py"
        with open(settings_file, 'w') as f:
            f.write(settings_content)
        
        print(f"✅ Production settings file created: {settings_file}")
        
        return True
    
    def setup_database(self):
        """Setup production database"""
        print("\n🗄️ Setting up Production Database")
        print("=" * 50)
        
        try:
            # Change to backend directory
            os.chdir(self.backend_dir)
            
            # Run migrations
            print("Running database migrations...")
            subprocess.run(["python3", "manage.py", "makemigrations"], check=True)
            subprocess.run(["python3", "manage.py", "migrate", "--settings=richesreach.settings_aws"], check=True)
            
            # Create superuser
            print("Creating superuser...")
            subprocess.run([
                "python3", "manage.py", "shell", "--settings=richesreach.settings_aws",
                "-c", """
from core.models import User
if not User.objects.filter(is_superuser=True).exists():
    User.objects.create_superuser(
        email='admin@richesreach.com',
        name='Admin User',
        password='admin123'
    )
    print('Superuser created: admin@richesreach.com / admin123')
else:
    print('Superuser already exists')
"""
            ], check=True)
            
            print("✅ Database setup completed")
            return True
            
        except subprocess.CalledProcessError as e:
            print(f"❌ Database setup failed: {e}")
            return False
    
    def run(self):
        """Run the complete setup process"""
        print("🚀 RichesReach Production Environment Setup")
        print("=" * 60)
        
        # Setup backend environment
        if not self.setup_backend_env():
            print("❌ Backend environment setup failed")
            return False
        
        # Setup database
        if not self.setup_database():
            print("❌ Database setup failed")
            return False
        
        print("\n🎉 Production environment setup completed successfully!")
        print("\n📋 Next steps:")
        print("1. Update your API keys in backend/.env")
        print("2. Configure your domain and SSL certificates")
        print("3. Deploy using your existing deployment scripts")
        print("\n🚀 To start the production server:")
        print("   cd backend && DJANGO_SETTINGS_MODULE=richesreach.settings_aws python3 unified_production_server.py")
        
        return True

if __name__ == "__main__":
    setup = ProductionEnvSetup()
    setup.run()

