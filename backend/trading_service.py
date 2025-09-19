"""
RichesReach Trading Service
Handles real brokerage integration with Alpaca API
"""

import os
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum

import requests
import pandas as pd
from alpaca.trading.client import TradingClient
from alpaca.trading.requests import MarketOrderRequest, LimitOrderRequest, StopLossRequest
from alpaca.trading.enums import OrderSide as AlpacaOrderSide, TimeInForce, OrderType as AlpacaOrderType, OrderStatus as AlpacaOrderStatus
from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import StockBarsRequest
from alpaca.data.timeframe import TimeFrame

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class OrderType(Enum):
    MARKET = "market"
    LIMIT = "limit"
    STOP_LOSS = "stop_loss"
    STOP_LIMIT = "stop_limit"

class OrderSide(Enum):
    BUY = "buy"
    SELL = "sell"

class OrderStatus(Enum):
    PENDING = "pending"
    FILLED = "filled"
    PARTIALLY_FILLED = "partially_filled"
    CANCELLED = "cancelled"
    REJECTED = "rejected"

@dataclass
class Order:
    id: str
    symbol: str
    side: OrderSide
    order_type: OrderType
    quantity: int
    price: Optional[float] = None
    stop_price: Optional[float] = None
    status: OrderStatus = OrderStatus.PENDING
    created_at: datetime = None
    filled_at: Optional[datetime] = None
    filled_quantity: int = 0
    average_fill_price: Optional[float] = None
    commission: float = 0.0
    notes: Optional[str] = None

@dataclass
class Account:
    id: str
    buying_power: float
    cash: float
    portfolio_value: float
    equity: float
    day_trade_count: int
    pattern_day_trader: bool
    trading_blocked: bool
    created_at: datetime

@dataclass
class Position:
    symbol: str
    quantity: int
    market_value: float
    cost_basis: float
    unrealized_pl: float
    unrealized_plpc: float
    current_price: float
    side: str = "long"

