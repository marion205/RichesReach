"""
Enhanced Brokerage Adapter Interface
Comprehensive interface for brokerage integrations with advanced order types
"""

import asyncio
import logging
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any, Union
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
import uuid


class OrderSide(Enum):
    """Order side enumeration"""
    BUY = "BUY"
    SELL = "SELL"
    LONG = "LONG"
    SHORT = "SHORT"


class OrderType(Enum):
    """Order type enumeration"""
    MARKET = "MARKET"
    LIMIT = "LIMIT"
    STOP = "STOP"
    STOP_LIMIT = "STOP_LIMIT"
    BRACKET = "BRACKET"
    OCO = "OCO"  # One-Cancels-Other
    ICEBERG = "ICEBERG"
    TRAILING_STOP = "TRAILING_STOP"
    TWAP = "TWAP"  # Time-Weighted Average Price
    VWAP = "VWAP"  # Volume-Weighted Average Price


class OrderStatus(Enum):
    """Order status enumeration"""
    PENDING = "PENDING"
    SUBMITTED = "SUBMITTED"
    ACCEPTED = "ACCEPTED"
    PARTIALLY_FILLED = "PARTIALLY_FILLED"
    FILLED = "FILLED"
    CANCELED = "CANCELED"
    REJECTED = "REJECTED"
    EXPIRED = "EXPIRED"


class TimeInForce(Enum):
    """Time in force enumeration"""
    DAY = "DAY"
    GTC = "GTC"  # Good Till Canceled
    IOC = "IOC"  # Immediate or Cancel
    FOK = "FOK"  # Fill or Kill


@dataclass
class Order:
    """Order data structure"""
    id: str
    client_order_id: Optional[str] = None
    symbol: str = ""
    side: OrderSide = OrderSide.BUY
    order_type: OrderType = OrderType.MARKET
    quantity: int = 0
    price: Optional[float] = None
    stop_price: Optional[float] = None
    time_in_force: TimeInForce = TimeInForce.DAY
    
    # Order status
    status: OrderStatus = OrderStatus.PENDING
    filled_quantity: int = 0
    filled_avg_price: Optional[float] = None
    remaining_quantity: int = 0
    
    # Timestamps
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    filled_at: Optional[datetime] = None
    
    # Advanced order fields
    take_profit_price: Optional[float] = None
    stop_loss_price: Optional[float] = None
    trailing_stop_percent: Optional[float] = None
    iceberg_display_size: Optional[int] = None
    
    # Metadata
    tags: List[str] = field(default_factory=list)
    notes: Optional[str] = None
    
    def __post_init__(self):
        """Calculate derived fields"""
        self.remaining_quantity = self.quantity - self.filled_quantity


@dataclass
class Position:
    """Position data structure"""
    symbol: str
    quantity: int
    side: OrderSide
    average_price: float
    current_price: float
    market_value: float
    unrealized_pnl: float
    unrealized_pnl_percent: float
    realized_pnl: float = 0.0
    
    # Additional fields
    cost_basis: float = 0.0
    day_pnl: float = 0.0
    day_pnl_percent: float = 0.0
    total_pnl: float = 0.0
    
    def __post_init__(self):
        """Calculate derived fields"""
        self.market_value = abs(self.quantity) * self.current_price
        self.cost_basis = abs(self.quantity) * self.average_price
        
        if self.quantity > 0:  # Long position
            self.unrealized_pnl = (self.current_price - self.average_price) * self.quantity
        else:  # Short position
            self.unrealized_pnl = (self.average_price - self.current_price) * abs(self.quantity)
        
        if self.cost_basis > 0:
            self.unrealized_pnl_percent = (self.unrealized_pnl / self.cost_basis) * 100
        
        self.total_pnl = self.unrealized_pnl + self.realized_pnl


@dataclass
class Account:
    """Account data structure"""
    account_id: str
    account_type: str  # "cash", "margin", "day_trading"
    
    # Balances
    cash: float = 0.0
    buying_power: float = 0.0
    portfolio_value: float = 0.0
    equity: float = 0.0
    
    # Day trading
    day_trade_count: int = 0
    pattern_day_trader: bool = False
    day_trading_buying_power: float = 0.0
    
    # Margin
    margin_equity: float = 0.0
    margin_used: float = 0.0
    margin_available: float = 0.0
    
    # Additional fields
    last_equity: float = 0.0
    last_equity_change: float = 0.0
    last_equity_change_percent: float = 0.0
    
    def __post_init__(self):
        """Calculate derived fields"""
        self.last_equity_change = self.equity - self.last_equity
        if self.last_equity > 0:
            self.last_equity_change_percent = (self.last_equity_change / self.last_equity) * 100


@dataclass
class Trade:
    """Trade execution data structure"""
    id: str
    order_id: str
    symbol: str
    side: OrderSide
    quantity: int
    price: float
    timestamp: datetime
    commission: float = 0.0
    fees: float = 0.0
    
    # Additional fields
    venue: Optional[str] = None
    liquidity: Optional[str] = None  # "maker" or "taker"


