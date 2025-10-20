#!/usr/bin/env python3
"""
Test Trading Without Funding
Test if we can place orders without funding (some sandbox accounts have default funds)
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

def test_trading_without_funding():
    """Test trading without funding - some sandbox accounts have default funds"""
    print("🔍 Testing Trading Without Funding...")
    
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
        # Get accounts
        response = requests.get(f"{BASE_URL}/accounts", headers=headers, timeout=30)
        if response.status_code != 200:
            print(f"❌ Failed to get accounts: {response.status_code}")
            return False
        
        accounts = response.json()
        print(f"📊 Found {len(accounts)} accounts")
        
        # Try each account
        for i, account in enumerate(accounts, 1):
            account_id = account.get('id', 'N/A')
            status = account.get('status', 'UNKNOWN')
            
            print(f"\n📊 Testing account {i}: {account_id}")
            print(f"   Status: {status}")
            
            if status in ['APPROVED', 'ACTIVE']:
                # Get account details first
                detail_response = requests.get(f"{BASE_URL}/accounts/{account_id}", headers=headers, timeout=30)
                if detail_response.status_code == 200:
                    account_details = detail_response.json()
                    buying_power = account_details.get('buying_power', 0)
                    cash = account_details.get('cash', 0)
                    print(f"   Buying Power: ${buying_power}")
                    print(f"   Cash: ${cash}")
                    
                    if float(buying_power) > 0:
                        print(f"   ✅ Account has buying power: ${buying_power}")
                        
                        # Try a small order
                        order_payload = {
                            "symbol": "AAPL",
                            "qty": "1",
                            "side": "buy",
                            "type": "market",
                            "time_in_force": "day"
                        }
                        
                        print(f"   📈 Placing order...")
                        order_response = requests.post(f"{BASE_URL}/trading/accounts/{account_id}/orders",
                                                     data=json.dumps(order_payload),
                                                     headers=headers,
                                                     timeout=30)
                        
                        print(f"   📊 Order Status: {order_response.status_code}")
                        print(f"   📊 Order Response: {order_response.text}")
                        
                        if order_response.status_code in [200, 201]:
                            order = order_response.json()
                            print(f"   ✅ Order placed successfully!")
                            print(f"   Order ID: {order.get('id', 'N/A')}")
                            return True
                        else:
                            print(f"   ❌ Order failed: {order_response.text}")
                    else:
                        print(f"   ❌ No buying power available")
                else:
                    print(f"   ❌ Failed to get account details: {detail_response.status_code}")
            else:
                print(f"   ⏳ Account not ready (status: {status})")
        
        return False
        
    except Exception as e:
        print(f"❌ Error testing trading: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Test Trading Without Funding")
    print("=" * 35)
    
    success = test_trading_without_funding()
    
    if success:
        print("\n🎉 Trading test successful!")
    else:
        print("\n❌ Trading test failed - accounts need funding")
        print("💡 In sandbox mode, accounts usually need to be funded first")
        print("   This requires setting up bank relationships or using Alpaca's web interface")
