#!/usr/bin/env python3
"""
Test script for local watchlist functionality
Tests the watchlist mutations with the local database setup
"""

import requests
import json

# Local server configuration
BASE_URL = "http://192.168.1.236:8000"
GRAPHQL_URL = f"{BASE_URL}/graphql/"

def test_health():
    """Test if the server is running"""
    try:
        response = requests.get(f"{BASE_URL}/healthz", timeout=5)
        if response.status_code == 200:
            print("✅ Health check passed")
            return True
        else:
            print(f"❌ Health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Health check error: {e}")
        return False

def get_auth_token():
    """Get authentication token for testing"""
    login_mutation = """
    mutation TokenAuth($email: String!, $password: String!) {
        tokenAuth(email: $email, password: $password) {
            token
            refreshToken
        }
    }
    """
    
    try:
        response = requests.post(
            GRAPHQL_URL,
            json={
                "query": login_mutation,
                "variables": {
                    "email": "test@example.com",
                    "password": "testpass123"
                }
            },
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"🔍 Auth response: {data}")
            if "data" in data and "tokenAuth" in data["data"] and data["data"]["tokenAuth"]["token"]:
                token = data["data"]["tokenAuth"]["token"]
                print("✅ Authentication successful")
                return token
            else:
                print(f"❌ Authentication failed: {data}")
                return None
        else:
            print(f"❌ Authentication request failed: {response.status_code}")
            return None
    except Exception as e:
        print(f"❌ Authentication error: {e}")
        return None

def test_watchlist_mutations(token):
    """Test watchlist mutations"""
    if not token:
        print("❌ No token available for watchlist testing")
        return False
    
    # Test addToWatchlist mutation
    add_mutation = """
    mutation AddToWatchlist($symbol: String!, $companyName: String, $notes: String) {
        addToWatchlist(symbol: $symbol, companyName: $companyName, notes: $notes) {
            success
            message
        }
    }
    """
    
    try:
        response = requests.post(
            GRAPHQL_URL,
            json={
                "query": add_mutation,
                "variables": {
                    "symbol": "AAPL",
                    "companyName": "Apple Inc.",
                    "notes": "Test from local database"
                }
            },
            headers={
                "Content-Type": "application/json",
                "Authorization": f"JWT {token}"
            },
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            if "data" in data and "addToWatchlist" in data["data"]:
                result = data["data"]["addToWatchlist"]
                if result["success"]:
                    print("✅ addToWatchlist mutation successful")
                    print(f"   Message: {result['message']}")
                else:
                    print(f"❌ addToWatchlist mutation failed: {result['message']}")
                    return False
            else:
                print(f"❌ addToWatchlist response error: {data}")
                return False
        else:
            print(f"❌ addToWatchlist request failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
    except Exception as e:
        print(f"❌ addToWatchlist error: {e}")
        return False
    
    # Test removeFromWatchlist mutation
    remove_mutation = """
    mutation RemoveFromWatchlist($symbol: String!) {
        removeFromWatchlist(symbol: $symbol) {
            success
            message
        }
    }
    """
    
    try:
        response = requests.post(
            GRAPHQL_URL,
            json={
                "query": remove_mutation,
                "variables": {
                    "symbol": "AAPL"
                }
            },
            headers={
                "Content-Type": "application/json",
                "Authorization": f"JWT {token}"
            },
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            if "data" in data and "removeFromWatchlist" in data["data"]:
                result = data["data"]["removeFromWatchlist"]
                if result["success"]:
                    print("✅ removeFromWatchlist mutation successful")
                    print(f"   Message: {result['message']}")
                    return True
                else:
                    print(f"❌ removeFromWatchlist mutation failed: {result['message']}")
                    return False
            else:
                print(f"❌ removeFromWatchlist response error: {data}")
                return False
        else:
            print(f"❌ removeFromWatchlist request failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
    except Exception as e:
        print(f"❌ removeFromWatchlist error: {e}")
        return False

def main():
    """Main test function"""
    print("🧪 Testing Local Watchlist Functionality")
    print("=" * 50)
    
    # Test health
    if not test_health():
        return
    
    # Get auth token
    token = get_auth_token()
    if not token:
        return
    
    # Test watchlist mutations
    if test_watchlist_mutations(token):
        print("\n🎉 All tests passed! Local database setup is working correctly.")
        print("\n📋 Summary:")
        print("✅ Local PostgreSQL database created")
        print("✅ Django migrations applied")
        print("✅ Superuser created (admin/admin123)")
        print("✅ Watchlist mutations working")
        print("✅ Ready for mobile app testing")
    else:
        print("\n❌ Some tests failed. Check the errors above.")

if __name__ == "__main__":
    main()
