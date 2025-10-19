#!/usr/bin/env python3
"""
Debug script to test API keys and stock quote fetching
"""
import os
import requests
import json

# Set the API keys
FINNHUB_API_KEY = "d2rnitpr01qv11lfegugd2rnitpr01qv11lfegv0"
POLYGON_API_KEY = "uuKmy9dPAjaSVXVEtCumQPga1dqEPDS2"
ALPHA_VANTAGE_API_KEY = "OHYSFF1AE446O7CR"

def test_finnhub():
    """Test Finnhub API"""
    print("Testing Finnhub API...")
    try:
        response = requests.get(
            "https://finnhub.io/api/v1/quote",
            params={
                "symbol": "AAPL",
                "token": FINNHUB_API_KEY
            },
            timeout=10
        )
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"Data: {json.dumps(data, indent=2)}")
            return data
        else:
            print(f"Error: {response.text}")
            return None
    except Exception as e:
        print(f"Exception: {e}")
        return None

def test_polygon():
    """Test Polygon API"""
    print("\nTesting Polygon API...")
    try:
        response = requests.get(
            f"https://api.polygon.io/v2/aggs/ticker/AAPL/prev?apikey={POLYGON_API_KEY}",
            timeout=10
        )
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"Data: {json.dumps(data, indent=2)}")
            return data
        else:
            print(f"Error: {response.text}")
            return None
    except Exception as e:
        print(f"Exception: {e}")
        return None

if __name__ == "__main__":
    print("=== API Keys Debug Test ===")
    print(f"FINNHUB_API_KEY: {FINNHUB_API_KEY[:10]}...")
    print(f"POLYGON_API_KEY: {POLYGON_API_KEY[:10]}...")
    print(f"ALPHA_VANTAGE_API_KEY: {ALPHA_VANTAGE_API_KEY[:10]}...")
    
    finnhub_data = test_finnhub()
    polygon_data = test_polygon()
    
    print("\n=== Summary ===")
    print(f"Finnhub working: {finnhub_data is not None}")
    print(f"Polygon working: {polygon_data is not None}")
