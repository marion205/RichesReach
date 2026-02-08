"""
Zero Trust Middleware for GraphQL and API requests
Implements "Never Trust, Always Verify" for every request
"""
import logging
from django.utils.deprecation import MiddlewareMixin
from django.http import JsonResponse
from .zero_trust_service import zero_trust_service

logger = logging.getLogger(__name__)


class ZeroTrustMiddleware(MiddlewareMixin):
    """
    Zero Trust middleware that verifies every request
    
    Principles:
    1. Verify every request (no implicit trust)
    2. Least privilege access
    3. Assume breach (defense in depth)
    4. Continuous verification
    """
    
    def process_request(self, request):
        """Verify every request before processing"""
        # Skip for public endpoints
        public_paths = [
            '/health',
            '/graphql/schema',
            '/static/',
            '/media/',
            '/defi/validate-transaction/',
            '/defi/record-transaction/',
        ]
        if any(request.path.startswith(path) for path in public_paths):
            return None
        
        # Get user from request
        user = getattr(request, 'user', None)
        
        if not user or user.is_anonymous:
            # Allow unauthenticated requests to GraphQL (GraphQL handles auth)
            if request.path.startswith('/graphql'):
                return None
            # Otherwise, require authentication
            return JsonResponse({
                'error': 'Authentication required',
                'code': 'UNAUTHENTICATED'
            }, status=401)
        
        # Extract request metadata
        device_id = request.META.get('HTTP_X_DEVICE_ID') or request.headers.get('X-Device-ID')
        ip_address = self._get_client_ip(request)
        user_agent = request.META.get('HTTP_USER_AGENT', '')
        
        # Determine action and resource from request
        action, resource = self._parse_request(request)
        
        request_metadata = {
            'device_id': device_id,
            'ip_address': ip_address,
            'user_agent': user_agent,
            'action': action,
            'resource': resource,
            'auth_method': self._get_auth_method(request),
        }
        
        # Verify request using Zero Trust
        verification_result = zero_trust_service.verify_request(user, request_metadata)
        
        # Store in request for downstream use
        request.zero_trust_verification = verification_result
        
        # Deny if not allowed
        if not verification_result['allowed']:
            logger.warning(
                f"[ZeroTrust] Access denied | user_id={user.id} action={action} "
                f"trust_score={verification_result['trust_score']} "
                f"risk_factors={len(verification_result['risk_factors'])}"
            )
            
            return JsonResponse({
                'error': 'Access denied',
                'code': 'ZERO_TRUST_DENIED',
                'reason': verification_result['reason'],
                'trust_score': verification_result['trust_score'],
                'requires_mfa': verification_result['requires_mfa'],
                'risk_factors': verification_result['risk_factors']
            }, status=403)
        
        # Require MFA if needed
        if verification_result['requires_mfa']:
            # Check if MFA token provided
            mfa_token = request.META.get('HTTP_X_MFA_TOKEN') or request.headers.get('X-MFA-Token')
            if not mfa_token:
                return JsonResponse({
                    'error': 'MFA required',
                    'code': 'MFA_REQUIRED',
                    'trust_score': verification_result['trust_score'],
                    'risk_factors': verification_result['risk_factors']
                }, status=403)
        
        # Log successful verification
        if verification_result['trust_score'] < 80:
            logger.info(
                f"[ZeroTrust] Access granted with low trust | user_id={user.id} "
                f"trust_score={verification_result['trust_score']}"
            )
        
        return None  # Continue processing
    
    def _get_client_ip(self, request):
        """Extract client IP address"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
    
    def _parse_request(self, request):
        """Parse request to determine action and resource"""
        path = request.path
        method = request.method
        
        # GraphQL requests
        if path.startswith('/graphql'):
            # Try to parse GraphQL operation
            if hasattr(request, 'body'):
                try:
                    import json
                    body = json.loads(request.body) if isinstance(request.body, bytes) else request.body
                    if isinstance(body, dict):
                        operation_name = body.get('operationName', '')
                        query = body.get('query', '')
                        
                        # Determine resource from operation name or query
                        if 'portfolio' in operation_name.lower() or 'portfolio' in query.lower():
                            return 'view_portfolio', 'portfolio'
                        elif 'trade' in operation_name.lower() or 'trade' in query.lower():
                            return 'create_trade', 'trading'
                        elif 'security' in operation_name.lower() or 'security' in query.lower():
                            return 'view_security', 'security'
                except:
                    pass
            
            return 'graphql_query', 'api'
        
        # REST API requests
        if method == 'GET':
            return 'view', path.split('/')[1] if len(path.split('/')) > 1 else 'api'
        elif method == 'POST':
            return 'create', path.split('/')[1] if len(path.split('/')) > 1 else 'api'
        elif method == 'PUT' or method == 'PATCH':
            return 'update', path.split('/')[1] if len(path.split('/')) > 1 else 'api'
        elif method == 'DELETE':
            return 'delete', path.split('/')[1] if len(path.split('/')) > 1 else 'api'
        
        return 'unknown', 'api'
    
    def _get_auth_method(self, request):
        """Determine authentication method used"""
        # Check for biometric token
        if request.META.get('HTTP_X_BIOMETRIC_TOKEN'):
            return 'biometric'
        
        # Check for MFA token
        if request.META.get('HTTP_X_MFA_TOKEN'):
            return 'mfa'
        
        # Check for JWT token
        auth_header = request.META.get('HTTP_AUTHORIZATION', '')
        if auth_header.startswith('Bearer ') or auth_header.startswith('JWT '):
            return 'jwt'
        
        return 'password'  # Default

