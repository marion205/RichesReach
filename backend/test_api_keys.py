#!/usr/bin/env python3
"""
Test script to verify API keys are working locally
"""
import os
import requests
import json

# Set environment variables for testing
os.environ['FINNHUB_API_KEY'] = 'd2rnitpr01qv11lfegugd2rnitpr01qv11lfegv0'
os.environ['ALPHA_VANTAGE_API_KEY'] = 'OHYSFF1AE446O7CR'
os.environ['POLYGON_API_KEY'] = 'uuKmy9dPAjaSVXVEtCumQPga1dqEPDS2'
os.environ['NEWS_API_KEY'] = '94a335c7316145f79840edd62f77e11e'
os.environ['OPENAI_API_KEY'] = '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'
os.environ['ALCHEMY_API_KEY'] = 'nqMHXQoBbcV2d9X_7Zp29JxpBoQ6nWRM'
os.environ['WALLETCONNECT_PROJECT_ID'] = '42421cf8-2df7-45c6-9475-df4f4b115ffc'
os.environ['SEPOLIA_ETH_URL'] = 'https://eth-sepolia.g.alchemy.com/v2/2-rJhszNwQ6I3NuBdN5pz'

def test_finnhub_api():
    """Test FinnHub API"""
    api_key = os.environ['FINNHUB_API_KEY']
    url = f"https://finnhub.io/api/v1/quote?symbol=AAPL&token={api_key}"
    
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            print("✅ FinnHub API working")
            print(f"   AAPL Price: ${data.get('c', 'N/A')}")
            return True
        else:
            print(f"❌ FinnHub API error: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ FinnHub API error: {e}")
        return False

def test_alpha_vantage_api():
    """Test Alpha Vantage API"""
    api_key = os.environ['ALPHA_VANTAGE_API_KEY']
    url = f"https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol=AAPL&apikey={api_key}"
    
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            if 'Global Quote' in data:
                print("✅ Alpha Vantage API working")
                quote = data['Global Quote']
                print(f"   AAPL Price: ${quote.get('05. price', 'N/A')}")
                return True
            else:
                print(f"❌ Alpha Vantage API error: {data}")
                return False
        else:
            print(f"❌ Alpha Vantage API error: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Alpha Vantage API error: {e}")
        return False

def test_news_api():
    """Test News API"""
    api_key = os.environ['NEWS_API_KEY']
    url = f"https://newsapi.org/v2/everything?q=Apple&apiKey={api_key}&pageSize=1"
    
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            if data.get('status') == 'ok':
                print("✅ News API working")
                print(f"   Articles found: {data.get('totalResults', 0)}")
                return True
            else:
                print(f"❌ News API error: {data}")
                return False
        else:
            print(f"❌ News API error: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ News API error: {e}")
        return False

def main():
    print("🧪 Testing API Keys...")
    print("=" * 50)
    
    results = []
    results.append(test_finnhub_api())
    results.append(test_alpha_vantage_api())
    results.append(test_news_api())
    
    print("\n" + "=" * 50)
    working_apis = sum(results)
    total_apis = len(results)
    
    if working_apis == total_apis:
        print(f"🎉 All {total_apis} APIs are working!")
    else:
        print(f"⚠️  {working_apis}/{total_apis} APIs are working")
    
    print("\n📋 Next Steps:")
    print("1. Add these API keys as GitHub repository secrets")
    print("2. Deploy to production")
    print("3. Test the endpoints on the live application")

if __name__ == "__main__":
    main()
