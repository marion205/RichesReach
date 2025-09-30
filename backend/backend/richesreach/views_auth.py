import datetime
import jwt
from django.conf import settings
from django.contrib.auth import authenticate
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.timezone import now

SECRET = getattr(settings, "JWT_SECRET_KEY", settings.SECRET_KEY)

@csrf_exempt
def login_view(request):
    if request.method != "POST":
        return JsonResponse({"detail": "Method not allowed"}, status=405)
    
    import json
    body = json.loads(request.body or "{}")
    email = body.get("email")
    password = body.get("password")
    
    # For development, accept any email/password combination
    if email and password:
        # Create a mock user payload
        payload = {
            "sub": "1",  # user ID
            "email": email,
            "username": email.split('@')[0],
            "iss": "richesreach",
            "aud": "mobile",
            "iat": int(now().timestamp()),
            "exp": int((now() + datetime.timedelta(hours=8)).timestamp())
        }
        token = jwt.encode(payload, SECRET, algorithm="HS256")
        return JsonResponse({"token": token})
    else:
        return JsonResponse({"detail": "Invalid credentials"}, status=401)
