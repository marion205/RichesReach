#!/usr/bin/env python3
"""
Production Configuration for RichesReach with AWS PostgreSQL
"""
import os

# Production Environment Variables
PRODUCTION_CONFIG = {
    # Django Core Settings
    'SECRET_KEY': 'django-insecure-production-key-change-this-in-production',
    'DEBUG': False,
    'ENVIRONMENT': 'production',
    'ALLOWED_HOSTS': 'localhost,127.0.0.1,0.0.0.0',
    
    # Database Configuration (AWS RDS PostgreSQL)
    # Replace with your actual AWS RDS endpoint
    'DB_NAME': 'richesreach_prod',
    'DB_USER': 'postgres',
    'DB_PASSWORD': 'your-secure-database-password',
    'DB_HOST': 'your-rds-endpoint.region.rds.amazonaws.com',
    'DB_PORT': '5432',
    
    # Redis Configuration (AWS ElastiCache)
    'REDIS_HOST': 'your-elasticache-endpoint.cache.amazonaws.com',
    'REDIS_PORT': '6379',
    'REDIS_DB': '0',
    
    # API Keys (Update with your actual keys)
    'FINNHUB_API_KEY': 'your-finnhub-api-key',
    'ALPHA_VANTAGE_API_KEY': 'your-alpha-vantage-api-key',
    'POLYGON_API_KEY': 'your-polygon-api-key',
    
    # AWS Configuration
    'AWS_ACCESS_KEY_ID': 'your-aws-access-key',
    'AWS_SECRET_ACCESS_KEY': 'your-aws-secret-key',
    'AWS_STORAGE_BUCKET_NAME': 'your-s3-bucket',
    'AWS_S3_REGION_NAME': 'us-east-1',
    
    # Email Configuration
    'EMAIL_HOST': 'smtp.gmail.com',
    'EMAIL_PORT': '587',
    'EMAIL_USE_TLS': True,
    'EMAIL_HOST_USER': 'your-email@gmail.com',
    'EMAIL_HOST_PASSWORD': 'your-app-password',
    'DEFAULT_FROM_EMAIL': 'noreply@yourdomain.com',
    
    # Frontend URL
    'FRONTEND_URL': 'http://localhost:3000',
    
    # Monitoring
    'SENTRY_DSN': 'your-sentry-dsn',
}

def set_production_env():
    """Set production environment variables"""
    for key, value in PRODUCTION_CONFIG.items():
        os.environ[key] = str(value)

if __name__ == "__main__":
    print("🔧 Production Configuration for RichesReach")
    print("=" * 50)
    print("\n📋 To use this configuration:")
    print("1. Update the database credentials with your actual AWS RDS endpoint")
    print("2. Update the API keys with your actual keys")
    print("3. Run: python3 -c 'from production_config import set_production_env; set_production_env()'")
    print("\n🚀 Then start the production server:")
    print("   DJANGO_SETTINGS_MODULE=richesreach.settings_aws python3 unified_production_server.py")

