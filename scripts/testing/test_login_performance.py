#!/usr/bin/env python3
"""
Test script to check login performance and identify bottlenecks
"""

import requests
import time
import json

# Configuration
BASE_URL = "http://localhost:8000"
GRAPHQL_URL = f"{BASE_URL}/graphql/"

def test_backend_connectivity():
    """Test if backend is accessible"""
    print("🔍 Testing backend connectivity...")
    try:
        response = requests.get(f"{BASE_URL}/", timeout=5)
        print(f"✅ Backend accessible (status: {response.status_code})")
        return True
    except requests.exceptions.RequestException as e:
        print(f"❌ Backend not accessible: {e}")
        return False

def test_graphql_schema():
    """Test GraphQL schema accessibility"""
    print("\n🔍 Testing GraphQL schema...")
    try:
        query = {
            "query": "{ __schema { types { name } } }"
        }
        start_time = time.time()
        response = requests.post(
            GRAPHQL_URL,
            json=query,
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        end_time = time.time()
        
        if response.status_code == 200:
            print(f"✅ GraphQL schema accessible ({end_time - start_time:.2f}s)")
            return True
        else:
            print(f"❌ GraphQL error (status: {response.status_code})")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ GraphQL request failed: {e}")
        return False

def test_login_performance():
    """Test login mutation performance"""
    print("\n🔍 Testing login performance...")
    
    # Test with a dummy user (this will fail but we can measure response time)
    login_mutation = {
        "query": """
            mutation TokenAuth($email: String!, $password: String!) {
                tokenAuth(email: $email, password: $password) {
                    token
                }
            }
        """,
        "variables": {
            "email": "test@example.com",
            "password": "testpassword"
        }
    }
    
    try:
        start_time = time.time()
        response = requests.post(
            GRAPHQL_URL,
            json=login_mutation,
            headers={"Content-Type": "application/json"},
            timeout=15
        )
        end_time = time.time()
        
        response_time = end_time - start_time
        print(f"⏱️ Login request completed in {response_time:.2f}s")
        
        if response.status_code == 200:
            data = response.json()
            if "errors" in data:
                print(f"✅ Login mutation processed (expected auth error)")
                print(f"📊 Response time: {response_time:.2f}s")
                
                # Check if response time is reasonable
                if response_time < 2.0:
                    print("✅ Response time is good (< 2s)")
                elif response_time < 5.0:
                    print("⚠️ Response time is acceptable (2-5s)")
                else:
                    print("❌ Response time is slow (> 5s)")
                    
                return True
            else:
                print("✅ Login successful (unexpected)")
                return True
        else:
            print(f"❌ HTTP error (status: {response.status_code})")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Login request failed: {e}")
        return False

def test_database_performance():
    """Test database query performance"""
    print("\n🔍 Testing database performance...")
    
    # Test a simple query
    test_query = {
        "query": "{ stockDiscussions { id title } }"
    }
    
    try:
        start_time = time.time()
        response = requests.post(
            GRAPHQL_URL,
            json=test_query,
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        end_time = time.time()
        
        response_time = end_time - start_time
        print(f"⏱️ Database query completed in {response_time:.2f}s")
        
        if response.status_code == 200:
            print("✅ Database query successful")
            if response_time < 1.0:
                print("✅ Database performance is good (< 1s)")
            elif response_time < 3.0:
                print("⚠️ Database performance is acceptable (1-3s)")
            else:
                print("❌ Database performance is slow (> 3s)")
            return True
        else:
            print(f"❌ Database query failed (status: {response.status_code})")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Database query failed: {e}")
        return False

def main():
    """Run all performance tests"""
    print("🚀 Starting Login Performance Tests...\n")
    
    # Test backend connectivity
    if not test_backend_connectivity():
        print("\n❌ Backend is not accessible. Please start the Django server.")
        return
    
    # Test GraphQL schema
    if not test_graphql_schema():
        print("\n❌ GraphQL schema not accessible.")
        return
    
    # Test login performance
    test_login_performance()
    
    # Test database performance
    test_database_performance()
    
    print("\n🎉 Performance tests completed!")
    print("\n💡 Recommendations:")
    print("   - If login is slow, check network connectivity")
    print("   - If database queries are slow, check database performance")
    print("   - Consider adding database indexes for frequently queried fields")
    print("   - Check for any blocking operations in the authentication flow")

if __name__ == "__main__":
    main()
