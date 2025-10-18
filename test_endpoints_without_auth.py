#!/usr/bin/env python3
"""
Test GraphQL endpoints that don't require authentication
"""

import requests
import json
import time

BASE_URL = "http://192.168.1.236:8000"

def test_endpoint(name, query, variables=None):
    """Test a single GraphQL endpoint"""
    print(f"\n🔍 Testing {name}...")
    
    payload = {
        "query": query
    }
    
    if variables:
        payload["variables"] = variables
    
    try:
        response = requests.post(
            f"{BASE_URL}/graphql/",
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            if "errors" in data:
                print(f"    ❌ {name} failed: {data['errors']}")
                return False
            else:
                result_data = data.get("data", {})
                print(f"    ✅ {name} successful")
                print(f"       Data keys: {list(result_data.keys())}")
                
                # Show some sample data
                for key, value in result_data.items():
                    if isinstance(value, list):
                        print(f"       {key}: {len(value)} items")
                    elif isinstance(value, dict):
                        print(f"       {key}: {len(value)} fields")
                    else:
                        print(f"       {key}: {value}")
                return True
        else:
            print(f"    ❌ {name} failed: HTTP {response.status_code}")
            return False
            
    except Exception as e:
        print(f"    ❌ {name} error: {e}")
        return False

def test_public_endpoints():
    """Test endpoints that don't require authentication"""
    print("🚀 Testing Public GraphQL Endpoints")
    print("=" * 50)
    
    endpoints = [
        {
            "name": "Schema Introspection",
            "query": """
            query {
                __schema {
                    queryType {
                        name
                        fields {
                            name
                            description
                        }
                    }
                }
            }
            """
        },
        {
            "name": "Top Yields (DeFi)",
            "query": """
            query GetTopYields($limit: Int) {
                topYields(limit: $limit) {
                    protocol
                    chain
                    apy
                    tvl
                    pool
                    token
                    risk
                }
            }
            """,
            "variables": {"limit": 5}
        },
        {
            "name": "AI Yield Optimizer",
            "query": """
            query GetAIYieldOptimizer($input: JSONString!) {
                aiYieldOptimizer(input: $input) {
                    optimizedYield
                    strategy
                    riskScore
                    recommendations {
                        protocol
                        allocation
                        expectedReturn
                    }
                }
            }
            """,
            "variables": {
                "input": json.dumps({
                    "riskTolerance": "medium",
                    "investmentAmount": 10000,
                    "timeHorizon": "6months"
                })
            }
        },
        {
            "name": "Stock Quotes",
            "query": """
            query GetStockQuotes($symbols: [String!]!) {
                stockQuotes(symbols: $symbols) {
                    symbol
                    price
                    change
                    changePercent
                    volume
                    marketCap
                }
            }
            """,
            "variables": {"symbols": ["AAPL", "MSFT", "TSLA"]}
        },
        {
            "name": "Crypto ML Signal",
            "query": """
            query GetCryptoMLSignal($symbol: String!) {
                cryptoMlSignal(symbol: $symbol) {
                    symbol
                    predictionType
                    probability
                    confidence
                    targetPrice
                    stopLoss
                    explanation
                    createdAt
                }
            }
            """,
            "variables": {"symbol": "BTC"}
        },
        {
            "name": "Generate ML Prediction",
            "query": """
            mutation GenerateMLPrediction($symbol: String!) {
                generateMlPrediction(symbol: $symbol) {
                    success
                    predictionId
                    probability
                    direction
                    targetPrice
                    explanation
                    message
                }
            }
            """,
            "variables": {"symbol": "ETH"}
        }
    ]
    
    passed = 0
    total = len(endpoints)
    
    for endpoint in endpoints:
        if test_endpoint(endpoint["name"], endpoint["query"], endpoint.get("variables")):
            passed += 1
    
    print(f"\n📊 Results: {passed}/{total} endpoints working")
    
    if passed == total:
        print("🎉 All public endpoints are working!")
    else:
        print(f"⚠️  {total - passed} endpoints need attention")
    
    return passed == total

def test_rest_endpoints():
    """Test REST API endpoints"""
    print("\n🌐 Testing REST API Endpoints")
    print("=" * 50)
    
    # Test health endpoint
    print("\n🔍 Testing Health Endpoint...")
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"    ✅ Health endpoint working: {data}")
        else:
            print(f"    ❌ Health endpoint failed: {response.status_code}")
    except Exception as e:
        print(f"    ❌ Health endpoint error: {e}")
    
    # Test stock quotes endpoint
    print("\n🔍 Testing Stock Quotes REST API...")
    try:
        response = requests.get(f"{BASE_URL}/api/market/quotes?symbols=AAPL,MSFT,TSLA", timeout=10)
        if response.status_code == 200:
            data = response.json()
            if isinstance(data, dict) and "quotes" in data:
                quotes = data["quotes"]
                print(f"    ✅ Stock quotes API working: {len(quotes)} quotes received")
                for quote in quotes[:3]:  # Show first 3
                    print(f"       {quote.get('symbol')}: ${quote.get('price', 'N/A')}")
            else:
                print(f"    ⚠️  Stock quotes API returned unexpected format: {data}")
        else:
            print(f"    ❌ Stock quotes API failed: {response.status_code}")
    except Exception as e:
        print(f"    ❌ Stock quotes API error: {e}")

def main():
    print("🧪 Comprehensive GraphQL & REST API Testing")
    print("=" * 60)
    
    # Test public GraphQL endpoints
    graphql_success = test_public_endpoints()
    
    # Test REST endpoints
    test_rest_endpoints()
    
    print(f"\n🏁 Testing Complete!")
    if graphql_success:
        print("✅ All public GraphQL endpoints are working correctly")
    else:
        print("⚠️  Some GraphQL endpoints need attention")

if __name__ == "__main__":
    main()
