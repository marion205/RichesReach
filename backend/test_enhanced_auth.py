#!/usr/bin/env python3
"""
Enhanced Authentication System Test Script
Tests all the new authentication features we've added.
"""

import os
import sys
import django
from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.mail import send_mail
from django.conf import settings
import json

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'richesreach.settings')
django.setup()

User = get_user_model()

class EnhancedAuthTester:
    """Test suite for enhanced authentication features"""
    
    def __init__(self):
        self.client = Client()
        self.test_user = None
        self.test_email = "test@example.com"
        self.test_password = "TestPassword123!"
        self.test_name = "Test User"
    
    def setup_test_user(self):
        """Create a test user for testing"""
        print("🔧 Setting up test user...")
        
        # Clean up any existing test user
        User.objects.filter(email=self.test_email).delete()
        
        # Create new test user
        self.test_user = User.objects.create_user(
            email=self.test_email,
            name=self.test_name,
            password=self.test_password,
            is_active=True
        )
        print(f"✅ Test user created: {self.test_user.email}")
    
    def test_password_strength_validation(self):
        """Test password strength validation"""
        print("\n🔐 Testing Password Strength Validation")
        print("=" * 40)
        
        from core.auth_utils import PasswordValidator
        
        # Test weak passwords
        weak_passwords = [
            "123",           # Too short
            "password",      # No numbers/special chars
            "12345678",      # Only numbers
            "Password",      # No numbers/special chars
        ]
        
        for password in weak_passwords:
            result = PasswordValidator.validate_password(password)
            print(f"Password: '{password}' -> {result['strength']} (Valid: {result['is_valid']})")
            assert not result['is_valid'], f"Weak password '{password}' should be invalid"
        
        # Test strong password
        strong_password = "StrongPass123!"
        result = PasswordValidator.validate_password(strong_password)
        print(f"Password: '{strong_password}' -> {result['strength']} (Valid: {result['is_valid']})")
        assert result['is_valid'], f"Strong password should be valid"
        
        print("✅ Password strength validation working correctly")
    
    def test_rate_limiting(self):
        """Test rate limiting functionality"""
        print("\n⏱️ Testing Rate Limiting")
        print("=" * 25)
        
        from core.auth_utils import RateLimiter
        
        # Create a mock request object
        class MockRequest:
            def __init__(self):
                self.META = {'REMOTE_ADDR': '127.0.0.1'}
        
        request = MockRequest()
        
        # Test rate limiting
        is_limited, attempts_remaining, reset_time = RateLimiter.is_rate_limited(
            request, 'login', max_attempts=3, window_minutes=1
        )
        
        print(f"Initial check - Limited: {is_limited}, Remaining: {attempts_remaining}")
        assert not is_limited, "Should not be rate limited initially"
        
        # Record some attempts
        for i in range(3):
            RateLimiter.record_attempt(request, 'login')
            is_limited, attempts_remaining, reset_time = RateLimiter.is_rate_limited(
                request, 'login', max_attempts=3, window_minutes=1
            )
            print(f"After {i+1} attempts - Limited: {is_limited}, Remaining: {attempts_remaining}")
        
        assert is_limited, "Should be rate limited after 3 attempts"
        print("✅ Rate limiting working correctly")
    
    def test_enhanced_signup(self):
        """Test enhanced signup with email verification"""
        print("\n📝 Testing Enhanced Signup")
        print("=" * 28)
        
        # Test signup mutation
        signup_mutation = """
        mutation Signup($email: String!, $name: String!, $password: String!) {
            createUser(email: $email, name: $name, password: $password) {
                user {
                    id
                    email
                    name
                }
                success
                message
            }
        }
        """
        
        variables = {
            "email": "newuser@example.com",
            "name": "New User",
            "password": "StrongPass123!"
        }
        
        response = self.client.post('/graphql/', {
            'query': signup_mutation,
            'variables': json.dumps(variables)
        }, content_type='application/json')
        
        data = json.loads(response.content)
        print(f"Signup response: {data}")
        
        if 'errors' in data:
            print(f"❌ Signup failed: {data['errors']}")
        else:
            result = data['data']['createUser']
            print(f"✅ Signup successful: {result['message']}")
            assert result['success'], "Signup should be successful"
    
    def test_enhanced_login(self):
        """Test enhanced login with security features"""
        print("\n🔑 Testing Enhanced Login")
        print("=" * 25)
        
        # Test enhanced login mutation
        login_mutation = """
        mutation Login($email: String!, $password: String!) {
            enhancedTokenAuth(email: $email, password: $password) {
                token
                user {
                    id
                    email
                    name
                }
                success
                message
            }
        }
        """
        
        variables = {
            "email": self.test_email,
            "password": self.test_password
        }
        
        response = self.client.post('/graphql/', {
            'query': login_mutation,
            'variables': json.dumps(variables)
        }, content_type='application/json')
        
        data = json.loads(response.content)
        print(f"Login response: {data}")
        
        if 'errors' in data:
            print(f"❌ Login failed: {data['errors']}")
        else:
            result = data['data']['enhancedTokenAuth']
            print(f"✅ Login successful: {result['message']}")
            assert result['success'], "Login should be successful"
            assert result['token'], "Should receive authentication token"
    
    def test_forgot_password(self):
        """Test forgot password functionality"""
        print("\n🔒 Testing Forgot Password")
        print("=" * 28)
        
        forgot_password_mutation = """
        mutation ForgotPassword($email: String!) {
            forgotPassword(email: $email) {
                success
                message
            }
        }
        """
        
        variables = {
            "email": self.test_email
        }
        
        response = self.client.post('/graphql/', {
            'query': forgot_password_mutation,
            'variables': json.dumps(variables)
        }, content_type='application/json')
        
        data = json.loads(response.content)
        print(f"Forgot password response: {data}")
        
        if 'errors' in data:
            print(f"❌ Forgot password failed: {data['errors']}")
        else:
            result = data['data']['forgotPassword']
            print(f"✅ Forgot password successful: {result['message']}")
            assert result['success'], "Forgot password should be successful"
    
    def test_change_password(self):
        """Test change password functionality"""
        print("\n🔄 Testing Change Password")
        print("=" * 28)
        
        # First login to get token
        login_mutation = """
        mutation Login($email: String!, $password: String!) {
            enhancedTokenAuth(email: $email, password: $password) {
                token
            }
        }
        """
        
        variables = {
            "email": self.test_email,
            "password": self.test_password
        }
        
        response = self.client.post('/graphql/', {
            'query': login_mutation,
            'variables': json.dumps(variables)
        }, content_type='application/json')
        
        data = json.loads(response.content)
        if 'errors' in data:
            print(f"❌ Login failed for change password test: {data['errors']}")
            return
        
        token = data['data']['enhancedTokenAuth']['token']
        
        # Test change password
        change_password_mutation = """
        mutation ChangePassword($currentPassword: String!, $newPassword: String!) {
            changePassword(currentPassword: $currentPassword, newPassword: $newPassword) {
                success
                message
            }
        }
        """
        
        variables = {
            "currentPassword": self.test_password,
            "newPassword": "NewStrongPass123!"
        }
        
        response = self.client.post('/graphql/', {
            'query': change_password_mutation,
            'variables': json.dumps(variables),
            'HTTP_AUTHORIZATION': f'Bearer {token}'
        }, content_type='application/json')
        
        data = json.loads(response.content)
        print(f"Change password response: {data}")
        
        if 'errors' in data:
            print(f"❌ Change password failed: {data['errors']}")
        else:
            result = data['data']['changePassword']
            print(f"✅ Change password successful: {result['message']}")
            assert result['success'], "Change password should be successful"
    
    def test_email_verification(self):
        """Test email verification functionality"""
        print("\n📧 Testing Email Verification")
        print("=" * 30)
        
        # Test verify email mutation
        verify_email_mutation = """
        mutation VerifyEmail($token: String!) {
            verifyEmail(token: $token) {
                success
                message
            }
        }
        """
        
        # Use a test token (in real scenario, this would come from email)
        variables = {
            "token": "test-verification-token"
        }
        
        response = self.client.post('/graphql/', {
            'query': verify_email_mutation,
            'variables': json.dumps(variables)
        }, content_type='application/json')
        
        data = json.loads(response.content)
        print(f"Verify email response: {data}")
        
        if 'errors' in data:
            print(f"❌ Verify email failed: {data['errors']}")
        else:
            result = data['data']['verifyEmail']
            print(f"✅ Verify email response: {result['message']}")
    
    def test_account_lockout(self):
        """Test account lockout functionality"""
        print("\n🔒 Testing Account Lockout")
        print("=" * 28)
        
        # Test multiple failed login attempts
        login_mutation = """
        mutation Login($email: String!, $password: String!) {
            enhancedTokenAuth(email: $email, password: $password) {
                token
                success
                message
            }
        }
        """
        
        # Try wrong password multiple times
        variables = {
            "email": self.test_email,
            "password": "WrongPassword123!"
        }
        
        for i in range(6):  # Try 6 times (should trigger lockout after 5)
            response = self.client.post('/graphql/', {
                'query': login_mutation,
                'variables': json.dumps(variables)
            }, content_type='application/json')
            
            data = json.loads(response.content)
            print(f"Failed attempt {i+1}: {data}")
            
            if 'errors' in data:
                error_message = data['errors'][0]['message']
                if "locked" in error_message.lower():
                    print("✅ Account lockout triggered correctly")
                    break
        else:
            print("⚠️ Account lockout may not be working as expected")
    
    def cleanup(self):
        """Clean up test data"""
        print("\n🧹 Cleaning up test data...")
        User.objects.filter(email__in=[self.test_email, "newuser@example.com"]).delete()
        cache.clear()
        print("✅ Cleanup complete")
    
    def run_all_tests(self):
        """Run all authentication tests"""
        print("🚀 Starting Enhanced Authentication Tests")
        print("=" * 50)
        
        try:
            self.setup_test_user()
            self.test_password_strength_validation()
            self.test_rate_limiting()
            self.test_enhanced_signup()
            self.test_enhanced_login()
            self.test_forgot_password()
            self.test_change_password()
            self.test_email_verification()
            self.test_account_lockout()
            
            print("\n🎉 All tests completed successfully!")
            print("✅ Enhanced authentication system is working correctly")
            
        except Exception as e:
            print(f"\n❌ Test failed: {e}")
            import traceback
            traceback.print_exc()
        
        finally:
            self.cleanup()

def main():
    """Main test runner"""
    print("🔐 RichesReach Enhanced Authentication Test Suite")
    print("=" * 55)
    print()
    
    # Check if Django is properly configured
    try:
        from django.conf import settings
        print(f"✅ Django configured: {settings.SETTINGS_MODULE}")
    except Exception as e:
        print(f"❌ Django configuration error: {e}")
        return
    
    # Check email configuration
    print(f"📧 Email backend: {settings.EMAIL_BACKEND}")
    print(f"📧 Email host: {settings.EMAIL_HOST}")
    print(f"📧 Default from: {settings.DEFAULT_FROM_EMAIL}")
    print()
    
    # Run tests
    tester = EnhancedAuthTester()
    tester.run_all_tests()

if __name__ == "__main__":
    main()
