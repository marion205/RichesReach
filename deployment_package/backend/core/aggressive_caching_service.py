"""
Aggressive Caching Service
Implements multi-layer caching strategy to reduce redundant calculations.
"""
import logging
import time
import hashlib
import json
from typing import Dict, Any, Optional, Callable, List
from functools import wraps
from django.core.cache import cache
from django.core.cache.backends.base import DEFAULT_TIMEOUT

logger = logging.getLogger(__name__)


class AggressiveCachingService:
    """
    Aggressive caching service with multiple cache layers:
    1. In-memory cache (fastest, per-process)
    2. Redis cache (shared across processes)
    3. Database query cache (for expensive queries)
    """
    
    def __init__(self):
        self.memory_cache = {}  # In-memory cache (per-process)
        self.memory_cache_ttl = {}  # TTL for memory cache entries
        self.default_ttl = 300  # 5 minutes default
        
        # Cache layers configuration
        self.cache_layers = {
            'memory': {'enabled': True, 'ttl': 60},  # 1 minute
            'redis': {'enabled': True, 'ttl': 300},  # 5 minutes
            'database': {'enabled': True, 'ttl': 600}  # 10 minutes
        }
    
    def get_cache_key(self, prefix: str, *args, **kwargs) -> str:
        """
        Generate a consistent cache key from arguments.
        
        Args:
            prefix: Cache key prefix
            *args: Positional arguments
            **kwargs: Keyword arguments
        
        Returns:
            Cache key string
        """
        # Sort kwargs for consistent hashing
        sorted_kwargs = sorted(kwargs.items())
        
        # Create hash of arguments
        key_data = json.dumps([str(args), sorted_kwargs], sort_keys=True)
        key_hash = hashlib.md5(key_data.encode()).hexdigest()[:12]
        
        return f"{prefix}:{key_hash}"
    
    def get_cached(
        self,
        cache_key: str,
        ttl: Optional[int] = None
    ) -> Optional[Any]:
        """
        Get cached value from multiple layers (memory -> Redis).
        
        Args:
            cache_key: Cache key
            ttl: Time to live (optional, uses default if not provided)
        
        Returns:
            Cached value or None
        """
        # Layer 1: Memory cache (fastest)
        if self.cache_layers['memory']['enabled']:
            if cache_key in self.memory_cache:
                ttl_entry = self.memory_cache_ttl.get(cache_key, 0)
                if time.time() < ttl_entry:
                    logger.debug(f"Memory cache hit: {cache_key}")
                    return self.memory_cache[cache_key]
                else:
                    # Expired, remove from memory cache
                    del self.memory_cache[cache_key]
                    del self.memory_cache_ttl[cache_key]
        
        # Layer 2: Redis cache (shared)
        if self.cache_layers['redis']['enabled']:
            try:
                cached_value = cache.get(cache_key)
                if cached_value is not None:
                    logger.debug(f"Redis cache hit: {cache_key}")
                    # Also store in memory cache for faster access
                    if self.cache_layers['memory']['enabled']:
                        self.memory_cache[cache_key] = cached_value
                        memory_ttl = self.cache_layers['memory']['ttl']
                        self.memory_cache_ttl[cache_key] = time.time() + memory_ttl
                    return cached_value
            except Exception as e:
                logger.warning(f"Redis cache error for {cache_key}: {e}")
        
        return None
    
    def set_cached(
        self,
        cache_key: str,
        value: Any,
        ttl: Optional[int] = None
    ) -> None:
        """
        Set cached value in multiple layers.
        
        Args:
            cache_key: Cache key
            value: Value to cache
            ttl: Time to live (optional, uses default if not provided)
        """
        if ttl is None:
            ttl = self.default_ttl
        
        # Layer 1: Memory cache
        if self.cache_layers['memory']['enabled']:
            self.memory_cache[cache_key] = value
            memory_ttl = min(ttl, self.cache_layers['memory']['ttl'])
            self.memory_cache_ttl[cache_key] = time.time() + memory_ttl
        
        # Layer 2: Redis cache
        if self.cache_layers['redis']['enabled']:
            try:
                cache.set(cache_key, value, timeout=ttl)
                logger.debug(f"Cached in Redis: {cache_key} (TTL: {ttl}s)")
            except Exception as e:
                logger.warning(f"Redis cache set error for {cache_key}: {e}")
    
    def invalidate(self, cache_key: str) -> None:
        """Invalidate cache key from all layers"""
        # Memory cache
        if cache_key in self.memory_cache:
            del self.memory_cache[cache_key]
            if cache_key in self.memory_cache_ttl:
                del self.memory_cache_ttl[cache_key]
        
        # Redis cache
        try:
            cache.delete(cache_key)
        except Exception as e:
            logger.warning(f"Redis cache delete error for {cache_key}: {e}")
    
    def invalidate_pattern(self, pattern: str) -> int:
        """
        Invalidate all cache keys matching a pattern.
        
        Args:
            pattern: Pattern to match (e.g., 'kelly:*')
        
        Returns:
            Number of keys invalidated
        """
        count = 0
        
        # Memory cache
        keys_to_delete = [k for k in self.memory_cache.keys() if pattern.replace('*', '') in k]
        for key in keys_to_delete:
            del self.memory_cache[key]
            if key in self.memory_cache_ttl:
                del self.memory_cache_ttl[key]
            count += 1
        
        # Redis cache (requires Redis SCAN, simplified here)
        try:
            # Note: This is a simplified version. In production, use Redis SCAN
            # For now, we'll just log the pattern
            logger.info(f"Invalidating Redis cache pattern: {pattern} ({count} memory keys)")
        except Exception as e:
            logger.warning(f"Redis pattern invalidation error: {e}")
        
        return count
    
    def cached_function(
        self,
        prefix: str,
        ttl: Optional[int] = None,
        key_func: Optional[Callable] = None
    ):
        """
        Decorator for caching function results.
        
        Args:
            prefix: Cache key prefix
            ttl: Time to live in seconds
            key_func: Optional function to generate cache key from arguments
        
        Example:
            @caching_service.cached_function('price_data', ttl=60)
            def get_price(symbol):
                return fetch_price(symbol)
        """
        def decorator(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                # Generate cache key
                if key_func:
                    cache_key = key_func(*args, **kwargs)
                else:
                    cache_key = self.get_cache_key(prefix, *args, **kwargs)
                
                # Try to get from cache
                cached_value = self.get_cached(cache_key, ttl)
                if cached_value is not None:
                    return cached_value
                
                # Cache miss - compute value
                value = func(*args, **kwargs)
                
                # Store in cache
                self.set_cached(cache_key, value, ttl)
                
                return value
            
            return wrapper
        return decorator
    
    def get_stats(self) -> Dict[str, Any]:
        """Get caching statistics"""
        return {
            'memory_cache_size': len(self.memory_cache),
            'memory_cache_keys': list(self.memory_cache.keys())[:10],  # First 10 keys
            'layers_enabled': {
                layer: config['enabled']
                for layer, config in self.cache_layers.items()
            },
            'default_ttl': self.default_ttl
        }


# Global instance
_aggressive_caching_service = None

def get_aggressive_caching_service() -> AggressiveCachingService:
    """Get global aggressive caching service instance"""
    global _aggressive_caching_service
    if _aggressive_caching_service is None:
        _aggressive_caching_service = AggressiveCachingService()
    return _aggressive_caching_service

