import datetime
import jwt
from django.conf import settings
from django.contrib.auth import authenticate
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.timezone import now
from django.contrib.auth import get_user_model

User = get_user_model()

@csrf_exempt
def login_view(request):
    if request.method != "POST":
        return JsonResponse({"detail": "Method not allowed"}, status=405)
    
    import json
    body = json.loads(request.body or "{}")
    email = body.get("email")
    password = body.get("password")
    
    # Authenticate user
    user = authenticate(request, username=email, password=password)
    
    if user:
            # Create GraphQL JWT compatible token using the same method as graphql_jwt
            from graphql_jwt.utils import jwt_encode, jwt_payload
            from graphql_jwt.settings import jwt_settings
            
            # Generate payload using the same method as graphql_jwt
            payload = jwt_payload(user)
            
            # Encode using the same settings as graphql_jwt
            token = jwt_encode(payload)
            
            return JsonResponse({
                "token": token,
                "user": {
                    "id": str(user.id),
                    "email": user.email,
                    "username": user.username
                }
            })
    else:
        return JsonResponse({"detail": "Invalid credentials"}, status=401)
