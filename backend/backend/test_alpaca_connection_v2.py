#!/usr/bin/env python3
"""
Test Alpaca Connection - Version 0.43.0 Compatible
Verify sandbox API keys work and check existing accounts
"""

import os
import requests
import json

# Load environment variables from env.secrets
def load_env_secrets():
    env_file = 'env.secrets'
    if os.path.exists(env_file):
        with open(env_file, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ[key] = value
        print("✅ Loaded environment variables from env.secrets")
    else:
        print("❌ env.secrets file not found")

def test_alpaca_connection():
    """Test Alpaca Broker API connection using raw requests"""
    print("🔍 Testing Alpaca Broker API Connection...")
    
    # Load environment variables
    load_env_secrets()
    
    # Get API keys (support both naming conventions)
    API_KEY = os.getenv('ALPACA_API_KEY_ID') or os.getenv('ALPACA_KEY_ID') or os.getenv('ALPACA_API_KEY')
    SECRET_KEY = os.getenv('ALPACA_API_SECRET_KEY') or os.getenv('ALPACA_SECRET_KEY') or os.getenv('ALPACA_SECRET_KEY')
    
    if not API_KEY or not SECRET_KEY:
        print("❌ Alpaca API keys not found in environment")
        return False
    
    print(f"📊 API Key: {API_KEY[:10]}...")
    print(f"📊 Secret Key: {SECRET_KEY[:10]}...")
    
    # Use raw requests to match our Django service
    BASE_URL = "https://broker-api.sandbox.alpaca.markets/v1"
    headers = {
        'APCA-API-KEY-ID': API_KEY,
        'APCA-API-SECRET-KEY': SECRET_KEY,
        'Content-Type': 'application/json'
    }
    
    try:
        # Test accounts endpoint
        response = requests.get(f"{BASE_URL}/accounts", headers=headers, timeout=30)
        print(f"📊 API Status: {response.status_code}")
        
        if response.status_code == 200:
            accounts = response.json()
            print(f"✅ Connected! Current accounts: {len(accounts)}")
            
            if accounts:
                print("📊 Existing accounts:")
                for acc in accounts[:5]:  # Show first 5
                    print(f"  - ID: {acc.get('id', 'N/A')}")
                    print(f"  - Number: {acc.get('account_number', 'N/A')}")
                    print(f"  - Status: {acc.get('status', 'N/A')}")
                    print(f"  - Created: {acc.get('created_at', 'N/A')}")
                    print("  ---")
            else:
                print("📊 No accounts yet—ready to create!")
                
            return True
        else:
            print(f"❌ API Error: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Alpaca Connection Test (v0.43.0 Compatible)")
    print("=" * 50)
    
    success = test_alpaca_connection()
    
    if success:
        print("\n🎉 Connection successful! Ready to create accounts.")
    else:
        print("\n❌ Connection failed. Check your API keys.")
