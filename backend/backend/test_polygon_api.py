#!/usr/bin/env python3
"""
Test script for Polygon API key validation
Run this to test your Polygon API key before using it in the app
"""

import os
import sys
import django
import httpx
import json

# Setup Django
sys.path.append('/Users/marioncollins/RichesReach/backend/backend')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'richesreach.settings')
django.setup()

from django.conf import settings

def test_polygon_api_key(api_key):
    """Test if a Polygon API key is valid"""
    if not api_key or api_key.strip() == '':
        print("❌ API key is empty")
        return False
    
    print(f"🔑 Testing API key: {api_key[:8]}...")
    
    try:
        with httpx.Client(timeout=10) as client:
            # Test free tier endpoint - daily open/close (use yesterday for weekend)
            from datetime import datetime, timedelta
            yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
            response = client.get(
                f"https://api.polygon.io/v1/open-close/AAPL/{yesterday}",
                params={"apikey": api_key}
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get("status") == "OK":
                    print("✅ API key is valid!")
                    print(f"📊 Sample data: {json.dumps(data, indent=2)[:200]}...")
                    return True
                else:
                    print(f"❌ API error: {data.get('error', 'Unknown error')}")
                    return False
            elif response.status_code == 401:
                print("❌ API key is invalid or unauthorized")
                return False
            else:
                print(f"❌ HTTP error: {response.status_code}")
                return False
                
    except Exception as e:
        print(f"❌ Connection error: {e}")
        return False

def test_options_endpoint(api_key):
    """Test if the API key has options access"""
    print(f"🎯 Testing options endpoint...")
    
    try:
        with httpx.Client(timeout=10) as client:
            response = client.get(
                "https://api.polygon.io/v3/reference/options/contracts",
                params={
                    "underlying_ticker": "AAPL",
                    "limit": 5,
                    "apikey": api_key
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get("status") == "OK":
                    print("✅ Options endpoint accessible!")
                    contracts = data.get("results", [])
                    print(f"📈 Found {len(contracts)} option contracts")
                    return True
                else:
                    print(f"❌ Options API error: {data.get('error', 'Unknown error')}")
                    return False
            elif response.status_code == 401:
                print("❌ Options endpoint requires authentication")
                return False
            else:
                print(f"❌ Options HTTP error: {response.status_code}")
                return False
                
    except Exception as e:
        print(f"❌ Options connection error: {e}")
        return False

def main():
    print("🚀 Polygon API Key Tester")
    print("=" * 50)
    
    # Get API key from environment or settings
    api_key = os.getenv('POLYGON_API_KEY') or getattr(settings, 'POLYGON_API_KEY', '')
    
    if not api_key:
        print("❌ No API key found in environment or settings")
        print("\n📝 To set an API key:")
        print("1. Get a free key from https://polygon.io/pricing")
        print("2. Set environment variable: export POLYGON_API_KEY='your_key_here'")
        print("3. Or update settings.py with your key")
        return
    
    # Test the API key
    if test_polygon_api_key(api_key):
        print("\n🎯 Testing options access...")
        test_options_endpoint(api_key)
    
    print("\n" + "=" * 50)
    print("💡 Tips:")
    print("- Free tier: 5 calls/minute, basic data")
    print("- Paid tiers: Higher limits, real-time data, options")
    print("- Check your plan at https://polygon.io/dashboard")

if __name__ == "__main__":
    main()
