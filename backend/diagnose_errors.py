#!/usr/bin/env python3
"""
Comprehensive error diagnostic for RichesReach app
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
from django.conf import settings

User = get_user_model()

def check_django_configuration():
    """Check Django configuration for issues"""
    print("🔧 Checking Django Configuration...")
    
    issues = []
    
    # Check database
    try:
        from django.db import connection
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        print("✅ Database connection working")
    except Exception as e:
        issues.append(f"Database error: {e}")
        print(f"❌ Database error: {e}")
    
    # Check settings
    try:
        print(f"✅ DEBUG: {settings.DEBUG}")
        print(f"✅ ALLOWED_HOSTS: {settings.ALLOWED_HOSTS}")
        print(f"✅ SECRET_KEY: {'Set' if settings.SECRET_KEY else 'Missing'}")
    except Exception as e:
        issues.append(f"Settings error: {e}")
        print(f"❌ Settings error: {e}")
    
    # Check installed apps
    try:
        print(f"✅ INSTALLED_APPS: {len(settings.INSTALLED_APPS)} apps")
    except Exception as e:
        issues.append(f"Installed apps error: {e}")
        print(f"❌ Installed apps error: {e}")
    
    return issues

def check_graphql_schema():
    """Check GraphQL schema for issues"""
    print("\n🔍 Checking GraphQL Schema...")
    
    issues = []
    
    try:
        response = requests.post(
            'http://192.168.1.151:8000/graphql/',
            json={'query': '{ __schema { types { name } } }'},
            headers={'Content-Type': 'application/json'},
            timeout=5
        )
        
        if response.status_code == 200:
            data = response.json()
            if 'data' in data and 'errors' not in data:
                types = data['data']['__schema']['types']
                print(f"✅ GraphQL schema working - {len(types)} types available")
                
                # Check for critical types
                type_names = [t['name'] for t in types]
                critical_types = ['Query', 'Mutation', 'UserType', 'StockType']
                missing_types = [t for t in critical_types if t not in type_names]
                
                if missing_types:
                    issues.append(f"Missing critical types: {missing_types}")
                    print(f"❌ Missing critical types: {missing_types}")
                else:
                    print("✅ All critical types present")
            else:
                issues.append("GraphQL schema response has errors")
                print(f"❌ GraphQL schema errors: {data.get('errors', 'Unknown')}")
        else:
            issues.append(f"GraphQL endpoint returned status {response.status_code}")
            print(f"❌ GraphQL endpoint returned status {response.status_code}")
            
    except Exception as e:
        issues.append(f"GraphQL schema check failed: {e}")
        print(f"❌ GraphQL schema check failed: {e}")
    
    return issues

def check_authentication():
    """Check authentication system"""
    print("\n🔐 Checking Authentication System...")
    
    issues = []
    
    try:
        # Test with working credentials
        login_data = {
            'query': '''
                mutation {
                    tokenAuth(
                        email: "test_security@example.com",
                        password: "TestPassword123!"
                    ) {
                        token
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
        
        if response.status_code == 200:
            data = response.json()
            if 'data' in data and data['data']['tokenAuth']['token']:
                print("✅ Authentication working")
                return (data['data']['tokenAuth']['token'], issues)
            else:
                issues.append("Authentication failed")
                print(f"❌ Authentication failed: {data.get('errors', 'Unknown')}")
        else:
            issues.append(f"Authentication request failed with status {response.status_code}")
            print(f"❌ Authentication request failed with status {response.status_code}")
            
    except Exception as e:
        issues.append(f"Authentication check failed: {e}")
        print(f"❌ Authentication check failed: {e}")
    
    return (None, issues)

def check_user_creation():
    """Check user creation functionality"""
    print("\n👤 Checking User Creation...")
    
    issues = []
    
    try:
        # Test user creation
        user_data = {
            'query': '''
                mutation {
                    createUser(
                        username: "testuser999",
                        email: "testuser999@example.com",
                        password: "TestPassword123!",
                        name: "Test User 999"
                    ) {
                        user {
                            id
                            name
                            email
                        }
                        success
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
        print(f"Response: {response.text[:200]}...")
        
        if response.status_code == 200:
            data = response.json()
            if 'data' in data:
                if data['data']['createUser']['success']:
                    print("✅ User creation working")
                else:
                    issues.append("User creation failed")
                    print("❌ User creation failed")
            else:
                issues.append("User creation response has errors")
                print(f"❌ User creation errors: {data.get('errors', 'Unknown')}")
        else:
            issues.append(f"User creation request failed with status {response.status_code}")
            print(f"❌ User creation request failed with status {response.status_code}")
            
    except Exception as e:
        issues.append(f"User creation check failed: {e}")
        print(f"❌ User creation check failed: {e}")
    
    return issues

def check_mobile_app_connectivity():
    """Check mobile app connectivity"""
    print("\n📱 Checking Mobile App Connectivity...")
    
    issues = []
    
    try:
        # Test the exact endpoint the mobile app uses
        response = requests.post(
            'http://192.168.1.151:8000/graphql/',
            json={'query': '{ __schema { queryType { name } } }'},
            headers={'Content-Type': 'application/json'},
            timeout=5
        )
        
        if response.status_code == 200:
            print("✅ Mobile app can connect to backend")
        else:
            issues.append(f"Mobile app connectivity failed - Status: {response.status_code}")
            print(f"❌ Mobile app connectivity failed - Status: {response.status_code}")
            
    except Exception as e:
        issues.append(f"Mobile app connectivity test failed: {e}")
        print(f"❌ Mobile app connectivity test failed: {e}")
    
    return issues

def check_database_integrity():
    """Check database integrity"""
    print("\n🗄️ Checking Database Integrity...")
    
    issues = []
    
    try:
        # Check if users exist
        user_count = User.objects.count()
        print(f"✅ Database has {user_count} users")
        
        # Check for any users with issues
        users_with_issues = User.objects.filter(
            models.Q(email__isnull=True) | models.Q(name__isnull=True)
        )
        
        if users_with_issues.exists():
            issues.append(f"Found {users_with_issues.count()} users with missing data")
            print(f"❌ Found {users_with_issues.count()} users with missing data")
        else:
            print("✅ All users have complete data")
            
    except Exception as e:
        issues.append(f"Database integrity check failed: {e}")
        print(f"❌ Database integrity check failed: {e}")
    
    return issues

def main():
    """Run comprehensive error diagnostic"""
    print("🚀 RichesReach App Error Diagnostic")
    print("=" * 60)
    
    all_issues = []
    
    # Run all checks
    all_issues.extend(check_django_configuration())
    all_issues.extend(check_graphql_schema())
    
    token, auth_issues = check_authentication()
    all_issues.extend(auth_issues)
    
    all_issues.extend(check_user_creation())
    all_issues.extend(check_mobile_app_connectivity())
    all_issues.extend(check_database_integrity())
    
    # Print summary
    print("\n" + "=" * 60)
    print("📊 DIAGNOSTIC SUMMARY")
    print("=" * 60)
    
    if not all_issues:
        print("🎉 No issues found! Your app is working perfectly!")
    else:
        print(f"⚠️ Found {len(all_issues)} issues:")
        for i, issue in enumerate(all_issues, 1):
            print(f"   {i}. {issue}")
        
        print("\n🔧 Recommended Actions:")
        print("   1. Check Django server logs for detailed error messages")
        print("   2. Verify mobile app is using correct GraphQL endpoint")
        print("   3. Check if all required environment variables are set")
        print("   4. Ensure database migrations are up to date")

if __name__ == "__main__":
    main()
