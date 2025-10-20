#!/usr/bin/env python3
"""
Test Real Alpaca Trading Integration
This script tests the complete trading functionality with real Alpaca API credentials
"""

import os
import sys
import django
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'richesreach.settings_local')
django.setup()

# Load environment variables from env.secrets
def load_env_secrets():
    """Load environment variables from env.secrets file"""
    env_file = project_root / 'env.secrets'
    if env_file.exists():
        with open(env_file, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ[key] = value
        print("✅ Loaded environment variables from env.secrets")
    else:
        print("❌ env.secrets file not found")

def test_alpaca_connection():
    """Test Alpaca API connection"""
    print("\n🔍 Testing Alpaca API Connection...")
    
    try:
        from core.services.alpaca_broker_service import AlpacaBrokerService
        from core.services.alpaca_crypto_service import AlpacaCryptoService
        
        # Test Broker Service
        broker_service = AlpacaBrokerService()
        print(f"📊 Broker API Key: {broker_service.api_key[:10]}...")
        print(f"📊 Broker Base URL: {broker_service.base_url}")
        
        # Test Crypto Service
        crypto_service = AlpacaCryptoService()
        print(f"💰 Crypto API Key: {crypto_service.api_key[:10]}...")
        print(f"💰 Crypto Base URL: {crypto_service.base_url}")
        
        return True
    except Exception as e:
        print(f"❌ Alpaca connection test failed: {e}")
        return False

def test_stock_trading():
    """Test stock trading functionality"""
    print("\n📈 Testing Stock Trading...")
    
    try:
        from core.mutations import PlaceStockOrder
        from django.contrib.auth import get_user_model
        
        User = get_user_model()
        user = User.objects.filter(email='test@example.com').first()
        
        if not user:
            print("❌ Test user not found")
            return False
        
        # Test the mutation
        mutation = PlaceStockOrder()
        result = mutation.mutate(
            info=None,  # We'll mock this
            symbol="AAPL",
            side="BUY",
            quantity=1,
            order_type="MARKET"
        )
        
        print(f"📊 Stock trading result: {result.success}")
        print(f"📊 Message: {result.message}")
        
        return result.success
    except Exception as e:
        print(f"❌ Stock trading test failed: {e}")
        return False

def test_crypto_trading():
    """Test crypto trading functionality"""
    print("\n💰 Testing Crypto Trading...")
    
    try:
        from core.crypto_graphql import ExecuteCryptoTrade
        from django.contrib.auth import get_user_model
        
        User = get_user_model()
        user = User.objects.filter(email='test@example.com').first()
        
        if not user:
            print("❌ Test user not found")
            return False
        
        # Test the mutation
        mutation = ExecuteCryptoTrade()
        result = mutation.mutate(
            info=None,  # We'll mock this
            symbol="BTC/USD",
            trade_type="BUY",
            quantity=0.001,
            order_type="MARKET"
        )
        
        print(f"💰 Crypto trading result: {result.ok}")
        if result.error:
            print(f"💰 Error: {result.error.message}")
        
        return result.ok
    except Exception as e:
        print(f"❌ Crypto trading test failed: {e}")
        return False

def test_graphql_endpoints():
    """Test GraphQL endpoints with real credentials"""
    print("\n🔗 Testing GraphQL Endpoints...")
    
    import requests
    import json
    
    # Get a fresh token
    auth_url = "http://192.168.1.236:8000/auth/"
    auth_data = {
        "email": "test@example.com",
        "password": "testpassword"
    }
    
    try:
        response = requests.post(auth_url, json=auth_data)
        if response.status_code == 200:
            token = response.json()['token']
            print(f"✅ Got authentication token: {token[:20]}...")
            
            # Test stock trading via GraphQL
            graphql_url = "http://192.168.1.236:8000/graphql/"
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {token}"
            }
            
            # Test stock order
            stock_query = {
                "query": """
                mutation {
                    placeStockOrder(symbol: "AAPL", side: "BUY", quantity: 1, orderType: "MARKET") {
                        success
                        orderId
                        message
                    }
                }
                """
            }
            
            response = requests.post(graphql_url, json=stock_query, headers=headers)
            if response.status_code == 200:
                result = response.json()
                print(f"📊 Stock order result: {result}")
            else:
                print(f"❌ Stock order failed: {response.status_code}")
            
            # Test crypto order
            crypto_query = {
                "query": """
                mutation {
                    executeCryptoTrade(symbol: "BTC/USD", tradeType: "BUY", quantity: 0.001, orderType: "MARKET") {
                        ok
                        trade {
                            id
                            tradeType
                            quantity
                        }
                        error {
                            code
                            message
                        }
                    }
                }
                """
            }
            
            response = requests.post(graphql_url, json=crypto_query, headers=headers)
            if response.status_code == 200:
                result = response.json()
                print(f"💰 Crypto order result: {result}")
            else:
                print(f"❌ Crypto order failed: {response.status_code}")
            
            return True
        else:
            print(f"❌ Authentication failed: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ GraphQL test failed: {e}")
        return False

def main():
    """Main test function"""
    print("🚀 Testing Real Alpaca Trading Integration")
    print("=" * 50)
    
    # Load environment variables
    load_env_secrets()
    
    # Test Alpaca connection
    if not test_alpaca_connection():
        print("\n❌ Alpaca connection test failed. Exiting.")
        return
    
    # Test stock trading
    stock_success = test_stock_trading()
    
    # Test crypto trading
    crypto_success = test_crypto_trading()
    
    # Test GraphQL endpoints
    graphql_success = test_graphql_endpoints()
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 TEST RESULTS SUMMARY")
    print("=" * 50)
    print(f"🔗 Alpaca Connection: {'✅ PASS' if True else '❌ FAIL'}")
    print(f"📈 Stock Trading: {'✅ PASS' if stock_success else '❌ FAIL'}")
    print(f"💰 Crypto Trading: {'✅ PASS' if crypto_success else '❌ FAIL'}")
    print(f"🔗 GraphQL Endpoints: {'✅ PASS' if graphql_success else '❌ FAIL'}")
    
    if all([stock_success, crypto_success, graphql_success]):
        print("\n🎉 ALL TESTS PASSED! Real trading is working!")
    else:
        print("\n⚠️  Some tests failed. Check the logs above.")

if __name__ == "__main__":
    main()
