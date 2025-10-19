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

# Test JWT token creation
SECRET_KEY = 'django-insecure-wk_qy339*l)1xg=(f6_e@9+d7sgi7%#0t!e17a3nkeu&p#@zq9'
ALGORITHM = 'HS256'

def create_test_token():
    """Create a test JWT token"""
    try:
        now = datetime.utcnow()
        payload = {
            'sub': 'test@example.com',
            'iat': now,
            'exp': now + timedelta(minutes=60),
            'jti': 'test-token-id'
        }
        
        token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
        print(f"Token created successfully: {token[:50]}...")
        
        # Test decoding
        decoded = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        print(f"Token decoded successfully: {decoded}")
        
        return token
    except Exception as e:
        print(f"Error creating token: {e}")
        return None

if __name__ == "__main__":
    create_test_token()
