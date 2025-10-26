"""
Polygon.io Market Data Provider
Real-time market data integration with Polygon.io API
"""

import asyncio
import logging
import aiohttp
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import json
import os

from .enhanced_base import (
    MarketDataProvider, Quote, OHLCV, NewsItem, FundamentalData, 
    MarketStatus, MarketSession, DataType
)


class PolygonProvider(MarketDataProvider):
    """Polygon.io market data provider implementation"""
    
    def __init__(self, api_key: str, base_url: str = "https://api.polygon.io"):
        super().__init__(api_key, base_url)
        self.logger = logging.getLogger(__name__)
        self.websocket_url = "wss://socket.polygon.io/stocks"
        self.active_subscriptions = {}
        self.quote_callbacks = {}
        
        # Rate limits for Polygon.io
        self.rate_limits = {
            "quotes": 5,  # 5 requests per minute for free tier
            "ohlcv": 5,
            "news": 5,
            "fundamentals": 5
        }
    
    async def get_quotes(self, symbols: List[str]) -> Dict[str, Quote]:
        """Get real-time quotes from Polygon.io"""
        quotes = {}
        
        # Polygon.io requires individual requests for each symbol in free tier
        for symbol in symbols:
            try:
                if not self._check_rate_limit("quotes", self.rate_limits["quotes"]):
                    self.logger.warning(f"Rate limit exceeded for quotes, using cached data for {symbol}")
                    continue
                
                endpoint = f"/v2/last/trade/{symbol}"
                params = {
                    "apikey": self.api_key
                }
                
                response = await self._make_request(endpoint, params)
                
                if "results" in response and response["results"]:
                    trade_data = response["results"]
                    
                    # Get additional quote data
                    quote_data = await self._get_quote_data(symbol)
                    
                    quote = Quote(
                        symbol=symbol,
                        price=trade_data.get("p", 0.0),
                        bid=quote_data.get("bid", 0.0),
                        ask=quote_data.get("ask", 0.0),
                        bid_size=quote_data.get("bid_size", 0),
                        ask_size=quote_data.get("ask_size", 0),
                        volume=trade_data.get("s", 0),
                        timestamp=self._parse_timestamp(trade_data.get("t", "")),
                        last_trade_price=trade_data.get("p", 0.0),
                        last_trade_size=trade_data.get("s", 0)
                    )
                    
                    quotes[symbol] = quote
                    
            except Exception as e:
                self.logger.error(f"Failed to get quote for {symbol}: {e}")
                continue
        
        return quotes
    
    async def _get_quote_data(self, symbol: str) -> Dict[str, Any]:
        """Get detailed quote data including bid/ask"""
        try:
            endpoint = f"/v1/last_quote/{symbol}"
            params = {
                "apikey": self.api_key
            }
            
            response = await self._make_request(endpoint, params)
            
            if "results" in response and response["results"]:
                quote_data = response["results"]
                return {
                    "bid": quote_data.get("P", 0.0),
                    "ask": quote_data.get("p", 0.0),
                    "bid_size": quote_data.get("S", 0),
                    "ask_size": quote_data.get("s", 0)
                }
            
        except Exception as e:
            self.logger.warning(f"Failed to get detailed quote data for {symbol}: {e}")
        
        return {"bid": 0.0, "ask": 0.0, "bid_size": 0, "ask_size": 0}
    
    async def get_ohlcv(
        self, 
        symbol: str, 
        timeframe: str, 
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 100
    ) -> List[OHLCV]:
        """Get OHLCV data from Polygon.io"""
        
        if not self._check_rate_limit("ohlcv", self.rate_limits["ohlcv"]):
            self.logger.warning("Rate limit exceeded for OHLCV data")
            return []
        
        try:
            # Convert timeframe to Polygon.io format
            polygon_timeframe = self._convert_timeframe(timeframe)
            
            # Set default date range if not provided
            if not end_date:
                end_date = datetime.now()
            if not start_date:
                start_date = end_date - timedelta(days=30)
            
            endpoint = f"/v2/aggs/ticker/{symbol}/range/1/{polygon_timeframe}/{start_date.strftime('%Y-%m-%d')}/{end_date.strftime('%Y-%m-%d')}"
            params = {
                "apikey": self.api_key,
                "adjusted": "true",
                "sort": "desc",
                "limit": min(limit, 50000)  # Polygon.io max limit
            }
            
            response = await self._make_request(endpoint, params)
            
            candles = []
            if "results" in response and response["results"]:
                for candle_data in response["results"][:limit]:
                    candle = OHLCV(
                        symbol=symbol,
                        timestamp=self._parse_timestamp(str(candle_data["t"])),
                        open=candle_data["o"],
                        high=candle_data["h"],
                        low=candle_data["l"],
                        close=candle_data["c"],
                        volume=candle_data["v"],
                        timeframe=timeframe,
                        vwap=candle_data.get("vw", None),
                        trades_count=candle_data.get("n", None)
                    )
                    candles.append(candle)
            
            return candles
            
        except Exception as e:
            self.logger.error(f"Failed to get OHLCV data for {symbol}: {e}")
            return []
    
    def _convert_timeframe(self, timeframe: str) -> str:
        """Convert timeframe to Polygon.io format"""
        timeframe_map = {
            "1m": "minute",
            "5m": "minute", 
            "15m": "minute",
            "30m": "minute",
            "1h": "hour",
            "1d": "day",
            "1w": "week",
            "1M": "month"
        }
        
        return timeframe_map.get(timeframe, "minute")
    
    async def get_news(
        self, 
        symbol: Optional[str] = None, 
        limit: int = 10,
        start_date: Optional[datetime] = None
    ) -> List[NewsItem]:
        """Get news data from Polygon.io"""
        
        if not self._check_rate_limit("news", self.rate_limits["news"]):
            self.logger.warning("Rate limit exceeded for news data")
            return []
        
        try:
            endpoint = "/v2/reference/news"
            params = {
                "apikey": self.api_key,
                "limit": min(limit, 1000)
            }
            
            if symbol:
                params["ticker"] = symbol
            
            if start_date:
                params["published_utc.gte"] = start_date.strftime("%Y-%m-%d")
            
            response = await self._make_request(endpoint, params)
            
            news_items = []
            if "results" in response and response["results"]:
                for news_data in response["results"][:limit]:
                    news_item = NewsItem(
                        id=news_data.get("id", ""),
                        title=news_data.get("title", ""),
                        summary=news_data.get("summary", ""),
                        content=news_data.get("content", ""),
                        url=news_data.get("article_url", ""),
                        published_at=self._parse_timestamp(news_data.get("published_utc", "")),
                        source=news_data.get("publisher", {}).get("name", ""),
                        symbols=[ticker["ticker"] for ticker in news_data.get("tickers", [])],
                        tags=news_data.get("keywords", [])
                    )
                    news_items.append(news_item)
            
            return news_items
            
        except Exception as e:
            self.logger.error(f"Failed to get news data: {e}")
            return []
    
    async def get_fundamental_data(self, symbol: str) -> Optional[FundamentalData]:
        """Get fundamental data from Polygon.io"""
        
        if not self._check_rate_limit("fundamentals", self.rate_limits["fundamentals"]):
            self.logger.warning("Rate limit exceeded for fundamental data")
            return None
        
        try:
            endpoint = f"/v1/meta/symbols/{symbol}/company"
            params = {
                "apikey": self.api_key
            }
            
            response = await self._make_request(endpoint, params)
            
            if "results" in response and response["results"]:
                data = response["results"]
                
                fundamental = FundamentalData(
                    symbol=symbol,
                    market_cap=data.get("market_cap"),
                    sector=data.get("sector"),
                    industry=data.get("industry"),
                    employees=data.get("employees"),
                    description=data.get("description")
                )
                
                return fundamental
            
        except Exception as e:
            self.logger.error(f"Failed to get fundamental data for {symbol}: {e}")
        
        return None
    
    async def get_market_status(self) -> MarketStatus:
        """Get market status from Polygon.io"""
        try:
            endpoint = "/v1/marketstatus/now"
            params = {
                "apikey": self.api_key
            }
            
            response = await self._make_request(endpoint, params)
            
            if "market" in response:
                market_data = response["market"]
                is_open = market_data.get("isOpen", False)
                
                # Determine session based on current time
                now = datetime.now()
                session = self._is_market_hours(now)
                
                return MarketStatus(
                    market_open=is_open,
                    session=session,
                    current_time=now,
                    timezone="US/Eastern"
                )
            
        except Exception as e:
            self.logger.error(f"Failed to get market status: {e}")
        
        # Fallback to local time calculation
        now = datetime.now()
        session = self._is_market_hours(now)
        
        return MarketStatus(
            market_open=session in [MarketSession.PRE_MARKET, MarketSession.REGULAR, MarketSession.AFTER_HOURS],
            session=session,
            current_time=now,
            timezone="US/Eastern"
        )
    
    async def subscribe_to_quotes(self, symbols: List[str], callback) -> str:
        """Subscribe to real-time quote updates via WebSocket"""
        import websockets
        
        subscription_id = f"polygon_sub_{len(symbols)}_{datetime.now().strftime('%H%M%S')}"
        
        async def websocket_handler():
            try:
                async with websockets.connect(self.websocket_url) as websocket:
                    # Authenticate
                    auth_message = {
                        "action": "auth",
                        "params": self.api_key
                    }
                    await websocket.send(json.dumps(auth_message))
                    
                    # Subscribe to quotes
                    subscribe_message = {
                        "action": "subscribe",
                        "params": [f"T.{symbol}" for symbol in symbols]
                    }
                    await websocket.send(json.dumps(subscribe_message))
                    
                    self.logger.info(f"Subscribed to quotes for {symbols}")
                    
                    # Listen for messages
                    async for message in websocket:
                        try:
                            data = json.loads(message)
                            
                            if data[0]["ev"] == "T":  # Trade event
                                trade_data = data[0]
                                quote = Quote(
                                    symbol=trade_data["sym"],
                                    price=trade_data["p"],
                                    bid=0.0,  # Will be updated with quote data
                                    ask=0.0,
                                    bid_size=0,
                                    ask_size=0,
                                    volume=trade_data["s"],
                                    timestamp=self._parse_timestamp(str(trade_data["t"])),
                                    last_trade_price=trade_data["p"],
                                    last_trade_size=trade_data["s"]
                                )
                                
                                # Call the callback
                                await callback(quote)
                                
                        except Exception as e:
                            self.logger.error(f"Error processing WebSocket message: {e}")
                            
            except Exception as e:
                self.logger.error(f"WebSocket connection failed: {e}")
        
        # Store subscription info
        self.active_subscriptions[subscription_id] = {
            "symbols": symbols,
            "callback": callback,
            "task": asyncio.create_task(websocket_handler())
        }
        
        return subscription_id
    
    async def unsubscribe_from_quotes(self, subscription_id: str) -> bool:
        """Unsubscribe from quote updates"""
        if subscription_id in self.active_subscriptions:
            subscription = self.active_subscriptions[subscription_id]
            subscription["task"].cancel()
            del self.active_subscriptions[subscription_id]
            self.logger.info(f"Unsubscribed from quotes: {subscription_id}")
            return True
        
        return False
    
    async def get_top_movers(self, limit: int = 10) -> Dict[str, List[Dict[str, Any]]]:
        """Get top movers from Polygon.io"""
        try:
            endpoint = "/v2/snapshot/locale/us/markets/stocks/gainers"
            params = {
                "apikey": self.api_key
            }
            
            response = await self._make_request(endpoint, params)
            
            gainers = []
            if "results" in response and response["results"]:
                for stock in response["results"][:limit]:
                    gainers.append({
                        "symbol": stock["ticker"],
                        "price": stock["day"]["c"],
                        "change": stock["day"]["c"] - stock["day"]["o"],
                        "change_percent": ((stock["day"]["c"] - stock["day"]["o"]) / stock["day"]["o"]) * 100,
                        "volume": stock["day"]["v"]
                    })
            
            # Get losers
            endpoint = "/v2/snapshot/locale/us/markets/stocks/losers"
            response = await self._make_request(endpoint, params)
            
            losers = []
            if "results" in response and response["results"]:
                for stock in response["results"][:limit]:
                    losers.append({
                        "symbol": stock["ticker"],
                        "price": stock["day"]["c"],
                        "change": stock["day"]["c"] - stock["day"]["o"],
                        "change_percent": ((stock["day"]["c"] - stock["day"]["o"]) / stock["day"]["o"]) * 100,
                        "volume": stock["day"]["v"]
                    })
            
            return {
                "gainers": gainers,
                "losers": losers,
                "volume_leaders": []  # Would need separate endpoint
            }
            
        except Exception as e:
            self.logger.error(f"Failed to get top movers: {e}")
            return {"gainers": [], "losers": [], "volume_leaders": []}
    
    async def search_symbols(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Search for symbols on Polygon.io"""
        try:
            endpoint = "/v3/reference/tickers"
            params = {
                "apikey": self.api_key,
                "search": query,
                "limit": limit,
                "active": "true"
            }
            
            response = await self._make_request(endpoint, params)
            
            symbols = []
            if "results" in response and response["results"]:
                for ticker in response["results"]:
                    symbols.append({
                        "symbol": ticker["ticker"],
                        "name": ticker["name"],
                        "market": ticker["market"],
                        "type": ticker["type"],
                        "active": ticker["active"]
                    })
            
            return symbols
            
        except Exception as e:
            self.logger.error(f"Failed to search symbols: {e}")
            return []
    
    async def get_sector_performance(self) -> Dict[str, float]:
        """Get sector performance from Polygon.io"""
        try:
            endpoint = "/v2/snapshot/locale/us/markets/stocks/sectors"
            params = {
                "apikey": self.api_key
            }
            
            response = await self._make_request(endpoint, params)
            
            sector_performance = {}
            if "results" in response and response["results"]:
                for sector in response["results"]:
                    sector_name = sector["name"]
                    change_percent = sector.get("change_percent", 0.0)
                    sector_performance[sector_name] = change_percent
            
            return sector_performance
            
        except Exception as e:
            self.logger.error(f"Failed to get sector performance: {e}")
            return {}
    
    async def cleanup(self):
        """Cleanup resources"""
        # Cancel all active subscriptions
        for subscription_id, subscription in self.active_subscriptions.items():
            subscription["task"].cancel()
        
        self.active_subscriptions.clear()
        self.logger.info("Polygon provider cleanup completed")


# Factory function for easy instantiation
def create_polygon_provider(api_key: Optional[str] = None) -> PolygonProvider:
    """Create Polygon provider instance"""
    if not api_key:
        api_key = os.getenv("POLYGON_API_KEY")
        if not api_key:
            raise ValueError("Polygon API key not provided and not found in environment variables")
    
    return PolygonProvider(api_key)
