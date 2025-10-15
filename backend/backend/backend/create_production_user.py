#!/usr/bin/env python3
"""
Create a test user in production database
"""
import os
import sys
import django

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'richesreach.settings_production')
django.setup()

from django.contrib.auth import get_user_model

User = get_user_model()

def create_test_user():
    """Create test user in production database"""
    try:
        user, created = User.objects.get_or_create(
            email='test@example.com',
            defaults={
                'name': 'Test User',
                'is_active': True,
            }
        )
        
        if created:
            user.set_password('password123')
            user.save()
            print(f'✅ User created successfully: {user.email}')
            print(f'   Name: {user.name}')
            print(f'   ID: {user.id}')
            print(f'   Active: {user.is_active}')
        else:
            print(f'ℹ️ User already exists: {user.email}')
            # Update password anyway
            user.set_password('password123')
            user.save()
            print(f'✅ Password updated for: {user.email}')
            print(f'   Name: {user.name}')
            print(f'   ID: {user.id}')
            print(f'   Active: {user.is_active}')
            
        return user
        
    except Exception as e:
        print(f'❌ Error creating user: {e}')
        return None

if __name__ == '__main__':
    print("👤 Creating test user in production database...")
    print("=" * 50)
    user = create_test_user()
    
    if user:
        print("\n🎉 User creation completed successfully!")
        print(f"Email: {user.email}")
        print(f"Password: password123")
    else:
        print("\n❌ User creation failed!")
        sys.exit(1)
