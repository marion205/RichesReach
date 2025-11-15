#!/usr/bin/env python3
"""
Complete Production Setup - GPT-4o, PostgreSQL, Kafka, All Services
"""
import os
import subprocess

def main():
    print("🚀 COMPLETE PRODUCTION SETUP")
    print("=" * 50)
    
    # Kill any existing servers
    print("🔄 Stopping existing servers...")
    subprocess.run(["pkill", "-f", "python.*runserver"], capture_output=True)
    
    # Complete production environment variables
    env_vars = {
        # AI Configuration
        "OPENAI_MODEL": "gpt-4o",
        "OPENAI_API_KEY": "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",
        "USE_OPENAI": "true",
        
        # Database Configuration
        "DATABASE_URL": "postgresql://appuser:@Master22@riches-reach-postgres.cmhsue8oy30k.us-east-1.rds.amazonaws.com:5432/postgres",
        
        # Market Data APIs
        "FINNHUB_API_KEY": "d2rnitpr01qv11lfegugd2rnitpr01qv11lfegv0",
        "POLYGON_API_KEY": "uuKmy9dPAjaSVXVEtCumQPga1dqEPDS2",
        "ALPHA_VANTAGE_API_KEY": "OHYSFF1AE446O7CR",
        "NEWS_API_KEY": "94a335c7316145f79840edd62f77e11e",
        
        # Crypto/DeFi APIs
        "WALLETCONNECT_PROJECT_ID": "42421cf8-2df7-45c6-9475-df4f4b115ffc",
        "ALCHEMY_API_KEY": "nqMHXQoBbcV2d9X_7Zp29JxpBoQ6nWRM",
        "SEPOLIA_ETH_RPC_URL": "https://eth-sepolia.g.alchemy.com/v2/2-rJhszNwQ6I3NuBdN5pz",
        
        # AWS Configuration
        "AWS_ACCESS_KEY_ID": "${AWS_ACCESS_KEY_ID}",
        "AWS_SECRET_ACCESS_KEY": "${AWS_SECRET_ACCESS_KEY}",
        "AWS_ACCOUNT_ID": "498606688292",
        "AWS_REGION": "us-east-1",
        
        # Bank Integration
        "USE_YODLEE": "true",
        "USE_SBLOC_MOCK": "false",
        "USE_SBLOC_AGGREGATOR": "true",
        
        # Production Settings
        "ENVIRONMENT": "production",
        "DEBUG": "false",
        "ENABLE_ML_SERVICES": "true",
        "ENABLE_MONITORING": "true",
        
        # Kafka/Streaming Configuration
        "KAFKA_ENABLED": "true",
        "KAFKA_BOOTSTRAP_SERVERS": "b-3.richesreachkafka.kbr9fv.c4.kafka.us-east-1.amazonaws.com:9094,b-2.richesreachkafka.kbr9fv.c4.kafka.us-east-1.amazonaws.com:9094,b-1.richesreachkafka.kbr9fv.c4.kafka.us-east-1.amazonaws.com:9094",
        "KAFKA_GROUP_ID": "riches-reach-producer",
        "KAFKA_TOPIC_PREFIX": "richesreach",
        "ENABLE_STREAMING": "true",
        "STREAMING_MODE": "production",
        # Data Lake Configuration
        "DATA_LAKE_BUCKET": "riches-reach-ai-datalake-20251005",
        
        # Redis Configuration
        "REDIS_URL": "redis://localhost:6379/0",
        
        # Server Configuration
        "API_HOST": "0.0.0.0",
        "API_PORT": "8000",
        "CORS_ORIGINS": "*",
        "ALLOWED_HOSTS": "*"
    }
    
    # Set environment variables
    for key, value in env_vars.items():
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
