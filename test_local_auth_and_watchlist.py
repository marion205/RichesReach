#!/usr/bin/env python3
"""
Test script for local authentication and watchlist functionality
"""

import requests
import json

# Local server configuration
BASE_URL = "http://192.168.1.236:8000"
GRAPHQL_URL = f"{BASE_URL}/graphql/"

def create_test_user():
    """Create a test user for authentication testing"""
    print("🔧 Creating test user...")
    # This would normally be done via Django management command
    # For now, we'll assume the user exists from our previous setup
    return True

def test_authentication():
    """Test authentication with the test user"""
    print("🔐 Testing authentication...")
    
    # Try to authenticate with the test user we created earlier
    auth_mutation = """
    mutation TokenAuth($email: String!, $password: String!) {
        tokenAuth(email: $email, password: $password) {
            token
        }
    }
    """
    
    try:
        response = requests.post(
            GRAPHQL_URL,
            json={
                "query": auth_mutation,
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
            
            if "data" in data and "tokenAuth" in data["data"]:
                token_data = data["data"]["tokenAuth"]
                if token_data["token"]:
                    print("✅ Authentication successful")
                    return token_data["token"]
                else:
                    print("❌ Authentication failed - no token returned")
                    return None
            else:
                print(f"❌ Authentication response error: {data}")
                return None
        else:
            print(f"❌ Authentication request failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return None
    except Exception as e:
        print(f"❌ Authentication error: {e}")
        return None

def test_watchlist_with_auth(token):
    """Test watchlist mutations with authentication"""
    if not token:
        print("❌ No token available for watchlist testing")
        return False
    
    print("📝 Testing watchlist mutations with authentication...")
    
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
            print(f"🔍 Add watchlist response: {data}")
            
            if "data" in data and "addToWatchlist" in data["data"]:
                result = data["data"]["addToWatchlist"]
                if result["success"]:
                    print("✅ addToWatchlist mutation successful")
                    print(f"   Message: {result['message']}")
                    
                    # Test removeFromWatchlist mutation
                    remove_mutation = """
                    mutation RemoveFromWatchlist($symbol: String!) {
                        removeFromWatchlist(symbol: $symbol) {
                            success
                            message
                        }
                    }
                    """
                    
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
                        print(f"🔍 Remove watchlist response: {data}")
                        
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
                        return False
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
        print(f"❌ Watchlist mutation error: {e}")
        return False

def main():
    """Main test function"""
    print("🧪 Testing Local Authentication and Watchlist Functionality")
    print("=" * 60)
    
    # Create test user (if needed)
    if not create_test_user():
        return
    
    # Test authentication
    token = test_authentication()
    if not token:
        print("\n❌ Authentication failed. Cannot test watchlist functionality.")
        return
    
    # Test watchlist mutations
    if test_watchlist_with_auth(token):
        print("\n🎉 All tests passed! Local database and watchlist functionality working correctly.")
        print("\n📋 Summary:")
        print("✅ Local PostgreSQL database working")
        print("✅ User authentication working")
        print("✅ Watchlist mutations working")
        print("✅ Ready for mobile app testing")
        
        print("\n📱 Mobile app should now work with:")
        print("   - Local Django server: http://192.168.1.236:8000")
        print("   - Local database: richesreach_local")
        print("   - Test user: test@example.com / testpass123")
    else:
        print("\n❌ Watchlist functionality test failed")

if __name__ == "__main__":
    main()
