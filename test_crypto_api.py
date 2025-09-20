#!/usr/bin/env python3
"""
Test crypto API endpoints
"""

import requests
import json

def test_crypto_api():
    base_url = "http://localhost:8125"
    
    print("🧪 Testing Crypto API...")
    
    # Test 1: Health check
    try:
        response = requests.get(f"{base_url}/")
        print(f"✅ Server health: {response.status_code}")
    except Exception as e:
        print(f"❌ Server not responding: {e}")
        return
    
    # Test 2: Crypto currencies
    try:
        response = requests.get(f"{base_url}/api/crypto/currencies")
        print(f"✅ Currencies endpoint: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   Found {len(data.get('currencies', []))} currencies")
        else:
            print(f"   Error: {response.text}")
    except Exception as e:
        print(f"❌ Currencies test failed: {e}")
    
    # Test 3: Crypto price
    try:
        response = requests.get(f"{base_url}/api/crypto/prices/BTC")
        print(f"✅ Price endpoint: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   BTC price: ${data.get('price_usd', 'N/A')}")
        else:
            print(f"   Error: {response.text}")
    except Exception as e:
        print(f"❌ Price test failed: {e}")
    
    # Test 4: GraphQL endpoint
    try:
        response = requests.get(f"{base_url}/graphql/")
        print(f"✅ GraphQL endpoint: {response.status_code}")
    except Exception as e:
        print(f"❌ GraphQL test failed: {e}")

if __name__ == "__main__":
    test_crypto_api()
