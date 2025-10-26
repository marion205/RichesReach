"""
Enhanced Market Data Provider Shim Interface
Comprehensive interface for market data providers with real-time capabilities
"""

import asyncio
import logging
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any, Union
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
import json


class MarketSession(Enum):
    """Market session enumeration"""
    PRE_MARKET = "PRE_MARKET"
    REGULAR = "REGULAR"
    AFTER_HOURS = "AFTER_HOURS"
    CLOSED = "CLOSED"


class DataType(Enum):
    """Data type enumeration"""
    QUOTE = "QUOTE"
    OHLCV = "OHLCV"
    NEWS = "NEWS"
    FUNDAMENTAL = "FUNDAMENTAL"
    OPTIONS = "OPTIONS"


@dataclass
class Quote:
    """Real-time quote data"""
    symbol: str
    price: float
    bid: float
    ask: float
    bid_size: int
    ask_size: int
    volume: int
    timestamp: datetime
    session: MarketSession = MarketSession.REGULAR
    
    # Additional fields
    high: Optional[float] = None
    low: Optional[float] = None
    open: Optional[float] = None
    previous_close: Optional[float] = None
    change: Optional[float] = None
    change_percent: Optional[float] = None
    
    # Market microstructure
    spread: Optional[float] = None
    mid_price: Optional[float] = None
    last_trade_price: Optional[float] = None
    last_trade_size: Optional[int] = None
    
    def __post_init__(self):
        """Calculate derived fields"""
        if self.bid and self.ask:
            self.spread = self.ask - self.bid
            self.mid_price = (self.bid + self.ask) / 2


@dataclass
class OHLCV:
    """OHLCV candle data"""
    symbol: str
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: int
    timeframe: str  # "1m", "5m", "15m", "1h", "1d"
    
    # Additional fields
    vwap: Optional[float] = None
    trades_count: Optional[int] = None
    bid_volume: Optional[int] = None
    ask_volume: Optional[int] = None


@dataclass
class NewsItem:
    """News item data"""
    id: str
    title: str
    summary: str
    content: Optional[str] = None
    url: Optional[str] = None
    published_at: datetime = field(default_factory=datetime.now)
    source: Optional[str] = None
    sentiment: Optional[float] = None  # -1 to 1
    symbols: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)


@dataclass
class FundamentalData:
    """Fundamental data"""
    symbol: str
    market_cap: Optional[float] = None
    pe_ratio: Optional[float] = None
    eps: Optional[float] = None
    dividend_yield: Optional[float] = None
    beta: Optional[float] = None
    sector: Optional[str] = None
    industry: Optional[str] = None
    employees: Optional[int] = None
    revenue: Optional[float] = None
    net_income: Optional[float] = None
    book_value: Optional[float] = None
    price_to_book: Optional[float] = None
    debt_to_equity: Optional[float] = None
    return_on_equity: Optional[float] = None
    return_on_assets: Optional[float] = None


@dataclass
class MarketStatus:
    """Market status information"""
    market_open: bool
    session: MarketSession
    next_open: Optional[datetime] = None
    next_close: Optional[datetime] = None
    current_time: datetime = field(default_factory=datetime.now)
    timezone: str = "US/Eastern"


