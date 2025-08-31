#!/usr/bin/env python3
"""
Test script to verify frontend GraphQL integration with Rust backend
"""

import requests
import json

# Test the GraphQL endpoint with Rust queries
def test_rust_graphql_integration():
    print("🧪 Testing Frontend GraphQL Integration with Rust Backend...")
    
    # GraphQL endpoint
    url = "http://localhost:8001/graphql/"
    
    # Test 1: Rust Health Check
    print("\n1️⃣ Testing Rust Health Check Query...")
    health_query = {
        "query": """
        query {
          rustHealth {
            status
            service
            timestamp
          }
        }
        """
    }
    
    try:
        response = requests.post(url, json=health_query)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Health Check: {data}")
        else:
            print(f"❌ Health Check Failed: {response.status_code}")
            print(response.text)
    except Exception as e:
        print(f"❌ Health Check Error: {e}")
    
    # Test 2: Rust Stock Analysis
    print("\n2️⃣ Testing Rust Stock Analysis Query...")
    analysis_query = {
        "query": """
        query {
          rustStockAnalysis(symbol: "AAPL") {
            symbol
            beginnerFriendlyScore
            riskLevel
            recommendation
            technicalIndicators {
              rsi
              macd
              sma20
              sma50
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
    }
    
    try:
        response = requests.post(url, json=analysis_query)
        if response.status_code == 200:
            data = response.json()
            if 'errors' in data:
                print(f"❌ Analysis Query Errors: {data['errors']}")
            else:
                print(f"✅ Analysis Query: {data}")
        else:
            print(f"❌ Analysis Query Failed: {response.status_code}")
            print(response.text)
    except Exception as e:
        print(f"❌ Analysis Query Error: {e}")
    
    # Test 3: Rust Recommendations
    print("\n3️⃣ Testing Rust Recommendations Query...")
    recommendations_query = {
        "query": """
        query {
          rustRecommendations {
            symbol
            reason
            riskLevel
            beginnerScore
          }
        }
        """
    }
    
    try:
        response = requests.post(url, json=recommendations_query)
        if response.status_code == 200:
            data = response.json()
            if 'errors' in data:
                print(f"❌ Recommendations Query Errors: {data['errors']}")
            else:
                print(f"✅ Recommendations Query: {data}")
        else:
            print(f"❌ Recommendations Query Failed: {response.status_code}")
            print(response.text)
    except Exception as e:
        print(f"❌ Recommendations Query Error: {e}")
    
    print("\n🎉 Frontend Integration Testing Complete!")

if __name__ == "__main__":
    test_rust_graphql_integration()
