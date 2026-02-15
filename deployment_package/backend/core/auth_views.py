"""
REST API Authentication Views
Provides REST endpoints for login/logout
"""
import json
import logging
import os
from django.http import JsonResponse
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.contrib.auth import authenticate, get_user_model
from django.contrib.auth.hashers import check_password

logger = logging.getLogger(__name__)
User = get_user_model()

# Try to import graphql_jwt for token generation
try:
    from graphql_jwt.shortcuts import get_token
    GRAPHQL_JWT_AVAILABLE = True
except ImportError:
    GRAPHQL_JWT_AVAILABLE = False
    logger.warning("graphql_jwt not available. Using dev tokens for authentication.")


# CSRF exempt because:
# 1. Login endpoint returns JWT token (no session cookies)
# 2. All subsequent requests use Bearer token auth
# 3. Stateless API design
# See: CSRF_VERIFICATION_CHECKLIST.md for full justification
@method_decorator(csrf_exempt, name='dispatch')
class LoginView(View):
    """
    REST API Login Endpoint
    POST /api/auth/login/
    
    Request body:
    {
        "email": "user@example.com",
        "password": "password123"
    }
    
    Response:
    {
        "access_token": "jwt_token_here",
        "token": "jwt_token_here",  # alias for compatibility
        "user": {
            "id": "1",
            "email": "user@example.com",
            "name": "User Name"
        }
    }
    """
    
    def post(self, request):
        try:
            body = json.loads(request.body)
            email = body.get('email', '').strip()
            password = body.get('password', '')
            
            if not email or not password:
                return JsonResponse(
                    {'error': 'Email and password are required'},
                    status=400
                )
            
            logger.info(f"Login attempt for email: {email}")
            
            # Try to authenticate user
            user = None
            
            # Method 1: Try Django's authenticate (requires proper backend)
            try:
                user = authenticate(request, username=email, password=password)
            except Exception as e:
                logger.warning(f"Authenticate failed: {e}")
            
            # Method 2: Manual authentication if Django auth fails
            if not user:
                try:
                    user = User.objects.get(email=email)
                    if user.check_password(password):
                        logger.info(f"Manual authentication successful for {email}")
                    else:
                        logger.warning(f"Invalid password for {email}")
                        user = None
                except User.DoesNotExist:
                    logger.warning(f"User not found: {email}")
                    user = None
                except Exception as e:
                    logger.error(f"Error during manual auth: {e}")
                    user = None
            
            # Method 3: Development fallback - create/get demo user
            if not user:
                logger.info("Authentication failed, checking for demo user...")
                try:
                    # For demo@example.com, always allow login in development
                    if email.lower() == 'demo@example.com':
                        user, created = User.objects.get_or_create(
                            email='demo@example.com',
                            defaults={
                                'name': 'Demo User',
                            }
                        )
                        if created:
                            # Development: use env or fixed default so app can log in
                            demo_password = os.getenv('DEV_DEMO_USER_PASSWORD', 'demo123')
                            user.set_password(demo_password)
                            user.save()
                            logger.info("Created demo user for development")
                        else:
                            # Sync password: env var or default demo123 so app can log in
                            demo_password = os.getenv('DEV_DEMO_USER_PASSWORD', 'demo123')
                            if not user.check_password(demo_password):
                                user.set_password(demo_password)
                                user.save()
                                logger.info("Reset demo user password to dev default")
                        # Accept request if password matches the demo user's current password
                        if user.check_password(password):
                            logger.info("Using demo user for development (dev mode)")
                        else:
                            user = None
                    else:
                        user = None
                except Exception as e:
                    logger.error(f"Error creating demo user: {e}")
                    user = None
            
            if not user:
                return JsonResponse(
                    {'error': 'Invalid email or password'},
                    status=401
                )
            
            # Generate token
            token = None
            if GRAPHQL_JWT_AVAILABLE:
                try:
                    token = get_token(user)
                    logger.info(f"Generated JWT token for {email}")
                except Exception as e:
                    logger.warning(f"Failed to generate JWT token: {e}")
            
            # Fallback to dev token if JWT not available
            if not token:
                import time
                token = f"dev-token-{int(time.time())}"
                logger.info(f"Using dev token for {email}")
            
            # Prepare user data
            user_data = {
                'id': str(user.id),
                'email': user.email,
                'name': getattr(user, 'name', ''),
            }
            
            # Add optional fields if they exist
            if hasattr(user, 'profile_pic') and user.profile_pic:
                user_data['profile_pic'] = user.profile_pic
            
            response_data = {
                'access_token': token,
                'token': token,  # Alias for compatibility
                'user': user_data,
            }
            
            logger.info(f"✅ Login successful for {email}")
            return JsonResponse(response_data, status=200)
            
        except json.JSONDecodeError:
            return JsonResponse(
                {'error': 'Invalid JSON in request body'},
                status=400
            )
        except Exception as e:
            logger.error(f"Error in login: {e}", exc_info=True)
            return JsonResponse(
                {'error': f'Internal server error: {str(e)}'},
                status=500
            )

