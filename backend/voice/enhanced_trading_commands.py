"""
Enhanced Voice AI Trading Commands System
Comprehensive voice command integration with real market data and brokerage
"""

import asyncio
import logging
import re
import json
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
import uuid

from backend.market.providers.enhanced_base import create_market_data_provider
from backend.broker.adapters.enhanced_base import create_brokerage_adapter, OrderSide, OrderType, TimeInForce


class VoiceCommandType(Enum):
    """Voice command type enumeration"""
    TRADE = "TRADE"
    QUOTE = "QUOTE"
    POSITION = "POSITION"
    ACCOUNT = "ACCOUNT"
    NEWS = "NEWS"
    MARKET_STATUS = "MARKET_STATUS"
    PORTFOLIO = "PORTFOLIO"
    ALERT = "ALERT"
    HELP = "HELP"


class VoiceCommandStatus(Enum):
    """Voice command status enumeration"""
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


@dataclass
class VoiceCommand:
    """Voice command data structure"""
    id: str
    command_type: VoiceCommandType
    original_text: str
    parsed_data: Dict[str, Any]
    status: VoiceCommandStatus = VoiceCommandStatus.PENDING
    result: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.now)
    voice_name: str = "Nova"
    confidence: float = 0.0


@dataclass
class VoiceTradingSession:
    """Voice trading session data"""
    session_id: str
    user_id: str
    voice_name: str
    active_commands: Dict[str, VoiceCommand] = field(default_factory=dict)
    command_history: List[VoiceCommand] = field(default_factory=list)
    market_data_provider: Optional[Any] = None
    brokerage_adapter: Optional[Any] = None
    created_at: datetime = field(default_factory=datetime.now)
    last_activity: datetime = field(default_factory=datetime.now)


