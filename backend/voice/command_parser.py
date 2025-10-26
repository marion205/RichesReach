"""
Voice AI Trading Command Parser
Parses natural language trading commands into structured order data
"""

import re
from typing import Dict, Optional, List
from dataclasses import dataclass
from enum import Enum


class OrderSide(Enum):
    BUY = "buy"
    SELL = "sell"
    LONG = "long"
    SHORT = "short"


class OrderType(Enum):
    MARKET = "market"
    LIMIT = "limit"
    STOP = "stop"
    STOP_LIMIT = "stop_limit"


@dataclass
class ParsedOrder:
    """Structured order data from voice command"""
    symbol: str
    side: str
    quantity: int
    order_type: str
    price: Optional[float] = None
    stop_price: Optional[float] = None
    confidence: float = 0.0
    raw_command: str = ""


class VoiceCommandParser:
    """Parses voice commands into trading orders"""
    
    def __init__(self):
        # Common trading symbols
        self.symbols = [
            "AAPL", "MSFT", "GOOGL", "AMZN", "TSLA", "META", "NVDA", "NFLX",
            "AMD", "INTC", "CRM", "ADBE", "PYPL", "UBER", "LYFT", "SQ"
        ]
        
        # Voice command patterns
        self.patterns = {
            # Buy patterns
            "buy": [
                r"(?:buy|long|purchase)\s+(\d+)\s+(\w+)(?:\s+at\s+(?:limit\s+)?(\$?\d+\.?\d*))?",
                r"(?:buy|long|purchase)\s+(\w+)\s+(\d+)(?:\s+at\s+(?:limit\s+)?(\$?\d+\.?\d*))?",
                r"(\d+)\s+(\w+)\s+(?:buy|long)(?:\s+at\s+(?:limit\s+)?(\$?\d+\.?\d*))?"
            ],
            # Sell patterns
            "sell": [
                r"(?:sell|short)\s+(\d+)\s+(\w+)(?:\s+at\s+(?:limit\s+)?(\$?\d+\.?\d*))?",
                r"(?:sell|short)\s+(\w+)\s+(\d+)(?:\s+at\s+(?:limit\s+)?(\$?\d+\.?\d*))?",
                r"(\d+)\s+(\w+)\s+(?:sell|short)(?:\s+at\s+(?:limit\s+)?(\$?\d+\.?\d*))?"
            ],
            # Market orders
            "market": [
                r"(?:buy|sell|long|short)\s+(\d+)\s+(\w+)\s+at\s+market",
                r"(\d+)\s+(\w+)\s+(?:buy|sell|long|short)\s+at\s+market"
            ],
            # Stop orders
            "stop": [
                r"(?:buy|sell|long|short)\s+(\d+)\s+(\w+)\s+stop\s+at\s+(\$?\d+\.?\d*)",
                r"(\d+)\s+(\w+)\s+(?:buy|sell|long|short)\s+stop\s+at\s+(\$?\d+\.?\d*)"
            ]
        }
        
        # Voice AI names for context
        self.voice_names = ["nova", "echo", "sage", "oracle", "zen", "quantum"]
    
    def parse_command(self, transcript: str) -> Optional[ParsedOrder]:
        """Parse voice command into structured order"""
        transcript = transcript.lower().strip()
        
        # Remove voice AI name if present
        for name in self.voice_names:
            transcript = transcript.replace(f"{name},", "").replace(f"{name} ", "")
        
        # Try each pattern type
        for order_type, patterns in self.patterns.items():
            for pattern in patterns:
                match = re.search(pattern, transcript)
                if match:
                    return self._build_order(match, order_type, transcript)
        
        return None
    
    def _build_order(self, match: re.Match, order_type: str, transcript: str) -> ParsedOrder:
        """Build ParsedOrder from regex match"""
        groups = match.groups()
        
        # Extract symbol and quantity
        if len(groups) >= 2:
            # Try to identify which group is symbol vs quantity
            symbol = None
            quantity = None
            price = None
            
            for group in groups:
                if group and group.upper() in self.symbols:
                    symbol = group.upper()
                elif group and group.isdigit():
                    quantity = int(group)
                elif group and self._is_price(group):
                    price = self._parse_price(group)
            
            if symbol and quantity:
                # Determine side based on order type
                side = self._determine_side(order_type, transcript)
                
                # Determine order type
                parsed_order_type = self._determine_order_type(order_type, price)
                
                # Calculate confidence
                confidence = self._calculate_confidence(symbol, quantity, transcript)
                
                return ParsedOrder(
                    symbol=symbol,
                    side=side,
                    quantity=quantity,
                    order_type=parsed_order_type,
                    price=price,
                    confidence=confidence,
                    raw_command=transcript
                )
        
        return None
    
    def _is_price(self, text: str) -> bool:
        """Check if text looks like a price"""
        try:
            # Remove $ and convert to float
            price_text = text.replace("$", "")
            float(price_text)
            return True
        except ValueError:
            return False
    
    def _parse_price(self, price_text: str) -> float:
        """Parse price text to float"""
        return float(price_text.replace("$", ""))
    
    def _determine_side(self, order_type: str, transcript: str) -> str:
        """Determine buy/sell side from context"""
        if order_type in ["buy", "market"] or any(word in transcript for word in ["buy", "long", "purchase"]):
            return "buy"
        elif order_type in ["sell", "stop"] or any(word in transcript for word in ["sell", "short"]):
            return "sell"
        else:
            return "buy"  # Default to buy
    
    def _determine_order_type(self, order_type: str, price: Optional[float]) -> str:
        """Determine order type"""
        if order_type == "stop":
            return "stop"
        elif price is not None:
            return "limit"
        else:
            return "market"
    
    def _calculate_confidence(self, symbol: str, quantity: int, transcript: str) -> float:
        """Calculate confidence score for parsed command"""
        confidence = 0.5  # Base confidence
        
        # Symbol confidence
        if symbol in self.symbols:
            confidence += 0.3
        
        # Quantity confidence
        if 1 <= quantity <= 10000:
            confidence += 0.1
        
        # Command clarity
        if any(word in transcript for word in ["buy", "sell", "long", "short"]):
            confidence += 0.1
        
        return min(confidence, 1.0)
    
    def get_confirmation_message(self, order: ParsedOrder, voice_name: str = "Nova") -> str:
        """Generate confirmation message for parsed order"""
        price_text = f" at ${order.price}" if order.price else " at market"
        
        return f"{voice_name} confirming: {order.side} {order.quantity} {order.symbol}{price_text}. Proceeding?"
    
    def get_execution_message(self, order: ParsedOrder, order_id: str, voice_name: str = "Nova") -> str:
        """Generate execution confirmation message"""
        return f"Order placed—ID {order_id}. Watching with Oracle."
    
    def get_error_message(self, error: str, voice_name: str = "Nova") -> str:
        """Generate error message"""
        return f"Sorry, I couldn't process that trade. {error}"


# Example usage and testing
def test_voice_parser():
    """Test the voice command parser"""
    parser = VoiceCommandParser()
    
    test_commands = [
        "Nova, buy 100 AAPL at limit $150",
        "Echo, sell 50 TSLA at market",
        "Long 25 MSFT at $300",
        "Short 10 NVDA stop at $200",
        "Buy 5 GOOGL",
        "Sell 100 META at limit $250"
    ]
    
    for command in test_commands:
        result = parser.parse_command(command)
        if result:
            print(f"Command: {command}")
            print(f"Parsed: {result.symbol} {result.side} {result.quantity} {result.order_type} {result.price}")
            print(f"Confidence: {result.confidence}")
            print(f"Confirmation: {parser.get_confirmation_message(result)}")
            print("---")
        else:
            print(f"Failed to parse: {command}")


if __name__ == "__main__":
    test_voice_parser()
