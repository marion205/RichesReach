import os
import json
import asyncio
import logging
import time
from typing import Dict, List, Optional

try:
    import redis.asyncio as aioredis
except ImportError:
    aioredis = None

try:
    from cachetools import TTLCache
except ImportError:
    # Fallback if cachetools not available
    class TTLCache(dict):
        def __init__(self, maxsize=2000, ttl=5):
            self.maxsize = maxsize
            self.ttl = ttl
            self._timestamps = {}
        
        def get(self, key, default=None):
            if key in self._timestamps:
                if time.time() - self._timestamps[key] < self.ttl:
                    return super().get(key, default)
                else:
                    # Expired
                    self.pop(key, None)
                    self._timestamps.pop(key, None)
            return default
        
        def __setitem__(self, key, value):
            if len(self) >= self.maxsize:
                # Remove oldest
                oldest_key = min(self._timestamps.keys(), key=lambda k: self._timestamps[k])
                self.pop(oldest_key, None)
                self._timestamps.pop(oldest_key, None)
            super().__setitem__(key, value)
            self._timestamps[key] = time.time()

log = logging.getLogger("price_cache")

class PriceCache:
    """Redis (TLS if rediss://) with local TTL fallback; batched get/set."""
    
    def __init__(self, url: Optional[str] = None, ttl_sec: int = 5, maxsize: int = 2000):
        self.ttl = ttl_sec
        self.local = TTLCache(maxsize=maxsize, ttl=ttl_sec)
        self.redis = None
        
        if url and aioredis:
            try:
                ssl = url.startswith("rediss://")
                self.redis = aioredis.from_url(
                    url, 
                    encoding="utf-8", 
                    decode_responses=True, 
                    ssl=ssl,
                    socket_connect_timeout=2,
                    socket_timeout=2,
                    retry_on_timeout=False
                )
                log.info("✅ Redis cache initialized with URL: %s", url[:20] + "..." if len(url) > 20 else url)
            except Exception as e:
                log.warning("⚠️ Redis disabled: %s", e)
                self.redis = None
        else:
            log.info("📦 Using in-memory cache only (Redis not available)")

    async def mget(self, symbols: List[str]) -> Dict[str, float]:
        """Get multiple prices from cache (local first, then Redis)"""
        out: Dict[str, float] = {}
        miss: List[str] = []
        
        # Local cache first
        for s in symbols:
            v = self.local.get(s)
            if v is not None:
                out[s] = v
            else:
                miss.append(s)
        
        # Redis if available and we have misses
        if self.redis and miss:
            try:
                vals = await asyncio.wait_for(self.redis.mget(miss), timeout=1.0)
                for s, v in zip(miss, vals):
                    if v is not None:
                        try:
                            price = float(v)
                            out[s] = price
                            self.local[s] = price  # Update local cache
                        except (ValueError, TypeError):
                            log.warning("Invalid price value for %s: %s", s, v)
            except asyncio.TimeoutError:
                log.warning("Redis mget timeout for symbols: %s", miss)
            except Exception as e:
                log.warning("Redis mget failed: %s", e)
        
        return out

    async def mset(self, prices: Dict[str, float]):
        """Set multiple prices in cache (local + Redis)"""
        # Update local cache
        for k, v in prices.items():
            self.local[k] = float(v)
        
        # Update Redis if available
        if self.redis and prices:
            try:
                async with self.redis.pipeline(transaction=False) as p:
                    for k, v in prices.items():
                        p.setex(k, self.ttl, float(v))
                    await asyncio.wait_for(p.execute(), timeout=1.0)
            except asyncio.TimeoutError:
                log.warning("Redis mset timeout for %d prices", len(prices))
            except Exception as e:
                log.warning("Redis mset failed: %s", e)

    async def close(self):
        """Close Redis connection"""
        if self.redis:
            try:
                await self.redis.close()
            except Exception as e:
                log.warning("Error closing Redis connection: %s", e)

# Global instance
price_cache = PriceCache(
    url=os.getenv("REDIS_URL"),
    ttl_sec=int(os.getenv("PRICE_TTL_SECONDS", "5")),
    maxsize=int(os.getenv("PRICE_CACHE_SIZE", "2000"))
)