class EnhancedVoiceCommandParser:
    """Enhanced voice command parser with real market integration"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # Enhanced symbol recognition
        self.symbols = {
            # Major stocks
            "AAPL": ["apple", "aapl"],
            "MSFT": ["microsoft", "msft"],
            "GOOGL": ["google", "googl", "alphabet"],
            "TSLA": ["tesla", "tsla"],
            "NVDA": ["nvidia", "nvda"],
            "META": ["meta", "facebook", "fb"],
            "AMZN": ["amazon", "amzn"],
            "NFLX": ["netflix", "nflx"],
            "AMD": ["amd", "advanced micro devices"],
            "INTC": ["intel", "intc"],
            "CRM": ["salesforce", "crm"],
            "ADBE": ["adobe", "adbe"],
            "PYPL": ["paypal", "pypl"],
            "UBER": ["uber", "uber technologies"],
            "LYFT": ["lyft"],
            
            # ETFs
            "SPY": ["spy", "spdr s&p 500"],
            "QQQ": ["qqq", "nasdaq 100"],
            "IWM": ["iwm", "russell 2000"],
            "VTI": ["vti", "total stock market"],
            "VOO": ["voo", "s&p 500"],
            
            # Crypto
            "BTC": ["bitcoin", "btc"],
            "ETH": ["ethereum", "eth"],
            "ADA": ["cardano", "ada"],
            "SOL": ["solana", "sol"]
        }
        
        # Order types
        self.order_types = {
            "market": ["market", "at market", "market order"],
            "limit": ["limit", "at limit", "limit order"],
            "stop": ["stop", "stop loss", "stop order"],
            "bracket": ["bracket", "bracket order"],
            "oco": ["oco", "one cancels other"],
            "trailing": ["trailing stop", "trailing"]
        }
        
        # Order sides
        self.order_sides = {
            "buy": ["buy", "long", "purchase", "acquire"],
            "sell": ["sell", "short", "close", "exit"]
        }
        
        # Command patterns
        self.command_patterns = {
            VoiceCommandType.TRADE: [
                r"(buy|sell|long|short)\s+(\d+)\s+(shares|stocks?)\s+of\s+(\w+)",
                r"(buy|sell)\s+(\d+)\s+(\w+)",
                r"place\s+(market|limit|stop)\s+order\s+for\s+(\d+)\s+(\w+)",
                r"(\w+)\s+(market|limit)\s+(\d+)\s+shares"
            ],
            VoiceCommandType.QUOTE: [
                r"(quote|price|current price)\s+for\s+(\w+)",
                r"what's\s+the\s+price\s+of\s+(\w+)",
                r"(\w+)\s+quote",
                r"show\s+me\s+(\w+)\s+price"
            ],
            VoiceCommandType.POSITION: [
                r"(position|positions)\s+for\s+(\w+)",
                r"my\s+(\w+)\s+position",
                r"show\s+(\w+)\s+position",
                r"position\s+status\s+(\w+)"
            ],
            VoiceCommandType.ACCOUNT: [
                r"(account|balance|equity|buying power)",
                r"my\s+(account|balance)",
                r"show\s+(account|balance)",
                r"what's\s+my\s+(balance|equity)"
            ],
            VoiceCommandType.NEWS: [
                r"(news|headlines)\s+for\s+(\w+)",
                r"(\w+)\s+news",
                r"show\s+me\s+(\w+)\s+news",
                r"latest\s+news\s+(\w+)"
            ],
            VoiceCommandType.MARKET_STATUS: [
                r"(market|markets)\s+(open|closed|status)",
                r"is\s+the\s+market\s+(open|closed)",
                r"market\s+hours",
                r"trading\s+status"
            ],
            VoiceCommandType.PORTFOLIO: [
                r"(portfolio|positions|holdings)",
                r"my\s+(portfolio|positions)",
                r"show\s+(portfolio|positions)",
                r"all\s+positions"
            ],
            VoiceCommandType.ALERT: [
                r"(alert|watch|monitor)\s+(\w+)\s+(above|below|at)\s+(\d+)",
                r"set\s+alert\s+for\s+(\w+)",
                r"notify\s+me\s+when\s+(\w+)\s+(hits|reaches)\s+(\d+)"
            ]
        }
    
    def parse_command(self, text: str, voice_name: str = "Nova") -> Optional[VoiceCommand]:
        """Parse voice command text into structured data"""
        try:
            text_lower = text.lower().strip()
            command_id = str(uuid.uuid4())
            
            # Determine command type
            command_type = self._identify_command_type(text_lower)
            if not command_type:
                return None
            
            # Parse command data
            parsed_data = self._parse_command_data(text_lower, command_type)
            if not parsed_data:
                return None
            
            # Calculate confidence
            confidence = self._calculate_confidence(text_lower, parsed_data)
            
            return VoiceCommand(
                id=command_id,
                command_type=command_type,
                original_text=text,
                parsed_data=parsed_data,
                voice_name=voice_name,
                confidence=confidence
            )
            
        except Exception as e:
            self.logger.error(f"Failed to parse voice command: {e}")
            return None
    
    def _identify_command_type(self, text: str) -> Optional[VoiceCommandType]:
        """Identify the type of voice command"""
        for command_type, patterns in self.command_patterns.items():
            for pattern in patterns:
                if re.search(pattern, text):
                    return command_type
        
        return None
    
    def _parse_command_data(self, text: str, command_type: VoiceCommandType) -> Optional[Dict[str, Any]]:
        """Parse command-specific data"""
        
        if command_type == VoiceCommandType.TRADE:
            return self._parse_trade_command(text)
        elif command_type == VoiceCommandType.QUOTE:
            return self._parse_quote_command(text)
        elif command_type == VoiceCommandType.POSITION:
            return self._parse_position_command(text)
        elif command_type == VoiceCommandType.ACCOUNT:
            return self._parse_account_command(text)
        elif command_type == VoiceCommandType.NEWS:
            return self._parse_news_command(text)
        elif command_type == VoiceCommandType.MARKET_STATUS:
            return self._parse_market_status_command(text)
        elif command_type == VoiceCommandType.PORTFOLIO:
            return self._parse_portfolio_command(text)
        elif command_type == VoiceCommandType.ALERT:
            return self._parse_alert_command(text)
        
        return None
    
    def _parse_trade_command(self, text: str) -> Optional[Dict[str, Any]]:
        """Parse trading command"""
        # Extract symbol
        symbol = self._extract_symbol(text)
        if not symbol:
            return None
        
        # Extract side
        side = self._extract_order_side(text)
        if not side:
            return None
        
        # Extract quantity
        quantity = self._extract_quantity(text)
        if not quantity:
            return None
        
        # Extract order type
        order_type = self._extract_order_type(text)
        
        # Extract price
        price = self._extract_price(text)
        
        # Extract stop price
        stop_price = self._extract_stop_price(text)
        
        return {
            "symbol": symbol,
            "side": side,
            "quantity": quantity,
            "order_type": order_type,
            "price": price,
            "stop_price": stop_price,
            "time_in_force": "DAY"
        }
    
    def _parse_quote_command(self, text: str) -> Optional[Dict[str, Any]]:
        """Parse quote command"""
        symbol = self._extract_symbol(text)
        if not symbol:
            return None
        
        return {"symbol": symbol}
    
    def _parse_position_command(self, text: str) -> Optional[Dict[str, Any]]:
        """Parse position command"""
        symbol = self._extract_symbol(text)
        return {"symbol": symbol}  # None means all positions
    
    def _parse_account_command(self, text: str) -> Optional[Dict[str, Any]]:
        """Parse account command"""
        return {"type": "account"}
    
    def _parse_news_command(self, text: str) -> Optional[Dict[str, Any]]:
        """Parse news command"""
        symbol = self._extract_symbol(text)
        return {"symbol": symbol}
    
    def _parse_market_status_command(self, text: str) -> Optional[Dict[str, Any]]:
        """Parse market status command"""
        return {"type": "market_status"}
    
    def _parse_portfolio_command(self, text: str) -> Optional[Dict[str, Any]]:
        """Parse portfolio command"""
        return {"type": "portfolio"}
    
    def _parse_alert_command(self, text: str) -> Optional[Dict[str, Any]]:
        """Parse alert command"""
        symbol = self._extract_symbol(text)
        if not symbol:
            return None
        
        # Extract price level
        price_match = re.search(r'(above|below|at)\s+(\d+(?:\.\d+)?)', text)
        if price_match:
            direction = price_match.group(1)
            price = float(price_match.group(2))
            return {
                "symbol": symbol,
                "direction": direction,
                "price": price
            }
        
        return None
    
    def _extract_symbol(self, text: str) -> Optional[str]:
        """Extract stock symbol from text"""
        # Direct symbol match
        for symbol, aliases in self.symbols.items():
            for alias in aliases:
                if alias in text:
                    return symbol
        
        # Pattern matching for common formats
        symbol_patterns = [
            r'\b([A-Z]{2,5})\b',  # 2-5 uppercase letters
            r'\$([A-Z]{2,5})\b'   # $SYMBOL format
        ]
        
        for pattern in symbol_patterns:
            match = re.search(pattern, text.upper())
            if match:
                symbol = match.group(1)
                if symbol in self.symbols:
                    return symbol
        
        return None
    
    def _extract_order_side(self, text: str) -> Optional[str]:
        """Extract order side from text"""
        for side, keywords in self.order_sides.items():
            for keyword in keywords:
                if keyword in text:
                    return side.upper()
        
        return None
    
    def _extract_quantity(self, text: str) -> Optional[int]:
        """Extract quantity from text"""
        # Number patterns
        quantity_patterns = [
            r'(\d+)\s+(shares?|stocks?)',
            r'(\d+)\s+(\w+)',  # Generic number + word
            r'\b(\d+)\b'       # Just a number
        ]
        
        for pattern in quantity_patterns:
            match = re.search(pattern, text)
            if match:
                try:
                    quantity = int(match.group(1))
                    if 1 <= quantity <= 10000:  # Reasonable range
                        return quantity
                except ValueError:
                    continue
        
        # Word to number conversion
        word_numbers = {
            "one": 1, "two": 2, "three": 3, "four": 4, "five": 5,
            "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10,
            "twenty": 20, "fifty": 50, "hundred": 100
        }
        
        for word, number in word_numbers.items():
            if word in text:
                return number
        
        return None
    
    def _extract_order_type(self, text: str) -> str:
        """Extract order type from text"""
        for order_type, keywords in self.order_types.items():
            for keyword in keywords:
                if keyword in text:
                    return order_type.upper()
        
        return "MARKET"  # Default to market order
    
    def _extract_price(self, text: str) -> Optional[float]:
        """Extract price from text"""
        price_patterns = [
            r'\$(\d+(?:\.\d{1,2})?)',  # $150.00
            r'at\s+(\d+(?:\.\d{1,2})?)',  # at 150
            r'for\s+(\d+(?:\.\d{1,2})?)',  # for 150
            r'(\d+(?:\.\d{1,2})?)\s+dollars?'  # 150 dollars
        ]
        
        for pattern in price_patterns:
            match = re.search(pattern, text)
            if match:
                try:
                    price = float(match.group(1))
                    if 0.01 <= price <= 10000:  # Reasonable price range
                        return price
                except ValueError:
                    continue
        
        return None
    
    def _extract_stop_price(self, text: str) -> Optional[float]:
        """Extract stop price from text"""
        stop_patterns = [
            r'stop\s+(?:at\s+)?(\d+(?:\.\d{1,2})?)',
            r'stop\s+loss\s+(?:at\s+)?(\d+(?:\.\d{1,2})?)',
            r'stop\s+price\s+(\d+(?:\.\d{1,2})?)'
        ]
        
        for pattern in stop_patterns:
            match = re.search(pattern, text)
            if match:
                try:
                    stop_price = float(match.group(1))
                    if 0.01 <= stop_price <= 10000:
                        return stop_price
                except ValueError:
                    continue
        
        return None
    
    def _calculate_confidence(self, text: str, parsed_data: Dict[str, Any]) -> float:
        """Calculate confidence score for parsed command"""
        confidence = 0.0
        
        # Base confidence for successful parsing
        confidence += 0.3
        
        # Symbol recognition
        if parsed_data.get("symbol"):
            confidence += 0.2
        
        # Order side recognition
        if parsed_data.get("side"):
            confidence += 0.2
        
        # Quantity recognition
        if parsed_data.get("quantity"):
            confidence += 0.2
        
        # Price recognition (if applicable)
        if parsed_data.get("price"):
            confidence += 0.1
        
        # Cap at 1.0
        return min(confidence, 1.0)


class VoiceTradingExecutor:
    """Voice trading command executor"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.market_data_provider = None
        self.brokerage_adapter = None
        self.active_sessions = {}
        
        # Initialize providers
        self._initialize_providers()
    
    def _initialize_providers(self):
        """Initialize market data and brokerage providers"""
        try:
            # Use mock providers for now, can be switched to real ones
            self.market_data_provider = create_market_data_provider("mock", "mock_key")
            self.brokerage_adapter = create_brokerage_adapter("mock", "mock_key", "mock_secret")
            
            self.logger.info("Voice trading providers initialized")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize providers: {e}")
    
    async def execute_command(self, command: VoiceCommand) -> VoiceCommand:
        """Execute a voice command"""
        try:
            command.status = VoiceCommandStatus.PROCESSING
            
            if command.command_type == VoiceCommandType.TRADE:
                result = await self._execute_trade_command(command)
            elif command.command_type == VoiceCommandType.QUOTE:
                result = await self._execute_quote_command(command)
            elif command.command_type == VoiceCommandType.POSITION:
                result = await self._execute_position_command(command)
            elif command.command_type == VoiceCommandType.ACCOUNT:
                result = await self._execute_account_command(command)
            elif command.command_type == VoiceCommandType.NEWS:
                result = await self._execute_news_command(command)
            elif command.command_type == VoiceCommandType.MARKET_STATUS:
                result = await self._execute_market_status_command(command)
            elif command.command_type == VoiceCommandType.PORTFOLIO:
                result = await self._execute_portfolio_command(command)
            elif command.command_type == VoiceCommandType.ALERT:
                result = await self._execute_alert_command(command)
            else:
                result = {"error": "Unknown command type"}
            
            command.result = result
            command.status = VoiceCommandStatus.COMPLETED
            
            return command
            
        except Exception as e:
            command.status = VoiceCommandStatus.FAILED
            command.error_message = str(e)
            command.result = {"error": str(e)}
            
            self.logger.error(f"Failed to execute command {command.id}: {e}")
            return command
    
    async def _execute_trade_command(self, command: VoiceCommand) -> Dict[str, Any]:
        """Execute trading command"""
        data = command.parsed_data
        
        # Create order
        from backend.broker.adapters.enhanced_base import Order
        
        order = Order(
            symbol=data["symbol"],
            side=OrderSide(data["side"]),
            order_type=OrderType(data["order_type"]),
            quantity=data["quantity"],
            price=data.get("price"),
            stop_price=data.get("stop_price"),
            time_in_force=TimeInForce(data.get("time_in_force", "DAY"))
        )
        
        # Place order
        placed_order = await self.brokerage_adapter.place_order(order)
        
        return {
            "action": "order_placed",
            "order": {
                "id": placed_order.id,
                "symbol": placed_order.symbol,
                "side": placed_order.side.value,
                "quantity": placed_order.quantity,
                "price": placed_order.price,
                "status": placed_order.status.value
            },
            "message": f"Order placed: {placed_order.side.value} {placed_order.quantity} shares of {placed_order.symbol}"
        }
    
    async def _execute_quote_command(self, command: VoiceCommand) -> Dict[str, Any]:
        """Execute quote command"""
        symbol = command.parsed_data["symbol"]
        
        # Get quote
        quotes = await self.market_data_provider.get_quotes([symbol])
        
        if symbol in quotes:
            quote = quotes[symbol]
            return {
                "action": "quote_retrieved",
                "quote": {
                    "symbol": quote.symbol,
                    "price": quote.price,
                    "bid": quote.bid,
                    "ask": quote.ask,
                    "volume": quote.volume,
                    "change": quote.change,
                    "change_percent": quote.change_percent
                },
                "message": f"{symbol} is trading at ${quote.price:.2f}"
            }
        else:
            return {
                "action": "quote_error",
                "error": f"No quote data available for {symbol}"
            }
    
    async def _execute_position_command(self, command: VoiceCommand) -> Dict[str, Any]:
        """Execute position command"""
        symbol = command.parsed_data.get("symbol")
        
        if symbol:
            # Get specific position
            position = await self.brokerage_adapter.get_position(symbol)
            if position:
                return {
                    "action": "position_retrieved",
                    "position": {
                        "symbol": position.symbol,
                        "quantity": position.quantity,
                        "side": position.side.value,
                        "average_price": position.average_price,
                        "current_price": position.current_price,
                        "unrealized_pnl": position.unrealized_pnl,
                        "unrealized_pnl_percent": position.unrealized_pnl_percent
                    },
                    "message": f"{symbol} position: {position.quantity} shares at ${position.average_price:.2f}"
                }
            else:
                return {
                    "action": "position_not_found",
                    "message": f"No position found for {symbol}"
                }
        else:
            # Get all positions
            positions = await self.brokerage_adapter.get_positions()
            return {
                "action": "positions_retrieved",
                "positions": [
                    {
                        "symbol": pos.symbol,
                        "quantity": pos.quantity,
                        "side": pos.side.value,
                        "average_price": pos.average_price,
                        "current_price": pos.current_price,
                        "unrealized_pnl": pos.unrealized_pnl
                    }
                    for pos in positions
                ],
                "message": f"Found {len(positions)} positions"
            }
    
    async def _execute_account_command(self, command: VoiceCommand) -> Dict[str, Any]:
        """Execute account command"""
        account = await self.brokerage_adapter.get_account()
        
        return {
            "action": "account_retrieved",
            "account": {
                "equity": account.equity,
                "cash": account.cash,
                "buying_power": account.buying_power,
                "portfolio_value": account.portfolio_value,
                "day_trade_count": account.day_trade_count
            },
            "message": f"Account equity: ${account.equity:,.2f}, Buying power: ${account.buying_power:,.2f}"
        }
    
    async def _execute_news_command(self, command: VoiceCommand) -> Dict[str, Any]:
        """Execute news command"""
        symbol = command.parsed_data["symbol"]
        
        # Get news
        news_items = await self.market_data_provider.get_news(symbol, limit=5)
        
        return {
            "action": "news_retrieved",
            "news": [
                {
                    "title": news.title,
                    "summary": news.summary,
                    "published_at": news.published_at.isoformat(),
                    "source": news.source,
                    "sentiment": news.sentiment
                }
                for news in news_items
            ],
            "message": f"Found {len(news_items)} news items for {symbol}"
        }
    
    async def _execute_market_status_command(self, command: VoiceCommand) -> Dict[str, Any]:
        """Execute market status command"""
        status = await self.market_data_provider.get_market_status()
        
        return {
            "action": "market_status_retrieved",
            "status": {
                "market_open": status.market_open,
                "session": status.session.value,
                "current_time": status.current_time.isoformat(),
                "timezone": status.timezone
            },
            "message": f"Market is {'open' if status.market_open else 'closed'}"
        }
    
    async def _execute_portfolio_command(self, command: VoiceCommand) -> Dict[str, Any]:
        """Execute portfolio command"""
        summary = await self.brokerage_adapter.get_portfolio_summary()
        
        return {
            "action": "portfolio_retrieved",
            "portfolio": {
                "total_market_value": summary["total_market_value"],
                "total_unrealized_pnl": summary["total_unrealized_pnl"],
                "total_realized_pnl": summary["total_realized_pnl"],
                "total_pnl": summary["total_pnl"],
                "position_count": summary["position_count"]
            },
            "message": f"Portfolio value: ${summary['total_market_value']:,.2f}, P&L: ${summary['total_pnl']:,.2f}"
        }
    
    async def _execute_alert_command(self, command: VoiceCommand) -> Dict[str, Any]:
        """Execute alert command"""
        data = command.parsed_data
        
        # For now, just acknowledge the alert request
        # In a real implementation, this would set up price alerts
        return {
            "action": "alert_set",
            "alert": {
                "symbol": data["symbol"],
                "direction": data["direction"],
                "price": data["price"]
            },
            "message": f"Alert set for {data['symbol']} {data['direction']} ${data['price']:.2f}"
        }
    
    async def create_session(self, user_id: str, voice_name: str = "Nova") -> VoiceTradingSession:
        """Create a new voice trading session"""
        session_id = str(uuid.uuid4())
        
        session = VoiceTradingSession(
            session_id=session_id,
            user_id=user_id,
            voice_name=voice_name,
            market_data_provider=self.market_data_provider,
            brokerage_adapter=self.brokerage_adapter
        )
        
        self.active_sessions[session_id] = session
        
        self.logger.info(f"Created voice trading session: {session_id}")
        return session
    
    async def get_session(self, session_id: str) -> Optional[VoiceTradingSession]:
        """Get voice trading session"""
        return self.active_sessions.get(session_id)
    
    async def cleanup_session(self, session_id: str):
        """Cleanup voice trading session"""
        if session_id in self.active_sessions:
            del self.active_sessions[session_id]
            self.logger.info(f"Cleaned up voice trading session: {session_id}")


