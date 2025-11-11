"""
Alpaca Broker API Service
Handles all interactions with Alpaca Broker API for account management, KYC, orders, positions, etc.
"""
import os
import requests
import hmac
import hashlib
import base64
import logging
from typing import Dict, Optional, List, Any
from datetime import datetime, time
from django.utils import timezone
from django.conf import settings

logger = logging.getLogger(__name__)


class AlpacaBrokerService:
    """Service for interacting with Alpaca Broker API"""
    
    def __init__(self):
        self.api_key = os.getenv('ALPACA_BROKER_API_KEY')
        self.api_secret = os.getenv('ALPACA_BROKER_API_SECRET')
        self.base_url = os.getenv('ALPACA_BROKER_BASE_URL', 'https://broker-api.sandbox.alpaca.markets')
        self.webhook_secret = os.getenv('ALPACA_WEBHOOK_SECRET', '')
        
        if not self.api_key or not self.api_secret:
            logger.warning("Alpaca Broker API credentials not configured")
    
    def _get_headers(self) -> Dict[str, str]:
        """Get authentication headers for API requests"""
        return {
            'APCA-API-KEY-ID': self.api_key,
            'APCA-API-SECRET-KEY': self.api_secret,
            'Content-Type': 'application/json',
        }
    
    def _make_request(
        self, 
        method: str, 
        endpoint: str, 
        data: Optional[Dict] = None,
        params: Optional[Dict] = None
    ) -> Optional[Dict]:
        """Make authenticated request to Alpaca Broker API"""
        if not self.api_key or not self.api_secret:
            logger.error("Alpaca Broker API credentials not configured")
            return None
        
        url = f"{self.base_url}{endpoint}"
        headers = self._get_headers()
        
        try:
            if method.upper() == 'GET':
                response = requests.get(url, headers=headers, params=params, timeout=30)
            elif method.upper() == 'POST':
                response = requests.post(url, headers=headers, json=data, timeout=30)
            elif method.upper() == 'PATCH':
                response = requests.patch(url, headers=headers, json=data, timeout=30)
            elif method.upper() == 'DELETE':
                response = requests.delete(url, headers=headers, timeout=30)
            else:
                logger.error(f"Unsupported HTTP method: {method}")
                return None
            
            response.raise_for_status()
            return response.json() if response.content else {}
        
        except requests.exceptions.HTTPError as e:
            error_detail = e.response.json() if e.response.content else {}
            logger.error(f"Alpaca API HTTP error: {e} - {error_detail}")
            return {'error': str(e), 'detail': error_detail}
        
        except requests.exceptions.RequestException as e:
            logger.error(f"Alpaca API request error: {e}")
            return {'error': str(e)}
    
    def verify_webhook_signature(self, payload: str, signature: str) -> bool:
        """Verify HMAC signature from Alpaca webhook"""
        if not self.webhook_secret:
            logger.warning("Webhook secret not configured, skipping signature verification")
            return True
        
        try:
            expected_signature = hmac.new(
                self.webhook_secret.encode('utf-8'),
                payload.encode('utf-8'),
                hashlib.sha256
            ).hexdigest()
            
            return hmac.compare_digest(expected_signature, signature)
        except Exception as e:
            logger.error(f"Error verifying webhook signature: {e}")
            return False
    
    # Account Management
    def create_account(self, account_data: Dict) -> Optional[Dict]:
        """Create a new brokerage account via Broker API"""
        return self._make_request('POST', '/v1/accounts', data=account_data)
    
    def get_account(self, account_id: str) -> Optional[Dict]:
        """Get account details"""
        return self._make_request('GET', f'/v1/accounts/{account_id}')
    
    def update_account(self, account_id: str, account_data: Dict) -> Optional[Dict]:
        """Update account information"""
        return self._make_request('PATCH', f'/v1/accounts/{account_id}', data=account_data)
    
    def get_account_status(self, account_id: str) -> Optional[Dict]:
        """Get account status (KYC, approval, etc.)"""
        return self._make_request('GET', f'/v1/accounts/{account_id}/status')
    
    # Documents
    def upload_document(self, account_id: str, document_data: Dict, file_path: str) -> Optional[Dict]:
        """Upload KYC document"""
        url = f"{self.base_url}/v1/accounts/{account_id}/documents"
        headers = self._get_headers()
        
        try:
            with open(file_path, 'rb') as f:
                files = {'document': f}
                data = {
                    'document_type': document_data.get('document_type'),
                    'document_sub_type': document_data.get('document_sub_type', ''),
                }
                response = requests.post(url, headers=headers, files=files, data=data, timeout=60)
                response.raise_for_status()
                return response.json()
        except Exception as e:
            logger.error(f"Error uploading document: {e}")
            return {'error': str(e)}
    
    # Orders
    def create_order(self, account_id: str, order_data: Dict) -> Optional[Dict]:
        """Place an order"""
        return self._make_request('POST', f'/v1/trading/accounts/{account_id}/orders', data=order_data)
    
    def get_order(self, account_id: str, order_id: str) -> Optional[Dict]:
        """Get order details"""
        return self._make_request('GET', f'/v1/trading/accounts/{account_id}/orders/{order_id}')
    
    def cancel_order(self, account_id: str, order_id: str) -> Optional[Dict]:
        """Cancel an order"""
        return self._make_request('DELETE', f'/v1/trading/accounts/{account_id}/orders/{order_id}')
    
    def get_orders(
        self, 
        account_id: str, 
        status: Optional[str] = None,
        limit: int = 50,
        after: Optional[str] = None
    ) -> Optional[List[Dict]]:
        """Get orders for account"""
        params = {'limit': limit}
        if status:
            params['status'] = status
        if after:
            params['after'] = after
        
        result = self._make_request('GET', f'/v1/trading/accounts/{account_id}/orders', params=params)
        return result if isinstance(result, list) else []
    
    # Positions
    def get_positions(self, account_id: str) -> Optional[List[Dict]]:
        """Get all positions for account"""
        result = self._make_request('GET', f'/v1/trading/accounts/{account_id}/positions')
        return result if isinstance(result, list) else []
    
    def get_position(self, account_id: str, symbol: str) -> Optional[Dict]:
        """Get position for specific symbol"""
        return self._make_request('GET', f'/v1/trading/accounts/{account_id}/positions/{symbol}')
    
    # Account Info
    def get_account_info(self, account_id: str) -> Optional[Dict]:
        """Get account info (buying power, cash, equity, etc.)"""
        return self._make_request('GET', f'/v1/trading/accounts/{account_id}/account')
    
    # Activities
    def get_activities(
        self,
        account_id: str,
        activity_type: Optional[str] = None,
        date: Optional[str] = None,
        until: Optional[str] = None,
        after: Optional[str] = None,
        direction: str = 'desc',
        page_size: int = 50
    ) -> Optional[List[Dict]]:
        """Get account activities"""
        params = {
            'page_size': page_size,
            'direction': direction,
        }
        if activity_type:
            params['activity_type'] = activity_type
        if date:
            params['date'] = date
        if until:
            params['until'] = until
        if after:
            params['after'] = after
        
        result = self._make_request('GET', f'/v1/accounts/{account_id}/activities', params=params)
        return result if isinstance(result, list) else []
    
    # Funding
    def create_bank_link(self, account_id: str, bank_data: Dict) -> Optional[Dict]:
        """Create bank link for ACH transfers"""
        return self._make_request('POST', f'/v1/accounts/{account_id}/ach_relationships', data=bank_data)
    
    def create_transfer(self, account_id: str, transfer_data: Dict) -> Optional[Dict]:
        """Create transfer (deposit/withdrawal)"""
        return self._make_request('POST', f'/v1/accounts/{account_id}/transfers', data=transfer_data)
    
    def get_transfers(self, account_id: str) -> Optional[List[Dict]]:
        """Get transfer history"""
        result = self._make_request('GET', f'/v1/accounts/{account_id}/transfers')
        return result if isinstance(result, list) else []
    
    # Statements & Documents
    def get_statements(self, account_id: str, year: Optional[int] = None) -> Optional[List[Dict]]:
        """Get statements"""
        params = {}
        if year:
            params['year'] = year
        result = self._make_request('GET', f'/v1/accounts/{account_id}/statements', params=params)
        return result if isinstance(result, list) else []
    
    def get_tax_documents(self, account_id: str, year: Optional[int] = None) -> Optional[List[Dict]]:
        """Get tax documents (1099s)"""
        params = {}
        if year:
            params['year'] = year
        result = self._make_request('GET', f'/v1/accounts/{account_id}/tax_documents', params=params)
        return result if isinstance(result, list) else []


