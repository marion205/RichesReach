#!/usr/bin/env python3
"""
GraphQL Verification Test Suite
Tests the fixes for mock data interception
"""

import requests
import json
import time

def test_graphql_fixes():
    """Test GraphQL fixes to ensure real schema execution"""
    
    GRAPHQL_URL = "http://localhost:8000/graphql/"
    
    print("🧪 GRAPHQL VERIFICATION TEST SUITE")
    print("=" * 50)
    print("Testing fixes for mock data interception...")
    print()
    
    # Wait for server to be ready
    print("⏳ Waiting for server to be ready...")
    time.sleep(5)
    
    # Test 1: Introspection (Should return schema, not mock user)
    print("🔍 Test 1: Schema Introspection")
    print("-" * 30)
    
    introspect_query = {
        "query": "{ __schema { types { name } } }"
    }
    
    try:
        response = requests.post(GRAPHQL_URL, json=introspect_query, headers={'Content-Type': 'application/json'}, timeout=10)
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Response keys: {list(data.keys())}")
            
            if 'data' in data and '__schema' in data['data']:
                types = data['data']['__schema']['types']
                type_names = [t['name'] for t in types[:10]]  # First 10 types
                print(f"✅ Schema types found: {type_names}")
                
                # Check if we're getting real schema (not mock user)
                if 'Query' in type_names and 'Mutation' in type_names:
                    print("✅ Real GraphQL schema loaded!")
                else:
                    print("❌ Schema doesn't look like real GraphQL schema")
            else:
                print("❌ No schema data in response")
                print(f"Response: {data}")
        else:
            print(f"❌ HTTP Error: {response.text}")
            
    except Exception as e:
        print(f"❌ Request failed: {e}")
    
    print()
    
    # Test 2: Simple Query (ping if available)
    print("🔍 Test 2: Simple Query (ping)")
    print("-" * 30)
    
    ping_query = {
        "query": "{ ping }"
    }
    
    try:
        response = requests.post(GRAPHQL_URL, json=ping_query, headers={'Content-Type': 'application/json'}, timeout=10)
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Response: {data}")
            
            if 'data' in data and 'ping' in data['data']:
                print("✅ Ping query executed successfully!")
            elif 'errors' in data:
                print(f"⚠️ GraphQL errors (expected if ping field doesn't exist): {data['errors']}")
            else:
                print("⚠️ Unexpected response format")
        else:
            print(f"❌ HTTP Error: {response.text}")
            
    except Exception as e:
        print(f"❌ Request failed: {e}")
    
    print()
    
    # Test 3: Me Query (Should be auth-aware, not forced mock)
    print("🔍 Test 3: Me Query (Auth-aware)")
    print("-" * 30)
    
    me_query = {
        "query": "{ me { id name email } }"
    }
    
    try:
        response = requests.post(GRAPHQL_URL, json=me_query, headers={'Content-Type': 'application/json'}, timeout=10)
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Response: {data}")
            
            if 'data' in data:
                if data['data']['me'] is None:
                    print("✅ Me query returns null for unauthenticated user (correct!)")
                elif 'errors' in data:
                    print(f"✅ Me query returns auth error (correct!): {data['errors']}")
                else:
                    print("⚠️ Me query returned data - check if this is expected")
            else:
                print("❌ No data in response")
        else:
            print(f"❌ HTTP Error: {response.text}")
            
    except Exception as e:
        print(f"❌ Request failed: {e}")
    
    print()
    
    # Test 4: Stocks Query (Should return real data or proper error)
    print("🔍 Test 4: Stocks Query")
    print("-" * 30)
    
    stocks_query = {
        "query": "{ stocks { symbol name } }"
    }
    
    try:
        response = requests.post(GRAPHQL_URL, json=stocks_query, headers={'Content-Type': 'application/json'}, timeout=10)
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Response keys: {list(data.keys())}")
            
            if 'data' in data and 'stocks' in data['data']:
                stocks = data['data']['stocks']
                if stocks and len(stocks) > 0:
                    print(f"✅ Stocks query returned {len(stocks)} stocks")
                    print(f"Sample stock: {stocks[0]}")
                else:
                    print("✅ Stocks query returned empty list (valid)")
            elif 'errors' in data:
                print(f"✅ Stocks query returned GraphQL errors (valid): {data['errors']}")
            else:
                print("⚠️ Unexpected response format")
        else:
            print(f"❌ HTTP Error: {response.text}")
            
    except Exception as e:
        print(f"❌ Request failed: {e}")
    
    print()
    
    # Test 5: Mutation Test
    print("🔍 Test 5: Mutation Test")
    print("-" * 30)
    
    mutation_query = {
        "query": """
        mutation {
            addToWatchlist(symbol: "AAPL") {
                success
                message
            }
        }
        """
    }
    
    try:
        response = requests.post(GRAPHQL_URL, json=mutation_query, headers={'Content-Type': 'application/json'}, timeout=10)
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Response: {data}")
            
            if 'data' in data and 'addToWatchlist' in data['data']:
                result = data['data']['addToWatchlist']
                print(f"✅ Mutation executed: {result}")
            elif 'errors' in data:
                print(f"✅ Mutation returned errors (expected without auth): {data['errors']}")
            else:
                print("⚠️ Unexpected mutation response")
        else:
            print(f"❌ HTTP Error: {response.text}")
            
    except Exception as e:
        print(f"❌ Request failed: {e}")
    
    print()
    print("=" * 50)
    print("🎯 VERIFICATION COMPLETE")
    print("=" * 50)
    print("Key Success Indicators:")
    print("✅ Schema introspection returns real GraphQL schema")
    print("✅ Queries execute without forced mock data")
    print("✅ Auth-aware responses (null/errors for unauthenticated)")
    print("✅ Mutations execute or return proper errors")
    print("✅ No more global mock data interception")

if __name__ == "__main__":
    test_graphql_fixes()
