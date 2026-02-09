"""
Enhanced Yodlee Client with Retry Logic and Better Error Handling
"""
import os
import requests
import logging
import time
from typing import Dict, List, Optional, Any
from functools import wraps
from django.conf import settings

logger = logging.getLogger(__name__)

# Import base YodleeClient
from .yodlee_client import YodleeClient


def retry_on_failure(max_retries=3, delay=1, backoff=2, exceptions=(requests.RequestException,)):
    """
    Decorator for retrying API calls with exponential backoff
    
    Args:
        max_retries: Maximum number of retry attempts
        delay: Initial delay in seconds
        backoff: Multiplier for delay after each retry
        exceptions: Tuple of exceptions to catch and retry
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            retries = 0
            current_delay = delay
            
            while retries < max_retries:
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    retries += 1
                    if retries >= max_retries:
                        logger.error(f"Max retries ({max_retries}) exceeded for {func.__name__}: {e}")
                        raise
                    
                    logger.warning(
                        f"Retry {retries}/{max_retries} for {func.__name__} after {current_delay}s: {e}"
                    )
                    time.sleep(current_delay)
                    current_delay *= backoff
            
            return None
        return wrapper
    return decorator


class EnhancedYodleeClient(YodleeClient):
    """Enhanced Yodlee client with retry logic and better error handling"""
    
    def __init__(self):
        super().__init__()
        self.max_retries = int(os.getenv('YODLEE_MAX_RETRIES', '3'))
        self.retry_delay = float(os.getenv('YODLEE_RETRY_DELAY', '1'))
        self.timeout = int(os.getenv('YODLEE_TIMEOUT', '10'))

    def _auth_token(self, login_name: str) -> Optional[str]:
        """Get access token with fixed timeout (legacy behavior)."""
        if not self.client_id or not self.client_secret:
            logger.error("Yodlee credentials not configured. Set YODLEE_CLIENT_ID and YODLEE_SECRET environment variables.")
            return None

        timeout = 10

        try:
            login_url = f"{self.base_url}/auth/token"

            headers = {
                'Api-Version': '1.1',
                'Content-Type': 'application/x-www-form-urlencoded',
                'loginName': login_name,
            }

            data = {
                'clientId': self.client_id.strip(),
                'secret': self.client_secret.strip(),
            }

            logger.info(f"🔵 Requesting token: URL={login_url}, loginName={login_name}")

            response = requests.post(
                login_url,
                headers=headers,
                data=data,
                timeout=timeout,
            )

            logger.info(f"🔵 Token response: status={response.status_code}")

            if response.status_code in (200, 201):
                response_data = response.json()
                if 'token' in response_data:
                    token = response_data.get('token', {}).get('accessToken')
                else:
                    token = response_data.get('accessToken')

                if token:
                    logger.info(f"✅ Token obtained for loginName={login_name}")
                    return token
                logger.warning(f"⚠️  Token response missing accessToken: {response_data}")
            else:
                error_text = response.text[:500] if response.text else "No error text"
                logger.error(f"❌ Failed to get token: {response.status_code} - {error_text}")

        except Exception as e:
            logger.error(f"Error getting token: {e}", exc_info=True)

        return None
    
    def _make_request_with_retry(
        self,
        method: str,
        url: str,
        headers: Dict[str, str],
        data: Optional[Dict] = None,
        params: Optional[Dict] = None,
        timeout: Optional[int] = None
    ) -> Optional[requests.Response]:
        """
        Make HTTP request with retry logic
        
        Returns:
            Response object or None if all retries fail
        """
        timeout = timeout or self.timeout
        retries = 0
        delay = self.retry_delay
        
        while retries < self.max_retries:
            try:
                if method.upper() == 'GET':
                    response = requests.get(url, headers=headers, params=params, timeout=timeout)
                elif method.upper() == 'POST':
                    response = requests.post(url, headers=headers, json=data, params=params, timeout=timeout)
                elif method.upper() == 'DELETE':
                    response = requests.delete(url, headers=headers, timeout=timeout)
                else:
                    raise ValueError(f"Unsupported HTTP method: {method}")
                
                # Check for rate limiting
                if response.status_code == 429:
                    retry_after = int(response.headers.get('Retry-After', delay * (2 ** retries)))
                    logger.warning(f"Rate limited, waiting {retry_after}s before retry")
                    time.sleep(retry_after)
                    retries += 1
                    continue
                
                # Check for server errors (5xx)
                if response.status_code >= 500:
                    logger.warning(f"Server error {response.status_code}, retrying...")
                    retries += 1
                    if retries < self.max_retries:
                        time.sleep(delay)
                        delay *= 2
                        continue
                
                # Success or client error (4xx) - don't retry
                return response
            
            except requests.Timeout:
                logger.warning(f"Request timeout, retrying... ({retries + 1}/{self.max_retries})")
                retries += 1
                if retries < self.max_retries:
                    time.sleep(delay)
                    delay *= 2
                    continue
                raise
            
            except requests.RequestException as e:
                logger.warning(f"Request error: {e}, retrying... ({retries + 1}/{self.max_retries})")
                retries += 1
                if retries < self.max_retries:
                    time.sleep(delay)
                    delay *= 2
                    continue
                raise
        
        return None
    
    @retry_on_failure(max_retries=3, delay=1, backoff=2)
    def get_accounts(self, user_id: str) -> List[Dict[str, Any]]:
        """Get all accounts for user with retry logic"""
        try:
            accounts_url = f"{self.base_url}/accounts"
            headers = self._get_user_token_headers(user_id)
            
            response = self._make_request_with_retry('GET', accounts_url, headers)
            
            if response and response.status_code == 200:
                data = response.json()
                return data.get('account', [])
            else:
                logger.error(f"Failed to get accounts: {response.status_code if response else 'No response'}")
                return []
        
        except Exception as e:
            logger.error(f"Error getting accounts: {e}", exc_info=True)
            return []
    
    @retry_on_failure(max_retries=3, delay=1, backoff=2)
    def get_transactions(
        self,
        user_id: str,
        account_id: Optional[str] = None,
        from_date: Optional[str] = None,
        to_date: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get transactions for user with retry logic"""
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
            
            response = self._make_request_with_retry('GET', transactions_url, headers, params=params)
            
            if response and response.status_code == 200:
                data = response.json()
                return data.get('transaction', [])
            else:
                logger.error(f"Failed to get transactions: {response.status_code if response else 'No response'}")
                return []
        
        except Exception as e:
            logger.error(f"Error getting transactions: {e}", exc_info=True)
            return []
    
    @retry_on_failure(max_retries=2, delay=2, backoff=2)
    def refresh_account(self, provider_account_id: str) -> bool:
        """Trigger account refresh with retry logic"""
        try:
            refresh_url = f"{self.base_url}/accounts/refresh"
            headers = self._get_headers()
            
            payload = {'providerAccountId': provider_account_id}
            
            response = self._make_request_with_retry(
                'POST',
                refresh_url,
                headers,
                data=payload,
                timeout=30  # Refresh can take longer
            )
            
            if response and response.status_code in [200, 202]:
                return True
            else:
                logger.error(f"Failed to refresh account: {response.status_code if response else 'No response'}")
                return False
        
        except Exception as e:
            logger.error(f"Error refreshing account: {e}", exc_info=True)
            return False

