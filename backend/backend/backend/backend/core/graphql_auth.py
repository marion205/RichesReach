"""
GraphQL Authentication Middleware for SimpleJWT
"""
from rest_framework_simplejwt.authentication import JWTAuthentication
from django.contrib.auth.models import AnonymousUser

_jwt_auth = JWTAuthentication()

def attach_user(get_response):
    """
    Middleware to attach authenticated user to GraphQL requests
    """
    def middleware(request):
        try:
            auth_result = _jwt_auth.authenticate(request)
            if auth_result:
                request.user, _ = auth_result
            else:
                request.user = getattr(request, "user", AnonymousUser())
        except Exception:
            request.user = AnonymousUser()
        return get_response(request)
    return middleware
