#!/usr/bin/env python3
"""
Test specific GraphQL queries to understand the issue
"""

import requests
import json

def test_specific_queries():
    """Test specific GraphQL queries to understand what's happening"""
    
    # Test 1: Simple introspection query
    query1 = """
    query {
        __schema {
            queryType {
                name
            }
        }
    }
    """
    
    # Test 2: Ping query (should work)
    query2 = """
    query {
        ping
    }
    """
    
    # Test 3: Me query (should return user data)
    query3 = """
    query {
        me {
            id
            name
            email
        }
    }
    """
    
    # Test 4: Stocks query (should return stocks)
    query4 = """
    query {
        stocks {
            symbol
            name
        }
    }
    """
    
    queries = [
        ("Introspection", query1),
        ("Ping", query2),
        ("Me", query3),
        ("Stocks", query4)
    ]
    
    for name, query in queries:
        print(f"\n🔍 Testing {name} Query:")
        print("-" * 40)
        
        response = requests.post(
            "http://localhost:8000/graphql/",
            json={"query": query},
            headers={"Content-Type": "application/json"}
        )
        
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            try:
                data = response.json()
                print(f"Response: {json.dumps(data, indent=2)}")
                
                # Check if there are errors
                if "errors" in data:
                    print(f"❌ GraphQL Errors: {data['errors']}")
                else:
                    print("✅ No GraphQL errors")
                    
            except Exception as e:
                print(f"❌ JSON Parse Error: {e}")
        else:
            print(f"❌ HTTP Error: {response.text}")

if __name__ == "__main__":
    print("🧪 TESTING SPECIFIC GRAPHQL QUERIES")
    print("=" * 50)
    test_specific_queries()
