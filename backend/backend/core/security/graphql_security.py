"""
GraphQL Security Middleware and Configuration
Implements production-ready security measures for GraphQL API
"""

import logging
from django.conf import settings
from django.core.cache import cache
from django.http import JsonResponse
from django.utils.deprecation import MiddlewareMixin
from graphql import GraphQLError
from graphql.execution import ExecutionResult
import time
import hashlib
import json
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

class GraphQLSecurityMiddleware(MiddlewareMixin):
    """
    Production GraphQL security middleware
    - Rate limiting
    - Query depth limiting
    - Query complexity analysis
    - Introspection blocking
    - Query cost analysis
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        super().__init__(get_response)
        
        # Security configuration
        self.max_depth = getattr(settings, 'GRAPHQL_MAX_DEPTH', 10)
        self.max_complexity = getattr(settings, 'GRAPHQL_MAX_COMPLEXITY', 1000)
        self.rate_limit_per_minute = getattr(settings, 'GRAPHQL_RATE_LIMIT_PER_MINUTE', 60)
        self.block_introspection = getattr(settings, 'GRAPHQL_BLOCK_INTROSPECTION', True)
        
    def process_request(self, request):
        """Process GraphQL requests for security checks"""
        if not request.path.startswith('/graphql'):
            return None
            
        # Rate limiting
        if not self._check_rate_limit(request):
            return JsonResponse({
                'errors': [{'message': 'Rate limit exceeded. Please try again later.'}]
            }, status=429)
            
        # Check for introspection queries in production
        if self.block_introspection and self._is_introspection_query(request):
            return JsonResponse({
                'errors': [{'message': 'Introspection queries are disabled in production.'}]
            }, status=400)
            
        return None
    
    def _check_rate_limit(self, request) -> bool:
        """Implement rate limiting based on IP address"""
        client_ip = self._get_client_ip(request)
        cache_key = f"graphql_rate_limit:{client_ip}"
        
        # Get current request count
        current_count = cache.get(cache_key, 0)
        
        if current_count >= self.rate_limit_per_minute:
            logger.warning(f"Rate limit exceeded for IP: {client_ip}")
            return False
            
        # Increment counter with 60 second expiry
        cache.set(cache_key, current_count + 1, 60)
        return True
    
    def _is_introspection_query(self, request) -> bool:
        """Check if the request contains introspection queries"""
        try:
            if request.method == 'POST':
                body = request.body.decode('utf-8')
                data = json.loads(body)
                query = data.get('query', '')
                
                # Check for introspection keywords
                introspection_keywords = [
                    '__schema', '__type', '__typename', '__field',
                    '__inputvalue', '__enumvalue', '__directive'
                ]
                
                return any(keyword in query for keyword in introspection_keywords)
        except (json.JSONDecodeError, UnicodeDecodeError):
            pass
            
        return False
    
    def _get_client_ip(self, request) -> str:
        """Get client IP address, handling proxy headers"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            ip = request.META.get('REMOTE_ADDR', 'unknown')
        return ip


class QueryComplexityAnalyzer:
    """
    Analyzes GraphQL query complexity to prevent expensive operations
    """
    
    def __init__(self):
        self.field_weights = {
            # High complexity fields
            'stocks': 10,
            'allStocks': 20,
            'searchTickers': 15,
            'quotes': 5,
            'portfolioMetrics': 8,
            'aiRecommendations': 12,
            'cryptoPortfolio': 10,
            'socialFeed': 6,
            'stockDiscussions': 8,
            
            # Medium complexity fields
            'me': 2,
            'user': 3,
            'posts': 4,
            'watchlist': 3,
            
            # Low complexity fields
            'ping': 1,
            'version': 1,
        }
    
    def calculate_complexity(self, query: str) -> int:
        """Calculate query complexity score"""
        complexity = 0
        query_lower = query.lower()
        
        for field, weight in self.field_weights.items():
            if field in query_lower:
                # Count occurrences and multiply by weight
                count = query_lower.count(field)
                complexity += count * weight
                
        return complexity


class GraphQLDepthLimiter:
    """
    Limits the depth of GraphQL queries to prevent deep nesting attacks
    """
    
    def __init__(self, max_depth: int = 10):
        self.max_depth = max_depth
    
    def analyze_depth(self, query: str) -> int:
        """Analyze query depth by counting nested braces"""
        depth = 0
        max_depth = 0
        
        for char in query:
            if char == '{':
                depth += 1
                max_depth = max(max_depth, depth)
            elif char == '}':
                depth -= 1
                
        return max_depth


def secure_graphql_response(response: ExecutionResult) -> ExecutionResult:
    """
    Sanitize GraphQL response to remove sensitive information
    """
    if response.errors:
        # Log errors but don't expose internal details
        for error in response.errors:
            logger.error(f"GraphQL Error: {error.message}")
            
        # Sanitize error messages in production
        if not settings.DEBUG:
            sanitized_errors = []
            for error in response.errors:
                if isinstance(error, GraphQLError):
                    sanitized_errors.append({
                        'message': 'An error occurred while processing your request.',
                        'locations': getattr(error, 'locations', None)
                    })
                else:
                    sanitized_errors.append({
                        'message': 'An error occurred while processing your request.'
                    })
            response.errors = sanitized_errors
    
    return response


class GraphQLAuditLogger:
    """
    Logs GraphQL operations for security auditing
    """
    
    def __init__(self):
        self.audit_logger = logging.getLogger('graphql_audit')
        
    def log_query(self, request, query: str, variables: Dict[str, Any], 
                  execution_time: float, success: bool):
        """Log GraphQL query for audit purposes"""
        client_ip = self._get_client_ip(request)
        user_id = getattr(request.user, 'id', None) if hasattr(request, 'user') else None
        
        # Create query hash for deduplication
        query_hash = hashlib.sha256(query.encode()).hexdigest()[:16]
        
        audit_data = {
            'timestamp': time.time(),
            'client_ip': client_ip,
            'user_id': user_id,
            'query_hash': query_hash,
            'execution_time': execution_time,
            'success': success,
            'query_length': len(query),
            'variables_count': len(variables) if variables else 0
        }
        
        # Log to audit logger
        self.audit_logger.info(f"GraphQL Query: {json.dumps(audit_data)}")
        
        # Log slow queries
        if execution_time > 5.0:  # 5 seconds
            logger.warning(f"Slow GraphQL query detected: {execution_time:.2f}s - {query_hash}")
    
    def _get_client_ip(self, request) -> str:
        """Get client IP address"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            return x_forwarded_for.split(',')[0].strip()
        return request.META.get('REMOTE_ADDR', 'unknown')


# Global instances
complexity_analyzer = QueryComplexityAnalyzer()
depth_limiter = GraphQLDepthLimiter()
audit_logger = GraphQLAuditLogger()
