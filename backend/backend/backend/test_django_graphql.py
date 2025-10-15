#!/usr/bin/env python3
"""
Test script to verify Django GraphQL endpoints are working correctly
"""
import requests
import json
import sys

def test_graphql_endpoint(base_url="http://localhost:8000"):
    """Test the GraphQL endpoint with various queries"""
    
    graphql_url = f"{base_url}/graphql/"
    
    # Test queries
    test_queries = [
        {
            "name": "Ping Test",
            "query": """
                query {
                    ping
                }
            """
        },
        {
            "name": "Advanced Stock Screening with Reasoning",
            "query": """
                query GetAdvancedStockScreening($limit: Int, $sortBy: String) {
                    advancedStockScreening(limit: $limit, sortBy: $sortBy) {
                        symbol
                        companyName
                        sector
                        reasoning
                    }
                }
            """,
            "variables": {"limit": 3, "sortBy": "ml_score"}
        },
        {
            "name": "Stock Chart Data with MACDHist",
            "query": """
                query Chart($symbol: String!, $inds: [String!]) {
                    stockChartData(symbol: $symbol, indicators: $inds) {
                        symbol
                        currentPrice
                        indicators {
                            MACDHist
                            MACD_hist
                            SMA20
                            RSI14
                        }
                    }
                }
            """,
            "variables": {"symbol": "AAPL", "inds": ["SMA20", "RSI14", "MACD", "MACDHist"]}
        },
        {
            "name": "Beginner Friendly Stocks",
            "query": """
                query GetBeginnerFriendlyStocks {
                    beginnerFriendlyStocks {
                        id
                        symbol
                        companyName
                        sector
                        marketCap
                        peRatio
                        dividendYield
                        beginnerFriendlyScore
                    }
                }
            """
        },
        {
            "name": "Option Orders Query",
            "query": """
                query OptionOrders($status: String) {
                    optionOrders(status: $status) {
                        id
                        symbol
                        optionType
                        strike
                        expiration
                        side
                        quantity
                        orderType
                        status
                    }
                }
            """,
            "variables": {"status": "FILLED"}
        }
    ]
    
    print(f"🧪 Testing Django GraphQL endpoint: {graphql_url}")
    print("=" * 60)
    
    success_count = 0
    total_tests = len(test_queries)
    
    for test in test_queries:
        print(f"\n📋 Testing: {test['name']}")
        
        payload = {
            "query": test["query"]
        }
        
        if "variables" in test:
            payload["variables"] = test["variables"]
        
        try:
            response = requests.post(
                graphql_url,
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                
                if "errors" in data and data["errors"]:
                    print(f"❌ GraphQL Errors: {data['errors']}")
                elif "data" in data:
                    print(f"✅ Success: {test['name']}")
                    success_count += 1
                    
                    # Show sample data for verification
                    if test["name"] == "Advanced Stock Screening with Reasoning":
                        if data["data"]["advancedStockScreening"]:
                            sample = data["data"]["advancedStockScreening"][0]
                            print(f"   📊 Sample: {sample['symbol']} - {sample.get('reasoning', 'No reasoning')}")
                    
                    elif test["name"] == "Stock Chart Data with MACDHist":
                        if data["data"]["stockChartData"]:
                            chart_data = data["data"]["stockChartData"]
                            indicators = chart_data.get("indicators", {})
                            print(f"   📈 Chart: {chart_data['symbol']} - MACDHist: {indicators.get('MACDHist', 'Missing')}")
                else:
                    print(f"❌ No data in response: {data}")
            else:
                print(f"❌ HTTP Error {response.status_code}: {response.text}")
                
        except requests.exceptions.RequestException as e:
            print(f"❌ Request failed: {e}")
        except json.JSONDecodeError as e:
            print(f"❌ JSON decode error: {e}")
    
    print("\n" + "=" * 60)
    print(f"📊 Test Results: {success_count}/{total_tests} tests passed")
    
    if success_count == total_tests:
        print("🎉 All tests passed! Django GraphQL is working correctly.")
        return True
    else:
        print("⚠️  Some tests failed. Check the errors above.")
        return False

if __name__ == "__main__":
    # Allow custom base URL
    base_url = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8000"
    success = test_graphql_endpoint(base_url)
    sys.exit(0 if success else 1)
