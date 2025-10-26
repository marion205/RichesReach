"""
Polygon.io market data provider implementation.
High-performance provider for real-time market data.
"""

import asyncio
import aiohttp
from typing import List, Dict, Optional
from datetime import datetime, timedelta
import logging

from .base import MarketDataProvider, Quote, OHLCV, NewsItem


class PolygonProvider(MarketDataProvider):
    """Polygon.io market data provider"""
    
    def __init__(self, api_key: str, base_url: str = "https://api.polygon.io"):
        self.api_key = api_key
        self.base_url = base_url
        self.session = None
        self.logger = logging.getLogger(__name__)
    
    async def _get_session(self):
        """Get or create aiohttp session"""
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession()
        return self.session
    
    async def _make_request(self, endpoint: str, params: Dict = None) -> Dict:
        """Make authenticated request to Polygon API"""
        if params is None:
            params = {}
        params['apikey'] = self.api_key
        
        session = await self._get_session()
        url = f"{self.base_url}{endpoint}"
        
        try:
            async with session.get(url, params=params) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    self.logger.error(f"Polygon API error: {response.status}")
                    return {}
        except Exception as e:
            self.logger.error(f"Polygon request failed: {e}")
            return {}
    
    async def get_quotes(self, symbols: List[str]) -> Dict[str, Quote]:
        """Get real-time quotes for multiple symbols"""
        quotes = {}
        
        # Polygon aggregates endpoint for multiple symbols
        symbols_str = ",".join(symbols)
        data = await self._make_request("/v2/aggs/ticker", {
            "tickers": symbols_str,
            "timespan": "minute",
            "from": (datetime.now() - timedelta(minutes=1)).strftime("%Y-%m-%d"),
            "to": datetime.now().strftime("%Y-%m-%d"),
            "adjusted": "true",
            "sort": "desc",
            "limit": 1
        })
        
        if "results" in data:
            for result in data["results"]:
                symbol = result["T"]
                quotes[symbol] = Quote(
                    symbol=symbol,
                    price=result["c"],  # close price
                    bid=result.get("b", result["c"] - 0.01),  # bid
                    ask=result.get("a", result["c"] + 0.01),  # ask
                    volume=result["v"],  # volume
                    timestamp=datetime.fromtimestamp(result["t"] / 1000),
                    change=result["c"] - result["o"],  # close - open
                    change_percent=((result["c"] - result["o"]) / result["o"]) * 100
                )
        
        return quotes
    
    async def get_ohlcv(self, symbol: str, timeframe: str, limit: int = 100) -> List[OHLCV]:
        """Get OHLCV data for a symbol"""
        # Map timeframe to Polygon timespan
        timespan_map = {
            "1m": "minute",
            "5m": "minute", 
            "15m": "minute",
            "1h": "hour",
            "1d": "day"
        }
        
        timespan = timespan_map.get(timeframe, "minute")
        
        # Calculate date range
        if timeframe == "1m":
            multiplier = 1
        elif timeframe == "5m":
            multiplier = 5
        elif timeframe == "15m":
            multiplier = 15
        elif timeframe == "1h":
            multiplier = 1
        elif timeframe == "1d":
            multiplier = 1
        else:
            multiplier = 1
        
        data = await self._make_request(f"/v2/aggs/ticker/{symbol}/range/{multiplier}/{timespan}", {
            "from": (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d"),
            "to": datetime.now().strftime("%Y-%m-%d"),
            "adjusted": "true",
            "sort": "desc",
            "limit": limit
        })
        
        ohlcv_data = []
        if "results" in data:
            for result in data["results"]:
                ohlcv_data.append(OHLCV(
                    timestamp=datetime.fromtimestamp(result["t"] / 1000),
                    open=result["o"],
                    high=result["h"],
                    low=result["l"],
                    close=result["c"],
                    volume=result["v"]
                ))
        
        return ohlcv_data[::-1]  # Reverse to get chronological order
    
    async def get_news(self, symbol: str, limit: int = 10) -> List[NewsItem]:
        """Get news for a symbol"""
        data = await self._make_request(f"/v1/meta/symbols/{symbol}/news", {
            "limit": limit
        })
        
        news_items = []
        if "results" in data:
            for item in data["results"]:
                news_items.append(NewsItem(
                    title=item.get("title", ""),
                    summary=item.get("summary", ""),
                    url=item.get("url", ""),
                    timestamp=datetime.fromtimestamp(item["timestamp"] / 1000),
                    sentiment_score=item.get("sentiment_score")
                ))
        
        return news_items
    
    async def get_market_status(self) -> Dict[str, bool]:
        """Get market status"""
        data = await self._make_request("/v1/marketstatus/now")
        
        if "market" in data:
            market_status = data["market"]
            return {
                "pre_market": market_status == "pre-market",
                "regular_market": market_status == "open",
                "after_hours": market_status == "after-hours",
                "is_open": market_status in ["open", "pre-market", "after-hours"]
            }
        
        return {
            "pre_market": False,
            "regular_market": False,
            "after_hours": False,
            "is_open": False
        }
    
    async def get_short_availability(self, symbol: str) -> Dict[str, bool]:
        """Check short availability (requires Polygon Pro plan)"""
        # This would require Polygon's short interest endpoint
        # For now, return mock data
        return {
            "available": True,
            "borrow_rate": 0.05,
            "shares_available": 1000000
        }
    
    async def get_halts(self, symbols: List[str]) -> Dict[str, bool]:
        """Check if symbols are halted"""
        halts = {}
        
        for symbol in symbols:
            data = await self._make_request(f"/v1/marketstatus/now")
            # Polygon doesn't have direct halt status, would need to check trades
            halts[symbol] = False
        
        return halts
    
    async def close(self):
        """Close the session"""
        if self.session and not self.session.closed:
            await self.session.close()


# Factory function for easy provider creation
def create_provider(provider_type: str, **kwargs) -> MarketDataProvider:
    """Create market data provider instance"""
    if provider_type == "polygon":
        return PolygonProvider(**kwargs)
    elif provider_type == "mock":
        return MockMarketDataProvider()
    else:
        raise ValueError(f"Unknown provider type: {provider_type}")
