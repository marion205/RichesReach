"""
Alpaca Integration Services
"""

import requests
import json
from datetime import datetime, timedelta
from django.conf import settings
from django.utils import timezone
from core.models.alpaca_models import AlpacaAccount, AlpacaPosition, AlpacaOrder
from core.models import User
from .models import AlpacaOAuthToken


class AlpacaOAuthService:
    """Service for handling Alpaca OAuth Connect integration"""
    
    def __init__(self):
        self.client_id = settings.ALPACA_CLIENT_ID
        self.client_secret = settings.ALPACA_CLIENT_SECRET
        self.redirect_uri = settings.ALPACA_REDIRECT_URI
        self.base_url = settings.ALPACA_BASE_URL
        
    def get_authorization_url(self, state=None):
        """Generate OAuth authorization URL"""
        params = {
            'response_type': 'code',
            'client_id': self.client_id,
            'redirect_uri': self.redirect_uri,
            'scope': 'trading:read trading:write account:read',
        }
        
        if state:
            params['state'] = state
            
        auth_url = f"{self.base_url}/oauth/authorize"
        query_string = '&'.join([f"{k}={v}" for k, v in params.items()])
        
        return f"{auth_url}?{query_string}"
    
    def exchange_code_for_token(self, code):
        """Exchange authorization code for access token"""
        token_url = f"{self.base_url}/oauth/token"
        
        data = {
            'grant_type': 'authorization_code',
            'code': code,
            'client_id': self.client_id,
            'client_secret': self.client_secret,
            'redirect_uri': self.redirect_uri,
        }
        
        response = requests.post(token_url, data=data)
        
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(f"Failed to exchange code for token: {response.text}")
    
    def refresh_access_token(self, refresh_token):
        """Refresh access token using refresh token"""
        token_url = f"{self.base_url}/oauth/token"
        
        data = {
            'grant_type': 'refresh_token',
            'refresh_token': refresh_token,
            'client_id': self.client_id,
            'client_secret': self.client_secret,
        }
        
        response = requests.post(token_url, data=data)
        
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(f"Failed to refresh token: {response.text}")
    
    def store_oauth_token(self, user, token_data):
        """Store OAuth token in database"""
        expires_at = timezone.now() + timedelta(seconds=token_data.get('expires_in', 3600))
        
        token, created = AlpacaOAuthToken.objects.update_or_create(
            user=user,
            defaults={
                'access_token': token_data['access_token'],
                'refresh_token': token_data.get('refresh_token', ''),
                'token_type': token_data.get('token_type', 'Bearer'),
                'expires_at': expires_at,
                'scope': token_data.get('scope', ''),
            }
        )
        
        return token


