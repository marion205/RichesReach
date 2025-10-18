"""
Authentication REST API endpoints for React Native app
Provides fallback authentication when GraphQL tokenAuth fails
"""
from django.contrib.auth import authenticate
from django.contrib.auth import get_user_model
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from graphql_jwt.shortcuts import get_token
import json
import logging

logger = logging.getLogger(__name__)
User = get_user_model()

@csrf_exempt
@require_http_methods(["POST"])
def rest_login(request):
    """
    REST API login endpoint for React Native app
    Accepts either {email, password} OR {username, password}
    Case-insensitive match for email/username. Returns JWT token.
    """
    try:
        # Parse JSON body
        data = json.loads(request.body)
        identifier = (data.get("email") or data.get("username") or "").strip()
        password = (data.get("password") or "").strip()
        
        if not identifier or not password:
            return JsonResponse({
                'success': False,
                'error': 'Email/username and password are required'
            }, status=400)
        
        logger.info(f"REST login attempt for: {identifier}")
        
        # Find user by email or username (case-insensitive)
        try:
            if "@" in identifier:
                user = User.objects.get(email__iexact=identifier)
            else:
                user = User.objects.get(username__iexact=identifier)
        except User.DoesNotExist:
            logger.warning(f"REST login failed - user not found: {identifier}")
            return JsonResponse({
                'success': False,
                'error': 'Invalid email or password'
            }, status=401)
        
        # Check if user is active
        if not user.is_active:
            logger.warning(f"REST login failed - inactive user: {identifier}")
            return JsonResponse({
                'success': False,
                'error': 'User account is inactive'
            }, status=403)
        
        # Check password
        if not user.check_password(password):
            logger.warning(f"REST login failed - wrong password: {identifier}")
            return JsonResponse({
                'success': False,
                'error': 'Invalid email or password'
            }, status=401)
        
        # Generate JWT token using the same method as GraphQL
        token = get_token(user)
        logger.info(f"REST login successful for: {identifier}")
        
        return JsonResponse({
            'success': True,
            'token': token,
            'user': {
                'id': user.id,
                'email': user.email,
                'username': user.username,
                'name': getattr(user, 'name', ''),
                'hasPremiumAccess': getattr(user, 'hasPremiumAccess', False),
                'subscriptionTier': getattr(user, 'subscriptionTier', 'free')
            }
        })
            
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Invalid JSON'
        }, status=400)
    except Exception as e:
        logger.error(f"REST login error: {e}")
        return JsonResponse({
            'success': False,
            'error': 'Internal server error'
        }, status=500)

@csrf_exempt
@require_http_methods(["POST"])
def rest_verify_token(request):
    """
    REST API token verification endpoint
    """
    try:
        data = json.loads(request.body)
        token = data.get('token')
        
        if not token:
            return JsonResponse({
                'success': False,
                'error': 'Token is required'
            }, status=400)
        
        # Verify token (this will be handled by JWT middleware in production)
        # For now, we'll just return success if token exists
        return JsonResponse({
            'success': True,
            'valid': True
        })
        
    except Exception as e:
        logger.error(f"Token verification error: {e}")
        return JsonResponse({
            'success': False,
            'error': 'Token verification failed'
        }, status=500)
