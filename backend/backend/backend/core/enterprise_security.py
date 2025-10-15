"""
Enterprise Security System
Comprehensive security measures for enterprise-level protection
"""
import hashlib
import hmac
import secrets
import time
import jwt
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum
from django.conf import settings
from django.core.cache import cache
from django.contrib.auth.hashers import make_password, check_password
from django.utils.crypto import get_random_string
import logging

from .enterprise_config import config
from .enterprise_exceptions import SecurityException, ErrorCode
from .enterprise_logging import get_enterprise_logger


class SecurityLevel(Enum):
    """Security levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class SecurityEvent:
    """Security event data structure"""
    event_type: str
    severity: SecurityLevel
    user_id: Optional[str]
    ip_address: Optional[str]
    user_agent: Optional[str]
    details: Dict[str, Any]
    timestamp: datetime


class PasswordValidator:
    """Enterprise password validation"""
    
    @staticmethod
    def validate_password(password: str) -> Tuple[bool, List[str]]:
        """Validate password strength"""
        errors = []
        
        if len(password) < config.security_config.password_min_length:
            errors.append(f"Password must be at least {config.security_config.password_min_length} characters long")
        
        if not any(c.isupper() for c in password):
            errors.append("Password must contain at least one uppercase letter")
        
        if not any(c.islower() for c in password):
            errors.append("Password must contain at least one lowercase letter")
        
        if not any(c.isdigit() for c in password):
            errors.append("Password must contain at least one digit")
        
        if not any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in password):
            errors.append("Password must contain at least one special character")
        
        # Check for common passwords
        common_passwords = [
            'password', '123456', '123456789', 'qwerty', 'abc123',
            'password123', 'admin', 'letmein', 'welcome', 'monkey'
        ]
        
        if password.lower() in common_passwords:
            errors.append("Password is too common and easily guessable")
        
        return len(errors) == 0, errors
    
    @staticmethod
    def hash_password(password: str) -> str:
        """Hash password using secure method"""
        return make_password(password)
    
    @staticmethod
    def verify_password(password: str, hashed: str) -> bool:
        """Verify password against hash"""
        return check_password(password, hashed)


class RateLimiter:
    """Rate limiting for security"""
    
    def __init__(self):
        self.logger = get_enterprise_logger('rate_limiter')
    
    def is_rate_limited(
        self,
        identifier: str,
        action: str,
        max_attempts: int = 5,
        window_minutes: int = 15
    ) -> bool:
        """Check if identifier is rate limited for action"""
        cache_key = f"rate_limit:{action}:{identifier}"
        
        attempts = cache.get(cache_key, [])
        now = time.time()
        
        # Remove old attempts outside window
        window_seconds = window_minutes * 60
        attempts = [attempt for attempt in attempts if now - attempt < window_seconds]
        
        if len(attempts) >= max_attempts:
            self.logger.warning(
                f"Rate limit exceeded for {identifier} on action {action}",
                extra_data={
                    'identifier': identifier,
                    'action': action,
                    'attempts': len(attempts),
                    'max_attempts': max_attempts
                }
            )
            return True
        
        # Record this attempt
        attempts.append(now)
        cache.set(cache_key, attempts, timeout=window_seconds)
        
        return False
    
    def reset_rate_limit(self, identifier: str, action: str):
        """Reset rate limit for identifier and action"""
        cache_key = f"rate_limit:{action}:{identifier}"
        cache.delete(cache_key)
    
    def get_remaining_attempts(
        self,
        identifier: str,
        action: str,
        max_attempts: int = 5,
        window_minutes: int = 15
    ) -> int:
        """Get remaining attempts before rate limit"""
        cache_key = f"rate_limit:{action}:{identifier}"
        attempts = cache.get(cache_key, [])
        
        now = time.time()
        window_seconds = window_minutes * 60
        attempts = [attempt for attempt in attempts if now - attempt < window_seconds]
        
        return max(0, max_attempts - len(attempts))


class JWTManager:
    """JWT token management"""
    
    def __init__(self):
        self.secret_key = config.security_config.jwt_secret_key
        self.algorithm = 'HS256'
        self.expiration_hours = config.security_config.jwt_expiration_hours
        self.logger = get_enterprise_logger('jwt_manager')
    
    def generate_token(self, user_id: str, additional_claims: Optional[Dict[str, Any]] = None) -> str:
        """Generate JWT token"""
        now = datetime.utcnow()
        payload = {
            'user_id': user_id,
            'iat': now,
            'exp': now + timedelta(hours=self.expiration_hours),
            'jti': secrets.token_urlsafe(32),  # JWT ID for token tracking
            **(additional_claims or {})
        }
        
        token = jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
        
        self.logger.info(
            f"Generated JWT token for user {user_id}",
            extra_data={'user_id': user_id, 'expires_in_hours': self.expiration_hours}
        )
        
        return token
    
    def verify_token(self, token: str) -> Dict[str, Any]:
        """Verify and decode JWT token"""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            
            # Check if token is blacklisted
            jti = payload.get('jti')
            if jti and self.is_token_blacklisted(jti):
                raise SecurityException(
                    "Token has been revoked",
                    ErrorCode.INVALID_TOKEN
                )
            
            return payload
            
        except jwt.ExpiredSignatureError:
            raise SecurityException(
                "Token has expired",
                ErrorCode.TOKEN_EXPIRED
            )
        except jwt.InvalidTokenError:
            raise SecurityException(
                "Invalid token",
                ErrorCode.INVALID_TOKEN
            )
    
    def blacklist_token(self, token: str):
        """Blacklist a token"""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm], options={"verify_exp": False})
            jti = payload.get('jti')
            
            if jti:
                # Store blacklisted token until expiration
                exp_timestamp = payload.get('exp', 0)
                exp_datetime = datetime.fromtimestamp(exp_timestamp)
                ttl = int((exp_datetime - datetime.utcnow()).total_seconds())
                
                if ttl > 0:
                    cache.set(f"blacklisted_token:{jti}", True, timeout=ttl)
                    
                    self.logger.info(
                        f"Token blacklisted",
                        extra_data={'jti': jti, 'user_id': payload.get('user_id')}
                    )
        
        except jwt.InvalidTokenError:
            pass  # Can't blacklist invalid token
    
    def is_token_blacklisted(self, jti: str) -> bool:
        """Check if token is blacklisted"""
        return cache.get(f"blacklisted_token:{jti}", False)


class InputSanitizer:
    """Input sanitization for security"""
    
    @staticmethod
    def sanitize_string(input_string: str, max_length: int = 1000) -> str:
        """Sanitize string input"""
        if not isinstance(input_string, str):
            return str(input_string)
        
        # Remove null bytes
        sanitized = input_string.replace('\x00', '')
        
        # Truncate if too long
        if len(sanitized) > max_length:
            sanitized = sanitized[:max_length]
        
        # Remove potentially dangerous characters
        dangerous_chars = ['<', '>', '"', "'", '&', '\x00', '\x01', '\x02', '\x03', '\x04', '\x05', '\x06', '\x07', '\x08', '\x0b', '\x0c', '\x0e', '\x0f', '\x10', '\x11', '\x12', '\x13', '\x14', '\x15', '\x16', '\x17', '\x18', '\x19', '\x1a', '\x1b', '\x1c', '\x1d', '\x1e', '\x1f']
        for char in dangerous_chars:
            sanitized = sanitized.replace(char, '')
        
        return sanitized.strip()
    
    @staticmethod
    def sanitize_dict(data: Dict[str, Any], max_length: int = 1000) -> Dict[str, Any]:
        """Sanitize dictionary input"""
        sanitized = {}
        
        for key, value in data.items():
            # Sanitize key
            clean_key = InputSanitizer.sanitize_string(str(key), max_length)
            
            # Sanitize value
            if isinstance(value, str):
                clean_value = InputSanitizer.sanitize_string(value, max_length)
            elif isinstance(value, dict):
                clean_value = InputSanitizer.sanitize_dict(value, max_length)
            elif isinstance(value, list):
                clean_value = [InputSanitizer.sanitize_string(str(item), max_length) if isinstance(item, str) else item for item in value]
            else:
                clean_value = value
            
            sanitized[clean_key] = clean_value
        
        return sanitized


class SecurityMonitor:
    """Security event monitoring"""
    
    def __init__(self):
        self.logger = get_enterprise_logger('security_monitor')
        self.rate_limiter = RateLimiter()
    
    def log_security_event(
        self,
        event_type: str,
        severity: SecurityLevel,
        user_id: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        """Log security event"""
        event = SecurityEvent(
            event_type=event_type,
            severity=severity,
            user_id=user_id,
            ip_address=ip_address,
            user_agent=user_agent,
            details=details or {},
            timestamp=datetime.utcnow()
        )
        
        # Log to security logger
        self.logger.log_security_event(
            event_type=event_type,
            severity=severity.value,
            details=details or {},
            context={
                'user_id': user_id,
                'ip_address': ip_address,
                'user_agent': user_agent
            }
        )
        
        # Store in cache for real-time monitoring
        self._store_security_event(event)
        
        # Check for suspicious patterns
        self._check_suspicious_patterns(event)
    
    def _store_security_event(self, event: SecurityEvent):
        """Store security event in cache"""
        try:
            cache_key = "security_events:recent"
            recent_events = cache.get(cache_key, [])
            recent_events.append({
                'event_type': event.event_type,
                'severity': event.severity.value,
                'user_id': event.user_id,
                'ip_address': event.ip_address,
                'timestamp': event.timestamp.isoformat(),
                'details': event.details
            })
            
            # Keep only last 100 events
            if len(recent_events) > 100:
                recent_events = recent_events[-100:]
            
            cache.set(cache_key, recent_events, timeout=3600)  # 1 hour
        except Exception as e:
            self.logger.error(f"Failed to store security event: {e}")
    
    def _check_suspicious_patterns(self, event: SecurityEvent):
        """Check for suspicious security patterns"""
        # Check for multiple failed login attempts
        if event.event_type == "failed_login" and event.user_id:
            if self.rate_limiter.is_rate_limited(f"login:{event.user_id}", "failed_login", max_attempts=5, window_minutes=15):
                self.log_security_event(
                    "multiple_failed_logins",
                    SecurityLevel.HIGH,
                    user_id=event.user_id,
                    ip_address=event.ip_address,
                    details={"pattern": "multiple_failed_logins"}
                )
        
        # Check for multiple failed attempts from same IP
        if event.event_type == "failed_login" and event.ip_address:
            if self.rate_limiter.is_rate_limited(f"ip:{event.ip_address}", "failed_login", max_attempts=10, window_minutes=15):
                self.log_security_event(
                    "suspicious_ip_activity",
                    SecurityLevel.HIGH,
                    ip_address=event.ip_address,
                    details={"pattern": "multiple_failed_logins_from_ip"}
                )
    
    def get_recent_security_events(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get recent security events"""
        cache_key = "security_events:recent"
        return cache.get(cache_key, [])[-limit:]


