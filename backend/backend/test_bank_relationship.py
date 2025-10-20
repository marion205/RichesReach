#!/usr/bin/env python3
"""
Test Bank Relationship Creation
Try to create a bank relationship and then fund accounts
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

def test_bank_relationship_creation():
    """Test creating a bank relationship"""
    print("🔍 Testing Bank Relationship Creation...")
    
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
    
    # Try to create a bank relationship
    bank_relationship_payload = {
        "account_id": account_id,
        "bank_name": "Test Bank",
        "bank_type": "checking",
        "account_number": "1234567890",
        "routing_number": "021000021",  # Test routing number
        "account_holder_name": "Test User",
        "account_holder_type": "individual"
    }
    
    print("🏦 Creating bank relationship...")
    print(f"Payload: {json.dumps(bank_relationship_payload, indent=2)}")
    
    try:
        response = requests.post(f"{BASE_URL}/bank_relationships",
                               data=json.dumps(bank_relationship_payload),
                               headers=headers,
                               timeout=30)
        
        print(f"📊 Response Status: {response.status_code}")
        print(f"📊 Response: {response.text}")
        
        if response.status_code in [200, 201]:
            bank_relationship = response.json()
            print("✅ Bank relationship created successfully!")
            print(f"   Relationship ID: {bank_relationship.get('id', 'N/A')}")
            return bank_relationship.get('id')
        else:
            print(f"❌ Bank relationship creation failed: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ Error creating bank relationship: {e}")
        return None

def test_funding_with_relationship(relationship_id, account_id):
    """Test funding with bank relationship"""
    print(f"\n🔍 Testing Funding with Relationship {relationship_id}...")
    
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
    
    # Try funding with relationship
    funding_payload = {
        "amount": "100000.00",
        "direction": "DEPOSIT",
        "transfer_type": "ach",
        "relationship_id": relationship_id
    }
    
    print("💰 Funding with relationship...")
    print(f"Payload: {json.dumps(funding_payload, indent=2)}")
    
    try:
        BASE_URL = "https://broker-api.sandbox.alpaca.markets/v1"
        response = requests.post(f"{BASE_URL}/accounts/{account_id}/transfers",
                               data=json.dumps(funding_payload),
                               headers=headers,
                               timeout=30)
        
        print(f"📊 Response Status: {response.status_code}")
        print(f"📊 Response: {response.text}")
        
        if response.status_code in [200, 201]:
            transfer = response.json()
            print("✅ Funding successful!")
            print(f"   Transfer ID: {transfer.get('id', 'N/A')}")
            return True
        else:
            print(f"❌ Funding failed: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error funding: {e}")
        return False

def test_simple_funding_workaround():
    """Test if there's a simple workaround for funding"""
    print("\n🔍 Testing Simple Funding Workaround...")
    
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
    
    # Try different approaches
    approaches = [
        {
            "name": "Direct Transfer (no type)",
            "url": f"{BASE_URL}/accounts/{account_id}/transfers",
            "payload": {
                "amount": "100000.00",
                "direction": "incoming"
            }
        },
        {
            "name": "Wire Transfer (no bank)",
            "url": f"{BASE_URL}/accounts/{account_id}/transfers",
            "payload": {
                "amount": "100000.00",
                "direction": "incoming",
                "transfer_type": "wire"
            }
        },
        {
            "name": "ACH Transfer (no bank)",
            "url": f"{BASE_URL}/accounts/{account_id}/transfers",
            "payload": {
                "amount": "100000.00",
                "direction": "incoming",
                "transfer_type": "ach"
            }
        }
    ]
    
    success_count = 0
    for approach in approaches:
        print(f"\n💰 Testing: {approach['name']}")
        print(f"   URL: {approach['url']}")
        print(f"   Payload: {json.dumps(approach['payload'], indent=2)}")
        
        try:
            response = requests.post(approach['url'], 
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
    print("🚀 Test Bank Relationship Creation")
    print("=" * 40)
    
    # Test bank relationship creation
    relationship_id = test_bank_relationship_creation()
    
    if relationship_id:
        # Test funding with relationship
        account_id = "a744f136-c5bc-4ddf-9603-e934057fd778"  # Use first account
        funding_success = test_funding_with_relationship(relationship_id, account_id)
        
        if funding_success:
            print("\n🎉 Funding with bank relationship successful!")
        else:
            print("\n❌ Funding with bank relationship failed")
    else:
        print("\n❌ Bank relationship creation failed")
    
    # Test simple workarounds
    workaround_success = test_simple_funding_workaround()
    
    if workaround_success:
        print("\n🎉 Found working funding workaround!")
    else:
        print("\n❌ No working funding method found")
        print("💡 You may need to use Alpaca's web interface to fund accounts")
