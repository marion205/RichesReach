# core/market_data_service.py
import json
import os
import hashlib
import time
import logging
from typing import Dict, Any, Optional
from django.conf import settings

logger = logging.getLogger(__name__)

# Redis configuration
try:
    import redis
    redis_client = redis.Redis.from_url(
        os.getenv("REDIS_URL", "redis://localhost:6379/0"),
        decode_responses=True,
        socket_connect_timeout=2,
        socket_timeout=2,
        retry_on_timeout=True
    )
    # Test connection
    redis_client.ping()
    REDIS_AVAILABLE = True
    logger.info("✅ Redis client initialized and connected")
except Exception as e:
    logger.warning(f"⚠️ Redis not available: {e}")
    redis_client = None
    REDIS_AVAILABLE = False

class MarketDataService:
    """Market data service with Polygon + Finnhub providers and caching"""
    
    def __init__(self):
        self.cache_ttl = {
            "quote": 30,  # 30 seconds for quotes (increased for better performance)
            "profile": 3600,  # 1 hour for profiles
            "options": 300,  # 5 minutes for options
            "market_status": 60,  # 1 minute for market status
        }
        self.cache_prefix = "md:v1:"  # Version the cache keys
    
    def _cache_key(self, kind: str, **params) -> str:
        """Generate cache key for data"""
        key_data = kind + ":" + json.dumps(params, sort_keys=True)
        return f"{self.cache_prefix}{hashlib.sha1(key_data.encode()).hexdigest()}"
    
    def _get_from_cache(self, cache_key: str) -> Optional[Dict[str, Any]]:
        """Get data from Redis cache"""
        if not REDIS_AVAILABLE:
            return None
        
        try:
            cached_data = redis_client.get(cache_key)
            if cached_data:
                logger.debug(f"🎯 Cache HIT: {cache_key[:20]}...")
                return json.loads(cached_data)
            else:
                logger.debug(f"❌ Cache MISS: {cache_key[:20]}...")
        except Exception as e:
            logger.warning(f"⚠️ Cache read error: {e}")
        
        return None
    
    def _set_cache(self, cache_key: str, data: Dict[str, Any], ttl: int):
        """Set data in Redis cache"""
        if not REDIS_AVAILABLE:
            return
        
        try:
            redis_client.setex(cache_key, ttl, json.dumps(data))
            logger.debug(f"💾 Cache SET: {cache_key[:20]}... (TTL: {ttl}s)")
        except Exception as e:
            logger.warning(f"⚠️ Cache write error: {e}")
    
    def get_quote(self, symbol: str) -> Dict[str, Any]:
        """Get real-time quote with caching and provider fallback"""
        symbol = symbol.upper().strip()
        cache_key = self._cache_key("quote", symbol=symbol)
        
        # Try cache first
        cached_data = self._get_from_cache(cache_key)
        if cached_data:
            logger.debug(f"Cache hit for quote: {symbol}")
            return cached_data
        
        # Try providers in order
        providers = [
            ("polygon", self._get_polygon_quote),
            ("finnhub", self._get_finnhub_quote),
        ]
        
        for provider_name, provider_func in providers:
            try:
                data = provider_func(symbol)
                if data and data.get("price"):
                    data["provider"] = provider_name
                    data["cached_at"] = int(time.time())
                    
                    # Cache the result
                    self._set_cache(cache_key, data, self.cache_ttl["quote"])
                    
                    logger.info(f"Quote retrieved for {symbol} from {provider_name}")
                    return data
            except Exception as e:
                logger.warning(f"{provider_name} quote failed for {symbol}: {e}")
                continue
        
        # Fallback to mock data
        logger.warning(f"All providers failed for {symbol}, using mock data")
        return self._get_mock_quote(symbol)
    
    def _get_polygon_quote(self, symbol: str) -> Dict[str, Any]:
        """Get quote from Polygon.io"""
        import httpx
        
        api_key = getattr(settings, 'POLYGON_API_KEY', None)
        if not api_key or api_key.strip() == '':
            raise Exception("Polygon API key not configured or empty")
        
        try:
            with httpx.Client(timeout=5) as client:
                # Use free tier endpoint - daily open/close data (use yesterday for weekends)
                from datetime import datetime, timedelta
                yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
                
                response = client.get(
                    f"https://api.polygon.io/v1/open-close/{symbol}/{yesterday}",
                    params={"apikey": api_key}
                )
                response.raise_for_status()
                data = response.json()
                
                if data.get("status") == "OK":
                    return {
                        "symbol": symbol,
                        "price": float(data.get("close", 0)),
                        "open": float(data.get("open", 0)),
                        "high": float(data.get("high", 0)),
                        "low": float(data.get("low", 0)),
                        "volume": int(data.get("volume", 0)),
                        "timestamp": int(time.time() * 1000),
                        "after_hours": float(data.get("afterHours", 0)) if data.get("afterHours") else None,
                        "pre_market": float(data.get("preMarket", 0)) if data.get("preMarket") else None,
                    }
                
                raise Exception(f"No quote data available for {symbol}")
            
        except Exception as e:
            raise Exception(f"Polygon API error: {e}")
    
    def _get_finnhub_quote(self, symbol: str) -> Dict[str, Any]:
        """Get quote from Finnhub"""
        import httpx
        
        api_key = getattr(settings, 'FINNHUB_API_KEY', None)
        if not api_key:
            raise Exception("Finnhub API key not configured")
        
        try:
            with httpx.Client(timeout=5) as client:
                response = client.get(
                    "https://finnhub.io/api/v1/quote",
                    params={"symbol": symbol, "token": api_key}
                )
                response.raise_for_status()
                data = response.json()
                
                if data.get("error"):
                    raise Exception(f"Finnhub error: {data['error']}")
                
                return {
                    "symbol": symbol,
                    "price": float(data.get("c", 0)),
                    "change": float(data.get("d", 0)),
                    "change_percent": float(data.get("dp", 0)),
                    "high": float(data.get("h", 0)),
                    "low": float(data.get("l", 0)),
                    "open": float(data.get("o", 0)),
                    "timestamp": int(time.time() * 1000),
                }
            
        except Exception as e:
            raise Exception(f"Finnhub API error: {e}")
    
    def _get_mock_quote(self, symbol: str) -> Dict[str, Any]:
        """Fallback mock quote data"""
        base_prices = {
            "AAPL": 150.0, "MSFT": 300.0, "GOOGL": 2500.0, "TSLA": 200.0,
            "AMZN": 3000.0, "META": 300.0, "NVDA": 400.0, "NFLX": 400.0
        }
        
        import random
        base_price = base_prices.get(symbol, 100.0)
        variation = random.uniform(-0.05, 0.05)
        current_price = base_price * (1 + variation)
        
        return {
            "symbol": symbol,
            "price": round(current_price, 2),
            "change": round(current_price - base_price, 2),
            "change_percent": round(variation * 100, 2),
            "timestamp": int(time.time() * 1000),
            "provider": "mock"
        }
    
    def get_options_chain(self, symbol: str, limit: int = 50) -> Dict[str, Any]:
        """Get options chain with caching and provider fallback"""
        symbol = symbol.upper().strip()
        cache_key = self._cache_key("options", symbol=symbol, limit=limit)
        
        # Try cache first
        cached_data = self._get_from_cache(cache_key)
        if cached_data:
            logger.debug(f"Cache hit for options: {symbol}")
            return cached_data
        
        # Try Polygon for options (Finnhub has limited options support)
        try:
            data = self._get_polygon_options(symbol, limit)
            if data and data.get("contracts"):
                data["provider"] = "polygon"
                data["cached_at"] = int(time.time())
                
                # Cache the result
                self._set_cache(cache_key, data, self.cache_ttl["options"])
                
                logger.info(f"Options chain retrieved for {symbol} from polygon")
                return data
        except Exception as e:
            logger.warning(f"Polygon options failed for {symbol}: {e}")
        
        # Fallback to mock options
        logger.warning(f"Options providers failed for {symbol}, using mock data")
        return self._get_mock_options(symbol, limit)
    
    def _get_polygon_options(self, symbol: str, limit: int) -> Dict[str, Any]:
        """Get options from Polygon.io"""
        import httpx
        
        api_key = getattr(settings, 'POLYGON_API_KEY', None)
        if not api_key or api_key.strip() == '':
            raise Exception("Polygon API key not configured or empty")
        
        try:
            with httpx.Client(timeout=10) as client:
                # Get options contracts
                response = client.get(
                    "https://api.polygon.io/v3/reference/options/contracts",
                    params={
                        "underlying_ticker": symbol,
                        "limit": limit,
                        "apikey": api_key
                    }
                )
                response.raise_for_status()
                data = response.json()
                
                if data.get("status") == "OK":
                    contracts = data.get("results", [])
                    
                    # Process contracts
                    contract_data = []
                    for contract in contracts[:limit]:
                        contract_data.append({
                            "symbol": contract.get("ticker", ""),
                            "type": contract.get("contract_type", "").upper(),
                            "strike": float(contract.get("strike_price", 0)),
                            "expiration": contract.get("expiration_date", ""),
                            "ticker": contract.get("ticker", ""),
                        })
                    
                    return {
                        "symbol": symbol,
                        "contracts": contract_data,
                    }
                
                raise Exception(f"No options data available for {symbol}")
                
        except Exception as e:
            raise Exception(f"Polygon options API error: {e}")
    
    def _get_option_quote(self, client, contract_symbol: str, api_key: str) -> Dict[str, Any]:
        """Get quote for a specific option contract"""
        try:
            response = client.get(
                f"https://api.polygon.io/v2/last/trade/{contract_symbol}",
                params={"apikey": api_key}
            )
            response.raise_for_status()
            data = response.json()
            
            if data.get("status") == "OK" and data.get("results"):
                result = data["results"]
                return {
                    "last_price": float(result.get("p", 0)),
                    "volume": result.get("s", 0)
                }
        except:
            pass
        
        # Fallback to NBBO
        try:
            response = client.get(
                f"https://api.polygon.io/v2/last/nbbo/{contract_symbol}",
                params={"apikey": api_key}
            )
            response.raise_for_status()
            data = response.json()
            
            if data.get("status") == "OK" and data.get("results"):
                result = data["results"]
                bid = result.get("bid", {})
                ask = result.get("ask", {})
                
                return {
                    "bid": float(bid.get("price", 0)) if bid.get("price") else None,
                    "ask": float(ask.get("price", 0)) if ask.get("price") else None
                }
        except:
            pass
        
        return {}
    
    def _get_mock_options(self, symbol: str, limit: int) -> Dict[str, Any]:
        """Fallback mock options data"""
        import random
        from datetime import datetime, timedelta
        
        # Get current price for realistic strikes
        quote_data = self.get_quote(symbol)
        current_price = quote_data.get("price", 100.0)
        
        # Generate expiration dates (next 4 Fridays)
        today = datetime.now()
        expirations = []
        for i in range(1, 5):
            exp_date = today + timedelta(days=7*i)
            expirations.append(exp_date.strftime('%Y-%m-%d'))
        
        contracts = []
        for exp in expirations[:2]:  # Only first 2 expirations
            for strike in range(int(current_price - 15), int(current_price + 15), 10):
                # Call option
                contracts.append({
                    "symbol": f'{symbol}{exp.replace("-", "")}C{strike:05d}',
                    "type": "CALL",
                    "strike": float(strike),
                    "expiration": exp,
                    "bid": max(0.01, (current_price - strike) * 0.1 + random.uniform(-0.5, 0.5)),
                    "ask": max(0.01, (current_price - strike) * 0.1 + random.uniform(0.5, 1.0)),
                    "last_price": max(0.01, (current_price - strike) * 0.1 + random.uniform(-0.3, 0.3)),
                    "volume": random.randint(100, 500),
                    "open_interest": random.randint(1000, 3000),
                })
                
                # Put option
                contracts.append({
                    "symbol": f'{symbol}{exp.replace("-", "")}P{strike:05d}',
                    "type": "PUT",
                    "strike": float(strike),
                    "expiration": exp,
                    "bid": max(0.01, (strike - current_price) * 0.1 + random.uniform(-0.5, 0.5)),
                    "ask": max(0.01, (strike - current_price) * 0.1 + random.uniform(0.5, 1.0)),
                    "last_price": max(0.01, (strike - current_price) * 0.1 + random.uniform(-0.3, 0.3)),
                    "volume": random.randint(100, 500),
                    "open_interest": random.randint(1000, 3000),
                })
        
        return {
            "symbol": symbol,
            "contracts": contracts[:limit],
            "provider": "mock"
        }
    
    def get_stock_chart_data(self, symbol: str, resolution: str = "D", limit: int = 180) -> Dict[str, Any]:
        """Get stock chart data (candlesticks) with caching"""
        cache_key = self._cache_key("chart", symbol=symbol, resolution=resolution, limit=limit)
        
        # Try cache first
        cached_data = self._get_from_cache(cache_key)
        if cached_data:
            return cached_data
        
        # Get from Finnhub
        try:
            finnhub_data = self._get_finnhub_chart(symbol, resolution, limit)
            if finnhub_data:
                self._set_cache(cache_key, finnhub_data, self.cache_ttl["quote"])
                return finnhub_data
        except Exception as e:
            logger.warning(f"Finnhub chart error for {symbol}: {e}")
        
        # Fallback to mock data
        return self._get_mock_chart_data(symbol, resolution, limit)
    
    def _get_finnhub_chart(self, symbol: str, resolution: str, limit: int) -> Dict[str, Any]:
        """Get chart data from Finnhub API"""
        import requests
        
        finnhub_key = os.getenv("FINNHUB_API_KEY")
        if not finnhub_key:
            raise Exception("FINNHUB_API_KEY not configured")
        
        # Map resolution to Finnhub format
        resolution_map = {
            '1': '1',  # 1 minute
            '5': '5',  # 5 minutes
            '15': '15',  # 15 minutes
            '30': '30',  # 30 minutes
            '60': '60',  # 1 hour
            'D': 'D',  # Daily
            'W': 'W',  # Weekly
            'M': 'M'   # Monthly
        }
        
        finnhub_resolution = resolution_map.get(resolution, 'D')
        
        # Calculate time range based on resolution and limit
        import time
        current_time = int(time.time())
        
        # Estimate time range needed
        if finnhub_resolution in ['1', '5', '15', '30', '60']:
            # Intraday data
            hours_back = min(limit, 24)  # Max 24 hours for intraday
            from_time = current_time - (hours_back * 3600)
        elif finnhub_resolution == 'D':
            # Daily data
            days_back = min(limit, 365)  # Max 1 year
            from_time = current_time - (days_back * 86400)
        elif finnhub_resolution == 'W':
            # Weekly data
            weeks_back = min(limit, 52)  # Max 1 year
            from_time = current_time - (weeks_back * 604800)
        else:  # Monthly
            months_back = min(limit, 12)  # Max 1 year
            from_time = current_time - (months_back * 2592000)
        
        url = f"https://finnhub.io/api/v1/stock/candle"
        params = {
            'symbol': symbol,
            'resolution': finnhub_resolution,
            'from': from_time,
            'to': current_time,
            'token': finnhub_key
        }
        
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        if data.get('s') == 'no_data':
            raise Exception(f"No data available for {symbol}")
        
        if 'c' not in data or not data['c']:
            raise Exception(f"Invalid chart data for {symbol}")
        
        # Convert Finnhub format to our format
        chart_data = []
        for i in range(len(data['c'])):
            chart_data.append({
                'timestamp': data['t'][i],
                'open': data['o'][i],
                'high': data['h'][i],
                'low': data['l'][i],
                'close': data['c'][i],
                'volume': data['v'][i] if 'v' in data else 0
            })
        
        return {
            'symbol': symbol,
            'data': chart_data,
            'provider': 'finnhub'
        }
    
    def _get_mock_chart_data(self, symbol: str, resolution: str, limit: int) -> Dict[str, Any]:
        """Generate mock chart data"""
        import time
        import random
        
        current_time = int(time.time())
        chart_data = []
        
        # Base price varies by symbol
        base_price = 100 + (hash(symbol) % 200)
        
        for i in range(min(limit, 30)):
            # Calculate timestamp based on resolution
            if resolution in ['1', '5', '15', '30', '60']:
                timestamp = current_time - (i * 3600)  # Hourly
            elif resolution == 'D':
                timestamp = current_time - (i * 86400)  # Daily
            elif resolution == 'W':
                timestamp = current_time - (i * 604800)  # Weekly
            else:  # Monthly
                timestamp = current_time - (i * 2592000)  # Monthly
            
            # Generate realistic price movement
            price_change = random.uniform(-2, 2)
            open_price = base_price + (i * 0.1) + price_change
            close_price = open_price + random.uniform(-1, 1)
            high_price = max(open_price, close_price) + random.uniform(0, 1)
            low_price = min(open_price, close_price) - random.uniform(0, 1)
            
            chart_data.append({
                'timestamp': timestamp,
                'open': round(open_price, 2),
                'high': round(high_price, 2),
                'low': round(low_price, 2),
                'close': round(close_price, 2),
                'volume': random.randint(100000, 1000000)
            })
        
        return {
            'symbol': symbol,
            'data': chart_data,
            'provider': 'mock'
        }
    
    def clear_cache(self, pattern: str = None):
        """Clear cache entries matching pattern"""
        if not REDIS_AVAILABLE:
            return {"cleared": 0, "redis_available": False}
        
        if pattern is None:
            pattern = f"{self.cache_prefix}*"
        
        try:
            keys = redis_client.keys(pattern)
            if keys:
                redis_client.delete(*keys)
                logger.info(f"🧹 Cleared {len(keys)} cache entries matching '{pattern}'")
                return {"cleared": len(keys), "pattern": pattern}
            return {"cleared": 0, "pattern": pattern}
        except Exception as e:
            logger.error(f"❌ Failed to clear cache: {e}")
            return {"error": str(e), "pattern": pattern}
    
    def get_cache_stats(self):
        """Get cache statistics"""
        if not REDIS_AVAILABLE:
            return {"redis_available": False}
        
        try:
            info = redis_client.info('memory')
            keys = redis_client.keys(f"{self.cache_prefix}*")
            
            return {
                "redis_available": True,
                "total_keys": len(keys),
                "memory_used": info.get('used_memory_human', 'unknown'),
                "memory_peak": info.get('used_memory_peak_human', 'unknown'),
                "cache_prefix": self.cache_prefix,
                "sample_keys": [key for key in keys[:5]]  # First 5 keys as sample
            }
        except Exception as e:
            logger.error(f"❌ Failed to get cache stats: {e}")
            return {"redis_available": True, "error": str(e)}