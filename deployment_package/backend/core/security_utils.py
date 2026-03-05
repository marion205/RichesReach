"""
Security Utilities
Production-safe helpers for SSL, secrets, and security checks.
"""
import os
import re
import ssl
import logging
from typing import Optional

logger = logging.getLogger(__name__)

# Patterns to redact from DEBUG (and below) logs — never log keys, tokens, or full query params.
_REDACT_PATTERNS = [
    (re.compile(r"\bapi[_-]?key\s*=\s*['\"]?[\w-]+", re.I), "apiKey=[REDACTED]"),
    (re.compile(r"\bapiKey\s*=\s*[\w-]+", re.I), "apiKey=[REDACTED]"),
    # Alpha Vantage rate-limit message: "We have detected your API key as XXXXX"
    (re.compile(r"your\s+API\s+key\s+as\s+[\w-]+", re.I), "your API key as [REDACTED]"),
    (re.compile(r"Authorization:\s*Bearer\s+\S+", re.I), "Authorization: Bearer [REDACTED]"),
    (re.compile(r"token\s*=\s*['\"]?[\w-]+", re.I), "token=[REDACTED]"),
    (re.compile(r"password\s*=\s*['\"]?\S+", re.I), "password=[REDACTED]"),
    (re.compile(r"secret\s*=\s*['\"]?\S+", re.I), "secret=[REDACTED]"),
    (re.compile(r"[\?&](api[_-]?key|token|auth)=[^&\s]+", re.I), "?apiKey=[REDACTED]"),
]


def redact_secrets_for_log(message: str) -> str:
    """
    Redact API keys, tokens, passwords, and auth headers from a string
    before it is written to logs. Use for any DEBUG (or lower) log
    that might contain request URLs, headers, or query params.

    Example: logger.debug("Request: %s", redact_secrets_for_log(str(request.headers)))
    """
    if not message:
        return message
    out = message
    for pattern, replacement in _REDACT_PATTERNS:
        out = pattern.sub(replacement, out)
    return out


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

