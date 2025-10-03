"""
Provider-agnostic market data service with caching and fallback.
"""
import time
import random
import logging
from typing import Dict, List, Optional, Any
from django.core.cache import cache
from django.conf import settings
import requests
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)

class RateLimitError(Exception):
    """Raised when API rate limit is exceeded"""
    pass

class ProviderError(Exception):
    """Raised when provider returns an error"""
    pass

@dataclass
class QuoteData:
    """Standardized quote data structure"""
    symbol: str
    price: float
    change: float
    change_percent: float
    volume: int
    market_cap: Optional[float] = None
    timestamp: Optional[str] = None
    stale: bool = False

class ProviderType(Enum):
    ALPHA_VANTAGE = "alpha_vantage"
    FINNHUB = "finnhub"
    POLYGON = "polygon"
    YAHOO = "yahoo"

class BaseProvider:
    """Base class for market data providers"""
    
    def __init__(self, api_key: str, rate_limit: int = 60):
        self.api_key = api_key
        self.rate_limit = rate_limit
        self.last_request_time = 0
        self.request_count = 0
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'RichesReach/1.0 (Financial Analysis App)'
        })
    
    def _check_rate_limit(self):
        """Check if we can make a request without hitting rate limits"""
        current_time = time.time()
        if current_time - self.last_request_time < 60:  # Within 1 minute window
            if self.request_count >= self.rate_limit:
                raise RateLimitError(f"Rate limit exceeded for {self.__class__.__name__}")
        else:
            # Reset counter for new minute
            self.request_count = 0
        
        self.last_request_time = current_time
        self.request_count += 1
    
    def _make_request(self, url: str, params: Dict = None) -> Dict:
        """Make HTTP request with rate limiting"""
        self._check_rate_limit()
        
        try:
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            raise ProviderError(f"Request failed: {e}")
    
    def get_quote(self, symbol: str) -> QuoteData:
        """Get quote data for a symbol - to be implemented by subclasses"""
        raise NotImplementedError

class AlphaVantageProvider(BaseProvider):
    """Alpha Vantage provider implementation"""
    
    def __init__(self, api_key: str):
        super().__init__(api_key, rate_limit=5)  # 5 requests per minute
        self.base_url = "https://www.alphavantage.co/query"
    
    def get_quote(self, symbol: str) -> QuoteData:
        """Get quote from Alpha Vantage"""
        params = {
            'function': 'GLOBAL_QUOTE',
            'symbol': symbol,
            'apikey': self.api_key
        }
        
        try:
            data = self._make_request(self.base_url, params)
            
            if 'Error Message' in data:
                raise ProviderError(f"Alpha Vantage error: {data['Error Message']}")
            
            if 'Note' in data:
                raise RateLimitError(f"Alpha Vantage rate limit: {data['Note']}")
            
            quote = data.get('Global Quote', {})
            if not quote:
                raise ProviderError("No quote data returned")
            
            return QuoteData(
                symbol=symbol,
                price=float(quote.get('05. price', 0)),
                change=float(quote.get('09. change', 0)),
                change_percent=float(quote.get('10. change percent', '0%').rstrip('%')),
                volume=int(quote.get('06. volume', 0)),
                market_cap=None,
                timestamp=quote.get('07. latest trading day')
            )
        except Exception as e:
            logger.warning(f"Alpha Vantage quote failed for {symbol}: {e}")
            raise

class FinnhubProvider(BaseProvider):
    """Finnhub provider implementation"""
    
    def __init__(self, api_key: str):
        super().__init__(api_key, rate_limit=60)  # 60 requests per minute
        self.base_url = "https://finnhub.io/api/v1"
    
    def get_quote(self, symbol: str) -> QuoteData:
        """Get quote from Finnhub"""
        params = {
            'symbol': symbol,
            'token': self.api_key
        }
        
        try:
            data = self._make_request(f"{self.base_url}/quote", params)
            
            if 'error' in data:
                raise ProviderError(f"Finnhub error: {data['error']}")
            
            return QuoteData(
                symbol=symbol,
                price=data.get('c', 0),  # current price
                change=data.get('d', 0),  # change
                change_percent=data.get('dp', 0),  # change percent
                volume=data.get('v', 0),  # volume
                market_cap=None,
                timestamp=None
            )
        except Exception as e:
            logger.warning(f"Finnhub quote failed for {symbol}: {e}")
            raise

