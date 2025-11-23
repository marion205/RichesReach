# core/auth_utils.py

import secrets

import hashlib

from datetime import timedelta


from django.core.cache import cache

from django.utils import timezone


class RateLimiter:
    """Rate limiting utility for authentication attempts."""

    @staticmethod
    def get_client_ip(request):
        """

        Extract client IP address from the request.

        Honors X-Forwarded-For if present.

        """

        x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")

        if x_forwarded_for:

            ip = x_forwarded_for.split(",")[0].strip()

        else:

            ip = request.META.get("REMOTE_ADDR")

        return ip

    @staticmethod
    def is_rate_limited(
        request,
        action: str = "login",
        max_attempts: int = 5,
        window_minutes: int = 15,
    ):
        """

        Check if client is rate limited for a specific action.



        Args:

            request: Django request object

            action: Type of action (login, signup, password_reset, etc.)

            max_attempts: Maximum attempts allowed in the window

            window_minutes: Time window in minutes



        Returns:

            tuple: (is_limited: bool, attempts_remaining: int, reset_time: datetime|None)

        """

        ip = RateLimiter.get_client_ip(request)

        cache_key = f"rate_limit_{action}_{ip}"

        attempts = cache.get(cache_key, 0)

        if attempts >= max_attempts:

            reset_time = cache.get(
                f"{cache_key}_reset",
                timezone.now() + timedelta(minutes=window_minutes),
            )

            return True, 0, reset_time

        return False, max_attempts - attempts, None

    @staticmethod
    def record_attempt(
        request,
        action: str = "login",
        window_minutes: int = 15,
    ):
        """Record an attempt for rate limiting."""

        ip = RateLimiter.get_client_ip(request)

        cache_key = f"rate_limit_{action}_{ip}"

        reset_key = f"{cache_key}_reset"

        attempts = cache.get(cache_key, 0) + 1

        cache.set(cache_key, attempts, timeout=window_minutes * 60)

        # Set reset time if this is the first attempt

        if attempts == 1:

            cache.set(
                reset_key,
                timezone.now() + timedelta(minutes=window_minutes),
                timeout=window_minutes * 60,
            )

    @staticmethod
    def clear_attempts(request, action: str = "login"):
        """Clear rate limit attempts (e.g., on successful login)."""

        ip = RateLimiter.get_client_ip(request)

        cache_key = f"rate_limit_{action}_{ip}"

        reset_key = f"{cache_key}_reset"

        cache.delete(cache_key)

        cache.delete(reset_key)


class PasswordValidator:
    """Password strength validation utility."""

    @staticmethod
    def validate_password(password: str):
        """

        Validate password strength.



        Returns:

            dict: {

                'is_valid': bool,

                'score': int (0-6),

                'strength': str,

                'requirements': dict,

                'suggestions': list[str],

            }

        """

        requirements = {
            "min_length": len(password) >= 8,
            "has_uppercase": any(c.isupper() for c in password),
            "has_lowercase": any(c.islower() for c in password),
            "has_numbers": any(c.isdigit() for c in password),
            "has_special": any(c in '!@#$%^&*(),.?":{}|<>' for c in password),
            "no_common_patterns": not PasswordValidator._has_common_patterns(password),
        }

        score = sum(requirements.values())

        if score <= 2:

            strength = "Weak"

        elif score <= 3:

            strength = "Fair"

        elif score <= 4:

            strength = "Good"

        else:

            strength = "Strong"

        # Require at least 4 out of 6 requirements

        is_valid = score >= 4

        suggestions = []

        if not requirements["min_length"]:

            suggestions.append("Use at least 8 characters")

        if not requirements["has_uppercase"]:

            suggestions.append("Add uppercase letters")

        if not requirements["has_lowercase"]:

            suggestions.append("Add lowercase letters")

        if not requirements["has_numbers"]:

            suggestions.append("Add numbers")

        if not requirements["has_special"]:

            suggestions.append("Add special characters")

        if not requirements["no_common_patterns"]:

            suggestions.append('Avoid common patterns like "123" or "abc"')

        return {
            "is_valid": is_valid,
            "score": score,
            "strength": strength,
            "requirements": requirements,
            "suggestions": suggestions,
        }

    @staticmethod
    def _has_common_patterns(password: str) -> bool:
        """Check for common weak patterns."""

        common_patterns = [
            "123",
            "abc",
            "password",
            "qwerty",
            "admin",
            "letmein",
            "welcome",
            "monkey",
            "dragon",
        ]

        password_lower = password.lower()

        return any(pattern in password_lower for pattern in common_patterns)


class SecurityUtils:
    """General security utilities."""

    @staticmethod
    def generate_secure_token(length: int = 32) -> str:
        """Generate a cryptographically secure random token."""

        return secrets.token_urlsafe(length)

    @staticmethod
    def hash_sensitive_data(data: str) -> str:
        """Hash sensitive data for logging/storage (shortened hex)."""

        return hashlib.sha256(data.encode()).hexdigest()[:16]

    @staticmethod
    def is_suspicious_request(request) -> bool:
        """

        Basic suspicious request detection.



        Heuristics:

        - Suspicious user agents (bot/crawler/scraper)

        - Too many requests from same IP in a short time window

        """

        user_agent = request.META.get("HTTP_USER_AGENT", "").lower()

        suspicious_agents = ["bot", "crawler", "spider", "scraper"]

        if any(agent in user_agent for agent in suspicious_agents):

            return True

        ip = RateLimiter.get_client_ip(request)

        cache_key = f"request_count_{ip}"

        count = cache.get(cache_key, 0) + 1

        cache.set(cache_key, count, timeout=60)  # 1 minute window

        if count > 100:  # More than 100 requests per minute

            return True

        return False


class AccountLockout:
    """Account lockout management."""

    @staticmethod
    def is_account_locked(user) -> bool:
        """Check if user account is locked."""

        if hasattr(user, "locked_until") and user.locked_until:

            return timezone.now() < user.locked_until

        return False

    @staticmethod
    def lock_account(user, minutes: int = 30):
        """Lock user account for specified minutes."""

        if hasattr(user, "locked_until"):

            user.locked_until = timezone.now() + timedelta(minutes=minutes)

            user.save()

    @staticmethod
    def unlock_account(user):
        """Unlock user account."""

        if hasattr(user, "locked_until"):

            user.locked_until = None

            user.save()

    @staticmethod
    def record_failed_attempt(user):
        """Record a failed login attempt and lock after threshold."""

        if hasattr(user, "failed_login_attempts"):

            user.failed_login_attempts += 1

            if user.failed_login_attempts >= 5:

                AccountLockout.lock_account(user, minutes=30)

            user.save()

    @staticmethod
    def clear_failed_attempts(user):
        """Clear failed login attempts (on successful login)."""

        if hasattr(user, "failed_login_attempts"):

            user.failed_login_attempts = 0

            user.save()
