"""
Alpaca WebSocket Streaming Integration
Real-time quote streaming for voice AI trading
"""

import asyncio
import json
import logging
from typing import Dict, List, Callable, Optional
from datetime import datetime
import aiohttp
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

from ..market.providers.base import MarketDataProvider
from ..broker.adapters.base import Broker


class AlpacaWebSocketStreamer:
    """Alpaca WebSocket streaming for real-time quotes"""
    
    def __init__(self, api_key: str, secret_key: str, paper: bool = True):
        self.api_key = api_key
        self.secret_key = secret_key
        self.paper = paper
        self.ws_url = "wss://paper-api.alpaca.markets/stream" if paper else "wss://api.alpaca.markets/stream"
        self.session = None
        self.websocket = None
        self.subscribed_symbols = set()
        self.quote_handlers = []
        self.logger = logging.getLogger(__name__)
        self.running = False
        
    async def connect(self):
        """Connect to Alpaca WebSocket"""
        try:
            self.session = aiohttp.ClientSession()
            
            # Authentication message
            auth_message = {
                "action": "auth",
                "key": self.api_key,
                "secret": self.secret_key
            }
            
            self.websocket = await self.session.ws_connect(self.ws_url)
            await self.websocket.send_str(json.dumps(auth_message))
            
            # Wait for auth confirmation
            auth_response = await self.websocket.receive()
            if auth_response.type == aiohttp.WSMsgType.TEXT:
                response_data = json.loads(auth_response.data)
                if response_data.get("T") == "success":
                    self.logger.info("✅ Alpaca WebSocket authenticated successfully")
                    self.running = True
                else:
                    self.logger.error(f"❌ WebSocket auth failed: {response_data}")
                    return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"❌ WebSocket connection failed: {e}")
            return False
    
    async def subscribe_quotes(self, symbols: List[str]):
        """Subscribe to quote updates for symbols"""
        if not self.websocket or not self.running:
            await self.connect()
        
        subscribe_message = {
            "action": "subscribe",
            "quotes": symbols
        }
        
        await self.websocket.send_str(json.dumps(subscribe_message))
        self.subscribed_symbols.update(symbols)
        self.logger.info(f"📡 Subscribed to quotes: {symbols}")
    
    async def unsubscribe_quotes(self, symbols: List[str]):
        """Unsubscribe from quote updates"""
        unsubscribe_message = {
            "action": "unsubscribe",
            "quotes": symbols
        }
        
        await self.websocket.send_str(json.dumps(unsubscribe_message))
        self.subscribed_symbols.difference_update(symbols)
        self.logger.info(f"📡 Unsubscribed from quotes: {symbols}")
    
    def add_quote_handler(self, handler: Callable):
        """Add quote update handler"""
        self.quote_handlers.append(handler)
    
    async def handle_quote_update(self, quote_data: Dict):
        """Handle incoming quote updates"""
        try:
            symbol = quote_data.get("S", "")
            bid_price = float(quote_data.get("bp", 0))
            ask_price = float(quote_data.get("ap", 0))
            bid_size = int(quote_data.get("bs", 0))
            ask_size = int(quote_data.get("as", 0))
            timestamp = quote_data.get("t", "")
            
            # Calculate spread in basis points
            if bid_price > 0 and ask_price > 0:
                spread_bps = ((ask_price - bid_price) / bid_price) * 10000
            else:
                spread_bps = 0
            
            quote_info = {
                "symbol": symbol,
                "bid_price": bid_price,
                "ask_price": ask_price,
                "bid_size": bid_size,
                "ask_size": ask_size,
                "spread_bps": spread_bps,
                "timestamp": timestamp,
                "mid_price": (bid_price + ask_price) / 2
            }
            
            # Call all registered handlers
            for handler in self.quote_handlers:
                try:
                    await handler(quote_info)
                except Exception as e:
                    self.logger.error(f"❌ Quote handler error: {e}")
            
            # Send to Django Channels for GraphQL subscriptions
            await self._send_to_channels(quote_info)
            
        except Exception as e:
            self.logger.error(f"❌ Quote update handling failed: {e}")
    
    async def _send_to_channels(self, quote_info: Dict):
        """Send quote update to Django Channels"""
        try:
            channel_layer = get_channel_layer()
            await channel_layer.group_send(
                "day_trading_updates",
                {
                    "type": "quote_update",
                    "symbol": quote_info["symbol"],
                    "bid_price": quote_info["bid_price"],
                    "ask_price": quote_info["ask_price"],
                    "spread_bps": quote_info["spread_bps"],
                    "timestamp": quote_info["timestamp"]
                }
            )
        except Exception as e:
            self.logger.error(f"❌ Channels send failed: {e}")
    
    async def listen(self):
        """Main listening loop"""
        if not self.running:
            return
        
        try:
            while self.running:
                msg = await self.websocket.receive()
                
                if msg.type == aiohttp.WSMsgType.TEXT:
                    data = json.loads(msg.data)
                    
                    # Handle different message types
                    if data.get("T") == "q":  # Quote update
                        await self.handle_quote_update(data)
                    elif data.get("T") == "success":
                        self.logger.info(f"✅ WebSocket operation successful: {data.get('msg', '')}")
                    elif data.get("T") == "error":
                        self.logger.error(f"❌ WebSocket error: {data.get('msg', '')}")
                
                elif msg.type == aiohttp.WSMsgType.ERROR:
                    self.logger.error(f"❌ WebSocket error: {msg.data}")
                    break
                
                elif msg.type == aiohttp.WSMsgType.CLOSE:
                    self.logger.info("🔌 WebSocket connection closed")
                    break
                    
        except Exception as e:
            self.logger.error(f"❌ WebSocket listening error: {e}")
        finally:
            await self.close()
    
    async def close(self):
        """Close WebSocket connection"""
        self.running = False
        if self.websocket:
            await self.websocket.close()
        if self.session:
            await self.session.close()
        self.logger.info("🔌 WebSocket connection closed")


