#!/usr/bin/env python3
"""
Test Advanced Analysis GraphQL query
"""

import requests
import json

BASE_URL = "http://192.168.1.236:8000"

def test_advanced_analysis():
    """Test the Advanced Analysis GraphQL query"""
    print("🔍 Testing Advanced Analysis GraphQL Query...")
    
    query = """
    query GetRustStockAnalysis($symbol: String!) {
        rustStockAnalysis(symbol: $symbol) {
            symbol
            beginnerFriendlyScore
            riskLevel
            recommendation
            technicalIndicators {
                rsi
                macd
                macdSignal
                macdHistogram
                sma20
                sma50
                ema12
                ema26
                bollingerUpper
                bollingerLower
                bollingerMiddle
            }
            fundamentalAnalysis {
                valuationScore
                growthScore
                stabilityScore
                dividendScore
                debtScore
            }
            reasoning
        }
    }
    """
    
    variables = {"symbol": "AAPL"}
    
    try:
        response = requests.post(
            f"{BASE_URL}/graphql/",
            json={"query": query, "variables": variables},
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Advanced Analysis Query: SUCCESS")
            print(f"📊 Response: {json.dumps(data, indent=2)}")
            return True
        else:
            print(f"❌ Advanced Analysis Query: FAILED ({response.status_code})")
            print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Advanced Analysis Query: ERROR - {str(e)}")
        return False

def test_other_queries():
    """Test other related queries"""
    print("\n🔍 Testing Other Stock Queries...")
    
    queries = [
        {
            "name": "Stock Chart Data",
            "query": """
            query GetStockChartData($symbol: String!, $tf: String!, $iv: String!, $limit: Int!, $inds: [String!]!) {
                stockChartData(symbol: $symbol, timeframe: $tf, interval: $iv, limit: $limit, indicators: $inds) {
                    symbol
                    currentPrice
                    changePercent
                    indicators
                }
            }
            """,
            "variables": {
                "symbol": "AAPL",
                "tf": "1D",
                "iv": "1D", 
                "limit": 30,
                "inds": ["SMA20", "SMA50", "RSI", "MACD"]
            }
        },
        {
            "name": "Stock Quotes",
            "query": """
            query GetQuotes($symbols: [String!]!) {
                quotes(symbols: $symbols) {
                    symbol
                    price
                    changePct
                }
            }
            """,
            "variables": {
                "symbols": ["AAPL", "MSFT"]
            }
        }
    ]
    
    results = []
    for test in queries:
        try:
            response = requests.post(
                f"{BASE_URL}/graphql/",
                json={"query": test["query"], "variables": test["variables"]},
                headers={"Content-Type": "application/json"},
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                if "errors" in data:
                    print(f"⚠️  {test['name']}: GraphQL Errors - {data['errors']}")
                    results.append(False)
                else:
                    print(f"✅ {test['name']}: SUCCESS")
                    results.append(True)
            else:
                print(f"❌ {test['name']}: FAILED ({response.status_code})")
                results.append(False)
                
        except Exception as e:
            print(f"❌ {test['name']}: ERROR - {str(e)}")
            results.append(False)
    
    return results

def main():
    print("🚀 Testing Advanced Analysis and Related Queries")
    print("=" * 60)
    
    # Test Advanced Analysis
    analysis_success = test_advanced_analysis()
    
    # Test other queries
    other_results = test_other_queries()
    
    print(f"\n📊 Results Summary:")
    print(f"Advanced Analysis: {'✅ SUCCESS' if analysis_success else '❌ FAILED'}")
    print(f"Other Queries: {sum(other_results)}/{len(other_results)} successful")
    
    if analysis_success and all(other_results):
        print("\n🎉 All queries working! Advanced Analysis should work in the mobile app.")
    else:
        print("\n⚠️  Some queries failed. Check the errors above.")

if __name__ == "__main__":
    main()