class AlpacaAPIService:
    """Service for interacting with Alpaca API"""
    
    def __init__(self, user=None):
        self.user = user
        self.base_url = settings.ALPACA_BASE_URL
        self.data_url = settings.ALPACA_DATA_URL
        
    def get_headers(self):
        """Get authorization headers for API requests"""
        if not self.user:
            raise Exception("User required for API requests")
            
        try:
            token = AlpacaOAuthToken.objects.get(user=self.user)
            
            # Check if token is expired and refresh if needed
            if token.expires_at <= timezone.now():
                oauth_service = AlpacaOAuthService()
                new_token_data = oauth_service.refresh_access_token(token.refresh_token)
                token = oauth_service.store_oauth_token(self.user, new_token_data)
            
            return {
                'Authorization': f"{token.token_type} {token.access_token}",
                'Content-Type': 'application/json',
            }
        except AlpacaOAuthToken.DoesNotExist:
            raise Exception("No OAuth token found for user")
    
    def get_account(self):
        """Get account information"""
        url = f"{self.base_url}/v1/account"
        headers = self.get_headers()
        
        response = requests.get(url, headers=headers)
        
        if response.status_code == 200:
            account_data = response.json()
            
            # Store/update account information
            account, created = AlpacaAccount.objects.update_or_create(
                user=self.user,
                defaults={
                    'alpaca_account_id': account_data['id'],
                    'account_number': account_data.get('account_number', ''),
                    'status': account_data['status'],
                    'currency': account_data['currency'],
                    'buying_power': float(account_data['buying_power']),
                    'cash': float(account_data['cash']),
                    'portfolio_value': float(account_data['portfolio_value']),
                }
            )
            
            return account_data
        else:
            raise Exception(f"Failed to get account: {response.text}")
    
    def get_positions(self):
        """Get current positions"""
        url = f"{self.base_url}/v1/positions"
        headers = self.get_headers()
        
        response = requests.get(url, headers=headers)
        
        if response.status_code == 200:
            positions_data = response.json()
            
            # Store/update positions
            for position_data in positions_data:
                AlpacaPosition.objects.update_or_create(
                    user=self.user,
                    symbol=position_data['symbol'],
                    defaults={
                        'qty': float(position_data['qty']),
                        'side': position_data['side'],
                        'market_value': float(position_data['market_value']),
                        'cost_basis': float(position_data['cost_basis']),
                        'unrealized_pl': float(position_data['unrealized_pl']),
                        'unrealized_plpc': float(position_data['unrealized_plpc']),
                        'current_price': float(position_data['current_price']),
                    }
                )
            
            return positions_data
        else:
            raise Exception(f"Failed to get positions: {response.text}")
    
    def get_orders(self, status=None, limit=100):
        """Get orders"""
        url = f"{self.base_url}/v1/orders"
        headers = self.get_headers()
        params = {'limit': limit}
        
        if status:
            params['status'] = status
        
        response = requests.get(url, headers=headers, params=params)
        
        if response.status_code == 200:
            orders_data = response.json()
            
            # Store/update orders
            for order_data in orders_data:
                AlpacaOrder.objects.update_or_create(
                    user=self.user,
                    alpaca_order_id=order_data['id'],
                    defaults={
                        'symbol': order_data['symbol'],
                        'qty': float(order_data['qty']),
                        'side': order_data['side'],
                        'order_type': order_data['order_type'],
                        'status': order_data['status'],
                        'limit_price': float(order_data.get('limit_price', 0)) if order_data.get('limit_price') else None,
                        'stop_price': float(order_data.get('stop_price', 0)) if order_data.get('stop_price') else None,
                        'filled_qty': float(order_data.get('filled_qty', 0)),
                        'filled_avg_price': float(order_data.get('filled_avg_price', 0)) if order_data.get('filled_avg_price') else None,
                        'submitted_at': datetime.fromisoformat(order_data['submitted_at'].replace('Z', '+00:00')),
                    }
                )
            
            return orders_data
        else:
            raise Exception(f"Failed to get orders: {response.text}")
    
    def place_order(self, symbol, qty, side, order_type, time_in_force='day', **kwargs):
        """Place a new order"""
        url = f"{self.base_url}/v1/orders"
        headers = self.get_headers()
        
        data = {
            'symbol': symbol,
            'qty': str(qty),
            'side': side,
            'type': order_type,
            'time_in_force': time_in_force,
        }
        
        # Add optional parameters
        if 'limit_price' in kwargs:
            data['limit_price'] = str(kwargs['limit_price'])
        if 'stop_price' in kwargs:
            data['stop_price'] = str(kwargs['stop_price'])
        if 'trail_price' in kwargs:
            data['trail_price'] = str(kwargs['trail_price'])
        if 'trail_percent' in kwargs:
            data['trail_percent'] = str(kwargs['trail_percent'])
        
        response = requests.post(url, headers=headers, json=data)
        
        if response.status_code == 201:
            order_data = response.json()
            
            # Store the new order
            AlpacaOrder.objects.create(
                user=self.user,
                alpaca_order_id=order_data['id'],
                symbol=order_data['symbol'],
                qty=float(order_data['qty']),
                side=order_data['side'],
                order_type=order_data['order_type'],
                status=order_data['status'],
                limit_price=float(order_data.get('limit_price', 0)) if order_data.get('limit_price') else None,
                stop_price=float(order_data.get('stop_price', 0)) if order_data.get('stop_price') else None,
                filled_qty=float(order_data.get('filled_qty', 0)),
                filled_avg_price=float(order_data.get('filled_avg_price', 0)) if order_data.get('filled_avg_price') else None,
                submitted_at=datetime.fromisoformat(order_data['submitted_at'].replace('Z', '+00:00')),
            )
            
            return order_data
        else:
            raise Exception(f"Failed to place order: {response.text}")
    
    def cancel_order(self, order_id):
        """Cancel an order"""
        url = f"{self.base_url}/v1/orders/{order_id}"
        headers = self.get_headers()
        
        response = requests.delete(url, headers=headers)
        
        if response.status_code == 204:
            # Update order status in database
            try:
                order = AlpacaOrder.objects.get(user=self.user, alpaca_order_id=order_id)
                order.status = 'canceled'
                order.save()
            except AlpacaOrder.DoesNotExist:
                pass
            
            return True
        else:
            raise Exception(f"Failed to cancel order: {response.text}")
    
    def get_market_data(self, symbols, timeframe='1Day', start=None, end=None):
        """Get market data for symbols"""
        url = f"{self.data_url}/v2/stocks/bars"
        headers = self.get_headers()
        
        params = {
            'symbols': ','.join(symbols),
            'timeframe': timeframe,
        }
        
        if start:
            params['start'] = start
        if end:
            params['end'] = end
        
        response = requests.get(url, headers=headers, params=params)
        
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(f"Failed to get market data: {response.text}")
