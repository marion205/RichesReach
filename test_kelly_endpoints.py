#!/usr/bin/env python3
"""
Quick test script to verify Kelly Criterion endpoints are working
"""
import requests
import json
import sys

BASE_URL = "http://127.0.0.1:8000"
GRAPHQL_URL = f"{BASE_URL}/graphql"

def test_health():
    """Test server health"""
    print("🔍 Testing server health...")
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        if response.status_code == 200:
            print("✅ Server is healthy")
            return True
        else:
            print(f"❌ Server returned status {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Server not responding: {e}")
        return False

def test_portfolio_kelly_metrics():
    """Test portfolioKellyMetrics GraphQL query"""
    print("\n🔍 Testing portfolioKellyMetrics query...")
    
    query = """
    query PortfolioKellyMetrics {
        portfolioKellyMetrics {
            totalPortfolioValue
            aggregateKellyFraction
            aggregateRecommendedFraction
            portfolioMaxDrawdownRisk
            weightedWinRate
            positionCount
            totalPositions
        }
    }
    """
    
    try:
        response = requests.post(
            GRAPHQL_URL,
            json={"query": query},
            headers={
                "Content-Type": "application/json",
                "Authorization": "Bearer dev-token-test"
            },
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            if "errors" in data:
                print(f"❌ GraphQL errors: {json.dumps(data['errors'], indent=2)}")
                return False
            else:
                metrics = data.get("data", {}).get("portfolioKellyMetrics", {})
                print("✅ Query successful!")
                print(f"   Total Portfolio Value: ${metrics.get('totalPortfolioValue', 0):,.2f}")
                print(f"   Total Positions: {metrics.get('totalPositions', 0)}")
                print(f"   Positions with Kelly Data: {metrics.get('positionCount', 0)}")
                print(f"   Aggregate Kelly Fraction: {metrics.get('aggregateKellyFraction', 0):.4f}")
                print(f"   Recommended Fraction: {metrics.get('aggregateRecommendedFraction', 0):.4f}")
                print(f"   Max Drawdown Risk: {metrics.get('portfolioMaxDrawdownRisk', 0):.4f}")
                print(f"   Weighted Win Rate: {metrics.get('weightedWinRate', 0):.4f}")
                return True
        else:
            print(f"❌ HTTP {response.status_code}: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_calculate_position_size_kelly():
    """Test calculatePositionSize with Kelly method"""
    print("\n🔍 Testing calculatePositionSize with Kelly method...")
    
    query = """
    query CalculatePositionSize {
        calculatePositionSize(
            accountEquity: 10000
            entryPrice: 150
            stopPrice: 145
            method: "KELLY"
            symbol: "AAPL"
        ) {
            positionSize
            positionValue
            kellyFraction
            recommendedFraction
            maxDrawdownRisk
            winRate
            avgWin
            avgLoss
        }
    }
    """
    
    try:
        response = requests.post(
            GRAPHQL_URL,
            json={
                "query": query,
                "operationName": "CalculatePositionSize"
            },
            headers={
                "Content-Type": "application/json",
                "Authorization": "Bearer dev-token-test"
            },
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            if "errors" in data:
                print(f"❌ GraphQL errors: {json.dumps(data['errors'], indent=2)}")
                return False
            else:
                result = data.get("data", {}).get("calculatePositionSize", {})
                print("✅ Query successful!")
                print(f"   Position Size: {result.get('positionSize', 0)} shares")
                print(f"   Position Value: ${result.get('positionValue', 0):,.2f}")
                print(f"   Kelly Fraction: {result.get('kellyFraction', 0):.4f}")
                print(f"   Recommended Fraction: {result.get('recommendedFraction', 0):.4f}")
                print(f"   Max Drawdown Risk: {result.get('maxDrawdownRisk', 0):.4f}")
                print(f"   Win Rate: {result.get('winRate', 0):.4f}")
                return True
        else:
            print(f"❌ HTTP {response.status_code}: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def main():
    print("=" * 60)
    print("Kelly Criterion Endpoints Test")
    print("=" * 60)
    
    # Test 1: Health check
    if not test_health():
        print("\n❌ Server is not running. Please start the backend server first.")
        sys.exit(1)
    
    # Test 2: Portfolio Kelly Metrics
    portfolio_test = test_portfolio_kelly_metrics()
    
    # Test 3: Calculate Position Size with Kelly
    position_test = test_calculate_position_size_kelly()
    
    # Summary
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)
    print(f"Health Check: ✅")
    print(f"Portfolio Kelly Metrics: {'✅' if portfolio_test else '❌'}")
    print(f"Calculate Position Size (Kelly): {'✅' if position_test else '❌'}")
    
    if portfolio_test and position_test:
        print("\n✅ All tests passed! Backend is working correctly.")
        return 0
    else:
        print("\n⚠️  Some tests failed. Check the errors above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())

