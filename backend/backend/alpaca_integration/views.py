"""
Alpaca Integration Views
"""

from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.views import View
from django.conf import settings
import json
import uuid

from .services import AlpacaOAuthService, AlpacaAPIService
from core.models.alpaca_models import AlpacaAccount, AlpacaPosition, AlpacaOrder
from .models import AlpacaOAuthToken


class AlpacaOAuthView(View):
    """Handle Alpaca OAuth Connect flow"""
    
    def get(self, request):
        """Initiate OAuth flow"""
        if not request.user.is_authenticated:
            return JsonResponse({'error': 'Authentication required'}, status=200)
        
        # Generate state parameter for security
        state = str(uuid.uuid4())
        request.session['alpaca_oauth_state'] = state
        
        oauth_service = AlpacaOAuthService()
        auth_url = oauth_service.get_authorization_url(state=state)
        
        return JsonResponse({
            'authorization_url': auth_url,
            'state': state
        })


class AlpacaCallbackView(View):
    """Handle OAuth callback"""
    
    def get(self, request):
        """Process OAuth callback"""
        if not request.user.is_authenticated:
            return JsonResponse({'error': 'Authentication required'}, status=200)
        
        code = request.GET.get('code')
        state = request.GET.get('state')
        error = request.GET.get('error')
        
        if error:
            return JsonResponse({'error': f'OAuth error: {error}'}, status=400)
        
        if not code:
            return JsonResponse({'error': 'Authorization code not provided'}, status=400)
        
        # Verify state parameter
        stored_state = request.session.get('alpaca_oauth_state')
        if state != stored_state:
            return JsonResponse({'error': 'Invalid state parameter'}, status=400)
        
        try:
            oauth_service = AlpacaOAuthService()
            token_data = oauth_service.exchange_code_for_token(code)
            oauth_service.store_oauth_token(request.user, token_data)
            
            # Clear state from session
            if 'alpaca_oauth_state' in request.session:
                del request.session['alpaca_oauth_state']
            
            return JsonResponse({
                'success': True,
                'message': 'Alpaca account connected successfully'
            })
            
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)


@method_decorator(csrf_exempt, name='dispatch')
class AlpacaAccountView(View):
    """Handle Alpaca account operations"""
    
    def get(self, request):
        """Get account information"""
        if not request.user.is_authenticated:
            return JsonResponse({'error': 'Authentication required'}, status=200)
        
        try:
            api_service = AlpacaAPIService(user=request.user)
            account_data = api_service.get_account()
            
            return JsonResponse({
                'success': True,
                'account': account_data
            })
            
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)


@method_decorator(csrf_exempt, name='dispatch')
class AlpacaPositionsView(View):
    """Handle Alpaca positions"""
    
    def get(self, request):
        """Get current positions"""
        if not request.user.is_authenticated:
            return JsonResponse({'error': 'Authentication required'}, status=200)
        
        try:
            api_service = AlpacaAPIService(user=request.user)
            positions_data = api_service.get_positions()
            
            return JsonResponse({
                'success': True,
                'positions': positions_data
            })
            
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)


@method_decorator(csrf_exempt, name='dispatch')
class AlpacaOrdersView(View):
    """Handle Alpaca orders"""
    
    def get(self, request):
        """Get orders"""
        if not request.user.is_authenticated:
            return JsonResponse({'error': 'Authentication required'}, status=200)
        
        try:
            api_service = AlpacaAPIService(user=request.user)
            status = request.GET.get('status')
            limit = int(request.GET.get('limit', 100))
            
            orders_data = api_service.get_orders(status=status, limit=limit)
            
            return JsonResponse({
                'success': True,
                'orders': orders_data
            })
            
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    
    def post(self, request):
        """Place a new order"""
        if not request.user.is_authenticated:
            return JsonResponse({'error': 'Authentication required'}, status=401)
        
        try:
            data = json.loads(request.body)
            
            required_fields = ['symbol', 'qty', 'side', 'order_type']
            for field in required_fields:
                if field not in data:
                    return JsonResponse({'error': f'Missing required field: {field}'}, status=400)
            
            api_service = AlpacaAPIService(user=request.user)
            order_data = api_service.place_order(
                symbol=data['symbol'],
                qty=data['qty'],
                side=data['side'],
                order_type=data['order_type'],
                time_in_force=data.get('time_in_force', 'day'),
                limit_price=data.get('limit_price'),
                stop_price=data.get('stop_price'),
                trail_price=data.get('trail_price'),
                trail_percent=data.get('trail_percent'),
            )
            
            return JsonResponse({
                'success': True,
                'order': order_data
            })
            
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON'}, status=400)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)


@method_decorator(csrf_exempt, name='dispatch')
class AlpacaOrderDetailView(View):
    """Handle individual order operations"""
    
    def delete(self, request, order_id):
        """Cancel an order"""
        if not request.user.is_authenticated:
            return JsonResponse({'error': 'Authentication required'}, status=401)
        
        try:
            api_service = AlpacaAPIService(user=request.user)
            success = api_service.cancel_order(order_id)
            
            if success:
                return JsonResponse({
                    'success': True,
                    'message': 'Order canceled successfully'
                })
            else:
                return JsonResponse({'error': 'Failed to cancel order'}, status=500)
                
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)


@method_decorator(csrf_exempt, name='dispatch')
class AlpacaMarketDataView(View):
    """Handle market data requests"""
    
    def get(self, request):
        """Get market data for symbols"""
        if not request.user.is_authenticated:
            return JsonResponse({'error': 'Authentication required'}, status=200)
        
        try:
            symbols = request.GET.get('symbols', '').split(',')
            if not symbols or symbols == ['']:
                return JsonResponse({'error': 'Symbols parameter required'}, status=400)
            
            timeframe = request.GET.get('timeframe', '1Day')
            start = request.GET.get('start')
            end = request.GET.get('end')
            
            api_service = AlpacaAPIService(user=request.user)
            market_data = api_service.get_market_data(
                symbols=symbols,
                timeframe=timeframe,
                start=start,
                end=end
            )
            
            return JsonResponse({
                'success': True,
                'data': market_data
            })
            
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)


# Legacy function-based views for compatibility
@login_required
def alpaca_connect(request):
    """Initiate Alpaca Connect OAuth flow"""
    oauth_service = AlpacaOAuthService()
    auth_url = oauth_service.get_authorization_url()
    
    return redirect(auth_url)


@login_required
def alpaca_callback(request):
    """Handle OAuth callback"""
    code = request.GET.get('code')
    error = request.GET.get('error')
    
    if error:
        return render(request, 'alpaca_integration/error.html', {
            'error': f'OAuth error: {error}'
        })
    
    if not code:
        return render(request, 'alpaca_integration/error.html', {
            'error': 'Authorization code not provided'
        })
    
    try:
        oauth_service = AlpacaOAuthService()
        token_data = oauth_service.exchange_code_for_token(code)
        oauth_service.store_oauth_token(request.user, token_data)
        
        return render(request, 'alpaca_integration/success.html', {
            'message': 'Alpaca account connected successfully!'
        })
        
    except Exception as e:
        return render(request, 'alpaca_integration/error.html', {
            'error': str(e)
        })