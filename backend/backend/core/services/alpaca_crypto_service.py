"""
Alpaca Crypto API Service
Handles cryptocurrency trading, balances, and on-chain operations through Alpaca's Crypto API
"""
import os
import requests
import logging
import json
from typing import Dict, List, Optional, Any
from datetime import datetime
from django.conf import settings

try:
    import websocket
    WEBSOCKET_AVAILABLE = True
except ImportError:
    WEBSOCKET_AVAILABLE = False
    websocket = None

logger = logging.getLogger(__name__)

class AlpacaCryptoService:
    """Service for interacting with Alpaca Crypto API"""
    
    def __init__(self):
        # Try Django settings first, then environment variables
        self.api_key = getattr(settings, 'ALPACA_CRYPTO_API_KEY', os.getenv('ALPACA_CRYPTO_API_KEY', ''))
        self.secret_key = getattr(settings, 'ALPACA_CRYPTO_SECRET_KEY', os.getenv('ALPACA_CRYPTO_SECRET_KEY', ''))
        self.base_url = getattr(settings, 'ALPACA_CRYPTO_BASE_URL', os.getenv('ALPACA_CRYPTO_BASE_URL', 'https://api.sandbox.alpaca.markets'))
        self.data_url = getattr(settings, 'ALPACA_CRYPTO_DATA_URL', os.getenv('ALPACA_CRYPTO_DATA_URL', 'https://data.sandbox.alpaca.markets'))
        self.environment = getattr(settings, 'ALPACA_ENVIRONMENT', os.getenv('ALPACA_ENVIRONMENT', 'sandbox'))
        
        if not self.api_key or not self.secret_key:
            logger.warning("Alpaca Crypto API credentials not configured")
        
        self.headers = {
            'APCA-API-KEY-ID': self.api_key,
            'APCA-API-SECRET-KEY': self.secret_key,
            'Content-Type': 'application/json'
        }
        
        # Supported states for crypto trading (as of Oct 2025)
        self.supported_states = [
            'AZ', 'CA', 'CT', 'GA', 'ID', 'IL', 'IN', 'IA', 'KS', 'KY',
            'ME', 'MD', 'MA', 'MI', 'MS', 'MO', 'MT', 'NE', 'NC', 'ND',
            'OH', 'RI', 'SC', 'SD', 'UT', 'VT', 'WA', 'WV'
        ]
    
    def _make_request(self, method: str, endpoint: str, data: Optional[Dict] = None) -> Dict:
        """Make HTTP request to Alpaca Crypto API"""
        url = f"{self.base_url}{endpoint}"
        
        try:
            if method.upper() == 'GET':
                response = requests.get(url, headers=self.headers)
            elif method.upper() == 'POST':
                response = requests.post(url, headers=self.headers, json=data)
            elif method.upper() == 'PUT':
                response = requests.put(url, headers=self.headers, json=data)
            elif method.upper() == 'DELETE':
                response = requests.delete(url, headers=self.headers)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")
            
            response.raise_for_status()
            return response.json() if response.content else {}
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Alpaca Crypto API request failed: {e}")
            if hasattr(e, 'response') and e.response is not None:
                logger.error(f"Response: {e.response.text}")
            raise
    
    # =============================================================================
    # CRYPTO ASSETS & MARKET DATA
    # =============================================================================
    
    def get_crypto_assets(self, status: str = 'active') -> List[Dict]:
        """Get available crypto assets"""
        endpoint = f"/v2/assets"
        params = {'asset_class': 'crypto', 'status': status}
        
        url = f"{self.base_url}{endpoint}"
        url += '?' + '&'.join([f"{k}={v}" for k, v in params.items()])
        
        response = requests.get(url, headers=self.headers)
        response.raise_for_status()
        data = response.json()
        return data if isinstance(data, list) else data.get('assets', [])
    
    def get_crypto_asset(self, symbol: str) -> Dict:
        """Get specific crypto asset details"""
        endpoint = f"/v2/assets/{symbol}"
        return self._make_request('GET', endpoint)
    
    def get_crypto_quotes(self, symbols: List[str]) -> Dict:
        """Get latest quotes for crypto symbols"""
        endpoint = f"/v2/crypto/quotes/latest"
        params = {'symbols': ','.join(symbols)}
        
        url = f"{self.data_url}{endpoint}"
        url += '?' + '&'.join([f"{k}={v}" for k, v in params.items()])
        
        response = requests.get(url, headers=self.headers)
        response.raise_for_status()
        return response.json()
    
    def get_crypto_bars(self, symbol: str, timeframe: str = '1Min', limit: int = 100) -> Dict:
        """Get historical bars for crypto symbol"""
        endpoint = f"/v2/crypto/bars"
        params = {
            'symbols': symbol,
            'timeframe': timeframe,
            'limit': limit
        }
        
        url = f"{self.data_url}{endpoint}"
        url += '?' + '&'.join([f"{k}={v}" for k, v in params.items()])
        
        response = requests.get(url, headers=self.headers)
        response.raise_for_status()
        return response.json()
    
    # =============================================================================
    # CRYPTO TRADING OPERATIONS
    # =============================================================================
    
    def create_crypto_order(self, order_data: Dict) -> Dict:
        """Create a crypto trading order"""
        endpoint = "/v2/crypto/orders"
        return self._make_request('POST', endpoint, order_data)
    
    def get_crypto_orders(self, status: Optional[str] = None, limit: int = 100) -> List[Dict]:
        """Get crypto orders"""
        endpoint = "/v2/crypto/orders"
        params = {'limit': limit}
        if status:
            params['status'] = status
        
        url = f"{self.base_url}{endpoint}"
        url += '?' + '&'.join([f"{k}={v}" for k, v in params.items()])
        
        response = requests.get(url, headers=self.headers)
        response.raise_for_status()
        data = response.json()
        return data if isinstance(data, list) else data.get('orders', [])
    
    def get_crypto_order(self, order_id: str) -> Dict:
        """Get specific crypto order"""
        endpoint = f"/v2/crypto/orders/{order_id}"
        return self._make_request('GET', endpoint)
    
    def cancel_crypto_order(self, order_id: str) -> Dict:
        """Cancel a crypto order"""
        endpoint = f"/v2/crypto/orders/{order_id}"
        return self._make_request('DELETE', endpoint)
    
    # =============================================================================
    # CRYPTO ACCOUNT & BALANCES
    # =============================================================================
    
    def get_crypto_account(self) -> Dict:
        """Get crypto account details"""
        endpoint = "/v2/crypto/account"
        return self._make_request('GET', endpoint)
    
    def get_crypto_positions(self) -> List[Dict]:
        """Get crypto positions"""
        endpoint = "/v2/crypto/positions"
        response = self._make_request('GET', endpoint)
        return response if isinstance(response, list) else response.get('positions', [])
    
    def get_crypto_position(self, symbol: str) -> Dict:
        """Get specific crypto position"""
        endpoint = f"/v2/crypto/positions/{symbol}"
        return self._make_request('GET', endpoint)
    
    def close_crypto_position(self, symbol: str, qty: Optional[str] = None) -> Dict:
        """Close a crypto position"""
        endpoint = f"/v2/crypto/positions/{symbol}"
        data = {}
        if qty:
            data['qty'] = qty
        
        return self._make_request('DELETE', endpoint, data if data else None)
    
    # =============================================================================
    # CRYPTO ACTIVITIES & HISTORY
    # =============================================================================
    
    def get_crypto_activities(self, activity_type: Optional[str] = None, limit: int = 100) -> List[Dict]:
        """Get crypto account activities"""
        endpoint = "/v2/crypto/account/activities"
        params = {'limit': limit}
        if activity_type:
            params['activity_type'] = activity_type
        
        url = f"{self.base_url}{endpoint}"
        url += '?' + '&'.join([f"{k}={v}" for k, v in params.items()])
        
        response = requests.get(url, headers=self.headers)
        response.raise_for_status()
        data = response.json()
        return data if isinstance(data, list) else data.get('activities', [])
    
    def get_crypto_portfolio_history(self, period: str = "1M") -> Dict:
        """Get crypto portfolio history"""
        endpoint = f"/v2/crypto/account/portfolio/history"
        params = {'period': period}
        
        url = f"{self.base_url}{endpoint}"
        url += '?' + '&'.join([f"{k}={v}" for k, v in params.items()])
        
        response = requests.get(url, headers=self.headers)
        response.raise_for_status()
        return response.json()
    
    # =============================================================================
    # ON-CHAIN TRANSFERS (where supported)
    # =============================================================================
    
    def create_crypto_transfer(self, transfer_data: Dict) -> Dict:
        """Create on-chain crypto transfer"""
        endpoint = "/v2/crypto/transfers"
        return self._make_request('POST', endpoint, transfer_data)
    
    def get_crypto_transfers(self, status: Optional[str] = None) -> List[Dict]:
        """Get crypto transfer history"""
        endpoint = "/v2/crypto/transfers"
        params = {}
        if status:
            params['status'] = status
        
        url = f"{self.base_url}{endpoint}"
        url += '?' + '&'.join([f"{k}={v}" for k, v in params.items()])
        
        response = requests.get(url, headers=self.headers)
        response.raise_for_status()
        data = response.json()
        return data if isinstance(data, list) else data.get('transfers', [])
    
    def get_crypto_transfer(self, transfer_id: str) -> Dict:
        """Get specific crypto transfer"""
        endpoint = f"/v2/crypto/transfers/{transfer_id}"
        return self._make_request('GET', endpoint)
    
    # =============================================================================
    # WEBSOCKET STREAMS
    # =============================================================================
    
    def connect_websocket(self, symbols: List[str], stream_types: List[str] = ['quotes']):
        """Connect to crypto WebSocket stream"""
        if not WEBSOCKET_AVAILABLE:
            raise ImportError("websocket-client package not available")
        
        ws_url = "wss://stream.data.alpaca.markets/v1beta3/crypto/us"
        
        auth_message = {
            "action": "auth",
            "key": self.api_key,
            "secret": self.secret_key
        }
        
        subscribe_message = {
            "action": "subscribe",
            "quotes": symbols,
            "trades": symbols if 'trades' in stream_types else [],
            "orderbooks": symbols if 'orderbooks' in stream_types else []
        }
        
        def on_message(ws, message):
            try:
                data = json.loads(message)
                logger.info(f"Crypto WebSocket message: {data}")
            except Exception as e:
                logger.error(f"WebSocket message error: {e}")
        
        def on_error(ws, error):
            logger.error(f"Crypto WebSocket error: {error}")
        
        def on_close(ws, close_status_code, close_msg):
            logger.info("Crypto WebSocket connection closed")
        
        def on_open(ws):
            logger.info("Crypto WebSocket connection opened")
            ws.send(json.dumps(auth_message))
            ws.send(json.dumps(subscribe_message))
        
        ws = websocket.WebSocketApp(
            ws_url,
            on_message=on_message,
            on_error=on_error,
            on_close=on_close,
            on_open=on_open
        )
        
        return ws
    
    # =============================================================================
    # UTILITY METHODS
    # =============================================================================
    
    def is_connected(self) -> bool:
        """Check if Alpaca Crypto API is properly connected"""
        try:
            self.get_crypto_account()
            return True
        except Exception as e:
            logger.error(f"Alpaca Crypto connection check failed: {e}")
            return False
    
    def is_crypto_eligible(self, user_state: str) -> bool:
        """Check if user's state supports crypto trading"""
        return user_state.upper() in self.supported_states
    
    def get_supported_crypto_pairs(self) -> List[str]:
        """Get list of supported crypto trading pairs"""
        try:
            assets = self.get_crypto_assets()
            return [asset['symbol'] for asset in assets if asset.get('tradable', False)]
        except Exception as e:
            logger.error(f"Failed to get crypto pairs: {e}")
            return []
    
    def calculate_crypto_fee(self, order_value: float, is_maker: bool = False) -> float:
        """Calculate crypto trading fee based on tiered structure"""
        # Alpaca Crypto fee structure (as of Oct 2025)
        if is_maker:
            return order_value * 0.0015  # 15 bps for makers
        else:
            return order_value * 0.0025  # 25 bps for takers
    
    def validate_crypto_order(self, order_data: Dict) -> Dict:
        """Validate crypto order parameters"""
        errors = []
        
        # Check required fields
        required_fields = ['symbol', 'side', 'type']
        for field in required_fields:
            if field not in order_data:
                errors.append(f"Missing required field: {field}")
        
        # Validate symbol format (e.g., BTC/USD)
        if 'symbol' in order_data:
            symbol = order_data['symbol']
            if '/' not in symbol or len(symbol.split('/')) != 2:
                errors.append("Invalid symbol format. Use format like BTC/USD")
        
        # Validate order type
        valid_types = ['market', 'limit', 'stop', 'stop_limit']
        if 'type' in order_data and order_data['type'] not in valid_types:
            errors.append(f"Invalid order type. Must be one of: {valid_types}")
        
        # Validate side
        valid_sides = ['buy', 'sell']
        if 'side' in order_data and order_data['side'] not in valid_sides:
            errors.append(f"Invalid side. Must be one of: {valid_sides}")
        
        # Check order value limits (max $200k per order)
        if 'notional' in order_data:
            try:
                notional = float(order_data['notional'])
                if notional > 200000:
                    errors.append("Order value exceeds maximum limit of $200,000")
            except ValueError:
                errors.append("Invalid notional value")
        
        return {
            'valid': len(errors) == 0,
            'errors': errors
        }
