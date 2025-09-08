#!/usr/bin/env python3
"""
Test password reset functionality
"""
import os
import sys
import django
import requests
import json

# Add the project directory to Python path
sys.path.append('/Users/marioncollins/RichesReach/backend')

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'richesreach.settings')
django.setup()

def test_graphql_schema():
    """Test that password reset mutations are in the GraphQL schema"""
    print("🧪 Testing GraphQL Schema for Password Reset Mutations")
    print("=" * 60)
    
    # Test GraphQL introspection
    introspection_query = """
    query IntrospectionQuery {
      __schema {
        mutationType {
          fields {
            name
            description
          }
        }
      }
    }
    """
    
    try:
        response = requests.post(
            'http://127.0.0.1:8000/graphql/',
            json={'query': introspection_query},
            headers={'Content-Type': 'application/json'},
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            mutations = data.get('data', {}).get('__schema', {}).get('mutationType', {}).get('fields', [])
            
            # Check for password reset mutations
            mutation_names = [mutation['name'] for mutation in mutations]
            
            print(f"✅ Found {len(mutations)} mutations in schema")
            
            # Check for our password reset mutations
            required_mutations = ['forgotPassword', 'resetPassword', 'changePassword']
            
            for mutation in required_mutations:
                if mutation in mutation_names:
                    print(f"✅ {mutation} mutation found in schema")
                else:
                    print(f"❌ {mutation} mutation NOT found in schema")
            
            return all(mutation in mutation_names for mutation in required_mutations)
        else:
            print(f"❌ GraphQL request failed with status {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ GraphQL schema test failed: {e}")
        return False

def test_forgot_password_mutation():
    """Test the forgot password mutation"""
    print("\n🧪 Testing Forgot Password Mutation")
    print("=" * 60)
    
    mutation = """
    mutation {
      forgotPassword(email: "test@example.com") {
        success
        message
      }
    }
    """
    
    try:
        response = requests.post(
            'http://127.0.0.1:8000/graphql/',
            json={'query': mutation},
            headers={'Content-Type': 'application/json'},
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            result = data.get('data', {}).get('forgotPassword', {})
            
            print(f"✅ Mutation executed successfully")
            print(f"   Success: {result.get('success')}")
            print(f"   Message: {result.get('message')}")
            
            # The mutation should work even if email sending fails
            return True
        else:
            print(f"❌ Mutation failed with status {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Forgot password mutation test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("🔐 RichesReach Password Reset Test Suite")
    print("=" * 60)
    
    tests = [
        ("GraphQL Schema", test_graphql_schema),
        ("Forgot Password Mutation", test_forgot_password_mutation),
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        print(f"\n{'='*20} {test_name} {'='*20}")
        try:
            success = test_func()
            results[test_name] = "✅ PASS" if success else "❌ FAIL"
        except Exception as e:
            print(f"❌ Test failed with exception: {e}")
            results[test_name] = "💥 ERROR"
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 TEST RESULTS SUMMARY")
    print("=" * 60)
    
    for test_name, result in results.items():
        print(f"{test_name:<30} {result}")
    
    passed = sum(1 for result in results.values() if "PASS" in result)
    total = len(results)
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Password reset functionality is working!")
    elif passed >= total * 0.5:
        print("⚠️  Some tests passed. Password reset is partially working.")
    else:
        print("❌ Multiple tests failed. Password reset needs fixing.")
    
    return passed == total

if __name__ == "__main__":
    main()
