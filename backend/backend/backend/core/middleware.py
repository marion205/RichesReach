# core/middleware.py
import time
import logging
from django.utils.deprecation import MiddlewareMixin
from django.conf import settings

logger = logging.getLogger(__name__)

class PerformanceMiddleware(MiddlewareMixin):
    """Middleware to track request performance and log slow requests"""
    
    def process_request(self, request):
        request.start_time = time.time()
    
    def process_response(self, request, response):
        if hasattr(request, 'start_time'):
            duration = time.time() - request.start_time
            
            # Log slow requests (> 1 second)
            if duration > 1.0:
                logger.warning(
                    f"Slow request: {request.method} {request.path} "
                    f"took {duration:.2f}s - Status: {response.status_code}"
                )
            
            # Add performance header
            response['X-Response-Time'] = f"{duration:.3f}s"
        
        return response

class SecurityHeadersMiddleware(MiddlewareMixin):
    """Add security headers for production"""
    
    def process_response(self, request, response):
        # Only add security headers in production
        if not settings.DEBUG:
            response['X-Content-Type-Options'] = 'nosniff'
            response['X-Frame-Options'] = 'DENY'
            response['X-XSS-Protection'] = '1; mode=block'
            response['Referrer-Policy'] = 'strict-origin-when-cross-origin'
            response['Permissions-Policy'] = 'geolocation=(), microphone=(), camera=()'
        
        return response

class RequestLoggingMiddleware(MiddlewareMixin):
    """Log all requests in production for monitoring"""
    
    def process_request(self, request):
        if not settings.DEBUG:
            logger.info(
                f"Request: {request.method} {request.path} "
                f"from {request.META.get('REMOTE_ADDR', 'unknown')} "
                f"User-Agent: {request.META.get('HTTP_USER_AGENT', 'unknown')[:100]}"
            )
    
    def process_response(self, request, response):
        if not settings.DEBUG:
            logger.info(
                f"Response: {request.method} {request.path} "
                f"Status: {response.status_code}"
            )
        return response
