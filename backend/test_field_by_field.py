#!/usr/bin/env python
"""
Test fields one by one to find the problematic field
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

def test_field_by_field():
    """Test fields one by one to find the problematic field"""
    base_url = "http://192.168.1.151:8000/graphql/"
    
    # Use existing user with recommendations
    email = "querytest1757018846@example.com"
    
    print(f"🧪 Testing fields with existing user: {email}")
    
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
    
    # Test each field individually
    fields_to_test = [
        "id",
        "riskProfile", 
        "portfolioAllocation",
        "expectedPortfolioReturn",
        "riskAssessment",
        "createdAt",
        "recommendedStocks { symbol }",
        "recommendedStocks { symbol companyName }",
        "recommendedStocks { symbol companyName allocation }",
        "recommendedStocks { symbol companyName allocation reasoning }",
        "recommendedStocks { symbol companyName allocation reasoning riskLevel }",
        "recommendedStocks { symbol companyName allocation reasoning riskLevel expectedReturn }"
    ]
    
    for i, field in enumerate(fields_to_test, 1):
        print(f"{i}️⃣ Testing field: {field}")
        
        query = {
            "query": f"""
                query {{
                    aiPortfolioRecommendations(userId: "22") {{
                        {field}
                    }}
                }}
            """
        }
        
        response = requests.post(base_url, json=query, headers=headers)
        result = response.json()
        
        if result.get('errors'):
            print(f"❌ Error with field '{field}': {result['errors']}")
            return False
        else:
            print(f"✅ Field '{field}' works fine")
    
    print("🎉 All fields work individually!")
    return True

if __name__ == "__main__":
    test_field_by_field()
