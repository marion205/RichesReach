#!/usr/bin/env python3
"""
Test Alpaca API Connection
"""
import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'richesreach.settings_local')
django.setup()

from alpaca.trading.client import TradingClient
from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import StockBarsRequest
from alpaca.data.timeframe import TimeFrame
from datetime import datetime, timedelta

def test_alpaca_connection():
    """Test Alpaca API connection with provided credentials"""
    
    # Test Alpaca configuration
    api_key = os.getenv('ALPACA_API_KEY', '')
    secret_key = os.getenv('ALPACA_SECRET_KEY', '')
    base_url = os.getenv('ALPACA_BASE_URL', 'https://broker-api.sandbox.alpaca.markets')

    print(f'🔑 API Key: {api_key[:10]}...' if api_key else '❌ No API Key')
    print(f'🔑 Secret Key: {secret_key[:10]}...' if secret_key else '❌ No Secret Key')
    print(f'🌐 Base URL: {base_url}')

    if api_key and secret_key:
        try:
            # Test Broker API (for account management and KYC)
            print("🔍 Testing Broker API connection...")
            import requests
            
            broker_url = f"{base_url}/v1/accounts"
            headers = {
                'APCA-API-KEY-ID': api_key,
                'APCA-API-SECRET-KEY': secret_key,
                'Content-Type': 'application/json'
            }
            
            response = requests.get(broker_url, headers=headers)
            print(f'📊 Broker API Response Status: {response.status_code}')
            
            if response.status_code == 200:
                accounts = response.json()
                print(f'✅ Broker API connected successfully!')
                print(f'📊 Response type: {type(accounts)}')
                print(f'📊 Response: {accounts}')
                
                # Handle different response formats
                if isinstance(accounts, list):
                    print(f'📊 Accounts found: {len(accounts)}')
                    if accounts:
                        account = accounts[0]
                        print(f'📈 Account ID: {account.get("id", "N/A")}')
                        print(f'📊 Account Status: {account.get("status", "N/A")}')
                elif isinstance(accounts, dict):
                    accounts_list = accounts.get("accounts", [])
                    print(f'📊 Accounts found: {len(accounts_list)}')
                    if accounts_list:
                        account = accounts_list[0]
                        print(f'📈 Account ID: {account.get("id", "N/A")}')
                        print(f'📊 Account Status: {account.get("status", "N/A")}')
            else:
                print(f'⚠️ Broker API response: {response.text}')
            
            # Test Trading API (for paper trading)
            print("\n🔍 Testing Trading API connection...")
            try:
                trading_client = TradingClient(api_key, secret_key, paper=True)
                account = trading_client.get_account()
                print(f'✅ Trading Client connected successfully!')
                print(f'📊 Account Status: {account.status}')
                print(f'💰 Buying Power: ${account.buying_power}')
                print(f'💵 Cash: ${account.cash}')
                print(f'📈 Portfolio Value: ${account.portfolio_value}')
            except Exception as trading_error:
                print(f'⚠️ Trading API error: {str(trading_error)}')
                print('💡 This is normal for broker API credentials')
            
            # Test Data API (for market data)
            print("\n🔍 Testing Data API connection...")
            try:
                data_client = StockHistoricalDataClient(api_key, secret_key)
                
                # Test getting some stock data
                request_params = StockBarsRequest(
                    symbol_or_symbols=["AAPL"],
                    timeframe=TimeFrame.Day,
                    start=datetime.now() - timedelta(days=5),
                    end=datetime.now()
                )
                
                bars = data_client.get_stock_bars(request_params)
                print(f'✅ Stock data retrieved successfully!')
                print(f'📊 AAPL bars count: {len(bars.data["AAPL"])}')
            except Exception as data_error:
                print(f'⚠️ Data API error: {str(data_error)}')
                print('💡 This is normal for broker API credentials')
            
            return True
            
        except Exception as e:
            print(f'❌ Alpaca connection failed: {str(e)}')
            return False
    else:
        print('❌ Missing API credentials')
        return False

if __name__ == "__main__":
    test_alpaca_connection()
