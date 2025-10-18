#!/usr/bin/env python3
"""
Create a test user for local development testing
"""
import os
import sys
import django

# Add the Django project to the Python path
sys.path.append('/Users/marioncollins/RichesReach/backend/backend/backend/backend')

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'richesreach.settings_local_db')
django.setup()

from django.contrib.auth import get_user_model
from core.models import User

def create_test_user():
    """Create a test user for mobile app testing"""
    User = get_user_model()
    
    # Check if user already exists
    try:
        user = User.objects.get(email='mobile@example.com')
        print(f"✅ User already exists: {user.email}")
        return user
    except User.DoesNotExist:
        pass
    
    # Create new user
    try:
        user = User.objects.create_user(
            email='mobile@example.com',
            username='mobile_user',
            password='mobilepass123',
            first_name='Mobile',
            last_name='Tester'
        )
        print(f"✅ Created new user: {user.email}")
        return user
    except Exception as e:
        print(f"❌ Error creating user: {e}")
        return None

if __name__ == "__main__":
    user = create_test_user()
    if user:
        print(f"User ID: {user.id}")
        print(f"Email: {user.email}")
        print(f"Username: {user.username}")
        print("Ready for mobile app authentication!")
