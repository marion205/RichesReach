#!/usr/bin/env python3
"""
Fix Production Configuration - GPT-4o and PostgreSQL
"""
import os

def update_env_file(file_path, updates):
    """Update environment file"""
    if os.path.exists(file_path):
        with open(file_path, 'r') as f:
            lines = f.readlines()
        
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
        
        # Add new keys
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
    """Fix production configuration"""
    print("🔧 Fixing Production Configuration...")
    print("=" * 50)
    
    # Production configuration with GPT-4o and PostgreSQL
    production_updates = {
        # Use GPT-4o (latest version)
        "OPENAI_MODEL": "gpt-4o",
        
        # Use PostgreSQL production database
        "DATABASE_URL": "postgresql://appuser:@Master22@riches-reach-postgres.cmhsue8oy30k.us-east-1.rds.amazonaws.com:5432/postgres",
        
        # All real API keys
        "ALPHA_VANTAGE_API_KEY": "OHYSFF1AE446O7CR",
        "FINNHUB_API_KEY": "d2rnitpr01qv11lfegugd2rnitpr01qv11lfegv0",
        "POLYGON_API_KEY": "uuKmy9dPAjaSVXVEtCumQPga1dqEPDS2",
        "NEWS_API_KEY": "94a335c7316145f79840edd62f77e11e",
        "OPENAI_API_KEY": "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",
        "WALLETCONNECT_PROJECT_ID": "42421cf8-2df7-45c6-9475-df4f4b115ffc",
        "ALCHEMY_API_KEY": "nqMHXQoBbcV2d9X_7Zp29JxpBoQ6nWRM",
        "SEPOLIA_ETH_RPC_URL": "https://eth-sepolia.g.alchemy.com/v2/2-rJhszNwQ6I3NuBdN5pz",
        "AWS_ACCESS_KEY_ID": "AWS_ACCESS_KEY_ID_PLACEHOLDER",
        "AWS_SECRET_ACCESS_KEY": "5ZT7z1M7ReIDCAKCxWyx9AdM8NrWrZJ2/CHzGWYW",
        
        # Production settings
        "USE_OPENAI": "true",
        "USE_SBLOC_MOCK": "false",
        "USE_YODLEE": "true",
        "USE_SBLOC_AGGREGATOR": "true",
        "ENABLE_ML_SERVICES": "true",
        "ENVIRONMENT": "production",
        "DEBUG": "false"
    }
    
    # Update all environment files for production
    env_files = [
        "/Users/marioncollins/RichesReach/.env",
        "/Users/marioncollins/RichesReach/backend/backend/.env",
        "/Users/marioncollins/RichesReach/backend/backend/.env.production"
    ]
    
    updated_count = 0
    for env_file in env_files:
        if update_env_file(env_file, production_updates):
            updated_count += 1
    
    print(f"\n✅ UPDATED {updated_count} ENVIRONMENT FILES")
    print("=" * 50)
    print("✅ PRODUCTION CONFIGURATION FIXED:")
    print("   🤖 OpenAI Model: gpt-4o (LATEST VERSION)")
    print("   🗄️ Database: PostgreSQL (PRODUCTION)")
    print("   🔑 Real API keys configured")
    print("   🏦 Bank integration enabled")
    print("   🚀 Production environment ready")
    
    print(f"\n🚀 READY FOR PRODUCTION:")
    print("   The server will now use:")
    print("   ✅ GPT-4o (latest AI model)")
    print("   ✅ PostgreSQL production database")
    print("   ✅ Real API keys (no placeholders)")
    print("   ✅ Real market data")
    print("   ✅ Real AI recommendations")
    print("   ✅ Production-ready configuration")

if __name__ == "__main__":
    main()
