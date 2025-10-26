"""
Base brokerage adapter interface for day trading system.
Allows seamless integration with different brokers (Alpaca, Interactive Brokers, etc.)
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional
from dataclasses import dataclass
from datetime import datetime
from enum import Enum


class OrderSide(Enum):
    BUY = "buy"
    SELL = "sell"


class OrderType(Enum):
    MARKET = "market"
    LIMIT = "limit"
    STOP = "stop"
    STOP_LIMIT = "stop_limit"
    TRAILING_STOP = "trailing_stop"


class TimeInForce(Enum):
    DAY = "day"
    GTC = "gtc"  # Good Till Cancelled
    IOC = "ioc"  # Immediate or Cancel
    FOK = "fok"  # Fill or Kill


class OrderStatus(Enum):
    NEW = "new"
    PARTIALLY_FILLED = "partially_filled"
    FILLED = "filled"
    CANCELED = "canceled"
    REJECTED = "rejected"
    PENDING_CANCEL = "pending_cancel"


@dataclass
class Order:
    """Standardized order structure"""
    id: str
    symbol: str
    side: OrderSide
    type: OrderType
    quantity: int
    status: OrderStatus
    filled_quantity: int = 0
    remaining_quantity: int = 0
    limit_price: Optional[float] = None
    stop_price: Optional[float] = None
    average_fill_price: Optional[float] = None
    time_in_force: TimeInForce = TimeInForce.DAY
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    client_order_id: Optional[str] = None


@dataclass
class Position:
    """Standardized position structure"""
    symbol: str
    quantity: int
    side: str  # "long" or "short"
    market_value: float
    cost_basis: float
    unrealized_pl: float
    unrealized_plpc: float
    current_price: float
    lastday_price: float
    change_today: float


@dataclass
class Account:
    """Standardized account structure"""
    account_id: str
    buying_power: float
    cash: float
    portfolio_value: float
    equity: float
    long_market_value: float
    short_market_value: float
    initial_margin: float
    maintenance_margin: float
    day_trade_count: int
    pattern_day_trader: bool
    day_trading_buying_power: float


class Broker(ABC):
    """Base interface for brokerage adapters"""
    
    @abstractmethod
    async def place_order(
        self,
        symbol: str,
        side: OrderSide,
        quantity: int,
        order_type: OrderType,
        limit_price: Optional[float] = None,
        stop_price: Optional[float] = None,
        time_in_force: TimeInForce = TimeInForce.DAY,
        client_order_id: Optional[str] = None,
        bracket_orders: Optional[Dict] = None
    ) -> Order:
        """Place an order"""
        pass
    
    @abstractmethod
    async def cancel_order(self, order_id: str) -> Dict[str, str]:
        """Cancel an order"""
        pass
    
    @abstractmethod
    async def get_order(self, order_id: str) -> Order:
        """Get order details"""
        pass
    
    @abstractmethod
    async def get_orders(self, status: Optional[OrderStatus] = None) -> List[Order]:
        """Get all orders"""
        pass
    
    @abstractmethod
    async def get_positions(self) -> List[Position]:
        """Get all positions"""
        pass
    
    @abstractmethod
    async def get_position(self, symbol: str) -> Optional[Position]:
        """Get position for specific symbol"""
        pass
    
    @abstractmethod
    async def get_account(self) -> Account:
        """Get account information"""
        pass
    
    @abstractmethod
    async def get_market_data(self, symbols: List[str]) -> Dict[str, Dict]:
        """Get real-time market data"""
        pass


class MockBroker(Broker):
    """Mock broker for testing and development"""
    
    def __init__(self):
        self.orders = {}
        self.positions = {}
        self.account = Account(
            account_id="mock_account",
            buying_power=100000.0,
            cash=100000.0,
            portfolio_value=100000.0,
            equity=100000.0,
            long_market_value=0.0,
            short_market_value=0.0,
            initial_margin=0.0,
            maintenance_margin=0.0,
            day_trade_count=0,
            pattern_day_trader=False,
            day_trading_buying_power=100000.0
        )
        self.order_counter = 0
    
    async def place_order(
        self,
        symbol: str,
        side: OrderSide,
        quantity: int,
        order_type: OrderType,
        limit_price: Optional[float] = None,
        stop_price: Optional[float] = None,
        time_in_force: TimeInForce = TimeInForce.DAY,
        client_order_id: Optional[str] = None,
        bracket_orders: Optional[Dict] = None
    ) -> Order:
        """Place a mock order"""
        self.order_counter += 1
        order_id = f"mock_order_{self.order_counter}"
        
        order = Order(
            id=order_id,
            symbol=symbol,
            side=side,
            type=order_type,
            quantity=quantity,
            status=OrderStatus.NEW,
            filled_quantity=0,
            remaining_quantity=quantity,
            limit_price=limit_price,
            stop_price=stop_price,
            time_in_force=time_in_force,
            created_at=datetime.now(),
            client_order_id=client_order_id
        )
        
        self.orders[order_id] = order
        
        # Simulate immediate fill for market orders
        if order_type == OrderType.MARKET:
            order.status = OrderStatus.FILLED
            order.filled_quantity = quantity
            order.remaining_quantity = 0
            order.average_fill_price = 100.0  # Mock price
            order.updated_at = datetime.now()
        
        return order
    
    async def cancel_order(self, order_id: str) -> Dict[str, str]:
        """Cancel a mock order"""
        if order_id in self.orders:
            self.orders[order_id].status = OrderStatus.CANCELED
            self.orders[order_id].updated_at = datetime.now()
            return {"status": "success", "message": "Order canceled"}
        return {"status": "error", "message": "Order not found"}
    
    async def get_order(self, order_id: str) -> Order:
        """Get mock order details"""
        return self.orders.get(order_id)
    
    async def get_orders(self, status: Optional[OrderStatus] = None) -> List[Order]:
        """Get all mock orders"""
        orders = list(self.orders.values())
        if status:
            orders = [o for o in orders if o.status == status]
        return orders
    
    async def get_positions(self) -> List[Position]:
        """Get all mock positions"""
        return list(self.positions.values())
    
    async def get_position(self, symbol: str) -> Optional[Position]:
        """Get mock position for symbol"""
        return self.positions.get(symbol)
    
    async def get_account(self) -> Account:
        """Get mock account information"""
        return self.account
    
    async def get_market_data(self, symbols: List[str]) -> Dict[str, Dict]:
        """Get mock market data"""
        import random
        data = {}
        for symbol in symbols:
            base_price = 100 + hash(symbol) % 500
            change = random.uniform(-5, 5)
            data[symbol] = {
                "price": base_price + change,
                "bid": base_price + change - 0.01,
                "ask": base_price + change + 0.01,
                "volume": random.randint(1000000, 10000000),
                "timestamp": datetime.now().isoformat()
            }
        return data


# Factory function for easy broker creation
def create_broker(broker_type: str, **kwargs) -> Broker:
    """Create broker instance"""
    if broker_type == "mock":
        return MockBroker()
    elif broker_type == "alpaca_paper":
        from .alpaca_paper import AlpacaPaperBroker
        return AlpacaPaperBroker(**kwargs)
    else:
        raise ValueError(f"Unknown broker type: {broker_type}")
