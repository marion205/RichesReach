"""
Alpaca OAuth Service
Handles OAuth flow for Alpaca Connect (OAuth-based app marketplace)
"""
import os
import requests
import secrets
import logging
from typing import Dict, Optional
from urllib.parse import urlencode
from django.conf import settings

logger = logging.getLogger(__name__)


class AlpacaOAuthService:
    """Service for handling Alpaca OAuth Connect flow"""
    
    # OAuth endpoints
    AUTHORIZE_URL = 'https://app.alpaca.markets/oauth/authorize'
    TOKEN_URL = 'https://api.alpaca.markets/oauth/token'
    
    # Trading API base URL
    TRADING_API_BASE = 'https://api.alpaca.markets'
    
    def __init__(self):
        self.client_id = os.getenv('ALPACA_OAUTH_CLIENT_ID')
        self.client_secret = os.getenv('ALPACA_OAUTH_CLIENT_SECRET')
        self.redirect_uri = os.getenv('ALPACA_OAUTH_REDIRECT_URI', 'https://api.richesreach.com/auth/alpaca/callback')
        
        # OAuth scopes
        self.scopes = [
            'trading:write',  # Place orders
            'account:read',   # Read account info
            'positions:read', # Read positions
        ]
        
        if not self.client_id or not self.client_secret:
            logger.warning("Alpaca OAuth credentials not configured")
    
    def generate_state(self) -> str:
        """Generate CSRF protection state token"""
        return secrets.token_urlsafe(32)
    
    def get_authorization_url(self, state: str, redirect_uri: Optional[str] = None) -> str:
        """
        Generate OAuth authorization URL
        
        Args:
            state: CSRF protection token
            redirect_uri: Optional custom redirect URI
        
        Returns:
            Authorization URL to redirect user to
        """
        if not self.client_id:
            raise ValueError("Alpaca OAuth client ID not configured")
        
        params = {
            'client_id': self.client_id,
            'redirect_uri': redirect_uri or self.redirect_uri,
            'response_type': 'code',
            'scope': ' '.join(self.scopes),
            'state': state,
        }
        
        return f"{self.AUTHORIZE_URL}?{urlencode(params)}"
    
    def exchange_code_for_tokens(self, code: str, redirect_uri: Optional[str] = None) -> Dict:
        """
        Exchange authorization code for access/refresh tokens
        
        Args:
            code: Authorization code from OAuth callback
            redirect_uri: Must match the redirect_uri used in authorization
        
        Returns:
            Dict with access_token, refresh_token, expires_in, etc.
        """
        if not self.client_id or not self.client_secret:
            raise ValueError("Alpaca OAuth credentials not configured")
        
        data = {
            'grant_type': 'authorization_code',
            'code': code,
            'client_id': self.client_id,
            'client_secret': self.client_secret,
            'redirect_uri': redirect_uri or self.redirect_uri,
        }
        
        try:
            response = requests.post(
                self.TOKEN_URL,
                data=data,
                headers={'Content-Type': 'application/x-www-form-urlencoded'},
                timeout=30
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as e:
            error_detail = e.response.json() if e.response.content else {}
            logger.error(f"Failed to exchange code for tokens: {e} - {error_detail}")
            raise Exception(f"OAuth token exchange failed: {error_detail}")
        except requests.exceptions.RequestException as e:
            logger.error(f"OAuth token exchange request error: {e}")
            raise Exception(f"OAuth token exchange failed: {str(e)}")
    
    def refresh_access_token(self, refresh_token: str) -> Dict:
        """
        Refresh expired access token using refresh token
        
        Args:
            refresh_token: Refresh token from previous OAuth flow
        
        Returns:
            Dict with new access_token, expires_in, etc.
        """
        if not self.client_id or not self.client_secret:
            raise ValueError("Alpaca OAuth credentials not configured")
        
        data = {
            'grant_type': 'refresh_token',
            'refresh_token': refresh_token,
            'client_id': self.client_id,
            'client_secret': self.client_secret,
        }
        
        try:
            response = requests.post(
                self.TOKEN_URL,
                data=data,
                headers={'Content-Type': 'application/x-www-form-urlencoded'},
                timeout=30
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as e:
            error_detail = e.response.json() if e.response.content else {}
            logger.error(f"Failed to refresh access token: {e} - {error_detail}")
            raise Exception(f"OAuth token refresh failed: {error_detail}")
        except requests.exceptions.RequestException as e:
            logger.error(f"OAuth token refresh request error: {e}")
            raise Exception(f"OAuth token refresh failed: {str(e)}")
    
    def revoke_token(self, token: str, token_type: str = 'access_token') -> bool:
        """
        Revoke access or refresh token
        
        Args:
            token: Token to revoke
            token_type: 'access_token' or 'refresh_token'
        
        Returns:
            True if successful
        """
        if not self.client_id or not self.client_secret:
            raise ValueError("Alpaca OAuth credentials not configured")
        
        data = {
            'client_id': self.client_id,
            'client_secret': self.client_secret,
            'token': token,
            'token_type_hint': token_type,
        }
        
        try:
            response = requests.post(
                f"{self.TOKEN_URL}/revoke",
                data=data,
                headers={'Content-Type': 'application/x-www-form-urlencoded'},
                timeout=30
            )
            response.raise_for_status()
            return True
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to revoke token: {e}")
            return False


# Singleton instance
_oauth_service = None

def get_oauth_service() -> AlpacaOAuthService:
    """Get singleton OAuth service instance"""
    global _oauth_service
    if _oauth_service is None:
        _oauth_service = AlpacaOAuthService()
    return _oauth_service

