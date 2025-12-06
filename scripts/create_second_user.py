#!/usr/bin/env python3
"""
Create a second test user for RichesReach
Usage: python3 scripts/create_second_user.py
"""

import os
import sys
import django

# Add backend to path
backend_path = os.path.join(os.path.dirname(__file__), '..', 'deployment_package', 'backend')
sys.path.insert(0, os.path.abspath(backend_path))
os.chdir(os.path.abspath(backend_path))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from django.contrib.auth import get_user_model

User = get_user_model()

def create_second_user():
    """Create a second test user"""
    
    # User 2 credentials
    email = 'user2@test.com'
    password = 'testpass123'
    name = 'Test User 2'
    
    # Check if user already exists
    if User.objects.filter(email=email).exists():
        print(f"⚠️  User {email} already exists!")
        user = User.objects.get(email=email)
        print(f"   User ID: {user.id}")
        print(f"   Name: {user.name}")
        print(f"   Created: {user.created_at}")
        return user
    
    # Create new user
    try:
        user = User.objects.create_user(
            email=email,
            password=password,
            name=name,
            is_active=True
        )
        print(f"✅ Created second user:")
        print(f"   Email: {user.email}")
        print(f"   Name: {user.name}")
        print(f"   Password: {password}")
        print(f"   User ID: {user.id}")
        print(f"\n📱 Login credentials:")
        print(f"   Email: {email}")
        print(f"   Password: {password}")
        return user
    except Exception as e:
        print(f"❌ Error creating user: {e}")
        return None

def list_all_users():
    """List all existing users"""
    users = User.objects.all().order_by('created_at')
    print(f"\n📋 All users ({users.count()} total):")
    for i, user in enumerate(users, 1):
        print(f"   {i}. {user.email} ({user.name}) - Created: {user.created_at}")

if __name__ == '__main__':
    print("🔧 Creating second user account...\n")
    user = create_second_user()
    list_all_users()

