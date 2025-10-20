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
            # Check if this is a GraphQL request
            if hasattr(request, 'path') and 'graphql' in request.path:
                print(f"JWT Auth: GraphQL request to {request.path}")
                print(f"JWT Auth: Authorization header: {request.META.get('HTTP_AUTHORIZATION', 'None')}")
            
            result = _jwt_auth.authenticate(request)
            if result:
                request.user, _ = result
                print(f"JWT Auth: User authenticated: {request.user}")
            else:
                # leave the user set by Django auth middleware if present
                request.user = getattr(request, "user", AnonymousUser())
                print(f"JWT Auth: No JWT auth, using: {request.user}")
        except Exception as e:
            request.user = AnonymousUser()
            print(f"JWT Auth: Exception: {e}")
        return get_response(request)
    return middleware
