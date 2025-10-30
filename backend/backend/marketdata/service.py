# marketdata/service.py
import json
import os
import hashlib
import time
import logging
from typing import Dict, Any, Optional
from django.conf import settings
from .provider_selector import ProviderSelector
from .models import Quote, OptionContract, Equity

logger = logging.getLogger(__name__)

# Redis configuration
try:
    import redis
    redis_client = redis.Redis.from_url(
        os.getenv("REDIS_URL", "redis://process.env.REDIS_HOST || "localhost:6379"/0"),
        decode_responses=True
    )
    REDIS_AVAILABLE = True
    logger.info("Redis client initialized")
except Exception as e:
    logger.warning(f"Redis not available: {e}")
    redis_client = None
    REDIS_AVAILABLE = False

class MarketDataService:
    """Main service for market data operations with caching and provider management"""
    
    def __init__(self):
        self.selector = ProviderSelector()
        self.cache_ttl = {
            "quote": 10,  # 10 seconds for quotes
            "profile": 3600,  # 1 hour for profiles
            "options": 300,  # 5 minutes for options
            "fundamentals": 1800,  # 30 minutes for fundamentals
        }
    
    def _cache_key(self, kind: str, **params) -> str:
        """Generate cache key for data"""
        key_data = kind + ":" + json.dumps(params, sort_keys=True)
        return f"md:{hashlib.sha1(key_data.encode()).hexdigest()}"
    
    def _get_from_cache(self, cache_key: str) -> Optional[Dict[str, Any]]:
        """Get data from Redis cache"""
        if not REDIS_AVAILABLE:
            return None
        
        try:
            cached_data = redis_client.get(cache_key)
            if cached_data:
                return json.loads(cached_data)
        except Exception as e:
            logger.warning(f"Cache read error: {e}")
        
        return None
    
    def _set_cache(self, cache_key: str, data: Dict[str, Any], ttl: int):
        """Set data in Redis cache"""
        if not REDIS_AVAILABLE:
            return
        
        try:
            redis_client.setex(cache_key, ttl, json.dumps(data))
        except Exception as e:
            logger.warning(f"Cache write error: {e}")
    
    def get_quote(self, symbol: str) -> Dict[str, Any]:
        """Get real-time quote with caching"""
        symbol = symbol.upper().strip()
        cache_key = self._cache_key("quote", symbol=symbol)
        
        # Try cache first
        cached_data = self._get_from_cache(cache_key)
        if cached_data:
            logger.debug(f"Cache hit for quote: {symbol}")
            return cached_data
        
        # Get from provider
        try:
            result = self.selector.get_quote(symbol)
            data = result["data"]
            data["provider"] = result["provider"]
            data["cached_at"] = int(time.time())
            
            # Cache the result
            self._set_cache(cache_key, data, self.cache_ttl["quote"])
            
            # Store in database for historical tracking
            self._store_quote_in_db(symbol, data, result["provider"])
            
            logger.info(f"Quote retrieved for {symbol} from {result['provider']}")
            return data
            
        except Exception as e:
            logger.error(f"Failed to get quote for {symbol}: {e}")
            raise
    
    def get_profile(self, symbol: str) -> Dict[str, Any]:
        """Get company profile with caching"""
        symbol = symbol.upper().strip()
        cache_key = self._cache_key("profile", symbol=symbol)
        
        # Try cache first
        cached_data = self._get_from_cache(cache_key)
        if cached_data:
            logger.debug(f"Cache hit for profile: {symbol}")
            return cached_data
        
        # Get from provider
        try:
            result = self.selector.get_profile(symbol)
            data = result["data"]
            data["provider"] = result["provider"]
            data["cached_at"] = int(time.time())
            
            # Cache the result
            self._set_cache(cache_key, data, self.cache_ttl["profile"])
            
            # Store in database
            self._store_equity_in_db(symbol, data, result["provider"])
            
            logger.info(f"Profile retrieved for {symbol} from {result['provider']}")
            return data
            
        except Exception as e:
            logger.error(f"Failed to get profile for {symbol}: {e}")
            raise
    
    def get_options_chain(self, symbol: str, limit: int = 50) -> Dict[str, Any]:
        """Get options chain with caching"""
        symbol = symbol.upper().strip()
        cache_key = self._cache_key("options", symbol=symbol, limit=limit)
        
        # Try cache first
        cached_data = self._get_from_cache(cache_key)
        if cached_data:
            logger.debug(f"Cache hit for options: {symbol}")
            return cached_data
        
        # Get from provider
        try:
            result = self.selector.get_options_chain(symbol, limit)
            data = result["data"]
            data["provider"] = result["provider"]
            data["cached_at"] = int(time.time())
            
            # Cache the result
            self._set_cache(cache_key, data, self.cache_ttl["options"])
            
            # Store contracts in database
            self._store_options_in_db(symbol, data, result["provider"])
            
            logger.info(f"Options chain retrieved for {symbol} from {result['provider']}")
            return data
            
        except Exception as e:
            logger.error(f"Failed to get options chain for {symbol}: {e}")
            raise
    
    def _store_quote_in_db(self, symbol: str, data: Dict[str, Any], provider: str):
        """Store quote data in database"""
        try:
            Quote.objects.create(
                symbol=symbol,
                price=data.get("price", 0),
                change=data.get("change"),
                change_percent=data.get("change_percent"),
                volume=data.get("volume"),
                high=data.get("high"),
                low=data.get("low"),
                open=data.get("open"),
                provider=provider
            )
        except Exception as e:
            logger.warning(f"Failed to store quote in DB: {e}")
    
    def _store_equity_in_db(self, symbol: str, data: Dict[str, Any], provider: str):
        """Store equity profile in database"""
        try:
            equity, created = Equity.objects.get_or_create(
                symbol=symbol,
                defaults={
                    "name": data.get("name"),
                    "exchange": data.get("exchange"),
                    "sector": data.get("sector"),
                    "industry": data.get("industry"),
                    "market_cap": data.get("market_cap"),
                }
            )
            
            if not created:
                # Update existing record
                equity.name = data.get("name") or equity.name
                equity.exchange = data.get("exchange") or equity.exchange
                equity.sector = data.get("sector") or equity.sector
                equity.industry = data.get("industry") or equity.industry
                equity.market_cap = data.get("market_cap") or equity.market_cap
                equity.save()
                
        except Exception as e:
            logger.warning(f"Failed to store equity in DB: {e}")
    
    def _store_options_in_db(self, symbol: str, data: Dict[str, Any], provider: str):
        """Store options contracts in database"""
        try:
            contracts = data.get("contracts", [])
            for contract_data in contracts:
                OptionContract.objects.update_or_create(
                    symbol=contract_data.get("symbol"),
                    provider=provider,
                    defaults={
                        "underlying": symbol,
                        "contract_type": contract_data.get("type", "").upper(),
                        "strike": contract_data.get("strike", 0),
                        "expiration": contract_data.get("expiration"),
                        "bid": contract_data.get("bid"),
                        "ask": contract_data.get("ask"),
                        "last_price": contract_data.get("last_price"),
                        "volume": contract_data.get("volume"),
                        "open_interest": contract_data.get("open_interest"),
                        "implied_volatility": contract_data.get("implied_volatility"),
                    }
                )
        except Exception as e:
            logger.warning(f"Failed to store options in DB: {e}")
    
    def get_provider_status(self) -> Dict[str, Any]:
        """Get status of all providers"""
        return self.selector.get_provider_status()
    
    def clear_cache(self, pattern: str = "md:*"):
        """Clear cache entries matching pattern"""
        if not REDIS_AVAILABLE:
            return {"cleared": 0}
        
        try:
            keys = redis_client.keys(pattern)
            if keys:
                redis_client.delete(*keys)
                logger.info(f"Cleared {len(keys)} cache entries")
                return {"cleared": len(keys)}
            return {"cleared": 0}
        except Exception as e:
            logger.error(f"Failed to clear cache: {e}")
            return {"error": str(e)}
