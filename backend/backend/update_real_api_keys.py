#!/usr/bin/env python3
"""
Update Production Configuration with Real API Keys
"""
import os

def update_env_file(file_path, updates):
    """Update environment file with real API keys"""
    if os.path.exists(file_path):
        with open(file_path, 'r') as f:
            lines = f.readlines()
        
        # Update existing lines and add new ones
        updated_lines = []
        updated_keys = set()
        
        for line in lines:
            if '=' in line and not line.strip().startswith('#'):
                key = line.split('=')[0].strip()
                if key in updates:
                    updated_lines.append(f"{key}={updates[key]}\n")
                    updated_keys.add(key)
                else:
                    updated_lines.append(line)
            else:
                updated_lines.append(line)
        
        # Add new keys that weren't in the file
        for key, value in updates.items():
            if key not in updated_keys:
                updated_lines.append(f"{key}={value}\n")
        
        with open(file_path, 'w') as f:
            f.writelines(updated_lines)
        
        print(f"✅ Updated {file_path}")
        return True
    else:
        print(f"❌ File not found: {file_path}")
        return False

def main():
    """Update all environment files with real API keys"""
    print("🔧 Updating Production Configuration with Real API Keys...")
    print("=" * 60)
    
    # Real API keys from user
    real_api_keys = {
        # Market Data APIs
        "ALPHA_VANTAGE_API_KEY": "OHYSFF1AE446O7CR",
        "FINNHUB_API_KEY": "d2rnitpr01qv11lfegugd2rnitpr01qv11lfegv0",
        "POLYGON_API_KEY": "uuKmy9dPAjaSVXVEtCumQPga1dqEPDS2",
        "NEWS_API_KEY": "94a335c7316145f79840edd62f77e11e",
        
        # AI Services
        "OPENAI_API_KEY": "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",
        
        # Blockchain/Web3
        "WALLETCONNECT_PROJECT_ID": "42421cf8-2df7-45c6-9475-df4f4b115ffc",
        "ALCHEMY_API_KEY": "nqMHXQoBbcV2d9X_7Zp29JxpBoQ6nWRM",
        "ALCHEMY_SEPOLIA_URL": "https://eth-sepolia.g.alchemy.com/v2/2-rJhszNwQ6I3NuBdN5pz",
        
        # AWS Credentials
        "AWS_ACCESS_KEY_ID": "${AWS_ACCESS_KEY_ID}",
        "AWS_SECRET_ACCESS_KEY": "${AWS_SECRET_ACCESS_KEY}",
        "AWS_ACCOUNT_ID": "498606688292",
        
        # Production Settings
        "USE_OPENAI": "true",
        "USE_SBLOC_MOCK": "false",
        "USE_YODLEE": "true",
        "USE_SBLOC_AGGREGATOR": "true",
        "ENABLE_ML_SERVICES": "true",
        "ENABLE_MONITORING": "true",
        "DEBUG": "false",
        "ENVIRONMENT": "production",
        "LOG_LEVEL": "info",
        
        # Database
        "DATABASE_URL": "postgresql://appuser:@Master22@riches-reach-postgres.cmhsue8oy30k.us-east-1.rds.amazonaws.com:5432/postgres",
        
        # Production URL
        "PRODUCTION_URL": "http://riches-reach-alb-1199497064.us-east-1.elb.amazonaws.com",
        
        # Test User Credentials
        "TEST_USER_EMAIL": "play.reviewer@richesreach.net",
        "TEST_USER_PASSWORD": "ReviewerPass123!"
    }
    
    # Files to update
    env_files = [
        "/Users/marioncollins/RichesReach/backend/backend/.env.production",
        "/Users/marioncollins/RichesReach/backend/backend/.env",
        "/Users/marioncollins/RichesReach/.env.production",
        "/Users/marioncollins/RichesReach/.env"
    ]
    
    updated_count = 0
    for env_file in env_files:
        if update_env_file(env_file, real_api_keys):
            updated_count += 1
    
    print(f"\n📊 UPDATED {updated_count} ENVIRONMENT FILES")
    print("=" * 60)
    print("✅ REAL API KEYS CONFIGURED:")
    print("   📈 Alpha Vantage: OHYSFF1AE446O7CR")
    print("   📊 Finnhub: d2rnitpr01qv11lfegugd2rnitpr01qv11lfegv0")
    print("   📉 Polygon: uuKmy9dPAjaSVXVEtCumQPga1dqEPDS2")
    print("   📰 News API: 94a335c7316145f79840edd62f77e11e")
    print("   🤖 OpenAI: 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")
    print("   🔗 WalletConnect: 42421cf8-2df7-45c6-9475-df4f4b115ffc")
    print("   ⛓️ Alchemy: nqMHXQoBbcV2d9X_7Zp29JxpBoQ6nWRM")
    print("   ☁️ AWS: AWS_ACCESS_KEY_ID_PLACEHOLDER")
    
    print("\n🚀 PRODUCTION SETTINGS ENABLED:")
    print("   ✅ OpenAI enabled (no more mock/fallback)")
    print("   ✅ SBLOC Mock disabled")
    print("   ✅ Yodlee integration enabled")
    print("   ✅ SBLOC Aggregator enabled")
    print("   ✅ ML Services enabled")
    print("   ✅ Production database configured")
    print("   ✅ Debug mode disabled")
    
    print("\n⚠️ NEXT STEPS:")
    print("   1. Restart the server to use real API keys")
    print("   2. Test endpoints to verify real data")
    print("   3. Monitor logs for successful API calls")
    
    print("\n🎯 EXPECTED RESULTS:")
    print("   ✅ No more 'using mock data' messages")
    print("   ✅ No more 401 Unauthorized errors")
    print("   ✅ Real market data from APIs")
    print("   ✅ Real AI recommendations")
    print("   ✅ Real bank integration")

if __name__ == "__main__":
    main()
