#!/usr/bin/env python3
"""
Debug Crypto Performance Issues
"""

import requests
import time
import json

BASE_URL = "http://localhost:8123"

def test_individual_components():
    """Test each component individually to find bottlenecks"""
    print("🔍 DEBUGGING CRYPTO PERFORMANCE")
    print("=" * 50)
    
    # Test 1: ML Signal (should be fast)
    print("\n1. Testing ML Signal (should be < 1s):")
    start = time.time()
    response = requests.post(f"{BASE_URL}/graphql/", json={
        "query": "query { cryptoMlSignal(symbol: \"BTC\") { symbol predictionType probability } }"
    })
    duration = time.time() - start
    print(f"   Duration: {duration:.2f}s")
    print(f"   Status: {response.status_code}")
    
    # Test 2: Simple recommendations query
    print("\n2. Testing Simple Recommendations:")
    start = time.time()
    response = requests.post(f"{BASE_URL}/graphql/", json={
        "query": "query { cryptoRecommendations(constraints: { maxSymbols: 1 }) { success } }"
    })
    duration = time.time() - start
    print(f"   Duration: {duration:.2f}s")
    print(f"   Status: {response.status_code}")
    
    # Test 3: Check if it's the batch price fetching
    print("\n3. Testing Batch Price Fetching:")
    start = time.time()
    response = requests.post(f"{BASE_URL}/graphql/", json={
        "query": "query { cryptoRecommendations(constraints: { maxSymbols: 2 }) { success recommendations { symbol } } }"
    })
    duration = time.time() - start
    print(f"   Duration: {duration:.2f}s")
    print(f"   Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"   Recommendations: {len(data.get('data', {}).get('cryptoRecommendations', {}).get('recommendations', []))}")
    
    # Test 4: Check server logs for errors
    print("\n4. Checking for errors in response:")
    if response.status_code == 200:
        data = response.json()
        if 'errors' in data:
            print(f"   Errors: {data['errors']}")
        else:
            print("   No errors in response")

if __name__ == "__main__":
    test_individual_components()