class BrokerGuardrails:
    """Guardrail logic for order placement and trading"""
    
    # Symbol whitelist (U.S. equities & ETFs only for MVP)
    SYMBOL_WHITELIST = {
        # Major indices
        'SPY', 'QQQ', 'DIA', 'IWM',
        # Tech
        'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'META', 'NVDA', 'TSLA', 'NFLX',
        # Finance
        'JPM', 'BAC', 'WFC', 'GS', 'MS',
        # Healthcare
        'JNJ', 'PFE', 'UNH', 'ABBV',
        # Consumer
        'WMT', 'HD', 'MCD', 'SBUX',
        # Industrial
        'BA', 'CAT', 'GE',
        # Energy
        'XOM', 'CVX',
        # Add more as needed
    }
    
    MAX_PER_ORDER_NOTIONAL = 10000  # $10k per order cap
    MAX_DAILY_NOTIONAL = 50000  # $50k daily cap per user
    MAX_POSITION_SIZE = 50000  # $50k max position size
    
    TRADING_HOURS_START = time(9, 30)  # 9:30 AM ET
    TRADING_HOURS_END = time(16, 0)    # 4:00 PM ET
    
    @staticmethod
    def market_is_open_now() -> bool:
        """Check if market is currently open (ET timezone)"""
        from pytz import timezone as tz
        et = tz('America/New_York')
        now_et = datetime.now(et).time()
        
        # Check if it's a weekday
        weekday = datetime.now(et).weekday()
        if weekday >= 5:  # Saturday = 5, Sunday = 6
            return False
        
        return BrokerGuardrails.TRADING_HOURS_START <= now_et <= BrokerGuardrails.TRADING_HOURS_END
    
    @staticmethod
    def is_symbol_whitelisted(symbol: str) -> bool:
        """Check if symbol is in whitelist"""
        return symbol.upper() in BrokerGuardrails.SYMBOL_WHITELIST
    
    @staticmethod
    def can_place_order(
        user,
        symbol: str,
        notional: float,
        order_type: str = 'MARKET',
        daily_notional_used: float = 0
    ) -> tuple[bool, str]:
        """
        Check if order can be placed
        Returns: (allowed, reason)
        """
        from .broker_models import BrokerAccount
        
        # Check if user has broker account
        try:
            broker_account = user.broker_account
        except BrokerAccount.DoesNotExist:
            return False, "No broker account found. Please complete onboarding first."
        
        # Check KYC status
        if broker_account.kyc_status != 'APPROVED':
            return False, f"Account not approved. Current status: {broker_account.kyc_status}"
        
        # Check trading restrictions
        if broker_account.trading_blocked:
            return False, "Trading is blocked on this account"
        
        # Check symbol whitelist
        if not BrokerGuardrails.is_symbol_whitelisted(symbol):
            return False, f"Symbol {symbol} is not available for trading"
        
        # Check per-order notional cap
        if notional > BrokerGuardrails.MAX_PER_ORDER_NOTIONAL:
            return False, f"Order size exceeds maximum per-order limit of ${BrokerGuardrails.MAX_PER_ORDER_NOTIONAL:,.2f}"
        
        # Check daily notional cap
        if daily_notional_used + notional > BrokerGuardrails.MAX_DAILY_NOTIONAL:
            remaining = BrokerGuardrails.MAX_DAILY_NOTIONAL - daily_notional_used
            return False, f"Order would exceed daily limit. Remaining: ${remaining:,.2f}"
        
        # Check trading hours (for market orders)
        if order_type == 'MARKET' and not BrokerGuardrails.market_is_open_now():
            return False, "Market orders can only be placed during market hours (9:30 AM - 4:00 PM ET)"
        
        # Check buying power (would need account info from Alpaca)
        # This should be checked before calling this function
        
        # Check PDT restrictions
        if broker_account.pattern_day_trader and broker_account.day_trade_count >= 3:
            return False, "Pattern Day Trader restrictions: Maximum day trades reached"
        
        return True, "Order passed all guardrail checks"
    
    @staticmethod
    def get_daily_notional_used(user, date: Optional[datetime] = None) -> float:
        """Calculate total notional used today"""
        from .broker_models import BrokerOrder
        
        if date is None:
            date = timezone.now()
        
        start_of_day = date.replace(hour=0, minute=0, second=0, microsecond=0)
        
        try:
            broker_account = user.broker_account
            orders_today = BrokerOrder.objects.filter(
                broker_account=broker_account,
                created_at__gte=start_of_day,
                status__in=['FILLED', 'PARTIALLY_FILLED']  # Only count orders that have been executed
            )
            
            total_notional = sum(
                float(order.notional) if order.notional else 0
                for order in orders_today
            )
            
            return total_notional
        except Exception:
            return 0.0

