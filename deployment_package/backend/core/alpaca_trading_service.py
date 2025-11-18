"""
Alpaca Trading API Service
Handles interactions with Alpaca Trading API using OAuth access tokens
"""
import requests
import logging
from typing import Dict, Optional, List, Any

logger = logging.getLogger(__name__)


class AlpacaTradingService:
    """Service for interacting with Alpaca Trading API using OAuth tokens"""
    
    BASE_URL = 'https://api.alpaca.markets'
    BASE_URL_PAPER = 'https://paper-api.alpaca.markets'
    
    def __init__(self, access_token: str, paper: bool = False):
        """
        Initialize Trading API service
        
        Args:
            access_token: OAuth access token
            paper: Use paper trading endpoint (default: False)
        """
        self.access_token = access_token
        self.base_url = self.BASE_URL_PAPER if paper else self.BASE_URL
    
    def _get_headers(self) -> Dict[str, str]:
        """Get authentication headers for API requests"""
        return {
            'Authorization': f'Bearer {self.access_token}',
            'Content-Type': 'application/json',
        }
    
    def _make_request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict] = None,
        params: Optional[Dict] = None
    ) -> Optional[Dict]:
        """Make authenticated request to Alpaca Trading API"""
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
            logger.error(f"Alpaca Trading API HTTP error: {e} - {error_detail}")
            return {'error': str(e), 'detail': error_detail}
        
        except requests.exceptions.RequestException as e:
            logger.error(f"Alpaca Trading API request error: {e}")
            return {'error': str(e)}
    
    # Account Operations
    def get_account(self) -> Optional[Dict]:
        """Get user's Alpaca account information"""
        return self._make_request('GET', '/v2/account')
    
    # Order Operations
    def create_order(
        self,
        symbol: str,
        qty: Optional[float] = None,
        side: str = 'buy',
        order_type: str = 'market',
        time_in_force: str = 'day',
        limit_price: Optional[float] = None,
        stop_price: Optional[float] = None,
        **kwargs
    ) -> Optional[Dict]:
        """
        Create a new order
        
        Args:
            symbol: Stock symbol
            qty: Quantity (for market/limit orders)
            side: 'buy' or 'sell'
            order_type: 'market', 'limit', 'stop', 'stop_limit'
            time_in_force: 'day', 'gtc', 'opg', 'cls', 'ioc', 'fok'
            limit_price: Required for limit orders
            stop_price: Required for stop orders
        """
        order_data = {
            'symbol': symbol.upper(),
            'side': side,
            'type': order_type,
            'time_in_force': time_in_force,
            **kwargs
        }
        
        if qty is not None:
            order_data['qty'] = qty
        
        if limit_price is not None:
            order_data['limit_price'] = limit_price
        
        if stop_price is not None:
            order_data['stop_price'] = stop_price
        
        return self._make_request('POST', '/v2/orders', data=order_data)
    
    def get_orders(
        self,
        status: Optional[str] = None,
        limit: int = 50,
        nested: bool = False
    ) -> Optional[List[Dict]]:
        """
        Get list of orders
        
        Args:
            status: Filter by status ('open', 'closed', 'all')
            limit: Maximum number of orders to return
            nested: Include nested order information
        """
        params = {
            'limit': limit,
            'nested': nested,
        }
        if status:
            params['status'] = status
        
        return self._make_request('GET', '/v2/orders', params=params)
    
    def get_order(self, order_id: str) -> Optional[Dict]:
        """Get specific order by ID"""
        return self._make_request('GET', f'/v2/orders/{order_id}')
    
    def cancel_order(self, order_id: str) -> bool:
        """Cancel an order"""
        result = self._make_request('DELETE', f'/v2/orders/{order_id}')
        return result is not None and 'error' not in result
    
    def cancel_all_orders(self) -> bool:
        """Cancel all open orders"""
        result = self._make_request('DELETE', '/v2/orders')
        return result is not None and 'error' not in result
    
    # Position Operations
    def get_positions(self) -> Optional[List[Dict]]:
        """Get all open positions"""
        return self._make_request('GET', '/v2/positions')
    
    def get_position(self, symbol: str) -> Optional[Dict]:
        """Get position for specific symbol"""
        return self._make_request('GET', f'/v2/positions/{symbol.upper()}')
    
    def close_position(self, symbol: str) -> Optional[Dict]:
        """Close position for symbol"""
        return self._make_request('DELETE', f'/v2/positions/{symbol.upper()}')
    
    def close_all_positions(self) -> Optional[List[Dict]]:
        """Close all positions"""
        return self._make_request('DELETE', '/v2/positions')
    
    # Account Activities
    def get_activities(
        self,
        activity_type: Optional[str] = None,
        date: Optional[str] = None,
        until: Optional[str] = None,
        after: Optional[str] = None,
        direction: str = 'desc',
        page_size: int = 50
    ) -> Optional[List[Dict]]:
        """
        Get account activities
        
        Args:
            activity_type: Filter by type (e.g., 'FILL', 'DIV', 'INT')
            date: Filter by date (YYYY-MM-DD)
            until: Filter activities until date
            after: Filter activities after date
            direction: 'asc' or 'desc'
            page_size: Number of results per page
        """
        params = {
            'direction': direction,
            'page_size': page_size,
        }
        if activity_type:
            params['activity_type'] = activity_type
        if date:
            params['date'] = date
        if until:
            params['until'] = until
        if after:
            params['after'] = after
        
        return self._make_request('GET', '/v2/account/activities', params=params)
    
    # Portfolio History
    def get_portfolio_history(
        self,
        period: str = '1M',
        timeframe: str = '1Day',
        end_date: Optional[str] = None,
        extended_hours: bool = True
    ) -> Optional[Dict]:
        """
        Get portfolio equity history
        
        Args:
            period: Time period ('1D', '5D', '1M', '3M', '1Y', 'All')
            timeframe: Bar timeframe ('1Min', '5Min', '15Min', '1H', '1Day')
            end_date: End date (YYYY-MM-DD)
            extended_hours: Include extended hours data
        """
        params = {
            'period': period,
            'timeframe': timeframe,
            'extended_hours': extended_hours,
        }
        if end_date:
            params['end_date'] = end_date
        
        return self._make_request('GET', '/v2/account/portfolio/history', params=params)

