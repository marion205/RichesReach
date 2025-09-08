#!/usr/bin/env python3
"""
Production Environment Configuration Script
This script helps configure production environment variables
"""

import os
import secrets
import string
from pathlib import Path

def generate_secret_key():
    """Generate a secure Django secret key"""
    return ''.join(secrets.choice(string.ascii_letters + string.digits + '!@#$%^&*(-_=+)') for _ in range(50))

def get_user_input(prompt, default=None, required=True):
    """Get user input with optional default value"""
    while True:
        if default:
            user_input = input(f"{prompt} (default: {default}): ").strip()
            if not user_input:
                user_input = default
        else:
            user_input = input(f"{prompt}: ").strip()
        
        if user_input or not required:
            return user_input
        print("This field is required. Please enter a value.")

def configure_backend_env():
    """Configure backend environment variables"""
    print("\n🔧 Configuring Backend Environment Variables")
    print("=" * 50)
    
    # Generate secure secret key
    secret_key = generate_secret_key()
    
    # Get configuration from user
    domain_name = get_user_input("Domain name (e.g., yourdomain.com)", required=True)
    debug = get_user_input("Debug mode", "False", required=False)
    
    # Database configuration
    print("\n📊 Database Configuration:")
    db_name = get_user_input("Database name", "richesreach", required=False)
    db_user = get_user_input("Database user", "postgres", required=False)
    db_password = get_user_input("Database password", required=True)
    db_host = get_user_input("Database host", "localhost", required=False)
    db_port = get_user_input("Database port", "5432", required=False)
    
    # Redis configuration
    print("\n🔴 Redis Configuration:")
    redis_host = get_user_input("Redis host", "localhost", required=False)
    redis_port = get_user_input("Redis port", "6379", required=False)
    redis_password = get_user_input("Redis password (optional)", required=False)
    
    # Email configuration
    print("\n📧 Email Configuration:")
    email_host = get_user_input("Email host", "smtp.gmail.com", required=False)
    email_port = get_user_input("Email port", "587", required=False)
    email_use_tls = get_user_input("Use TLS", "True", required=False)
    email_host_user = get_user_input("Email username", required=True)
    email_host_password = get_user_input("Email password/app password", required=True)
    default_from_email = get_user_input("Default from email", f"noreply@{domain_name}", required=False)
    
    # API Keys
    print("\n🔑 API Keys:")
    openai_api_key = get_user_input("OpenAI API key", required=True)
    alpha_vantage_api_key = get_user_input("Alpha Vantage API key", required=True)
    news_api_key = get_user_input("News API key", required=True)
    
    # AWS Configuration (optional)
    print("\n☁️ AWS Configuration (optional):")
    aws_access_key_id = get_user_input("AWS Access Key ID", required=False)
    aws_secret_access_key = get_user_input("AWS Secret Access Key", required=False)
    aws_storage_bucket_name = get_user_input("AWS S3 Bucket Name", required=False)
    aws_s3_region_name = get_user_input("AWS S3 Region", "us-east-1", required=False)
    
    # Sentry (optional)
    print("\n🐛 Error Tracking (optional):")
    sentry_dsn = get_user_input("Sentry DSN", required=False)
    
    # Create .env file content
    env_content = f"""# Production Environment Variables for RichesReach Backend
# Generated on {os.popen('date').read().strip()}

# Django Settings
SECRET_KEY={secret_key}
DEBUG={debug}
DOMAIN_NAME={domain_name}

# Database Configuration
DB_NAME={db_name}
DB_USER={db_user}
DB_PASSWORD={db_password}
DB_HOST={db_host}
DB_PORT={db_port}

# Redis Configuration
REDIS_HOST={redis_host}
REDIS_PORT={redis_port}
REDIS_PASSWORD={redis_password}

# Email Configuration
EMAIL_HOST={email_host}
EMAIL_PORT={email_port}
EMAIL_USE_TLS={email_use_tls}
EMAIL_HOST_USER={email_host_user}
EMAIL_HOST_PASSWORD={email_host_password}
DEFAULT_FROM_EMAIL={default_from_email}

# API Keys
OPENAI_API_KEY={openai_api_key}
ALPHA_VANTAGE_API_KEY={alpha_vantage_api_key}
NEWS_API_KEY={news_api_key}

# AWS Configuration
AWS_ACCESS_KEY_ID={aws_access_key_id}
AWS_SECRET_ACCESS_KEY={aws_secret_access_key}
AWS_STORAGE_BUCKET_NAME={aws_storage_bucket_name}
AWS_S3_REGION_NAME={aws_s3_region_name}

# Sentry (Error Tracking)
SENTRY_DSN={sentry_dsn}

# Security
SECURE_SSL_REDIRECT=True
SECURE_HSTS_SECONDS=31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS=True
SECURE_HSTS_PRELOAD=True
"""
    
    # Write to file
    backend_env_path = Path("backend/.env")
    with open(backend_env_path, "w") as f:
        f.write(env_content)
    
    print(f"\n✅ Backend environment configured: {backend_env_path}")
    return domain_name

