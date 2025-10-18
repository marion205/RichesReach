#!/usr/bin/env python3
"""
Test script to verify mobile app connection to local Django server
"""

import requests
import json
import time

# Local server configuration
BASE_URL = "http://192.168.1.236:8000"
GRAPHQL_URL = f"{BASE_URL}/graphql/"

def test_server_health():
    """Test if the local server is running"""
    try:
        response = requests.get(f"{BASE_URL}/healthz", timeout=5)
        if response.status_code == 200:
            print("✅ Local server health check passed")
            return True
        else:
            print(f"❌ Local server health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Local server health check error: {e}")
        return False

def test_graphql_schema():
    """Test if GraphQL schema includes watchlist mutations"""
    try:
        response = requests.post(
            GRAPHQL_URL,
            json={"query": "{ __schema { mutationType { fields { name } } } }"},
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            if "data" in data and "__schema" in data["data"]:
                mutations = data["data"]["__schema"]["mutationType"]["fields"]
                watchlist_mutations = [m["name"] for m in mutations if "Watchlist" in m["name"]]
                
                if "addToWatchlist" in watchlist_mutations and "removeFromWatchlist" in watchlist_mutations:
                    print("✅ GraphQL schema includes watchlist mutations")
                    print(f"   Available watchlist mutations: {watchlist_mutations}")
                    return True
                else:
                    print(f"❌ Watchlist mutations not found. Available: {[m['name'] for m in mutations[:10]]}")
                    return False
            else:
                print(f"❌ GraphQL schema response error: {data}")
                return False
        else:
            print(f"❌ GraphQL schema request failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ GraphQL schema test error: {e}")
        return False

def test_watchlist_mutation():
    """Test watchlist mutation without authentication (should fail gracefully)"""
    try:
        response = requests.post(
            GRAPHQL_URL,
            json={
                "query": "mutation { addToWatchlist(symbol: \"AAPL\", companyName: \"Apple Inc.\", notes: \"Test\") { success message } }"
            },
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            if "data" in data and "addToWatchlist" in data["data"]:
                result = data["data"]["addToWatchlist"]
                if not result["success"] and "logged in" in result["message"].lower():
                    print("✅ Watchlist mutation correctly requires authentication")
                    print(f"   Message: {result['message']}")
                    return True
                else:
                    print(f"❌ Unexpected watchlist mutation result: {result}")
                    return False
            else:
                print(f"❌ Watchlist mutation response error: {data}")
                return False
        else:
            print(f"❌ Watchlist mutation request failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Watchlist mutation test error: {e}")
        return False

def main():
    """Main test function"""
    print("🧪 Testing Mobile App Connection to Local Django Server")
    print("=" * 60)
    
    # Test server health
    if not test_server_health():
        print("\n❌ Local server is not running. Please start it first:")
        print("   cd backend/backend/backend/backend")
        print("   export DJANGO_SETTINGS_MODULE='richesreach.settings_local_db'")
        print("   python3 manage.py runserver 0.0.0.0:8000")
        return
    
    # Test GraphQL schema
    if not test_graphql_schema():
        print("\n❌ GraphQL schema test failed")
        return
    
    # Test watchlist mutation
    if not test_watchlist_mutation():
        print("\n❌ Watchlist mutation test failed")
        return
    
    print("\n🎉 All tests passed! Local server is ready for mobile app testing.")
    print("\n📋 Summary:")
    print("✅ Local Django server running on port 8000")
    print("✅ GraphQL endpoint accessible")
    print("✅ Watchlist mutations available in schema")
    print("✅ Authentication properly enforced")
    print("✅ Ready for mobile app connection")
    
    print("\n📱 Next steps:")
    print("1. Start the mobile app: cd mobile && ./start-local-test.sh")
    print("2. Test watchlist functionality in the app")
    print("3. Verify it connects to local server (not production)")

if __name__ == "__main__":
    main()
