#!/usr/bin/env python3
"""
Test Trading with Real Alpaca Accounts
Tests stock and crypto trading with the created accounts
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

def test_stock_trading():
    """Test stock trading with real account"""
    print("🔍 Testing Stock Trading with Real Account...")
    
    # Load environment variables
    load_env_secrets()
    
    # Get API keys
    API_KEY = os.getenv('ALPACA_API_KEY_ID') or os.getenv('ALPACA_KEY_ID') or os.getenv('ALPACA_API_KEY')
    SECRET_KEY = os.getenv('ALPACA_API_SECRET_KEY') or os.getenv('ALPACA_SECRET_KEY') or os.getenv('ALPACA_SECRET_KEY')
    
    if not API_KEY or not SECRET_KEY:
        print("❌ Alpaca API keys not found")
        return False
    
    # Get first account
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
        if not accounts:
            print("❌ No accounts found")
            return False
        
        account_id = accounts[0]['id']
        print(f"📊 Using account: {account_id}")
        
        # Test stock order
        order_payload = {
            "symbol": "AAPL",
            "qty": "1",
            "side": "buy",
            "type": "market",
            "time_in_force": "day"
        }
        
        print("📈 Placing stock order...")
        order_response = requests.post(f"{BASE_URL}/trading/accounts/{account_id}/orders",
                                     data=json.dumps(order_payload),
                                     headers=headers,
                                     timeout=30)
        
        print(f"📊 Order Status: {order_response.status_code}")
        
        if order_response.status_code in [200, 201]:
            order = order_response.json()
            print("✅ Stock order placed successfully!")
            print(f"  - Order ID: {order.get('id', 'N/A')}")
            print(f"  - Symbol: {order.get('symbol', 'N/A')}")
            print(f"  - Side: {order.get('side', 'N/A')}")
            print(f"  - Quantity: {order.get('qty', 'N/A')}")
            print(f"  - Status: {order.get('status', 'N/A')}")
            return True
        else:
            print(f"❌ Stock order failed: {order_response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Stock trading error: {e}")
        return False

def test_crypto_trading():
    """Test crypto trading with real account"""
    print("\n🔍 Testing Crypto Trading with Real Account...")
    
    # Load environment variables
    load_env_secrets()
    
    # Get API keys
    API_KEY = os.getenv('ALPACA_API_KEY_ID') or os.getenv('ALPACA_KEY_ID') or os.getenv('ALPACA_API_KEY')
    SECRET_KEY = os.getenv('ALPACA_API_SECRET_KEY') or os.getenv('ALPACA_SECRET_KEY') or os.getenv('ALPACA_SECRET_KEY')
    
    if not API_KEY or not SECRET_KEY:
        print("❌ Alpaca API keys not found")
        return False
    
    # Use crypto API
    BASE_URL = "https://api.sandbox.alpaca.markets/v2"
    headers = {
        'APCA-API-KEY-ID': API_KEY,
        'APCA-API-SECRET-KEY': SECRET_KEY,
        'Content-Type': 'application/json'
    }
    
    try:
        # Test crypto order
        order_payload = {
            "symbol": "BTC/USD",
            "qty": "0.001",
            "side": "buy",
            "type": "market",
            "time_in_force": "day"
        }
        
        print("💰 Placing crypto order...")
        order_response = requests.post(f"{BASE_URL}/crypto/orders",
                                     data=json.dumps(order_payload),
                                     headers=headers,
                                     timeout=30)
        
        print(f"📊 Order Status: {order_response.status_code}")
        
        if order_response.status_code in [200, 201]:
            order = order_response.json()
            print("✅ Crypto order placed successfully!")
            print(f"  - Order ID: {order.get('id', 'N/A')}")
            print(f"  - Symbol: {order.get('symbol', 'N/A')}")
            print(f"  - Side: {order.get('side', 'N/A')}")
            print(f"  - Quantity: {order.get('qty', 'N/A')}")
            print(f"  - Status: {order.get('status', 'N/A')}")
            return True
        else:
            print(f"❌ Crypto order failed: {order_response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Crypto trading error: {e}")
        return False

def test_graphql_trading():
    """Test trading via GraphQL (if server is running)"""
    print("\n🔍 Testing Trading via GraphQL...")
    
    try:
        # Test if server is running
        response = requests.get("http://192.168.1.236:8000/graphql/", timeout=5)
        if response.status_code != 200:
            print("❌ GraphQL server not running")
            return False
        
        print("✅ GraphQL server is running")
        print("📊 You can now test trading through your React Native app!")
        return True
        
    except Exception as e:
        print(f"❌ GraphQL server not accessible: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Test Trading with Real Alpaca Accounts")
    print("=" * 50)
    
    # Test stock trading
    stock_success = test_stock_trading()
    
    # Test crypto trading
    crypto_success = test_crypto_trading()
    
    # Test GraphQL server
    graphql_success = test_graphql_trading()
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 TEST RESULTS SUMMARY")
    print("=" * 50)
    print(f"📈 Stock Trading: {'✅ PASS' if stock_success else '❌ FAIL'}")
    print(f"💰 Crypto Trading: {'✅ PASS' if crypto_success else '❌ FAIL'}")
    print(f"🔗 GraphQL Server: {'✅ PASS' if graphql_success else '❌ FAIL'}")
    
    if all([stock_success, crypto_success, graphql_success]):
        print("\n🎉 ALL TESTS PASSED! Trading is fully working!")
    else:
        print("\n⚠️  Some tests failed. Check the logs above.")