class CSRFProtection:
    """CSRF protection utilities"""
    
    @staticmethod
    def generate_csrf_token() -> str:
        """Generate CSRF token"""
        return secrets.token_urlsafe(32)
    
    @staticmethod
    def verify_csrf_token(token: str, session_token: str) -> bool:
        """Verify CSRF token"""
        return hmac.compare_digest(token, session_token)
    
    @staticmethod
    def validate_csrf_header(request) -> bool:
        """Validate CSRF header"""
        csrf_token = request.META.get('HTTP_X_CSRFTOKEN')
        if not csrf_token:
            return False
        
        # In a real implementation, you'd compare with session token
        # For now, just check if it's a valid format
        return len(csrf_token) >= 32


class SecurityHeaders:
    """Security headers management"""
    
    @staticmethod
    def get_security_headers() -> Dict[str, str]:
        """Get security headers"""
        return {
            'X-Content-Type-Options': 'nosniff',
            'X-Frame-Options': 'DENY',
            'X-XSS-Protection': '1; mode=block',
            'Strict-Transport-Security': 'max-age=31536000; includeSubDomains',
            'Content-Security-Policy': "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'",
            'Referrer-Policy': 'strict-origin-when-cross-origin',
            'Permissions-Policy': 'geolocation=(), microphone=(), camera=()'
        }
    
    @staticmethod
    def add_security_headers(response):
        """Add security headers to response"""
        headers = SecurityHeaders.get_security_headers()
        for header, value in headers.items():
            response[header] = value
        return response


# Global security instances
password_validator = PasswordValidator()
rate_limiter = RateLimiter()
jwt_manager = JWTManager()
input_sanitizer = InputSanitizer()
security_monitor = SecurityMonitor()
csrf_protection = CSRFProtection()
security_headers = SecurityHeaders()
