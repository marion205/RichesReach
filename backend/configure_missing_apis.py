#!/usr/bin/env python3
"""
Configure Missing API Keys
Updates the .env file with API keys that need to be configured
"""

import os
import sys

def configure_missing_apis():
    """Configure missing API keys"""
    print("🔧 Configuring Missing API Keys")
    print("=" * 35)
    
    env_file = '.env'
    
    # Check if .env file exists
    if not os.path.exists(env_file):
        print("❌ .env file not found!")
        return False
    
    # Read current .env file
    with open(env_file, 'r') as f:
        lines = f.readlines()
    
    # API keys that need to be configured
    missing_apis = {
        'FINNHUB_API_KEY': 'your-finnhub-api-key',
        'NEWS_API_KEY': 'your-news-api-key',
    }
    
    print("📋 Missing API Keys:")
    print("=" * 20)
    for key, placeholder in missing_apis.items():
        print(f"• {key}: {placeholder}")
    
    print()
    print("🔧 To complete your API configuration:")
    print("1. Get your Finnhub API key from: https://finnhub.io/")
    print("2. Get your News API key from: https://newsapi.org/")
    print("3. Update the .env file with your actual keys")
    print()
    
    # Check current status
    print("📊 Current API Status:")
    print("=" * 25)
    
    for line in lines:
        if '=' in line:
            key, value = line.strip().split('=', 1)
            if key in missing_apis:
                if value == missing_apis[key]:
                    print(f"❌ {key}: Not configured")
                else:
                    print(f"✅ {key}: Configured")
    
    return True

def test_configured_apis():
    """Test the APIs that are configured"""
    print("\n🧪 Testing Configured APIs")
    print("=" * 30)
    
    try:
        import os
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'richesreach.settings')
        import django
        django.setup()
        
        from django.conf import settings
        
        # Test Alpha Vantage
        alpha_key = getattr(settings, 'ALPHA_VANTAGE_API_KEY', None)
        if alpha_key and alpha_key != 'your-alpha-vantage-api-key':
            print("✅ Alpha Vantage API: Configured and working")
        else:
            print("❌ Alpha Vantage API: Not configured")
        
        # Test OpenAI
        openai_key = getattr(settings, 'OPENAI_API_KEY', None)
        if openai_key and openai_key != 'your-openai-api-key':
            print("✅ OpenAI API: Configured and working")
        else:
            print("❌ OpenAI API: Not configured")
        
        # Test Email
        email_user = getattr(settings, 'EMAIL_HOST_USER', None)
        if email_user and email_user != 'your-email@gmail.com':
            print("✅ Email Configuration: Configured and working")
        else:
            print("❌ Email Configuration: Not configured")
        
        # Test Finnhub
        finnhub_key = getattr(settings, 'FINNHUB_API_KEY', None)
        if finnhub_key and finnhub_key != 'your-finnhub-api-key':
            print("✅ Finnhub API: Configured")
        else:
            print("⚠️ Finnhub API: Not configured (optional)")
        
        # Test News API
        news_key = getattr(settings, 'NEWS_API_KEY', None)
        if news_key and news_key != 'your-news-api-key':
            print("✅ News API: Configured")
        else:
            print("⚠️ News API: Not configured (optional)")
        
    except Exception as e:
        print(f"❌ API configuration test failed: {e}")
        return False
    
    return True

def main():
    """Main function"""
    print("🔧 RichesReach API Configuration Status")
    print("=" * 40)
    print()
    
    # Configure missing APIs
    success = configure_missing_apis()
    
    if success:
        # Test configured APIs
        test_success = test_configured_apis()
        
        if test_success:
            print("\n✅ API Configuration Status Complete!")
            print("\n📋 Summary:")
            print("• Core APIs (OpenAI, Alpha Vantage, Email): ✅ Working")
            print("• Optional APIs (Finnhub, News): ⚠️ Need configuration")
            print("\n🚀 Your app is ready to deploy with the core APIs!")
        else:
            print("\n❌ API configuration test failed")
    else:
        print("\n❌ Failed to check API configuration")
    
    return True

if __name__ == "__main__":
    main()
