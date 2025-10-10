#!/usr/bin/env python3
"""
Quick Production Fix - GPT-4o and PostgreSQL
"""
import os
import subprocess

def main():
    print("🚀 QUICK PRODUCTION FIX")
    print("=" * 40)
    
    # Kill any existing servers
    print("🔄 Stopping existing servers...")
    subprocess.run(["pkill", "-f", "python.*runserver"], capture_output=True)
    
    # Set environment variables directly
    env_vars = {
        "OPENAI_MODEL": "gpt-4o",
        "DATABASE_URL": "postgresql://appuser:@Master22@riches-reach-postgres.cmhsue8oy30k.us-east-1.rds.amazonaws.com:5432/postgres",
        "OPENAI_API_KEY": "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",
        "FINNHUB_API_KEY": "d2rnitpr01qv11lfegugd2rnitpr01qv11lfegv0",
        "POLYGON_API_KEY": "uuKmy9dPAjaSVXVEtCumQPga1dqEPDS2",
        "ALPHA_VANTAGE_API_KEY": "OHYSFF1AE446O7CR",
        "NEWS_API_KEY": "94a335c7316145f79840edd62f77e11e",
        "USE_OPENAI": "true",
        "USE_SBLOC_MOCK": "false",
        "USE_YODLEE": "true",
        "USE_SBLOC_AGGREGATOR": "true",
        "ENVIRONMENT": "production",
        "DEBUG": "false"
    }
    
    # Set environment variables
    for key, value in env_vars.items():
        os.environ[key] = value
    
    print("✅ Environment variables set:")
    print(f"   🤖 OPENAI_MODEL: {os.environ.get('OPENAI_MODEL')}")
    print(f"   🗄️ DATABASE_URL: {os.environ.get('DATABASE_URL')[:50]}...")
    print(f"   🔑 OPENAI_API_KEY: {os.environ.get('OPENAI_API_KEY')[:20]}...")
    print(f"   🌍 ENVIRONMENT: {os.environ.get('ENVIRONMENT')}")
    
    print(f"\n🚀 Starting production server...")
    print("   Server will use:")
    print("   ✅ GPT-4o (latest AI model)")
    print("   ✅ PostgreSQL production database")
    print("   ✅ Real API keys")
    print("   ✅ Production configuration")
    
    # Start the server
    os.chdir("/Users/marioncollins/RichesReach/backend/backend")
    subprocess.run(["python3", "manage.py", "runserver", "0.0.0.0:8000"])

if __name__ == "__main__":
    main()
