"""
Yodlee API Client - Wrapper for Yodlee FastLink and Data APIs
"""
import os
import requests
import logging
from typing import Dict, List, Optional, Any
from django.conf import settings
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class YodleeClient:
    """Client for Yodlee API integration"""
    
    def __init__(self):
        # CRITICAL: Strip whitespace to avoid Y303 errors from hidden newlines/spaces
        self.base_url = os.getenv('YODLEE_BASE_URL', 'https://sandbox.api.yodlee.com/ysl').strip()
        self.client_id = os.getenv('YODLEE_CLIENT_ID', '').strip()
        self.client_secret = os.getenv('YODLEE_SECRET', '').strip()
        self.app_id = os.getenv('YODLEE_APP_ID', '').strip()
        self.fastlink_url = os.getenv('YODLEE_FASTLINK_URL', 'https://fastlink.yodlee.com').strip()
        self.webhook_secret = os.getenv('YODLEE_WEBHOOK_SECRET', '').strip()
        
        # Debug logging for credential validation
        if self.client_id and self.client_secret:
            logger.info(f"🔵 YodleeClient initialized: base_url={self.base_url}, client_id_length={len(self.client_id)}, secret_length={len(self.client_secret)}")
            # Check for common issues
            if '\n' in self.client_id or '\n' in self.client_secret:
                logger.warning("⚠️  Newline detected in credentials (should be stripped)")
            if self.client_id.startswith(' ') or self.client_id.endswith(' '):
                logger.warning("⚠️  Whitespace detected in client_id (should be stripped)")
            if self.client_secret.startswith(' ') or self.client_secret.endswith(' '):
                logger.warning("⚠️  Whitespace detected in client_secret (should be stripped)")
        else:
            logger.warning("Yodlee credentials not configured")
        
        # Cache for access tokens (user_id -> token)
        self._user_tokens = {}
    
    def _get_headers(self, include_auth: bool = True) -> Dict[str, str]:
        """Get standard headers for Yodlee API requests"""
        headers = {
            'Content-Type': 'application/json',
            'Api-Version': '1.1',
        }
        
        if include_auth and self.client_id and self.client_secret:
            # Basic auth for Yodlee
            import base64
            # Build credentials string and encode
            credentials = f"{self.client_id}:{self.client_secret}"
            encoded = base64.b64encode(credentials.encode()).decode()
            headers['Authorization'] = f"Basic {encoded}"
            
            # Debug logging (first 50 chars of base64 only, for troubleshooting)
            logger.debug(f"🔵 Yodlee auth: RAW credentials length={len(credentials)}, B64 length={len(encoded)}, B64 (first 50)={encoded[:50]}...")
        
        return headers
    
    def _get_user_token_headers(self, user_id: str) -> Dict[str, str]:
        """Get headers with user-specific access token"""
        headers = self._get_headers(include_auth=True)
        
        # Get or create user token
        token = self._get_user_token(user_id)
        if token:
            headers['Authorization'] = f"Bearer {token}"
        
        return headers
    
    def _get_user_token(self, user_id: str) -> Optional[str]:
        """Get or create user access token"""
        # Validate credentials first
        if not self.client_id or not self.client_secret:
            logger.error("Yodlee credentials not configured. Set YODLEE_CLIENT_ID and YODLEE_SECRET environment variables.")
            return None
        
        # Check cache first
        if user_id in self._user_tokens:
            logger.debug(f"🔵 Using cached token for user {user_id}")
            return self._user_tokens[user_id]
        
        # Create user session/login
        try:
            login_url = f"{self.base_url}/auth/token"
            login_name = f"user_{user_id}"  # Yodlee expects unique loginName per user
            
            # Yodlee expects form-urlencoded, not JSON
            headers = {
                'Api-Version': '1.1',
                'Content-Type': 'application/x-www-form-urlencoded',
                'loginName': login_name,
            }
            
            # Form-encoded body with clientId and secret (strip whitespace)
            data = {
                'clientId': self.client_id.strip(),
                'secret': self.client_secret.strip(),
            }
            
            logger.info(f"🔵 Requesting user token: URL={login_url}, loginName={login_name}")
            logger.debug(f"🔵 Request headers: {list(headers.keys())}")
            logger.debug(f"🔵 Credential lengths: client_id={len(data['clientId'])}, secret={len(data['secret'])}")
            
            response = requests.post(
                login_url,
                headers=headers,
                data=data,  # Use data= for form-urlencoded, not json=
                timeout=15
            )
            
            logger.info(f"🔵 Token response: status={response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                token = data.get('token', {}).get('accessToken')
                if token:
                    self._user_tokens[user_id] = token
                    logger.info(f"✅ User token obtained for user {user_id}")
                    return token
                else:
                    logger.warning(f"⚠️  Token response missing accessToken: {data}")
            else:
                error_text = response.text[:500] if response.text else "No error text"
                logger.error(f"❌ Failed to get user token: {response.status_code} - {error_text}")
                # If Y303, log detailed diagnostic info
                if 'Y303' in error_text or response.status_code == 400:
                    logger.error(f"🔍 Y303 Diagnostic: client_id length={len(self.client_id)}, secret length={len(self.client_secret)}, base_url={self.base_url}")
                    logger.error(f"🔍 Y303 Diagnostic: client_id stripped={self.client_id == self.client_id.strip()}, secret stripped={self.client_secret == self.client_secret.strip()}")
        
        except Exception as e:
            logger.error(f"Error getting user token: {e}", exc_info=True)
        
        return None
    
    def register_user(self, user_id: str) -> bool:
        """Register a new user in Yodlee (may require admin loginName)"""
        try:
            # In Yodlee sandbox, users typically need to be pre-registered
            # OR you need an admin loginName to register them programmatically
            # For now, we'll log that registration is needed but return True
            # to allow the token request to proceed (it will fail with Y305 if user doesn't exist)
            login_name = f"user_{user_id}"
            logger.info(f"🔵 User registration check: loginName={login_name}")
            logger.info(f"ℹ️  Note: In Yodlee sandbox, users must be pre-registered via admin console")
            logger.info(f"ℹ️  OR use admin loginName in YODLEE_ADMIN_LOGINNAME env var")
            
            # Check if admin loginName is configured
            admin_login = os.getenv('YODLEE_ADMIN_LOGINNAME', '').strip()
            if admin_login:
                logger.info(f"🔵 Admin loginName configured, attempting user registration...")
                # TODO: Implement admin-based user registration if needed
                # For now, return True to allow token request (will fail with Y305 if user doesn't exist)
                return True
            else:
                logger.warning(f"⚠️  No YODLEE_ADMIN_LOGINNAME configured - users must be pre-registered")
                return True  # Return True to allow token attempt (will fail gracefully with Y305)
                
        except Exception as e:
            logger.error(f"Error in user registration check: {e}", exc_info=True)
            return True  # Allow token attempt anyway
    
    def ensure_user(self, user_id: str) -> bool:
        """Ensure Yodlee user exists (register if needed, then get token)"""
        try:
            # First, try to register the user
            registered = self.register_user(user_id)
            if not registered:
                logger.warning(f"⚠️  User registration may have failed, but trying to get token anyway")
            
            # Then try to get token
            token = self._get_user_token(user_id)
            return token is not None
        except Exception as e:
            logger.error(f"Error ensuring user: {e}")
            return False
    
    def create_fastlink_token(self, user_id: str) -> Optional[str]:
        """Create FastLink token for user"""
        try:
            token = self._get_user_token(user_id)
            if not token:
                logger.error("Failed to get user token for FastLink")
                return None
            
            # FastLink token is the same as user access token
            return token
        
        except Exception as e:
            logger.error(f"Error creating FastLink token: {e}")
            return None
    
    def get_accounts(self, user_id: str) -> List[Dict[str, Any]]:
        """Get all accounts for user"""
        try:
            accounts_url = f"{self.base_url}/accounts"
            headers = self._get_user_token_headers(user_id)
            
            response = requests.get(
                accounts_url,
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                return data.get('account', [])
            else:
                logger.error(f"Failed to get accounts: {response.status_code} - {response.text}")
                return []
        
        except Exception as e:
            logger.error(f"Error getting accounts: {e}")
            return []
    
    def get_transactions(
        self,
        user_id: str,
        account_id: Optional[str] = None,
        from_date: Optional[str] = None,
        to_date: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get transactions for user"""
        try:
            transactions_url = f"{self.base_url}/transactions"
            headers = self._get_user_token_headers(user_id)
            
            params = {}
            if account_id:
                params['accountId'] = account_id
            if from_date:
                params['fromDate'] = from_date
            if to_date:
                params['toDate'] = to_date
            
            response = requests.get(
                transactions_url,
                headers=headers,
                params=params,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                return data.get('transaction', [])
            else:
                logger.error(f"Failed to get transactions: {response.status_code} - {response.text}")
                return []
        
        except Exception as e:
            logger.error(f"Error getting transactions: {e}")
            return []
    
    def refresh_account(self, provider_account_id: str) -> bool:
        """Trigger account refresh for provider account"""
        try:
            refresh_url = f"{self.base_url}/accounts/refresh"
            headers = self._get_headers()
            
            payload = {
                'providerAccountId': provider_account_id
            }
            
            response = requests.post(
                refresh_url,
                headers=headers,
                json=payload,
                timeout=30  # Refresh can take longer
            )
            
            if response.status_code in [200, 202]:
                return True
            else:
                logger.error(f"Failed to refresh account: {response.status_code} - {response.text}")
                return False
        
        except Exception as e:
            logger.error(f"Error refreshing account: {e}")
            return False
    
    def delete_account(self, provider_account_id: str) -> bool:
        """Delete provider account"""
        try:
            delete_url = f"{self.base_url}/providerAccounts/{provider_account_id}"
            headers = self._get_headers()
            
            response = requests.delete(
                delete_url,
                headers=headers,
                timeout=10
            )
            
            if response.status_code in [200, 204]:
                return True
            else:
                logger.error(f"Failed to delete account: {response.status_code} - {response.text}")
                return False
        
        except Exception as e:
            logger.error(f"Error deleting account: {e}")
            return False
    
    def verify_webhook_signature(self, payload: str, signature: str) -> bool:
        """Verify webhook signature"""
        if not self.webhook_secret:
            logger.warning("YODLEE_WEBHOOK_SECRET not configured, skipping signature verification")
            return True
        
        try:
            import hmac
            import hashlib
            
            expected_signature = hmac.new(
                self.webhook_secret.encode(),
                payload.encode(),
                hashlib.sha256
            ).hexdigest()
            
            return hmac.compare_digest(expected_signature, signature)
        
        except Exception as e:
            logger.error(f"Error verifying webhook signature: {e}")
            return False
    
    @staticmethod
    def normalize_account(yodlee_account: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize Yodlee account to our format"""
        return {
            'yodlee_account_id': str(yodlee_account.get('id', '')),
            'provider_account_id': str(yodlee_account.get('providerAccountId', '')),
            'provider_name': yodlee_account.get('providerName', ''),
            'name': yodlee_account.get('accountName', ''),
            'mask': yodlee_account.get('accountNumber', '')[-4:] if yodlee_account.get('accountNumber') else '',
            'account_type': yodlee_account.get('CONTAINER', ''),
            'account_subtype': yodlee_account.get('accountType', ''),
            'currency': yodlee_account.get('CONTAINER', 'USD'),
            'balance_current': yodlee_account.get('balance', {}).get('amount', 0) if yodlee_account.get('balance') else None,
            'balance_available': yodlee_account.get('availableBalance', {}).get('amount', 0) if yodlee_account.get('availableBalance') else None,
            'last_updated': yodlee_account.get('lastUpdated', None),
        }
    
    @staticmethod
    def normalize_transaction(yodlee_transaction: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize Yodlee transaction to our format"""
        amount = yodlee_transaction.get('amount', {}).get('amount', 0) if yodlee_transaction.get('amount') else 0
        transaction_type = 'CREDIT' if amount >= 0 else 'DEBIT'
        
        return {
            'yodlee_transaction_id': str(yodlee_transaction.get('id', '')),
            'amount': abs(amount),  # Store as positive, use type for direction
            'currency': yodlee_transaction.get('amount', {}).get('currency', 'USD') if yodlee_transaction.get('amount') else 'USD',
            'description': yodlee_transaction.get('description', {}).get('original', '') if yodlee_transaction.get('description') else '',
            'merchant_name': yodlee_transaction.get('merchant', {}).get('name', '') if yodlee_transaction.get('merchant') else '',
            'category': yodlee_transaction.get('category', ''),
            'subcategory': yodlee_transaction.get('subCategory', ''),
            'transaction_type': transaction_type,
            'posted_date': yodlee_transaction.get('postDate', ''),
            'transaction_date': yodlee_transaction.get('transactionDate', ''),
            'status': yodlee_transaction.get('status', 'POSTED'),
            'raw_json': yodlee_transaction,
        }

