#!/usr/bin/env python3
"""
Check Alpaca Account Status
Check if accounts are approved and ready for trading
"""

import os
import requests
import json
import time

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

def check_account_status():
    """Check status of all accounts"""
    print("🔍 Checking Alpaca Account Status...")
    
    # Load environment variables
    load_env_secrets()
    
    # Get API keys
    API_KEY = os.getenv('ALPACA_API_KEY_ID') or os.getenv('ALPACA_KEY_ID') or os.getenv('ALPACA_API_KEY')
    SECRET_KEY = os.getenv('ALPACA_API_SECRET_KEY') or os.getenv('ALPACA_SECRET_KEY') or os.getenv('ALPACA_SECRET_KEY')
    
    if not API_KEY or not SECRET_KEY:
        print("❌ Alpaca API keys not found")
        return False
    
    # Use raw requests
    BASE_URL = "https://broker-api.sandbox.alpaca.markets/v1"
    headers = {
        'APCA-API-KEY-ID': API_KEY,
        'APCA-API-SECRET-KEY': SECRET_KEY,
        'Content-Type': 'application/json'
    }
    
    try:
        # Get accounts
        response = requests.get(f"{BASE_URL}/accounts", headers=headers, timeout=30)
        if response.status_code != 200:
            print(f"❌ Failed to get accounts: {response.status_code}")
            return False
        
        accounts = response.json()
        print(f"📊 Found {len(accounts)} accounts")
        
        approved_count = 0
        for i, account in enumerate(accounts, 1):
            status = account.get('status', 'UNKNOWN')
            account_id = account.get('id', 'N/A')
            email = account.get('contact', {}).get('email_address', 'N/A')
            
            print(f"  {i}. ID: {account_id}")
            print(f"     Email: {email}")
            print(f"     Status: {status}")
            
            if status == 'APPROVED':
                approved_count += 1
                print(f"     ✅ Ready for trading!")
            elif status == 'SUBMITTED':
                print(f"     ⏳ Pending approval...")
            else:
                print(f"     ❌ Status: {status}")
            print()
        
        print(f"📊 Summary: {approved_count}/{len(accounts)} accounts approved")
        
        if approved_count > 0:
            print("🎉 You have approved accounts ready for trading!")
            return True
        else:
            print("⏳ No approved accounts yet. In sandbox, accounts are usually auto-approved within minutes.")
            print("   Please wait a few minutes and run this script again.")
            return False
            
    except Exception as e:
        print(f"❌ Error checking accounts: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Check Alpaca Account Status")
    print("=" * 35)
    
    success = check_account_status()
    
    if success:
        print("\n🎉 Ready to test trading!")
    else:
        print("\n⏳ Please wait for account approval and try again.")
