"""
GraphQL Authentication Middleware for SimpleJWT
"""
from django.contrib.auth.models import AnonymousUser
from rest_framework_simplejwt.authentication import JWTAuthentication

_jwt_auth = JWTAuthentication()

def attach_user(get_response):
    """
    Django middleware that authenticates the request via SimpleJWT and
    makes request.user available to GraphQL resolvers.
    """
    def middleware(request):
        try:
            result = _jwt_auth.authenticate(request)
            if result:
                request.user, _ = result
            else:
                # leave the user set by Django auth middleware if present
                request.user = getattr(request, "user", AnonymousUser())
        except Exception:
            request.user = AnonymousUser()
        return get_response(request)
    return middleware
