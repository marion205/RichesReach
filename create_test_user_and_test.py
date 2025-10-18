#!/usr/bin/env python3
"""
Create test user and run basic GraphQL tests
"""

import os
import sys
import django

# Add the Django project to the path
sys.path.append('backend/backend/backend/backend')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'richesreach.settings_dev')

# Setup Django
django.setup()

from django.contrib.auth import get_user_model
from django.db import connection
import requests
import json

User = get_user_model()

def create_test_user():
    """Create a test user if it doesn't exist"""
    try:
        user = User.objects.get(email="test@example.com")
        print(f"✅ Test user already exists: {user.email} (ID: {user.id})")
        return user
    except User.DoesNotExist:
        print("Creating test user...")
        user = User.objects.create_user(
            email="test@example.com",
            username="test",
            password="testpass123",
            first_name="Test",
            last_name="User"
        )
        print(f"✅ Created test user: {user.email} (ID: {user.id})")
        return user

def test_graphql_endpoint():
    """Test basic GraphQL functionality"""
    base_url = "http://192.168.1.236:8000"
    
    # Test 1: Health check
    print("\n🔍 Testing health endpoint...")
    try:
        response = requests.get(f"{base_url}/health", timeout=5)
        if response.status_code == 200:
            print("✅ Health endpoint working")
        else:
            print(f"❌ Health endpoint failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Health endpoint error: {e}")
        return False
    
    # Test 2: GraphQL introspection
    print("\n🔍 Testing GraphQL introspection...")
    introspection_query = {
        "query": "{ __schema { queryType { name fields { name } } } }"
    }
    
    try:
        response = requests.post(
            f"{base_url}/graphql/",
            json=introspection_query,
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            if "data" in data and "__schema" in data["data"]:
                query_count = len(data["data"]["__schema"]["queryType"]["fields"])
                print(f"✅ GraphQL introspection working - {query_count} queries available")
            else:
                print(f"❌ GraphQL introspection failed: {data}")
                return False
        else:
            print(f"❌ GraphQL introspection failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ GraphQL introspection error: {e}")
        return False
    
    # Test 3: Login mutation
    print("\n🔍 Testing login mutation...")
    login_query = {
        "query": """
        mutation TokenAuth($email: String!, $password: String!) {
            tokenAuth(email: $email, password: $password) {
                token
                user {
                    id
                    email
                    username
                }
            }
        }
        """,
        "variables": {
            "email": "test@example.com",
            "password": "testpass123"
        }
    }
    
    try:
        response = requests.post(
            f"{base_url}/graphql/",
            json=login_query,
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            if "data" in data and data["data"]["tokenAuth"]["token"]:
                token = data["data"]["tokenAuth"]["token"]
                user_data = data["data"]["tokenAuth"]["user"]
                print(f"✅ Login successful - Token: {token[:20]}...")
                print(f"   User: {user_data['email']} (ID: {user_data['id']})")
                return token
            else:
                print(f"❌ Login failed: {data}")
                return False
        else:
            print(f"❌ Login failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Login error: {e}")
        return False

def test_authenticated_queries(token):
    """Test authenticated GraphQL queries"""
    base_url = "http://192.168.1.236:8000"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}"
    }
    
    # Test queries
    queries = [
        {
            "name": "GetMe",
            "query": """
            query GetMe {
                me {
                    id
                    email
                    username
                    firstName
                    lastName
                }
            }
            """
        },
        {
            "name": "CryptoPortfolio",
            "query": """
            query GetCryptoPortfolio {
                cryptoPortfolio {
                    totalValue
                    totalReturn
                    totalReturnPercent
                    positions {
                        id
                        symbol
                        quantity
                        currentPrice
                        marketValue
                    }
                }
            }
            """
        },
        {
            "name": "TopYields",
            "query": """
            query GetTopYields($limit: Int) {
                topYields(limit: $limit) {
                    protocol
                    chain
                    apy
                    tvl
                }
            }
            """,
            "variables": {"limit": 5}
        }
    ]
    
    print(f"\n🔍 Testing authenticated queries with token: {token[:20]}...")
    
    for query_test in queries:
        print(f"\n  Testing {query_test['name']}...")
        
        payload = {
            "query": query_test["query"]
        }
        
        if "variables" in query_test:
            payload["variables"] = query_test["variables"]
        
        try:
            response = requests.post(
                f"{base_url}/graphql/",
                json=payload,
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                if "errors" in data:
                    print(f"    ❌ {query_test['name']} failed: {data['errors']}")
                else:
                    result_data = data.get("data", {})
                    print(f"    ✅ {query_test['name']} successful")
                    print(f"       Data keys: {list(result_data.keys())}")
            else:
                print(f"    ❌ {query_test['name']} failed: {response.status_code}")
        except Exception as e:
            print(f"    ❌ {query_test['name']} error: {e}")

def main():
    print("🚀 GraphQL Testing with User Creation")
    print("=" * 50)
    
    # Create test user
    user = create_test_user()
    
    # Test GraphQL endpoints
    token = test_graphql_endpoint()
    
    if token:
        # Test authenticated queries
        test_authenticated_queries(token)
        print("\n🎉 Testing completed successfully!")
    else:
        print("\n❌ Testing failed - could not authenticate")

if __name__ == "__main__":
    main()
