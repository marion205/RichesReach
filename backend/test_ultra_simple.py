#!/usr/bin/env python3
"""
Ultra Simple Test to Find the 15-Second Delay
"""

import requests
import time

BASE_URL = "http://localhost:8123"

def test_ultra_simple():
    """Test with the simplest possible query"""
    print("🔍 ULTRA SIMPLE TEST")
    print("=" * 30)
    
    # Test 1: Just check if server responds
    print("1. Testing server health...")
    start = time.time()
    response = requests.get(f"{BASE_URL}/health", timeout=5)
    duration = time.time() - start
    print(f"   Health check: {duration:.3f}s")
    
    # Test 2: Simple GraphQL query
    print("\n2. Testing simple GraphQL...")
    start = time.time()
    response = requests.post(f"{BASE_URL}/graphql/", json={
        "query": "query { __typename }"
    }, timeout=5)
    duration = time.time() - start
    print(f"   Simple GraphQL: {duration:.3f}s")
    
    # Test 3: Test with a non-existent field
    print("\n3. Testing non-existent field...")
    start = time.time()
    response = requests.post(f"{BASE_URL}/graphql/", json={
        "query": "query { nonExistentField }"
    }, timeout=5)
    duration = time.time() - start
    print(f"   Non-existent field: {duration:.3f}s")
    
    # Test 4: Test crypto recommendations with minimal constraints
    print("\n4. Testing crypto recommendations...")
    start = time.time()
    response = requests.post(f"{BASE_URL}/graphql/", json={
        "query": "query { cryptoRecommendations(constraints: { maxSymbols: 1 }) { success } }"
    }, timeout=20)
    duration = time.time() - start
    print(f"   Crypto recommendations: {duration:.3f}s")
    print(f"   Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"   Response: {data}")

if __name__ == "__main__":
    test_ultra_simple()