class PolygonProvider(BaseProvider):
    """Polygon provider implementation"""
    
    def __init__(self, api_key: str):
        super().__init__(api_key, rate_limit=5)  # 5 requests per minute
        self.base_url = "https://api.polygon.io/v1"
    
    def get_quote(self, symbol: str) -> QuoteData:
        """Get quote from Polygon"""
        params = {
            'apikey': self.api_key
        }
        
        try:
            data = self._make_request(f"{self.base_url}/last_quote/stocks/{symbol}", params)
            
            if data.get('status') != 'OK':
                raise ProviderError(f"Polygon error: {data.get('message', 'Unknown error')}")
            
            quote = data.get('results', {})
            if not quote:
                raise ProviderError("No quote data returned")
            
            # Polygon returns bid/ask, we'll use the midpoint
            bid = quote.get('P', 0)  # bid price
            ask = quote.get('p', 0)  # ask price
            price = (bid + ask) / 2 if bid and ask else bid or ask or 0
            
            return QuoteData(
                symbol=symbol,
                price=price,
                change=0,  # Polygon doesn't provide change in this endpoint
                change_percent=0,
                volume=0,  # Polygon doesn't provide volume in this endpoint
                market_cap=None,
                timestamp=None
            )
        except Exception as e:
            logger.warning(f"Polygon quote failed for {symbol}: {e}")
            raise

class YahooProvider(BaseProvider):
    """Yahoo Finance provider implementation (free, no API key needed)"""
    
    def __init__(self):
        super().__init__("", rate_limit=100)  # 100 requests per minute
        self.base_url = "https://query1.finance.yahoo.com/v8/finance/chart"
    
    def get_quote(self, symbol: str) -> QuoteData:
        """Get quote from Yahoo Finance"""
        params = {
            'symbols': symbol,
            'includePrePost': 'false',
            'interval': '1d',
            'range': '1d'
        }
        
        try:
            data = self._make_request(f"{self.base_url}/{symbol}", params)
            
            if not data.get('chart', {}).get('result'):
                raise ProviderError("No data returned from Yahoo Finance")
            
            result = data['chart']['result'][0]
            meta = result.get('meta', {})
            
            current_price = meta.get('regularMarketPrice', 0)
            previous_close = meta.get('previousClose', 0)
            change = current_price - previous_close
            change_percent = (change / previous_close * 100) if previous_close else 0
            
            return QuoteData(
                symbol=symbol,
                price=current_price,
                change=change,
                change_percent=change_percent,
                volume=meta.get('regularMarketVolume', 0),
                market_cap=meta.get('marketCap'),
                timestamp=None
            )
        except Exception as e:
            logger.warning(f"Yahoo Finance quote failed for {symbol}: {e}")
            raise

