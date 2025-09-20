#!/usr/bin/env python3
import os
import sys
import django

# Add the backend directory to the Python path
sys.path.append('/Users/marioncollins/RichesReach/backend')

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'richesreach.settings')
django.setup()

from core.models import User

# Create a test user
try:
    user = User.objects.create_user(
        email='test@example.com',
        password='testpass',
        name='Test User'
    )
    print(f"User created successfully: {user.email}")
except Exception as e:
    print(f"Error creating user: {e}")
