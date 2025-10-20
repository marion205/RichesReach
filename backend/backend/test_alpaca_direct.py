#!/usr/bin/env python3
"""
Direct Alpaca API Test
This script tests the Alpaca API directly without Django database dependencies
"""

import os
import requests
import json

def load_env_secrets():
    """Load environment variables from env.secrets file"""
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

def test_alpaca_broker_api():
    """Test Alpaca Broker API directly"""
    print("\n🔍 Testing Alpaca Broker API...")
    
    api_key = os.getenv('ALPACA_API_KEY')
    secret_key = os.getenv('ALPACA_SECRET_KEY')
    base_url = os.getenv('ALPACA_BASE_URL', 'https://broker-api.sandbox.alpaca.markets')
    
    if not api_key or not secret_key:
        print("❌ Alpaca API credentials not found")
        return False
    
    headers = {
        'APCA-API-KEY-ID': api_key,
        'APCA-API-SECRET-KEY': secret_key,
        'Content-Type': 'application/json'
    }
    
    try:
        # Test accounts endpoint
        response = requests.get(f"{base_url}/v1/accounts", headers=headers)
        print(f"📊 Broker API Status: {response.status_code}")
        
        if response.status_code == 200:
            accounts = response.json()
            print(f"📊 Response: {accounts}")
            if isinstance(accounts, list):
                print(f"📊 Found {len(accounts)} accounts")
            else:
                print(f"📊 Found {len(accounts.get('accounts', []))} accounts")
            return True
        else:
            print(f"❌ Broker API Error: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Broker API Test Failed: {e}")
        return False

def test_alpaca_crypto_api():
    """Test Alpaca Crypto API directly"""
    print("\n🔍 Testing Alpaca Crypto API...")
    
    api_key = os.getenv('ALPACA_CRYPTO_API_KEY', os.getenv('ALPACA_API_KEY'))
    secret_key = os.getenv('ALPACA_CRYPTO_SECRET_KEY', os.getenv('ALPACA_SECRET_KEY'))
    base_url = os.getenv('ALPACA_CRYPTO_BASE_URL', 'https://api.sandbox.alpaca.markets')
    
    if not api_key or not secret_key:
        print("❌ Alpaca Crypto API credentials not found")
        return False
    
    headers = {
        'APCA-API-KEY-ID': api_key,
        'APCA-API-SECRET-KEY': secret_key,
        'Content-Type': 'application/json'
    }
    
    try:
        # Test crypto assets endpoint
        response = requests.get(f"{base_url}/v2/crypto/assets", headers=headers)
        print(f"💰 Crypto API Status: {response.status_code}")
        
        if response.status_code == 200:
            assets = response.json()
            print(f"💰 Found {len(assets)} crypto assets")
            return True
        else:
            print(f"❌ Crypto API Error: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Crypto API Test Failed: {e}")
        return False

def test_alpaca_trading():
    """Test Alpaca trading functionality"""
    print("\n🔍 Testing Alpaca Trading...")
    
    api_key = os.getenv('ALPACA_API_KEY')
    secret_key = os.getenv('ALPACA_SECRET_KEY')
    base_url = os.getenv('ALPACA_BASE_URL', 'https://broker-api.sandbox.alpaca.markets')
    
    if not api_key or not secret_key:
        print("❌ Alpaca API credentials not found")
        return False
    
    headers = {
        'APCA-API-KEY-ID': api_key,
        'APCA-API-SECRET-KEY': secret_key,
        'Content-Type': 'application/json'
    }
    
    try:
        # Test creating a paper trading order
        order_data = {
            'symbol': 'AAPL',
            'qty': '1',
            'side': 'buy',
            'type': 'market',
            'time_in_force': 'day'
        }
        
        # First get accounts to find a valid account ID
        accounts_response = requests.get(f"{base_url}/v1/accounts", headers=headers)
        if accounts_response.status_code != 200:
            print(f"❌ Cannot get accounts: {accounts_response.text}")
            return False
        
        accounts = accounts_response.json()
        print(f"📊 Accounts response: {accounts}")
        
        if isinstance(accounts, list):
            if not accounts:
                print("❌ No accounts found")
                return False
            account_id = accounts[0]['id']
        else:
            if not accounts.get('accounts'):
                print("❌ No accounts found")
                return False
            account_id = accounts['accounts'][0]['id']
        print(f"📊 Using account ID: {account_id}")
        
        # Try to create an order
        order_response = requests.post(
            f"{base_url}/v1/trading/accounts/{account_id}/orders",
            headers=headers,
            json=order_data
        )
        
        print(f"📊 Order Status: {order_response.status_code}")
        
        if order_response.status_code in [200, 201]:
            order = order_response.json()
            print(f"✅ Order created successfully: {order.get('id')}")
            return True
        else:
            print(f"❌ Order creation failed: {order_response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Trading Test Failed: {e}")
        return False

def main():
    """Main test function"""
    print("🚀 Testing Alpaca API Direct Integration")
    print("=" * 50)
    
    # Load environment variables
    load_env_secrets()
    
    # Test Broker API
    broker_success = test_alpaca_broker_api()
    
    # Test Crypto API
    crypto_success = test_alpaca_crypto_api()
    
    # Test Trading
    trading_success = test_alpaca_trading()
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 TEST RESULTS SUMMARY")
    print("=" * 50)
    print(f"🔗 Broker API: {'✅ PASS' if broker_success else '❌ FAIL'}")
    print(f"💰 Crypto API: {'✅ PASS' if crypto_success else '❌ FAIL'}")
    print(f"📈 Trading: {'✅ PASS' if trading_success else '❌ FAIL'}")
    
    if all([broker_success, crypto_success, trading_success]):
        print("\n🎉 ALL TESTS PASSED! Real Alpaca integration is working!")
    else:
        print("\n⚠️  Some tests failed. Check the logs above.")

if __name__ == "__main__":
    main()
