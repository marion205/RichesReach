#!/usr/bin/env python3
"""
Test Alpaca's Test Funding API
Explore different funding methods available in sandbox
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

def test_funding_endpoints():
    """Test different funding endpoints available in sandbox"""
    print("🔍 Testing Alpaca's Test Funding API...")
    
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
    
    # Test different funding methods
    funding_methods = [
        {
            "name": "Test Deposit (v1)",
            "url": f"{BASE_URL}/accounts/{account_id}/transfers",
            "payload": {
                "amount": "100000.00",
                "direction": "DEPOSIT",
                "transfer_type": "test_deposit"  # Special test type
            }
        },
        {
            "name": "Test Deposit (v2)",
            "url": f"{BASE_URL}/accounts/{account_id}/transfers",
            "payload": {
                "amount": "100000.00",
                "direction": "DEPOSIT",
                "transfer_type": "test",
                "test_mode": True
            }
        },
        {
            "name": "Sandbox Deposit",
            "url": f"{BASE_URL}/accounts/{account_id}/transfers",
            "payload": {
                "amount": "100000.00",
                "direction": "DEPOSIT",
                "transfer_type": "sandbox_deposit"
            }
        },
        {
            "name": "Paper Money Deposit",
            "url": f"{BASE_URL}/accounts/{account_id}/transfers",
            "payload": {
                "amount": "100000.00",
                "direction": "DEPOSIT",
                "transfer_type": "paper_money"
            }
        },
        {
            "name": "Test Credit",
            "url": f"{BASE_URL}/accounts/{account_id}/test_credit",
            "payload": {
                "amount": "100000.00"
            }
        },
        {
            "name": "Sandbox Credit",
            "url": f"{BASE_URL}/accounts/{account_id}/sandbox_credit",
            "payload": {
                "amount": "100000.00"
            }
        },
        {
            "name": "Test Funding",
            "url": f"{BASE_URL}/accounts/{account_id}/test_funding",
            "payload": {
                "amount": "100000.00"
            }
        }
    ]
    
    success_count = 0
    for method in funding_methods:
        print(f"\n💰 Testing: {method['name']}")
        print(f"   URL: {method['url']}")
        print(f"   Payload: {json.dumps(method['payload'], indent=2)}")
        
        try:
            response = requests.post(method['url'], 
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

def test_alternative_funding():
    """Test alternative funding approaches"""
    print("\n🔍 Testing Alternative Funding Approaches...")
    
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
    
    # Test different approaches
    approaches = [
        {
            "name": "Direct Account Update",
            "url": f"{BASE_URL}/accounts/{account_id}",
            "method": "PATCH",
            "payload": {
                "buying_power": "100000.00",
                "cash": "100000.00"
            }
        },
        {
            "name": "Account Balance Update",
            "url": f"{BASE_URL}/accounts/{account_id}/balance",
            "method": "POST",
            "payload": {
                "amount": "100000.00"
            }
        },
        {
            "name": "Test Transfer (no type)",
            "url": f"{BASE_URL}/accounts/{account_id}/transfers",
            "method": "POST",
            "payload": {
                "amount": "100000.00",
                "direction": "DEPOSIT"
            }
        }
    ]
    
    success_count = 0
    for approach in approaches:
        print(f"\n💰 Testing: {approach['name']}")
        print(f"   URL: {approach['url']}")
        print(f"   Method: {approach['method']}")
        print(f"   Payload: {json.dumps(approach['payload'], indent=2)}")
        
        try:
            if approach['method'] == 'POST':
                response = requests.post(approach['url'], 
                                       data=json.dumps(approach['payload']),
                                       headers=headers,
                                       timeout=30)
            elif approach['method'] == 'PATCH':
                response = requests.patch(approach['url'], 
                                        data=json.dumps(approach['payload']),
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
    
    print(f"\n📊 Summary: {success_count}/{len(approaches)} approaches successful")
    return success_count > 0

if __name__ == "__main__":
    print("🚀 Test Alpaca's Test Funding API")
    print("=" * 40)
    
    # Test funding endpoints
    funding_success = test_funding_endpoints()
    
    # Test alternative approaches
    alt_success = test_alternative_funding()
    
    if funding_success or alt_success:
        print("\n🎉 Found working funding method!")
    else:
        print("\n❌ No working funding method found")
        print("💡 You may need to use Alpaca's web interface to fund accounts")
