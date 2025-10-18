#!/usr/bin/env python3
"""
Simple GraphQL Endpoint Testing for React Native App
Tests key endpoints that the mobile app needs
"""
import requests
import json
import subprocess
import sys
from datetime import datetime

# Configuration
BASE_URL = "http://192.168.1.236:8000"
GRAPHQL_URL = f"{BASE_URL}/graphql/"
TEST_EMAIL = "test@example.com"
TEST_PASSWORD = "testpass123"

def get_clean_token():
    """Get a clean JWT token from Django"""
    try:
        result = subprocess.run([
            "python3", "manage.py", "shell", "-c",
            f"""
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'richesreach.settings_dev_real')
import django
django.setup()
from django.contrib.auth import get_user_model
from graphql_jwt.shortcuts import get_token
U = get_user_model()
user = U.objects.get(email='{TEST_EMAIL}')
token = get_token(user)
print(token)
"""
        ], cwd="/Users/marioncollins/RichesReach/backend/backend/backend/backend", 
        capture_output=True, text=True, timeout=10)
        
        if result.returncode == 0:
            # Extract just the token from the output
            lines = result.stdout.strip().split('\n')
            for line in lines:
                if line.startswith('eyJ'):  # JWT tokens start with eyJ
                    return line.strip()
        return None
    except Exception as e:
        print(f"Error getting token: {e}")
        return None

def make_request(query, variables=None, token=None):
    """Make a GraphQL request"""
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    
    payload = {"query": query}
    if variables:
        payload["variables"] = variables
    
    try:
        response = requests.post(GRAPHQL_URL, json=payload, headers=headers, timeout=10)
        return response.json(), response.status_code
    except Exception as e:
        print(f"Request failed: {e}")
        return None, 0

def test_endpoint(name, query, variables=None, token=None, expected_fields=None):
    """Test a single GraphQL endpoint"""
    print(f"\n🧪 Testing {name}...")
    
    data, status = make_request(query, variables, token)
    
    if data and "data" in data and data["data"]:
        print(f"✅ {name} - SUCCESS")
        
        if expected_fields:
            result = data["data"]
            for field in expected_fields:
                if field in result:
                    print(f"   ✓ {field}: {type(result[field]).__name__}")
                else:
                    print(f"   ✗ Missing field: {field}")
        
        # Show sample data
        if "data" in data:
            result = data["data"]
            if isinstance(result, list) and len(result) > 0:
                print(f"   Sample: {result[0] if len(result) > 0 else 'Empty list'}")
            elif isinstance(result, dict):
                print(f"   Sample: {list(result.keys())}")
        
        return True
    else:
        print(f"❌ {name} - FAILED")
        if data and "errors" in data:
            for error in data["errors"]:
                print(f"   Error: {error.get('message', 'Unknown error')}")
        return False

def main():
    print("🚀 React Native GraphQL Endpoint Testing")
    print("=" * 50)
    
    # Get authentication token
    print("🔐 Getting authentication token...")
    token = get_clean_token()
    if not token:
        print("❌ Failed to get authentication token")
        return False
    
    print(f"✅ Got token (length: {len(token)})")
    
    # Test endpoints
    tests = [
        {
            "name": "User Profile (me)",
            "query": """
            query {
                me {
                    id
                    email
                    username
                    name
                    hasPremiumAccess
                }
            }
            """,
            "token": token,
            "expected_fields": ["id", "email", "username", "name"]
        },
        {
            "name": "Watchlist Query",
            "query": """
            query {
                myWatchlist {
                    id
                    stock {
                        symbol
                        companyName
                    }
                    notes
                    addedAt
                }
            }
            """,
            "token": token,
            "expected_fields": ["myWatchlist"]
        },
        {
            "name": "Add to Watchlist",
            "query": """
            mutation AddToWatchlist($symbol: String!, $companyName: String, $notes: String) {
                addToWatchlist(symbol: $symbol, companyName: $companyName, notes: $notes) {
                    success
                    message
                }
            }
            """,
            "variables": {
                "symbol": "TSLA",
                "companyName": "Tesla, Inc.",
                "notes": "Test from React Native endpoint test"
            },
            "token": token,
            "expected_fields": ["addToWatchlist"]
        },
        {
            "name": "Stocks Query",
            "query": """
            query {
                stocks {
                    symbol
                    companyName
                    currentPrice
                    changePercent
                }
            }
            """,
            "token": token,
            "expected_fields": ["stocks"]
        },
        {
            "name": "Portfolio Query",
            "query": """
            query {
                myPortfolios {
                    totalValue
                    totalReturn
                }
            }
            """,
            "token": token,
            "expected_fields": ["myPortfolios"]
        },
        {
            "name": "AI Recommendations",
            "query": """
            query {
                aiRecommendations {
                    buyRecommendations {
                        symbol
                        confidence
                    }
                    sellRecommendations {
                        symbol
                        confidence
                    }
                }
            }
            """,
            "token": token,
            "expected_fields": ["aiRecommendations"]
        },
        {
            "name": "Market Data",
            "query": """
            query {
                marketData {
                    symbol
                    price
                    change
                    changePercent
                }
            }
            """,
            "token": token,
            "expected_fields": ["marketData"]
        }
    ]
    
    results = []
    for test in tests:
        success = test_endpoint(
            test["name"], 
            test["query"], 
            test.get("variables"), 
            test.get("token"),
            test.get("expected_fields")
        )
        results.append((test["name"], success))
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 TEST SUMMARY")
    print("=" * 50)
    
    passed = sum(1 for _, success in results if success)
    total = len(results)
    
    for name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status}: {name}")
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! React Native app should work with local server.")
    else:
        print("⚠️  Some tests failed. Check the logs above for details.")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
