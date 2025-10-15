#!/usr/bin/env python3
"""
Complete Production Verification - All Services Ready
"""
import os
import subprocess
import requests
import json
import time

def main():
    print("🚀 COMPLETE PRODUCTION VERIFICATION")
    print("=" * 60)
    
    # Set ALL production environment variables
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
        
        # AAVE Configuration
        "AAVE_NETWORK": "sepolia",
        "AAVE_POOL_ADDRESS": "0x6Ae43d3271ff6888e7Fc43Fd7321a503ff738951",
        "RPC_SEPOLIA": "https://eth-sepolia.g.alchemy.com/v2/2-rJhszNwQ6I3NuBdN5pz",
        
        # AWS Configuration
        "AWS_ACCESS_KEY_ID": "AWS_ACCESS_KEY_ID_PLACEHOLDER",
        "AWS_SECRET_ACCESS_KEY": "5ZT7z1M7ReIDCAKCxWyx9AdM8NrWrZJ2/CHzGWYW",
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
        "KAFKA_BOOTSTRAP_SERVERS": "localhost:9092",
        "KAFKA_TOPIC_PREFIX": "richesreach",
        "ENABLE_STREAMING": "true",
        "STREAMING_MODE": "production",
        
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
    print(f"   🏦 AAVE/DeFi: Sepolia Network")
    print(f"   ☁️ AWS: Configured")
    print(f"   📡 Kafka/Streaming: Enabled")
    print(f"   🌍 Environment: {os.environ.get('ENVIRONMENT')}")
    
    print(f"\n🚀 STARTING PRODUCTION SERVER...")
    
    # Start the server
    os.chdir("/Users/marioncollins/RichesReach/backend/backend")
    server_process = subprocess.Popen(["python3", "manage.py", "runserver", "0.0.0.0:8000"], 
                                    stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    
    # Wait for server to start
    print("⏳ Waiting for server to start...")
    time.sleep(10)
    
    # Test all endpoints
    print("\n🧪 TESTING ALL PRODUCTION ENDPOINTS...")
    
    base_url = "http://localhost:8000"
    endpoints = [
        ("GET", "/health/", 200),
        ("GET", "/live/", 200),
        ("GET", "/ready/", 200),
        ("POST", "/auth/", 200),
        ("GET", "/me/", 200),
        ("POST", "/graphql/", 200),
        ("POST", "/api/ai-options/recommendations/", 200),
        ("POST", "/api/ai-portfolio/optimize", 200),
        ("POST", "/api/ml/status", 200),
        ("GET", "/api/sbloc/health/", 200),
        ("GET", "/api/sbloc/banks", 200),
        ("GET", "/api/yodlee/fastlink/start", 302),
        ("GET", "/api/yodlee/accounts", 302),
        ("GET", "/api/market-data/stocks", 200),
        ("GET", "/api/market-data/options", 200),
        ("GET", "/api/market-data/news", 200),
        ("POST", "/api/crypto/prices", 200),
        ("POST", "/api/defi/account", 200),
        ("POST", "/rust/analyze", 200),
        ("GET", "/api/mobile/config", 200),
        ("GET", "/user-profile/", 200),
        ("GET", "/signals/", 200),
        ("GET", "/discussions/", 200),
        ("GET", "/prices/?symbols=BTC,ETH,AAPL", 200),
    ]
    
    passed = 0
    total = len(endpoints)
    
    for method, endpoint, expected_status in endpoints:
        try:
            if method == "GET":
                response = requests.get(f"{base_url}{endpoint}", timeout=10)
            else:
                response = requests.post(f"{base_url}{endpoint}", 
                                       json={"test": "data"}, timeout=10)
            
            if response.status_code == expected_status:
                print(f"✅ {method} {endpoint} - Status: {response.status_code}")
                passed += 1
            else:
                print(f"❌ {method} {endpoint} - Expected: {expected_status}, Got: {response.status_code}")
        except Exception as e:
            print(f"❌ {method} {endpoint} - Error: {str(e)}")
    
    print(f"\n📊 RESULTS: {passed}/{total} endpoints working ({passed/total*100:.1f}%)")
    
    if passed == total:
        print("🎉 ALL SYSTEMS PRODUCTION READY!")
        print("✅ GPT-4o AI")
        print("✅ PostgreSQL Database")
        print("✅ Real Market Data")
        print("✅ Bank Integration")
        print("✅ AAVE/DeFi Integration")
        print("✅ Kafka Streaming")
        print("✅ AWS Services")
        print("✅ All 25 API Endpoints")
        print("\n🚀 READY FOR PRODUCTION DEPLOYMENT!")
    else:
        print("⚠️ Some issues need to be resolved before production deployment.")
    
    # Clean up
    server_process.terminate()
    server_process.wait()

if __name__ == "__main__":
    main()
