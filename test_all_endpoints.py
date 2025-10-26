#!/usr/bin/env python3
"""
Comprehensive endpoint testing script for RichesReach
Tests all critical endpoints to ensure 100% functionality
"""

import requests
import json
import time
import sys

BASE_URL = "http://localhost:8000"

def test_endpoint(method, endpoint, data=None, expected_status=200, description=""):
    """Test a single endpoint and return results"""
    try:
        if method == "GET":
            response = requests.get(f"{BASE_URL}{endpoint}", timeout=10)
        elif method == "POST":
            response = requests.post(f"{BASE_URL}{endpoint}", json=data, timeout=10)
        
        success = response.status_code == expected_status
        print(f"{'✅' if success else '❌'} {description}")
        print(f"   Status: {response.status_code} (expected: {expected_status})")
        
        if response.status_code == 200:
            try:
                json_data = response.json()
                print(f"   Response: {json.dumps(json_data, indent=2)[:200]}...")
            except:
                print(f"   Response: {response.text[:200]}...")
        else:
            print(f"   Error: {response.text[:200]}...")
        
        print()
        return success
        
    except Exception as e:
        print(f"❌ {description}")
        print(f"   Error: {str(e)}")
        print()
        return False

def main():
    print("🚀 RICHESREACH COMPREHENSIVE ENDPOINT TESTING")
    print("=" * 50)
    
    # Wait for server to be ready
    print("⏳ Waiting for server to be ready...")
    time.sleep(3)
    
    # Test basic connectivity
    print("1. BASIC CONNECTIVITY TESTS")
    print("-" * 30)
    test_endpoint("GET", "/health", description="Health Check")
    
    # Test GraphQL endpoint
    print("2. GRAPHQL ENDPOINT TESTS")
    print("-" * 30)
    
    # Test dayTradingPicks query
    graphql_query = {
        "query": """
        query {
            dayTradingPicks(mode: "SAFE") {
                asOf
                mode
                picks {
                    symbol
                    side
                    score
                    features {
                        momentum_15m
                        rvol_10m
                        catalyst_score
                        sentiment_score
                        news_sentiment
                        social_sentiment
                    }
                    risk {
                        atr_5m
                        size_shares
                        stop
                    }
                    notes
                }
                regimeContext {
                    regimeType
                    confidence
                    strategyWeights
                    recommendations
                    sentimentEnabled
                }
            }
        }
        """
    }
    
    test_endpoint("POST", "/graphql/", data=graphql_query, description="GraphQL dayTradingPicks Query")
    
    # Test AI endpoints
    print("3. AI ENDPOINT TESTS")
    print("-" * 30)
    test_endpoint("GET", "/api/regime-detection/current-regime/", description="Regime Detection")
    test_endpoint("GET", "/api/sentiment-analysis/AAPL", description="Sentiment Analysis")
    test_endpoint("GET", "/api/ml-picks/generate/SAFE", description="ML Pick Generation")
    
    # Test mobile features
    print("4. MOBILE FEATURE TESTS")
    print("-" * 30)
    gesture_data = {
        "symbol": "AAPL",
        "gesture_type": "swipe_right"
    }
    test_endpoint("POST", "/api/mobile/gesture-trade/", data=gesture_data, description="Mobile Gesture Trading")
    
    # Test voice AI
    print("5. VOICE AI TESTS")
    print("-" * 30)
    test_endpoint("GET", "/api/voice-ai/voices/", description="Voice AI Voices List")
    
    voice_data = {
        "text": "Test voice synthesis",
        "voice_id": "nova"
    }
    test_endpoint("POST", "/api/voice-ai/synthesize/", data=voice_data, description="Voice AI Synthesis")
    
    # Test market data
    print("6. MARKET DATA TESTS")
    print("-" * 30)
    test_endpoint("GET", "/api/market/quotes", description="Market Quotes")
    test_endpoint("GET", "/api/real-market/quotes/AAPL", description="Real Market Data")
    
    # Test brokerage
    print("7. BROKERAGE TESTS")
    print("-" * 30)
    test_endpoint("GET", "/api/real-brokerage/account/", description="Brokerage Account")
    test_endpoint("GET", "/api/real-brokerage/positions/", description="Brokerage Positions")
    
    # Test voice trading
    print("8. VOICE TRADING TESTS")
    print("-" * 30)
    test_endpoint("GET", "/api/voice-trading/help-commands/", description="Voice Trading Help")
    test_endpoint("GET", "/api/voice-trading/available-symbols/", description="Voice Trading Symbols")
    
    print("🎉 TESTING COMPLETE!")
    print("=" * 50)

if __name__ == "__main__":
    main()
