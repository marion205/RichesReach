# core/authentication.py
from django.contrib.auth.backends import BaseBackend
from django.contrib.auth import get_user_model

# Make graphql_jwt optional for testing
try:
    from graphql_jwt.shortcuts import get_user_by_token
    from graphql_jwt.exceptions import PermissionDenied
    GRAPHQL_JWT_AVAILABLE = True
except ImportError:
    GRAPHQL_JWT_AVAILABLE = False
    # Mock functions for when graphql_jwt is not available
    def get_user_by_token(token):
        return None
    class PermissionDenied(Exception):
        pass

User = get_user_model()


class JWTAuthenticationBackend(BaseBackend):
    def authenticate(self, request, **kwargs):
        # This method is called by Django's authentication system
        # For GraphQL, we'll handle this in the middleware
        return None

    def get_user(self, user_id):
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None


def get_user_from_token(token):
    """Extract user from JWT token"""
    if not GRAPHQL_JWT_AVAILABLE:
        return None
    try:
        if token:
            user = get_user_by_token(token)
            return user
    except (PermissionDenied, Exception):
        pass
    return None
