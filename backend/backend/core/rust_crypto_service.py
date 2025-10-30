"""
Rust Crypto Analysis Service Integration
High-performance crypto analysis using Rust service
"""

import asyncio
import aiohttp
import json
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import redis
from django.conf import settings

logger = logging.getLogger(__name__)

class RustCryptoService:
    """High-performance crypto analysis service using Rust backend"""
    
    def __init__(self):
        self.rust_base_url = "process.env.WHISPER_API_URL || "http://localhost:3001""
        self.redis_client = None
        self.cache_ttl = 300  # 5 minutes
        self._init_redis()
    
    def _init_redis(self):
        """Initialize Redis connection for caching"""
        try:
            self.redis_client = redis.Redis(
                host=getattr(settings, 'REDIS_HOST', 'localhost'),
                port=getattr(settings, 'REDIS_PORT', 6379),
                db=getattr(settings, 'REDIS_DB', 0),
                decode_responses=True
            )
            # Test connection
            self.redis_client.ping()
            logger.info("✅ Redis connected successfully")
        except Exception as e:
            logger.warning(f"⚠️ Redis not available: {e}")
            self.redis_client = None
    
    async def _make_request(self, endpoint: str, method: str = "GET", data: Optional[Dict] = None) -> Optional[Dict]:
        """Make HTTP request to production-grade Rust service"""
        try:
            url = f"{self.rust_base_url}/{endpoint}"
            async with aiohttp.ClientSession() as session:
                if method == "POST":
                    async with session.post(url, json=data) as response:
                        if response.status == 200:
                            return await response.json()
                else:
                    async with session.get(url, params=data) as response:
                        if response.status == 200:
                            return await response.json()
                
                logger.error(f"Rust service error: {response.status}")
                return None
        except Exception as e:
            logger.error(f"Error calling Rust service: {e}")
            return None
    
    def _get_cache_key(self, prefix: str, identifier: str) -> str:
        """Generate cache key"""
        return f"rust_crypto:{prefix}:{identifier}"
    
    async def _get_from_cache(self, key: str) -> Optional[Dict]:
        """Get data from Redis cache"""
        if not self.redis_client:
            return None
        
        try:
            cached = self.redis_client.get(key)
            if cached:
                return json.loads(cached)
        except Exception as e:
            logger.warning(f"Cache get error: {e}")
        return None
    
    async def _set_cache(self, key: str, data: Dict, ttl: int = None) -> bool:
        """Set data in Redis cache"""
        if not self.redis_client:
            return False
        
        try:
            ttl = ttl or self.cache_ttl
            self.redis_client.setex(key, ttl, json.dumps(data))
            return True
        except Exception as e:
            logger.warning(f"Cache set error: {e}")
            return False
    
    async def analyze_crypto(self, symbol: str, timeframe: str = "ALL") -> Optional[Dict]:
        """Analyze cryptocurrency using Rust service"""
        cache_key = self._get_cache_key("analysis", f"{symbol.upper()}::{timeframe}")
        
        # Try cache first
        cached_result = await self._get_from_cache(cache_key)
        if cached_result:
            logger.info(f"Cache hit for {symbol} analysis")
            return cached_result
        
        # Call production-grade Rust service
        logger.info(f"Calling production Rust service for {symbol} analysis")
        start_time = datetime.now()
        
        result = await self._make_request("v1/analyze", "POST", {"symbol": symbol, "timeframe": timeframe})
        
        if result:
            duration = (datetime.now() - start_time).total_seconds()
            logger.info(f"Rust analysis completed for {symbol} in {duration:.3f}s")
            
            # Cache the result
            await self._set_cache(cache_key, result)
            return result
        
        return None
    
    async def get_crypto_recommendations(self, limit: int = 6, symbols: Optional[List[str]] = None) -> Optional[List[Dict]]:
        """Get crypto recommendations using Rust service"""
        cache_key = self._get_cache_key("recommendations", f"{limit}:{':'.join(symbols or [])}")
        
        # Try cache first
        cached_result = await self._get_from_cache(cache_key)
        if cached_result:
            logger.info("Cache hit for recommendations")
            return cached_result
        
        # Call production-grade Rust service
        logger.info("Calling production Rust service for recommendations")
        start_time = datetime.now()
        
        params = {"limit": limit}
        if symbols:
            params["symbols"] = ",".join(symbols)
        
        result = await self._make_request("v1/recommendations", "GET", params)
        
        if result:
            duration = (datetime.now() - start_time).total_seconds()
            logger.info(f"Rust recommendations completed in {duration:.3f}s")
            
            # Cache the result
            await self._set_cache(cache_key, result, ttl=600)  # 10 minutes for recommendations
            return result
        
        return None
    
    async def get_rust_health(self) -> Optional[Dict]:
        """Check production Rust service health"""
        return await self._make_request("health/live")
    
    async def get_rust_readiness(self) -> Optional[Dict]:
        """Check production Rust service readiness"""
        return await self._make_request("health/ready")
    
    def is_available(self) -> bool:
        """Check if production Rust service is available (synchronous)"""
        try:
            import requests
            response = requests.get(f"{self.rust_base_url}/health/live", timeout=2)
            return response.status_code == 200
        except:
            return False
    
    async def get_metrics(self) -> Optional[str]:
        """Get Prometheus metrics from production Rust service"""
        try:
            import aiohttp
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.rust_base_url}/metrics") as response:
                    if response.status == 200:
                        return await response.text()
        except Exception as e:
            logger.warning(f"Metrics fetch error: {e}")
        return None
    
    async def clear_cache(self, pattern: str = "rust_crypto:*") -> bool:
        """Clear Redis cache"""
        if not self.redis_client:
            return False
        
        try:
            keys = self.redis_client.keys(pattern)
            if keys:
                self.redis_client.delete(*keys)
                logger.info(f"Cleared {len(keys)} cache entries")
            return True
        except Exception as e:
            logger.error(f"Cache clear error: {e}")
            return False

# Global instance
rust_crypto_service = RustCryptoService()

# Convenience functions for easy integration
async def analyze_crypto_with_rust(symbol: str) -> Optional[Dict]:
    """Analyze crypto using Rust service"""
    return await rust_crypto_service.analyze_crypto(symbol)

async def get_crypto_recommendations_with_rust(limit: int = 6, symbols: Optional[List[str]] = None) -> Optional[List[Dict]]:
    """Get crypto recommendations using Rust service"""
    return await rust_crypto_service.get_crypto_recommendations(limit, symbols)

def is_rust_service_available() -> bool:
    """Check if Rust service is available"""
    return rust_crypto_service.is_available()
