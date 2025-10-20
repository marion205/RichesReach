"""
Robust Market Data Service with Provider Fallback and Timeouts
"""
import os
import asyncio
import httpx
import time
import logging
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class QuoteData:
    symbol: str
    price: float
    change: float
    change_percent: float
    volume: int
    high: float
    low: float
    timestamp: int
    provider: str

class MarketDataProvider:
    """Base class for market data providers"""
    
    def __init__(self, name: str, api_key: str, timeout: float = 4.0):
        self.name = name
        self.api_key = api_key
        self.timeout = timeout
        self.is_configured = bool(api_key)
    
    async def fetch_quotes(self, symbols: List[str], client: httpx.AsyncClient) -> List[QuoteData]:
        """Fetch quotes for given symbols"""
        raise NotImplementedError

class PolygonProvider(MarketDataProvider):
    """Polygon.io provider"""
    
    async def fetch_quotes(self, symbols: List[str], client: httpx.AsyncClient) -> List[QuoteData]:
        if not self.api_key:
            raise RuntimeError("POLYGON_API_KEY not configured")
        
        # Polygon.io batch endpoint
        symbols_str = ",".join(symbols)
        url = f"https://api.polygon.io/v2/snapshot/locale/us/markets/stocks/tickers"
        params = {
            "tickers": symbols_str,
            "apikey": self.api_key
        }
        
        response = await client.get(url, params=params, timeout=self.timeout)
        response.raise_for_status()
        data = response.json()
        
        quotes = []
        if "results" in data:
            for ticker_data in data["results"]:
                symbol = ticker_data.get("ticker", "")
                day_data = ticker_data.get("day", {})
                
                if day_data:
                    quotes.append(QuoteData(
                        symbol=symbol,
                        price=day_data.get("c", 0.0),  # close
                        change=day_data.get("c", 0.0) - day_data.get("o", 0.0),  # close - open
                        change_percent=((day_data.get("c", 0.0) - day_data.get("o", 0.0)) / day_data.get("o", 1.0)) * 100,
                        volume=day_data.get("v", 0),  # volume
                        high=day_data.get("h", 0.0),  # high
                        low=day_data.get("l", 0.0),   # low
                        timestamp=int(time.time() * 1000),
                        provider="polygon"
                    ))
        
        return quotes

class FinnhubProvider(MarketDataProvider):
    """Finnhub provider"""
    
    async def fetch_quotes(self, symbols: List[str], client: httpx.AsyncClient) -> List[QuoteData]:
        if not self.api_key:
            raise RuntimeError("FINNHUB_API_KEY not configured")
        
        quotes = []
        for symbol in symbols:
            url = f"https://finnhub.io/api/v1/quote"
            params = {
                "symbol": symbol,
                "token": self.api_key
            }
            
            response = await client.get(url, params=params, timeout=self.timeout)
            response.raise_for_status()
            data = response.json()
            
            if data.get("c"):  # current price exists
                quotes.append(QuoteData(
                    symbol=symbol,
                    price=data.get("c", 0.0),
                    change=data.get("d", 0.0),  # change
                    change_percent=data.get("dp", 0.0),  # change percent
                    volume=0,  # Finnhub doesn't provide volume in quote endpoint
                    high=data.get("h", 0.0),  # high
                    low=data.get("l", 0.0),   # low
                    timestamp=int(time.time() * 1000),
                    provider="finnhub"
                ))
        
        return quotes

class AlphaVantageProvider(MarketDataProvider):
    """Alpha Vantage provider (fallback)"""
    
    async def fetch_quotes(self, symbols: List[str], client: httpx.AsyncClient) -> List[QuoteData]:
        if not self.api_key:
            raise RuntimeError("ALPHAVANTAGE_API_KEY not configured")
        
        quotes = []
        for symbol in symbols:
            url = "https://www.alphavantage.co/query"
            params = {
                "function": "GLOBAL_QUOTE",
                "symbol": symbol,
                "apikey": self.api_key
            }
            
            response = await client.get(url, params=params, timeout=self.timeout)
            response.raise_for_status()
            data = response.json()
            
            quote_data = data.get("Global Quote", {})
            if quote_data and quote_data.get("05. price"):
                price = float(quote_data.get("05. price", 0))
                change = float(quote_data.get("09. change", 0))
                change_percent = float(quote_data.get("10. change percent", "0%").replace("%", ""))
                
                quotes.append(QuoteData(
                    symbol=symbol,
                    price=price,
                    change=change,
                    change_percent=change_percent,
                    volume=int(quote_data.get("06. volume", 0)),
                    high=float(quote_data.get("03. high", 0)),
                    low=float(quote_data.get("04. low", 0)),
                    timestamp=int(time.time() * 1000),
                    provider="alpha_vantage"
                ))
        
        return quotes

