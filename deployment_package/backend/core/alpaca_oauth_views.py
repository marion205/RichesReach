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

try:
    from .models import AlpacaConnection
except ImportError:
    AlpacaConnection = None

try:
    from .broker_models import BrokerAccount
except ImportError:
    BrokerAccount = None


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
        request.session['alpaca_oauth_redirect'] = request.GET.get('redirect_uri', '/api/auth/alpaca/success')
        
        # Generate authorization URL
        redirect_uri = request.GET.get('redirect_uri') or oauth_service.redirect_uri
        auth_url = oauth_service.get_authorization_url(state, redirect_uri)
        
        user_id = 'anonymous'
        if getattr(request, 'user', None) and getattr(request.user, 'is_authenticated', False):
            user_id = getattr(request.user, 'id', 'anonymous')
        logger.info(f"OAuth flow initiated for user {user_id}")
        
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
            redirect_uri = request.session.get('alpaca_oauth_redirect', '/api/auth/alpaca/success')
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
        redirect_uri = request.session.pop('alpaca_oauth_redirect', '/api/auth/alpaca/success')
        
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
        
        # Store connection in DB and sync to BrokerAccount so app GraphQL (alpacaAccount) shows linked account
        if hasattr(request, 'user') and request.user.is_authenticated:
            alpaca_account_id = account.get('id', '')
            if AlpacaConnection:
                token_expires_at = timezone.now() + timedelta(seconds=int(expires_in or 3600))
                AlpacaConnection.objects.update_or_create(
                    user=request.user,
                    defaults={
                        'alpaca_account_id': alpaca_account_id,
                        'access_token': access_token,
                        'refresh_token': refresh_token or '',
                        'token_expires_at': token_expires_at,
                    }
                )
                logger.info(f"OAuth flow completed for user {request.user.id}, account {alpaca_account_id}")
            if BrokerAccount and alpaca_account_id:
                broker_account, _ = BrokerAccount.objects.get_or_create(
                    user=request.user,
                    defaults={'kyc_status': 'NOT_STARTED'}
                )
                updates = {}
                if broker_account.alpaca_account_id != alpaca_account_id:
                    updates['alpaca_account_id'] = alpaca_account_id
                    updates['status'] = account.get('status') or broker_account.status
                # Connect users already have an approved Alpaca account
                if broker_account.kyc_status != 'APPROVED':
                    updates['kyc_status'] = 'APPROVED'
                if updates:
                    for k, v in updates.items():
                        setattr(broker_account, k, v)
                    broker_account.save(update_fields=list(updates.keys()))
        
        # Redirect to frontend with success
        return HttpResponseRedirect(f"{redirect_uri}?connected=true&account_id={account.get('id')}")
    
    except Exception as e:
        logger.error(f"OAuth callback error: {e}", exc_info=True)
        redirect_uri = request.session.get('alpaca_oauth_redirect', '/api/auth/alpaca/success')
        return HttpResponseRedirect(f"{redirect_uri}?error=oauth_failed&message={str(e)}")


@csrf_exempt
@require_http_methods(["GET"])
def alpaca_oauth_success(request):
    """
    Success page shown after OAuth callback completes.
    Immediately deep-links back into the RichesReach app via com.richesreach.app://
    with the same query params, then shows a fallback message if the app doesn't open.

    GET /api/auth/alpaca/success?connected=true&account_id=...
    """
    from django.http import HttpResponse
    from urllib.parse import urlencode

    connected = request.GET.get('connected', '')
    account_id = request.GET.get('account_id', '')
    error = request.GET.get('error', '')
    message = request.GET.get('message', '')

    # Build deep-link URL that mirrors the query params back into the app
    deep_link_params = {}
    if connected:
        deep_link_params['connected'] = connected
    if account_id:
        deep_link_params['account_id'] = account_id
    if error:
        deep_link_params['error'] = error
    if message:
        deep_link_params['message'] = message

    qs = urlencode(deep_link_params)
    deep_link = f"com.richesreach.app://auth/alpaca/callback{'?' + qs if qs else ''}"

    if error:
        heading = "Connection Failed"
        body_text = f"Error: {error}. Returning to RichesReach&hellip;"
        status_color = "#e53e3e"
    elif connected == 'true':
        heading = "Alpaca Connected ✓"
        body_text = "Account linked successfully. Returning to RichesReach&hellip;"
        status_color = "#38a169"
    else:
        heading = "Alpaca OAuth"
        body_text = "Returning to RichesReach&hellip;"
        status_color = "#3182ce"

    html = f"""<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>RichesReach – Alpaca</title>
  <style>
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
      background: #f7f8fa;
      display: flex;
      align-items: center;
      justify-content: center;
      min-height: 100vh;
      padding: 24px;
    }}
    .card {{
      background: #fff;
      border-radius: 16px;
      padding: 40px 32px;
      max-width: 360px;
      width: 100%;
      text-align: center;
      box-shadow: 0 4px 24px rgba(0,0,0,0.08);
    }}
    .icon {{
      font-size: 48px;
      margin-bottom: 16px;
    }}
    h1 {{
      font-size: 22px;
      font-weight: 700;
      color: {status_color};
      margin-bottom: 12px;
    }}
    p {{
      font-size: 15px;
      color: #555;
      line-height: 1.5;
      margin-bottom: 24px;
    }}
    .open-btn {{
      display: inline-block;
      background: #007AFF;
      color: #fff;
      font-size: 16px;
      font-weight: 600;
      padding: 14px 28px;
      border-radius: 10px;
      text-decoration: none;
      margin-bottom: 12px;
    }}
    .hint {{
      font-size: 13px;
      color: #aaa;
    }}
  </style>
</head>
<body>
  <div class="card">
    <div class="icon">{'✅' if connected == 'true' and not error else '❌' if error else '🔗'}</div>
    <h1>{heading}</h1>
    <p>{body_text}</p>
    <div id="manual" style="display:none">
      <a class="open-btn" href="{deep_link}">Open RichesReach</a>
      <p class="hint">You can close this window if the app is already open.</p>
    </div>
  </div>
  <script>
    // DOM is ready — attempt deep-link now
    window.location.href = "{deep_link}";

    // After 1.5 s, if the app hasn't opened, show the manual button
    setTimeout(function() {{
      var btn = document.getElementById('manual');
      if (btn) btn.style.display = 'block';
    }}, 1500);
  </script>
</body>
</html>"""

    return HttpResponse(html)


@csrf_exempt
@require_http_methods(["POST"])
@login_required
def alpaca_oauth_disconnect(request):
    """
    Disconnect Alpaca account (revoke tokens)
    
    POST /api/auth/alpaca/disconnect
    """
    try:
        if AlpacaConnection:
            try:
                connection = AlpacaConnection.objects.get(user=request.user)
                oauth_service = get_oauth_service()
                refresh_token = connection.get_decrypted_refresh_token()
                if refresh_token and getattr(oauth_service, 'revoke_token', None):
                    try:
                        oauth_service.revoke_token(refresh_token, 'refresh_token')
                    except Exception as revoke_err:
                        logger.warning(f"Alpaca revoke token failed: {revoke_err}")
                connection.delete()
            except AlpacaConnection.DoesNotExist:
                pass
        if BrokerAccount:
            try:
                broker_account = BrokerAccount.objects.get(user=request.user)
                if broker_account.alpaca_account_id:
                    broker_account.alpaca_account_id = None
                    broker_account.save(update_fields=['alpaca_account_id'])
            except BrokerAccount.DoesNotExist:
                pass
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

