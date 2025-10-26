"""
Alpaca Paper Trading Adapter
Real brokerage integration with Alpaca Markets for paper trading
"""

import asyncio
import logging
import aiohttp
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import json
import os

from alpaca.trading.client import TradingClient
from alpaca.trading.requests import (
    MarketOrderRequest, LimitOrderRequest, StopLossRequest, 
    TakeProfitRequest, TrailingStopRequest
)
from alpaca.trading.enums import OrderSide as AlpacaOrderSide, OrderType as AlpacaOrderType, TimeInForce as AlpacaTimeInForce
from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import StockBarsRequest, StockQuotesRequest
from alpaca.data.timeframe import TimeFrame

from .enhanced_base import (
    BrokerageAdapter, Order, Position, Account, Trade,
    OrderSide, OrderType, OrderStatus, TimeInForce
)


class AlpacaAdapter(BrokerageAdapter):
    """Alpaca Markets brokerage adapter implementation"""
    
    def __init__(self, api_key: str, api_secret: str, base_url: Optional[str] = None, paper: bool = True):
        super().__init__(api_key, api_secret, base_url, paper)
        self.logger = logging.getLogger(__name__)
        
        # Initialize Alpaca clients
        self.trading_client = TradingClient(
            api_key=api_key,
            secret_key=api_secret,
            paper=paper,
            api_version="v2"
        )
        
        self.data_client = StockHistoricalDataClient(
            api_key=api_key,
            secret_key=api_secret
        )
        
        # Alpaca-specific configuration
        self.base_url = base_url or ("https://paper-api.alpaca.markets" if paper else "https://api.alpaca.markets")
        self.data_url = "https://data.alpaca.markets"
        
        self.logger.info(f"Alpaca adapter initialized (paper: {paper})")
    
    def _convert_order_side(self, side: OrderSide) -> AlpacaOrderSide:
        """Convert order side to Alpaca format"""
        if side in [OrderSide.BUY, OrderSide.LONG]:
            return AlpacaOrderSide.BUY
        elif side in [OrderSide.SELL, OrderSide.SHORT]:
            return AlpacaOrderSide.SELL
        else:
            raise ValueError(f"Invalid order side: {side}")
    
    def _convert_order_type(self, order_type: OrderType) -> AlpacaOrderType:
        """Convert order type to Alpaca format"""
        type_map = {
            OrderType.MARKET: AlpacaOrderType.MARKET,
            OrderType.LIMIT: AlpacaOrderType.LIMIT,
            OrderType.STOP: AlpacaOrderType.STOP,
            OrderType.STOP_LIMIT: AlpacaOrderType.STOP_LIMIT,
            OrderType.TRAILING_STOP: AlpacaOrderType.TRAILING_STOP
        }
        
        if order_type not in type_map:
            raise ValueError(f"Unsupported order type: {order_type}")
        
        return type_map[order_type]
    
    def _convert_time_in_force(self, tif: TimeInForce) -> AlpacaTimeInForce:
        """Convert time in force to Alpaca format"""
        tif_map = {
            TimeInForce.DAY: AlpacaTimeInForce.DAY,
            TimeInForce.GTC: AlpacaTimeInForce.GTC,
            TimeInForce.IOC: AlpacaTimeInForce.IOC,
            TimeInForce.FOK: AlpacaTimeInForce.FOK
        }
        
        return tif_map.get(tif, AlpacaTimeInForce.DAY)
    
    def _convert_alpaca_order(self, alpaca_order) -> Order:
        """Convert Alpaca order to our Order format"""
        # Convert side
        if alpaca_order.side == AlpacaOrderSide.BUY:
            side = OrderSide.BUY
        else:
            side = OrderSide.SELL
        
        # Convert order type
        type_map = {
            AlpacaOrderType.MARKET: OrderType.MARKET,
            AlpacaOrderType.LIMIT: OrderType.LIMIT,
            AlpacaOrderType.STOP: OrderType.STOP,
            AlpacaOrderType.STOP_LIMIT: OrderType.STOP_LIMIT,
            AlpacaOrderType.TRAILING_STOP: OrderType.TRAILING_STOP
        }
        order_type = type_map.get(alpaca_order.order_type, OrderType.MARKET)
        
        # Convert status
        status_map = {
            "new": OrderStatus.PENDING,
            "accepted": OrderStatus.ACCEPTED,
            "partially_filled": OrderStatus.PARTIALLY_FILLED,
            "filled": OrderStatus.FILLED,
            "canceled": OrderStatus.CANCELED,
            "rejected": OrderStatus.REJECTED,
            "expired": OrderStatus.EXPIRED
        }
        status = status_map.get(alpaca_order.status, OrderStatus.PENDING)
        
        # Convert time in force
        tif_map = {
            "day": TimeInForce.DAY,
            "gtc": TimeInForce.GTC,
            "ioc": TimeInForce.IOC,
            "fok": TimeInForce.FOK
        }
        time_in_force = tif_map.get(alpaca_order.time_in_force, TimeInForce.DAY)
        
        return Order(
            id=alpaca_order.id,
            client_order_id=alpaca_order.client_order_id,
            symbol=alpaca_order.symbol,
            side=side,
            order_type=order_type,
            quantity=int(alpaca_order.qty),
            price=float(alpaca_order.limit_price) if alpaca_order.limit_price else None,
            stop_price=float(alpaca_order.stop_price) if alpaca_order.stop_price else None,
            time_in_force=time_in_force,
            status=status,
            filled_quantity=int(alpaca_order.filled_qty),
            filled_avg_price=float(alpaca_order.filled_avg_price) if alpaca_order.filled_avg_price else None,
            created_at=alpaca_order.created_at,
            updated_at=alpaca_order.updated_at
        )
    
    def _convert_alpaca_position(self, alpaca_position) -> Position:
        """Convert Alpaca position to our Position format"""
        # Determine side based on quantity
        if alpaca_position.qty > 0:
            side = OrderSide.LONG
            quantity = int(alpaca_position.qty)
        else:
            side = OrderSide.SHORT
            quantity = int(abs(alpaca_position.qty))
        
        return Position(
            symbol=alpaca_position.symbol,
            quantity=quantity,
            side=side,
            average_price=float(alpaca_position.avg_entry_price),
            current_price=float(alpaca_position.current_price),
            market_value=float(alpaca_position.market_value),
            unrealized_pnl=float(alpaca_position.unrealized_pl),
            unrealized_pnl_percent=float(alpaca_position.unrealized_plpc) * 100,
            realized_pnl=float(alpaca_position.realized_pl),
            cost_basis=float(alpaca_position.cost_basis),
            day_pnl=float(alpaca_position.unrealized_pl),  # Alpaca doesn't separate day PnL
            day_pnl_percent=float(alpaca_position.unrealized_plpc) * 100
        )
    
    def _convert_alpaca_account(self, alpaca_account) -> Account:
        """Convert Alpaca account to our Account format"""
        return Account(
            account_id=alpaca_account.id,
            account_type=alpaca_account.account_type,
            cash=float(alpaca_account.cash),
            buying_power=float(alpaca_account.buying_power),
            portfolio_value=float(alpaca_account.portfolio_value),
            equity=float(alpaca_account.equity),
            day_trade_count=int(alpaca_account.day_trade_count),
            pattern_day_trader=alpaca_account.pattern_day_trader,
            day_trading_buying_power=float(alpaca_account.day_trading_buying_power),
            margin_equity=float(alpaca_account.margin_equity),
            margin_used=float(alpaca_account.margin_used),
            margin_available=float(alpaca_account.margin_available),
            last_equity=float(alpaca_account.last_equity),
            last_equity_change=float(alpaca_account.last_equity_change),
            last_equity_change_percent=float(alpaca_account.last_equity_change_percent)
        )
    
    async def place_order(self, order: Order) -> Order:
        """Place an order with Alpaca"""
        
        # Validate order
        errors = self._validate_order(order)
        if errors:
            raise ValueError(f"Order validation failed: {', '.join(errors)}")
        
        try:
            # Create Alpaca order request
            if order.order_type == OrderType.MARKET:
                request = MarketOrderRequest(
                    symbol=order.symbol,
                    qty=order.quantity,
                    side=self._convert_order_side(order.side),
                    time_in_force=self._convert_time_in_force(order.time_in_force),
                    client_order_id=order.client_order_id
                )
            
            elif order.order_type == OrderType.LIMIT:
                request = LimitOrderRequest(
                    symbol=order.symbol,
                    qty=order.quantity,
                    side=self._convert_order_side(order.side),
                    limit_price=order.price,
                    time_in_force=self._convert_time_in_force(order.time_in_force),
                    client_order_id=order.client_order_id
                )
            
            elif order.order_type == OrderType.STOP:
                request = StopLossRequest(
                    symbol=order.symbol,
                    qty=order.quantity,
                    side=self._convert_order_side(order.side),
                    stop_price=order.stop_price,
                    time_in_force=self._convert_time_in_force(order.time_in_force),
                    client_order_id=order.client_order_id
                )
            
            elif order.order_type == OrderType.TRAILING_STOP:
                request = TrailingStopRequest(
                    symbol=order.symbol,
                    qty=order.quantity,
                    side=self._convert_order_side(order.side),
                    trail_percent=order.trailing_stop_percent,
                    time_in_force=self._convert_time_in_force(order.time_in_force),
                    client_order_id=order.client_order_id
                )
            
            else:
                raise ValueError(f"Unsupported order type: {order.order_type}")
            
            # Submit order
            alpaca_order = self.trading_client.submit_order(request)
            
            # Convert back to our format
            placed_order = self._convert_alpaca_order(alpaca_order)
            
            # Store in active orders
            self.active_orders[placed_order.id] = placed_order
            
            self.logger.info(f"Order placed: {placed_order.id} - {placed_order.symbol} {placed_order.side.value} {placed_order.quantity}")
            
            return placed_order
            
        except Exception as e:
            self.logger.error(f"Failed to place order: {e}")
            raise
    
    async def cancel_order(self, order_id: str) -> bool:
        """Cancel an order"""
        try:
            self.trading_client.cancel_order_by_id(order_id)
            
            # Update local cache
            if order_id in self.active_orders:
                self.active_orders[order_id].status = OrderStatus.CANCELED
                self.active_orders[order_id].updated_at = datetime.now()
            
            self.logger.info(f"Order canceled: {order_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to cancel order {order_id}: {e}")
            return False
    
    async def modify_order(self, order_id: str, **kwargs) -> Order:
        """Modify an existing order"""
        try:
            # Alpaca doesn't support order modification directly
            # We need to cancel and replace
            await self.cancel_order(order_id)
            
            # Get original order
            original_order = await self.get_order(order_id)
            if not original_order:
                raise ValueError(f"Order {order_id} not found")
            
            # Create new order with modifications
            new_order = Order(
                id=str(uuid.uuid4()),
                symbol=original_order.symbol,
                side=original_order.side,
                order_type=original_order.order_type,
                quantity=kwargs.get('quantity', original_order.quantity),
                price=kwargs.get('price', original_order.price),
                stop_price=kwargs.get('stop_price', original_order.stop_price),
                time_in_force=kwargs.get('time_in_force', original_order.time_in_force)
            )
            
            return await self.place_order(new_order)
            
        except Exception as e:
            self.logger.error(f"Failed to modify order {order_id}: {e}")
            raise
    
    async def get_order(self, order_id: str) -> Optional[Order]:
        """Get order details"""
        try:
            alpaca_order = self.trading_client.get_order_by_id(order_id)
            return self._convert_alpaca_order(alpaca_order)
            
        except Exception as e:
            self.logger.error(f"Failed to get order {order_id}: {e}")
            return None
    
    async def get_orders(
        self, 
        status: Optional[OrderStatus] = None,
        symbol: Optional[str] = None,
        limit: int = 100
    ) -> List[Order]:
        """Get list of orders"""
        try:
            # Convert status to Alpaca format
            alpaca_status = None
            if status:
                status_map = {
                    OrderStatus.PENDING: "new",
                    OrderStatus.ACCEPTED: "accepted",
                    OrderStatus.PARTIALLY_FILLED: "partially_filled",
                    OrderStatus.FILLED: "filled",
                    OrderStatus.CANCELED: "canceled",
                    OrderStatus.REJECTED: "rejected",
                    OrderStatus.EXPIRED: "expired"
                }
                alpaca_status = status_map.get(status)
            
            # Get orders from Alpaca
            alpaca_orders = self.trading_client.get_orders(
                status=alpaca_status,
                symbols=[symbol] if symbol else None,
                limit=limit
            )
            
            # Convert to our format
            orders = [self._convert_alpaca_order(order) for order in alpaca_orders]
            
            return orders
            
        except Exception as e:
            self.logger.error(f"Failed to get orders: {e}")
            return []
    
    async def get_positions(self) -> List[Position]:
        """Get current positions"""
        try:
            alpaca_positions = self.trading_client.get_all_positions()
            positions = [self._convert_alpaca_position(pos) for pos in alpaca_positions]
            
            # Update cache
            self.positions_cache = positions
            self.last_cache_update = datetime.now()
            
            return positions
            
        except Exception as e:
            self.logger.error(f"Failed to get positions: {e}")
            return []
    
    async def get_position(self, symbol: str) -> Optional[Position]:
        """Get position for specific symbol"""
        try:
            alpaca_position = self.trading_client.get_open_position(symbol)
            return self._convert_alpaca_position(alpaca_position)
            
        except Exception as e:
            self.logger.error(f"Failed to get position for {symbol}: {e}")
            return None
    
    async def get_account(self) -> Account:
        """Get account information"""
        try:
            alpaca_account = self.trading_client.get_account()
            account = self._convert_alpaca_account(alpaca_account)
            
            # Update cache
            self.account_cache = account
            self.last_cache_update = datetime.now()
            
            return account
            
        except Exception as e:
            self.logger.error(f"Failed to get account: {e}")
            raise
    
    async def get_trades(
        self, 
        symbol: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 100
    ) -> List[Trade]:
        """Get trade history"""
        try:
            # Alpaca doesn't have a direct trades endpoint
            # We need to get filled orders instead
            orders = await self.get_orders(status=OrderStatus.FILLED, symbol=symbol, limit=limit)
            
            trades = []
            for order in orders:
                if order.filled_quantity > 0 and order.filled_avg_price:
                    trade = Trade(
                        id=f"trade_{order.id}",
                        order_id=order.id,
                        symbol=order.symbol,
                        side=order.side,
                        quantity=order.filled_quantity,
                        price=order.filled_avg_price,
                        timestamp=order.filled_at or order.updated_at,
                        commission=0.0,  # Alpaca doesn't charge commissions
                        fees=0.0
                    )
                    trades.append(trade)
            
            return trades
            
        except Exception as e:
            self.logger.error(f"Failed to get trades: {e}")
            return []
    
    async def get_quotes(self, symbols: List[str]) -> Dict[str, Dict[str, Any]]:
        """Get real-time quotes using Alpaca data API"""
        try:
            quotes = {}
            
            for symbol in symbols:
                try:
                    # Get latest quote
                    quote_request = StockQuotesRequest(
                        symbol_or_symbols=[symbol],
                        limit=1
                    )
                    
                    quote_data = self.data_client.get_stock_latest_quote(quote_request)
                    
                    if symbol in quote_data:
                        quote = quote_data[symbol]
                        quotes[symbol] = {
                            "symbol": symbol,
                            "price": float(quote.bid_price) if quote.bid_price else 0.0,
                            "bid": float(quote.bid_price) if quote.bid_price else 0.0,
                            "ask": float(quote.ask_price) if quote.ask_price else 0.0,
                            "size": int(quote.bid_size) if quote.bid_size else 0,
                            "timestamp": quote.timestamp.isoformat() if quote.timestamp else datetime.now().isoformat()
                        }
                
                except Exception as e:
                    self.logger.warning(f"Failed to get quote for {symbol}: {e}")
                    continue
            
            return quotes
            
        except Exception as e:
            self.logger.error(f"Failed to get quotes: {e}")
            return {}
    
    async def get_historical_data(
        self,
        symbol: str,
        timeframe: str,
        start_date: datetime,
        end_date: datetime,
        limit: int = 1000
    ) -> List[Dict[str, Any]]:
        """Get historical OHLCV data"""
        try:
            # Convert timeframe to Alpaca format
            tf_map = {
                "1m": TimeFrame.Minute,
                "5m": TimeFrame(5, "Minute"),
                "15m": TimeFrame(15, "Minute"),
                "1h": TimeFrame.Hour,
                "1d": TimeFrame.Day
            }
            
            alpaca_timeframe = tf_map.get(timeframe, TimeFrame.Minute)
            
            # Create request
            request = StockBarsRequest(
                symbol_or_symbols=[symbol],
                timeframe=alpaca_timeframe,
                start=start_date,
                end=end_date,
                limit=limit
            )
            
            # Get data
            bars = self.data_client.get_stock_bars(request)
            
            # Convert to our format
            historical_data = []
            if symbol in bars.data:
                for bar in bars.data[symbol]:
                    historical_data.append({
                        "symbol": symbol,
                        "timestamp": bar.timestamp.isoformat(),
                        "open": float(bar.open),
                        "high": float(bar.high),
                        "low": float(bar.low),
                        "close": float(bar.close),
                        "volume": int(bar.volume),
                        "timeframe": timeframe
                    })
            
            return historical_data
            
        except Exception as e:
            self.logger.error(f"Failed to get historical data for {symbol}: {e}")
            return []
    
    async def get_market_status(self) -> Dict[str, Any]:
        """Get market status"""
        try:
            clock = self.trading_client.get_clock()
            
            return {
                "market_open": clock.is_open,
                "next_open": clock.next_open.isoformat() if clock.next_open else None,
                "next_close": clock.next_close.isoformat() if clock.next_close else None,
                "current_time": clock.timestamp.isoformat(),
                "timezone": "US/Eastern"
            }
            
        except Exception as e:
            self.logger.error(f"Failed to get market status: {e}")
            return {
                "market_open": False,
                "current_time": datetime.now().isoformat(),
                "timezone": "US/Eastern"
            }
    
    async def cleanup(self):
        """Cleanup resources"""
        await super().cleanup()
        self.logger.info("Alpaca adapter cleanup completed")


# Factory function for easy instantiation
def create_alpaca_adapter(
    api_key: Optional[str] = None,
    api_secret: Optional[str] = None,
    paper: bool = True
) -> AlpacaAdapter:
    """Create Alpaca adapter instance"""
    
    if not api_key:
        api_key = os.getenv("ALPACA_API_KEY_ID")
        if not api_key:
            raise ValueError("Alpaca API key not provided and not found in environment variables")
    
    if not api_secret:
        api_secret = os.getenv("ALPACA_SECRET_KEY")
        if not api_secret:
            raise ValueError("Alpaca API secret not provided and not found in environment variables")
    
    return AlpacaAdapter(api_key, api_secret, paper=paper)