class TradingService:
    """Main trading service for RichesReach"""
    
    def __init__(self):
        self.api_key = os.getenv('ALPACA_API_KEY')
        self.secret_key = os.getenv('ALPACA_SECRET_KEY')
        self.base_url = os.getenv('ALPACA_BASE_URL', 'https://paper-api.alpaca.markets')
        self.data_url = os.getenv('ALPACA_DATA_URL', 'https://data.alpaca.markets')
        
        # Initialize clients
        self.trading_client = None
        self.data_client = None
        self._initialize_clients()
        
        # Cache for account data
        self._account_cache = None
        self._positions_cache = None
        self._cache_expiry = None
        
    def _initialize_clients(self):
        """Initialize Alpaca API clients"""
        try:
            if self.api_key and self.secret_key:
                self.trading_client = TradingClient(
                    api_key=self.api_key,
                    secret_key=self.secret_key,
                    paper=True  # Use paper trading for safety
                )
                self.data_client = StockHistoricalDataClient(
                    api_key=self.api_key,
                    secret_key=self.secret_key
                )
                logger.info("✅ Alpaca trading clients initialized successfully")
            else:
                logger.warning("⚠️ Alpaca API keys not found, using mock mode")
                self.trading_client = None
                self.data_client = None
        except Exception as e:
            logger.error(f"❌ Failed to initialize Alpaca clients: {e}")
            self.trading_client = None
            self.data_client = None
    
    async def get_account(self) -> Optional[Account]:
        """Get account information"""
        try:
            if not self.trading_client:
                return self._get_mock_account()
            
            # Check cache first
            if self._account_cache and self._cache_expiry and datetime.now() < self._cache_expiry:
                return self._account_cache
            
            account = self.trading_client.get_account()
            
            account_data = Account(
                id=account.id,
                buying_power=float(account.buying_power),
                cash=float(account.cash),
                portfolio_value=float(account.portfolio_value),
                equity=float(account.equity),
                day_trade_count=account.day_trade_count,
                pattern_day_trader=account.pattern_day_trader,
                trading_blocked=account.trading_blocked,
                created_at=account.created_at
            )
            
            # Cache for 30 seconds
            self._account_cache = account_data
            self._cache_expiry = datetime.now() + timedelta(seconds=30)
            
            return account_data
            
        except Exception as e:
            logger.error(f"❌ Failed to get account: {e}")
            return self._get_mock_account()
    
    async def get_positions(self) -> List[Position]:
        """Get current positions"""
        try:
            if not self.trading_client:
                return self._get_mock_positions()
            
            # Check cache first
            if self._positions_cache and self._cache_expiry and datetime.now() < self._cache_expiry:
                return self._positions_cache
            
            positions = self.trading_client.get_all_positions()
            
            position_list = []
            for pos in positions:
                position_data = Position(
                    symbol=pos.symbol,
                    quantity=int(pos.qty),
                    market_value=float(pos.market_value),
                    cost_basis=float(pos.cost_basis),
                    unrealized_pl=float(pos.unrealized_pl),
                    unrealized_plpc=float(pos.unrealized_plpc),
                    current_price=float(pos.current_price),
                    side=pos.side
                )
                position_list.append(position_data)
            
            # Cache for 30 seconds
            self._positions_cache = position_list
            self._cache_expiry = datetime.now() + timedelta(seconds=30)
            
            return position_list
            
        except Exception as e:
            logger.error(f"❌ Failed to get positions: {e}")
            return self._get_mock_positions()
    
    async def place_market_order(self, symbol: str, quantity: int, side: str, notes: str = None) -> Optional[Order]:
        """Place a market order"""
        try:
            if not self.trading_client:
                return self._create_mock_order(symbol, quantity, side, OrderType.MARKET)
            
            # Validate order
            if not await self._validate_order(symbol, quantity, side):
                return None
            
            # Create order request
            order_side = AlpacaOrderSide.BUY if side.lower() == 'buy' else AlpacaOrderSide.SELL
            order_request = MarketOrderRequest(
                symbol=symbol,
                qty=quantity,
                side=order_side,
                time_in_force=TimeInForce.DAY
            )
            
            # Submit order
            submitted_order = self.trading_client.submit_order(order_request)
            
            # Create order object
            order = Order(
                id=submitted_order.id,
                symbol=symbol,
                side=OrderSide(side.lower()),
                order_type=OrderType.MARKET,
                quantity=quantity,
                status=OrderStatus(submitted_order.status.value),
                created_at=submitted_order.created_at,
                notes=notes
            )
            
            logger.info(f"✅ Market order placed: {side} {quantity} {symbol}")
            return order
            
        except Exception as e:
            logger.error(f"❌ Failed to place market order: {e}")
            return None
    
    async def place_limit_order(self, symbol: str, quantity: int, side: str, limit_price: float, notes: str = None) -> Optional[Order]:
        """Place a limit order"""
        try:
            if not self.trading_client:
                return self._create_mock_order(symbol, quantity, side, OrderType.LIMIT, limit_price)
            
            # Validate order
            if not await self._validate_order(symbol, quantity, side, limit_price):
                return None
            
            # Create order request
            order_side = AlpacaOrderSide.BUY if side.lower() == 'buy' else AlpacaOrderSide.SELL
            order_request = LimitOrderRequest(
                symbol=symbol,
                qty=quantity,
                side=order_side,
                time_in_force=TimeInForce.DAY,
                limit_price=limit_price
            )
            
            # Submit order
            submitted_order = self.trading_client.submit_order(order_request)
            
            # Create order object
            order = Order(
                id=submitted_order.id,
                symbol=symbol,
                side=OrderSide(side.lower()),
                order_type=OrderType.LIMIT,
                quantity=quantity,
                price=limit_price,
                status=OrderStatus(submitted_order.status.value),
                created_at=submitted_order.created_at,
                notes=notes
            )
            
            logger.info(f"✅ Limit order placed: {side} {quantity} {symbol} @ ${limit_price}")
            return order
            
        except Exception as e:
            logger.error(f"❌ Failed to place limit order: {e}")
            return None
    
    async def place_stop_loss_order(self, symbol: str, quantity: int, side: str, stop_price: float, notes: str = None) -> Optional[Order]:
        """Place a stop loss order"""
        try:
            if not self.trading_client:
                return self._create_mock_order(symbol, quantity, side, OrderType.STOP_LOSS, stop_price=stop_price)
            
            # Validate order
            if not await self._validate_order(symbol, quantity, side, stop_price):
                return None
            
            # Create order request
            order_side = AlpacaOrderSide.BUY if side.lower() == 'buy' else AlpacaOrderSide.SELL
            order_request = StopLossRequest(
                symbol=symbol,
                qty=quantity,
                side=order_side,
                time_in_force=TimeInForce.DAY,
                stop_price=stop_price
            )
            
            # Submit order
            submitted_order = self.trading_client.submit_order(order_request)
            
            # Create order object
            order = Order(
                id=submitted_order.id,
                symbol=symbol,
                side=OrderSide(side.lower()),
                order_type=OrderType.STOP_LOSS,
                quantity=quantity,
                stop_price=stop_price,
                status=OrderStatus(submitted_order.status.value),
                created_at=submitted_order.created_at,
                notes=notes
            )
            
            logger.info(f"✅ Stop loss order placed: {side} {quantity} {symbol} @ ${stop_price}")
            return order
            
        except Exception as e:
            logger.error(f"❌ Failed to place stop loss order: {e}")
            return None
    
    async def cancel_order(self, order_id: str) -> bool:
        """Cancel an order"""
        try:
            if not self.trading_client:
                logger.info(f"✅ Mock order {order_id} cancelled")
                return True
            
            self.trading_client.cancel_order_by_id(order_id)
            logger.info(f"✅ Order {order_id} cancelled")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to cancel order {order_id}: {e}")
            return False
    
    async def get_order_status(self, order_id: str) -> Optional[Order]:
        """Get order status"""
        try:
            if not self.trading_client:
                return self._get_mock_order_status(order_id)
            
            order = self.trading_client.get_order_by_id(order_id)
            
            return Order(
                id=order.id,
                symbol=order.symbol,
                side=OrderSide(order.side.value),
                order_type=OrderType(order.order_type.value),
                quantity=int(order.qty),
                price=float(order.limit_price) if order.limit_price else None,
                stop_price=float(order.stop_price) if order.stop_price else None,
                status=OrderStatus(order.status.value),
                created_at=order.created_at,
                filled_at=order.filled_at,
                filled_quantity=int(order.filled_qty),
                average_fill_price=float(order.filled_avg_price) if order.filled_avg_price else None,
                commission=float(order.commission) if order.commission else 0.0
            )
            
        except Exception as e:
            logger.error(f"❌ Failed to get order status: {e}")
            return None
    
    async def get_orders(self, status: str = None, limit: int = 50) -> List[Order]:
        """Get orders with optional status filter"""
        try:
            if not self.trading_client:
                return self._get_mock_orders(limit)
            
            # Get orders from Alpaca
            orders = self.trading_client.get_orders(
                status=status,
                limit=limit,
                direction='desc'
            )
            
            order_list = []
            for order in orders:
                order_data = Order(
                    id=order.id,
                    symbol=order.symbol,
                    side=OrderSide(order.side.value),
                    order_type=OrderType(order.order_type.value),
                    quantity=int(order.qty),
                    price=float(order.limit_price) if order.limit_price else None,
                    stop_price=float(order.stop_price) if order.stop_price else None,
                    status=OrderStatus(order.status.value),
                    created_at=order.created_at,
                    filled_at=order.filled_at,
                    filled_quantity=int(order.filled_qty),
                    average_fill_price=float(order.filled_avg_price) if order.filled_avg_price else None,
                    commission=float(order.commission) if order.commission else 0.0
                )
                order_list.append(order_data)
            
            return order_list
            
        except Exception as e:
            logger.error(f"❌ Failed to get orders: {e}")
            return self._get_mock_orders(limit)
    
    async def get_quote(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Get real-time quote for a symbol"""
        try:
            if not self.data_client:
                return self._get_mock_quote(symbol)
            
            # Get latest quote
            quote = self.data_client.get_latest_quote(symbol)
            
            return {
                'symbol': symbol,
                'bid': float(quote.bid_price),
                'ask': float(quote.ask_price),
                'bid_size': int(quote.bid_size),
                'ask_size': int(quote.ask_size),
                'timestamp': quote.timestamp
            }
            
        except Exception as e:
            logger.error(f"❌ Failed to get quote for {symbol}: {e}")
            return self._get_mock_quote(symbol)
    
    async def _validate_order(self, symbol: str, quantity: int, side: str, price: float = None) -> bool:
        """Validate order before submission"""
        try:
            # Get account info
            account = await self.get_account()
            if not account:
                return False
            
            # Check if trading is blocked
            if account.trading_blocked:
                logger.error("❌ Trading is blocked for this account")
                return False
            
            # Calculate order value
            if price:
                order_value = quantity * price
            else:
                # For market orders, use current price estimate
                quote = await self.get_quote(symbol)
                if not quote:
                    return False
                order_value = quantity * ((quote['bid'] + quote['ask']) / 2)
            
            # Check buying power for buy orders
            if side.lower() == 'buy' and order_value > account.buying_power:
                logger.error(f"❌ Insufficient buying power. Required: ${order_value:.2f}, Available: ${account.buying_power:.2f}")
                return False
            
            # Check position for sell orders
            if side.lower() == 'sell':
                positions = await self.get_positions()
                position = next((p for p in positions if p.symbol == symbol), None)
                if not position or position.quantity < quantity:
                    logger.error(f"❌ Insufficient shares to sell. Required: {quantity}, Available: {position.quantity if position else 0}")
                    return False
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Order validation failed: {e}")
            return False
    
    # Mock data methods for development/testing
    def _get_mock_account(self) -> Account:
        """Get mock account data"""
        return Account(
            id="mock-account-123",
            buying_power=10000.0,
            cash=10000.0,
            portfolio_value=40125.9,
            equity=40125.9,
            day_trade_count=0,
            pattern_day_trader=False,
            trading_blocked=False,
            created_at=datetime.now() - timedelta(days=30)
        )
    
    def _get_mock_positions(self) -> List[Position]:
        """Get mock positions data"""
        return [
            Position(
                symbol="AAPL",
                quantity=50,
                market_value=11894.0,
                cost_basis=7500.0,
                unrealized_pl=4394.0,
                unrealized_plpc=58.59,
                current_price=237.88
            ),
            Position(
                symbol="MSFT",
                quantity=30,
                market_value=15253.5,
                cost_basis=10000.0,
                unrealized_pl=5253.5,
                unrealized_plpc=52.54,
                current_price=508.45
            )
        ]
    
    def _create_mock_order(self, symbol: str, quantity: int, side: str, order_type: OrderType, price: float = None, stop_price: float = None) -> Order:
        """Create mock order"""
        return Order(
            id=f"mock-order-{datetime.now().timestamp()}",
            symbol=symbol,
            side=OrderSide(side.lower()),
            order_type=order_type,
            quantity=quantity,
            price=price,
            stop_price=stop_price,
            status=OrderStatus.PENDING,
            created_at=datetime.now(),
            notes="Mock order for development"
        )
    
    def _get_mock_order_status(self, order_id: str) -> Order:
        """Get mock order status"""
        return Order(
            id=order_id,
            symbol="AAPL",
            side=OrderSide.BUY,
            order_type=OrderType.MARKET,
            quantity=10,
            status=OrderStatus.FILLED,
            created_at=datetime.now() - timedelta(minutes=5),
            filled_at=datetime.now() - timedelta(minutes=4),
            filled_quantity=10,
            average_fill_price=237.88,
            commission=1.0
        )
    
    def _get_mock_orders(self, limit: int) -> List[Order]:
        """Get mock orders"""
        orders = []
        for i in range(min(limit, 5)):
            order = Order(
                id=f"mock-order-{i}",
                symbol=["AAPL", "MSFT", "GOOGL", "AMZN", "TSLA"][i % 5],
                side=OrderSide.BUY if i % 2 == 0 else OrderSide.SELL,
                order_type=OrderType.MARKET if i % 3 == 0 else OrderType.LIMIT,
                quantity=10 + i * 5,
                price=200.0 + i * 10 if i % 3 != 0 else None,
                status=OrderStatus.FILLED if i < 3 else OrderStatus.PENDING,
                created_at=datetime.now() - timedelta(hours=i),
                filled_at=datetime.now() - timedelta(hours=i-1) if i < 3 else None,
                filled_quantity=10 + i * 5 if i < 3 else 0,
                average_fill_price=200.0 + i * 10 if i < 3 else None,
                commission=1.0 + i * 0.5
            )
            orders.append(order)
        return orders
    
    def _get_mock_quote(self, symbol: str) -> Dict[str, Any]:
        """Get mock quote data"""
        base_prices = {
            "AAPL": 237.88,
            "MSFT": 508.45,
            "GOOGL": 252.03,
            "AMZN": 231.23,
            "TSLA": 416.85
        }
        
        base_price = base_prices.get(symbol, 100.0)
        spread = base_price * 0.001  # 0.1% spread
        
        return {
            'symbol': symbol,
            'bid': base_price - spread,
            'ask': base_price + spread,
            'bid_size': 1000,
            'ask_size': 1000,
            'timestamp': datetime.now()
        }

# Global trading service instance
trading_service = TradingService()
