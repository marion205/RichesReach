#!/usr/bin/env python3
"""
Test login functionality for RichesReach
"""
import os
import sys
import django
import requests
import json

# Add the backend directory to Python path
sys.path.append('/Users/marioncollins/RichesReach/backend')

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'richesreach.settings')
django.setup()

def test_login_mutation():
    """Test login via GraphQL mutation"""
    print("🔐 Testing Login Mutation...")
    
    try:
        # Test login mutation
        mutation = """
        mutation {
            tokenAuth(email: "test@example.com", password: "testpassword") {
                token
                refreshToken
                user {
                    id
                    email
                    name
                }
            }
        }
        """
        
        response = requests.post(
            'http://localhost:8000/graphql/',
            json={'query': mutation},
            headers={'Content-Type': 'application/json'},
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            if 'data' in data and 'tokenAuth' in data['data']:
                if data['data']['tokenAuth']:
                    print("✅ Login mutation is working")
                    print(f"   Token: {data['data']['tokenAuth']['token'][:20]}...")
                    return True
                else:
                    print("❌ Login failed - invalid credentials")
                    return False
            else:
                print(f"❌ Login mutation returned errors: {data.get('errors', [])}")
                return False
        else:
            print(f"❌ Login mutation returned status {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ Login mutation not accessible: {e}")
        return False

def test_create_user():
    """Test creating a user via GraphQL mutation"""
    print("\n👤 Testing Create User Mutation...")
    
    try:
        # Test create user mutation
        mutation = """
        mutation {
            createUser(email: "test@example.com", password: "testpassword", name: "Test User") {
                success
                message
                user {
                    id
                    email
                    name
                }
            }
        }
        """
        
        response = requests.post(
            'http://localhost:8000/graphql/',
            json={'query': mutation},
            headers={'Content-Type': 'application/json'},
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            if 'data' in data and 'createUser' in data['data']:
                if data['data']['createUser']['success']:
                    print("✅ Create user mutation is working")
                    print(f"   User: {data['data']['createUser']['user']['email']}")
                    return True
                else:
                    print(f"❌ Create user failed: {data['data']['createUser']['message']}")
                    return False
            else:
                print(f"❌ Create user mutation returned errors: {data.get('errors', [])}")
                return False
        else:
            print(f"❌ Create user mutation returned status {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ Create user mutation not accessible: {e}")
        return False

def test_backend_health():
    """Test if backend is running"""
    print("🌐 Testing Backend Health...")
    
    try:
        response = requests.get('http://localhost:8000/health', timeout=5)
        if response.status_code == 200:
            print("✅ Backend server is running")
            return True
        else:
            print(f"❌ Backend server returned status {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ Backend server not accessible: {e}")
        return False

def main():
    """Run all login tests"""
    print("🚀 RichesReach Login Test Suite")
    print("=" * 50)
    
    tests = [
        test_backend_health,
        test_create_user,
        test_login_mutation,
    ]
    
    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"❌ Test {test.__name__} crashed: {e}")
            results.append(False)
    
    print("\n" + "=" * 50)
    print("📋 Test Results Summary")
    print("=" * 50)
    
    passed = sum(results)
    total = len(results)
    
    print(f"✅ Passed: {passed}/{total}")
    print(f"❌ Failed: {total - passed}/{total}")
    
    if passed == total:
        print("\n🎉 All login tests passed!")
    else:
        print("\n⚠️  Some login tests failed. Check the output above for details.")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
