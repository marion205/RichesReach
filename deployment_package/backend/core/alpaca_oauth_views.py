"""
Alpaca OAuth Views
Handles OAuth flow endpoints for Alpaca Connect
"""
import json
import logging
from django.http import JsonResponse, HttpResponseRedirect
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from datetime import timedelta
from .alpaca_oauth_service import get_oauth_service
from .alpaca_trading_service import AlpacaTradingService

logger = logging.getLogger(__name__)


@csrf_exempt
@require_http_methods(["GET"])
def alpaca_oauth_initiate(request):
    """
    Initiate OAuth flow - redirect to Alpaca authorization page
    
    GET /api/auth/alpaca/initiate
    """
    try:
        oauth_service = get_oauth_service()
        
        # Generate CSRF protection state
        state = oauth_service.generate_state()
        
        # Store state in session for verification
        request.session['alpaca_oauth_state'] = state
        request.session['alpaca_oauth_redirect'] = request.GET.get('redirect_uri', '/trading')
        
        # Generate authorization URL
        redirect_uri = request.GET.get('redirect_uri') or oauth_service.redirect_uri
        auth_url = oauth_service.get_authorization_url(state, redirect_uri)
        
        logger.info(f"OAuth flow initiated for user {request.user.id if hasattr(request, 'user') else 'anonymous'}")
        
        return HttpResponseRedirect(auth_url)
    
    except Exception as e:
        logger.error(f"Failed to initiate OAuth flow: {e}")
        return JsonResponse({
            'error': 'Failed to initiate OAuth flow',
            'message': str(e)
        }, status=500)


@csrf_exempt
@require_http_methods(["GET"])
def alpaca_oauth_callback(request):
    """
    Handle OAuth callback from Alpaca
    
    GET /api/auth/alpaca/callback?code=...&state=...
    """
    try:
        code = request.GET.get('code')
        state = request.GET.get('state')
        error = request.GET.get('error')
        
        # Handle OAuth errors
        if error:
            error_description = request.GET.get('error_description', 'OAuth authorization failed')
            logger.error(f"OAuth error: {error} - {error_description}")
            redirect_uri = request.session.get('alpaca_oauth_redirect', '/trading')
            return HttpResponseRedirect(f"{redirect_uri}?error={error}&error_description={error_description}")
        
        if not code:
            return JsonResponse({
                'error': 'Missing authorization code'
            }, status=400)
        
        # Verify state (CSRF protection)
        stored_state = request.session.get('alpaca_oauth_state')
        if not state or state != stored_state:
            logger.error(f"Invalid OAuth state: expected {stored_state}, got {state}")
            return JsonResponse({
                'error': 'Invalid state parameter'
            }, status=400)
        
        # Clear state from session
        del request.session['alpaca_oauth_state']
        redirect_uri = request.session.pop('alpaca_oauth_redirect', '/trading')
        
        # Exchange code for tokens
        oauth_service = get_oauth_service()
        tokens = oauth_service.exchange_code_for_tokens(code)
        
        access_token = tokens.get('access_token')
        refresh_token = tokens.get('refresh_token')
        expires_in = tokens.get('expires_in', 3600)
        
        if not access_token:
            logger.error("No access token in OAuth response")
            return JsonResponse({
                'error': 'Failed to obtain access token'
            }, status=500)
        
        # Get user's Alpaca account info
        trading_service = AlpacaTradingService(access_token)
        account = trading_service.get_account()
        
        if not account:
            logger.error("Failed to fetch Alpaca account after OAuth")
            return JsonResponse({
                'error': 'Failed to fetch Alpaca account'
            }, status=500)
        
        # Store connection (you'll need to create AlpacaConnection model)
        # For now, we'll store in session or return to frontend
        if hasattr(request, 'user') and request.user.is_authenticated:
            # TODO: Create AlpacaConnection model and store tokens
            # AlpacaConnection.objects.create_or_update(
            #     user=request.user,
            #     alpaca_account_id=account.get('id'),
            #     access_token=encrypt(access_token),
            #     refresh_token=encrypt(refresh_token),
            #     token_expires_at=timezone.now() + timedelta(seconds=expires_in),
            # )
            logger.info(f"OAuth flow completed for user {request.user.id}, account {account.get('id')}")
        
        # Redirect to frontend with success
        return HttpResponseRedirect(f"{redirect_uri}?connected=true&account_id={account.get('id')}")
    
    except Exception as e:
        logger.error(f"OAuth callback error: {e}", exc_info=True)
        redirect_uri = request.session.get('alpaca_oauth_redirect', '/trading')
        return HttpResponseRedirect(f"{redirect_uri}?error=oauth_failed&message={str(e)}")


@csrf_exempt
@require_http_methods(["POST"])
@login_required
def alpaca_oauth_disconnect(request):
    """
    Disconnect Alpaca account (revoke tokens)
    
    POST /api/auth/alpaca/disconnect
    """
    try:
        # TODO: Get stored tokens from AlpacaConnection model
        # connection = AlpacaConnection.objects.get(user=request.user)
        # oauth_service = get_oauth_service()
        # oauth_service.revoke_token(connection.refresh_token, 'refresh_token')
        # connection.delete()
        
        return JsonResponse({
            'success': True,
            'message': 'Alpaca account disconnected'
        })
    
    except Exception as e:
        logger.error(f"Failed to disconnect Alpaca account: {e}")
        return JsonResponse({
            'error': 'Failed to disconnect account',
            'message': str(e)
        }, status=500)

