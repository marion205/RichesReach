#!/usr/bin/env python3
"""
Comprehensive test of all app features
"""
import os
import sys
import django
import requests
import json
from datetime import datetime

# Add the backend directory to Python path
sys.path.append('/Users/marioncollins/RichesReach/backend')

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'richesreach.settings')
django.setup()

from django.contrib.auth import get_user_model
from django.test import Client
from django.conf import settings

User = get_user_model()

def test_server_connectivity():
    """Test if the server is accessible"""
    print("🔍 Testing server connectivity...")
    
    try:
        # Test GraphQL endpoint
        response = requests.post(
            'http://192.168.1.151:8000/graphql/',
            json={'query': '{ __schema { types { name } } }'},
            headers={'Content-Type': 'application/json'},
            timeout=5
        )
        
        if response.status_code == 200:
            print("✅ GraphQL endpoint is accessible")
            return True
        else:
            print(f"❌ GraphQL endpoint returned status {response.status_code}")
            print(f"Response: {response.text[:200]}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to server at http://192.168.1.151:8000")
        return False
    except Exception as e:
        print(f"❌ Server connectivity test failed: {e}")
        return False

def test_user_creation():
    """Test user creation"""
    print("\n👤 Testing user creation...")
    
    try:
        # Create a test user
        user_data = {
            'query': '''
                mutation {
                    createUser(input: {
                        username: "testuser123",
                        email: "testuser123@example.com",
                        password: "TestPassword123!"
                    }) {
                        user {
                            id
                            username
                            email
                        }
                        success
                        errors
                    }
                }
            '''
        }
        
        response = requests.post(
            'http://192.168.1.151:8000/graphql/',
            json=user_data,
            headers={'Content-Type': 'application/json'},
            timeout=10
        )
        
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text[:500]}")
        
        if response.status_code == 200:
            data = response.json()
            if 'data' in data and data['data']['createUser']['success']:
                print("✅ User creation successful")
                return True
            else:
                print("❌ User creation failed")
                print(f"Errors: {data.get('errors', 'No errors field')}")
                return False
        else:
            print(f"❌ User creation request failed with status {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ User creation test failed: {e}")
        return False

def test_authentication():
    """Test authentication"""
    print("\n🔐 Testing authentication...")
    
    try:
        # Test login
        login_data = {
            'query': '''
                mutation {
                    tokenAuth(input: {
                        email: "testuser123@example.com",
                        password: "TestPassword123!"
                    }) {
                        token
                        refreshToken
                        user {
                            id
                            username
                            email
                        }
                    }
                }
            '''
        }
        
        response = requests.post(
            'http://192.168.1.151:8000/graphql/',
            json=login_data,
            headers={'Content-Type': 'application/json'},
            timeout=10
        )
        
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text[:500]}")
        
        if response.status_code == 200:
            data = response.json()
            if 'data' in data and data['data']['tokenAuth']['token']:
                print("✅ Authentication successful")
                return data['data']['tokenAuth']['token']
            else:
                print("❌ Authentication failed")
                print(f"Errors: {data.get('errors', 'No errors field')}")
                return None
        else:
            print(f"❌ Authentication request failed with status {response.status_code}")
            return None
            
    except Exception as e:
        print(f"❌ Authentication test failed: {e}")
        return None

def test_authenticated_queries(token):
    """Test authenticated queries"""
    print("\n🔒 Testing authenticated queries...")
    
    if not token:
        print("❌ No token provided for authenticated queries")
        return False
    
    try:
        # Test me query
        me_data = {
            'query': '''
                query {
                    me {
                        id
                        username
                        email
                        isActive
                        dateJoined
                    }
                }
            '''
        }
        
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {token}'
        }
        
        response = requests.post(
            'http://192.168.1.151:8000/graphql/',
            json=me_data,
            headers=headers,
            timeout=10
        )
        
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text[:500]}")
        
        if response.status_code == 200:
            data = response.json()
            if 'data' in data and data['data']['me']:
                print("✅ Authenticated query successful")
                return True
            else:
                print("❌ Authenticated query failed")
                print(f"Errors: {data.get('errors', 'No errors field')}")
                return False
        else:
            print(f"❌ Authenticated query request failed with status {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Authenticated query test failed: {e}")
        return False

def test_stock_queries():
    """Test stock-related queries"""
    print("\n📈 Testing stock queries...")
    
    try:
        # Test stocks query
        stocks_data = {
            'query': '''
                query {
                    stocks {
                        id
                        symbol
                        name
                        sector
                        currentPrice
                        change
                        changePercent
                    }
                }
            '''
        }
        
        response = requests.post(
            'http://192.168.1.151:8000/graphql/',
            json=stocks_data,
            headers={'Content-Type': 'application/json'},
            timeout=10
        )
        
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text[:500]}")
        
        if response.status_code == 200:
            data = response.json()
            if 'data' in data and data['data']['stocks']:
                print("✅ Stock queries successful")
                return True
            else:
                print("❌ Stock queries failed")
                print(f"Errors: {data.get('errors', 'No errors field')}")
                return False
        else:
            print(f"❌ Stock query request failed with status {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Stock query test failed: {e}")
        return False

