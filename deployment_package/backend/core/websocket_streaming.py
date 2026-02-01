"""
WebSocket Streaming Service
Real-time price data streaming via WebSocket for sub-500ms latency.
Supports Alpaca and Polygon WebSocket APIs.
"""
import logging
import asyncio
import json
import time
from typing import Dict, List, Optional, Callable, Any
from datetime import datetime
import aiohttp
from collections import deque

logger = logging.getLogger(__name__)


class WebSocketStreamingService:
    """
    WebSocket streaming service for real-time price data.
    Maintains persistent connections and caches latest prices.
    """
    
    def __init__(self):
        self.connections = {}  # symbol -> websocket connection
        self.price_cache = {}  # symbol -> latest price data
        self.subscribers = {}  # symbol -> list of callbacks
        self.reconnect_delay = 5.0  # seconds
        self.max_reconnect_attempts = 10
        self.is_running = False
        
    async def connect_alpaca(
        self,
        symbols: List[str],
        api_key: str,
        api_secret: str,
        base_url: str = "wss://stream.data.alpaca.markets/v2/iex"
    ) -> bool:
        """
        Connect to Alpaca WebSocket stream.
        
        Args:
            symbols: List of symbols to subscribe to
            api_key: Alpaca API key
            api_secret: Alpaca API secret
            base_url: WebSocket URL
        
        Returns:
            True if connection successful
        """
        try:
            auth_message = {
                "action": "authenticate",
                "data": {
                    "key_id": api_key,
                    "secret_key": api_secret
                }
            }
            
            subscribe_message = {
                "action": "subscribe",
                "trades": symbols,
                "bars": symbols,
                "quotes": symbols
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.ws_connect(base_url) as ws:
                    # Authenticate
                    await ws.send_json(auth_message)
                    auth_response = await ws.receive_json()
                    
                    # Handle both dict and list responses
                    if isinstance(auth_response, list):
                        # Alpaca sometimes returns list of messages
                        auth_response = auth_response[0] if auth_response else {}
                    
                    if isinstance(auth_response, dict) and auth_response.get("T") == "success":
                        logger.info("✅ Alpaca WebSocket authenticated")
                    else:
                        logger.error(f"❌ Alpaca authentication failed: {auth_response}")
                        return False
                    
                    # Subscribe to symbols
                    await ws.send_json(subscribe_message)
                    logger.info(f"✅ Subscribed to {len(symbols)} symbols on Alpaca")
                    
                    # Store connection
                    for symbol in symbols:
                        self.connections[symbol] = ws
                    
                    # Start message loop
                    await self._handle_alpaca_messages(ws, symbols)
                    
        except Exception as e:
            logger.error(f"Error connecting to Alpaca WebSocket: {e}")
            return False
        
        return True
    
    async def _handle_alpaca_messages(self, ws, symbols: List[str]):
        """Handle incoming messages from Alpaca WebSocket"""
        try:
            async for msg in ws:
                if msg.type == aiohttp.WSMsgType.TEXT:
                    data = json.loads(msg.data)
                    
                    # Handle different message types
                    if data.get("T") == "t":  # Trade
                        symbol = data.get("S")
                        price = data.get("p")
                        volume = data.get("s")
                        timestamp = data.get("t")
                        
                        self._update_price_cache(symbol, {
                            'price': price,
                            'volume': volume,
                            'timestamp': timestamp,
                            'source': 'alpaca_trade'
                        })
                        
                    elif data.get("T") == "b":  # Bar
                        symbol = data.get("S")
                        bar = data.get("o")  # Open
                        high = data.get("h")
                        low = data.get("l")
                        close = data.get("c")
                        volume = data.get("v")
                        timestamp = data.get("t")
                        
                        self._update_price_cache(symbol, {
                            'open': bar,
                            'high': high,
                            'low': low,
                            'close': close,
                            'volume': volume,
                            'timestamp': timestamp,
                            'source': 'alpaca_bar'
                        })
                        
                elif msg.type == aiohttp.WSMsgType.ERROR:
                    logger.error(f"WebSocket error: {msg}")
                    break
                    
        except Exception as e:
            logger.error(f"Error handling Alpaca messages: {e}")
            raise
    
    async def connect_polygon(
        self,
        symbols: List[str],
        api_key: str,
        base_url: str = "wss://socket.polygon.io/stocks"
    ) -> bool:
        """
        Connect to Polygon WebSocket stream.
        
        Args:
            symbols: List of symbols to subscribe to
            api_key: Polygon API key
            base_url: WebSocket URL
        
        Returns:
            True if connection successful
        """
        try:
            # Format symbols for Polygon (prefix with T. for trades, Q. for quotes, A. for aggregates)
            trade_symbols = [f"T.{symbol}" for symbol in symbols]
            quote_symbols = [f"Q.{symbol}" for symbol in symbols]
            agg_symbols = [f"A.{symbol}" for symbol in symbols]
            
            subscribe_message = {
                "action": "subscribe",
                "params": ",".join(trade_symbols + quote_symbols + agg_symbols)
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.ws_connect(f"{base_url}?apiKey={api_key}") as ws:
                    # Subscribe
                    await ws.send_json(subscribe_message)
                    logger.info(f"✅ Subscribed to {len(symbols)} symbols on Polygon")
                    
                    # Store connection
                    for symbol in symbols:
                        self.connections[symbol] = ws
                    
                    # Start message loop
                    await self._handle_polygon_messages(ws, symbols)
                    
        except Exception as e:
            logger.error(f"Error connecting to Polygon WebSocket: {e}")
            return False
        
        return True
    
    async def _handle_polygon_messages(self, ws, symbols: List[str]):
        """Handle incoming messages from Polygon WebSocket"""
        try:
            async for msg in ws:
                if msg.type == aiohttp.WSMsgType.TEXT:
                    messages = json.loads(msg.data)
                    
                    # Polygon sends array of messages
                    for message in messages:
                        event_type = message.get("ev")
                        symbol = message.get("sym")
                        
                        if event_type == "T":  # Trade
                            price = message.get("p")
                            volume = message.get("s")
                            timestamp = message.get("t")
                            
                            self._update_price_cache(symbol, {
                                'price': price,
                                'volume': volume,
                                'timestamp': timestamp,
                                'source': 'polygon_trade'
                            })
                            
                        elif event_type == "Q":  # Quote
                            bid = message.get("bp")
                            ask = message.get("ap")
                            timestamp = message.get("t")
                            
                            # Use mid price
                            price = (bid + ask) / 2 if bid and ask else None
                            
                            if price:
                                self._update_price_cache(symbol, {
                                    'price': price,
                                    'bid': bid,
                                    'ask': ask,
                                    'timestamp': timestamp,
                                    'source': 'polygon_quote'
                                })
                            
                        elif event_type == "A":  # Aggregate (bar)
                            open_price = message.get("o")
                            high = message.get("h")
                            low = message.get("l")
                            close = message.get("c")
                            volume = message.get("v")
                            timestamp = message.get("t")
                            
                            self._update_price_cache(symbol, {
                                'open': open_price,
                                'high': high,
                                'low': low,
                                'close': close,
                                'volume': volume,
                                'timestamp': timestamp,
                                'source': 'polygon_bar'
                            })
                            
                elif msg.type == aiohttp.WSMsgType.ERROR:
                    logger.error(f"WebSocket error: {msg}")
                    break
                    
        except Exception as e:
            logger.error(f"Error handling Polygon messages: {e}")
            raise
    
    def _update_price_cache(self, symbol: str, price_data: Dict[str, Any]):
        """Update price cache and notify subscribers"""
        self.price_cache[symbol] = {
            **price_data,
            'last_updated': time.time()
        }
        
        # Notify subscribers
        if symbol in self.subscribers:
            for callback in self.subscribers[symbol]:
                try:
                    callback(symbol, price_data)
                except Exception as e:
                    logger.error(f"Error in subscriber callback for {symbol}: {e}")
    
    def subscribe(self, symbol: str, callback: Callable[[str, Dict], None]):
        """
        Subscribe to price updates for a symbol.
        
        Args:
            symbol: Stock symbol
            callback: Function(symbol, price_data) called on updates
        """
        if symbol not in self.subscribers:
            self.subscribers[symbol] = []
        self.subscribers[symbol].append(callback)
    
    def unsubscribe(self, symbol: str, callback: Callable[[str, Dict], None]):
        """Unsubscribe from price updates"""
        if symbol in self.subscribers:
            if callback in self.subscribers[symbol]:
                self.subscribers[symbol].remove(callback)
    
    def get_latest_price(self, symbol: str) -> Optional[Dict[str, Any]]:
        """
        Get latest cached price for symbol.
        
        Args:
            symbol: Stock symbol
        
        Returns:
            Latest price data or None
        """
        return self.price_cache.get(symbol)
    
    async def start_streaming(
        self,
        symbols: List[str],
        provider: str = "alpaca",
        api_key: Optional[str] = None,
        api_secret: Optional[str] = None
    ):
        """
        Start streaming prices for symbols.
        
        Args:
            symbols: List of symbols to stream
            provider: "alpaca" or "polygon"
            api_key: API key
            api_secret: API secret (for Alpaca)
        """
        self.is_running = True
        
        if provider == "alpaca":
            if not api_key or not api_secret:
                logger.error("Alpaca requires both api_key and api_secret")
                return
            
            await self.connect_alpaca(symbols, api_key, api_secret)
            
        elif provider == "polygon":
            if not api_key:
                logger.error("Polygon requires api_key")
                return
            
            await self.connect_polygon(symbols, api_key)
        
        else:
            logger.error(f"Unknown provider: {provider}")
    
    async def stop_streaming(self):
        """Stop all WebSocket connections"""
        self.is_running = False
        
        for symbol, ws in self.connections.items():
            try:
                await ws.close()
            except:
                pass
        
        self.connections.clear()
        logger.info("✅ Stopped all WebSocket connections")


# Global instance
_websocket_service = None

def get_websocket_service() -> WebSocketStreamingService:
    """Get global WebSocket streaming service instance"""
    global _websocket_service
    if _websocket_service is None:
        _websocket_service = WebSocketStreamingService()
    return _websocket_service

