#!/usr/bin/env python3
"""
Batch Create Alpaca Trading Accounts - Sandbox
Creates multiple trading accounts for testing
"""

import os
import requests
import json
import time
from datetime import datetime

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

def create_account_payload(i):
    """Create account payload for account number i"""
    return {
        "contact": {
            "email_address": f"user{i}@richesreach.com",
            "phone_number": f"+1555{i:03d}1234",  # E.164 format
            "street_address": ["123 Test St"],
            "city": "Test City",
            "state": "CA",  # 2-letter state code
            "postal_code": "12345",
            "country": "USA"  # ISO 3166-1 alpha-3 format
        },
        "identity": {
            "given_name": "Test",
            "family_name": f"User{i}",
            "date_of_birth": f"1990-{max(1, (i % 12) + 1):02d}-{max(1, (i % 28) + 1):02d}",
            "tax_id": f"555-{i:02d}-{i:04d}",  # Fake SSN for sandbox
            "tax_id_type": "USA_TAX_ID",
            "country_of_tax_residence": "USA"  # ISO 3166-1 alpha-3 format
        },
        "disclosures": {
            "is_control_person": False,
            "is_affiliated_exchange_or_finra": False,
            "is_politically_exposed": False,
            "immediate_family_exposed": False
        },
        "agreements": [
            {
                "agreement": "account_agreement",
                "signed_at": datetime.utcnow().isoformat() + "Z",
                "ip_address": "0.0.0.0"
            },
            {
                "agreement": "customer_agreement", 
                "signed_at": datetime.utcnow().isoformat() + "Z",
                "ip_address": "0.0.0.0"
            }
        ]
    }

def fund_account(account_id, api_key, secret_key):
    """Fund account with paper money (sandbox only)"""
    BASE_URL = "https://broker-api.sandbox.alpaca.markets/v1"
    headers = {
        'APCA-API-KEY-ID': api_key,
        'APCA-API-SECRET-KEY': secret_key,
        'Content-Type': 'application/json'
    }
    
    fund_payload = {
        "amount": "100000.00",  # $100k paper money
        "direction": "DEPOSIT",
        "transfer_type": "ach"  # Required field
    }
    
    try:
        response = requests.post(f"{BASE_URL}/accounts/{account_id}/transfers",
                               data=json.dumps(fund_payload),
                               headers=headers,
                               timeout=30)
        
        if response.status_code in [200, 201]:
            return True
        else:
            print(f"⚠️  Funding failed for {account_id}: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        print(f"⚠️  Funding error for {account_id}: {e}")
        return False

def batch_create_accounts(num_accounts=5):
    """Create multiple trading accounts"""
    print(f"🔍 Creating {num_accounts} Alpaca Trading Accounts...")
    
    # Load environment variables
    load_env_secrets()
    
    # Get API keys (support both naming conventions)
    API_KEY = os.getenv('ALPACA_API_KEY_ID') or os.getenv('ALPACA_KEY_ID') or os.getenv('ALPACA_API_KEY')
    SECRET_KEY = os.getenv('ALPACA_API_SECRET_KEY') or os.getenv('ALPACA_SECRET_KEY') or os.getenv('ALPACA_SECRET_KEY')
    
    if not API_KEY or not SECRET_KEY:
        print("❌ Alpaca API keys not found in environment")
        return []
    
    # Use raw requests to match our Django service
    BASE_URL = "https://broker-api.sandbox.alpaca.markets/v1"
    headers = {
        'APCA-API-KEY-ID': API_KEY,
        'APCA-API-SECRET-KEY': SECRET_KEY,
        'Content-Type': 'application/json'
    }
    
    created_accounts = []
    
    for i in range(1, num_accounts + 1):
        try:
            print(f"\n📊 Creating account {i}/{num_accounts}...")
            
            payload = create_account_payload(i)
            response = requests.post(f"{BASE_URL}/accounts", 
                                   data=json.dumps(payload), 
                                   headers=headers, 
                                   timeout=30)
            
            if response.status_code in [200, 201]:
                account = response.json()
                print(f"✅ Account {i} created: {account.get('id', 'N/A')}")
                print(f"   - Email: {account.get('contact', {}).get('email_address', 'N/A')}")
                print(f"   - Status: {account.get('status', 'N/A')}")
                
                # Fund the account
                account_id = account.get('id')
                if account_id:
                    print(f"💰 Funding account {i}...")
                    fund_account(account_id, API_KEY, SECRET_KEY)
                
                created_accounts.append(account)
            else:
                print(f"❌ Account {i} failed: {response.status_code}")
                print(f"   Response: {response.text}")
            
            # Polite spacing between requests
            if i < num_accounts:
                time.sleep(0.5)
                
        except Exception as e:
            print(f"❌ Error creating account {i}: {e}")
    
    return created_accounts

if __name__ == "__main__":
    print("🚀 Batch Create Alpaca Trading Accounts")
    print("=" * 45)
    
    # Create 5 accounts by default
    accounts = batch_create_accounts(5)
    
    print(f"\n📊 SUMMARY")
    print("=" * 20)
    print(f"✅ Successfully created: {len(accounts)} accounts")
    
    if accounts:
        print("\n📋 Account Details:")
        for i, account in enumerate(accounts, 1):
            print(f"  {i}. ID: {account.get('id', 'N/A')}")
            print(f"     Email: {account.get('contact', {}).get('email_address', 'N/A')}")
            print(f"     Status: {account.get('status', 'N/A')}")
            print()
    
    print("🎉 Batch creation complete!")
    print("You can now use these accounts for trading in your app!")
