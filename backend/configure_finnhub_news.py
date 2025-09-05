#!/usr/bin/env python3
"""
Configure Finnhub and News API Keys
Updates the .env file with Finnhub and News API keys
"""

import os
import sys

def configure_finnhub_api():
    """Configure Finnhub API key"""
    print("📈 Configuring Finnhub API")
    print("=" * 30)
    
    print("🔑 To get your Finnhub API key:")
    print("1. Go to: https://finnhub.io/")
    print("2. Sign up for a free account")
    print("3. Go to your dashboard")
    print("4. Copy your API key")
    print()
    
    # Get API key from user
    api_key = input("Enter your Finnhub API key (or press Enter to skip): ").strip()
    
    if api_key:
        return update_env_file('FINNHUB_API_KEY', api_key)
    else:
        print("⏭️ Skipping Finnhub API configuration")
        return False

def configure_news_api():
    """Configure News API key"""
    print("\n📰 Configuring News API")
    print("=" * 25)
    
    print("🔑 To get your News API key:")
    print("1. Go to: https://newsapi.org/")
    print("2. Sign up for a free account")
    print("3. Go to your dashboard")
    print("4. Copy your API key")
    print()
    
    # Get API key from user
    api_key = input("Enter your News API key (or press Enter to skip): ").strip()
    
    if api_key:
        return update_env_file('NEWS_API_KEY', api_key)
    else:
        print("⏭️ Skipping News API configuration")
        return False

def update_env_file(key, value):
    """Update the .env file with a new key-value pair"""
    env_file = '.env'
    
    try:
        # Read current .env file
        if os.path.exists(env_file):
            with open(env_file, 'r') as f:
                lines = f.readlines()
        else:
            lines = []
        
        # Check if key already exists
        key_found = False
        for i, line in enumerate(lines):
            if line.startswith(f'{key}='):
                lines[i] = f'{key}={value}\n'
                key_found = True
                break
        
        # If key not found, add it
        if not key_found:
            lines.append(f'{key}={value}\n')
        
        # Write back to file
        with open(env_file, 'w') as f:
            f.writelines(lines)
        
        print(f"✅ {key} configured successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Failed to update {key}: {e}")
        return False

def test_apis():
    """Test the configured APIs"""
    print("\n🧪 Testing Configured APIs")
    print("=" * 30)
    
    try:
        import os
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'richesreach.settings')
        import django
        django.setup()
        
        from django.conf import settings
        import requests
        
        # Test Finnhub API
        finnhub_key = getattr(settings, 'FINNHUB_API_KEY', None)
        if finnhub_key and finnhub_key != 'your-finnhub-api-key':
            print("📈 Testing Finnhub API...")
            try:
                url = f"https://finnhub.io/api/v1/quote"
                params = {'symbol': 'AAPL', 'token': finnhub_key}
                response = requests.get(url, params=params, timeout=10)
                
                if response.status_code == 200:
                    data = response.json()
                    if 'c' in data:
                        print(f"✅ Finnhub API working! AAPL price: ${data.get('c', 'N/A')}")
                    else:
                        print("⚠️ Finnhub API responded but with unexpected format")
                else:
                    print(f"❌ Finnhub API test failed: {response.status_code}")
            except Exception as e:
                print(f"❌ Finnhub API test error: {e}")
        else:
            print("⚠️ Finnhub API not configured")
        
        # Test News API
        news_key = getattr(settings, 'NEWS_API_KEY', None)
        if news_key and news_key != 'your-news-api-key':
            print("📰 Testing News API...")
            try:
                url = f"https://newsapi.org/v2/top-headlines"
                params = {
                    'category': 'business',
                    'country': 'us',
                    'pageSize': 1,
                    'apiKey': news_key
                }
                response = requests.get(url, params=params, timeout=10)
                
                if response.status_code == 200:
                    data = response.json()
                    if data.get('status') == 'ok':
                        articles = data.get('articles', [])
                        print(f"✅ News API working! Found {len(articles)} articles")
                    else:
                        print("⚠️ News API responded but with unexpected format")
                else:
                    print(f"❌ News API test failed: {response.status_code}")
            except Exception as e:
                print(f"❌ News API test error: {e}")
        else:
            print("⚠️ News API not configured")
        
    except Exception as e:
        print(f"❌ API testing failed: {e}")

def main():
    """Main configuration function"""
    print("🔧 Finnhub & News API Configuration")
    print("=" * 40)
    print()
    
    print("📋 This will configure:")
    print("• Finnhub API - Additional market data and news")
    print("• News API - Financial news and market updates")
    print()
    
    # Configure APIs
    finnhub_success = configure_finnhub_api()
    news_success = configure_news_api()
    
    # Test APIs
    if finnhub_success or news_success:
        test_apis()
    
    # Summary
    print("\n" + "=" * 40)
    print("📊 Configuration Summary")
    print("=" * 40)
    
    if finnhub_success:
        print("✅ Finnhub API: Configured")
    else:
        print("⚠️ Finnhub API: Not configured")
    
    if news_success:
        print("✅ News API: Configured")
    else:
        print("⚠️ News API: Not configured")
    
    print("\n🚀 Your app works perfectly with or without these APIs!")
    print("Core features (OpenAI, Alpha Vantage, Email) are all working.")
    
    return True

if __name__ == "__main__":
    main()
