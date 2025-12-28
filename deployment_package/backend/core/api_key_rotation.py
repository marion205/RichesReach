"""
API Key Rotation Policy Enforcement and Warnings Service

Manages rotation policies, tracks key age, and provides warnings for external API keys.
This is NOT automatic rotation - it's governance and alerting.

For actual rotation:
- Store secrets in AWS Secrets Manager / Parameter Store
- Rotate via scheduled job or runbook
- This service tracks when rotation is needed and warns
"""
import os
import logging
from typing import Dict, Optional, List
from datetime import datetime, timedelta
from django.core.cache import cache
from django.utils import timezone

logger = logging.getLogger(__name__)


class APIKeyRotationPolicy:
    """Policy for API key rotation"""
    
    def __init__(
        self,
        key_name: str,
        rotation_days: int = 90,  # Rotate every 90 days
        warning_days: int = 7,  # Warn 7 days before expiration
        auto_rotate: bool = False,  # Whether to auto-rotate
    ):
        self.key_name = key_name
        self.rotation_days = rotation_days
        self.warning_days = warning_days
        self.auto_rotate = auto_rotate


class APIKeyRotationService:
    """
    Service for managing API key rotation policy enforcement and warnings.
    
    This service:
    - Tracks key age and rotation policies
    - Provides warnings when rotation is needed
    - Does NOT automatically rotate keys (that requires secrets manager + runbook)
    """
    
    # Default rotation policies
    DEFAULT_POLICIES = {
        'YODLEE_CLIENT_ID': APIKeyRotationPolicy('YODLEE_CLIENT_ID', rotation_days=90, warning_days=7),
        'YODLEE_SECRET': APIKeyRotationPolicy('YODLEE_SECRET', rotation_days=90, warning_days=7),
        'ALPHA_VANTAGE_API_KEY': APIKeyRotationPolicy('ALPHA_VANTAGE_API_KEY', rotation_days=180, warning_days=14),
        'POLYGON_API_KEY': APIKeyRotationPolicy('POLYGON_API_KEY', rotation_days=180, warning_days=14),
        'FINNHUB_API_KEY': APIKeyRotationPolicy('FINNHUB_API_KEY', rotation_days=180, warning_days=14),
    }
    
    def __init__(self):
        self.policies: Dict[str, APIKeyRotationPolicy] = {}
        self._load_policies()
    
    def _load_policies(self):
        """Load rotation policies from environment or use defaults"""
        for key_name, default_policy in self.DEFAULT_POLICIES.items():
            # Check for custom policy in env
            rotation_days = int(os.getenv(f'{key_name}_ROTATION_DAYS', default_policy.rotation_days))
            warning_days = int(os.getenv(f'{key_name}_WARNING_DAYS', default_policy.warning_days))
            auto_rotate = os.getenv(f'{key_name}_AUTO_ROTATE', 'false').lower() == 'true'
            
            self.policies[key_name] = APIKeyRotationPolicy(
                key_name=key_name,
                rotation_days=rotation_days,
                warning_days=warning_days,
                auto_rotate=auto_rotate,
            )
    
    def get_key_age(self, key_name: str) -> Optional[timedelta]:
        """Get age of API key (from cache or metadata)"""
        cache_key = f'api_key_created_{key_name}'
        created_timestamp = cache.get(cache_key)
        
        if created_timestamp:
            return timezone.now() - datetime.fromisoformat(created_timestamp)
        
        # If not in cache, assume it was created when service started
        # In production, store this in database or secrets manager metadata
        return None
    
    def record_key_creation(self, key_name: str):
        """Record when an API key was created/rotated"""
        cache_key = f'api_key_created_{key_name}'
        cache.set(cache_key, timezone.now().isoformat(), timeout=365 * 24 * 60 * 60)  # 1 year
        logger.info(f"Recorded creation time for {key_name}")
    
    def check_rotation_needed(self, key_name: str) -> Dict[str, any]:
        """Check if key rotation is needed"""
        if key_name not in self.policies:
            return {
                'needs_rotation': False,
                'reason': 'No rotation policy for this key',
            }
        
        policy = self.policies[key_name]
        key_age = self.get_key_age(key_name)
        
        if not key_age:
            # First time - record creation
            self.record_key_creation(key_name)
            return {
                'needs_rotation': False,
                'reason': 'Key age unknown, recording creation time',
            }
        
        days_old = key_age.days
        days_until_rotation = policy.rotation_days - days_old
        days_until_warning = days_until_rotation - policy.warning_days
        
        needs_rotation = days_old >= policy.rotation_days
        needs_warning = days_until_warning <= 0 and not needs_rotation
        
        result = {
            'needs_rotation': needs_rotation,
            'needs_warning': needs_warning,
            'days_old': days_old,
            'days_until_rotation': days_until_rotation,
            'rotation_days': policy.rotation_days,
        }
        
        if needs_rotation:
            result['reason'] = f'Key is {days_old} days old (rotation every {policy.rotation_days} days)'
            logger.warning(f"🔑 API key {key_name} needs rotation: {result['reason']}")
        elif needs_warning:
            result['reason'] = f'Key will need rotation in {days_until_rotation} days'
            logger.info(f"🔑 API key {key_name} rotation warning: {result['reason']}")
        else:
            result['reason'] = f'Key is {days_old} days old, rotation in {days_until_rotation} days'
        
        return result
    
    def get_all_key_statuses(self) -> Dict[str, Dict]:
        """Get rotation status for all managed keys"""
        statuses = {}
        for key_name in self.policies.keys():
            statuses[key_name] = self.check_rotation_needed(key_name)
        return statuses


# Global instance
_api_key_rotation_service = None

def get_api_key_rotation_service() -> APIKeyRotationService:
    """Get global API key rotation service instance"""
    global _api_key_rotation_service
    if _api_key_rotation_service is None:
        _api_key_rotation_service = APIKeyRotationService()
    return _api_key_rotation_service

