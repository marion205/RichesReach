"""
Rate Limiting Middleware
Provides rate limiting for API endpoints to prevent abuse
"""
import time
import logging
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
    RATE_LIMITS = {
        '/api/auth/alpaca/initiate': {'limit': 5, 'window': 60},  # 5 per minute
        '/api/auth/alpaca/callback': {'limit': 10, 'window': 60},  # 10 per minute
        '/graphql/': {'limit': 100, 'window': 60},  # 100 per minute
        '/api/yodlee/': {'limit': 20, 'window': 60},  # 20 per minute
        '/api/market/quotes': {'limit': 60, 'window': 60},  # 60 per minute
    }
    
    # Default rate limit for unlisted endpoints
    DEFAULT_LIMIT = {'limit': 100, 'window': 60}  # 100 per minute
    
    def get_client_ip(self, request) -> str:
        """Get client IP address from request"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip or 'unknown'
    
    def get_rate_limit(self, path: str) -> Dict:
        """Get rate limit configuration for path"""
        for pattern, limit in self.RATE_LIMITS.items():
            if pattern in path:
                return limit
        return self.DEFAULT_LIMIT
    
    def check_rate_limit(self, request) -> Optional[JsonResponse]:
        """Check if request exceeds rate limit"""
        path = request.path
        ip = self.get_client_ip(request)
        rate_limit = self.get_rate_limit(path)
        
        # Create cache key
        cache_key = f'rate_limit:{ip}:{path}'
        
        # Get current count
        current_count = cache.get(cache_key, 0)
        
        if current_count >= rate_limit['limit']:
            logger.warning(f"Rate limit exceeded for {ip} on {path}")
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

