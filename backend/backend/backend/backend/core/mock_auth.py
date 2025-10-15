# core/mock_auth.py
import datetime
import jwt
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

# Mock secret key for JWT generation (doesn't need to match prod)
SECRET_KEY = "mocksecret"

@csrf_exempt
def mock_login(request):
    """Mock login endpoint that returns a proper 3-part JWT"""
    if request.method == "POST":
        try:
            # Build a proper 3-part JWT payload
            payload = {
                "user_id": 1,
                "username": "demo_user",
                "email": "demo@example.com",
                "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=24),  # 24 hour expiry
                "iat": datetime.datetime.utcnow(),
                "iss": "riches-reach-mock"
            }
            
            # Generate a proper JWT with 3 parts (header.payload.signature)
            token = jwt.encode(payload, SECRET_KEY, algorithm="HS256")
            
            return JsonResponse({
                "access": token,
                "refresh": token,  # For compatibility
                "user": {
                    "id": 1,
                    "username": "demo_user",
                    "email": "demo@example.com"
                }
            })
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)
    
    return JsonResponse({"detail": "Method not allowed"}, status=405)
