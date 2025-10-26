"""
Base market data provider interface for day trading system.
Allows seamless swapping between Polygon, Finnhub, IEX without touching the algo.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Optional
from dataclasses import dataclass
from datetime import datetime


@dataclass
class Quote:
    """Standardized quote structure"""
    symbol: str
    price: float
    bid: float
    ask: float
    volume: int
    timestamp: datetime
    change: float
    change_percent: float


@dataclass
class OHLCV:
    """Standardized OHLCV structure"""
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: int


@dataclass
class NewsItem:
    """Standardized news structure"""
    title: str
    summary: str
    url: str
    timestamp: datetime
    sentiment_score: Optional[float] = None


class MarketDataProvider(ABC):
    """Base interface for market data providers"""
    
    @abstractmethod
    def get_quotes(self, symbols: List[str]) -> Dict[str, Quote]:
        """Get real-time quotes for multiple symbols"""
        pass
    
    @abstractmethod
    def get_ohlcv(self, symbol: str, timeframe: str, limit: int = 100) -> List[OHLCV]:
        """Get OHLCV data for a symbol"""
        pass
    
    @abstractmethod
    def get_news(self, symbol: str, limit: int = 10) -> List[NewsItem]:
        """Get news for a symbol"""
        pass
    
    @abstractmethod
    def get_market_status(self) -> Dict[str, bool]:
        """Get market status (pre-market, regular, after-hours)"""
        pass
    
    @abstractmethod
    def get_short_availability(self, symbol: str) -> Dict[str, bool]:
        """Check if symbol is available for shorting"""
        pass
    
    @abstractmethod
    def get_halts(self, symbols: List[str]) -> Dict[str, bool]:
        """Check if symbols are halted"""
        pass


class MockMarketDataProvider(MarketDataProvider):
    """Mock provider for testing and development"""
    
    def get_quotes(self, symbols: List[str]) -> Dict[str, Quote]:
        """Generate mock quotes"""
        import random
        from datetime import datetime
        
        quotes = {}
        for symbol in symbols:
            base_price = 100 + hash(symbol) % 500
            change = random.uniform(-5, 5)
            quotes[symbol] = Quote(
                symbol=symbol,
                price=base_price + change,
                bid=base_price + change - 0.01,
                ask=base_price + change + 0.01,
                volume=random.randint(1000000, 10000000),
                timestamp=datetime.now(),
                change=change,
                change_percent=change / base_price * 100
            )
        return quotes
    
    def get_ohlcv(self, symbol: str, timeframe: str, limit: int = 100) -> List[OHLCV]:
        """Generate mock OHLCV data"""
        import random
        from datetime import datetime, timedelta
        
        data = []
        base_price = 100 + hash(symbol) % 500
        current_time = datetime.now()
        
        for i in range(limit):
            price_change = random.uniform(-2, 2)
            open_price = base_price + price_change
            high_price = open_price + random.uniform(0, 3)
            low_price = open_price - random.uniform(0, 3)
            close_price = open_price + random.uniform(-1, 1)
            volume = random.randint(100000, 1000000)
            
            data.append(OHLCV(
                timestamp=current_time - timedelta(minutes=i),
                open=round(open_price, 2),
                high=round(high_price, 2),
                low=round(low_price, 2),
                close=round(close_price, 2),
                volume=volume
            ))
        
        return data[::-1]  # Reverse to get chronological order
    
    def get_news(self, symbol: str, limit: int = 10) -> List[NewsItem]:
        """Generate mock news"""
        from datetime import datetime, timedelta
        
        news_items = []
        for i in range(limit):
            news_items.append(NewsItem(
                title=f"{symbol} Market Update #{i+1}",
                summary=f"Latest developments in {symbol} trading activity",
                url=f"https://example.com/news/{symbol.lower()}-{i+1}",
                timestamp=datetime.now() - timedelta(hours=i),
                sentiment_score=random.uniform(-1, 1)
            ))
        
        return news_items
    
    def get_market_status(self) -> Dict[str, bool]:
        """Mock market status"""
        return {
            "pre_market": False,
            "regular_market": True,
            "after_hours": False,
            "is_open": True
        }
    
    def get_short_availability(self, symbol: str) -> Dict[str, bool]:
        """Mock short availability"""
        return {
            "available": True,
            "borrow_rate": 0.05,
            "shares_available": 1000000
        }
    
    def get_halts(self, symbols: List[str]) -> Dict[str, bool]:
        """Mock halt status"""
        return {symbol: False for symbol in symbols}
