"""
Enhanced API Service with intelligent caching and rate limiting
"""
import time

import hashlib

import json

from datetime import datetime

from typing import Dict, Any, Optional, List



import requests

from django.core.cache import cache

from django.conf import settings  # noqa: F401  (kept in case you use it later)

from .models import Stock



import logging



logger = logging.getLogger(__name__)





class EnhancedAPIService:

    """Enhanced API service with intelligent caching and rate limiting."""



    def __init__(self):
        # Load API keys from environment or Secrets Manager
        # NEVER hardcode API keys in production
        from .secrets_manager import get_secret
        
        self.api_keys: List[str] = []
        
        # Try to load from environment or secrets manager
        key1 = get_secret('alpha_vantage_key_1', default=os.getenv('ALPHA_VANTAGE_API_KEY'))
        key2 = get_secret('alpha_vantage_key_2', default=os.getenv('ALPHA_VANTAGE_API_KEY_2'))
        
        if key1:
            self.api_keys.append(key1)
        if key2:
            self.api_keys.append(key2)
        
        if not self.api_keys:
            logger.warning("No Alpha Vantage API keys found. Set ALPHA_VANTAGE_API_KEY or configure Secrets Manager.")

        self.current_key_index: int = 0



        # Cache TTL settings (seconds)

        self.cache_ttl: Dict[str, int] = {

            "stock_data": 3600,      # 1 hour

            "options_data": 1800,    # 30 minutes

            "market_data": 300,      # 5 minutes

            "search_results": 7200,  # 2 hours

        }



    # ------------------------------------------------------------------

    # API key rotation & rate limiting

    # ------------------------------------------------------------------

    def get_api_key(self) -> str:

        """Get current API key."""

        return self.api_keys[self.current_key_index]



    def rotate_api_key(self) -> None:

        """Rotate to next API key."""

        self.current_key_index = (self.current_key_index + 1) % len(self.api_keys)

        logger.info(f"Rotated to API key index: {self.current_key_index}")



    def is_rate_limited(self, api_key: str) -> bool:

        """Check if API key is rate limited (24h window by default)."""

        cache_key = f"rate_limit_{api_key}"

        rate_limit_data = cache.get(cache_key)

        if not rate_limit_data:

            return False



        # Still within the rate-limit window?

        if time.time() - rate_limit_data["timestamp"] < 86400:  # 24 hours

            return rate_limit_data["limited"]



        # Window expired, clear it

        cache.delete(cache_key)

        return False



    def set_rate_limited(self, api_key: str, hours: int = 24) -> None:

        """Mark API key as rate limited."""

        cache_key = f"rate_limit_{api_key}"

        cache.set(

            cache_key,

            {

                "limited": True,

                "timestamp": time.time(),

                "expires_in_hours": hours,

            },

            timeout=hours * 3600,

        )

        logger.warning(

            f"API key {api_key[:8]}... marked as rate limited for {hours} hours"

        )



    # ------------------------------------------------------------------

    # Caching helpers

    # ------------------------------------------------------------------

    def get_cache_key(self, endpoint: str, params: Dict[str, Any]) -> str:

        """Generate cache key for API request."""

        # Fix: Convert all values to strings before sorting to avoid TypeError
        # when params contain mixed types (bool/str/int)
        safe_params = {k: str(v) for k, v in params.items()}
        sorted_params = sorted(safe_params.items())

        param_string = json.dumps(sorted_params, sort_keys=True)

        hash_key = hashlib.md5(param_string.encode()).hexdigest()

        return f"api_cache_{endpoint}_{hash_key}"



    def get_cached_data(

        self,

        cache_key: str,

        data_type: str,

    ) -> Optional[Dict[str, Any]]:

        """Get cached data if available and not expired (TTL handled by cache)."""

        cached_data = cache.get(cache_key)

        if not cached_data:

            return None



        # Soft TTL check in case cache timeout and our TTL differ

        if time.time() - cached_data["timestamp"] < self.cache_ttl.get(

            data_type, 3600

        ):

            logger.info(f"Using cached data for {data_type}")

            return cached_data["data"]



        # Expired

        cache.delete(cache_key)

        return None



    def set_cached_data(

        self,

        cache_key: str,

        data: Dict[str, Any],

        data_type: str,

    ) -> None:

        """Cache API response data."""

        cache_data = {

            "data": data,

            "timestamp": time.time(),

            "data_type": data_type,

        }

        ttl = self.cache_ttl.get(data_type, 3600)

        cache.set(cache_key, cache_data, timeout=ttl)

        logger.info(f"Cached {data_type} data for {ttl} seconds")



    # ------------------------------------------------------------------

    # Core API request logic

    # ------------------------------------------------------------------

    def make_api_request(

        self,

        endpoint: str,

        params: Dict[str, Any],

        data_type: str = "stock_data",

    ) -> Optional[Dict[str, Any]]:

        """

        Make API request with intelligent caching and rate limiting.



        Returns parsed JSON dict on success, or None on failure.

        """

        cache_key = self.get_cache_key(endpoint, params)



        # 1) Check cache first

        cached_data = self.get_cached_data(cache_key, data_type)

        if cached_data is not None:

            return cached_data



        # 2) Try each API key until one works

        for _ in range(len(self.api_keys)):

            api_key = self.get_api_key()



            # Skip keys we know are rate limited

            if self.is_rate_limited(api_key):

                logger.warning(

                    f"API key {api_key[:8]}... is rate limited, trying next key"

                )

                self.rotate_api_key()

                continue



            try:

                # Make the API request

                params_with_key = {**params, "apikey": api_key}

                response = self._make_http_request(endpoint, params_with_key)



                if response is not None:

                    # Cache successful response

                    self.set_cached_data(cache_key, response, data_type)

                    return response



            except Exception as e:

                msg = str(e).lower()

                if "rate limit" in msg or "25 requests per day" in msg:

                    logger.warning(f"Rate limit hit for API key {api_key[:8]}...")

                    self.set_rate_limited(api_key)

                    self.rotate_api_key()

                    continue

                else:

                    logger.error(f"API request failed: {e}")

                    break



        logger.error("All API keys failed or are rate limited")

        return None



    def _make_http_request(

        self,

        endpoint: str,

        params: Dict[str, Any],

    ) -> Optional[Dict[str, Any]]:

        """Make HTTP request to API endpoint."""

        try:

            response = requests.get(endpoint, params=params, timeout=10)

            response.raise_for_status()

            data = response.json()



            # Alpha Vantage error pattern

            if "Error Message" in data:

                error_msg = data["Error Message"]

                if "rate limit" in error_msg.lower():

                    raise Exception(f"Rate limit: {error_msg}")

                raise Exception(f"API error: {error_msg}")



            # Another Alpha Vantage rate-limit message shape

            if "Note" in data and "calls per minute" in data["Note"].lower():

                raise Exception(f"Rate limit: {data['Note']}")



            return data

        except requests.exceptions.RequestException as e:

            logger.error(f"HTTP request failed: {e}")

            return None



    # ------------------------------------------------------------------

    # Public convenience methods

    # ------------------------------------------------------------------

    def get_stock_data(self, symbol: str) -> Optional[Dict[str, Any]]:

        """Get stock data with caching (Alpha Vantage GLOBAL_QUOTE)."""

        params = {

            "function": "GLOBAL_QUOTE",

            "symbol": symbol,

        }

        return self.make_api_request(

            "https://www.alphavantage.co/query",

            params,

            "stock_data",

        )



    def search_stocks(self, query: str) -> Optional[Dict[str, Any]]:

        """Search stocks with caching (Alpha Vantage SYMBOL_SEARCH)."""

        params = {

            "function": "SYMBOL_SEARCH",

            "keywords": query,

        }

        return self.make_api_request(

            "https://www.alphavantage.co/query",

            params,

            "search_results",

        )



    def get_market_data(self, symbols: List[str]) -> Dict[str, Any]:

        """

        Get market data for multiple symbols with batching and per-symbol caching.



        Returns:

            dict mapping symbol -> data (API or DB fallback)

        """

        results: Dict[str, Any] = {}



        for symbol in symbols:

            symbol = symbol.upper().strip()

            if not symbol:

                continue



            cache_key = f"market_data_{symbol}"

            cached = self.get_cached_data(cache_key, "market_data")

            if cached is not None:

                results[symbol] = cached

                continue



            data = self.get_stock_data(symbol)

            if data:

                results[symbol] = data

                self.set_cached_data(cache_key, data, "market_data")

            else:

                # Try DB fallback

                results[symbol] = self._get_real_stock_data_from_db(symbol)



        return results



    def _get_real_stock_data_from_db(self, symbol: str) -> Optional[Dict[str, Any]]:

        """

        Get real stock data from database when API fails.



        Returns an Alpha Vantage-like "Global Quote" payload if possible.

        """

        try:

            stock = Stock.objects.filter(symbol=symbol).first()

            if not stock or not stock.current_price:

                return None



            current_price = float(stock.current_price)



            open_price = getattr(stock, "open_price", current_price)

            high_price = getattr(stock, "high_price", current_price)

            low_price = getattr(stock, "low_price", current_price)

            previous_close = getattr(stock, "previous_close", current_price)

            volume = getattr(stock, "volume", 1_000_000)



            # Calculate change if we have previous close

            if previous_close and previous_close != current_price:

                change = current_price - previous_close

                change_percent = (

                    (change / previous_close) * 100 if previous_close > 0 else 0

                )

            else:

                change = getattr(stock, "change", 0)

                change_percent = getattr(stock, "change_percent", 0)



            return {

                "Global Quote": {

                    "01. symbol": symbol,

                    "02. open": str(open_price),

                    "03. high": str(high_price),

                    "04. low": str(low_price),

                    "05. price": str(current_price),

                    "06. volume": str(volume),

                    "07. latest trading day": datetime.now().strftime("%Y-%m-%d"),

                    "08. previous close": str(previous_close),

                    "09. change": str(change),

                    "10. change percent": f"{change_percent:.2f}%",

                }

            }

        except Exception as e:

            logger.error(f"Error getting real stock data for {symbol}: {e}")

            return None





# Global instance

enhanced_api_service = EnhancedAPIService()
