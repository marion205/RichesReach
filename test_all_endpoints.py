#!/usr/bin/env python3
"""
Comprehensive test script to verify all GraphQL endpoints used by the React Native app.
This will help identify which endpoints are causing 400 errors.
"""

import requests
import json
import sys

BASE_URL = "http://localhost:8000"
GRAPHQL_URL = f"{BASE_URL}/graphql/"

def test_endpoint(name, query, variables=None):
    """Test a GraphQL endpoint and return the result."""
    try:
        payload = {"query": query}
        if variables:
            payload["variables"] = variables
            
        response = requests.post(GRAPHQL_URL, json=payload, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            if "errors" in data:
                print(f"❌ {name}: GraphQL errors - {data['errors']}")
                return False
            else:
                print(f"✅ {name}: Success")
                return True
        else:
            print(f"❌ {name}: HTTP {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ {name}: Exception - {str(e)}")
        return False

def main():
    print("🧪 Testing All GraphQL Endpoints...")
    print("=" * 50)
    
    # Test queries
    tests = [
        ("Stocks Query", """
            query {
                stocks {
                    companyName
                    currentPrice
                    beginnerFriendlyScore
                    dividendScore
                }
            }
        """),
        
        ("Beginner Friendly Stocks", """
            query {
                beginnerFriendlyStocks {
                    companyName
                    currentPrice
                    beginnerFriendlyScore
                    dividendScore
                }
            }
        """),
        
        ("Stock Discussions", """
            query {
                stockDiscussions(stockSymbol: "AAPL") {
                    id
                    content
                    author
                    createdAt
                }
            }
        """),
        
        ("Crypto Prices", """
            query {
                cryptoPrices {
                    symbol
                    price
                    change24h
                }
            }
        """),
        
        ("Portfolio Analysis", """
            query {
                portfolioAnalysis {
                    totalValue
                    dailyChange
                    dailyChangePercent
                    totalReturn
                    totalReturnPercent
                }
            }
        """),
        
        ("Rust Stock Analysis", """
            query {
                rustStockAnalysis(symbol: "AAPL") {
                    symbol
                    fundamentalAnalysis {
                        dividendScore
                        peRatio
                        marketCap
                    }
                }
            }
        """),
        
        ("Advanced Stock Screening", """
            query {
                advancedStockScreening {
                    companyName
                    currentPrice
                    beginnerFriendlyScore
                    dividendScore
                }
            }
        """),
    ]
    
    passed = 0
    total = len(tests)
    
    for name, query in tests:
        if test_endpoint(name, query):
            passed += 1
    
    print("=" * 50)
    print(f"📊 Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All endpoints are working!")
        return 0
    else:
        print("⚠️  Some endpoints need fixing")
        return 1

if __name__ == "__main__":
    sys.exit(main())