class MarketDataProvider(ABC):
    """Abstract base class for market data providers"""
    
    def __init__(self, api_key: str, base_url: Optional[str] = None):
        self.api_key = api_key
        self.base_url = base_url
        self.logger = logging.getLogger(self.__class__.__name__)
        self.rate_limits = {}
        self.last_request_time = {}
        
    @abstractmethod
    async def get_quotes(self, symbols: List[str]) -> Dict[str, Quote]:
        """Get real-time quotes for symbols"""
        pass
    
    @abstractmethod
    async def get_ohlcv(
        self, 
        symbol: str, 
        timeframe: str, 
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 100
    ) -> List[OHLCV]:
        """Get OHLCV data for symbol"""
        pass
    
    @abstractmethod
    async def get_news(
        self, 
        symbol: Optional[str] = None, 
        limit: int = 10,
        start_date: Optional[datetime] = None
    ) -> List[NewsItem]:
        """Get news data"""
        pass
    
    @abstractmethod
    async def get_fundamental_data(self, symbol: str) -> Optional[FundamentalData]:
        """Get fundamental data for symbol"""
        pass
    
    @abstractmethod
    async def get_market_status(self) -> MarketStatus:
        """Get current market status"""
        pass
    
    @abstractmethod
    async def subscribe_to_quotes(self, symbols: List[str], callback) -> str:
        """Subscribe to real-time quote updates"""
        pass
    
    @abstractmethod
    async def unsubscribe_from_quotes(self, subscription_id: str) -> bool:
        """Unsubscribe from quote updates"""
        pass
    
    async def get_top_movers(self, limit: int = 10) -> Dict[str, List[Dict[str, Any]]]:
        """Get top movers (gainers, losers, volume leaders)"""
        # Default implementation - can be overridden
        return {
            "gainers": [],
            "losers": [],
            "volume_leaders": []
        }
    
    async def search_symbols(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Search for symbols by name or ticker"""
        # Default implementation - can be overridden
        return []
    
    async def get_sector_performance(self) -> Dict[str, float]:
        """Get sector performance data"""
        # Default implementation - can be overridden
        return {}
    
    async def get_economic_calendar(self, start_date: datetime, end_date: datetime) -> List[Dict[str, Any]]:
        """Get economic calendar events"""
        # Default implementation - can be overridden
        return []
    
    def _check_rate_limit(self, endpoint: str, requests_per_minute: int = 60) -> bool:
        """Check if rate limit is exceeded"""
        now = datetime.now()
        if endpoint not in self.last_request_time:
            self.last_request_time[endpoint] = []
        
        # Remove requests older than 1 minute
        cutoff_time = now - timedelta(minutes=1)
        self.last_request_time[endpoint] = [
            req_time for req_time in self.last_request_time[endpoint] 
            if req_time > cutoff_time
        ]
        
        # Check if we're under the limit
        if len(self.last_request_time[endpoint]) >= requests_per_minute:
            return False
        
        # Add current request
        self.last_request_time[endpoint].append(now)
        return True
    
    async def _make_request(
        self, 
        endpoint: str, 
        params: Dict[str, Any] = None,
        headers: Dict[str, str] = None
    ) -> Dict[str, Any]:
        """Make HTTP request with rate limiting and error handling"""
        import aiohttp
        
        if not self._check_rate_limit(endpoint):
            raise Exception(f"Rate limit exceeded for {endpoint}")
        
        url = f"{self.base_url}{endpoint}" if self.base_url else endpoint
        
        default_headers = {
            "User-Agent": "RichesReach/1.0",
            "Accept": "application/json"
        }
        
        if headers:
            default_headers.update(headers)
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params, headers=default_headers) as response:
                    if response.status == 200:
                        return await response.json()
                    else:
                        error_text = await response.text()
                        raise Exception(f"HTTP {response.status}: {error_text}")
        
        except aiohttp.ClientError as e:
            self.logger.error(f"Request failed for {endpoint}: {e}")
            raise
        except Exception as e:
            self.logger.error(f"Unexpected error for {endpoint}: {e}")
            raise
    
    def _parse_timestamp(self, timestamp_str: str) -> datetime:
        """Parse timestamp string to datetime"""
        try:
            # Try ISO format first
            return datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
        except ValueError:
            try:
                # Try Unix timestamp
                return datetime.fromtimestamp(float(timestamp_str))
            except ValueError:
                # Try common formats
                for fmt in ['%Y-%m-%d %H:%M:%S', '%Y-%m-%dT%H:%M:%S', '%Y-%m-%d']:
                    try:
                        return datetime.strptime(timestamp_str, fmt)
                    except ValueError:
                        continue
                raise ValueError(f"Unable to parse timestamp: {timestamp_str}")
    
    def _calculate_change_percent(self, current: float, previous: float) -> float:
        """Calculate percentage change"""
        if previous == 0:
            return 0.0
        return ((current - previous) / previous) * 100
    
    def _is_market_hours(self, timestamp: datetime) -> MarketSession:
        """Determine market session based on timestamp"""
        # Simple implementation - can be enhanced
        hour = timestamp.hour
        weekday = timestamp.weekday()
        
        # Weekend
        if weekday >= 5:  # Saturday = 5, Sunday = 6
            return MarketSession.CLOSED
        
        # Pre-market (4:00 AM - 9:30 AM ET)
        if 4 <= hour < 9 or (hour == 9 and timestamp.minute < 30):
            return MarketSession.PRE_MARKET
        
        # Regular hours (9:30 AM - 4:00 PM ET)
        if (hour == 9 and timestamp.minute >= 30) or (10 <= hour < 16):
            return MarketSession.REGULAR
        
        # After hours (4:00 PM - 8:00 PM ET)
        if hour == 16 or (17 <= hour < 20):
            return MarketSession.AFTER_HOURS
        
        # Closed
        return MarketSession.CLOSED


class MockMarketDataProvider(MarketDataProvider):
    """Mock market data provider for testing"""
    
    def __init__(self, api_key: str = "mock_key"):
        super().__init__(api_key)
        self.mock_data = self._generate_mock_data()
    
    def _generate_mock_data(self) -> Dict[str, Any]:
        """Generate mock market data"""
        import random
        
        symbols = ["AAPL", "MSFT", "GOOGL", "TSLA", "NVDA", "META", "AMZN", "NFLX"]
        mock_data = {}
        
        for symbol in symbols:
            base_price = random.uniform(50, 500)
            mock_data[symbol] = {
                "price": base_price,
                "bid": base_price - random.uniform(0.01, 0.05),
                "ask": base_price + random.uniform(0.01, 0.05),
                "volume": random.randint(1000000, 10000000),
                "high": base_price + random.uniform(0, 5),
                "low": base_price - random.uniform(0, 5),
                "open": base_price + random.uniform(-2, 2),
                "previous_close": base_price + random.uniform(-3, 3)
            }
        
        return mock_data
    
    async def get_quotes(self, symbols: List[str]) -> Dict[str, Quote]:
        """Get mock quotes"""
        quotes = {}
        
        for symbol in symbols:
            if symbol in self.mock_data:
                data = self.mock_data[symbol]
                quote = Quote(
                    symbol=symbol,
                    price=data["price"],
                    bid=data["bid"],
                    ask=data["ask"],
                    bid_size=random.randint(100, 1000),
                    ask_size=random.randint(100, 1000),
                    volume=data["volume"],
                    timestamp=datetime.now(),
                    high=data["high"],
                    low=data["low"],
                    open=data["open"],
                    previous_close=data["previous_close"],
                    change=data["price"] - data["previous_close"],
                    change_percent=self._calculate_change_percent(
                        data["price"], data["previous_close"]
                    )
                )
                quotes[symbol] = quote
        
        return quotes
    
    async def get_ohlcv(
        self, 
        symbol: str, 
        timeframe: str, 
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 100
    ) -> List[OHLCV]:
        """Get mock OHLCV data"""
        import random
        
        if symbol not in self.mock_data:
            return []
        
        base_price = self.mock_data[symbol]["price"]
        candles = []
        
        for i in range(limit):
            timestamp = datetime.now() - timedelta(minutes=i)
            open_price = base_price + random.uniform(-2, 2)
            high_price = open_price + random.uniform(0, 3)
            low_price = open_price - random.uniform(0, 3)
            close_price = open_price + random.uniform(-1, 1)
            volume = random.randint(100000, 1000000)
            
            candle = OHLCV(
                symbol=symbol,
                timestamp=timestamp,
                open=open_price,
                high=high_price,
                low=low_price,
                close=close_price,
                volume=volume,
                timeframe=timeframe
            )
            candles.append(candle)
        
        return candles
    
    async def get_news(
        self, 
        symbol: Optional[str] = None, 
        limit: int = 10,
        start_date: Optional[datetime] = None
    ) -> List[NewsItem]:
        """Get mock news data"""
        news_items = []
        
        for i in range(limit):
            news_item = NewsItem(
                id=f"news_{i}",
                title=f"Mock news item {i}",
                summary=f"This is a mock news summary for item {i}",
                content=f"Mock news content for item {i}",
                url=f"https://example.com/news/{i}",
                published_at=datetime.now() - timedelta(hours=i),
                source="Mock News",
                sentiment=random.uniform(-1, 1),
                symbols=[symbol] if symbol else ["AAPL", "MSFT"],
                tags=["mock", "testing"]
            )
            news_items.append(news_item)
        
        return news_items
    
    async def get_fundamental_data(self, symbol: str) -> Optional[FundamentalData]:
        """Get mock fundamental data"""
        if symbol not in self.mock_data:
            return None
        
        import random
        
        return FundamentalData(
            symbol=symbol,
            market_cap=random.uniform(1000000000, 3000000000000),
            pe_ratio=random.uniform(10, 50),
            eps=random.uniform(1, 20),
            dividend_yield=random.uniform(0, 5),
            beta=random.uniform(0.5, 2.0),
            sector="Technology",
            industry="Software",
            employees=random.randint(1000, 200000),
            revenue=random.uniform(1000000000, 500000000000),
            net_income=random.uniform(100000000, 100000000000),
            book_value=random.uniform(10, 100),
            price_to_book=random.uniform(1, 10),
            debt_to_equity=random.uniform(0, 2),
            return_on_equity=random.uniform(5, 25),
            return_on_assets=random.uniform(3, 15)
        )
    
    async def get_market_status(self) -> MarketStatus:
        """Get mock market status"""
        now = datetime.now()
        session = self._is_market_hours(now)
        
        return MarketStatus(
            market_open=session in [MarketSession.PRE_MARKET, MarketSession.REGULAR, MarketSession.AFTER_HOURS],
            session=session,
            next_open=now + timedelta(hours=1) if session == MarketSession.CLOSED else None,
            next_close=now + timedelta(hours=1) if session != MarketSession.CLOSED else None,
            current_time=now
        )
    
    async def subscribe_to_quotes(self, symbols: List[str], callback) -> str:
        """Mock subscription to quotes"""
        subscription_id = f"mock_sub_{len(symbols)}"
        self.logger.info(f"Mock subscription created: {subscription_id} for {symbols}")
        return subscription_id
    
    async def unsubscribe_from_quotes(self, subscription_id: str) -> bool:
        """Mock unsubscribe from quotes"""
        self.logger.info(f"Mock subscription cancelled: {subscription_id}")
        return True


# Factory function
def create_market_data_provider(provider_type: str, api_key: str, **kwargs) -> MarketDataProvider:
    """Create market data provider instance"""
    
    if provider_type.lower() == "mock":
        return MockMarketDataProvider(api_key)
    elif provider_type.lower() == "polygon":
        from .polygon_provider import PolygonProvider
        return PolygonProvider(api_key, **kwargs)
    elif provider_type.lower() == "alpha_vantage":
        from .alpha_vantage_provider import AlphaVantageProvider
        return AlphaVantageProvider(api_key, **kwargs)
    elif provider_type.lower() == "yahoo":
        from .yahoo_provider import YahooProvider
        return YahooProvider(api_key, **kwargs)
    else:
        raise ValueError(f"Unknown provider type: {provider_type}")


# Utility functions
async def get_multiple_quotes(
    providers: List[MarketDataProvider], 
    symbols: List[str]
) -> Dict[str, Quote]:
    """Get quotes from multiple providers and merge results"""
    
    all_quotes = {}
    
    for provider in providers:
        try:
            quotes = await provider.get_quotes(symbols)
            all_quotes.update(quotes)
        except Exception as e:
            logging.getLogger(__name__).warning(f"Provider {provider.__class__.__name__} failed: {e}")
    
    return all_quotes


async def get_best_quote(
    providers: List[MarketDataProvider], 
    symbol: str
) -> Optional[Quote]:
    """Get the best quote from multiple providers"""
    
    quotes = []
    
    for provider in providers:
        try:
            provider_quotes = await provider.get_quotes([symbol])
            if symbol in provider_quotes:
                quotes.append(provider_quotes[symbol])
        except Exception as e:
            logging.getLogger(__name__).warning(f"Provider {provider.__class__.__name__} failed: {e}")
    
    if not quotes:
        return None
    
    # Return quote with best spread (smallest spread)
    best_quote = min(quotes, key=lambda q: q.spread if q.spread else float('inf'))
    return best_quote