class MarketDataService:
    """
    Provider-agnostic market data service with caching and fallback.
    """
    
    def __init__(self):
        self.providers = []
        self._initialize_providers()
        
        # Cache configuration
        self.cache_ttl = 60  # 1 minute for real-time data
        self.stale_cache_ttl = 86400  # 1 day for stale data
    
    def _initialize_providers(self):
        """Initialize available providers based on API keys"""
        # Add providers in order of preference (best first)
        
        # Yahoo Finance (always available, no API key needed)
        self.providers.append(YahooProvider())
        
        # Finnhub (good rate limits)
        if settings.FINNHUB_API_KEY:
            self.providers.append(FinnhubProvider(settings.FINNHUB_API_KEY))
        
        # Alpha Vantage (limited but reliable)
        if settings.ALPHA_VANTAGE_API_KEY and not settings.DISABLE_ALPHA_VANTAGE:
            self.providers.append(AlphaVantageProvider(settings.ALPHA_VANTAGE_API_KEY))
        
        # Polygon (premium, good for additional data)
        if settings.POLYGON_API_KEY:
            self.providers.append(PolygonProvider(settings.POLYGON_API_KEY))
        
        logger.info(f"Initialized {len(self.providers)} market data providers")
    
    def _get_cache_key(self, symbol: str, data_type: str = "quote") -> str:
        """Generate cache key for symbol and data type"""
        return f"md:{data_type}:{symbol.upper()}"
    
    def _get_stale_cache_key(self, symbol: str, data_type: str = "quote") -> str:
        """Generate stale cache key for symbol and data type"""
        return f"md:{data_type}:{symbol.upper()}:stale"
    
    def get_quote(self, symbol: str) -> QuoteData:
        """
        Get quote data with caching and provider fallback.
        
        Args:
            symbol: Stock symbol (e.g., 'AAPL')
            
        Returns:
            QuoteData object with current quote information
            
        Raises:
            ProviderError: If all providers fail
        """
        cache_key = self._get_cache_key(symbol, "quote")
        
        # Try to get from cache first
        cached_data = cache.get(cache_key)
        if cached_data:
            logger.debug(f"Cache hit for {symbol}")
            return QuoteData(**cached_data)
        
        # Try each provider in order
        last_error = None
        for provider in self.providers:
            try:
                logger.debug(f"Fetching quote for {symbol} from {provider.__class__.__name__}")
                quote_data = provider.get_quote(symbol)
                
                # Cache the successful result
                cache.set(cache_key, quote_data.__dict__, self.cache_ttl)
                
                # Also cache as stale data for longer period
                stale_key = self._get_stale_cache_key(symbol, "quote")
                cache.set(stale_key, quote_data.__dict__, self.stale_cache_ttl)
                
                logger.info(f"Successfully fetched quote for {symbol} from {provider.__class__.__name__}")
                return quote_data
                
            except RateLimitError as e:
                logger.warning(f"Rate limit hit for {provider.__class__.__name__}: {e}")
                last_error = e
                continue
            except ProviderError as e:
                logger.warning(f"Provider error for {provider.__class__.__name__}: {e}")
                last_error = e
                continue
            except Exception as e:
                logger.error(f"Unexpected error for {provider.__class__.__name__}: {e}")
                last_error = e
                continue
        
        # All providers failed, try to return stale data
        stale_key = self._get_stale_cache_key(symbol, "quote")
        stale_data = cache.get(stale_key)
        if stale_data:
            logger.warning(f"Returning stale data for {symbol}")
            stale_quote = QuoteData(**stale_data)
            stale_quote.stale = True
            return stale_quote
        
        # No data available
        error_msg = f"All providers failed for {symbol}. Last error: {last_error}"
        logger.error(error_msg)
        raise ProviderError(error_msg)
    
    def get_multiple_quotes(self, symbols: List[str]) -> Dict[str, QuoteData]:
        """
        Get quotes for multiple symbols with batching optimization.
        
        Args:
            symbols: List of stock symbols
            
        Returns:
            Dictionary mapping symbols to QuoteData objects
        """
        results = {}
        failed_symbols = []
        
        # Try to get from cache first
        for symbol in symbols:
            cache_key = self._get_cache_key(symbol, "quote")
            cached_data = cache.get(cache_key)
            if cached_data:
                results[symbol] = QuoteData(**cached_data)
            else:
                failed_symbols.append(symbol)
        
        # Fetch missing symbols
        for symbol in failed_symbols:
            try:
                results[symbol] = self.get_quote(symbol)
            except ProviderError as e:
                logger.error(f"Failed to fetch quote for {symbol}: {e}")
                # Try stale data
                stale_key = self._get_stale_cache_key(symbol, "quote")
                stale_data = cache.get(stale_key)
                if stale_data:
                    stale_quote = QuoteData(**stale_data)
                    stale_quote.stale = True
                    results[symbol] = stale_quote
        
        return results
    
    def get_benchmark_data(self, symbol: str, timeframe: str = "1M") -> Dict[str, Any]:
        """
        Get benchmark data with caching.
        
        Args:
            symbol: Benchmark symbol (e.g., 'SPY')
            timeframe: Time period (1D, 1W, 1M, 3M, 6M, 1Y)
            
        Returns:
            Dictionary with benchmark data
        """
        cache_key = self._get_cache_key(f"{symbol}_{timeframe}", "benchmark")
        
        # Try cache first
        cached_data = cache.get(cache_key)
        if cached_data:
            return cached_data
        
        # For now, return mock data - this would be implemented with real API calls
        # in a production environment
        mock_data = {
            "symbol": symbol,
            "timeframe": timeframe,
            "dataPoints": [
                {"timestamp": "2024-01-01", "value": 100.0, "change": 0.0, "changePercent": 0.0},
                {"timestamp": "2024-01-02", "value": 101.5, "change": 1.5, "changePercent": 1.5},
                # ... more data points
            ],
            "totalReturn": 5.2,
            "totalReturnPercent": 5.2,
            "volatility": 12.3,
            "sharpeRatio": 0.42,
            "maxDrawdown": -8.7
        }
        
        # Cache for 10 minutes
        cache.set(cache_key, mock_data, 600)
        
        return mock_data

# Global instance
market_data_service = MarketDataService()
