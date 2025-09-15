# core/auth_utils.py
from django.core.cache import cache
from django.utils import timezone
from datetime import timedelta
import hashlib
import ipaddress
class RateLimiter:
"""Rate limiting utility for authentication attempts"""
@staticmethod
def get_client_ip(request):
"""Extract client IP address from request"""
x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
if x_forwarded_for:
ip = x_forwarded_for.split(',')[0]
else:
ip = request.META.get('REMOTE_ADDR')
return ip
@staticmethod
def is_rate_limited(request, action='login', max_attempts=5, window_minutes=15):
"""
Check if client is rate limited for a specific action
Args:
request: Django request object
action: Type of action (login, signup, password_reset)
max_attempts: Maximum attempts allowed in window
window_minutes: Time window in minutes
Returns:
tuple: (is_limited, attempts_remaining, reset_time)
"""
ip = RateLimiter.get_client_ip(request)
cache_key = f"rate_limit_{action}_{ip}"
attempts = cache.get(cache_key, 0)
if attempts >= max_attempts:
# Calculate when the rate limit resets
reset_time = cache.get(f"{cache_key}_reset", timezone.now() + timedelta(minutes=window_minutes))
return True, 0, reset_time
return False, max_attempts - attempts, None
@staticmethod
def record_attempt(request, action='login', window_minutes=15):
"""Record an attempt for rate limiting"""
ip = RateLimiter.get_client_ip(request)
cache_key = f"rate_limit_{action}_{ip}"
reset_key = f"{cache_key}_reset"
attempts = cache.get(cache_key, 0) + 1
cache.set(cache_key, attempts, timeout=window_minutes * 60)
# Set reset time if this is the first attempt
if attempts == 1:
cache.set(reset_key, timezone.now() + timedelta(minutes=window_minutes), timeout=window_minutes * 60)
@staticmethod
def clear_attempts(request, action='login'):
"""Clear rate limit attempts (e.g., on successful login)"""
ip = RateLimiter.get_client_ip(request)
cache_key = f"rate_limit_{action}_{ip}"
reset_key = f"{cache_key}_reset"
cache.delete(cache_key)
cache.delete(reset_key)
class PasswordValidator:
"""Password strength validation utility"""
@staticmethod
def validate_password(password):
"""
Validate password strength
Returns:
dict: {
'is_valid': bool,
'score': int (0-5),
'strength': str,
'requirements': dict,
'suggestions': list
}
"""
requirements = {
'min_length': len(password) >= 8,
'has_uppercase': any(c.isupper() for c in password),
'has_lowercase': any(c.islower() for c in password),
'has_numbers': any(c.isdigit() for c in password),
'has_special': any(c in '!@#$%^&*(),.?":{}|<>' for c in password),
'no_common_patterns': not PasswordValidator._has_common_patterns(password)
}
score = sum(requirements.values())
if score <= 2:
strength = 'Weak'
elif score <= 3:
strength = 'Fair'
elif score <= 4:
strength = 'Good'
else:
strength = 'Strong'
is_valid = score >= 4 # Require at least 4 out of 6 requirements
suggestions = []
if not requirements['min_length']:
suggestions.append('Use at least 8 characters')
if not requirements['has_uppercase']:
suggestions.append('Add uppercase letters')
if not requirements['has_lowercase']:
suggestions.append('Add lowercase letters')
if not requirements['has_numbers']:
suggestions.append('Add numbers')
if not requirements['has_special']:
suggestions.append('Add special characters')
if not requirements['no_common_patterns']:
suggestions.append('Avoid common patterns like "123" or "abc"')
return {
'is_valid': is_valid,
'score': score,
'strength': strength,
'requirements': requirements,
'suggestions': suggestions
}
@staticmethod
def _has_common_patterns(password):
"""Check for common weak patterns"""
common_patterns = [
'123', 'abc', 'password', 'qwerty', 'admin',
'letmein', 'welcome', 'monkey', 'dragon'
]
password_lower = password.lower()
return any(pattern in password_lower for pattern in common_patterns)
class SecurityUtils:
"""General security utilities"""
@staticmethod
def generate_secure_token(length=32):
"""Generate a cryptographically secure random token"""
import secrets
return secrets.token_urlsafe(length)
@staticmethod
def hash_sensitive_data(data):
"""Hash sensitive data for logging/storage"""
return hashlib.sha256(data.encode()).hexdigest()[:16]
@staticmethod
def is_suspicious_request(request):
"""Basic suspicious request detection"""
# Check for common attack patterns
user_agent = request.META.get('HTTP_USER_AGENT', '').lower()
suspicious_agents = ['bot', 'crawler', 'spider', 'scraper']
if any(agent in user_agent for agent in suspicious_agents):
return True
# Check for rapid requests (basic check)
ip = RateLimiter.get_client_ip(request)
cache_key = f"request_count_{ip}"
count = cache.get(cache_key, 0) + 1
cache.set(cache_key, count, timeout=60) # 1 minute window
if count > 100: # More than 100 requests per minute
return True
return False
class AccountLockout:
"""Account lockout management"""
@staticmethod
def is_account_locked(user):
"""Check if user account is locked"""
if hasattr(user, 'locked_until') and user.locked_until:
return timezone.now() < user.locked_until
return False
@staticmethod
def lock_account(user, minutes=30):
"""Lock user account for specified minutes"""
if hasattr(user, 'locked_until'):
user.locked_until = timezone.now() + timedelta(minutes=minutes)
user.save()
@staticmethod
def unlock_account(user):
"""Unlock user account"""
if hasattr(user, 'locked_until'):
user.locked_until = None
user.save()
@staticmethod
def record_failed_attempt(user):
"""Record a failed login attempt"""
if hasattr(user, 'failed_login_attempts'):
user.failed_login_attempts += 1
# Lock account after 5 failed attempts
if user.failed_login_attempts >= 5:
AccountLockout.lock_account(user, minutes=30)
user.save()
@staticmethod
def clear_failed_attempts(user):
"""Clear failed login attempts (on successful login)"""
if hasattr(user, 'failed_login_attempts'):
user.failed_login_attempts = 0
user.save()
