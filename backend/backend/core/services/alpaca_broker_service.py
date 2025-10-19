"""
Alpaca Broker API Service
Handles account management, KYC/AML, and trading operations through Alpaca's Broker API
"""
import os
import requests
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
from django.conf import settings

logger = logging.getLogger(__name__)

class AlpacaBrokerService:
    """Service for interacting with Alpaca Broker API"""
    
    def __init__(self):
        # Try Django settings first, then environment variables
        self.api_key = getattr(settings, 'ALPACA_API_KEY', os.getenv('ALPACA_API_KEY', ''))
        self.secret_key = getattr(settings, 'ALPACA_SECRET_KEY', os.getenv('ALPACA_SECRET_KEY', ''))
        self.base_url = getattr(settings, 'ALPACA_BASE_URL', os.getenv('ALPACA_BASE_URL', 'https://broker-api.sandbox.alpaca.markets'))
        self.environment = getattr(settings, 'ALPACA_ENVIRONMENT', os.getenv('ALPACA_ENVIRONMENT', 'sandbox'))
        
        if not self.api_key or not self.secret_key:
            logger.warning("Alpaca API credentials not configured")
        
        self.headers = {
            'APCA-API-KEY-ID': self.api_key,
            'APCA-API-SECRET-KEY': self.secret_key,
            'Content-Type': 'application/json'
        }
    
    def _make_request(self, method: str, endpoint: str, data: Optional[Dict] = None) -> Dict:
        """Make HTTP request to Alpaca Broker API"""
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
            logger.error(f"Alpaca API request failed: {e}")
            if hasattr(e, 'response') and e.response is not None:
                logger.error(f"Response: {e.response.text}")
            raise
    
    # =============================================================================
    # ACCOUNT MANAGEMENT
    # =============================================================================
    
    def create_account(self, account_data: Dict) -> Dict:
        """Create a new brokerage account"""
        endpoint = "/v1/accounts"
        return self._make_request('POST', endpoint, account_data)
    
    def get_accounts(self) -> List[Dict]:
        """Get all accounts"""
        endpoint = "/v1/accounts"
        response = self._make_request('GET', endpoint)
        return response if isinstance(response, list) else response.get('accounts', [])
    
    def get_account(self, account_id: str) -> Dict:
        """Get specific account details"""
        endpoint = f"/v1/accounts/{account_id}"
        return self._make_request('GET', endpoint)
    
    def update_account(self, account_id: str, account_data: Dict) -> Dict:
        """Update account information"""
        endpoint = f"/v1/accounts/{account_id}"
        return self._make_request('PUT', endpoint, account_data)
    
    # =============================================================================
    # KYC/AML WORKFLOWS
    # =============================================================================
    
    def create_kyc_document(self, account_id: str, document_data: Dict) -> Dict:
        """Create KYC document for account"""
        endpoint = f"/v1/accounts/{account_id}/documents"
        return self._make_request('POST', endpoint, document_data)
    
    def get_kyc_documents(self, account_id: str) -> List[Dict]:
        """Get KYC documents for account"""
        endpoint = f"/v1/accounts/{account_id}/documents"
        response = self._make_request('GET', endpoint)
        return response if isinstance(response, list) else response.get('documents', [])
    
    def get_kyc_document(self, account_id: str, document_id: str) -> Dict:
        """Get specific KYC document"""
        endpoint = f"/v1/accounts/{account_id}/documents/{document_id}"
        return self._make_request('GET', endpoint)
    
    def upload_kyc_document(self, account_id: str, document_id: str, file_data: bytes, content_type: str) -> Dict:
        """Upload KYC document file"""
        endpoint = f"/v1/accounts/{account_id}/documents/{document_id}/upload"
        
        headers = self.headers.copy()
        headers['Content-Type'] = content_type
        
        url = f"{self.base_url}{endpoint}"
        response = requests.post(url, headers=headers, data=file_data)
        response.raise_for_status()
        return response.json() if response.content else {}
    
    # =============================================================================
    # TRADING OPERATIONS
    # =============================================================================
    
    def create_order(self, account_id: str, order_data: Dict) -> Dict:
        """Create a trading order"""
        endpoint = f"/v1/trading/accounts/{account_id}/orders"
        return self._make_request('POST', endpoint, order_data)
    
    def get_orders(self, account_id: str, status: Optional[str] = None) -> List[Dict]:
        """Get orders for account"""
        endpoint = f"/v1/trading/accounts/{account_id}/orders"
        params = {}
        if status:
            params['status'] = status
        
        url = f"{self.base_url}{endpoint}"
        if params:
            url += '?' + '&'.join([f"{k}={v}" for k, v in params.items()])
        
        response = requests.get(url, headers=self.headers)
        response.raise_for_status()
        data = response.json()
        return data if isinstance(data, list) else data.get('orders', [])
    
    def get_order(self, account_id: str, order_id: str) -> Dict:
        """Get specific order"""
        endpoint = f"/v1/trading/accounts/{account_id}/orders/{order_id}"
        return self._make_request('GET', endpoint)
    
    def cancel_order(self, account_id: str, order_id: str) -> Dict:
        """Cancel an order"""
        endpoint = f"/v1/trading/accounts/{account_id}/orders/{order_id}"
        return self._make_request('DELETE', endpoint)
    
    # =============================================================================
    # PORTFOLIO & POSITIONS
    # =============================================================================
    
    def get_positions(self, account_id: str) -> List[Dict]:
        """Get account positions"""
        endpoint = f"/v1/trading/accounts/{account_id}/positions"
        response = self._make_request('GET', endpoint)
        return response if isinstance(response, list) else response.get('positions', [])
    
    def get_position(self, account_id: str, symbol: str) -> Dict:
        """Get specific position"""
        endpoint = f"/v1/trading/accounts/{account_id}/positions/{symbol}"
        return self._make_request('GET', endpoint)
    
    def close_position(self, account_id: str, symbol: str, qty: Optional[str] = None) -> Dict:
        """Close a position"""
        endpoint = f"/v1/trading/accounts/{account_id}/positions/{symbol}"
        data = {}
        if qty:
            data['qty'] = qty
        
        return self._make_request('DELETE', endpoint, data if data else None)
    
    def get_portfolio_history(self, account_id: str, period: str = "1M") -> Dict:
        """Get portfolio history"""
        endpoint = f"/v1/trading/accounts/{account_id}/portfolio/history"
        params = {'period': period}
        
        url = f"{self.base_url}{endpoint}?period={period}"
        response = requests.get(url, headers=self.headers)
        response.raise_for_status()
        return response.json()
    
    # =============================================================================
    # ACCOUNT ACTIVITIES
    # =============================================================================
    
    def get_activities(self, account_id: str, activity_type: Optional[str] = None) -> List[Dict]:
        """Get account activities"""
        endpoint = f"/v1/accounts/{account_id}/activities"
        params = {}
        if activity_type:
            params['activity_type'] = activity_type
        
        url = f"{self.base_url}{endpoint}"
        if params:
            url += '?' + '&'.join([f"{k}={v}" for k, v in params.items()])
        
        response = requests.get(url, headers=self.headers)
        response.raise_for_status()
        data = response.json()
        return data if isinstance(data, list) else data.get('activities', [])
    
    # =============================================================================
    # UTILITY METHODS
    # =============================================================================
    
    def is_connected(self) -> bool:
        """Check if Alpaca API is properly connected"""
        try:
            self.get_accounts()
            return True
        except Exception as e:
            logger.error(f"Alpaca connection check failed: {e}")
            return False
    
    def get_account_status(self, account_id: str) -> str:
        """Get account status"""
        try:
            account = self.get_account(account_id)
            return account.get('status', 'unknown')
        except Exception as e:
            logger.error(f"Failed to get account status: {e}")
            return 'error'
    
    def is_account_approved(self, account_id: str) -> bool:
        """Check if account is approved for trading"""
        status = self.get_account_status(account_id)
        return status in ['APPROVED', 'ACTIVE']
