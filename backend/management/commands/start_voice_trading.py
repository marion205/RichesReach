"""
RichesReach Voice AI Trading Integration
Complete setup script for voice-powered day trading
"""

import asyncio
import logging
import os
from datetime import datetime
from django.conf import settings
from django.core.management.base import BaseCommand

from backend.streaming.alpaca_websocket import create_alpaca_streamer
from backend.voice.command_parser import VoiceCommandParser
from backend.broker.adapters.alpaca_paper import AlpacaPaperBroker
from backend.market.providers.polygon import PolygonProvider


class VoiceTradingManager:
    """Main manager for voice AI trading system"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.alpaca_streamer = None
        self.broker = None
        self.market_data_provider = None
        self.voice_parser = VoiceCommandParser()
        self.running = False
        
        # Configuration
        self.config = {
            "max_symbols": 20,
            "rvol_threshold": 2.0,
            "spread_threshold": 5.0,  # bps
            "confidence_threshold": 0.7,
            "voice_alerts_enabled": True,
            "paper_trading": True,
        }
    
    async def initialize(self):
        """Initialize all components"""
        try:
            self.logger.info("🚀 Initializing Voice AI Trading System...")
            
            # Initialize broker
            self.broker = AlpacaPaperBroker(
                api_key_id=settings.ALPACA_API_KEY_ID,
                api_secret_key=settings.ALPACA_SECRET_KEY
            )
            
            # Initialize market data provider
            self.market_data_provider = PolygonProvider(
                api_key=settings.POLYGON_API_KEY
            )
            
            # Initialize WebSocket streamer
            self.alpaca_streamer = await create_alpaca_streamer(
                api_key=settings.ALPACA_API_KEY_ID,
                secret_key=settings.ALPACA_SECRET_KEY,
                paper=self.config["paper_trading"]
            )
            
            self.logger.info("✅ Voice AI Trading System initialized successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Initialization failed: {e}")
            return False
    
    async def start_streaming(self, symbols: list):
        """Start streaming quotes for symbols"""
        try:
            if not self.alpaca_streamer:
                await self.initialize()
            
            # Limit symbols to avoid rate limits
            limited_symbols = symbols[:self.config["max_symbols"]]
            
            await self.alpaca_streamer.subscribe_quotes(limited_symbols)
            self.logger.info(f"📡 Started streaming quotes for {len(limited_symbols)} symbols")
            
            # Start listening loop
            self.running = True
            await self.alpaca_streamer.listen()
            
        except Exception as e:
            self.logger.error(f"❌ Streaming failed: {e}")
    
    async def process_voice_command(self, transcript: str, user_id: str = None):
        """Process voice command and execute trade if confirmed"""
        try:
            # Parse voice command
            parsed_order = self.voice_parser.parse_command(transcript)
            
            if not parsed_order:
                return {
                    "success": False,
                    "message": "Could not parse voice command",
                    "error": "Invalid command format"
                }
            
            # Check confidence threshold
            if parsed_order.confidence < self.config["confidence_threshold"]:
                return {
                    "success": False,
                    "message": "Command confidence too low",
                    "error": f"Confidence: {parsed_order.confidence:.2f}"
                }
            
            # Get current quote for validation
            quotes = await self.market_data_provider.get_quotes([parsed_order.symbol])
            if parsed_order.symbol not in quotes:
                return {
                    "success": False,
                    "message": "Symbol not found",
                    "error": f"Could not get quote for {parsed_order.symbol}"
                }
            
            quote = quotes[parsed_order.symbol]
            
            # Check spread threshold
            spread_bps = ((quote.ask - quote.bid) / quote.bid) * 10000
            if spread_bps > self.config["spread_threshold"]:
                return {
                    "success": False,
                    "message": "Spread too wide",
                    "error": f"Spread: {spread_bps:.1f} bps"
                }
            
            # Execute order
            order = await self.broker.place_order(
                symbol=parsed_order.symbol,
                side=self._map_side(parsed_order.side),
                quantity=parsed_order.quantity,
                order_type=self._map_order_type(parsed_order.order_type),
                limit_price=parsed_order.price,
                client_order_id=f"voice-{user_id}-{datetime.now().timestamp()}"
            )
            
            # Log the trade
            await self._log_trade(parsed_order, order, user_id)
            
            return {
                "success": True,
                "order_id": order.id,
                "message": f"Order placed successfully: {order.symbol} {order.side} {order.quantity}",
                "order": {
                    "id": order.id,
                    "symbol": order.symbol,
                    "side": order.side.value,
                    "quantity": order.quantity,
                    "status": order.status.value,
                }
            }
            
        except Exception as e:
            self.logger.error(f"❌ Voice command processing failed: {e}")
            return {
                "success": False,
                "message": "Voice command processing failed",
                "error": str(e)
            }
    
    def _map_side(self, side: str):
        """Map string side to OrderSide enum"""
        from backend.broker.adapters.base import OrderSide
        return OrderSide.BUY if side.lower() == "buy" else OrderSide.SELL
    
    def _map_order_type(self, order_type: str):
        """Map string order type to OrderType enum"""
        from backend.broker.adapters.base import OrderType
        return OrderType(order_type.lower())
    
    async def _log_trade(self, parsed_order, order, user_id):
        """Log trade for analysis and compliance"""
        trade_log = {
            "timestamp": datetime.now().isoformat(),
            "user_id": user_id,
            "voice_command": parsed_order.raw_command,
            "parsed_order": {
                "symbol": parsed_order.symbol,
                "side": parsed_order.side,
                "quantity": parsed_order.quantity,
                "order_type": parsed_order.order_type,
                "price": parsed_order.price,
                "confidence": parsed_order.confidence,
            },
            "executed_order": {
                "id": order.id,
                "symbol": order.symbol,
                "side": order.side.value,
                "quantity": order.quantity,
                "status": order.status.value,
                "created_at": order.created_at.isoformat() if order.created_at else None,
            }
        }
        
        # Log to file or database
        self.logger.info(f"📊 Trade logged: {trade_log}")
    
    async def get_trading_status(self):
        """Get current trading status and metrics"""
        try:
            account = await self.broker.get_account()
            positions = await self.broker.get_positions()
            orders = await self.broker.get_orders()
            
            return {
                "account": {
                    "buying_power": account.buying_power,
                    "portfolio_value": account.portfolio_value,
                    "day_trade_count": account.day_trade_count,
                    "pattern_day_trader": account.pattern_day_trader,
                },
                "positions": [
                    {
                        "symbol": pos.symbol,
                        "quantity": pos.quantity,
                        "side": pos.side,
                        "market_value": pos.market_value,
                        "unrealized_pl": pos.unrealized_pl,
                    }
                    for pos in positions
                ],
                "open_orders": [
                    {
                        "id": order.id,
                        "symbol": order.symbol,
                        "side": order.side.value,
                        "quantity": order.quantity,
                        "status": order.status.value,
                    }
                    for order in orders
                    if order.status.value in ["new", "partially_filled"]
                ],
                "streaming": {
                    "active": self.running,
                    "symbols": list(self.alpaca_streamer.subscribed_symbols) if self.alpaca_streamer else [],
                }
            }
            
        except Exception as e:
            self.logger.error(f"❌ Status check failed: {e}")
            return {"error": str(e)}
    
    async def shutdown(self):
        """Shutdown the trading system"""
        self.running = False
        
        if self.alpaca_streamer:
            await self.alpaca_streamer.close()
        
        if self.broker:
            await self.broker.close()
        
        self.logger.info("🔌 Voice AI Trading System shutdown complete")


# Django management command
class Command(BaseCommand):
    help = 'Start Voice AI Trading System'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--symbols',
            nargs='+',
            default=['AAPL', 'MSFT', 'GOOGL', 'TSLA', 'NVDA'],
            help='Symbols to stream quotes for'
        )
        parser.add_argument(
            '--paper',
            action='store_true',
            default=True,
            help='Use paper trading'
        )
    
    def handle(self, *args, **options):
        symbols = options['symbols']
        paper_trading = options['paper']
        
        # Configure logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
        # Create and run trading manager
        manager = VoiceTradingManager()
        manager.config["paper_trading"] = paper_trading
        
        async def run():
            if await manager.initialize():
                self.stdout.write(
                    self.style.SUCCESS('✅ Voice AI Trading System started successfully')
                )
                await manager.start_streaming(symbols)
            else:
                self.stdout.write(
                    self.style.ERROR('❌ Failed to initialize Voice AI Trading System')
                )
        
        # Run the async function
        asyncio.run(run())


# Example usage
if __name__ == "__main__":
    async def main():
        manager = VoiceTradingManager()
        
        if await manager.initialize():
            print("✅ System initialized")
            
            # Test voice command
            result = await manager.process_voice_command(
                "Nova, buy 100 AAPL at limit $150",
                user_id="test_user"
            )
            print(f"Voice command result: {result}")
            
            # Get status
            status = await manager.get_trading_status()
            print(f"Trading status: {status}")
            
            await manager.shutdown()
    
    asyncio.run(main())