class BrokerageAdapter(ABC):
    """Abstract base class for brokerage adapters"""
    
    def __init__(self, api_key: str, api_secret: str, base_url: Optional[str] = None, paper: bool = True):
        self.api_key = api_key
        self.api_secret = api_secret
        self.base_url = base_url
        self.paper = paper
        self.logger = logging.getLogger(self.__class__.__name__)
        self.active_orders = {}
        self.positions_cache = {}
        self.account_cache = None
        self.last_cache_update = None
    
    @abstractmethod
    async def place_order(self, order: Order) -> Order:
        """Place an order"""
        pass
    
    @abstractmethod
    async def cancel_order(self, order_id: str) -> bool:
        """Cancel an order"""
        pass
    
    @abstractmethod
    async def modify_order(self, order_id: str, **kwargs) -> Order:
        """Modify an existing order"""
        pass
    
    @abstractmethod
    async def get_order(self, order_id: str) -> Optional[Order]:
        """Get order details"""
        pass
    
    @abstractmethod
    async def get_orders(
        self, 
        status: Optional[OrderStatus] = None,
        symbol: Optional[str] = None,
        limit: int = 100
    ) -> List[Order]:
        """Get list of orders"""
        pass
    
    @abstractmethod
    async def get_positions(self) -> List[Position]:
        """Get current positions"""
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
    async def get_trades(
        self, 
        symbol: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 100
    ) -> List[Trade]:
        """Get trade history"""
        pass
    
    # Advanced order methods
    async def place_bracket_order(
        self,
        symbol: str,
        side: OrderSide,
        quantity: int,
        entry_price: Optional[float] = None,
        take_profit_price: Optional[float] = None,
        stop_loss_price: Optional[float] = None,
        time_in_force: TimeInForce = TimeInForce.DAY
    ) -> List[Order]:
        """Place a bracket order (entry + take profit + stop loss)"""
        
        orders = []
        
        # Entry order
        entry_order = Order(
            id=str(uuid.uuid4()),
            symbol=symbol,
            side=side,
            order_type=OrderType.LIMIT if entry_price else OrderType.MARKET,
            quantity=quantity,
            price=entry_price,
            time_in_force=time_in_force,
            order_type=OrderType.BRACKET
        )
        
        entry_order = await self.place_order(entry_order)
        orders.append(entry_order)
        
        # Take profit order
        if take_profit_price:
            tp_side = OrderSide.SELL if side == OrderSide.BUY else OrderSide.BUY
            tp_order = Order(
                id=str(uuid.uuid4()),
                symbol=symbol,
                side=tp_side,
                order_type=OrderType.LIMIT,
                quantity=quantity,
                price=take_profit_price,
                time_in_force=TimeInForce.GTC,
                tags=["bracket_tp", entry_order.id]
            )
            tp_order = await self.place_order(tp_order)
            orders.append(tp_order)
        
        # Stop loss order
        if stop_loss_price:
            sl_side = OrderSide.SELL if side == OrderSide.BUY else OrderSide.BUY
            sl_order = Order(
                id=str(uuid.uuid4()),
                symbol=symbol,
                side=sl_side,
                order_type=OrderType.STOP,
                quantity=quantity,
                stop_price=stop_loss_price,
                time_in_force=TimeInForce.GTC,
                tags=["bracket_sl", entry_order.id]
            )
            sl_order = await self.place_order(sl_order)
            orders.append(sl_order)
        
        return orders
    
    async def place_oco_order(
        self,
        symbol: str,
        side: OrderSide,
        quantity: int,
        limit_price: float,
        stop_price: float,
        time_in_force: TimeInForce = TimeInForce.DAY
    ) -> List[Order]:
        """Place an OCO (One-Cancels-Other) order"""
        
        orders = []
        oco_id = str(uuid.uuid4())
        
        # Limit order
        limit_order = Order(
            id=str(uuid.uuid4()),
            symbol=symbol,
            side=side,
            order_type=OrderType.LIMIT,
            quantity=quantity,
            price=limit_price,
            time_in_force=time_in_force,
            tags=["oco", oco_id]
        )
        limit_order = await self.place_order(limit_order)
        orders.append(limit_order)
        
        # Stop order
        stop_order = Order(
            id=str(uuid.uuid4()),
            symbol=symbol,
            side=side,
            order_type=OrderType.STOP,
            quantity=quantity,
            stop_price=stop_price,
            time_in_force=time_in_force,
            tags=["oco", oco_id]
        )
        stop_order = await self.place_order(stop_order)
        orders.append(stop_order)
        
        return orders
    
    async def place_trailing_stop_order(
        self,
        symbol: str,
        side: OrderSide,
        quantity: int,
        trailing_percent: float,
        time_in_force: TimeInForce = TimeInForce.GTC
    ) -> Order:
        """Place a trailing stop order"""
        
        trailing_order = Order(
            id=str(uuid.uuid4()),
            symbol=symbol,
            side=side,
            order_type=OrderType.TRAILING_STOP,
            quantity=quantity,
            trailing_stop_percent=trailing_percent,
            time_in_force=time_in_force
        )
        
        return await self.place_order(trailing_order)
    
    async def place_iceberg_order(
        self,
        symbol: str,
        side: OrderSide,
        total_quantity: int,
        display_size: int,
        price: Optional[float] = None,
        time_in_force: TimeInForce = TimeInForce.DAY
    ) -> Order:
        """Place an iceberg order"""
        
        iceberg_order = Order(
            id=str(uuid.uuid4()),
            symbol=symbol,
            side=side,
            order_type=OrderType.ICEBERG,
            quantity=total_quantity,
            price=price,
            iceberg_display_size=display_size,
            time_in_force=time_in_force
        )
        
        return await self.place_order(iceberg_order)
    
    # Utility methods
    def _generate_client_order_id(self, prefix: str = "RR") -> str:
        """Generate unique client order ID"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        random_suffix = str(uuid.uuid4())[:8]
        return f"{prefix}_{timestamp}_{random_suffix}"
    
    def _validate_order(self, order: Order) -> List[str]:
        """Validate order parameters"""
        errors = []
        
        if not order.symbol:
            errors.append("Symbol is required")
        
        if order.quantity <= 0:
            errors.append("Quantity must be positive")
        
        if order.order_type in [OrderType.LIMIT, OrderType.STOP_LIMIT] and not order.price:
            errors.append("Price is required for limit orders")
        
        if order.order_type in [OrderType.STOP, OrderType.STOP_LIMIT] and not order.stop_price:
            errors.append("Stop price is required for stop orders")
        
        if order.order_type == OrderType.BRACKET:
            if not order.take_profit_price and not order.stop_loss_price:
                errors.append("Bracket orders require take profit or stop loss price")
        
        return errors
    
    async def _cache_positions(self, force_refresh: bool = False):
        """Cache positions data"""
        if (not force_refresh and 
            self.positions_cache and 
            self.last_cache_update and 
            datetime.now() - self.last_cache_update < timedelta(seconds=30)):
            return
        
        try:
            self.positions_cache = await self.get_positions()
            self.last_cache_update = datetime.now()
        except Exception as e:
            self.logger.error(f"Failed to cache positions: {e}")
    
    async def _cache_account(self, force_refresh: bool = False):
        """Cache account data"""
        if (not force_refresh and 
            self.account_cache and 
            self.last_cache_update and 
            datetime.now() - self.last_cache_update < timedelta(seconds=30)):
            return
        
        try:
            self.account_cache = await self.get_account()
            self.last_cache_update = datetime.now()
        except Exception as e:
            self.logger.error(f"Failed to cache account: {e}")
    
    async def get_cached_positions(self) -> List[Position]:
        """Get cached positions"""
        await self._cache_positions()
        return self.positions_cache or []
    
    async def get_cached_account(self) -> Optional[Account]:
        """Get cached account"""
        await self._cache_account()
        return self.account_cache
    
    async def calculate_position_size(
        self,
        symbol: str,
        risk_amount: float,
        entry_price: float,
        stop_loss_price: float
    ) -> int:
        """Calculate position size based on risk"""
        
        if stop_loss_price <= 0 or entry_price <= 0:
            return 0
        
        risk_per_share = abs(entry_price - stop_loss_price)
        if risk_per_share <= 0:
            return 0
        
        position_size = int(risk_amount / risk_per_share)
        
        # Ensure we don't exceed buying power
        account = await self.get_cached_account()
        if account and account.buying_power > 0:
            max_shares = int(account.buying_power / entry_price)
            position_size = min(position_size, max_shares)
        
        return max(0, position_size)
    
    async def get_portfolio_summary(self) -> Dict[str, Any]:
        """Get portfolio summary"""
        account = await self.get_cached_account()
        positions = await self.get_cached_positions()
        
        total_market_value = sum(pos.market_value for pos in positions)
        total_unrealized_pnl = sum(pos.unrealized_pnl for pos in positions)
        total_realized_pnl = sum(pos.realized_pnl for pos in positions)
        
        return {
            "account": account,
            "positions": positions,
            "total_market_value": total_market_value,
            "total_unrealized_pnl": total_unrealized_pnl,
            "total_realized_pnl": total_realized_pnl,
            "total_pnl": total_unrealized_pnl + total_realized_pnl,
            "position_count": len(positions),
            "last_updated": self.last_cache_update
        }
    
    async def cleanup(self):
        """Cleanup resources"""
        self.positions_cache = None
        self.account_cache = None
        self.active_orders.clear()
        self.logger.info(f"{self.__class__.__name__} cleanup completed")


# Factory function
def create_brokerage_adapter(
    broker_type: str, 
    api_key: str, 
    api_secret: str, 
    **kwargs
) -> BrokerageAdapter:
    """Create brokerage adapter instance"""
    
    if broker_type.lower() == "alpaca":
        from .alpaca_adapter import AlpacaAdapter
        return AlpacaAdapter(api_key, api_secret, **kwargs)
    elif broker_type.lower() == "mock":
        from .mock_adapter import MockBrokerageAdapter
        return MockBrokerageAdapter(api_key, api_secret, **kwargs)
    else:
        raise ValueError(f"Unknown broker type: {broker_type}")
