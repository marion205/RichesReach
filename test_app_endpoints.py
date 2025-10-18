#!/usr/bin/env python3
"""
Quick test of all app endpoints to ensure no 400/404/500 errors
"""

import requests
import json
import time

BASE_URL = "http://192.168.1.236:8000"

def test_endpoint(name, url, method="GET", data=None, headers=None):
    """Test a single endpoint"""
    print(f"🔍 Testing {name}...")
    
    try:
        if method == "GET":
            response = requests.get(url, timeout=10, headers=headers)
        elif method == "POST":
            response = requests.post(url, json=data, timeout=10, headers=headers)
        
        if response.status_code == 200:
            print(f"    ✅ {name}: OK (200)")
            return True
        elif response.status_code == 400:
            print(f"    ⚠️  {name}: Bad Request (400) - {response.text[:100]}")
            return False
        elif response.status_code == 404:
            print(f"    ❌ {name}: Not Found (404)")
            return False
        elif response.status_code == 500:
            print(f"    ❌ {name}: Server Error (500) - {response.text[:100]}")
            return False
        else:
            print(f"    ⚠️  {name}: {response.status_code} - {response.text[:100]}")
            return False
            
    except Exception as e:
        print(f"    ❌ {name}: Error - {str(e)}")
        return False

def main():
    print("🚀 Testing All App Endpoints")
    print("=" * 50)
    
    # Test basic endpoints
    endpoints = [
        ("Health Check", f"{BASE_URL}/health"),
        ("Root", f"{BASE_URL}/"),
        ("GraphQL", f"{BASE_URL}/graphql/", "POST", {"query": "{ __schema { queryType { name } } }"}),
        ("Stock Quotes", f"{BASE_URL}/api/market/quotes?symbols=AAPL,MSFT"),
        ("Admin", f"{BASE_URL}/admin/"),
    ]
    
    passed = 0
    total = len(endpoints)
    
    for endpoint in endpoints:
        if len(endpoint) == 2:
            name, url = endpoint
            if test_endpoint(name, url):
                passed += 1
        elif len(endpoint) == 4:
            name, url, method, data = endpoint
            if test_endpoint(name, url, method, data):
                passed += 1
    
    print(f"\n📊 Results: {passed}/{total} endpoints working")
    
    if passed == total:
        print("🎉 All endpoints are working perfectly!")
    else:
        print(f"⚠️  {total - passed} endpoints need attention")
    
    # Test GraphQL queries that the app uses
    print(f"\n🔍 Testing Key GraphQL Queries...")
    
    graphql_queries = [
        ("Top Yields", {"query": "query { topYields(limit: 5) { protocol apy } }"}),
        ("AI Optimizer", {"query": "query { aiYieldOptimizer(userRiskTolerance: 0.5, limit: 3) { expectedApy totalRisk } }"}),
        ("Stock Quotes", {"query": "query { quotes(symbols: [\"AAPL\", \"MSFT\"]) { symbol price changePct } }"}),
        ("ML Prediction", {"query": "mutation { generateMlPrediction(symbol: \"ETH\") { success probability } }"}),
    ]
    
    gql_passed = 0
    gql_total = len(graphql_queries)
    
    for name, query in graphql_queries:
        if test_endpoint(f"GraphQL: {name}", f"{BASE_URL}/graphql/", "POST", query):
            gql_passed += 1
    
    print(f"\n📊 GraphQL Results: {gql_passed}/{gql_total} queries working")
    
    print(f"\n🏁 Overall Status: {passed + gql_passed}/{total + gql_total} endpoints working")
    
    if passed + gql_passed == total + gql_total:
        print("🎉 Perfect! Your app should load without any errors!")
    else:
        print("⚠️  Some endpoints have issues - check the logs above")

if __name__ == "__main__":
    main()