def configure_mobile_env(domain_name):
    """Configure mobile environment variables"""
    print("\n📱 Configuring Mobile Environment Variables")
    print("=" * 50)
    
    # Get configuration from user
    api_url = get_user_input("API URL", f"https://{domain_name}", required=False)
    graphql_url = get_user_input("GraphQL URL", f"https://{domain_name}/graphql", required=False)
    ws_url = get_user_input("WebSocket URL", f"wss://{domain_name}/ws", required=False)
    
    # API Keys
    print("\n🔑 API Keys:")
    alpha_vantage_api_key = get_user_input("Alpha Vantage API key", required=True)
    news_api_key = get_user_input("News API key", required=True)
    
    # App Configuration
    print("\n📱 App Configuration:")
    app_version = get_user_input("App version", "1.0.0", required=False)
    build_number = get_user_input("Build number", "1", required=False)
    
    # Create .env.production file content
    env_content = f"""# Mobile App Production Environment Configuration
# Generated on {os.popen('date').read().strip()}

EXPO_PUBLIC_API_URL={api_url}
EXPO_PUBLIC_GRAPHQL_URL={graphql_url}
EXPO_PUBLIC_WS_URL={ws_url}
EXPO_PUBLIC_ENVIRONMENT=production
EXPO_PUBLIC_APP_VERSION={app_version}
EXPO_PUBLIC_BUILD_NUMBER={build_number}

# API Keys
EXPO_PUBLIC_ALPHA_VANTAGE_API_KEY={alpha_vantage_api_key}
EXPO_PUBLIC_NEWS_API_KEY={news_api_key}

# Features
EXPO_PUBLIC_ENABLE_BIOMETRIC_AUTH=true
EXPO_PUBLIC_ENABLE_PUSH_NOTIFICATIONS=true
EXPO_PUBLIC_ENABLE_ANALYTICS=true
EXPO_PUBLIC_ENABLE_CRASH_REPORTING=true
"""
    
    # Write to file
    mobile_env_path = Path("mobile/.env.production")
    with open(mobile_env_path, "w") as f:
        f.write(env_content)
    
    print(f"\n✅ Mobile environment configured: {mobile_env_path}")

def main():
    """Main configuration function"""
    print("🚀 RichesReach Production Environment Configuration")
    print("=" * 60)
    print("This script will help you configure production environment variables.")
    print("Make sure you have all your API keys and credentials ready.")
    
    # Check if we're in the right directory
    if not Path("backend").exists() or not Path("mobile").exists():
        print("❌ Error: Please run this script from the project root directory")
        return
    
    # Configure backend environment
    domain_name = configure_backend_env()
    
    # Configure mobile environment
    configure_mobile_env(domain_name)
    
    print("\n🎉 Production environment configuration completed!")
    print("\n📋 Next steps:")
    print("1. Review the generated .env files")
    print("2. Deploy to your production server")
    print("3. Start the services with Docker Compose")
    print("4. Test your deployment")
    
    print(f"\n🔗 Your app will be available at: https://{domain_name}")

if __name__ == "__main__":
    main()
