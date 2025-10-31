"""
Redis Feature-Hash Caching
==========================
Efficient caching for ML inference results using feature hashing.

Uses BLAKE3 for fast hashing and Redis for storage with TTL.
"""

from __future__ import annotations

import json
import logging
from typing import Any, Dict, Optional, Callable
from dataclasses import dataclass

logger = logging.getLogger(__name__)

# Optional imports
try:
    import blake3
    BLAKE3_AVAILABLE = True
except ImportError:
    BLAKE3_AVAILABLE = False
    logger.warning("blake3 not installed, using hashlib fallback")

try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    logger.warning("redis not installed, caching disabled")


class FeatureCache:
    """
    Redis-backed cache for ML inference results.
    
    Uses feature hashing to create deterministic cache keys.
    """
    
    def __init__(
        self,
        redis_client: Optional[Any] = None,
        key_prefix: str = "ml",
        default_ttl: int = 300
    ):
        """
        Initialize feature cache.
        
        Args:
            redis_client: Redis client instance (will create if None)
            key_prefix: Prefix for cache keys
            default_ttl: Default TTL in seconds
        """
        self.key_prefix = key_prefix
        self.default_ttl = default_ttl
        
        if redis_client is None and REDIS_AVAILABLE:
            try:
                import os
                redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/1")
                self.redis = redis.from_url(redis_url)
            except Exception as e:
                logger.warning(f"Failed to connect to Redis: {e}")
                self.redis = None
        else:
            self.redis = redis_client
    
    def _hash_features(self, features: Dict[str, Any]) -> str:
        """Create deterministic hash of features."""
        # Normalize JSON: sort keys, no spaces
        payload = json.dumps(features, separators=(",", ":"), sort_keys=True)
        
        if BLAKE3_AVAILABLE:
            return blake3.blake3(payload.encode()).hexdigest()
        else:
            import hashlib
            return hashlib.sha256(payload.encode()).hexdigest()
    
    def _cache_key(self, model: str, features: Dict[str, Any]) -> str:
        """Generate cache key."""
        feature_hash = self._hash_features(features)
        return f"{self.key_prefix}:{model}:{feature_hash}"
    
    def get(
        self,
        model: str,
        features: Dict[str, Any]
    ) -> Optional[Any]:
        """
        Get cached result if available.
        
        Args:
            model: Model name
            features: Input features
            
        Returns:
            Cached result or None
        """
        if not self.redis:
            return None
        
        try:
            key = self._cache_key(model, features)
            value = self.redis.get(key)
            if value:
                return json.loads(value)
        except Exception as e:
            logger.warning(f"Cache get failed: {e}")
        
        return None
    
    def set(
        self,
        model: str,
        features: Dict[str, Any],
        result: Any,
        ttl: Optional[int] = None
    ) -> None:
        """
        Cache a result.
        
        Args:
            model: Model name
            features: Input features
            result: Result to cache
            ttl: TTL in seconds (uses default if None)
        """
        if not self.redis:
            return
        
        try:
            key = self._cache_key(model, features)
            value = json.dumps(result)
            ttl = ttl or self.default_ttl
            self.redis.setex(key, ttl, value)
        except Exception as e:
            logger.warning(f"Cache set failed: {e}")
    
    def cached_predict(
        self,
        model: str,
        features: Dict[str, Any],
        infer_fn: Callable[[Dict[str, Any]], Any],
        ttl: Optional[int] = None
    ) -> Any:
        """
        Predict with caching.
        
        Args:
            model: Model name
            features: Input features
            infer_fn: Inference function to call if cache miss
            ttl: TTL for cached result
            
        Returns:
            Inference result (from cache or fresh)
        """
        # Try cache first
        cached = self.get(model, features)
        if cached is not None:
            logger.debug(f"Cache hit for {model}")
            return cached
        
        # Cache miss - run inference
        logger.debug(f"Cache miss for {model}, running inference")
        result = infer_fn(features)
        
        # Cache result
        self.set(model, features, result, ttl)
        
        return result


# Global cache instance
_feature_cache: Optional[FeatureCache] = None


def get_feature_cache() -> FeatureCache:
    """Get global feature cache instance."""
    global _feature_cache
    if _feature_cache is None:
        _feature_cache = FeatureCache()
    return _feature_cache

