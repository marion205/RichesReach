#!/usr/bin/env python3
"""
Fund Alpaca Accounts - Direct Method
Fund all accounts using direct account update (PATCH method)
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

def fund_account_direct(account_id, api_key, secret_key, amount="100000.00"):
    """Fund account using direct PATCH method"""
    BASE_URL = "https://broker-api.sandbox.alpaca.markets/v1"
    headers = {
        'APCA-API-KEY-ID': api_key,
        'APCA-API-SECRET-KEY': secret_key,
        'Content-Type': 'application/json'
    }
    
    # Direct account update payload
    payload = {
        "buying_power": amount,
        "cash": amount
    }
    
    try:
        print(f"💰 Funding account {account_id} with ${amount}...")
        response = requests.patch(f"{BASE_URL}/accounts/{account_id}",
                                data=json.dumps(payload),
                                headers=headers,
                                timeout=30)
        
        print(f"📊 Response: {response.status_code}")
        
        if response.status_code == 200:
            account = response.json()
            print(f"✅ Account funded successfully!")
            print(f"   - ID: {account.get('id', 'N/A')}")
            print(f"   - Status: {account.get('status', 'N/A')}")
            print(f"   - Account Number: {account.get('account_number', 'N/A')}")
            return True
        else:
            print(f"❌ Funding failed: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Funding error: {e}")
        return False

def fund_all_accounts_direct():
    """Fund all accounts using direct method"""
    print("🔍 Funding All Alpaca Accounts (Direct Method)...")
    
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
                success = fund_account_direct(account_id, API_KEY, SECRET_KEY)
                if success:
                    funded_count += 1
                    print(f"✅ Account {i} funded successfully!")
                else:
                    print(f"❌ Account {i} funding failed")
            else:
                print(f"⏳ Account {i} not ready for funding (status: {status})")
            
            # Small delay between accounts
            if i < len(accounts):
                time.sleep(0.5)
        
        print(f"\n📊 Summary: {funded_count}/{len(accounts)} accounts funded")
        return funded_count > 0
        
    except Exception as e:
        print(f"❌ Error funding accounts: {e}")
        return False

def check_account_balances():
    """Check account balances after funding"""
    print("\n🔍 Checking Account Balances...")
    
    # Load environment variables
    load_env_secrets()
    
    # Get API keys
    API_KEY = os.getenv('ALPACA_API_KEY_ID') or os.getenv('ALPACA_KEY_ID') or os.getenv('ALPACA_API_KEY')
    SECRET_KEY = os.getenv('ALPACA_API_SECRET_KEY') or os.getenv('ALPACA_SECRET_KEY') or os.getenv('ALPACA_SECRET_KEY')
    
    if not API_KEY or not SECRET_KEY:
        print("❌ Alpaca API keys not found")
        return False
    
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
        print(f"📊 Account Balances:")
        
        total_buying_power = 0
        for i, account in enumerate(accounts, 1):
            account_id = account.get('id', 'N/A')
            
            # Get account details
            detail_response = requests.get(f"{BASE_URL}/accounts/{account_id}", headers=headers, timeout=30)
            if detail_response.status_code == 200:
                account_details = detail_response.json()
                buying_power = account_details.get('buying_power', 0)
                cash = account_details.get('cash', 0)
                status = account_details.get('status', 'UNKNOWN')
                
                print(f"  {i}. {account_id}")
                print(f"     Status: {status}")
                print(f"     Buying Power: ${buying_power}")
                print(f"     Cash: ${cash}")
                
                total_buying_power += float(buying_power) if buying_power else 0
            else:
                print(f"  {i}. {account_id} - Failed to get details")
        
        print(f"\n📊 Total Buying Power: ${total_buying_power:,.2f}")
        return total_buying_power > 0
        
    except Exception as e:
        print(f"❌ Error checking balances: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Fund Alpaca Accounts (Direct Method)")
    print("=" * 45)
    
    # Fund all accounts
    success = fund_all_accounts_direct()
    
    if success:
        print("\n🎉 Funding complete! Checking balances...")
        
        # Check balances
        balance_success = check_account_balances()
        
        if balance_success:
            print("\n✅ Accounts are now ready for trading!")
        else:
            print("\n⚠️  Funding may not have worked as expected")
    else:
        print("\n❌ Funding failed. Check the logs above.")
