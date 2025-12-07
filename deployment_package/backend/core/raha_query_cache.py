"""
RAHA Query Result Caching
Implements caching for expensive RAHA GraphQL queries to improve performance
"""
import logging
import hashlib
import json
from typing import Any, Optional
from django.core.cache import cache
from django.contrib.auth import get_user_model

User = get_user_model()
logger = logging.getLogger(__name__)


def get_cache_key(prefix: str, user_id: int, **kwargs) -> str:
    """
    Generate a cache key from prefix, user_id, and optional kwargs.
    
    Args:
        prefix: Cache key prefix (e.g., 'raha_signals', 'strategy_dashboard')
        user_id: User ID for user-specific caching
        **kwargs: Additional parameters to include in cache key
    
    Returns:
        Cache key string
    """
    # Sort kwargs for consistent key generation
    sorted_kwargs = sorted(kwargs.items())
    kwargs_str = json.dumps(sorted_kwargs, sort_keys=True)
    
    # Create hash for long keys
    key_str = f"{prefix}:user_{user_id}:{kwargs_str}"
    if len(key_str) > 200:
        key_hash = hashlib.md5(key_str.encode()).hexdigest()
        return f"{prefix}:user_{user_id}:{key_hash}"
    
    return key_str


def cache_query_result(
    cache_key: str,
    result: Any,
    timeout: int = 300,
    version: Optional[int] = None
) -> bool:
    """
    Cache a query result.
    
    Args:
        cache_key: Cache key
        result: Result to cache (must be JSON-serializable)
        timeout: Cache timeout in seconds (default: 5 minutes)
        version: Optional cache version
    
    Returns:
        True if cached successfully, False otherwise
    """
    try:
        cache.set(cache_key, result, timeout=timeout, version=version)
        return True
    except Exception as e:
        logger.warning(f"Failed to cache query result: {e}")
        return False


def get_cached_query_result(
    cache_key: str,
    version: Optional[int] = None
) -> Optional[Any]:
    """
    Get a cached query result.
    
    Args:
        cache_key: Cache key
        version: Optional cache version
    
    Returns:
        Cached result or None if not found
    """
    try:
        return cache.get(cache_key, version=version)
    except Exception as e:
        logger.warning(f"Failed to get cached query result: {e}")
        return None


def invalidate_cache_pattern(pattern: str) -> int:
    """
    Invalidate cache entries matching a pattern.
    Note: This is a simple implementation. For production, consider using
    Redis with SCAN for pattern matching.
    
    Args:
        pattern: Cache key pattern (e.g., 'raha_signals:user_*')
    
    Returns:
        Number of entries invalidated
    """
    # For LocMemCache, we can't easily pattern match
    # For Redis, we'd use SCAN with pattern matching
    # For now, this is a placeholder
    logger.info(f"Cache invalidation requested for pattern: {pattern}")
    return 0


# Cache timeout constants (in seconds)
CACHE_TIMEOUTS = {
    'strategies': 3600,  # 1 hour - strategies rarely change
    'strategy': 3600,  # 1 hour
    'user_strategy_settings': 300,  # 5 minutes - user settings change occasionally
    'raha_signals': 60,  # 1 minute - signals are real-time
    'backtest_run': 300,  # 5 minutes - backtest results don't change
    'user_backtests': 180,  # 3 minutes - backtest list changes when new backtests run
    'raha_metrics': 300,  # 5 minutes - metrics update periodically
    'strategy_dashboard': 300,  # 5 minutes - dashboard aggregates update periodically
    'ml_models': 300,  # 5 minutes - ML models change when training completes
    'strategy_blends': 300,  # 5 minutes
    'notification_preferences': 600,  # 10 minutes - preferences change rarely
    'auto_trading_settings': 600,  # 10 minutes - settings change rarely
}

