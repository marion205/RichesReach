#!/usr/bin/env python3
"""
Fund Alpaca Accounts
Fund all accounts with paper money for trading
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

def fund_account(account_id, api_key, secret_key, amount="100000.00"):
    """Fund a single account with paper money"""
    BASE_URL = "https://broker-api.sandbox.alpaca.markets/v1"
    headers = {
        'APCA-API-KEY-ID': api_key,
        'APCA-API-SECRET-KEY': secret_key,
        'Content-Type': 'application/json'
    }
    
    # Try different transfer types
    transfer_types = ["ach", "wire", "check"]
    
    for transfer_type in transfer_types:
        fund_payload = {
            "amount": amount,
            "direction": "DEPOSIT",
            "transfer_type": transfer_type
        }
        
        try:
            print(f"💰 Trying {transfer_type} transfer for {amount}...")
            response = requests.post(f"{BASE_URL}/accounts/{account_id}/transfers",
                                   data=json.dumps(fund_payload),
                                   headers=headers,
                                   timeout=30)
            
            print(f"📊 Response: {response.status_code} - {response.text}")
            
            if response.status_code in [200, 201]:
                print(f"✅ {transfer_type} transfer successful!")
                return True
            else:
                print(f"❌ {transfer_type} transfer failed: {response.text}")
                
        except Exception as e:
            print(f"❌ {transfer_type} transfer error: {e}")
    
    return False

def fund_all_accounts():
    """Fund all accounts with paper money"""
    print("🔍 Funding All Alpaca Accounts...")
    
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
        
        funded_count = 0
        for i, account in enumerate(accounts, 1):
            account_id = account.get('id', 'N/A')
            status = account.get('status', 'UNKNOWN')
            
            print(f"\n📊 Funding account {i}/{len(accounts)}: {account_id}")
            print(f"   Status: {status}")
            
            if status in ['APPROVED', 'ACTIVE']:
                success = fund_account(account_id, API_KEY, SECRET_KEY)
                if success:
                    funded_count += 1
                    print(f"✅ Account {i} funded successfully!")
                else:
                    print(f"❌ Account {i} funding failed")
            else:
                print(f"⏳ Account {i} not ready for funding (status: {status})")
            
            # Small delay between accounts
            if i < len(accounts):
                time.sleep(1)
        
        print(f"\n📊 Summary: {funded_count}/{len(accounts)} accounts funded")
        return funded_count > 0
        
    except Exception as e:
        print(f"❌ Error funding accounts: {e}")
        return False

def check_account_balance(account_id, api_key, secret_key):
    """Check account balance"""
    BASE_URL = "https://broker-api.sandbox.alpaca.markets/v1"
    headers = {
        'APCA-API-KEY-ID': api_key,
        'APCA-API-SECRET-KEY': secret_key,
        'Content-Type': 'application/json'
    }
    
    try:
        response = requests.get(f"{BASE_URL}/accounts/{account_id}", headers=headers, timeout=30)
        if response.status_code == 200:
            account = response.json()
            buying_power = account.get('buying_power', 'N/A')
            cash = account.get('cash', 'N/A')
            print(f"📊 Account {account_id}:")
            print(f"   - Buying Power: ${buying_power}")
            print(f"   - Cash: ${cash}")
            return float(buying_power) if buying_power != 'N/A' else 0
        else:
            print(f"❌ Failed to get account balance: {response.status_code}")
            return 0
    except Exception as e:
        print(f"❌ Error checking balance: {e}")
        return 0

if __name__ == "__main__":
    print("🚀 Fund Alpaca Accounts")
    print("=" * 25)
    
    # Load environment variables
    load_env_secrets()
    
    # Get API keys
    API_KEY = os.getenv('ALPACA_API_KEY_ID') or os.getenv('ALPACA_KEY_ID') or os.getenv('ALPACA_API_KEY')
    SECRET_KEY = os.getenv('ALPACA_API_SECRET_KEY') or os.getenv('ALPACA_SECRET_KEY') or os.getenv('ALPACA_SECRET_KEY')
    
    if not API_KEY or not SECRET_KEY:
        print("❌ Alpaca API keys not found")
        exit(1)
    
    # Fund all accounts
    success = fund_all_accounts()
    
    if success:
        print("\n🎉 Funding complete! Checking balances...")
        
        # Check balances
        BASE_URL = "https://broker-api.sandbox.alpaca.markets/v1"
        headers = {
            'APCA-API-KEY-ID': API_KEY,
            'APCA-API-SECRET-KEY': SECRET_KEY,
            'Content-Type': 'application/json'
        }
        
        response = requests.get(f"{BASE_URL}/accounts", headers=headers, timeout=30)
        if response.status_code == 200:
            accounts = response.json()
            for account in accounts:
                check_account_balance(account['id'], API_KEY, SECRET_KEY)
        
        print("\n✅ Accounts are now ready for trading!")
    else:
        print("\n❌ Funding failed. Check the logs above.")
