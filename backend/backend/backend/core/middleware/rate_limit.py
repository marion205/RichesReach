"""
Rate limiting middleware for GraphQL and API endpoints.
"""
import time
import hashlib
from typing import Dict, Optional
from django.core.cache import cache
from django.http import JsonResponse
from django.utils.deprecation import MiddlewareMixin
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

class RateLimitMiddleware(MiddlewareMixin):
    """
    Rate limiting middleware for GraphQL and API requests.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        super().__init__(get_response)
        
        # Rate limit configuration
        self.rate_limits = {
            'graphql': {
                'requests_per_minute': 60,
                'burst_limit': 10,
                'window_size': 60,  # seconds
            },
            'api': {
                'requests_per_minute': 120,
                'burst_limit': 20,
                'window_size': 60,  # seconds
            },
            'default': {
                'requests_per_minute': 100,
                'burst_limit': 15,
                'window_size': 60,  # seconds
            }
        }
    
    def _get_client_ip(self, request):
        """Get client IP address"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
    
    def _get_rate_limit_key(self, request, endpoint_type: str = 'default') -> str:
        """Generate rate limit key for client and endpoint"""
        client_ip = self._get_client_ip(request)
        user_id = getattr(request.user, 'id', None) if hasattr(request, 'user') and request.user.is_authenticated else None
        
        # Use user ID if authenticated, otherwise IP
        identifier = str(user_id) if user_id else client_ip
        return f"rate_limit:{endpoint_type}:{identifier}"
    
    def _get_rate_limit_config(self, request) -> Dict:
        """Get rate limit configuration for request"""
        path = request.path
        
        if '/graphql' in path:
            return self.rate_limits['graphql']
        elif '/api/' in path:
            return self.rate_limits['api']
        else:
            return self.rate_limits['default']
    
    def _check_rate_limit(self, request) -> tuple[bool, Dict]:
        """
        Check if request is within rate limits.
        
        Returns:
            (is_allowed, rate_info)
        """
        config = self._get_rate_limit_config(request)
        key = self._get_rate_limit_key(request, self._get_endpoint_type(request))
        
        current_time = int(time.time())
        window_start = current_time - config['window_size']
        
        # Get current request count from cache
        rate_data = cache.get(key, {
            'requests': [],
            'last_reset': current_time
        })
        
        # Clean old requests outside the window
        rate_data['requests'] = [
            req_time for req_time in rate_data['requests'] 
            if req_time > window_start
        ]
        
        # Check if we're within limits
        current_requests = len(rate_data['requests'])
        max_requests = config['requests_per_minute']
        
        if current_requests >= max_requests:
            # Rate limit exceeded
            oldest_request = min(rate_data['requests']) if rate_data['requests'] else current_time
            reset_time = oldest_request + config['window_size']
            
            rate_info = {
                'limit': max_requests,
                'remaining': 0,
                'reset_time': reset_time,
                'retry_after': reset_time - current_time
            }
            
            return False, rate_info
        
        # Add current request
        rate_data['requests'].append(current_time)
        rate_data['last_reset'] = current_time
        
        # Update cache
        cache.set(key, rate_data, config['window_size'] * 2)
        
        rate_info = {
            'limit': max_requests,
            'remaining': max_requests - current_requests - 1,
            'reset_time': current_time + config['window_size'],
            'retry_after': 0
        }
        
        return True, rate_info
    
    def _get_endpoint_type(self, request) -> str:
        """Determine endpoint type for rate limiting"""
        path = request.path
        
        if '/graphql' in path:
            return 'graphql'
        elif '/api/' in path:
            return 'api'
        else:
            return 'default'
    
    def process_request(self, request):
        """Process incoming request for rate limiting"""
        # Skip rate limiting for certain paths
        skip_paths = ['/health/', '/healthz', '/static/', '/media/']
        if any(request.path.startswith(path) for path in skip_paths):
            return None
        
        # Check rate limit
        is_allowed, rate_info = self._check_rate_limit(request)
        
        if not is_allowed:
            logger.warning(f"Rate limit exceeded for {self._get_client_ip(request)} on {request.path}")
            
            response = JsonResponse({
                'error': 'Rate limit exceeded',
                'message': 'Too many requests. Please try again later.',
                'rate_limit': rate_info
            }, status=429)
            
            # Add rate limit headers
            response['X-RateLimit-Limit'] = str(rate_info['limit'])
            response['X-RateLimit-Remaining'] = str(rate_info['remaining'])
            response['X-RateLimit-Reset'] = str(rate_info['reset_time'])
            response['Retry-After'] = str(rate_info['retry_after'])
            
            return response
        
        # Add rate limit info to request for logging
        request.rate_limit_info = rate_info
        
        return None
    
    def process_response(self, request, response):
        """Add rate limit headers to response"""
        if hasattr(request, 'rate_limit_info'):
            rate_info = request.rate_limit_info
            response['X-RateLimit-Limit'] = str(rate_info['limit'])
            response['X-RateLimit-Remaining'] = str(rate_info['remaining'])
            response['X-RateLimit-Reset'] = str(rate_info['reset_time'])
        
        return response


class GraphQLRateLimitMiddleware:
    """
    GraphQL-specific rate limiting middleware.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        # Only apply to GraphQL requests
        if '/graphql' not in request.path:
            return self.get_response(request)
        
        # Check if it's a GraphQL request
        if request.method == 'POST' and request.content_type == 'application/json':
            try:
                import json
                data = json.loads(request.body)
                query = data.get('query', '')
                
                # Rate limit based on query complexity
                complexity = self._calculate_query_complexity(query)
                
                if complexity > 100:  # High complexity threshold
                    # Apply stricter rate limits for complex queries
                    rate_limit_key = f"graphql_complex:{self._get_client_ip(request)}"
                    current_requests = cache.get(rate_limit_key, 0)
                    
                    if current_requests >= 5:  # Max 5 complex queries per minute
                        return JsonResponse({
                            'errors': [{
                                'message': 'Rate limit exceeded for complex queries',
                                'extensions': {
                                    'code': 'RATE_LIMIT_EXCEEDED',
                                    'retryAfter': 60
                                }
                            }]
                        }, status=429)
                    
                    cache.set(rate_limit_key, current_requests + 1, 60)
                
            except (json.JSONDecodeError, KeyError):
                pass  # Not a valid GraphQL request
        
        return self.get_response(request)
    
    def _get_client_ip(self, request):
        """Get client IP address"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
    
    def _calculate_query_complexity(self, query: str) -> int:
        """
        Calculate query complexity based on field count and depth.
        This is a simplified implementation.
        """
        if not query:
            return 0
        
        # Count fields and nested queries
        field_count = query.count('{') - query.count('}')
        depth = max(0, field_count)
        
        # Count specific expensive operations
        expensive_ops = ['benchmarkSeries', 'swingSignals', 'smartAlerts']
        expensive_count = sum(query.count(op) for op in expensive_ops)
        
        return depth + (expensive_count * 10)
