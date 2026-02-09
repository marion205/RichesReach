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
        self.admin_loginname = os.getenv('YODLEE_ADMIN_LOGINNAME', '').strip()
        
        # Check API key rotation status
        try:
            from .api_key_rotation import get_api_key_rotation_service
            rotation_service = get_api_key_rotation_service()
            
            # Check Yodlee credentials rotation status
            client_id_status = rotation_service.check_rotation_needed('YODLEE_CLIENT_ID')
            secret_status = rotation_service.check_rotation_needed('YODLEE_SECRET')
            
            if client_id_status.get('needs_rotation') or secret_status.get('needs_rotation'):
                logger.warning(f"⚠️  Yodlee credentials need rotation: CLIENT_ID={client_id_status.get('needs_rotation')}, SECRET={secret_status.get('needs_rotation')}")
            elif client_id_status.get('needs_warning') or secret_status.get('needs_warning'):
                logger.info(f"🔑 Yodlee credentials rotation warning: CLIENT_ID={client_id_status.get('days_until_rotation')} days, SECRET={secret_status.get('days_until_rotation')} days")
            
            # Record key creation if first time
            if self.client_id:
                rotation_service.record_key_creation('YODLEE_CLIENT_ID')
            if self.client_secret:
                rotation_service.record_key_creation('YODLEE_SECRET')
        except Exception as e:
            logger.debug(f"API key rotation service not available: {e}")
        
        # Debug logging for credential validation (NO SECRETS LOGGED)
        # Only log lengths and validation issues, never actual secret values
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
    
    def _auth_token(self, login_name: str) -> Optional[str]:
        """Get access token for a given loginName (admin or user)"""
        # Validate credentials first
        if not self.client_id or not self.client_secret:
            logger.error("Yodlee credentials not configured. Set YODLEE_CLIENT_ID and YODLEE_SECRET environment variables.")
            return None
        timeout = int(os.getenv('YODLEE_TIMEOUT', '10'))
        
        try:
            login_url = f"{self.base_url}/auth/token"
            
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
            
            logger.info(f"🔵 Requesting token: URL={login_url}, loginName={login_name}")
            
            response = requests.post(
                login_url,
                headers=headers,
                data=data,  # Use data= for form-urlencoded, not json=
                timeout=timeout
            )
            
            logger.info(f"🔵 Token response: status={response.status_code}")
            
            if response.status_code in (200, 201):
                response_data = response.json()
                # Handle both formats: {"token": {"accessToken": "..."}} and {"accessToken": "..."}
                if 'token' in response_data:
                    token = response_data.get('token', {}).get('accessToken')
                else:
                    token = response_data.get('accessToken')
                
                if token:
                    logger.info(f"✅ Token obtained for loginName={login_name}")
                    return token
                else:
                    logger.warning(f"⚠️  Token response missing accessToken: {response_data}")
            else:
                error_text = response.text[:500] if response.text else "No error text"
                logger.error(f"❌ Failed to get token: {response.status_code} - {error_text}")
        
        except Exception as e:
            logger.error(f"Error getting token: {e}", exc_info=True)
        
        return None
    
    def admin_token(self) -> Optional[str]:
        """Get admin access token"""
        if not self.admin_loginname:
            logger.error("YODLEE_ADMIN_LOGINNAME not configured. Required for user registration.")
            return None
        return self._auth_token(self.admin_loginname)
    
    def _get_user_token(self, login_name: str) -> Optional[str]:
        """Get user access token (cached)"""
        # Check cache first
        if login_name in self._user_tokens:
            logger.debug(f"🔵 Using cached token for loginName={login_name}")
            return self._user_tokens[login_name]
        
        # Get fresh token
        token = self._auth_token(login_name)
        if token:
            self._user_tokens[login_name] = token
        return token
    
    def _get_user_token_headers(self, user_id: str) -> Dict[str, str]:
        """Get headers with user-specific access token (legacy method - uses user_id)"""
        headers = self._get_headers(include_auth=True)
        
        # Legacy: try to get token using user_id as loginName
        login_name = f"user_{user_id}"
        token = self._get_user_token(login_name)
        if token:
            headers['Authorization'] = f"Bearer {token}"
        
        return headers
    
    def register_user(self, admin_token: str, login_name: str, email: str) -> bool:
        """Register a new user in Yodlee using admin token"""
        try:
            register_url = f"{self.base_url}/user/register"
            
            headers = {
                'Api-Version': '1.1',
                'Authorization': f'Bearer {admin_token}',
                'Content-Type': 'application/json',
            }
            
            payload = {
                'user': {
                    'loginName': login_name,
                    'email': email,
                    'locale': 'en_US',
                    'preferences': {
                        'currency': 'USD'
                    }
                }
            }
            
            logger.info(f"🔵 Registering Yodlee user: loginName={login_name}, email={email}")
            
            response = requests.post(
                register_url,
                headers=headers,
                json=payload,
                timeout=20
            )
            
            if response.status_code in (200, 201):
                logger.info(f"✅ User registered in Yodlee: {login_name}")
                return True
            
            # Check for specific error codes
            try:
                error_data = response.json()
                error_code = error_data.get('errorCode', '')
                error_msg = (error_data.get('errorMessage') or '').lower()
                
                # If user already exists, treat as OK
                if 'already' in error_msg and 'exist' in error_msg:
                    logger.info(f"✅ User already exists in Yodlee: {login_name}")
                    return True
                
                # Y820: User registration not supported (sandbox limitation)
                if error_code == 'Y820' or 'not supported for sandbox' in error_msg:
                    logger.warning(f"⚠️  Sandbox limitation: Programmatic user registration not supported (Y820)")
                    logger.warning(f"⚠️  Users must be pre-registered in Yodlee admin console for sandbox")
                    return False  # Registration failed, but this is expected in sandbox
            except Exception:
                pass
            
            # Log error but don't raise (will try token request anyway)
            error_text = response.text[:500] if response.text else "No error text"
            logger.warning(f"⚠️  User registration response: {response.status_code} - {error_text}")
            return False
                
        except Exception as e:
            logger.error(f"Error registering user: {e}", exc_info=True)
            return False
    
    def ensure_user_registered(self, login_name: str, email: str) -> bool:
        """Ensure Yodlee user exists (register if needed using admin token) - Idempotent"""
        try:
            # First, try to get user token - if this succeeds, user already exists
            existing_token = self._get_user_token(login_name)
            if existing_token:
                logger.info(f"✅ User already exists in Yodlee: {login_name}")
                return True
            
            # User doesn't exist, register them
            logger.info(f"🔵 User not found, registering: {login_name}")
            
            # Get admin token
            admin_token = self.admin_token()
            if not admin_token:
                logger.error("❌ Cannot register user: admin token unavailable")
                return False
            
            # Register user
            registered = self.register_user(admin_token, login_name, email)
            if registered:
                logger.info(f"✅ New Yodlee user registered: {login_name} (email: {email})")
            return registered
        except Exception as e:
            logger.error(f"Error ensuring user registered: {e}", exc_info=True)
            return False

    def ensure_user(self, login_name: str) -> bool:
        """Legacy helper for ensuring a user token can be fetched."""
        token = self._get_user_token(login_name)
        return bool(token)
    
    def create_fastlink_token(self, login_name: str) -> Optional[str]:
        """Create FastLink token for user (must use user token, not admin)"""
        try:
            token = self._get_user_token(login_name)
            if not token:
                logger.error(f"Failed to get user token for FastLink: loginName={login_name}")
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

