# core/authentication.py
from django.contrib.auth.backends import BaseBackend
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import AccessToken
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
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
    """Extract user from JWT token using SimpleJWT"""
    try:
        if token:
            access_token = AccessToken(token)
            user_id = access_token['user_id']
            user = User.objects.get(pk=user_id)
            return user
    except (InvalidToken, TokenError, User.DoesNotExist, Exception):
        pass
    return None
