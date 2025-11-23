# core/authentication.py
from django.contrib.auth.backends import BaseBackend
from django.contrib.auth import get_user_model
import logging

logger = logging.getLogger(__name__)

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
    if not token:
        return None
    
    # DEVELOPMENT MODE: Handle dev tokens for testing
    if token.startswith('dev-token-'):
        # In development, try to get/create a user for dev tokens
        # Priority: 1) demo@example.com (default login), 2) test@example.com (fallback)
        try:
            # First, try to get or create demo@example.com (default in login screen)
            user, created = User.objects.get_or_create(
                email='demo@example.com',
                defaults={}
            )
            if created:
                user.set_unusable_password()  # Don't set a password for dev user
                # Try to set optional fields if they exist
                if hasattr(user, 'username'):
                    user.username = 'demo'
                if hasattr(user, 'name'):
                    user.name = 'Demo User'
                user.save()
                logger.info(f"Created dev user: {user.email}")
            else:
                logger.info(f"Using existing dev user: {user.email}")
            return user
        except Exception as e:
            logger.warning(f"Failed to get/create demo@example.com: {e}, trying test@example.com")
            # Fallback to test@example.com if demo@example.com fails
            try:
                user, created = User.objects.get_or_create(
                    email='test@example.com',
                    defaults={}
                )
                if created:
                    user.set_unusable_password()
                    if hasattr(user, 'username'):
                        user.username = 'testuser'
                    if hasattr(user, 'name'):
                        user.name = 'Test User'
                    user.save()
                return user
            except Exception as e2:
                logger.warning(f"Failed to get/create test user: {e2}")
                return None
    
    # Production: Use real JWT token validation
    if not GRAPHQL_JWT_AVAILABLE:
        return None
    try:
        user = get_user_by_token(token)
        return user
    except (PermissionDenied, Exception):
        pass
    return None
