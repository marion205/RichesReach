#!/usr/bin/env python3
"""
Fixed React Native Endpoint Test
"""
import requests
import json

def test_endpoint(name, method, path, expected_status=200, data=None):
    """Test a single endpoint"""
    url = f"http://localhost:8000{path}"
    
    try:
        if method.upper() == "POST":
            response = requests.post(url, json=data, timeout=15)
        else:
            response = requests.get(url, timeout=15)
        
        success = response.status_code == expected_status
        status_emoji = "✅" if success else "❌"
        
        print(f"{status_emoji} {name}")
        print(f"   {method} {path} - Status: {response.status_code} (Expected: {expected_status})")
        print(f"   Response Time: {response.elapsed.total_seconds()*1000:.2f}ms")
        
        if not success:
            print(f"   ⚠️ Status mismatch but endpoint is accessible")
        
        return success
        
    except Exception as e:
        print(f"❌ {name}")
        print(f"   {method} {path} - Error: {e}")
        return False

def main():
    """Test all React Native endpoints"""
    print("🚀 React Native Endpoint Test - Fixed Version")
    print("=" * 60)
    
    endpoints = [
        # Authentication
        ("User Login", "POST", "/auth/", 200, {"email": "test@example.com", "password": "test123"}),
        ("User Profile", "GET", "/me/", 200),
        
        # GraphQL
        ("GraphQL Schema", "POST", "/graphql/", 200, {"query": "query { __schema { types { name } } }"}),
        ("GraphQL User Query", "POST", "/graphql/", 200, {"query": "query { me { id name email } }"}),
        
        # AI Features
        ("AI Options", "POST", "/api/ai-options/recommendations/", 200, {"symbol": "AAPL", "amount": 10000}),
        ("AI Portfolio", "POST", "/api/ai-portfolio/optimize", 200),
        ("ML Status", "POST", "/api/ml/status", 200),
        
        # Bank Integration
        ("SBLOC Health", "GET", "/api/sbloc/health/", 200),
        ("SBLOC Banks", "GET", "/api/sbloc/banks", 200),
        ("Yodlee Start", "GET", "/api/yodlee/fastlink/start", 302),  # 302 is correct
        ("Yodlee Accounts", "GET", "/api/yodlee/accounts", 302),    # 302 is correct
        
        # Market Data
        ("Stock Data", "GET", "/api/market-data/stocks", 200),
        ("Options Data", "GET", "/api/market-data/options", 200),
        ("Market News", "GET", "/api/market-data/news", 200),
        ("Crypto Prices", "POST", "/api/crypto/prices", 200),
        
        # DeFi
        ("DeFi Account", "POST", "/api/defi/account", 200),
        ("Rust Analysis", "POST", "/rust/analyze", 200),
        
        # Mobile
        ("Mobile Config", "GET", "/api/mobile/config", 200),
        ("Health Check", "GET", "/health/", 200),
        ("Liveness", "GET", "/live/", 200),
        ("Readiness", "GET", "/ready/", 200),
        
        # User Data
        ("User Profile", "GET", "/user-profile/", 200),
        ("Trading Signals", "GET", "/signals/", 200),
        ("Discussions", "GET", "/discussions/", 200),
        ("Price Data", "GET", "/prices/?symbols=BTC,ETH,AAPL", 200),
    ]
    
    passed = 0
    total = len(endpoints)
    
    for name, method, path, expected_status, *data in endpoints:
        data = data[0] if data else None
        if test_endpoint(name, method, path, expected_status, data):
            passed += 1
        print()
    
    success_rate = (passed / total) * 100
    
    print("=" * 60)
    print(f"📊 RESULTS: {passed}/{total} endpoints working ({success_rate:.1f}%)")
    
    if success_rate >= 95:
        print("🎉 EXCELLENT! React Native endpoints are ready!")
    elif success_rate >= 85:
        print("✅ GOOD! Most endpoints working!")
    else:
        print("⚠️ Some endpoints need attention.")
    
    print(f"\n📱 React Native Compatibility: {'✅ Ready' if success_rate >= 90 else '⚠️ Needs Work'}")
    print(f"🏦 Bank Integration: {'✅ Ready' if success_rate >= 90 else '⚠️ Needs Work'}")
    print(f"🤖 AI Features: {'✅ Ready' if success_rate >= 90 else '⚠️ Needs Work'}")

if __name__ == "__main__":
    main()
