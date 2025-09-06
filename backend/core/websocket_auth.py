"""
Custom WebSocket authentication middleware for JWT tokens
"""
import jwt
from django.contrib.auth.models import AnonymousUser
from django.contrib.auth import get_user_model
from django.conf import settings
import logging

logger = logging.getLogger(__name__)
User = get_user_model()

class JWTAuthMiddleware:
    """
    Custom middleware to authenticate WebSocket connections using JWT tokens
    """
    
    def __init__(self, app):
        self.app = app
    
    async def __call__(self, scope, receive, send):
        # Extract JWT token from query parameters or headers
        query_string = scope.get('query_string', b'').decode()
        headers = dict(scope.get('headers', []))
        
        # Try to get token from query parameters first
        token = None
        if query_string:
            params = dict(param.split('=') for param in query_string.split('&') if '=' in param)
            token = params.get('token')
        
        # If not in query params, try Authorization header
        if not token:
            auth_header = headers.get(b'authorization', b'').decode()
            if auth_header.startswith('Bearer '):
                token = auth_header[7:]
        
        # Authenticate user with JWT token
        user = AnonymousUser()
        if token:
            try:
                # Use graphql_jwt's get_user_by_token for consistency
                from graphql_jwt.shortcuts import get_user_by_token
                from graphql_jwt.exceptions import PermissionDenied
                
                # Get user synchronously first, then convert to async
                user = await self.get_user_from_token(token)
                if not isinstance(user, AnonymousUser):
                    logger.info(f"🔐 WebSocket JWT Auth - User authenticated: {user.email}")
                else:
                    logger.warning("🔐 WebSocket JWT Auth - Token authentication failed")
            except Exception as e:
                logger.warning(f"🔐 WebSocket JWT Auth - Error: {e}")
        else:
            logger.info("🔐 WebSocket JWT Auth - No token provided")
        
        # Add user to scope
        scope['user'] = user
        
        return await self.app(scope, receive, send)
    
    async def get_user_from_token(self, token):
        """Get user from JWT token asynchronously"""
        try:
            from channels.db import database_sync_to_async
            from graphql_jwt.shortcuts import get_user_by_token
            
            # Run the synchronous get_user_by_token in a thread
            return await database_sync_to_async(get_user_by_token)(token)
        except Exception:
            return AnonymousUser()
    
    async def get_user(self, user_id):
        """Get user by ID asynchronously"""
        try:
            from channels.db import database_sync_to_async
            return await database_sync_to_async(User.objects.get)(id=user_id)
        except User.DoesNotExist:
            return AnonymousUser()
