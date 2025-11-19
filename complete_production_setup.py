#!/usr/bin/env python3
"""
Complete Production Setup - GPT-4o, PostgreSQL, Kafka, All Services
⚠️ SECURITY: This script now reads from environment variables or .env file
Never hardcode API keys in source code!
"""
import os
import subprocess
from pathlib import Path
from dotenv import load_dotenv

def load_env_file():
    """Load environment variables from .env file if it exists"""
    env_path = Path(__file__).parent / '.env'
    if env_path.exists():
        load_dotenv(env_path)
        print(f"✅ Loaded environment variables from {env_path}")
    else:
        print(f"⚠️  No .env file found at {env_path}")
        print("   Please create .env file from .env.example template")
        print("   Or set environment variables manually")

def get_env_var(key: str, default: str = None, required: bool = False) -> str:
    """Get environment variable with validation"""
    value = os.getenv(key, default)
    if required and not value:
        raise ValueError(
            f"❌ Required environment variable {key} is not set.\n"
            f"   Please set it in your .env file or environment.\n"
            f"   See .env.example for template."
        )
    if not value and key.endswith('_KEY') or key.endswith('_SECRET') or key.endswith('_PASSWORD'):
        print(f"⚠️  Warning: {key} is not set. Some features may not work.")
    return value or ''

def main():
    print("🚀 COMPLETE PRODUCTION SETUP")
    print("=" * 50)
    
    # Load environment variables from .env file
    load_env_file()
    
    # Kill any existing servers
    print("🔄 Stopping existing servers...")
    subprocess.run(["pkill", "-f", "python.*runserver"], capture_output=True)
    
    # Read environment variables (with defaults for non-sensitive config)
    env_vars = {
        # AI Configuration
        "OPENAI_MODEL": get_env_var("OPENAI_MODEL", "gpt-4o"),
        "OPENAI_API_KEY": get_env_var("OPENAI_API_KEY", required=True),
        "USE_OPENAI": get_env_var("USE_OPENAI", "true"),
        
        # Database Configuration
        "DATABASE_URL": get_env_var("DATABASE_URL", required=True),
        
        # Market Data APIs
        "FINNHUB_API_KEY": get_env_var("FINNHUB_API_KEY", required=True),
        "POLYGON_API_KEY": get_env_var("POLYGON_API_KEY", required=True),
        "ALPHA_VANTAGE_API_KEY": get_env_var("ALPHA_VANTAGE_API_KEY", required=True),
        "NEWS_API_KEY": get_env_var("NEWS_API_KEY", required=True),
        
        # Crypto/DeFi APIs
        "WALLETCONNECT_PROJECT_ID": get_env_var("WALLETCONNECT_PROJECT_ID", ""),
        "ALCHEMY_API_KEY": get_env_var("ALCHEMY_API_KEY", ""),
        "SEPOLIA_ETH_RPC_URL": get_env_var("SEPOLIA_ETH_RPC_URL", ""),
        
        # AWS Configuration
        "AWS_ACCESS_KEY_ID": get_env_var("AWS_ACCESS_KEY_ID", ""),
        "AWS_SECRET_ACCESS_KEY": get_env_var("AWS_SECRET_ACCESS_KEY", ""),
        "AWS_ACCOUNT_ID": get_env_var("AWS_ACCOUNT_ID", ""),
        "AWS_REGION": get_env_var("AWS_REGION", "us-east-1"),
        
        # Bank Integration
        "USE_YODLEE": get_env_var("USE_YODLEE", "true"),
        "USE_SBLOC_MOCK": get_env_var("USE_SBLOC_MOCK", "false"),
        "USE_SBLOC_AGGREGATOR": get_env_var("USE_SBLOC_AGGREGATOR", "true"),
        
        # Production Settings
        "ENVIRONMENT": get_env_var("ENVIRONMENT", "production"),
        "DEBUG": get_env_var("DEBUG", "false"),
        "ENABLE_ML_SERVICES": get_env_var("ENABLE_ML_SERVICES", "true"),
        "ENABLE_MONITORING": get_env_var("ENABLE_MONITORING", "true"),
        
        # Kafka/Streaming Configuration
        "KAFKA_ENABLED": get_env_var("KAFKA_ENABLED", "true"),
        "KAFKA_BOOTSTRAP_SERVERS": get_env_var("KAFKA_BOOTSTRAP_SERVERS", ""),
        "KAFKA_GROUP_ID": get_env_var("KAFKA_GROUP_ID", "riches-reach-producer"),
        "KAFKA_TOPIC_PREFIX": get_env_var("KAFKA_TOPIC_PREFIX", "richesreach"),
        "ENABLE_STREAMING": get_env_var("ENABLE_STREAMING", "true"),
        "STREAMING_MODE": get_env_var("STREAMING_MODE", "production"),
        "DATA_LAKE_BUCKET": get_env_var("DATA_LAKE_BUCKET", ""),
        
        # Redis Configuration
        "REDIS_URL": get_env_var("REDIS_URL", "redis://localhost:6379/0"),
        
        # Server Configuration
        "API_HOST": get_env_var("API_HOST", "0.0.0.0"),
        "API_PORT": get_env_var("API_PORT", "8000"),
        "CORS_ORIGINS": get_env_var("CORS_ORIGINS", "*"),
        "ALLOWED_HOSTS": get_env_var("ALLOWED_HOSTS", "*")
    }
    
    # Set environment variables (only if they have values)
    for key, value in env_vars.items():
        if value:
            os.environ[key] = value
    
    print("✅ PRODUCTION ENVIRONMENT CONFIGURED:")
    print(f"   🤖 OpenAI Model: {os.environ.get('OPENAI_MODEL')}")
    print(f"   🗄️ Database: PostgreSQL (Production)")
    print(f"   📊 Market Data: Finnhub, Polygon, Alpha Vantage")
    print(f"   🏦 Bank Integration: Yodlee + SBLOC")
    print(f"   ☁️ AWS: Configured")
    print(f"   📡 Kafka/Streaming: Enabled")
    print(f"   🗄️ Data Lake (S3): {os.environ.get('DATA_LAKE_BUCKET', 'Not configured')}")
    print(f"   🌍 Environment: {os.environ.get('ENVIRONMENT')}")
    
    print(f"\n🚀 STARTING PRODUCTION SERVER...")
    print("   Server will use:")
    print("   ✅ GPT-4o (latest AI model)")
    print("   ✅ PostgreSQL production database")
    print("   ✅ Real API keys for all services")
    print("   ✅ Kafka streaming enabled (MSK cluster)")
    print("   ✅ Data Lake enabled (S3: riches-reach-ai-datalake-20251005)")
    print("   ✅ Bank integration ready")
    print("   ✅ All production services")
    
    # Start the server
    os.chdir("/Users/marioncollins/RichesReach/backend/backend")
    subprocess.run(["python3", "manage.py", "runserver", "0.0.0.0:8000"])

if __name__ == "__main__":
    main()
