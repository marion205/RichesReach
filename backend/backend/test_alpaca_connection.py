#!/usr/bin/env python3
"""
Test Alpaca Connection
Verify sandbox API keys work and check existing accounts
"""

import os
from alpaca.broker.client import BrokerClient

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
    """Test Alpaca Broker API connection"""
    print("🔍 Testing Alpaca Broker API Connection...")
    
    # Load environment variables
    load_env_secrets()
    
    # Get API keys
    API_KEY = os.getenv('ALPACA_API_KEY')
    SECRET_KEY = os.getenv('ALPACA_SECRET_KEY')
    
    if not API_KEY or not SECRET_KEY:
        print("❌ Alpaca API keys not found in environment")
        return False
    
    print(f"📊 API Key: {API_KEY[:10]}...")
    print(f"📊 Secret Key: {SECRET_KEY[:10]}...")
    
    try:
        # Create client
        client = BrokerClient(API_KEY, SECRET_KEY, sandbox=True)
        print("✅ Broker client created successfully")
        
        # Get account list
        accounts = client.get_account_list()
        print(f"✅ Connected! Current accounts: {len(accounts)}")
        
        if accounts:
            print("📊 Existing accounts:")
            for acc in accounts:
                print(f"  - ID: {acc.id}")
                print(f"  - Number: {acc.account_number}")
                print(f"  - Status: {acc.status}")
                print(f"  - Created: {acc.created_at}")
                print("  ---")
        else:
            print("📊 No accounts yet—ready to create!")
            
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Alpaca Connection Test")
    print("=" * 40)
    
    success = test_alpaca_connection()
    
    if success:
        print("\n🎉 Connection successful! Ready to create accounts.")
    else:
        print("\n❌ Connection failed. Check your API keys.")