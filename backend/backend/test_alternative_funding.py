#!/usr/bin/env python3
"""
Test Alternative Funding Methods
Try different approaches to fund Alpaca accounts
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

def test_trading_api_funding():
    """Test funding through trading API"""
    print("🔍 Testing Trading API Funding...")
    
    # Load environment variables
    load_env_secrets()
    
    # Get API keys
    API_KEY = os.getenv('ALPACA_API_KEY_ID') or os.getenv('ALPACA_KEY_ID') or os.getenv('ALPACA_API_KEY')
    SECRET_KEY = os.getenv('ALPACA_API_SECRET_KEY') or os.getenv('ALPACA_SECRET_KEY') or os.getenv('ALPACA_SECRET_KEY')
    
    if not API_KEY or not SECRET_KEY:
        print("❌ Alpaca API keys not found")
        return False
    
    headers = {
        'APCA-API-KEY-ID': API_KEY,
        'APCA-API-SECRET-KEY': SECRET_KEY,
        'Content-Type': 'application/json'
    }
    
    # Get first account
    BASE_URL = "https://broker-api.sandbox.alpaca.markets/v1"
    response = requests.get(f"{BASE_URL}/accounts", headers=headers, timeout=30)
    if response.status_code != 200:
        print(f"❌ Failed to get accounts: {response.status_code}")
        return False
    
    accounts = response.json()
    if not accounts:
        print("❌ No accounts found")
        return False
    
    account_id = accounts[0]['id']
    print(f"📊 Using account: {account_id}")
    
    # Try different funding approaches
    funding_methods = [
        {
            "name": "Trading API Account Update",
            "url": f"https://api.sandbox.alpaca.markets/v2/account",
            "method": "PATCH",
            "payload": {
                "buying_power": "100000.00",
                "cash": "100000.00"
            }
        },
        {
            "name": "Trading API Transfer",
            "url": f"https://api.sandbox.alpaca.markets/v2/account/transfers",
            "method": "POST",
            "payload": {
                "amount": "100000.00",
                "direction": "deposit",
                "transfer_type": "ach"
            }
        },
        {
            "name": "Broker API with Bank ID",
            "url": f"{BASE_URL}/accounts/{account_id}/transfers",
            "method": "POST",
            "payload": {
                "amount": "100000.00",
                "direction": "DEPOSIT",
                "transfer_type": "ach",
                "bank_id": "test_bank_123"
            }
        },
        {
            "name": "Broker API with Relationship ID",
            "url": f"{BASE_URL}/accounts/{account_id}/transfers",
            "method": "POST",
            "payload": {
                "amount": "100000.00",
                "direction": "DEPOSIT",
                "transfer_type": "ach",
                "relationship_id": "test_relationship_123"
            }
        }
    ]
    
    success_count = 0
    for method in funding_methods:
        print(f"\n💰 Testing: {method['name']}")
        print(f"   URL: {method['url']}")
        print(f"   Method: {method['method']}")
        print(f"   Payload: {json.dumps(method['payload'], indent=2)}")
        
        try:
            if method['method'] == 'POST':
                response = requests.post(method['url'], 
                                       data=json.dumps(method['payload']),
                                       headers=headers,
                                       timeout=30)
            elif method['method'] == 'PATCH':
                response = requests.patch(method['url'], 
                                        data=json.dumps(method['payload']),
                                        headers=headers,
                                        timeout=30)
            
            print(f"   Status: {response.status_code}")
            print(f"   Response: {response.text}")
            
            if response.status_code in [200, 201]:
                print(f"   ✅ SUCCESS!")
                success_count += 1
            else:
                print(f"   ❌ Failed")
                
        except Exception as e:
            print(f"   ❌ Error: {e}")
    
    print(f"\n📊 Summary: {success_count}/{len(funding_methods)} methods successful")
    return success_count > 0

def test_sandbox_specific_endpoints():
    """Test sandbox-specific endpoints"""
    print("\n🔍 Testing Sandbox-Specific Endpoints...")
    
    # Load environment variables
    load_env_secrets()
    
    # Get API keys
    API_KEY = os.getenv('ALPACA_API_KEY_ID') or os.getenv('ALPACA_KEY_ID') or os.getenv('ALPACA_API_KEY')
    SECRET_KEY = os.getenv('ALPACA_API_SECRET_KEY') or os.getenv('ALPACA_SECRET_KEY') or os.getenv('ALPACA_SECRET_KEY')
    
    if not API_KEY or not SECRET_KEY:
        print("❌ Alpaca API keys not found")
        return False
    
    headers = {
        'APCA-API-KEY-ID': API_KEY,
        'APCA-API-SECRET-KEY': SECRET_KEY,
        'Content-Type': 'application/json'
    }
    
    # Get first account
    BASE_URL = "https://broker-api.sandbox.alpaca.markets/v1"
    response = requests.get(f"{BASE_URL}/accounts", headers=headers, timeout=30)
    if response.status_code != 200:
        print(f"❌ Failed to get accounts: {response.status_code}")
        return False
    
    accounts = response.json()
    if not accounts:
        print("❌ No accounts found")
        return False
    
    account_id = accounts[0]['id']
    print(f"📊 Using account: {account_id}")
    
    # Try sandbox-specific endpoints
    sandbox_methods = [
        {
            "name": "Sandbox Credit",
            "url": f"{BASE_URL}/sandbox/credit",
            "method": "POST",
            "payload": {
                "account_id": account_id,
                "amount": "100000.00"
            }
        },
        {
            "name": "Sandbox Fund",
            "url": f"{BASE_URL}/sandbox/fund",
            "method": "POST",
            "payload": {
                "account_id": account_id,
                "amount": "100000.00"
            }
        },
        {
            "name": "Test Credit",
            "url": f"{BASE_URL}/test/credit",
            "method": "POST",
            "payload": {
                "account_id": account_id,
                "amount": "100000.00"
            }
        },
        {
            "name": "Account Credit",
            "url": f"{BASE_URL}/accounts/{account_id}/credit",
            "method": "POST",
            "payload": {
                "amount": "100000.00"
            }
        }
    ]
    
    success_count = 0
    for method in sandbox_methods:
        print(f"\n💰 Testing: {method['name']}")
        print(f"   URL: {method['url']}")
        print(f"   Method: {method['method']}")
        print(f"   Payload: {json.dumps(method['payload'], indent=2)}")
        
        try:
            if method['method'] == 'POST':
                response = requests.post(method['url'], 
                                       data=json.dumps(method['payload']),
                                       headers=headers,
                                       timeout=30)
            elif method['method'] == 'PATCH':
                response = requests.patch(method['url'], 
                                        data=json.dumps(method['payload']),
                                        headers=headers,
                                        timeout=30)
            
            print(f"   Status: {response.status_code}")
            print(f"   Response: {response.text}")
            
            if response.status_code in [200, 201]:
                print(f"   ✅ SUCCESS!")
                success_count += 1
            else:
                print(f"   ❌ Failed")
                
        except Exception as e:
            print(f"   ❌ Error: {e}")
    
    print(f"\n📊 Summary: {success_count}/{len(sandbox_methods)} methods successful")
    return success_count > 0

if __name__ == "__main__":
    print("🚀 Test Alternative Funding Methods")
    print("=" * 40)
    
    # Test trading API funding
    trading_success = test_trading_api_funding()
    
    # Test sandbox-specific endpoints
    sandbox_success = test_sandbox_specific_endpoints()
    
    if trading_success or sandbox_success:
        print("\n🎉 Found working funding method!")
    else:
        print("\n❌ No working funding method found")
        print("💡 You may need to use Alpaca's web interface to fund accounts")
        print("   or check if there are other sandbox-specific funding methods")
