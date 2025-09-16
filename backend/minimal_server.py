#!/usr/bin/env python3
"""
Minimal Django server for testing authentication
"""
import os
import sys
import django
from django.conf import settings
from django.core.wsgi import get_wsgi_application

# Add the backend directory to the Python path
sys.path.append('/Users/marioncollins/RichesReach/backend')

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'richesreach.settings')
django.setup()

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
import json
import jwt
from datetime import datetime, timedelta

# JWT Configuration
SECRET_KEY = 'django-insecure-wk_qy339*l)1xg=(f6_e@9+d7sgi7%#0t!e17a3nkeu&p#@zq9'
ALGORITHM = 'HS256'
ACCESS_TOKEN_EXPIRE_MINUTES = 60

# Simple in-memory user storage
users_db = {
    "test@example.com": {
        "email": "test@example.com",
        "password": "testpass",  # Store plain text for simplicity
        "name": "Test User",
        "id": "1"
    }
}

def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

@csrf_exempt
@require_http_methods(["POST"])
def graphql_endpoint(request):
    """GraphQL endpoint for authentication"""
    try:
        request_data = json.loads(request.body.decode('utf-8'))
        query = request_data.get("query", "")
        variables = request_data.get("variables", {})
        
        # Handle tokenAuth mutation
        if "tokenAuth" in query:
            email = variables.get("email", "")
            password = variables.get("password", "")
            
            if not email or not password:
                return JsonResponse({
                    "errors": [{"message": "Email and password are required"}]
                })
            
            # Check user credentials
            user = users_db.get(email.lower())
            if not user or user["password"] != password:
                return JsonResponse({
                    "errors": [{"message": "Please enter valid credentials"}]
                })
            
            # Create token
            access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
            access_token = create_access_token(
                data={"sub": email.lower()}, expires_delta=access_token_expires
            )
            
            return JsonResponse({
                "data": {
                    "tokenAuth": {
                        "token": access_token
                    }
                }
            })
        
        # Handle createUser mutation
        elif "createUser" in query:
            email = variables.get("email", "")
            name = variables.get("name", "")
            password = variables.get("password", "")
            
            if not email or not name or not password:
                return JsonResponse({
                    "errors": [{"message": "Email, name, and password are required"}]
                })
            
            if email.lower() in users_db:
                return JsonResponse({
                    "errors": [{"message": "User already exists"}]
                })
            
            # Create new user
            user_id = str(len(users_db) + 1)
            users_db[email.lower()] = {
                "email": email.lower(),
                "password": password,  # Store plain text for simplicity
                "name": name,
                "id": user_id
            }
            
            return JsonResponse({
                "data": {
                    "createUser": {
                        "user": {
                            "id": user_id,
                            "email": email.lower(),
                            "name": name
                        }
                    }
                }
            })
        
        # Handle other queries
        return JsonResponse({
            "data": {
                "__schema": {
                    "types": [{"name": "Query"}, {"name": "Mutation"}]
                }
            }
        })
        
    except Exception as e:
        return JsonResponse({
            "errors": [{"message": str(e)}]
        })

if __name__ == "__main__":
    from django.core.management import execute_from_command_line
    execute_from_command_line(['manage.py', 'runserver', '0.0.0.0:8000'])
