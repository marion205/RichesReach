#!/usr/bin/env python
"""
Test a simple query to isolate the issue
"""
import os
import sys
import django
import requests
import json
import time

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'richesreach.settings')
django.setup()

def test_simple_query():
    """Test a simple query to isolate the issue"""
    base_url = "http://192.168.1.151:8000/graphql/"
    
    # Create unique email
    timestamp = int(time.time())
    email = f"simpletest{timestamp}@example.com"
    
    print(f"🧪 Testing simple query with email: {email}")
    
    # Step 1: Create user and get token
    create_user_query = {
        "query": f"""
            mutation {{
                createUser(email: "{email}", password: "TestPassword123!", name: "Simple Test User") {{
                    user {{
                        id
                        name
                        email
                    }}
                    success
                    message
                }}
            }}
        """
    }
    
    response = requests.post(base_url, json=create_user_query)
    result = response.json()
    
    if not result.get('data', {}).get('createUser', {}).get('success'):
        print(f"❌ User creation failed: {result}")
        return False
    
    user_id = result['data']['createUser']['user']['id']
    print(f"✅ User created with ID: {user_id}")
    
    # Get token
    auth_query = {
        "query": f"""
            mutation {{
                tokenAuth(email: "{email}", password: "TestPassword123!") {{
                    token
                }}
            }}
        """
    }
    
    response = requests.post(base_url, json=auth_query)
    result = response.json()
    
    if not result.get('data', {}).get('tokenAuth', {}).get('token'):
        print(f"❌ Authentication failed: {result}")
        return False
    
    token = result['data']['tokenAuth']['token']
    headers = {
        "Authorization": f"JWT {token}",
        "Content-Type": "application/json"
    }
    
    # Test 1: Simple query without userId parameter
    print("1️⃣ Testing simple query without userId...")
    simple_query = {
        "query": """
            query {
                aiPortfolioRecommendations(userId: "22") {
                    id
                    riskProfile
                }
            }
        """
    }
    
    response = requests.post(base_url, json=simple_query, headers=headers)
    result = response.json()
    
    print("Simple query result:")
    print(json.dumps(result, indent=2))
    
    # Test 2: Query with just basic fields
    print("2️⃣ Testing query with basic fields...")
    basic_query = {
        "query": f"""
            query {{
                aiPortfolioRecommendations(userId: "{user_id}") {{
                    id
                    riskProfile
                    riskAssessment
                }}
            }}
        """
    }
    
    response = requests.post(base_url, json=basic_query, headers=headers)
    result = response.json()
    
    print("Basic query result:")
    print(json.dumps(result, indent=2))
    
    return True

if __name__ == "__main__":
    test_simple_query()
