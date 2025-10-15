#!/usr/bin/env python3
"""
Fix Database Configuration for Local Testing
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
    """Fix database configuration for local testing"""
    print("🔧 Fixing Database Configuration for Local Testing...")
    print("=" * 60)
    
    # Local testing configuration
    local_updates = {
        # Use SQLite for local testing
        "DATABASE_URL": "sqlite:///db.sqlite3",
        
        # Ensure OpenAI model is correct
        "OPENAI_MODEL": "gpt-4o-mini",
        
        # Keep all the real API keys
        "ALPHA_VANTAGE_API_KEY": "OHYSFF1AE446O7CR",
        "FINNHUB_API_KEY": "d2rnitpr01qv11lfegugd2rnitpr01qv11lfegv0",
        "POLYGON_API_KEY": "uuKmy9dPAjaSVXVEtCumQPga1dqEPDS2",
        "NEWS_API_KEY": "94a335c7316145f79840edd62f77e11e",
        "OPENAI_API_KEY": "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",
        
        # Production settings
        "USE_OPENAI": "true",
        "USE_SBLOC_MOCK": "false",
        "USE_YODLEE": "true",
        "USE_SBLOC_AGGREGATOR": "true",
        "ENABLE_ML_SERVICES": "true",
        "DEBUG": "true",
        "ENVIRONMENT": "development"
    }
    
    # Update all environment files to use SQLite
    env_files = [
        "/Users/marioncollins/RichesReach/.env",
        "/Users/marioncollins/RichesReach/backend/backend/.env",
        "/Users/marioncollins/RichesReach/backend/backend/.env.production"
    ]
    
    updated_count = 0
    for env_file in env_files:
        if update_env_file(env_file, local_updates):
            updated_count += 1
    
    print(f"\n✅ UPDATED {updated_count} ENVIRONMENT FILES")
    print("=" * 60)
    print("✅ CONFIGURATION FIXED:")
    print("   🗄️ Database: SQLite (for local testing)")
    print("   🤖 OpenAI Model: gpt-4o-mini")
    print("   🔑 Real API keys configured")
    print("   🏦 Bank integration enabled")
    print("   🐛 Debug mode enabled")
    
    print(f"\n🚀 READY TO START SERVER:")
    print("   The server will now use:")
    print("   ✅ SQLite database (no connection errors)")
    print("   ✅ gpt-4o-mini model")
    print("   ✅ Real API keys (no placeholders)")
    print("   ✅ Real market data")
    print("   ✅ Real AI recommendations")

if __name__ == "__main__":
    main()
