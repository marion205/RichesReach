"""
Security Utilities
Production-safe helpers for SSL, secrets, and security checks
"""
import os
import ssl
import logging
from typing import Optional

logger = logging.getLogger(__name__)


def get_ssl_context(verify: Optional[bool] = None) -> ssl.SSLContext:
    """
    Get SSL context with production guard.
    
    Args:
        verify: Optional override. If None, uses SSL_VERIFY env var.
    
    Returns:
        SSL context (verified in production, optionally unverified in dev)
    
    Raises:
        ValueError: If SSL verification is disabled in production
    """
    environment = os.getenv('ENVIRONMENT', 'development').lower()
    
    # Determine verification setting
    if verify is None:
        verify_ssl = os.getenv('SSL_VERIFY', 'true').lower() == 'true'
    else:
        verify_ssl = verify
    
    # Hard block in production
    if environment == 'production' and not verify_ssl:
        raise ValueError(
            "SSL verification cannot be disabled in production. "
            "Set SSL_VERIFY=true or remove SSL_VERIFY from environment."
        )
    
    if verify_ssl:
        return ssl.create_default_context()
    else:
        # Only allow in development
        context = ssl.create_default_context()
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE
        logger.warning("⚠️ SSL verification disabled (development only)")
        return context


def get_requests_verify() -> bool:
    """
    Get requests library verify setting with production guard.
    
    Returns:
        True if SSL verification should be enabled, False otherwise
    
    Raises:
        ValueError: If SSL verification is disabled in production
    """
    environment = os.getenv('ENVIRONMENT', 'development').lower()
    verify_ssl = os.getenv('SSL_VERIFY', 'true').lower() == 'true'
    
    # Hard block in production
    if environment == 'production' and not verify_ssl:
        raise ValueError(
            "SSL verification cannot be disabled in production. "
            "Set SSL_VERIFY=true or remove SSL_VERIFY from environment."
        )
    
    return verify_ssl

