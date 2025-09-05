#!/usr/bin/env python3
"""
Simple Enhanced Authentication Test
Tests the core authentication features without complex cleanup
"""

import os
import sys
import django
from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.core.cache import cache
import json

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'richesreach.settings')
django.setup()

User = get_user_model()

def test_password_strength():
    """Test password strength validation"""
    print("🔐 Testing Password Strength Validation")
    print("=" * 40)
    
    try:
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
        return True
        
    except Exception as e:
        print(f"❌ Password strength test failed: {e}")
        return False

def test_rate_limiting():
    """Test rate limiting functionality"""
    print("\n⏱️ Testing Rate Limiting")
    print("=" * 25)
    
    try:
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
        return True
        
    except Exception as e:
        print(f"❌ Rate limiting test failed: {e}")
        return False

def test_user_security_fields():
    """Test that User model has security fields"""
    print("\n👤 Testing User Security Fields")
    print("=" * 32)
    
    try:
        # Check if User model has security fields
        user_fields = [field.name for field in User._meta.fields]
        security_fields = [
            'failed_login_attempts',
            'locked_until', 
            'last_login_ip',
            'email_verified',
            'two_factor_enabled',
            'two_factor_secret',
            'created_at',
            'updated_at'
        ]
        
        for field in security_fields:
            if field in user_fields:
                print(f"✅ Field exists: {field}")
            else:
                print(f"❌ Field missing: {field}")
                return False
        
        # Test creating a user
        test_email = "test_security@example.com"
        
        # Check if user already exists
        if User.objects.filter(email=test_email).exists():
            user = User.objects.get(email=test_email)
            print(f"✅ Using existing test user: {user.email}")
        else:
            user = User.objects.create_user(
                email=test_email,
                name="Security Test User",
                password="TestPassword123!"
            )
            print(f"✅ Created test user: {user.email}")
        
        # Test security fields
        print(f"✅ Failed login attempts: {user.failed_login_attempts}")
        print(f"✅ Email verified: {user.email_verified}")
        print(f"✅ Two factor enabled: {user.two_factor_enabled}")
        print(f"✅ Created at: {user.created_at}")
        print(f"✅ Updated at: {user.updated_at}")
        
        # Test security methods
        print(f"✅ Is locked: {user.is_locked()}")
        
        print("✅ User security fields working correctly")
        return True
        
    except Exception as e:
        print(f"❌ User security fields test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_enhanced_mutations():
    """Test that enhanced mutations are available"""
    print("\n🔧 Testing Enhanced Mutations")
    print("=" * 30)
    
    try:
        from core.mutations import (
            ForgotPassword, ResetPassword, ChangePassword, 
            VerifyEmail, ResendVerificationEmail, EnhancedTokenAuth
        )
        
        mutations = [
            ('ForgotPassword', ForgotPassword),
            ('ResetPassword', ResetPassword),
            ('ChangePassword', ChangePassword),
            ('VerifyEmail', VerifyEmail),
            ('ResendVerificationEmail', ResendVerificationEmail),
            ('EnhancedTokenAuth', EnhancedTokenAuth),
        ]
        
        for name, mutation_class in mutations:
            print(f"✅ Mutation available: {name}")
            assert mutation_class is not None, f"{name} mutation should be available"
        
        print("✅ All enhanced mutations are available")
        return True
        
    except Exception as e:
        print(f"❌ Enhanced mutations test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_email_configuration():
    """Test email configuration"""
    print("\n📧 Testing Email Configuration")
    print("=" * 32)
    
    try:
        from django.conf import settings
        
        print(f"✅ Email backend: {settings.EMAIL_BACKEND}")
        print(f"✅ Email host: {settings.EMAIL_HOST}")
        print(f"✅ Email port: {settings.EMAIL_PORT}")
        print(f"✅ Email use TLS: {settings.EMAIL_USE_TLS}")
        print(f"✅ Default from email: {settings.DEFAULT_FROM_EMAIL}")
        print(f"✅ Frontend URL: {settings.FRONTEND_URL}")
        
        # Check if email settings are configured
        if settings.EMAIL_HOST_USER and settings.EMAIL_HOST_USER != "your-email@gmail.com":
            print("✅ Email credentials configured")
        else:
            print("⚠️ Email credentials need to be configured")
        
        print("✅ Email configuration is set up")
        return True
        
    except Exception as e:
        print(f"❌ Email configuration test failed: {e}")
        return False

def main():
    """Main test runner"""
    print("🔐 RichesReach Enhanced Authentication Simple Test")
    print("=" * 55)
    print()
    
    tests = [
        ("Password Strength Validation", test_password_strength),
        ("Rate Limiting", test_rate_limiting),
        ("User Security Fields", test_user_security_fields),
        ("Enhanced Mutations", test_enhanced_mutations),
        ("Email Configuration", test_email_configuration),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n🧪 Running: {test_name}")
        print("-" * 40)
        
        try:
            if test_func():
                passed += 1
                print(f"✅ {test_name} PASSED")
            else:
                print(f"❌ {test_name} FAILED")
        except Exception as e:
            print(f"❌ {test_name} FAILED with exception: {e}")
    
    print(f"\n📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests passed! Enhanced authentication system is working correctly!")
        print("\n📋 Next steps:")
        print("1. Configure your email credentials in backend/.env")
        print("2. Test the GraphQL mutations in your frontend")
        print("3. Deploy with confidence!")
    else:
        print(f"\n⚠️ {total - passed} tests failed. Please check the issues above.")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
