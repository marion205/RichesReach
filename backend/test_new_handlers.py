#!/usr/bin/env python3
"""
Test New GraphQL Handlers
"""

import requests
import time

BASE_URL = "http://localhost:8123"

def test_ml_signal():
    """Test ML signal with new handler"""
    print("🤖 Testing ML Signal with New Handler...")
    
    # Test 1: With variables
    print("   Test 1: With variables")
    response = requests.post(f"{BASE_URL}/graphql/", json={
        "query": "query($s: String!) { cryptoMlSignal(symbol: $s) { symbol probability confidenceLevel explanation } }",
        "variables": {"s": "BTC"}
    }, timeout=10)
    
    print(f"   Status: {response.status_code}")
    print(f"   Response: {response.json()}")
    
    # Test 2: Without variables (inline)
    print("\n   Test 2: Without variables")
    response = requests.post(f"{BASE_URL}/graphql/", json={
        "query": "query { cryptoMlSignal(symbol: \"BTC\") { symbol probability confidenceLevel explanation } }"
    }, timeout=10)
    
    print(f"   Status: {response.status_code}")
    print(f"   Response: {response.json()}")

def test_recommendations():
    """Test recommendations with new handler"""
    print("\n🚀 Testing Recommendations with New Handler...")
    
    response = requests.post(f"{BASE_URL}/graphql/", json={
        "query": "query { cryptoRecommendations(limit: 3) { symbol score probability confidenceLevel explanation } }"
    }, timeout=10)
    
    print(f"   Status: {response.status_code}")
    print(f"   Response: {response.json()}")

def test_field_detection():
    """Test field detection"""
    print("\n🔍 Testing Field Detection...")
    
    # Test what fields are detected
    response = requests.post(f"{BASE_URL}/graphql/", json={
        "query": "query { cryptoMlSignal(symbol: \"BTC\") { symbol } }"
    }, timeout=10)
    
    print(f"   Status: {response.status_code}")
    print(f"   Response: {response.json()}")

if __name__ == "__main__":
    test_field_detection()
    test_ml_signal()
    test_recommendations()
