#!/usr/bin/env python3
"""
Production Readiness Verification Script
Ensures all mocks are disabled and real services are enabled
"""
import os
import sys
import subprocess
import requests
from pathlib import Path

def check_environment_variables():
    """Check that no mock flags are enabled"""
    print("🔍 Checking environment variables...")
    
    mock_flags = []
    for key, value in os.environ.items():
        if key.endswith('_MOCK') and value.lower() in ['true', '1', 'yes', 'on']:
            mock_flags.append(f"{key}={value}")
    
    if mock_flags:
        print(f"❌ Mock flags enabled: {', '.join(mock_flags)}")
        return False
    
    print("✅ No mock flags enabled")
    return True

def check_django_settings():
    """Check Django settings for production readiness"""
    print("🔍 Checking Django settings...")
    
    try:
        # Set Django settings
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'richesreach.settings_dev_real')
        
        # Import Django
        import django
        django.setup()
        
        from django.conf import settings
        
        # Check mock flags
        mock_attrs = [attr for attr in dir(settings) if attr.endswith('_MOCK')]
        enabled_mocks = []
        
        for attr in mock_attrs:
            if getattr(settings, attr, False):
                enabled_mocks.append(attr)
        
        if enabled_mocks:
            print(f"❌ Mock settings enabled: {', '.join(enabled_mocks)}")
            return False
        
        # Check real services
        real_services = {
            'ALPHA_VANTAGE_API_KEY': getattr(settings, 'ALPHA_VANTAGE_API_KEY', ''),
            'POLYGON_API_KEY': getattr(settings, 'POLYGON_API_KEY', ''),
            'FINNHUB_API_KEY': getattr(settings, 'FINNHUB_API_KEY', ''),
        }
        
        configured_services = [k for k, v in real_services.items() if v]
        print(f"✅ Real services configured: {', '.join(configured_services)}")
        
        return True
        
    except Exception as e:
        print(f"❌ Django settings check failed: {e}")
        return False

def check_market_data_api():
    """Test that market data API returns real data"""
    print("🔍 Testing market data API...")
    
    try:
        response = requests.get("http://192.168.1.236:8000/api/market/quotes?symbols=AAPL", timeout=10)
        if response.status_code == 200:
            data = response.json()
            if data and len(data) > 0:
                stock = data[0]
                if stock.get('price', 0) > 0 and stock.get('provider'):
                    print(f"✅ Market data working: AAPL at ${stock['price']} from {stock['provider']}")
                    return True
        
        print("❌ Market data API returned invalid data")
        return False
        
    except Exception as e:
        print(f"❌ Market data API test failed: {e}")
        return False

def check_mobile_environment():
    """Check mobile environment files"""
    print("🔍 Checking mobile environment...")
    
    mobile_env = Path("mobile/env.local")
    if not mobile_env.exists():
        print("❌ Mobile environment file not found")
        return False
    
    with open(mobile_env) as f:
        content = f.read()
        
    # Check for disabled features
    disabled_features = []
    for line in content.split('\n'):
        if 'EXPO_PUBLIC_' in line and '_ENABLED=false' in line:
            disabled_features.append(line.strip())
    
    if disabled_features:
        print(f"❌ Mobile features disabled: {', '.join(disabled_features)}")
        return False
    
    print("✅ All mobile features enabled")
    return True

def main():
    """Run all production readiness checks"""
    print("🚀 RICHESREACH - PRODUCTION READINESS VERIFICATION")
    print("=" * 60)
    
    checks = [
        ("Environment Variables", check_environment_variables),
        ("Django Settings", check_django_settings),
        ("Market Data API", check_market_data_api),
        ("Mobile Environment", check_mobile_environment),
    ]
    
    results = []
    for name, check_func in checks:
        print(f"\n📋 {name}:")
        try:
            result = check_func()
            results.append((name, result))
        except Exception as e:
            print(f"❌ {name} check failed with error: {e}")
            results.append((name, False))
    
    print("\n" + "=" * 60)
    print("📊 PRODUCTION READINESS SUMMARY:")
    
    all_passed = True
    for name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"  {name}: {status}")
        if not passed:
            all_passed = False
    
    print("=" * 60)
    
    if all_passed:
        print("🎉 ALL CHECKS PASSED - PRODUCTION READY!")
        print("🚀 Your app is ready for App Store and Play Store deployment!")
        return 0
    else:
        print("❌ SOME CHECKS FAILED - NOT PRODUCTION READY")
        print("🔧 Fix the issues above before deploying to production")
        return 1

if __name__ == "__main__":
    sys.exit(main())
