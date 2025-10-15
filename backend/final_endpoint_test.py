#!/usr/bin/env python3
"""
Final Endpoint Test - Verify All API Endpoints Return 200
"""
import requests
import json

def test_endpoint(url, method="GET", expected_status=200, data=None):
    """Test a single endpoint"""
    try:
        if method == "POST":
            response = requests.post(url, json=data, timeout=10)
        else:
            response = requests.get(url, timeout=10)
        
        success = response.status_code == expected_status
        return success, response.status_code, response.text[:100]
    except Exception as e:
        return False, 0, str(e)

def main():
    """Test all endpoints"""
    base_url = "http://localhost:8000"
    
    endpoints = [
        # Health endpoints
        ("/health/", "GET", 200, None),
        ("/live/", "GET", 200, None),
        ("/ready/", "GET", 200, None),
        
        # GraphQL
        ("/graphql/", "POST", 200, {"query": "query { __schema { types { name } } }"}),
        
        # AI endpoints
        ("/api/ai-options/recommendations/", "POST", 200, {"symbol": "AAPL", "amount": 10000}),
        ("/api/ai-portfolio/optimize", "POST", 200, None),
        ("/api/ml/status", "POST", 200, None),
        
        # Bank integration
        ("/api/sbloc/health/", "GET", 200, None),
        ("/api/sbloc/banks", "GET", 200, None),
        ("/api/yodlee/fastlink/start", "GET", 302, None),  # 302 is expected for auth
        
        # Crypto/DeFi
        ("/api/crypto/prices", "POST", 200, None),
        ("/api/defi/account", "POST", 200, None),
        ("/rust/analyze", "POST", 200, None),
        
        # Market data
        ("/api/market-data/stocks", "GET", 200, None),
        ("/api/market-data/options", "GET", 200, None),
        ("/api/market-data/news", "GET", 200, None),
        
        # Mobile
        ("/api/mobile/config", "GET", 200, None),
    ]
    
    print("🧪 Testing All API Endpoints...")
    print("=" * 60)
    
    passed = 0
    total = len(endpoints)
    
    for endpoint, method, expected_status, data in endpoints:
        url = f"{base_url}{endpoint}"
        success, status, response = test_endpoint(url, method, expected_status, data)
        
        status_emoji = "✅" if success else "❌"
        print(f"{status_emoji} {method} {endpoint} - Status: {status} (Expected: {expected_status})")
        
        if success:
            passed += 1
        else:
            print(f"   Response: {response}")
    
    print("=" * 60)
    print(f"📊 RESULTS: {passed}/{total} endpoints working ({passed/total*100:.1f}%)")
    
    if passed == total:
        print("🎉 ALL ENDPOINTS WORKING! Ready for production!")
    elif passed >= total * 0.8:
        print("✅ Most endpoints working! Minor issues remaining.")
    else:
        print("⚠️ Multiple endpoints need attention.")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
