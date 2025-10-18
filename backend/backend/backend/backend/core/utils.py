"""
Utility functions for GraphQL resolvers
"""
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from django.conf import settings

def get_user_or_mock(info):
    """
    Get authenticated user or create a mock user for development
    """
    user = getattr(info.context, "user", None)
    
    # Only return a mock user if explicitly enabled
    if getattr(settings, "USE_MOCK_USER", False) and settings.DEBUG and (not user or isinstance(user, AnonymousUser) or not user.is_authenticated):
        # Create a mock user for development
        class MockUser:
            def __init__(self):
                self.id = 1
                self.is_authenticated = True
                self.email = "dev@local"
                self.username = "devuser"
                self.first_name = "Dev"
                self.last_name = "User"
        
        user = MockUser()
        print(f"DEBUG: Using mock user for development: {user.username}")
    
    return user