def test_watchlist_queries():
    """Test watchlist queries"""
    print("\n👀 Testing watchlist queries...")
    
    try:
        # Test watchlist query
        watchlist_data = {
            'query': '''
                query {
                    myWatchlist {
                        id
                        stock {
                            symbol
                            name
                        }
                        addedAt
                    }
                }
            '''
        }
        
        response = requests.post(
            'http://192.168.1.151:8000/graphql/',
            json=watchlist_data,
            headers={'Content-Type': 'application/json'},
            timeout=10
        )
        
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text[:500]}")
        
        if response.status_code == 200:
            data = response.json()
            if 'data' in data:
                print("✅ Watchlist queries successful")
                return True
            else:
                print("❌ Watchlist queries failed")
                print(f"Errors: {data.get('errors', 'No errors field')}")
                return False
        else:
            print(f"❌ Watchlist query request failed with status {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Watchlist query test failed: {e}")
        return False

def test_news_queries():
    """Test news queries"""
    print("\n📰 Testing news queries...")
    
    try:
        # Test news query
        news_data = {
            'query': '''
                query {
                    news {
                        id
                        title
                        summary
                        url
                        publishedAt
                        source
                    }
                }
            '''
        }
        
        response = requests.post(
            'http://192.168.1.151:8000/graphql/',
            json=news_data,
            headers={'Content-Type': 'application/json'},
            timeout=10
        )
        
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text[:500]}")
        
        if response.status_code == 200:
            data = response.json()
            if 'data' in data:
                print("✅ News queries successful")
                return True
            else:
                print("❌ News queries failed")
                print(f"Errors: {data.get('errors', 'No errors field')}")
                return False
        else:
            print(f"❌ News query request failed with status {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ News query test failed: {e}")
        return False

def test_social_features():
    """Test social features"""
    print("\n👥 Testing social features...")
    
    try:
        # Test posts query
        posts_data = {
            'query': '''
                query {
                    posts {
                        id
                        content
                        author {
                            username
                        }
                        createdAt
                        likesCount
                        commentsCount
                    }
                }
            '''
        }
        
        response = requests.post(
            'http://192.168.1.151:8000/graphql/',
            json=posts_data,
            headers={'Content-Type': 'application/json'},
            timeout=10
        )
        
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text[:500]}")
        
        if response.status_code == 200:
            data = response.json()
            if 'data' in data:
                print("✅ Social features successful")
                return True
            else:
                print("❌ Social features failed")
                print(f"Errors: {data.get('errors', 'No errors field')}")
                return False
        else:
            print(f"❌ Social features request failed with status {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Social features test failed: {e}")
        return False

def test_chat_features():
    """Test chat features"""
    print("\n💬 Testing chat features...")
    
    try:
        # Test chat sessions query
        chat_data = {
            'query': '''
                query {
                    chatSessions {
                        id
                        title
                        createdAt
                        messages {
                            id
                            content
                            role
                            timestamp
                        }
                    }
                }
            '''
        }
        
        response = requests.post(
            'http://192.168.1.151:8000/graphql/',
            json=chat_data,
            headers={'Content-Type': 'application/json'},
            timeout=10
        )
        
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text[:500]}")
        
        if response.status_code == 200:
            data = response.json()
            if 'data' in data:
                print("✅ Chat features successful")
                return True
            else:
                print("❌ Chat features failed")
                print(f"Errors: {data.get('errors', 'No errors field')}")
                return False
        else:
            print(f"❌ Chat features request failed with status {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Chat features test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("🚀 Starting comprehensive feature tests...")
    print("=" * 60)
    
    # Test results
    results = {}
    
    # Test server connectivity
    results['server'] = test_server_connectivity()
    
    if not results['server']:
        print("\n❌ Server is not accessible. Stopping tests.")
        return
    
    # Test user creation
    results['user_creation'] = test_user_creation()
    
    # Test authentication
    token = test_authentication()
    results['authentication'] = token is not None
    
    # Test authenticated queries
    results['authenticated_queries'] = test_authenticated_queries(token)
    
    # Test stock queries
    results['stocks'] = test_stock_queries()
    
    # Test watchlist queries
    results['watchlist'] = test_watchlist_queries()
    
    # Test news queries
    results['news'] = test_news_queries()
    
    # Test social features
    results['social'] = test_social_features()
    
    # Test chat features
    results['chat'] = test_chat_features()
    
    # Print summary
    print("\n" + "=" * 60)
    print("📊 TEST RESULTS SUMMARY")
    print("=" * 60)
    
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name.upper():<20} {status}")
    
    passed = sum(1 for r in results.values() if r)
    total = len(results)
    
    print(f"\nOverall: {passed}/{total} tests passed ({passed/total*100:.1f}%)")
    
    if passed == total:
        print("🎉 All tests passed! Your app is working perfectly!")
    else:
        print("⚠️  Some tests failed. Check the logs above for details.")

if __name__ == "__main__":
    main()
