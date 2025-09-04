#!/usr/bin/env python3
"""
Test script for RichesReach API keys
Run this to verify your API keys are working
"""

import requests
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv('backend/.env')

def test_news_api():
    """Test News API"""
    api_key = os.getenv('NEWS_API_KEY')
    if not api_key:
        print("❌ NEWS_API_KEY not found in environment")
        return False
    
    try:
        url = f"https://newsapi.org/v2/everything?q=stocks&apiKey={api_key}&pageSize=1"
        response = requests.get(url)
        
        if response.status_code == 200:
            data = response.json()
            print("✅ News API working!")
            print(f"   Found {data.get('totalResults', 0)} articles")
            return True
        else:
            print(f"❌ News API error: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
    except Exception as e:
        print(f"❌ News API error: {e}")
        return False

def test_alpha_vantage():
    """Test Alpha Vantage API"""
    api_key = os.getenv('ALPHA_VANTAGE_API_KEY')
    if not api_key:
        print("❌ ALPHA_VANTAGE_API_KEY not found in environment")
        return False
    
    try:
        url = f"https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol=AAPL&apikey={api_key}"
        response = requests.get(url)
        
        if response.status_code == 200:
            data = response.json()
            if 'Global Quote' in data:
                print("✅ Alpha Vantage API working!")
                quote = data['Global Quote']
                print(f"   AAPL Price: ${quote.get('05. price', 'N/A')}")
                return True
            else:
                print("❌ Alpha Vantage API error: Invalid response format")
                return False
        else:
            print(f"❌ Alpha Vantage API error: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Alpha Vantage API error: {e}")
        return False

def test_finnhub():
    """Test Finnhub API"""
    api_key = os.getenv('FINNHUB_API_KEY')
    if not api_key:
        print("❌ FINNHUB_API_KEY not found in environment")
        return False
    
    try:
        url = f"https://finnhub.io/api/v1/quote?symbol=AAPL&token={api_key}"
        response = requests.get(url)
        
        if response.status_code == 200:
            data = response.json()
            if 'c' in data:  # 'c' is current price
                print("✅ Finnhub API working!")
                print(f"   AAPL Price: ${data.get('c', 'N/A')}")
                return True
            else:
                print("❌ Finnhub API error: Invalid response format")
                return False
        else:
            print(f"❌ Finnhub API error: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Finnhub API error: {e}")
        return False

def main():
    print("🔑 Testing RichesReach API Keys")
    print("=" * 40)
    
    # Check if .env file exists
    if not os.path.exists('backend/.env'):
        print("❌ No .env file found in backend directory")
        print("   Please create backend/.env with your API keys")
        return
    
    # Test each API
    news_ok = test_news_api()
    alpha_ok = test_alpha_vantage()
    finnhub_ok = test_finnhub()
    
    print("\n" + "=" * 40)
    print("📊 Test Results:")
    print(f"   News API: {'✅' if news_ok else '❌'}")
    print(f"   Alpha Vantage: {'✅' if alpha_ok else '❌'}")
    print(f"   Finnhub: {'✅' if finnhub_ok else '❌'}")
    
    if all([news_ok, alpha_ok, finnhub_ok]):
        print("\n🎉 All APIs working! Your app is ready for deployment!")
    else:
        print("\n⚠️  Some APIs need attention. Check your API keys.")

if __name__ == "__main__":
    main()
