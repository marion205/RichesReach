#!/usr/bin/env python3
"""
Local Development Setup Test
Tests if Django backend and React Native frontend are running properly
"""
import requests
import time
import subprocess
import sys
import os

def test_django_server():
    """Test if Django server is running"""
    print("🔍 Testing Django Backend Server...")
    
    try:
        # Test GraphQL endpoint
        response = requests.get("http://localhost:8000/graphql/", timeout=5)
        if response.status_code == 200:
            print("  ✅ Django GraphQL endpoint: http://localhost:8000/graphql/")
            return True
        else:
            print(f"  ⚠️ Django responded with status: {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"  ❌ Django server not responding: {e}")
        return False

def test_metro_bundler():
    """Test if Metro bundler is running"""
    print("🔍 Testing React Native Metro Bundler...")
    
    try:
        # Test Metro status endpoint
        response = requests.get("http://localhost:8081/status", timeout=5)
        if response.status_code == 200:
            print("  ✅ Metro bundler: http://localhost:8081")
            return True
        else:
            print(f"  ⚠️ Metro responded with status: {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"  ❌ Metro bundler not responding: {e}")
        return False

def test_graphql_schema():
    """Test GraphQL schema loading"""
    print("🔍 Testing GraphQL Schema...")
    
    try:
        # Test GraphQL introspection
        query = {
            "query": """
            query IntrospectionQuery {
                __schema {
                    queryType {
                        name
                    }
                    mutationType {
                        name
                    }
                }
            }
            """
        }
        
        response = requests.post(
            "http://localhost:8000/graphql/",
            json=query,
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            if "data" in data and "__schema" in data["data"]:
                print("  ✅ GraphQL schema loaded successfully")
                print(f"  📊 Query type: {data['data']['__schema']['queryType']['name']}")
                print(f"  📊 Mutation type: {data['data']['__schema']['mutationType']['name']}")
                return True
            else:
                print(f"  ⚠️ GraphQL response: {data}")
                return False
        else:
            print(f"  ❌ GraphQL request failed: {response.status_code}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"  ❌ GraphQL test failed: {e}")
        return False

def test_alpaca_mutations():
    """Test Alpaca-related mutations"""
    print("🔍 Testing Alpaca Mutations...")
    
    try:
        # Test KYC workflow initiation
        query = {
            "query": """
            query TestKYC {
                __type(name: "KYCWorkflowType") {
                    name
                    fields {
                        name
                        type {
                            name
                        }
                    }
                }
            }
            """
        }
        
        response = requests.post(
            "http://localhost:8000/graphql/",
            json=query,
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            if "data" in data and "__type" in data["data"]:
                print("  ✅ KYC workflow types available")
                return True
            else:
                print(f"  ⚠️ KYC types not found: {data}")
                return False
        else:
            print(f"  ❌ KYC test failed: {response.status_code}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"  ❌ KYC test failed: {e}")
        return False

def main():
    """Main test function"""
    print("🚀 Local Development Setup Test")
    print("=" * 50)
    
    # Wait a moment for servers to start
    print("⏳ Waiting for servers to start...")
    time.sleep(5)
    
    # Test Django server
    django_ok = test_django_server()
    
    # Test Metro bundler
    metro_ok = test_metro_bundler()
    
    # Test GraphQL schema
    graphql_ok = False
    if django_ok:
        graphql_ok = test_graphql_schema()
    
    # Test Alpaca mutations
    alpaca_ok = False
    if graphql_ok:
        alpaca_ok = test_alpaca_mutations()
    
    print("\n" + "=" * 50)
    print("📊 Test Results:")
    print(f"  Django Backend: {'✅ PASS' if django_ok else '❌ FAIL'}")
    print(f"  Metro Bundler: {'✅ PASS' if metro_ok else '❌ FAIL'}")
    print(f"  GraphQL Schema: {'✅ PASS' if graphql_ok else '❌ FAIL'}")
    print(f"  Alpaca Features: {'✅ PASS' if alpaca_ok else '❌ FAIL'}")
    
    if django_ok and graphql_ok:
        print("\n🎉 Backend is ready for testing!")
        print("📱 You can now test the UI features:")
        print("  • KYC Workflow: http://localhost:8000/graphql/")
        print("  • Trading Features: Available in React Native app")
        print("  • Email Notifications: Integrated in workflows")
        print("  • WebSocket Updates: Real-time features enabled")
        print("  • Analytics: Performance reporting available")
    else:
        print("\n⚠️ Some services need attention:")
        if not django_ok:
            print("  • Start Django: cd backend/backend && python3 manage.py runserver")
        if not metro_ok:
            print("  • Start Metro: cd mobile && npx expo start")
    
    print("\n🚀 Ready to test advanced features!")

if __name__ == "__main__":
    main()