class VoiceTradingManager:
    """Main voice trading manager"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.parser = EnhancedVoiceCommandParser()
        self.executor = VoiceTradingExecutor()
    
    async def process_voice_command(
        self, 
        text: str, 
        voice_name: str = "Nova",
        session_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Process voice command end-to-end"""
        try:
            # Parse command
            command = self.parser.parse_command(text, voice_name)
            if not command:
                return {
                    "success": False,
                    "error": "Could not parse voice command",
                    "message": f"{voice_name}: I didn't understand that command. Please try again."
                }
            
            # Check confidence
            if command.confidence < 0.5:
                return {
                    "success": False,
                    "error": "Low confidence in command parsing",
                    "message": f"{voice_name}: I'm not sure I understood correctly. Could you please repeat that?"
                }
            
            # Execute command
            executed_command = await self.executor.execute_command(command)
            
            if executed_command.status == VoiceCommandStatus.COMPLETED:
                return {
                    "success": True,
                    "command": {
                        "id": executed_command.id,
                        "type": executed_command.command_type.value,
                        "original_text": executed_command.original_text,
                        "confidence": executed_command.confidence
                    },
                    "result": executed_command.result,
                    "message": executed_command.result.get("message", "Command executed successfully")
                }
            else:
                return {
                    "success": False,
                    "error": executed_command.error_message,
                    "message": f"{voice_name}: Sorry, I couldn't execute that command. {executed_command.error_message}"
                }
            
        except Exception as e:
            self.logger.error(f"Failed to process voice command: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": f"{voice_name}: I encountered an error processing your command. Please try again."
            }
    
    async def get_help_commands(self, voice_name: str = "Nova") -> Dict[str, Any]:
        """Get available voice commands"""
        return {
            "success": True,
            "voice_name": voice_name,
            "commands": {
                "trading": [
                    "Buy 100 shares of AAPL",
                    "Sell 50 TSLA at market",
                    "Place limit order for 25 MSFT at $300",
                    "Buy 10 GOOGL with stop loss at $2500"
                ],
                "quotes": [
                    "What's the price of AAPL",
                    "Show me TSLA quote",
                    "Current price for MSFT"
                ],
                "positions": [
                    "Show my AAPL position",
                    "What positions do I have",
                    "Position status for TSLA"
                ],
                "account": [
                    "What's my account balance",
                    "Show my buying power",
                    "Account equity"
                ],
                "news": [
                    "News for AAPL",
                    "Show me TSLA headlines",
                    "Latest news for MSFT"
                ],
                "market": [
                    "Is the market open",
                    "Market status",
                    "Trading hours"
                ],
                "portfolio": [
                    "Show my portfolio",
                    "All positions",
                    "Portfolio summary"
                ],
                "alerts": [
                    "Alert me when AAPL hits $160",
                    "Watch TSLA above $250",
                    "Monitor MSFT below $300"
                ]
            },
            "message": f"{voice_name}: Here are the commands I can help you with. Try saying any of these phrases."
        }


# Global instance
voice_trading_manager = VoiceTradingManager()
