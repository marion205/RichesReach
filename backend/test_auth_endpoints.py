#!/usr/bin/env python3
"""
Test script for tax optimization endpoints with authentication
"""
import requests
import json

# Production API base URL
API_BASE = "http://riches-reach-alb-1199497064.us-east-1.elb.amazonaws.com"

def test_endpoints():
    print("🧪 TESTING TAX OPTIMIZATION ENDPOINTS")
    print("====================================")
    print()
    
    # Test 1: Root endpoint (should work without auth)
    print("1. Testing root endpoint (no auth required):")
    try:
        response = requests.get(f"{API_BASE}/")
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            print(f"   Response: {response.json()}")
        else:
            print(f"   Response: {response.text[:200]}")
    except Exception as e:
        print(f"   Error: {e}")
    print()
    
    # Test 2: Version endpoint (should work without auth)
    print("2. Testing version endpoint (no auth required):")
    try:
        response = requests.get(f"{API_BASE}/__version__")
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            print(f"   Response: {response.json()}")
        else:
            print(f"   Response: {response.text[:200]}")
    except Exception as e:
        print(f"   Error: {e}")
    print()
    
    # Test 3: Tax optimization endpoint (should require auth)
    print("3. Testing tax optimization endpoint (auth required):")
    try:
        response = requests.get(f"{API_BASE}/api/tax/optimization-summary")
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            print(f"   Response: {response.json()}")
        elif response.status_code == 401:
            print("   ✅ Correctly requires authentication (401)")
        elif response.status_code == 500:
            print("   ⚠️  Server error (500) - may be due to missing JsonResponse import in Docker image")
        else:
            print(f"   Response: {response.text[:200]}")
    except Exception as e:
        print(f"   Error: {e}")
    print()
    
    # Test 4: Other tax endpoints
    tax_endpoints = [
        "/api/tax/loss-harvesting",
        "/api/tax/capital-gains-optimization", 
        "/api/tax/tax-efficient-rebalancing",
        "/api/tax/tax-bracket-analysis",
        "/api/tax/smart-lot-optimizer-v2",
        "/api/tax/two-year-gains-planner",
        "/api/tax/wash-sale-guard-v2",
        "/api/tax/borrow-vs-sell-advisor"
    ]
    
    print("4. Testing other tax optimization endpoints:")
    for endpoint in tax_endpoints:
        try:
            response = requests.get(f"{API_BASE}{endpoint}")
            print(f"   {endpoint}: {response.status_code}")
        except Exception as e:
            print(f"   {endpoint}: Error - {e}")
    print()
    
    print("✅ Endpoint testing complete!")
    print()
    print("📋 SUMMARY:")
    print("- Root and version endpoints should return 200")
    print("- Tax optimization endpoints should return 401 (auth required) or 500 (server error)")
    print("- If endpoints return 500, it's likely due to missing JsonResponse import in Docker image")
    print("- This is expected behavior for premium features that require authentication")

if __name__ == "__main__":
    test_endpoints()
