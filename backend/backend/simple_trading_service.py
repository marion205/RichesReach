"""
Simplified Trading Service for RichesReach
Uses REST API calls instead of the alpaca-py library to avoid dependency conflicts
"""

import os
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum
import requests
import json

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
    id: str
    symbol: str
    quantity: int
    market_value: float
    cost_basis: float
    unrealized_pl: float
    unrealized_plpc: float
    current_price: float
    side: str = "long"

class SimpleTradingService:
    """Simplified trading service using REST API calls"""
    
    def __init__(self):
        self.api_key = os.getenv('ALPACA_API_KEY')
        self.secret_key = os.getenv('ALPACA_SECRET_KEY')
        self.base_url = os.getenv('ALPACA_BASE_URL', 'https://paper-api.alpaca.markets')
        
        # Headers for API requests
        self.headers = {
            'APCA-API-KEY-ID': self.api_key or '',
            'APCA-API-SECRET-KEY': self.secret_key or '',
            'Content-Type': 'application/json'
        }
        
        # Cache for account data
        self._account_cache = None
        self._positions_cache = None
        self._cache_expiry = None
        
        logger.info("✅ Simple Trading Service initialized")
    
    async def get_account(self) -> Optional[Account]:
        """Get account information"""
        try:
            if not self.api_key or not self.secret_key:
                return self._get_mock_account()
            
            # Check cache first
            if self._account_cache and self._cache_expiry and datetime.now() < self._cache_expiry:
                return self._account_cache
            
            response = requests.get(f"{self.base_url}/v2/account", headers=self.headers)
            response.raise_for_status()
            
            account_data = response.json()
            
            account = Account(
                id=account_data.get('id', ''),
                buying_power=float(account_data.get('buying_power', 0)),
                cash=float(account_data.get('cash', 0)),
                portfolio_value=float(account_data.get('portfolio_value', 0)),
                equity=float(account_data.get('equity', 0)),
                day_trade_count=account_data.get('day_trade_count', 0),
                pattern_day_trader=account_data.get('pattern_day_trader', False),
                trading_blocked=account_data.get('trading_blocked', False),
                created_at=datetime.fromisoformat(account_data.get('created_at', '').replace('Z', '+00:00'))
            )
            
            # Cache for 30 seconds
            self._account_cache = account
            self._cache_expiry = datetime.now() + timedelta(seconds=30)
            
            return account
            
        except Exception as e:
            logger.error(f"❌ Failed to get account: {e}")
            return self._get_mock_account()
    
    async def get_positions(self) -> List[Position]:
        """Get current positions"""
        try:
            if not self.api_key or not self.secret_key:
                return self._get_mock_positions()
            
            # Check cache first
            if self._positions_cache and self._cache_expiry and datetime.now() < self._cache_expiry:
                return self._positions_cache
            
            response = requests.get(f"{self.base_url}/v2/positions", headers=self.headers)
            response.raise_for_status()
            
            positions_data = response.json()
            
            position_list = []
            for pos in positions_data:
                position = Position(
                    id=pos.get('asset_id', f"pos_{pos.get('symbol', 'unknown')}"),
                    symbol=pos.get('symbol', ''),
                    quantity=int(pos.get('qty', 0)),
                    market_value=float(pos.get('market_value', 0)),
                    cost_basis=float(pos.get('cost_basis', 0)),
                    unrealized_pl=float(pos.get('unrealized_pl', 0)),
                    unrealized_plpc=float(pos.get('unrealized_plpc', 0)),
                    current_price=float(pos.get('current_price', 0)),
                    side=pos.get('side', 'long')
                )
                position_list.append(position)
            
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
            if not self.api_key or not self.secret_key:
                return self._create_mock_order(symbol, quantity, side, OrderType.MARKET)
            
            # Validate order
            if not await self._validate_order(symbol, quantity, side):
                return None
            
            # Create order payload
            order_payload = {
                'symbol': symbol.upper(),
                'qty': str(quantity),
                'side': side.lower(),
                'type': 'market',
                'time_in_force': 'day'
            }
            
            if notes:
                order_payload['client_order_id'] = f"rr_{datetime.now().timestamp()}"
            
            response = requests.post(f"{self.base_url}/v2/orders", 
                                   headers=self.headers, 
                                   data=json.dumps(order_payload))
            response.raise_for_status()
            
            order_data = response.json()
            
            order = Order(
                id=order_data.get('id', ''),
                symbol=symbol.upper(),
                side=OrderSide(side.lower()),
                order_type=OrderType.MARKET,
                quantity=quantity,
                status=OrderStatus(order_data.get('status', 'pending')),
                created_at=datetime.fromisoformat(order_data.get('created_at', '').replace('Z', '+00:00')),
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
            if not self.api_key or not self.secret_key:
                return self._create_mock_order(symbol, quantity, side, OrderType.LIMIT, limit_price)
            
            # Validate order
            if not await self._validate_order(symbol, quantity, side, limit_price):
                return None
            
            # Create order payload
            order_payload = {
                'symbol': symbol.upper(),
                'qty': str(quantity),
                'side': side.lower(),
                'type': 'limit',
                'time_in_force': 'day',
                'limit_price': str(limit_price)
            }
            
            if notes:
                order_payload['client_order_id'] = f"rr_{datetime.now().timestamp()}"
            
            response = requests.post(f"{self.base_url}/v2/orders", 
                                   headers=self.headers, 
                                   data=json.dumps(order_payload))
            response.raise_for_status()
            
            order_data = response.json()
            
            order = Order(
                id=order_data.get('id', ''),
                symbol=symbol.upper(),
                side=OrderSide(side.lower()),
                order_type=OrderType.LIMIT,
                quantity=quantity,
                price=limit_price,
                status=OrderStatus(order_data.get('status', 'pending')),
                created_at=datetime.fromisoformat(order_data.get('created_at', '').replace('Z', '+00:00')),
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
            if not self.api_key or not self.secret_key:
                return self._create_mock_order(symbol, quantity, side, OrderType.STOP_LOSS, stop_price=stop_price)
            
            # Validate order
            if not await self._validate_order(symbol, quantity, side, stop_price):
                return None
            
            # Create order payload
            order_payload = {
                'symbol': symbol.upper(),
                'qty': str(quantity),
                'side': side.lower(),
                'type': 'stop',
                'time_in_force': 'day',
                'stop_price': str(stop_price)
            }
            
            if notes:
                order_payload['client_order_id'] = f"rr_{datetime.now().timestamp()}"
            
            response = requests.post(f"{self.base_url}/v2/orders", 
                                   headers=self.headers, 
                                   data=json.dumps(order_payload))
            response.raise_for_status()
            
            order_data = response.json()
            
            order = Order(
                id=order_data.get('id', ''),
                symbol=symbol.upper(),
                side=OrderSide(side.lower()),
                order_type=OrderType.STOP_LOSS,
                quantity=quantity,
                stop_price=stop_price,
                status=OrderStatus(order_data.get('status', 'pending')),
                created_at=datetime.fromisoformat(order_data.get('created_at', '').replace('Z', '+00:00')),
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
            if not self.api_key or not self.secret_key:
                logger.info(f"✅ Mock order {order_id} cancelled")
                return True
            
            response = requests.delete(f"{self.base_url}/v2/orders/{order_id}", headers=self.headers)
            response.raise_for_status()
            
            logger.info(f"✅ Order {order_id} cancelled")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to cancel order {order_id}: {e}")
            return False
    
    async def get_order_status(self, order_id: str) -> Optional[Order]:
        """Get order status"""
        try:
            if not self.api_key or not self.secret_key:
                return self._get_mock_order_status(order_id)
            
            response = requests.get(f"{self.base_url}/v2/orders/{order_id}", headers=self.headers)
            response.raise_for_status()
            
            order_data = response.json()
            
            return Order(
                id=order_data.get('id', ''),
                symbol=order_data.get('symbol', ''),
                side=OrderSide(order_data.get('side', 'buy')),
                order_type=OrderType(order_data.get('order_type', 'market')),
                quantity=int(order_data.get('qty', 0)),
                price=float(order_data.get('limit_price', 0)) if order_data.get('limit_price') else None,
                stop_price=float(order_data.get('stop_price', 0)) if order_data.get('stop_price') else None,
                status=OrderStatus(order_data.get('status', 'pending')),
                created_at=datetime.fromisoformat(order_data.get('created_at', '').replace('Z', '+00:00')),
                filled_at=datetime.fromisoformat(order_data.get('filled_at', '').replace('Z', '+00:00')) if order_data.get('filled_at') else None,
                filled_quantity=int(order_data.get('filled_qty', 0)),
                average_fill_price=float(order_data.get('filled_avg_price', 0)) if order_data.get('filled_avg_price') else None,
                commission=float(order_data.get('commission', 0)) if order_data.get('commission') else 0.0
            )
            
        except Exception as e:
            logger.error(f"❌ Failed to get order status: {e}")
            return None
    
    async def get_orders(self, status: str = None, limit: int = 50) -> List[Order]:
        """Get orders with optional status filter"""
        try:
            if not self.api_key or not self.secret_key:
                return self._get_mock_orders(limit)
            
            params = {'limit': limit}
            if status:
                params['status'] = status
            
            response = requests.get(f"{self.base_url}/v2/orders", 
                                  headers=self.headers, 
                                  params=params)
            response.raise_for_status()
            
            orders_data = response.json()
            
            order_list = []
            for order_data in orders_data:
                order = Order(
                    id=order_data.get('id', ''),
                    symbol=order_data.get('symbol', ''),
                    side=OrderSide(order_data.get('side', 'buy')),
                    order_type=OrderType(order_data.get('order_type', 'market')),
                    quantity=int(order_data.get('qty', 0)),
                    price=float(order_data.get('limit_price', 0)) if order_data.get('limit_price') else None,
                    stop_price=float(order_data.get('stop_price', 0)) if order_data.get('stop_price') else None,
                    status=OrderStatus(order_data.get('status', 'pending')),
                    created_at=datetime.fromisoformat(order_data.get('created_at', '').replace('Z', '+00:00')),
                    filled_at=datetime.fromisoformat(order_data.get('filled_at', '').replace('Z', '+00:00')) if order_data.get('filled_at') else None,
                    filled_quantity=int(order_data.get('filled_qty', 0)),
                    average_fill_price=float(order_data.get('filled_avg_price', 0)) if order_data.get('filled_avg_price') else None,
                    commission=float(order_data.get('commission', 0)) if order_data.get('commission') else 0.0
                )
                order_list.append(order)
            
            return order_list
            
        except Exception as e:
            logger.error(f"❌ Failed to get orders: {e}")
            return self._get_mock_orders(limit)
    
    async def get_quote(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Get real-time quote for a symbol"""
        try:
            if not self.api_key or not self.secret_key:
                return self._get_mock_quote(symbol)
            
            response = requests.get(f"{self.base_url}/v2/stocks/{symbol}/quotes/latest", 
                                  headers=self.headers)
            response.raise_for_status()
            
            quote_data = response.json()
            quote = quote_data.get('quote', {})
            
            return {
                'symbol': symbol,
                'bid': float(quote.get('bp', 0)),
                'ask': float(quote.get('ap', 0)),
                'bid_size': int(quote.get('bs', 0)),
                'ask_size': int(quote.get('as', 0)),
                'timestamp': datetime.fromisoformat(quote.get('t', '').replace('Z', '+00:00'))
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
    
    # All mock methods removed for production

# Global trading service instance
trading_service = SimpleTradingService()
