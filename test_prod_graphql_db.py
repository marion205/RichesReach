#!/usr/bin/env python3
"""
Test Production GraphQL and Database Connection
This script tests if GraphQL is working properly with the production database.
"""

import requests
import json
import sys
import os

# Production endpoints
ENDPOINTS = [
    "https://api.richesreach.com",
    "http://riches-reach-alb-1199497064.us-east-1.elb.amazonaws.com"
]

def test_graphql_endpoint(base_url):
    """Test GraphQL endpoint and check if it's using database"""
    print(f"\n🔍 Testing GraphQL at: {base_url}/graphql/")
    print("=" * 60)
    
    # Test 1: Basic GraphQL introspection
    print("\n1. Testing GraphQL Introspection...")
    try:
        response = requests.post(
            f"{base_url}/graphql/",
            json={"query": "{ __typename }"},
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Status: {response.status_code}")
            print(f"   Response: {json.dumps(data, indent=2)}")
            
            if data.get("data") and data["data"].get("__typename"):
                print("   ✅ GraphQL is responding correctly")
            else:
                print("   ⚠️  GraphQL responded but returned empty data")
        else:
            print(f"   ❌ Status: {response.status_code}")
            print(f"   Response: {response.text[:200]}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False
    
    # Test 2: Test a query that requires database
    print("\n2. Testing Database Query (me query)...")
    try:
        # This query should return user data if database is connected
        query = """
        query {
            me {
                id
                username
                email
            }
        }
        """
        
        response = requests.post(
            f"{base_url}/graphql/",
            json={"query": query},
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Status: {response.status_code}")
            
            if data.get("errors"):
                error_msg = data["errors"][0].get("message", "Unknown error")
                if "authentication" in error_msg.lower() or "permission" in error_msg.lower():
                    print(f"   ✅ GraphQL is working (authentication required: {error_msg[:50]})")
                    print("   ℹ️  This is expected - query requires authentication")
                else:
                    print(f"   ⚠️  GraphQL error: {error_msg[:100]}")
            elif data.get("data"):
                if data["data"].get("me"):
                    print("   ✅ GraphQL returned user data from database!")
                else:
                    print("   ⚠️  GraphQL returned empty data (may be using fallback)")
            else:
                print(f"   ⚠️  Unexpected response: {json.dumps(data, indent=2)[:200]}")
        else:
            print(f"   ❌ Status: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # Test 3: Test a query that should work without auth
    print("\n3. Testing Public Query (if available)...")
    try:
        # Try to get schema introspection
        query = """
        query IntrospectionQuery {
            __schema {
                queryType {
                    name
                    fields {
                        name
                    }
                }
            }
        }
        """
        
        response = requests.post(
            f"{base_url}/graphql/",
            json={"query": query},
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            if data.get("data") and data["data"].get("__schema"):
                print("   ✅ GraphQL schema introspection working")
                query_type = data["data"]["__schema"].get("queryType", {})
                if query_type.get("fields"):
                    field_count = len(query_type["fields"])
                    print(f"   ✅ Schema has {field_count} query fields")
                    print("   ✅ GraphQL schema is properly configured")
            elif data.get("errors"):
                error_msg = data["errors"][0].get("message", "")
                if "introspection" in error_msg.lower():
                    print("   ℹ️  Introspection disabled (security feature)")
                else:
                    print(f"   ⚠️  Schema error: {error_msg[:100]}")
            else:
                print("   ⚠️  Could not introspect schema")
        else:
            print(f"   ⚠️  Status: {response.status_code}")
    except Exception as e:
        print(f"   ⚠️  Error: {e}")
    
    return True

def test_health_endpoint(base_url):
    """Test health endpoint"""
    print(f"\n🏥 Testing Health Endpoint: {base_url}/health/")
    try:
        response = requests.get(f"{base_url}/health/", timeout=10)
        if response.status_code == 200:
            print(f"   ✅ Health endpoint: {response.status_code}")
            return True
        else:
            print(f"   ⚠️  Health endpoint: {response.status_code}")
            return False
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False

def main():
    print("🧪 Production GraphQL & Database Connection Test")
    print("=" * 60)
    
    results = []
    
    for endpoint in ENDPOINTS:
        print(f"\n{'='*60}")
        print(f"Testing: {endpoint}")
        print('='*60)
        
        # Test health first
        health_ok = test_health_endpoint(endpoint)
        
        # Test GraphQL
        graphql_ok = test_graphql_endpoint(endpoint)
        
        results.append({
            "endpoint": endpoint,
            "health": health_ok,
            "graphql": graphql_ok
        })
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 SUMMARY")
    print("=" * 60)
    
    for result in results:
        print(f"\n{result['endpoint']}:")
        print(f"  Health: {'✅' if result['health'] else '❌'}")
        print(f"  GraphQL: {'✅' if result['graphql'] else '❌'}")
    
    print("\n" + "=" * 60)
    print("💡 INTERPRETATION")
    print("=" * 60)
    print("""
    ✅ GraphQL responding with __typename:
       - GraphQL endpoint is working
       - Server is running and accessible
    
    ✅ Authentication errors on protected queries:
       - GraphQL is properly configured
       - Database connection likely working (queries are being processed)
       - Need JWT token for authenticated queries
    
    ⚠️  Empty data responses:
       - May indicate fallback mode (not using database)
       - Check server logs for "Using Django Graphene schema" message
    
    ❌ Connection errors:
       - Server may be down
       - Network/firewall issues
       - Check AWS ECS service status
    """)

if __name__ == "__main__":
    main()

