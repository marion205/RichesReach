"""
Rate Limiting Middleware
Provides rate limiting for API endpoints to prevent abuse
"""
import time
import logging
import os
from typing import Dict, Optional
from django.core.cache import cache
from django.http import JsonResponse
from django.utils.deprecation import MiddlewareMixin

logger = logging.getLogger(__name__)


class RateLimitMiddleware(MiddlewareMixin):
    """
    Rate limiting middleware
    
    Limits requests per IP address based on endpoint patterns
    """
    
    # Rate limit configurations (requests per window)
    # Sensitive endpoints have stricter limits
    RATE_LIMITS = {
        # Authentication endpoints
        '/api/auth/alpaca/initiate': {'limit': 5, 'window': 60},  # 5 per minute
        '/api/auth/alpaca/callback': {'limit': 10, 'window': 60},  # 10 per minute
        '/api/auth/login': {'limit': 5, 'window': 60},  # 5 per minute
        '/api/auth/signup': {'limit': 3, 'window': 60},  # 3 per minute
        
        # Yodlee banking endpoints (sensitive)
        '/api/yodlee/fastlink/start': {'limit': 10, 'window': 60},  # 10 per minute
        '/api/yodlee/fastlink/callback': {'limit': 20, 'window': 60},  # 20 per minute
        '/api/yodlee/accounts': {'limit': 30, 'window': 60},  # 30 per minute
        '/api/yodlee/transactions': {'limit': 30, 'window': 60},  # 30 per minute
        '/api/yodlee/refresh': {'limit': 10, 'window': 60},  # 10 per minute
        '/api/yodlee/': {'limit': 20, 'window': 60},  # 20 per minute (catch-all)
        
        # GraphQL
        '/graphql/': {'limit': 100, 'window': 60},  # 100 per minute
        
        # Market data
        '/api/market/quotes': {'limit': 60, 'window': 60},  # 60 per minute
        
        # Daily Brief (can be called frequently)
        '/api/daily-brief/': {'limit': 20, 'window': 60},  # 20 per minute
        
        # Portfolio endpoints
        '/api/portfolio/': {'limit': 30, 'window': 60},  # 30 per minute
    }
    
    # Default rate limit for unlisted endpoints
    DEFAULT_LIMIT = {'limit': 100, 'window': 60}  # 100 per minute
    
    def get_client_ip(self, request) -> str:
        """
        Get client IP address from request (proxy-safe).
        
        IMPORTANT: Only trusts X-Forwarded-For from trusted proxies.
        In production, configure TRUSTED_PROXIES env var with comma-separated proxy IPs.
        """
        # Get trusted proxies from environment (comma-separated IPs/CIDR)
        trusted_proxies = os.getenv('TRUSTED_PROXIES', '').split(',')
        trusted_proxies = [p.strip() for p in trusted_proxies if p.strip()]
        
        # Get the immediate client IP (could be proxy)
        immediate_ip = request.META.get('REMOTE_ADDR', '')
        
        # Check if immediate IP is a trusted proxy
        is_trusted_proxy = False
        if trusted_proxies and immediate_ip:
            import ipaddress
            try:
                immediate_ip_obj = ipaddress.ip_address(immediate_ip)
                for proxy_pattern in trusted_proxies:
                    try:
                        if '/' in proxy_pattern:
                            # CIDR notation
                            if immediate_ip_obj in ipaddress.ip_network(proxy_pattern, strict=False):
                                is_trusted_proxy = True
                                break
                        else:
                            # Single IP
                            if immediate_ip_obj == ipaddress.ip_address(proxy_pattern):
                                is_trusted_proxy = True
                                break
                    except ValueError:
                        continue
            except ValueError:
                pass  # Invalid IP format
        
        # If trusted proxy, use X-Forwarded-For; otherwise use REMOTE_ADDR
        if is_trusted_proxy:
            x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
            if x_forwarded_for:
                # X-Forwarded-For can contain multiple IPs: "client, proxy1, proxy2"
                # The first one is the original client
                ip = x_forwarded_for.split(',')[0].strip()
                return ip or immediate_ip
            else:
                # Trusted proxy but no X-Forwarded-For header - use immediate IP
                return immediate_ip
        else:
            # Not behind a trusted proxy - use REMOTE_ADDR directly
            return immediate_ip or 'unknown'
    
    def get_rate_limit(self, path: str) -> Dict:
        """Get rate limit configuration for path"""
        for pattern, limit in self.RATE_LIMITS.items():
            if pattern in path:
                return limit
        return self.DEFAULT_LIMIT
    
    def check_rate_limit(self, request) -> Optional[JsonResponse]:
        """
        Check if request exceeds rate limit.
        
        For auth endpoints, uses IP + username/device for stricter limiting.
        For other endpoints, uses IP only.
        """
        path = request.path
        ip = self.get_client_ip(request)
        rate_limit = self.get_rate_limit(path)
        
        # For auth endpoints, add username/device to rate limit key
        # This prevents IP rotation attacks
        is_auth_endpoint = any(auth_path in path for auth_path in [
            '/api/auth/login',
            '/api/auth/signup',
            '/api/auth/alpaca/initiate',
        ])
        
        if is_auth_endpoint:
            # Try to get username from request body or headers
            username = None
            try:
                # For POST requests, try to get username from body
                if request.method == 'POST' and hasattr(request, 'body'):
                    import json
                    try:
                        body_data = json.loads(request.body)
                        username = body_data.get('email') or body_data.get('username')
                    except (json.JSONDecodeError, AttributeError):
                        pass
            except Exception:
                pass
            
            # Normalize username for rate limit key (lowercase, strip whitespace)
            if username:
                username_normalized = username.lower().strip()
                cache_key = f'rate_limit:{ip}:{username_normalized}:{path}'
            else:
                # Fallback to IP-only if username not available
                cache_key = f'rate_limit:{ip}:{path}'
        else:
            # Non-auth endpoints: IP-only rate limiting
            cache_key = f'rate_limit:{ip}:{path}'
        
        # Get current count
        current_count = cache.get(cache_key, 0)
        
        if current_count >= rate_limit['limit']:
            logger.warning(f"Rate limit exceeded for {ip} on {path} (key: {cache_key})")
            return JsonResponse({
                'error': 'Rate limit exceeded',
                'message': f'Too many requests. Limit: {rate_limit["limit"]} per {rate_limit["window"]} seconds',
                'retry_after': rate_limit['window']
            }, status=429)
        
        # Increment count
        cache.set(
            cache_key,
            current_count + 1,
            timeout=rate_limit['window']
        )
        
        return None
    
    def process_request(self, request):
        """Process request and check rate limits"""
        # Skip rate limiting for admin and static files
        if request.path.startswith('/admin/') or request.path.startswith('/static/'):
            return None
        
        # Check rate limit
        rate_limit_response = self.check_rate_limit(request)
        if rate_limit_response:
            return rate_limit_response
        
        return None

