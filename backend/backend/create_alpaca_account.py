#!/usr/bin/env python3
"""
Create Alpaca Trading Account - Sandbox
Creates a single trading account with proper KYC data
"""

import os
import requests
import json
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

def create_alpaca_account():
    """Create a single Alpaca trading account"""
    print("🔍 Creating Alpaca Trading Account...")
    
    # Load environment variables
    load_env_secrets()
    
    # Get API keys (support both naming conventions)
    API_KEY = os.getenv('ALPACA_API_KEY_ID') or os.getenv('ALPACA_KEY_ID') or os.getenv('ALPACA_API_KEY')
    SECRET_KEY = os.getenv('ALPACA_API_SECRET_KEY') or os.getenv('ALPACA_SECRET_KEY') or os.getenv('ALPACA_SECRET_KEY')
    
    if not API_KEY or not SECRET_KEY:
        print("❌ Alpaca API keys not found in environment")
        return False
    
    # Use raw requests to match our Django service
    BASE_URL = "https://broker-api.sandbox.alpaca.markets/v1"
    headers = {
        'APCA-API-KEY-ID': API_KEY,
        'APCA-API-SECRET-KEY': SECRET_KEY,
        'Content-Type': 'application/json'
    }
    
    # Account creation payload (sandbox-friendly)
    payload = {
        "contact": {
            "email_address": "test@richesreach.com",
            "phone_number": "+15551234567",  # E.164 format
            "street_address": ["123 Test St"],
            "city": "Test City",
            "state": "CA",  # 2-letter state code
            "postal_code": "12345",
            "country": "USA"  # ISO 3166-1 alpha-3 format
        },
        "identity": {
            "given_name": "Test",
            "family_name": "User",
            "date_of_birth": "1990-01-01",
            "tax_id": "555-12-3456",  # Fake SSN for sandbox
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
    
    try:
        print("📊 Creating account with payload...")
        response = requests.post(f"{BASE_URL}/accounts", 
                               data=json.dumps(payload), 
                               headers=headers, 
                               timeout=30)
        
        print(f"📊 Response Status: {response.status_code}")
        
        if response.status_code in [200, 201]:
            account = response.json()
            print("✅ Account Created Successfully!")
            print(f"  - ID: {account.get('id', 'N/A')}")
            print(f"  - Number: {account.get('account_number', 'N/A')}")
            print(f"  - Status: {account.get('status', 'N/A')}")
            print(f"  - Created: {account.get('created_at', 'N/A')}")
            print(f"  - Email: {account.get('contact', {}).get('email_address', 'N/A')}")
            
            # Optional: Fund with paper money
            account_id = account.get('id')
            if account_id:
                print(f"\n💰 Funding account with $100,000 paper money...")
                fund_account(account_id, API_KEY, SECRET_KEY)
            
            return account
        else:
            print(f"❌ Account creation failed: {response.status_code}")
            print(f"Response: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ Error creating account: {e}")
        return None

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
            print("✅ Account funded with $100,000!")
        else:
            print(f"⚠️  Funding failed: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"⚠️  Funding error: {e}")

if __name__ == "__main__":
    print("🚀 Create Alpaca Trading Account")
    print("=" * 40)
    
    account = create_alpaca_account()
    
    if account:
        print(f"\n🎉 Account created successfully!")
        print(f"Account ID: {account.get('id')}")
        print("You can now use this account for trading in your app!")
    else:
        print("\n❌ Account creation failed. Check the logs above.")
