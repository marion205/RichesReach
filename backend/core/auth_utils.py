"""
Authentication utilities for ML mutations
Handles user authentication, rate limiting, and security
"""
import time
import hashlib
import logging
from typing import Optional, Dict, Any, Tuple
from django.core.cache import cache
from django.contrib.auth import get_user_model
from django.conf import settings
from graphql import GraphQLError

logger = logging.getLogger(__name__)
User = get_user_model()

class RateLimiter:
    """Rate limiting utility for ML mutations"""
    
    @staticmethod
    def is_rate_limited(context, action: str, max_attempts: int, window_minutes: int) -> Tuple[bool, Optional[str], Optional[int]]:
        """
        Check if user is rate limited for a specific action
        
        Returns:
            (is_limited, message, retry_after_seconds)
        """
        try:
            # Get user from context
            user = getattr(context, 'user', None)
            if not user or user.is_anonymous:
                return False, None, None
            
            # Create rate limit key
            key = f"rate_limit:{action}:{user.id}"
            
            # Get current count
            current_count = cache.get(key, 0)
            
            if current_count >= max_attempts:
                # Calculate retry after time
                retry_after = window_minutes * 60
                return True, f"Rate limit exceeded for {action}. Try again in {window_minutes} minutes.", retry_after
            
            return False, None, None
            
        except Exception as e:
            logger.error(f"Rate limiting error: {e}")
            return False, None, None
    
    @staticmethod
    def record_attempt(context, action: str, window_minutes: int) -> None:
        """Record an attempt for rate limiting"""
        try:
            user = getattr(context, 'user', None)
            if not user or user.is_anonymous:
                return
            
            key = f"rate_limit:{action}:{user.id}"
            
            # Increment counter
            current_count = cache.get(key, 0)
            cache.set(key, current_count + 1, window_minutes * 60)
            
        except Exception as e:
            logger.error(f"Rate limiting record error: {e}")

class MLMutationAuth:
    """Authentication utilities for ML mutations"""
    
    @staticmethod
    def require_authentication(context) -> User:
        """Require user to be authenticated for ML mutations"""
        user = getattr(context, 'user', None)
        
        if not user or user.is_anonymous:
            raise GraphQLError("Authentication required for ML mutations. Please log in.")
        
        return user
    
    @staticmethod
    def require_income_profile(user: User) -> Any:
        """Require user to have an income profile"""
        try:
            from .models import IncomeProfile
            return user.incomeProfile
        except IncomeProfile.DoesNotExist:
            raise GraphQLError(
                "Income profile required for ML mutations. "
                "Please create your income profile first to get personalized recommendations."
            )
    
    @staticmethod
    def check_user_permissions(user: User, feature: str) -> bool:
        """Check if user has permissions for specific features"""
        try:
            # Check if user has premium access for institutional features
            if feature == "institutional_ml":
                return getattr(user, 'hasPremiumAccess', False) or getattr(user, 'subscriptionTier', '') in ['PREMIUM', 'ENTERPRISE']
            
            # Check if user has basic access for ML features
            if feature == "basic_ml":
                return True  # All authenticated users can use basic ML
            
            return False
            
        except Exception as e:
            logger.error(f"Permission check error: {e}")
            return False
    
    @staticmethod
    def get_user_context(user: User) -> Dict[str, Any]:
        """Get user context for ML mutations"""
        try:
            profile = MLMutationAuth.require_income_profile(user)
            
            return {
                'user_id': user.id,
                'username': user.username,
                'email': user.email,
                'has_premium': getattr(user, 'hasPremiumAccess', False),
                'subscription_tier': getattr(user, 'subscriptionTier', 'BASIC'),
                'income_profile': {
                    'age': profile.age,
                    'income_bracket': profile.income_bracket,
                    'investment_goals': profile.investment_goals,
                    'risk_tolerance': profile.risk_tolerance,
                    'investment_horizon': profile.investment_horizon,
                }
            }
            
        except Exception as e:
            logger.error(f"User context error: {e}")
            return {
                'user_id': user.id,
                'username': user.username,
                'email': user.email,
                'has_premium': False,
                'subscription_tier': 'BASIC',
                'income_profile': None
            }

