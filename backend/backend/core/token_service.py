"""
Secure Token Service for Agora and Stream.io
Generates short-lived tokens server-side to keep secrets secure
"""

import os
import time
import json
from datetime import datetime, timedelta
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

# Agora token generation (requires agora-token-builder package)
try:
    from agora_token_builder import RtcTokenBuilder, RtcRole
    AGORA_AVAILABLE = True
except ImportError:
    AGORA_AVAILABLE = False
    logger.warning("agora-token-builder not installed. Install with: pip install agora-token-builder")

# Stream.io token generation (requires stream-chat package)
try:
    from stream_chat import StreamChat
    STREAM_AVAILABLE = True
except ImportError:
    STREAM_AVAILABLE = False
    logger.warning("stream-chat not installed. Install with: pip install stream-chat")


@csrf_exempt
@require_http_methods(["GET"])
def agora_token(request):
    """
    Generate Agora RTC token for live streaming
    GET /api/agora/token?channel=room123&uid=1&role=publisher
    """
    if not AGORA_AVAILABLE:
        return JsonResponse({
            'error': 'Agora token service not available. Install agora-access-token package.'
        }, status=500)
    
    try:
        # Get parameters
        channel = request.GET.get('channel')
        uid = request.GET.get('uid', '0')
        role = request.GET.get('role', 'publisher')  # publisher or subscriber
        
        if not channel:
            return JsonResponse({'error': 'channel parameter required'}, status=400)
        
        # Get Agora configuration from settings
        agora_app_id = getattr(settings, 'AGORA_APP_ID', None)
        agora_app_certificate = getattr(settings, 'AGORA_APP_CERTIFICATE', None)
        
        if not agora_app_id:
            return JsonResponse({'error': 'Agora App ID not configured'}, status=500)
        
        # Token expiration (default 1 hour)
        token_ttl = int(getattr(settings, 'AGORA_TOKEN_TTL_SECONDS', 3600))
        privilege_expire_time = int(time.time()) + token_ttl
        
        # Generate token
        if agora_app_certificate:
            # Production: use certificate for secure tokens
            token = RtcTokenBuilder.buildTokenWithUid(
                agora_app_id,
                agora_app_certificate,
                channel,
                int(uid),
                RtcRole.PUBLISHER if role == 'publisher' else RtcRole.SUBSCRIBER,
                privilege_expire_time
            )
        else:
            # Development: use null token (Agora allows this for testing)
            token = None
            logger.warning("Agora App Certificate not configured. Using null token for development.")
        
        return JsonResponse({
            'appId': agora_app_id,
            'channel': channel,
            'uid': int(uid),
            'token': token,
            'expiresIn': token_ttl,
            'expiresAt': privilege_expire_time
        })
        
    except Exception as e:
        logger.error(f"Agora token generation error: {e}")
        return JsonResponse({'error': 'Failed to generate Agora token'}, status=500)


@csrf_exempt
@require_http_methods(["GET"])
def stream_token(request):
    """
    Generate Stream.io user token for chat
    GET /api/stream/token?userId=user123
    """
    if not STREAM_AVAILABLE:
        return JsonResponse({
            'error': 'Stream token service not available. Install stream-chat package.'
        }, status=500)
    
    try:
        # Get parameters
        user_id = request.GET.get('userId')
        
        if not user_id:
            return JsonResponse({'error': 'userId parameter required'}, status=400)
        
        # Get Stream configuration from settings
        stream_api_key = getattr(settings, 'STREAM_API_KEY', None)
        stream_api_secret = getattr(settings, 'STREAM_API_SECRET', None)
        
        if not stream_api_key or not stream_api_secret:
            return JsonResponse({'error': 'Stream API credentials not configured'}, status=500)
        
        # Initialize Stream client
        server_client = StreamChat(stream_api_key, stream_api_secret)
        
        # Token expiration (default 1 hour)
        token_ttl = int(getattr(settings, 'STREAM_TOKEN_TTL_SECONDS', 3600))
        expires_at = int(time.time()) + token_ttl
        
        # Create user token
        token = server_client.create_token(user_id, expires_at)
        
        return JsonResponse({
            'apiKey': stream_api_key,
            'userId': user_id,
            'token': token,
            'expiresIn': token_ttl,
            'expiresAt': expires_at
        })
        
    except Exception as e:
        logger.error(f"Stream token generation error: {e}")
        return JsonResponse({'error': 'Failed to generate Stream token'}, status=500)


@csrf_exempt
@require_http_methods(["GET"])
def token_status(request):
    """
    Check token service status and configuration
    GET /api/token/status
    """
    status = {
        'agora': {
            'available': AGORA_AVAILABLE,
            'app_id_configured': bool(getattr(settings, 'AGORA_APP_ID', None)),
            'certificate_configured': bool(getattr(settings, 'AGORA_APP_CERTIFICATE', None)),
        },
        'stream': {
            'available': STREAM_AVAILABLE,
            'api_key_configured': bool(getattr(settings, 'STREAM_API_KEY', None)),
            'api_secret_configured': bool(getattr(settings, 'STREAM_API_SECRET', None)),
        }
    }
    
    return JsonResponse(status)
