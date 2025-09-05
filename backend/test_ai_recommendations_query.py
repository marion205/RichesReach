#!/usr/bin/env python
"""
Test the aiPortfolioRecommendations query
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

def test_ai_recommendations_query():
    """Test the aiPortfolioRecommendations query"""
    base_url = "http://192.168.1.151:8000/graphql/"
    
    # Create unique email
    timestamp = int(time.time())
    email = f"querytest{timestamp}@example.com"
    
    print(f"🧪 Testing AI recommendations query with email: {email}")
    
    # Step 1: Create user
    print("1️⃣ Creating user...")
    create_user_query = {
        "query": f"""
            mutation {{
                createUser(email: "{email}", password: "TestPassword123!", name: "Query Test User") {{
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
                    investmentGoals: ["Retirement Savings", "Wealth Building"]
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
    else:
        print(f"❌ AI recommendations generation failed: {result}")
        return False
    
    # Step 5: Test the aiPortfolioRecommendations query
    print("5️⃣ Testing aiPortfolioRecommendations query...")
    query_recommendations = {
        "query": f"""
            query {{
                aiPortfolioRecommendations(userId: "{user_id}") {{
                    id
                    riskProfile
                    portfolioAllocation
                    recommendedStocks {{
                        symbol
                        companyName
                        allocation
                        reasoning
                        riskLevel
                        expectedReturn
                    }}
                    expectedPortfolioReturn
                    riskAssessment
                    createdAt
                }}
            }}
        """
    }
    
    response = requests.post(base_url, json=query_recommendations, headers=headers)
    result = response.json()
    
    print("Query result:")
    print(json.dumps(result, indent=2))
    
    if result.get('data', {}).get('aiPortfolioRecommendations'):
        recommendations = result['data']['aiPortfolioRecommendations']
        print(f"✅ Query successful! Found {len(recommendations)} recommendations")
        if recommendations:
            rec = recommendations[0]
            print(f"   First recommendation ID: {rec['id']}")
            print(f"   Risk Profile: {rec['riskProfile']}")
            print(f"   Expected Return: {rec['expectedPortfolioReturn']}%")
            print(f"   Number of Stocks: {len(rec['recommendedStocks'])}")
        return True
    else:
        print(f"❌ Query failed or returned no data: {result}")
        return False

if __name__ == "__main__":
    success = test_ai_recommendations_query()
    if success:
        print("\n🎉 AI recommendations query is working correctly!")
    else:
        print("\n💥 Query test failed. Check the errors above.")
    sys.exit(0 if success else 1)
