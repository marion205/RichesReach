#!/usr/bin/env python3
"""
Quick test script to verify Alpha Vantage API is working
"""
import requests
import json

def test_alpha_vantage_api():
    """Test the Alpha Vantage API directly"""
    api_key = 'K0A7XYLDNXHNQ1WI'
    symbol = 'AAPL'
    
    print(f"🔍 Testing Alpha Vantage API for {symbol}...")
    print(f"🔑 Using API key: {api_key[:8]}...")
    
    try:
        # Test GLOBAL_QUOTE endpoint
        params = {
            'function': 'GLOBAL_QUOTE',
            'symbol': symbol,
            'apikey': api_key
        }
        
        response = requests.get(
            'https://www.alphavantage.co/query',
            params=params,
            timeout=10
        )
        
        print(f"📡 Response status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"📊 Response data: {json.dumps(data, indent=2)}")
            
            if 'Global Quote' in data:
                quote = data['Global Quote']
                price = quote.get('05. price', 'N/A')
                change = quote.get('09. change', 'N/A')
                change_percent = quote.get('10. change percent', 'N/A')
                
                print(f"✅ SUCCESS! {symbol} current price: ${price}")
                print(f"   Change: {change} ({change_percent})")
            else:
                print("❌ No 'Global Quote' in response")
                if 'Error Message' in data:
                    print(f"   Error: {data['Error Message']}")
                if 'Note' in data:
                    print(f"   Note: {data['Note']}")
        else:
            print(f"❌ HTTP Error: {response.status_code}")
            print(f"   Response: {response.text}")
            
    except Exception as e:
        print(f"❌ Exception: {e}")

if __name__ == "__main__":
    test_alpha_vantage_api()
