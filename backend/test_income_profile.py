#!/usr/bin/env python
"""
Test the createIncomeProfile mutation
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

def test_income_profile():
    """Test the complete income profile creation flow"""
    base_url = "http://192.168.1.151:8000/graphql/"
    
    # Create unique email
    timestamp = int(time.time())
    email = f"profiletest{timestamp}@example.com"
    
    print(f"🧪 Testing with email: {email}")
    
    # Step 1: Create user
    print("1️⃣ Creating user...")
    create_user_query = {
        "query": f"""
            mutation {{
                createUser(email: "{email}", password: "TestPassword123!", name: "Profile Test User") {{
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
    
    if result.get('data', {}).get('createUser', {}).get('success'):
        print("✅ User created successfully!")
        user_id = result['data']['createUser']['user']['id']
        print(f"   User ID: {user_id}")
    else:
        print(f"❌ User creation failed: {result}")
        return False
    
    # Step 2: Get authentication token
    print("2️⃣ Getting authentication token...")
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
    
    if result.get('data', {}).get('tokenAuth', {}).get('token'):
        token = result['data']['tokenAuth']['token']
        print("✅ Authentication successful!")
        print(f"   Token: {token[:20]}...")
    else:
        print(f"❌ Authentication failed: {result}")
        return False
    
    # Step 3: Create income profile
    print("3️⃣ Creating income profile...")
    create_profile_query = {
        "query": """
            mutation {
                createIncomeProfile(
                    incomeBracket: "$50,000 - $75,000"
                    age: 25
                    investmentGoals: ["Retirement Savings", "Wealth Building"]
                    riskTolerance: "Moderate"
                    investmentHorizon: "5-10 years"
                ) {
                    success
                    message
                    incomeProfile {
                        id
                        incomeBracket
                        age
                        investmentGoals
                        riskTolerance
                        investmentHorizon
                    }
                }
            }
        """
    }
    
    headers = {
        "Authorization": f"JWT {token}",
        "Content-Type": "application/json"
    }
    
    response = requests.post(base_url, json=create_profile_query, headers=headers)
    result = response.json()
    
    if result.get('data', {}).get('createIncomeProfile', {}).get('success'):
        print("✅ Income profile created successfully!")
        profile = result['data']['createIncomeProfile']['incomeProfile']
        print(f"   Profile ID: {profile['id']}")
        print(f"   Income Bracket: {profile['incomeBracket']}")
        print(f"   Age: {profile['age']}")
        print(f"   Risk Tolerance: {profile['riskTolerance']}")
        print(f"   Investment Goals: {profile['investmentGoals']}")
        return True
    else:
        print(f"❌ Income profile creation failed: {result}")
        return False

if __name__ == "__main__":
    success = test_income_profile()
    if success:
        print("\n🎉 All tests passed! The createIncomeProfile mutation is working correctly.")
    else:
        print("\n💥 Tests failed. Check the errors above.")
    sys.exit(0 if success else 1)
