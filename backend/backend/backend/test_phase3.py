#!/usr/bin/env python3
"""
Test script for Phase 3 features
"""
import requests
import json
import time

def test_endpoint():
    url = "http://localhost:8123/graphql"
    
    # Test 1: Basic chart data
    print("🧪 Testing Basic Chart Data...")
    query1 = {
        "query": "query Chart($symbol: String!) { stockChartData(symbol: $symbol) { symbol currentPrice } }",
        "variables": {"symbol": "AAPL"}
    }
    
    try:
        response = requests.post(url, json=query1, timeout=10)
        data = response.json()
        if "data" in data and data["data"].get("stockChartData"):
            print("✅ Basic chart data: WORKING")
        else:
            print("❌ Basic chart data: FAILED")
            print(f"Response: {data}")
    except Exception as e:
        print(f"❌ Basic chart data: ERROR - {e}")
    
    time.sleep(1)
    
    # Test 2: Batch chart data
    print("\n🧪 Testing Batch Chart Data...")
    query2 = {
        "query": "query BatchTest($symbols: [String!]!) { batchStockChartData(symbols: $symbols) { symbol currentPrice } }",
        "variables": {"symbols": ["AAPL", "MSFT"]}
    }
    
    try:
        response = requests.post(url, json=query2, timeout=10)
        data = response.json()
        if "data" in data and data["data"].get("batchStockChartData"):
            print("✅ Batch chart data: WORKING")
            print(f"Response: {data}")
        else:
            print("❌ Batch chart data: FAILED")
            print(f"Response: {data}")
    except Exception as e:
        print(f"❌ Batch chart data: ERROR - {e}")
    
    time.sleep(1)
    
    # Test 3: Research hub
    print("\n🧪 Testing Research Hub...")
    query3 = {
        "query": "query Research($symbol: String!) { researchHub(symbol: $symbol) { symbol company { name } } }",
        "variables": {"symbol": "AAPL"}
    }
    
    try:
        response = requests.post(url, json=query3, timeout=10)
        data = response.json()
        if "data" in data and data["data"].get("researchHub"):
            print("✅ Research hub: WORKING")
            print(f"Response: {data}")
        else:
            print("❌ Research hub: FAILED")
            print(f"Response: {data}")
    except Exception as e:
        print(f"❌ Research hub: ERROR - {e}")
    
    time.sleep(1)
    
    # Test 4: Options trading
    print("\n🧪 Testing Options Trading...")
    query4 = {
        "query": "mutation PlaceOrder($input: PlaceOptionOrderInput!) { placeOptionOrder(input: $input) { success preview order { id } } }",
        "variables": {"input": {"symbol": "AAPL", "optionType": "CALL", "strike": 170, "expiration": "2024-12-20", "side": "BUY", "orderType": "MARKET", "quantity": 1, "preview": True}}
    }
    
    try:
        response = requests.post(url, json=query4, timeout=10)
        data = response.json()
        if "data" in data and data["data"].get("placeOptionOrder"):
            print("✅ Options trading: WORKING")
            print(f"Response: {data}")
        else:
            print("❌ Options trading: FAILED")
            print(f"Response: {data}")
    except Exception as e:
        print(f"❌ Options trading: ERROR - {e}")

if __name__ == "__main__":
    test_endpoint()
