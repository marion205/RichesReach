"""
Mock Brokerage Adapter
Mock implementation for testing and development
"""

import asyncio
import logging
import random
import uuid
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta

from .enhanced_base import (
    BrokerageAdapter, Order, Position, Account, Trade,
    OrderSide, OrderType, OrderStatus, TimeInForce
)


class MockBrokerageAdapter(BrokerageAdapter):
    """Mock brokerage adapter for testing and development"""
    
    def __init__(self, api_key: str = "mock_key", api_secret: str = "mock_secret", **kwargs):
        super().__init__(api_key, api_secret, **kwargs)
        self.logger = logging.getLogger(__name__)
        
        # Mock data storage
        self.mock_orders = {}
        self.mock_positions = {}
        self.mock_account = self._create_mock_account()
        self.mock_trades = []
        
        # Mock symbols and prices
        self.mock_symbols = {
            "AAPL": {"price": 150.0, "bid": 149.95, "ask": 150.05},
            "MSFT": {"price": 300.0, "bid": 299.95, "ask": 300.05},
            "GOOGL": {"price": 2500.0, "bid": 2499.95, "ask": 2500.05},
            "TSLA": {"price": 200.0, "bid": 199.95, "ask": 200.05},
            "NVDA": {"price": 400.0, "bid": 399.95, "ask": 400.05},
            "META": {"price": 350.0, "bid": 349.95, "ask": 350.05},
            "AMZN": {"price": 3200.0, "bid": 3199.95, "ask": 3200.05},
            "NFLX": {"price": 450.0, "bid": 449.95, "ask": 450.05}
        }
        
        self.logger.info("Mock brokerage adapter initialized")
    
    def _create_mock_account(self) -> Account:
        """Create mock account data"""
        return Account(
            account_id="mock_account_123",
            account_type="margin",
            cash=100000.0,
            buying_power=200000.0,
            portfolio_value=100000.0,
            equity=100000.0,
            day_trade_count=0,
            pattern_day_trader=False,
            day_trading_buying_power=400000.0,
            margin_equity=100000.0,
            margin_used=0.0,
            margin_available=200000.0,
            last_equity=100000.0,
            last_equity_change=0.0,
            last_equity_change_percent=0.0
        )
    
    def _simulate_price_movement(self, symbol: str) -> float:
        """Simulate price movement for a symbol"""
        if symbol not in self.mock_symbols:
            return 100.0
        
        current_price = self.mock_symbols[symbol]["price"]
        # Random walk with slight upward bias
        change_percent = random.uniform(-0.02, 0.03)  # -2% to +3%
        new_price = current_price * (1 + change_percent)
        
        # Update mock data
        self.mock_symbols[symbol]["price"] = new_price
        self.mock_symbols[symbol]["bid"] = new_price - 0.05
        self.mock_symbols[symbol]["ask"] = new_price + 0.05
        
        return new_price
    
    async def place_order(self, order: Order) -> Order:
        """Place a mock order"""
        
        # Validate order
        errors = self._validate_order(order)
        if errors:
            raise ValueError(f"Order validation failed: {', '.join(errors)}")
        
        # Generate order ID if not provided
        if not order.id:
            order.id = str(uuid.uuid4())
        
        # Set client order ID if not provided
        if not order.client_order_id:
            order.client_order_id = self._generate_client_order_id()
        
        # Simulate order processing
        await asyncio.sleep(0.1)  # Simulate network delay
        
        # Determine fill price
        if order.order_type == OrderType.MARKET:
            fill_price = self.mock_symbols.get(order.symbol, {}).get("price", 100.0)
        elif order.order_type == OrderType.LIMIT:
            fill_price = order.price
        else:
            fill_price = order.price or self.mock_symbols.get(order.symbol, {}).get("price", 100.0)
        
        # Simulate order execution (90% success rate)
        if random.random() < 0.9:
            order.status = OrderStatus.FILLED
            order.filled_quantity = order.quantity
            order.filled_avg_price = fill_price
            order.filled_at = datetime.now()
            
            # Create trade record
            trade = Trade(
                id=str(uuid.uuid4()),
                order_id=order.id,
                symbol=order.symbol,
                side=order.side,
                quantity=order.quantity,
                price=fill_price,
                timestamp=datetime.now(),
                commission=0.0,
                fees=0.0
            )
            self.mock_trades.append(trade)
            
            # Update position
            await self._update_position(order, fill_price)
            
            self.logger.info(f"Mock order filled: {order.id} - {order.symbol} {order.side.value} {order.quantity} @ {fill_price}")
        else:
            order.status = OrderStatus.REJECTED
            self.logger.warning(f"Mock order rejected: {order.id}")
        
        # Store order
        self.mock_orders[order.id] = order
        
        return order
    
    async def _update_position(self, order: Order, fill_price: float):
        """Update position after order fill"""
        symbol = order.symbol
        
        if symbol not in self.mock_positions:
            self.mock_positions[symbol] = Position(
                symbol=symbol,
                quantity=0,
                side=OrderSide.LONG,
                average_price=0.0,
                current_price=fill_price,
                market_value=0.0,
                unrealized_pnl=0.0,
                unrealized_pnl_percent=0.0,
                realized_pnl=0.0
            )
        
        position = self.mock_positions[symbol]
        
        # Calculate new position
        if order.side in [OrderSide.BUY, OrderSide.LONG]:
            # Adding to long position or closing short
            if position.quantity >= 0:
                # Adding to long position
                total_cost = (position.quantity * position.average_price) + (order.quantity * fill_price)
                total_quantity = position.quantity + order.quantity
                position.average_price = total_cost / total_quantity if total_quantity > 0 else 0.0
                position.quantity = total_quantity
                position.side = OrderSide.LONG
            else:
                # Closing short position
                if order.quantity <= abs(position.quantity):
                    # Partial close
                    position.quantity += order.quantity
                    if position.quantity == 0:
                        position.average_price = 0.0
                else:
                    # Over-close, creating long position
                    remaining_quantity = order.quantity - abs(position.quantity)
                    position.average_price = fill_price
                    position.quantity = remaining_quantity
                    position.side = OrderSide.LONG
        
        else:  # SELL or SHORT
            if position.quantity <= 0:
                # Adding to short position
                total_cost = (abs(position.quantity) * position.average_price) + (order.quantity * fill_price)
                total_quantity = abs(position.quantity) + order.quantity
                position.average_price = total_cost / total_quantity if total_quantity > 0 else 0.0
                position.quantity = -total_quantity
                position.side = OrderSide.SHORT
            else:
                # Closing long position
                if order.quantity <= position.quantity:
                    # Partial close
                    position.quantity -= order.quantity
                    if position.quantity == 0:
                        position.average_price = 0.0
                else:
                    # Over-close, creating short position
                    remaining_quantity = order.quantity - position.quantity
                    position.average_price = fill_price
                    position.quantity = -remaining_quantity
                    position.side = OrderSide.SHORT
        
        # Update current price and recalculate PnL
        position.current_price = fill_price
        position.__post_init__()  # Recalculate derived fields
        
        # Remove position if quantity is zero
        if position.quantity == 0:
            del self.mock_positions[symbol]
    
    async def cancel_order(self, order_id: str) -> bool:
        """Cancel a mock order"""
        if order_id in self.mock_orders:
            order = self.mock_orders[order_id]
            if order.status in [OrderStatus.PENDING, OrderStatus.ACCEPTED]:
                order.status = OrderStatus.CANCELED
                order.updated_at = datetime.now()
                self.logger.info(f"Mock order canceled: {order_id}")
                return True
        
        return False
    
    async def modify_order(self, order_id: str, **kwargs) -> Order:
        """Modify a mock order"""
        if order_id not in self.mock_orders:
            raise ValueError(f"Order {order_id} not found")
        
        order = self.mock_orders[order_id]
        
        # Update order fields
        for key, value in kwargs.items():
            if hasattr(order, key):
                setattr(order, key, value)
        
        order.updated_at = datetime.now()
        
        self.logger.info(f"Mock order modified: {order_id}")
        return order
    
    async def get_order(self, order_id: str) -> Optional[Order]:
        """Get mock order details"""
        return self.mock_orders.get(order_id)
    
    async def get_orders(
        self, 
        status: Optional[OrderStatus] = None,
        symbol: Optional[str] = None,
        limit: int = 100
    ) -> List[Order]:
        """Get mock orders"""
        orders = list(self.mock_orders.values())
        
        # Filter by status
        if status:
            orders = [order for order in orders if order.status == status]
        
        # Filter by symbol
        if symbol:
            orders = [order for order in orders if order.symbol == symbol]
        
        # Sort by created_at descending
        orders.sort(key=lambda x: x.created_at, reverse=True)
        
        return orders[:limit]
    
    async def get_positions(self) -> List[Position]:
        """Get mock positions"""
        # Update current prices
        for symbol, position in self.mock_positions.items():
            position.current_price = self._simulate_price_movement(symbol)
            position.__post_init__()  # Recalculate PnL
        
        return list(self.mock_positions.values())
    
    async def get_position(self, symbol: str) -> Optional[Position]:
        """Get mock position for symbol"""
        if symbol in self.mock_positions:
            position = self.mock_positions[symbol]
            position.current_price = self._simulate_price_movement(symbol)
            position.__post_init__()
            return position
        
        return None
    
    async def get_account(self) -> Account:
        """Get mock account information"""
        # Update account based on positions
        positions = await self.get_positions()
        
        total_market_value = sum(pos.market_value for pos in positions)
        total_unrealized_pnl = sum(pos.unrealized_pnl for pos in positions)
        
        self.mock_account.portfolio_value = self.mock_account.cash + total_market_value
        self.mock_account.equity = self.mock_account.cash + total_market_value
        
        # Update buying power
        self.mock_account.buying_power = self.mock_account.cash * 2  # 2x leverage
        
        return self.mock_account
    
    async def get_trades(
        self, 
        symbol: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 100
    ) -> List[Trade]:
        """Get mock trade history"""
        trades = self.mock_trades.copy()
        
        # Filter by symbol
        if symbol:
            trades = [trade for trade in trades if trade.symbol == symbol]
        
        # Filter by date range
        if start_date:
            trades = [trade for trade in trades if trade.timestamp >= start_date]
        
        if end_date:
            trades = [trade for trade in trades if trade.timestamp <= end_date]
        
        # Sort by timestamp descending
        trades.sort(key=lambda x: x.timestamp, reverse=True)
        
        return trades[:limit]
    
    async def get_quotes(self, symbols: List[str]) -> Dict[str, Dict[str, Any]]:
        """Get mock quotes"""
        quotes = {}
        
        for symbol in symbols:
            if symbol in self.mock_symbols:
                data = self.mock_symbols[symbol]
                quotes[symbol] = {
                    "symbol": symbol,
                    "price": data["price"],
                    "bid": data["bid"],
                    "ask": data["ask"],
                    "size": random.randint(100, 1000),
                    "timestamp": datetime.now().isoformat()
                }
        
        return quotes
    
    async def get_market_status(self) -> Dict[str, Any]:
        """Get mock market status"""
        now = datetime.now()
        hour = now.hour
        
        # Simple market hours simulation
        market_open = 9 <= hour < 16  # 9 AM to 4 PM
        
        return {
            "market_open": market_open,
            "next_open": (now + timedelta(hours=1)).isoformat() if not market_open else None,
            "next_close": (now + timedelta(hours=1)).isoformat() if market_open else None,
            "current_time": now.isoformat(),
            "timezone": "US/Eastern"
        }
    
    async def simulate_market_movement(self):
        """Simulate market movement for all symbols"""
        for symbol in self.mock_symbols:
            self._simulate_price_movement(symbol)
        
        # Update positions
        await self.get_positions()
    
    async def cleanup(self):
        """Cleanup mock resources"""
        await super().cleanup()
        self.mock_orders.clear()
        self.mock_positions.clear()
        self.mock_trades.clear()
        self.logger.info("Mock brokerage adapter cleanup completed")