class MockProvider(MarketDataProvider):
    """Mock provider for testing"""
    
    async def fetch_quotes(self, symbols: List[str], client: httpx.AsyncClient) -> List[QuoteData]:
        import random
        
        base_prices = {
            "AAPL": 150.0, "MSFT": 300.0, "GOOGL": 2500.0, "TSLA": 200.0,
            "AMZN": 3000.0, "META": 300.0, "NVDA": 400.0, "NFLX": 400.0,
            "ADBE": 580.0, "AMD": 125.0, "CRM": 220.0, "INTC": 45.0,
            "LYFT": 12.0, "PYPL": 65.0, "UBER": 45.0
        }
        
        quotes = []
        for symbol in symbols:
            base_price = base_prices.get(symbol, 100.0)
            variation = random.uniform(-0.05, 0.05)
            current_price = base_price * (1 + variation)
            
            quotes.append(QuoteData(
                symbol=symbol,
                price=round(current_price, 2),
                change=round(current_price - base_price, 2),
                change_percent=round(variation * 100, 2),
                volume=random.randint(1000000, 10000000),
                high=round(current_price * 1.02, 2),
                low=round(current_price * 0.98, 2),
                timestamp=int(time.time() * 1000),
                provider="mock"
            ))
        
        return quotes

class RobustMarketService:
    """Robust market data service with provider fallback"""
    
    def __init__(self):
        self.providers = [
            PolygonProvider("polygon", os.getenv("POLYGON_API_KEY")),
            FinnhubProvider("finnhub", os.getenv("FINNHUB_API_KEY")),
            AlphaVantageProvider("alpha_vantage", os.getenv("ALPHAVANTAGE_API_KEY")),
        ]
        
        # Add mock provider if enabled
        mock_enabled = os.getenv("USE_MARKET_MOCK", "false").lower() == "true"
        logger.info(f"🔍 Mock mode enabled: {mock_enabled}")
        if mock_enabled:
            self.providers.insert(0, MockProvider("mock", "mock_key"))  # Insert at beginning for priority
            logger.info(f"✅ Mock provider added to providers list")
        
        # TTL cache
        self._cache: Dict[str, tuple[float, List[QuoteData]]] = {}
        self.cache_ttl = 10  # 10 seconds
    
    def _cache_key(self, symbols: List[str]) -> str:
        return ",".join(sorted(symbols))
    
    def _get_cached_quotes(self, symbols: List[str]) -> Optional[List[QuoteData]]:
        """Get cached quotes if still valid"""
        key = self._cache_key(symbols)
        now = time.time()
        
        if key in self._cache:
            timestamp, quotes = self._cache[key]
            if now - timestamp < self.cache_ttl:
                return quotes
            else:
                del self._cache[key]
        
        return None
    
    def _cache_quotes(self, symbols: List[str], quotes: List[QuoteData]):
        """Cache quotes with timestamp"""
        key = self._cache_key(symbols)
        self._cache[key] = (time.time(), quotes)
    
    async def get_quotes(self, symbols: List[str]) -> List[Dict[str, Any]]:
        """Get quotes with provider fallback and caching"""
        if not symbols:
            return []
        
        # Check cache first
        cached_quotes = self._get_cached_quotes(symbols)
        if cached_quotes:
            logger.info(f"📦 Cache hit for symbols: {symbols}")
            return [self._quote_to_dict(q) for q in cached_quotes]
        
        # Try providers in order
        errors = {}
        async with httpx.AsyncClient(timeout=5.0) as client:
            for provider in self.providers:
                if not provider.is_configured:
                    continue
                
                try:
                    logger.info(f"🔄 Trying {provider.name} for symbols: {symbols}")
                    quotes = await provider.fetch_quotes(symbols, client)
                    
                    if quotes:
                        logger.info(f"✅ {provider.name} succeeded: {len(quotes)} quotes")
                        self._cache_quotes(symbols, quotes)
                        return [self._quote_to_dict(q) for q in quotes]
                    
                except Exception as e:
                    error_msg = str(e)
                    errors[provider.name] = error_msg
                    logger.warning(f"❌ {provider.name} failed: {error_msg}")
        
        # All providers failed
        logger.error(f"❌ All providers failed for symbols {symbols}: {errors}")
        return []
    
    def _quote_to_dict(self, quote: QuoteData) -> Dict[str, Any]:
        """Convert QuoteData to dictionary format"""
        return {
            "symbol": quote.symbol,
            "price": quote.price,
            "change": quote.change,
            "change_percent": quote.change_percent,
            "volume": quote.volume,
            "high": quote.high,
            "low": quote.low,
            "timestamp": quote.timestamp,
            "provider": quote.provider
        }
    
    def get_provider_status(self) -> Dict[str, Any]:
        """Get status of all providers"""
        return {
            provider.name: {
                "configured": provider.is_configured,
                "timeout": provider.timeout
            }
            for provider in self.providers
        }

# Global instance
market_service = RobustMarketService()
