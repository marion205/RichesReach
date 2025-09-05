#!/usr/bin/env python
"""
Test the full mobile app query
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

def test_full_mobile_query():
    """Test the full mobile app query"""
    base_url = "http://192.168.1.151:8000/graphql/"
    
    # Use existing user with recommendations
    email = "querytest1757018846@example.com"
    
    print(f"🧪 Testing full mobile query with user: {email}")
    
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
    
    # Test the full mobile app query
    print("🧪 Testing full mobile app query...")
    full_query = {
        "query": """
            query GetAIRecommendations($userId: ID!) {
                aiPortfolioRecommendations(userId: $userId) {
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
                    createdAt
                }
            }
        """,
        "variables": {
            "userId": "22"
        }
    }
    
    response = requests.post(base_url, json=full_query, headers=headers)
    result = response.json()
    
    print("Full query result:")
    print(json.dumps(result, indent=2))
    
    if result.get('data', {}).get('aiPortfolioRecommendations'):
        recommendations = result['data']['aiPortfolioRecommendations']
        print(f"✅ Full query successful! Found {len(recommendations)} recommendations")
        if recommendations:
            rec = recommendations[0]
            print(f"   Recommendation ID: {rec['id']}")
            print(f"   Risk Profile: {rec['riskProfile']}")
            print(f"   Expected Return: {rec['expectedPortfolioReturn']}%")
            print(f"   Number of Stocks: {len(rec['recommendedStocks'])}")
            print("   Stock Recommendations:")
            for stock in rec['recommendedStocks']:
                print(f"     - {stock['symbol']}: {stock['allocation']}% ({stock['reasoning']})")
        return True
    else:
        print(f"❌ Full query failed: {result}")
        return False

if __name__ == "__main__":
    success = test_full_mobile_query()
    if success:
        print("\n🎉 Full mobile app query is working correctly!")
    else:
        print("\n💥 Full query test failed. Check the errors above.")
    sys.exit(0 if success else 1)