class SecurityUtils:
    """Security utilities for ML mutations"""
    
    @staticmethod
    def validate_input_data(data: Dict[str, Any], required_fields: list) -> bool:
        """Validate input data for ML mutations"""
        try:
            for field in required_fields:
                if field not in data:
                    return False
                
                # Additional validation based on field type
                if field == 'modelVersion' and not isinstance(data[field], str):
                    return False
                if field == 'universe' and not isinstance(data[field], list):
                    return False
                if field == 'constraints' and not isinstance(data[field], dict):
                    return False
            
            return True
            
        except Exception as e:
            logger.error(f"Input validation error: {e}")
            return False
    
    @staticmethod
    def sanitize_input(data: Dict[str, Any]) -> Dict[str, Any]:
        """Sanitize input data for ML mutations"""
        try:
            sanitized = {}
            
            for key, value in data.items():
                if isinstance(value, str):
                    # Remove potentially dangerous characters
                    sanitized[key] = value.strip()[:1000]  # Limit string length
                elif isinstance(value, (int, float)):
                    # Validate numeric ranges
                    if key == 'universe_limit':
                        sanitized[key] = max(1, min(5000, int(value)))
                    elif key == 'top_n':
                        sanitized[key] = max(1, min(100, int(value)))
                    else:
                        sanitized[key] = value
                elif isinstance(value, list):
                    # Limit list size and sanitize items
                    sanitized[key] = [str(item)[:50] for item in value[:100]]
                elif isinstance(value, dict):
                    # Recursively sanitize dict
                    sanitized[key] = SecurityUtils.sanitize_input(value)
                else:
                    sanitized[key] = value
            
            return sanitized
            
        except Exception as e:
            logger.error(f"Input sanitization error: {e}")
            return data
    
    @staticmethod
    def generate_audit_hash(data: Dict[str, Any]) -> str:
        """Generate audit hash for ML mutation inputs"""
        try:
            # Create a stable hash of the input data
            import json
            data_str = json.dumps(data, sort_keys=True, separators=(',', ':'))
            return hashlib.sha256(data_str.encode()).hexdigest()[:16]
            
        except Exception as e:
            logger.error(f"Audit hash generation error: {e}")
            return "unknown"

class MLMutationValidator:
    """Validator for ML mutation inputs"""
    
    @staticmethod
    def validate_universe(universe: Optional[list]) -> list:
        """Validate and clean universe input"""
        if not universe:
            return []
        
        # Limit universe size
        max_size = getattr(settings, 'INSTITUTIONAL_CONFIG', {}).get('MAX_UNIVERSE_SIZE', 2000)
        if len(universe) > max_size:
            raise GraphQLError(f"Universe size exceeds maximum of {max_size} symbols")
        
        # Validate symbols
        valid_symbols = []
        for symbol in universe:
            if isinstance(symbol, str) and symbol.isalpha() and len(symbol) <= 10:
                valid_symbols.append(symbol.upper())
        
        return valid_symbols
    
    @staticmethod
    def validate_constraints(constraints: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Validate optimization constraints"""
        if not constraints:
            return {}
        
        # Get default constraints from settings
        default_constraints = getattr(settings, 'INSTITUTIONAL_CONFIG', {}).get('DEFAULT_CONSTRAINTS', {})
        
        validated = {}
        
        # Validate each constraint
        for key, value in constraints.items():
            if key in default_constraints:
                if isinstance(value, (int, float)):
                    # Ensure value is within reasonable bounds
                    if key in ['max_weight_per_name', 'max_sector_weight', 'max_turnover']:
                        validated[key] = max(0.0, min(1.0, float(value)))
                    elif key in ['min_liquidity_score']:
                        validated[key] = max(0.0, float(value))
                    elif key in ['risk_aversion', 'cost_aversion']:
                        validated[key] = max(0.0, min(100.0, float(value)))
                    elif key in ['cvar_confidence']:
                        validated[key] = max(0.5, min(0.99, float(value)))
                    else:
                        validated[key] = float(value)
                elif key == 'long_only':
                    validated[key] = bool(value)
                else:
                    validated[key] = value
        
        return validated

def get_ml_mutation_context(info) -> Dict[str, Any]:
    """Get comprehensive context for ML mutations"""
    try:
        # Get user
        user = MLMutationAuth.require_authentication(info.context)
        
        # Get user context
        user_context = MLMutationAuth.get_user_context(user)
        
        # Check permissions
        has_basic_ml = MLMutationAuth.check_user_permissions(user, "basic_ml")
        has_institutional_ml = MLMutationAuth.check_user_permissions(user, "institutional_ml")
        
        return {
            'user': user,
            'user_context': user_context,
            'permissions': {
                'basic_ml': has_basic_ml,
                'institutional_ml': has_institutional_ml,
            },
            'rate_limiter': RateLimiter(),
            'validator': MLMutationValidator(),
            'security': SecurityUtils(),
        }
        
    except Exception as e:
        logger.error(f"ML mutation context error: {e}")
        raise GraphQLError("Failed to initialize ML mutation context")