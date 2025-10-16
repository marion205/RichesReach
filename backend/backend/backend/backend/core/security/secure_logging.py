"""
Secure Logging System with PII Redaction
Implements production-ready logging with sensitive data protection
"""

import logging
import json
import re
from typing import Any, Dict, List, Optional
from django.conf import settings
from django.utils import timezone
import hashlib


class PIIRedactor:
    """
    Redacts personally identifiable information from log messages
    """
    
    def __init__(self):
        # Patterns for sensitive data
        self.patterns = {
            'email': r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
            'phone': r'\b(?:\+?1[-.\s]?)?\(?([0-9]{3})\)?[-.\s]?([0-9]{3})[-.\s]?([0-9]{4})\b',
            'ssn': r'\b\d{3}-?\d{2}-?\d{4}\b',
            'credit_card': r'\b(?:\d{4}[-\s]?){3}\d{4}\b',
            'api_key': r'\b[A-Za-z0-9]{20,}\b',  # Generic API key pattern
            'jwt_token': r'\beyJ[A-Za-z0-9_-]*\.[A-Za-z0-9_-]*\.[A-Za-z0-9_-]*\b',
            'password': r'(?i)(password|passwd|pwd)\s*[:=]\s*[^\s]+',
            'secret': r'(?i)(secret|key|token)\s*[:=]\s*[^\s]+',
            'ip_address': r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b',
        }
        
        # Replacement values
        self.replacements = {
            'email': '[EMAIL_REDACTED]',
            'phone': '[PHONE_REDACTED]',
            'ssn': '[SSN_REDACTED]',
            'credit_card': '[CARD_REDACTED]',
            'api_key': '[API_KEY_REDACTED]',
            'jwt_token': '[JWT_REDACTED]',
            'password': '[PASSWORD_REDACTED]',
            'secret': '[SECRET_REDACTED]',
            'ip_address': '[IP_REDACTED]',
        }
    
    def redact(self, text: str) -> str:
        """Redact PII from text"""
        if not isinstance(text, str):
            return text
            
        redacted_text = text
        
        for pattern_name, pattern in self.patterns.items():
            replacement = self.replacements[pattern_name]
            redacted_text = re.sub(pattern, replacement, redacted_text, flags=re.IGNORECASE)
        
        return redacted_text
    
    def redact_dict(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Redact PII from dictionary"""
        if not isinstance(data, dict):
            return data
            
        redacted_data = {}
        
        for key, value in data.items():
            # Redact sensitive keys
            if any(sensitive in key.lower() for sensitive in ['password', 'secret', 'key', 'token', 'email', 'phone']):
                redacted_data[key] = '[REDACTED]'
            elif isinstance(value, str):
                redacted_data[key] = self.redact(value)
            elif isinstance(value, dict):
                redacted_data[key] = self.redact_dict(value)
            elif isinstance(value, list):
                redacted_data[key] = [self.redact_dict(item) if isinstance(item, dict) else self.redact(str(item)) for item in value]
            else:
                redacted_data[key] = value
        
        return redacted_data


class SecureJSONFormatter(logging.Formatter):
    """
    JSON formatter with PII redaction
    """
    
    def __init__(self):
        super().__init__()
        self.redactor = PIIRedactor()
    
    def format(self, record):
        """Format log record as JSON with PII redaction"""
        log_data = {
            'timestamp': timezone.now().isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'message': self.redactor.redact(record.getMessage()),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno,
        }
        
        # Add exception info if present
        if record.exc_info:
            log_data['exception'] = self.formatException(record.exc_info)
        
        # Add extra fields with redaction
        if hasattr(record, 'extra_data'):
            log_data['extra'] = self.redactor.redact_dict(record.extra_data)
        
        # Add request info if available
        if hasattr(record, 'request'):
            log_data['request'] = self._format_request_info(record.request)
        
        return json.dumps(log_data, default=str)
    
    def _format_request_info(self, request) -> Dict[str, Any]:
        """Format request information with PII redaction"""
        request_info = {
            'method': request.method,
            'path': request.path,
            'user_agent': request.META.get('HTTP_USER_AGENT', ''),
            'content_type': request.META.get('CONTENT_TYPE', ''),
        }
        
        # Add IP address (redacted)
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            request_info['ip'] = '[IP_REDACTED]'
        else:
            request_info['ip'] = '[IP_REDACTED]'
        
        # Add user info if authenticated
        if hasattr(request, 'user') and request.user.is_authenticated:
            request_info['user_id'] = request.user.id
            request_info['username'] = '[USERNAME_REDACTED]'
        
        return request_info


class SecurityAuditLogger:
    """
    Dedicated logger for security events
    """
    
    def __init__(self):
        self.logger = logging.getLogger('security_audit')
        self.redactor = PIIRedactor()
    
    def log_authentication_attempt(self, request, success: bool, user_id: Optional[int] = None):
        """Log authentication attempts"""
        event_data = {
            'event_type': 'authentication_attempt',
            'success': success,
            'user_id': user_id,
            'timestamp': timezone.now().isoformat(),
            'ip': self._get_client_ip(request),
            'user_agent': request.META.get('HTTP_USER_AGENT', ''),
        }
        
        self.logger.info(f"Auth attempt: {json.dumps(event_data)}")
    
    def log_token_usage(self, request, token_type: str, user_id: int, success: bool):
        """Log JWT token usage"""
        event_data = {
            'event_type': 'token_usage',
            'token_type': token_type,
            'user_id': user_id,
            'success': success,
            'timestamp': timezone.now().isoformat(),
            'ip': self._get_client_ip(request),
        }
        
        self.logger.info(f"Token usage: {json.dumps(event_data)}")
    
    def log_rate_limit_exceeded(self, request, endpoint: str):
        """Log rate limit violations"""
        event_data = {
            'event_type': 'rate_limit_exceeded',
            'endpoint': endpoint,
            'timestamp': timezone.now().isoformat(),
            'ip': self._get_client_ip(request),
            'user_agent': request.META.get('HTTP_USER_AGENT', ''),
        }
        
        self.logger.warning(f"Rate limit exceeded: {json.dumps(event_data)}")
    
    def log_suspicious_activity(self, request, activity_type: str, details: Dict[str, Any]):
        """Log suspicious activities"""
        event_data = {
            'event_type': 'suspicious_activity',
            'activity_type': activity_type,
            'details': self.redactor.redact_dict(details),
            'timestamp': timezone.now().isoformat(),
            'ip': self._get_client_ip(request),
            'user_agent': request.META.get('HTTP_USER_AGENT', ''),
        }
        
        self.logger.warning(f"Suspicious activity: {json.dumps(event_data)}")
    
    def log_graphql_query(self, request, query_hash: str, complexity: int, execution_time: float, success: bool):
        """Log GraphQL queries for security monitoring"""
        event_data = {
            'event_type': 'graphql_query',
            'query_hash': query_hash,
            'complexity': complexity,
            'execution_time': execution_time,
            'success': success,
            'timestamp': timezone.now().isoformat(),
            'ip': self._get_client_ip(request),
            'user_id': getattr(request.user, 'id', None) if hasattr(request, 'user') else None,
        }
        
        self.logger.info(f"GraphQL query: {json.dumps(event_data)}")
    
    def _get_client_ip(self, request) -> str:
        """Get client IP address"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            return x_forwarded_for.split(',')[0].strip()
        return request.META.get('REMOTE_ADDR', 'unknown')


class SlowQueryLogger:
    """
    Logs slow GraphQL queries for performance monitoring
    """
    
    def __init__(self, threshold: float = 5.0):
        self.logger = logging.getLogger('slow_queries')
        self.threshold = threshold
        self.redactor = PIIRedactor()
    
    def log_slow_query(self, request, query: str, execution_time: float, complexity: int):
        """Log slow GraphQL queries"""
        if execution_time > self.threshold:
            query_hash = hashlib.sha256(query.encode()).hexdigest()[:16]
            
            event_data = {
                'event_type': 'slow_query',
                'query_hash': query_hash,
                'execution_time': execution_time,
                'complexity': complexity,
                'query_length': len(query),
                'timestamp': timezone.now().isoformat(),
                'ip': self._get_client_ip(request),
                'user_id': getattr(request.user, 'id', None) if hasattr(request, 'user') else None,
            }
            
            self.logger.warning(f"Slow query detected: {json.dumps(event_data)}")
    
    def _get_client_ip(self, request) -> str:
        """Get client IP address"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            return x_forwarded_for.split(',')[0].strip()
        return request.META.get('REMOTE_ADDR', 'unknown')


# Global instances
security_audit_logger = SecurityAuditLogger()
slow_query_logger = SlowQueryLogger()
pii_redactor = PIIRedactor()


def setup_secure_logging():
    """Setup secure logging configuration"""
    
    # Create formatters
    json_formatter = SecureJSONFormatter()
    
    # Security audit logger
    security_logger = logging.getLogger('security_audit')
    security_logger.setLevel(logging.INFO)
    security_handler = logging.StreamHandler()
    security_handler.setFormatter(json_formatter)
    security_logger.addHandler(security_handler)
    security_logger.propagate = False
    
    # GraphQL audit logger
    graphql_logger = logging.getLogger('graphql_audit')
    graphql_logger.setLevel(logging.INFO)
    graphql_handler = logging.StreamHandler()
    graphql_handler.setFormatter(json_formatter)
    graphql_logger.addHandler(graphql_handler)
    graphql_logger.propagate = False
    
    # Slow queries logger
    slow_logger = logging.getLogger('slow_queries')
    slow_logger.setLevel(logging.WARNING)
    slow_handler = logging.StreamHandler()
    slow_handler.setFormatter(json_formatter)
    slow_logger.addHandler(slow_handler)
    slow_logger.propagate = False
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    
    # Remove default handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Add secure handler
    secure_handler = logging.StreamHandler()
    secure_handler.setFormatter(json_formatter)
    root_logger.addHandler(secure_handler)
