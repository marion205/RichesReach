#!/usr/bin/env python3
import os
import sys
import django
import jwt
from datetime import datetime, timedelta

# Add the backend directory to the Python path
sys.path.append('/Users/marioncollins/RichesReach/backend')

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'richesreach.settings')
django.setup()

from django.contrib.auth import get_user_model

User = get_user_model()

# Create a test user directly
try:
    # Check if user already exists
    user = User.objects.filter(email='test@example.com').first()
    if not user:
        user = User.objects.create_user(
            email='test@example.com',
            password='testpass',
            name='Test User'
        )
        print(f"User created: {user.email}")
    else:
        print(f"User already exists: {user.email}")
    
    # Test password
    if user.check_password('testpass'):
        print("Password verification successful")
    else:
        print("Password verification failed")
        
    # Create JWT token
    SECRET_KEY = 'django-insecure-wk_qy339*l)1xg=(f6_e@9+d7sgi7%#0t!e17a3nkeu&p#@zq9'
    ALGORITHM = 'HS256'
    
    now = datetime.utcnow()
    payload = {
        'sub': user.email,
        'iat': now,
        'exp': now + timedelta(minutes=60),
    }
    
    token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
    print(f"JWT token created: {token[:50]}...")
    
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
