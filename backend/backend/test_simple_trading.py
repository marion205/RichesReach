#!/usr/bin/env python3
"""
Simple Trading Test
Test basic trading functionality with detailed error checking
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

def test_account_details():
    """Get detailed account information"""
    print("🔍 Getting Detailed Account Information...")
    
    # Load environment variables
    load_env_secrets()
    
    # Get API keys
    API_KEY = os.getenv('ALPACA_API_KEY_ID') or os.getenv('ALPACA_KEY_ID') or os.getenv('ALPACA_API_KEY')
    SECRET_KEY = os.getenv('ALPACA_API_SECRET_KEY') or os.getenv('ALPACA_SECRET_KEY') or os.getenv('ALPACA_SECRET_KEY')
    
    if not API_KEY or not SECRET_KEY:
        print("❌ Alpaca API keys not found")
        return None
    
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
            return None
        
        accounts = response.json()
        if not accounts:
            print("❌ No accounts found")
            return None
        
        # Get detailed info for first account
        account_id = accounts[0]['id']
        print(f"📊 Getting details for account: {account_id}")
        
        # Get account details
        detail_response = requests.get(f"{BASE_URL}/accounts/{account_id}", headers=headers, timeout=30)
        if detail_response.status_code == 200:
            account_details = detail_response.json()
            print("📊 Account Details:")
            print(f"  - ID: {account_details.get('id', 'N/A')}")
            print(f"  - Status: {account_details.get('status', 'N/A')}")
            print(f"  - Account Number: {account_details.get('account_number', 'N/A')}")
            print(f"  - Created: {account_details.get('created_at', 'N/A')}")
            print(f"  - Trading Blocked: {account_details.get('trading_blocked', 'N/A')}")
            print(f"  - Transfers Blocked: {account_details.get('transfers_blocked', 'N/A')}")
            print(f"  - Day Trading Count: {account_details.get('day_trading_count', 'N/A')}")
            print(f"  - Pattern Day Trader: {account_details.get('pattern_day_trader', 'N/A')}")
            
            # Check if account can trade
            trading_blocked = account_details.get('trading_blocked', False)
            if trading_blocked:
                print("❌ Account is blocked from trading")
                return None
            else:
                print("✅ Account is not blocked from trading")
                return account_details
        else:
            print(f"❌ Failed to get account details: {detail_response.status_code}")
            return None
            
    except Exception as e:
        print(f"❌ Error getting account details: {e}")
        return None

def test_simple_order():
    """Test a simple order with detailed error handling"""
    print("\n🔍 Testing Simple Order...")
    
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
        # Get first account
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
        
        # Try a very simple order
        order_payload = {
            "symbol": "AAPL",
            "qty": "1",
            "side": "buy",
            "type": "market",
            "time_in_force": "day"
        }
        
        print("📈 Placing order...")
        print(f"Payload: {json.dumps(order_payload, indent=2)}")
        
        order_response = requests.post(f"{BASE_URL}/trading/accounts/{account_id}/orders",
                                     data=json.dumps(order_payload),
                                     headers=headers,
                                     timeout=30)
        
        print(f"📊 Order Response Status: {order_response.status_code}")
        print(f"📊 Order Response: {order_response.text}")
        
        if order_response.status_code in [200, 201]:
            order = order_response.json()
            print("✅ Order placed successfully!")
            return True
        else:
            print(f"❌ Order failed: {order_response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Order error: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Simple Trading Test")
    print("=" * 25)
    
    # Get account details
    account_details = test_account_details()
    
    if account_details:
        # Test simple order
        order_success = test_simple_order()
        
        if order_success:
            print("\n🎉 Trading test successful!")
        else:
            print("\n❌ Trading test failed")
    else:
        print("\n❌ Cannot proceed with trading test")
