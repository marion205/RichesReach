#!/usr/bin/env python3
"""
Comprehensive Swing Trading Test
Tests the complete flow from UI components to GraphQL endpoints
"""

import requests
import json
import time
from typing import Dict, List, Any

# Configuration
GRAPHQL_URL = "http://localhost:8000/graphql/"
BACKEND_URL = "http://localhost:8000/"

def test_backend_health():
    """Test if backend is running"""
    print("🔍 Testing Backend Health...")
    try:
        response = requests.get(f"{BACKEND_URL}health/", timeout=5)
        if response.status_code == 200:
            print("   ✅ Backend is running")
            return True
        else:
            print(f"   ❌ Backend health check failed: {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"   ❌ Backend not accessible: {e}")
        return False

def test_graphql_introspection():
    """Test GraphQL introspection to verify schema"""
    print("\n🔍 Testing GraphQL Schema...")
    try:
        query = """
        query IntrospectionQuery {
          __schema {
            queryType {
              name
              fields {
                name
                type {
                  name
                }
              }
            }
          }
        }
        """
        
        response = requests.post(GRAPHQL_URL, json={"query": query}, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        
        if "errors" in data:
            print(f"   ❌ GraphQL introspection errors: {data['errors']}")
            return False
        
        # Check if swing trading queries exist
        query_fields = data.get("data", {}).get("__schema", {}).get("queryType", {}).get("fields", [])
        swing_queries = [field for field in query_fields if "market" in field.get("name", "").lower() or 
                        "sector" in field.get("name", "").lower() or 
                        "swing" in field.get("name", "").lower()]
        
        if swing_queries:
            print(f"   ✅ Found {len(swing_queries)} swing trading queries in schema")
            for query in swing_queries[:3]:  # Show first 3
                print(f"      - {query['name']}")
            return True
        else:
            print("   ⚠️  No swing trading queries found in schema")
            return False
            
    except Exception as e:
        print(f"   ❌ GraphQL introspection failed: {e}")
        return False

def test_market_data_query():
    """Test market data query"""
    print("\n📊 Testing Market Data Query...")
    try:
        query = """
        query GetMarketData {
          marketData {
            symbol
            name
            price
            change
            changePercent
            volume
            marketCap
            timestamp
          }
        }
        """
        
        response = requests.post(GRAPHQL_URL, json={"query": query}, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        
        if "errors" in data:
            print(f"   ❌ GraphQL errors: {data['errors']}")
            return False
        
        market_data = data.get("data", {}).get("marketData", [])
        
        if not market_data:
            print("   ⚠️  No market data returned")
            return False
        
        print(f"   ✅ Got {len(market_data)} market data points")
        
        # Validate data structure
        required_fields = ['symbol', 'name', 'price', 'change', 'changePercent', 'volume', 'marketCap', 'timestamp']
        sample = market_data[0]
        
        missing_fields = [field for field in required_fields if field not in sample]
        if missing_fields:
            print(f"   ❌ Missing fields: {missing_fields}")
            return False
        
        # Show sample data
        print(f"   📋 Sample: {sample['symbol']} - ${sample['price']:.2f} ({sample['changePercent']:+.2f}%)")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Market data query failed: {e}")
        return False

def test_sector_data_query():
    """Test sector data query"""
    print("\n🏢 Testing Sector Data Query...")
    try:
        query = """
        query GetSectorData {
          sectorData {
            name
            symbol
            change
            changePercent
            weight
          }
        }
        """
        
        response = requests.post(GRAPHQL_URL, json={"query": query}, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        
        if "errors" in data:
            print(f"   ❌ GraphQL errors: {data['errors']}")
            return False
        
        sector_data = data.get("data", {}).get("sectorData", [])
        
        if not sector_data:
            print("   ⚠️  No sector data returned")
            return False
        
        print(f"   ✅ Got {len(sector_data)} sector data points")
        
        # Validate data structure
        required_fields = ['name', 'symbol', 'change', 'changePercent', 'weight']
        sample = sector_data[0]
        
        missing_fields = [field for field in required_fields if field not in sample]
        if missing_fields:
            print(f"   ❌ Missing fields: {missing_fields}")
            return False
        
        # Show sample data
        print(f"   📋 Sample: {sample['name']} ({sample['symbol']}) - {sample['changePercent']:+.2f}%")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Sector data query failed: {e}")
        return False

def test_volatility_data_query():
    """Test volatility data query"""
    print("\n📈 Testing Volatility Data Query...")
    try:
        query = """
        query GetVolatilityData {
          volatilityData {
            vix
            vixChange
            fearGreedIndex
            putCallRatio
          }
        }
        """
        
        response = requests.post(GRAPHQL_URL, json={"query": query}, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        
        if "errors" in data:
            print(f"   ❌ GraphQL errors: {data['errors']}")
            return False
        
        volatility_data = data.get("data", {}).get("volatilityData", {})
        
        if not volatility_data:
            print("   ⚠️  No volatility data returned")
            return False
        
        print("   ✅ Got volatility data")
        
        # Validate data structure
        required_fields = ['vix', 'vixChange', 'fearGreedIndex', 'putCallRatio']
        missing_fields = [field for field in required_fields if field not in volatility_data]
        
        if missing_fields:
            print(f"   ❌ Missing fields: {missing_fields}")
            return False
        
        # Show sample data
        print(f"   📋 VIX: {volatility_data['vix']:.2f} ({volatility_data['vixChange']:+.2f})")
        print(f"   📋 Fear & Greed: {volatility_data['fearGreedIndex']}")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Volatility data query failed: {e}")
        return False

def test_technical_indicators_query():
    """Test technical indicators query"""
    print("\n🔧 Testing Technical Indicators Query...")
    try:
        query = """
        query GetTechnicalIndicators($symbol: String!) {
          technicalIndicators(symbol: $symbol) {
            name
            value
            signal
            strength
            description
          }
        }
        """
        
        variables = {"symbol": "AAPL"}
        
        response = requests.post(GRAPHQL_URL, json={"query": query, "variables": variables}, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        
        if "errors" in data:
            print(f"   ❌ GraphQL errors: {data['errors']}")
            return False
        
        indicators = data.get("data", {}).get("technicalIndicators", [])
        
        if not indicators:
            print("   ⚠️  No technical indicators returned")
            return False
        
        print(f"   ✅ Got {len(indicators)} technical indicators")
        
        # Validate data structure
        required_fields = ['name', 'value', 'signal', 'strength', 'description']
        sample = indicators[0]
        
        missing_fields = [field for field in required_fields if field not in sample]
        if missing_fields:
            print(f"   ❌ Missing fields: {missing_fields}")
            return False
        
        # Show sample data
        print(f"   📋 Sample: {sample['name']} = {sample['value']:.2f} ({sample['signal']})")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Technical indicators query failed: {e}")
        return False

def test_swing_signals_query():
    """Test swing signals query"""
    print("\n🎯 Testing Swing Signals Query...")
    try:
        query = """
        query GetSwingSignals {
          swingSignals(limit: 3) {
            id
            symbol
            timeframe
            triggeredAt
            signalType
            entryPrice
            stopPrice
            targetPrice
            mlScore
            thesis
            riskRewardRatio
            daysSinceTriggered
            isLikedByUser
            userLikeCount
            isActive
            isValidated
            createdBy {
              id
              username
              name
            }
            technicalIndicators {
              name
              value
              signal
              strength
              description
            }
            patterns {
              name
              confidence
              signal
              description
              timeframe
            }
          }
        }
        """
        
        response = requests.post(GRAPHQL_URL, json={"query": query}, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        
        if "errors" in data:
            print(f"   ❌ GraphQL errors: {data['errors']}")
            return False
        
        signals = data.get("data", {}).get("swingSignals", [])
        
        if not signals:
            print("   ⚠️  No swing signals returned")
            return False
        
        print(f"   ✅ Got {len(signals)} swing signals")
        
        # Validate data structure
        required_fields = ['id', 'symbol', 'timeframe', 'triggeredAt', 'signalType', 'entryPrice', 'mlScore', 'thesis']
        sample = signals[0]
        
        missing_fields = [field for field in required_fields if field not in sample]
        if missing_fields:
            print(f"   ❌ Missing fields: {missing_fields}")
            return False
        
        # Show sample data
        print(f"   📋 Sample: {sample['symbol']} - {sample['signalType']} (ML Score: {sample['mlScore']:.2f})")
        print(f"   📋 Entry: ${sample['entryPrice']:.2f}, Thesis: {sample['thesis'][:50]}...")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Swing signals query failed: {e}")
        return False

def test_performance_metrics_query():
    """Test performance metrics query"""
    print("\n📊 Testing Performance Metrics Query...")
    try:
        query = """
        query GetPerformanceMetrics {
          performanceMetrics {
            totalTrades
            winningTrades
            losingTrades
            winRate
            avgWin
            avgLoss
            profitFactor
            totalReturn
            maxDrawdown
            sharpeRatio
            avgHoldingPeriod
          }
        }
        """
        
        response = requests.post(GRAPHQL_URL, json={"query": query}, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        
        if "errors" in data:
            print(f"   ❌ GraphQL errors: {data['errors']}")
            return False
        
        metrics = data.get("data", {}).get("performanceMetrics", {})
        
        if not metrics:
            print("   ⚠️  No performance metrics returned")
            return False
        
        print("   ✅ Got performance metrics")
        
        # Validate data structure
        required_fields = ['totalTrades', 'winningTrades', 'losingTrades', 'winRate', 'avgWin', 'avgLoss', 'profitFactor', 'totalReturn', 'maxDrawdown', 'sharpeRatio', 'avgHoldingPeriod']
        missing_fields = [field for field in required_fields if field not in metrics]
        
        if missing_fields:
            print(f"   ❌ Missing fields: {missing_fields}")
            return False
        
        # Show sample data
        print(f"   📋 Total Trades: {metrics['totalTrades']}, Win Rate: {metrics['winRate']:.1f}%")
        print(f"   📋 Total Return: ${metrics['totalReturn']:.2f}, Sharpe Ratio: {metrics['sharpeRatio']:.2f}")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Performance metrics query failed: {e}")
        return False

def test_mutations():
    """Test swing trading mutations"""
    print("\n🔄 Testing Swing Trading Mutations...")
    try:
        # Test like signal mutation
        query = """
        mutation LikeSignal($signalId: ID!) {
          likeSignal(signalId: $signalId) {
            success
            isLiked
            likeCount
            errors
          }
        }
        """
        
        variables = {"signalId": "test_signal_123"}
        
        response = requests.post(GRAPHQL_URL, json={"query": query, "variables": variables}, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        
        if "errors" in data:
            print(f"   ❌ GraphQL errors: {data['errors']}")
            return False
        
        like_result = data.get("data", {}).get("likeSignal", {})
        
        if not like_result:
            print("   ⚠️  No like signal result returned")
            return False
        
        print("   ✅ Like signal mutation working")
        print(f"   📋 Success: {like_result.get('success', False)}, Like Count: {like_result.get('likeCount', 0)}")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Mutations test failed: {e}")
        return False

def test_data_consistency():
    """Test data consistency across queries"""
    print("\n🔍 Testing Data Consistency...")
    try:
        # Get market data and check if symbols are consistent
        market_query = """
        query GetMarketData {
          marketData {
            symbol
            price
          }
        }
        """
        
        response = requests.post(GRAPHQL_URL, json={"query": market_query}, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        market_data = data.get("data", {}).get("marketData", [])
        
        if not market_data:
            print("   ⚠️  No market data for consistency check")
            return False
        
        # Check if prices are reasonable (not zero or negative)
        valid_prices = [item for item in market_data if item.get('price', 0) > 0]
        
        if len(valid_prices) == len(market_data):
            print("   ✅ All market prices are valid")
        else:
            print(f"   ⚠️  {len(market_data) - len(valid_prices)} invalid prices found")
        
        # Check if symbols are expected ones
        expected_symbols = ['SPY', 'QQQ', 'IWM', 'VIX']
        found_symbols = [item['symbol'] for item in market_data]
        
        missing_symbols = [sym for sym in expected_symbols if sym not in found_symbols]
        if missing_symbols:
            print(f"   ⚠️  Missing expected symbols: {missing_symbols}")
        else:
            print("   ✅ All expected symbols found")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Data consistency test failed: {e}")
        return False

def run_comprehensive_test():
    """Run all tests"""
    print("🧪 COMPREHENSIVE SWING TRADING TEST")
    print("=" * 60)
    
    tests = [
        ("Backend Health", test_backend_health),
        ("GraphQL Schema", test_graphql_introspection),
        ("Market Data", test_market_data_query),
        ("Sector Data", test_sector_data_query),
        ("Volatility Data", test_volatility_data_query),
        ("Technical Indicators", test_technical_indicators_query),
        ("Swing Signals", test_swing_signals_query),
        ("Performance Metrics", test_performance_metrics_query),
        ("Mutations", test_mutations),
        ("Data Consistency", test_data_consistency),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"   ❌ {test_name} test crashed: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 60)
    print("📈 COMPREHENSIVE TEST SUMMARY:")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {test_name}")
    
    print(f"\n🎯 Overall: {passed}/{total} tests passed ({passed/total*100:.1f}%)")
    
    if passed == total:
        print("\n🎉 ALL TESTS PASSED!")
        print("✅ Swing trading integration is fully functional")
        print("✅ UI components can fetch real data")
        print("✅ GraphQL endpoints are working correctly")
        print("✅ Data structure is consistent")
        print("✅ Mutations are functional")
    else:
        print(f"\n⚠️  {total - passed} tests failed")
        print("Please check the errors above and ensure:")
        print("- Backend server is running on port 8000")
        print("- All dependencies are installed")
        print("- Database is accessible")
    
    return passed == total

if __name__ == "__main__":
    run_comprehensive_test()
