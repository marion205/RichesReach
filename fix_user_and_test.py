#!/usr/bin/env python3
"""
Fix user password and test authentication
"""

import os
import sys
import django

# Add the Django project to the path
sys.path.append('backend/backend/backend/backend')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'richesreach.settings_dev')

# Setup Django
django.setup()

from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import make_password

User = get_user_model()

def fix_user_password():
    """Fix the test user's password"""
    try:
        user = User.objects.get(email="test@example.com")
        print(f"Found user: {user.email} (ID: {user.id})")
        
        # Set the password properly
        user.set_password("testpass123")
        user.save()
        
        print("✅ Password updated successfully")
        
        # Test the password
        if user.check_password("testpass123"):
            print("✅ Password verification successful")
            return user
        else:
            print("❌ Password verification failed")
            return None
            
    except User.DoesNotExist:
        print("❌ User not found")
        return None

def test_login():
    """Test login with curl"""
    import subprocess
    
    print("\n🔍 Testing login with curl...")
    
    curl_command = [
        "curl", "-X", "POST", 
        "http://192.168.1.236:8000/graphql/",
        "-H", "Content-Type: application/json",
        "-d", '{"query": "mutation { tokenAuth(email: \\"test@example.com\\", password: \\"testpass123\\") { token user { id email } } }"}'
    ]
    
    try:
        result = subprocess.run(curl_command, capture_output=True, text=True, timeout=10)
        
        if result.returncode == 0:
            print("✅ Curl command successful")
            print(f"Response: {result.stdout}")
            
            # Parse JSON response
            import json
            try:
                data = json.loads(result.stdout)
                if data.get("data", {}).get("tokenAuth", {}).get("token"):
                    print("✅ Login successful - token received")
                    return data["data"]["tokenAuth"]["token"]
                else:
                    print("❌ Login failed - no token received")
                    print(f"Full response: {data}")
                    return None
            except json.JSONDecodeError as e:
                print(f"❌ JSON decode error: {e}")
                return None
        else:
            print(f"❌ Curl command failed: {result.stderr}")
            return None
            
    except Exception as e:
        print(f"❌ Curl test error: {e}")
        return None

def main():
    print("🔧 Fixing User Password and Testing Authentication")
    print("=" * 60)
    
    # Fix user password
    user = fix_user_password()
    
    if user:
        # Test login
        token = test_login()
        
        if token:
            print(f"\n🎉 Authentication working! Token: {token[:20]}...")
        else:
            print("\n❌ Authentication still failing")
    else:
        print("\n❌ Could not fix user password")

if __name__ == "__main__":
    main()
