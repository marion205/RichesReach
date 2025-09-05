#!/usr/bin/env python
"""
Test to find the correct user ID
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

def test_user_id():
    """Test to find the correct user ID"""
    base_url = "http://192.168.1.151:8000/graphql/"
    
    # Use existing user with recommendations
    email = "querytest1757018846@example.com"
    
    print(f"🧪 Testing with user: {email}")
    
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
    
    # Get the user's actual ID
    print("1️⃣ Getting user ID...")
    me_query = {
        "query": """
            query {
                me {
                    id
                    name
                    email
                }
            }
        """
    }
    
    response = requests.post(base_url, json=me_query, headers=headers)
    result = response.json()
    
    print("Me query result:")
    print(json.dumps(result, indent=2))
    
    if result.get('data', {}).get('me'):
        user_id = result['data']['me']['id']
        print(f"✅ User ID: {user_id}")
        
        # Test with the correct user ID
        print("2️⃣ Testing with correct user ID...")
        recommendations_query = {
            "query": f"""
                query {{
                    aiPortfolioRecommendations(userId: "{user_id}") {{
                        id
                        riskProfile
                    }}
                }}
            """
        }
        
        response = requests.post(base_url, json=recommendations_query, headers=headers)
        result = response.json()
        
        print("Recommendations query result:")
        print(json.dumps(result, indent=2))
        
        return True
    else:
        print("❌ Could not get user info")
        return False

if __name__ == "__main__":
    test_user_id()