class VoiceAITradingStreamer:
    """Voice AI integration with Alpaca streaming"""
    
    def __init__(self, alpaca_streamer: AlpacaWebSocketStreamer):
        self.alpaca_streamer = alpaca_streamer
        self.logger = logging.getLogger(__name__)
        self.rvol_thresholds = {
            "SAFE": 2.0,
            "AGGRESSIVE": 1.5
        }
        self.breakout_thresholds = {
            "SAFE": 0.5,
            "AGGRESSIVE": 0.3
        }
    
    async def handle_quote_for_voice(self, quote_info: Dict):
        """Handle quotes for voice AI alerts"""
        try:
            symbol = quote_info["symbol"]
            spread_bps = quote_info["spread_bps"]
            
            # Check for breakout conditions
            if spread_bps < 5:  # Tight spread indicates good liquidity
                # Calculate RVOL (would need historical data)
                rvol = await self._calculate_rvol(symbol)
                
                # Check for voice alert conditions
                if rvol > self.rvol_thresholds["AGGRESSIVE"]:
                    await self._trigger_voice_alert(symbol, "breakout", rvol, spread_bps)
                
                # Check for momentum
                momentum = await self._calculate_momentum(symbol)
                if abs(momentum) > self.breakout_thresholds["AGGRESSIVE"]:
                    direction = "up" if momentum > 0 else "down"
                    await self._trigger_voice_alert(symbol, f"{direction} momentum", momentum, spread_bps)
        
        except Exception as e:
            self.logger.error(f"❌ Voice quote handling failed: {e}")
    
    async def _calculate_rvol(self, symbol: str) -> float:
        """Calculate relative volume (mock implementation)"""
        # In real implementation, this would fetch historical volume data
        import random
        return random.uniform(0.5, 3.0)
    
    async def _calculate_momentum(self, symbol: str) -> float:
        """Calculate price momentum (mock implementation)"""
        # In real implementation, this would calculate 15-minute momentum
        import random
        return random.uniform(-2.0, 2.0)
    
    async def _trigger_voice_alert(self, symbol: str, alert_type: str, value: float, spread_bps: float):
        """Trigger voice AI alert"""
        try:
            # Generate alert message
            if alert_type == "breakout":
                message = f"Echo: {symbol} breakout detected! RVOL {value:.1f}x, spread {spread_bps:.1f} bps. Consider long position."
            elif "momentum" in alert_type:
                direction = "up" if value > 0 else "down"
                message = f"Nova: {symbol} {direction} momentum {abs(value):.1f}% - spread {spread_bps:.1f} bps."
            else:
                message = f"Oracle: {symbol} alert - {alert_type} {value:.2f}"
            
            # Send to voice AI system
            await self._send_voice_alert(symbol, message, alert_type)
            
            self.logger.info(f"🔊 Voice alert triggered: {symbol} - {alert_type}")
            
        except Exception as e:
            self.logger.error(f"❌ Voice alert failed: {e}")
    
    async def _send_voice_alert(self, symbol: str, message: str, alert_type: str):
        """Send alert to voice AI system"""
        try:
            # Send to Django Channels for voice AI
            channel_layer = get_channel_layer()
            await channel_layer.group_send(
                "voice_alerts",
                {
                    "type": "voice_alert",
                    "symbol": symbol,
                    "message": message,
                    "alert_type": alert_type,
                    "timestamp": datetime.now().isoformat()
                }
            )
        except Exception as e:
            self.logger.error(f"❌ Voice alert send failed: {e}")


# Factory function for easy setup
async def create_alpaca_streamer(api_key: str, secret_key: str, paper: bool = True) -> AlpacaWebSocketStreamer:
    """Create and configure Alpaca WebSocket streamer"""
    streamer = AlpacaWebSocketStreamer(api_key, secret_key, paper)
    
    # Add voice AI handler
    voice_handler = VoiceAITradingStreamer(streamer)
    streamer.add_quote_handler(voice_handler.handle_quote_for_voice)
    
    # Connect
    await streamer.connect()
    
    return streamer
