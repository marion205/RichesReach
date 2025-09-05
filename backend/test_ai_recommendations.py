#!/usr/bin/env python
"""
Test the generateAiRecommendations mutation
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

def test_ai_recommendations():
    """Test the complete AI recommendations flow"""
    base_url = "http://192.168.1.151:8000/graphql/"
    
    # Create unique email
    timestamp = int(time.time())
    email = f"airecommendtest{timestamp}@example.com"
    
    print(f"🧪 Testing AI recommendations with email: {email}")
    
    # Step 1: Create user
    print("1️⃣ Creating user...")
    create_user_query = {
        "query": f"""
            mutation {{
                createUser(email: "{email}", password: "TestPassword123!", name: "AI Test User") {{
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
                    incomeBracket: "$75,000 - $100,000"
                    age: 30
                    investmentGoals: ["Retirement Savings", "Wealth Building", "Passive Income"]
                    riskTolerance: "Moderate"
                    investmentHorizon: "10+ years"
                ) {
                    success
                    message
                    incomeProfile {
                        id
                        riskTolerance
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
        print(f"   Risk Tolerance: {profile['riskTolerance']}")
    else:
        print(f"❌ Income profile creation failed: {result}")
        return False
    
    # Step 4: Generate AI recommendations
    print("4️⃣ Generating AI recommendations...")
    generate_recommendations_query = {
        "query": """
            mutation {
                generateAiRecommendations {
                    success
                    message
                    recommendations {
                        id
                        riskProfile
                        portfolioAllocation
                        recommendedStocks {
                            symbol
                            companyName
                            allocation
                            reasoning
                            riskLevel
                            expectedReturn
                        }
                        expectedPortfolioReturn
                        riskAssessment
                    }
                }
            }
        """
    }
    
    response = requests.post(base_url, json=generate_recommendations_query, headers=headers)
    result = response.json()
    
    if result.get('data', {}).get('generateAiRecommendations', {}).get('success'):
        print("✅ AI recommendations generated successfully!")
        recommendations = result['data']['generateAiRecommendations']['recommendations']
        if recommendations:
            rec = recommendations[0]
            print(f"   Recommendation ID: {rec['id']}")
            print(f"   Risk Profile: {rec['riskProfile']}")
            print(f"   Expected Return: {rec['expectedPortfolioReturn']}%")
            print(f"   Number of Stocks: {len(rec['recommendedStocks'])}")
            print("   Top Stock Recommendations:")
            for stock in rec['recommendedStocks'][:3]:  # Show first 3
                print(f"     - {stock['symbol']}: {stock['allocation']}% ({stock['reasoning']})")
        return True
    else:
        print(f"❌ AI recommendations generation failed: {result}")
        return False

if __name__ == "__main__":
    success = test_ai_recommendations()
    if success:
        print("\n🎉 All tests passed! The generateAiRecommendations mutation is working correctly.")
    else:
        print("\n💥 Tests failed. Check the errors above.")
    sys.exit(0 if success else 1)
