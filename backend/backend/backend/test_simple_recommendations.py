#!/usr/bin/env python3
"""
Test Simple Recommendations to Find Bottleneck
"""

import requests
import time
import json

BASE_URL = "http://localhost:8123"

def test_minimal_recommendations():
    """Test with minimal constraints to find the bottleneck"""
    print("🔍 TESTING MINIMAL RECOMMENDATIONS")
    print("=" * 50)
    
    # Test with very minimal query
    query = {
        "query": """
        query {
            cryptoRecommendations(constraints: { 
                maxSymbols: 1,
                minProbability: 0.1,
                minLiquidityUsd24h: 1000
            }) {
                success
                message
                recommendations {
                    symbol
                    score
                }
            }
        }
        """
    }
    
    print("Testing minimal recommendations query...")
    start = time.time()
    
    try:
        response = requests.post(f"{BASE_URL}/graphql/", json=query, timeout=30)
        duration = time.time() - start
        
        print(f"Duration: {duration:.2f}s")
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Success: {data.get('data', {}).get('cryptoRecommendations', {}).get('success')}")
            print(f"Message: {data.get('data', {}).get('cryptoRecommendations', {}).get('message')}")
            recs = data.get('data', {}).get('cryptoRecommendations', {}).get('recommendations', [])
            print(f"Recommendations count: {len(recs)}")
            if recs:
                print(f"First recommendation: {recs[0]}")
        else:
            print(f"Error: {response.text}")
            
    except Exception as e:
        print(f"Exception: {e}")

if __name__ == "__main__":
    test_minimal_recommendations()
