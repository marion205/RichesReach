#!/usr/bin/env python3
"""
RAHA GraphQL End-to-End Test Script
Tests all GraphQL queries and mutations
"""

import requests
import json
import sys

BASE_URL = "http://127.0.0.1:8000/graphql/"
AUTH_TOKEN = "dev-token-test"

def test_query(name, query):
    """Test a GraphQL query"""
    print(f"Testing {name}... ", end="", flush=True)
    
    payload = {"query": query}
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {AUTH_TOKEN}"
    }
    
    try:
        response = requests.post(BASE_URL, json=payload, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        if "errors" in data and data["errors"]:
            print("❌ FAIL")
            print(json.dumps(data["errors"], indent=2))
            return False
        elif "data" in data:
            print("✅ PASS")
            # Show a snippet of the data
            if data["data"]:
                data_preview = json.dumps(data["data"], indent=2)
                lines = data_preview.split('\n')[:5]
                if len(lines) < len(data_preview.split('\n')):
                    print(f"   Preview: {lines[0]}...")
                else:
                    print(f"   {data_preview[:100]}...")
            return True
        else:
            print("⚠️  UNKNOWN")
            print(f"   Response: {response.text[:200]}")
            return False
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
        return False

def main():
    print("🧪 RAHA GraphQL End-to-End Testing")
    print("=" * 50)
    print()
    
    results = []
    
    # Test 1: Get Strategies
    query1 = """
    query {
        strategies {
            id
            name
            slug
            description
            category
        }
    }
    """
    results.append(("Get Strategies", test_query("Get Strategies", query1)))
    print()
    
    # Test 2: Get User Strategy Settings
    query2 = """
    query {
        userStrategySettings {
            id
            enabled
            parameters
            strategyVersion {
                id
                strategy {
                    name
                }
            }
        }
    }
    """
    results.append(("Get User Strategy Settings", test_query("Get User Strategy Settings", query2)))
    print()
    
    # Test 3: Get RAHA Signals
    query3 = """
    query {
        rahaSignals(symbol: "AAPL", timeframe: "5m", limit: 5) {
            id
            signalType
            price
            stopLoss
            takeProfit
            confidenceScore
        }
    }
    """
    results.append(("Get RAHA Signals", test_query("Get RAHA Signals", query3)))
    print()
    
    # Test 4: Get Stock Chart Data
    query4 = """
    query {
        stockChartData(symbol: "AAPL", timeframe: "1H") {
            symbol
            data {
                timestamp
                open
                close
            }
        }
    }
    """
    results.append(("Get Stock Chart Data", test_query("Get Stock Chart Data", query4)))
    print()
    
    # Test 5: Get User Backtests
    query5 = """
    query {
        userBacktests(limit: 5) {
            id
            status
            createdAt
            metrics
        }
    }
    """
    results.append(("Get User Backtests", test_query("Get User Backtests", query5)))
    print()
    
    # Summary
    print("=" * 50)
    print("📊 Test Summary")
    print("=" * 50)
    passed = sum(1 for _, result in results if result)
    total = len(results)
    print(f"Passed: {passed}/{total}")
    print()
    
    if passed == total:
        print("✅ All tests passed!")
        return 0
    else:
        print("⚠️  Some tests failed. Check output above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
