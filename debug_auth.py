#!/usr/bin/env python3
"""
Debug authentication issues
"""

import os
import sys
import django

# Add the Django project to the path
sys.path.append('backend/backend/backend/backend')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'richesreach.settings_dev')

# Setup Django
django.setup()

from django.contrib.auth import get_user_model, authenticate
from django.contrib.auth.hashers import check_password
import requests
import json

User = get_user_model()

def debug_user():
    """Debug user authentication"""
    try:
        user = User.objects.get(email="test@example.com")
        print(f"User found: {user.email} (ID: {user.id})")
        print(f"Username: {user.username}")
        print(f"First name: {user.first_name}")
        print(f"Last name: {user.last_name}")
        print(f"Is active: {user.is_active}")
        print(f"Is staff: {user.is_staff}")
        print(f"Is superuser: {user.is_superuser}")
        print(f"Date joined: {user.date_joined}")
        
        # Test password
        if user.check_password("testpass123"):
            print("✅ Password check successful")
        else:
            print("❌ Password check failed")
            
        # Test Django authenticate
        auth_user = authenticate(email="test@example.com", password="testpass123")
        if auth_user:
            print("✅ Django authenticate successful")
        else:
            print("❌ Django authenticate failed")
            
        return user
        
    except User.DoesNotExist:
        print("❌ User not found")
        return None

def test_graphql_auth():
    """Test GraphQL authentication with different approaches"""
    print("\n🔍 Testing GraphQL authentication...")
    
    # Test 1: Simple tokenAuth
    query1 = {
        "query": "mutation { tokenAuth(email: \"test@example.com\", password: \"testpass123\") { token user { id email } } }"
    }
    
    print("Test 1: Simple tokenAuth")
    response = requests.post(
        "http://192.168.1.236:8000/graphql/",
        json=query1,
        headers={"Content-Type": "application/json"},
        timeout=10
    )
    
    print(f"Status: {response.status_code}")
    print(f"Response: {response.text}")
    
    # Test 2: With variables
    query2 = {
        "query": """
        mutation TokenAuth($email: String!, $password: String!) {
            tokenAuth(email: $email, password: $password) {
                token
                user {
                    id
                    email
                    username
                }
            }
        }
        """,
        "variables": {
            "email": "test@example.com",
            "password": "testpass123"
        }
    }
    
    print("\nTest 2: tokenAuth with variables")
    response = requests.post(
        "http://192.168.1.236:8000/graphql/",
        json=query2,
        headers={"Content-Type": "application/json"},
        timeout=10
    )
    
    print(f"Status: {response.status_code}")
    print(f"Response: {response.text}")
    
    # Test 3: Check if there are any errors in the response
    if response.status_code == 200:
        try:
            data = json.loads(response.text)
            if "errors" in data:
                print(f"GraphQL errors: {data['errors']}")
        except:
            pass

def test_direct_auth():
    """Test direct authentication without GraphQL"""
    print("\n🔍 Testing direct authentication...")
    
    # Test Django's authenticate function directly
    from django.contrib.auth import authenticate
    
    user = authenticate(email="test@example.com", password="testpass123")
    if user:
        print(f"✅ Direct authentication successful: {user.email}")
        
        # Test JWT token generation
        try:
            from graphql_jwt.utils import jwt_encode
            from graphql_jwt.settings import jwt_settings
            
            payload = jwt_settings.JWT_PAYLOAD_HANDLER(user)
            token = jwt_settings.JWT_ENCODE_HANDLER(payload)
            
            print(f"✅ JWT token generated: {token[:20]}...")
            return token
            
        except Exception as e:
            print(f"❌ JWT token generation failed: {e}")
            return None
    else:
        print("❌ Direct authentication failed")
        return None

def main():
    print("🔧 Debugging Authentication Issues")
    print("=" * 50)
    
    # Debug user
    user = debug_user()
    
    if user:
        # Test GraphQL auth
        test_graphql_auth()
        
        # Test direct auth
        token = test_direct_auth()
        
        if token:
            print(f"\n🎉 Authentication working! Token: {token[:20]}...")
        else:
            print("\n❌ Authentication issues found")

if __name__ == "__main__":
    main()
