"""
Advanced Order Types and Execution Engine
Bracket orders, OCO, Iceberg, and sophisticated execution algorithms
"""

import asyncio
import logging
import numpy as np
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum
import uuid

from ..broker.adapters.base import Broker, OrderSide, OrderType, TimeInForce
from ..market.providers.base import MarketDataProvider


class AdvancedOrderType(Enum):
    """Advanced order types"""
    BRACKET = "BRACKET"
    OCO = "OCO"  # One-Cancels-Other
    ICEBERG = "ICEBERG"
    TRAILING_STOP = "TRAILING_STOP"
    SCALE_IN = "SCALE_IN"
    SCALE_OUT = "SCALE_OUT"
    TWAP = "TWAP"  # Time-Weighted Average Price
    VWAP = "VWAP"  # Volume-Weighted Average Price


class OrderStatus(Enum):
    """Order status enumeration"""
    PENDING = "PENDING"
    SUBMITTED = "SUBMITTED"
    PARTIALLY_FILLED = "PARTIALLY_FILLED"
    FILLED = "FILLED"
    CANCELLED = "CANCELLED"
    REJECTED = "REJECTED"
    EXPIRED = "EXPIRED"


@dataclass
class BracketOrder:
    """Bracket order configuration"""
    symbol: str
    side: OrderSide
    quantity: int
    entry_price: float
    stop_loss: float
    take_profit_1: float
    take_profit_2: Optional[float] = None
    
    # Order IDs
    entry_order_id: Optional[str] = None
    stop_loss_order_id: Optional[str] = None
    take_profit_1_order_id: Optional[str] = None
    take_profit_2_order_id: Optional[str] = None
    
    # Status
    status: OrderStatus = OrderStatus.PENDING
    filled_quantity: int = 0
    average_fill_price: float = 0.0
    
    # Timestamps
    created_at: datetime = None
    updated_at: datetime = None


@dataclass
class OCOOrder:
    """One-Cancels-Other order configuration"""
    symbol: str
    side: OrderSide
    quantity: int
    
    # Two orders - one cancels the other
    order_1_price: float
    order_1_type: OrderType
    order_2_price: float
    order_2_type: OrderType
    
    # Order IDs
    order_1_id: Optional[str] = None
    order_2_id: Optional[str] = None
    
    # Status
    status: OrderStatus = OrderStatus.PENDING
    active_order_id: Optional[str] = None
    
    # Timestamps
    created_at: datetime = None
    updated_at: datetime = None


@dataclass
class IcebergOrder:
    """Iceberg order configuration"""
    symbol: str
    side: OrderSide
    total_quantity: int
    visible_quantity: int
    price: float
    
    # Order ID
    order_id: Optional[str] = None
    
    # Status
    status: OrderStatus = OrderStatus.PENDING
    filled_quantity: int = 0
    remaining_quantity: int = 0
    
    # Timestamps
    created_at: datetime = None
    updated_at: datetime = None


@dataclass
class TrailingStopOrder:
    """Trailing stop order configuration"""
    symbol: str
    side: OrderSide
    quantity: int
    trail_amount: float
    trail_percent: Optional[float] = None
    
    # Order ID
    order_id: Optional[str] = None
    
    # Status
    status: OrderStatus = OrderStatus.PENDING
    current_stop_price: float = 0.0
    highest_price: float = 0.0  # For long positions
    lowest_price: float = 0.0   # For short positions
    
    # Timestamps
    created_at: datetime = None
    updated_at: datetime = None


class AdvancedOrderEngine:
    """Advanced order execution engine"""
    
    def __init__(self, broker: Broker, market_data_provider: MarketDataProvider):
        self.broker = broker
        self.market_data_provider = market_data_provider
        self.logger = logging.getLogger(__name__)
        
        # Order tracking
        self.active_orders = {}
        self.order_history = []
        
        # Order execution parameters
        self.execution_params = {
            "max_retries": 3,
            "retry_delay": 1.0,  # seconds
            "execution_timeout": 300,  # 5 minutes
            "price_tolerance": 0.01,  # 1 cent tolerance
        }
        
        # Order monitoring
        self.order_monitor_task = None
        self.is_monitoring = False
    
    async def place_bracket_order(
        self, 
        symbol: str, 
        side: OrderSide, 
        quantity: int,
        entry_price: float,
        stop_loss: float,
        take_profit_1: float,
        take_profit_2: Optional[float] = None
    ) -> BracketOrder:
        """Place a bracket order"""
        
        try:
            # Create bracket order
            bracket_order = BracketOrder(
                symbol=symbol,
                side=side,
                quantity=quantity,
                entry_price=entry_price,
                stop_loss=stop_loss,
                take_profit_1=take_profit_1,
                take_profit_2=take_profit_2,
                created_at=datetime.now()
            )
            
            # Place entry order
            entry_order = await self.broker.place_order(
                symbol=symbol,
                side=side,
                qty=quantity,
                type=OrderType.LIMIT,
                limit_price=entry_price,
                time_in_force=TimeInForce.DAY,
                client_order_id=f"BRACKET_ENTRY_{uuid.uuid4().hex[:8]}"
            )
            
            bracket_order.entry_order_id = entry_order.id
            bracket_order.status = OrderStatus.SUBMITTED
            
            # Store order
            order_id = f"BRACKET_{uuid.uuid4().hex[:8]}"
            self.active_orders[order_id] = bracket_order
            
            self.logger.info(f"✅ Bracket order placed for {symbol}: Entry={entry_price}, SL={stop_loss}, TP1={take_profit_1}")
            
            return bracket_order
            
        except Exception as e:
            self.logger.error(f"❌ Bracket order failed for {symbol}: {e}")
            raise
    
    async def place_oco_order(
        self,
        symbol: str,
        side: OrderSide,
        quantity: int,
        order_1_price: float,
        order_1_type: OrderType,
        order_2_price: float,
        order_2_type: OrderType
    ) -> OCOOrder:
        """Place an OCO (One-Cancels-Other) order"""
        
        try:
            # Create OCO order
            oco_order = OCOOrder(
                symbol=symbol,
                side=side,
                quantity=quantity,
                order_1_price=order_1_price,
                order_1_type=order_1_type,
                order_2_price=order_2_price,
                order_2_type=order_2_type,
                created_at=datetime.now()
            )
            
            # Place both orders
            order_1 = await self.broker.place_order(
                symbol=symbol,
                side=side,
                qty=quantity,
                type=order_1_type,
                limit_price=order_1_price if order_1_type == OrderType.LIMIT else None,
                stop_price=order_1_price if order_1_type == OrderType.STOP else None,
                time_in_force=TimeInForce.DAY,
                client_order_id=f"OCO_1_{uuid.uuid4().hex[:8]}"
            )
            
            order_2 = await self.broker.place_order(
                symbol=symbol,
                side=side,
                qty=quantity,
                type=order_2_type,
                limit_price=order_2_price if order_2_type == OrderType.LIMIT else None,
                stop_price=order_2_price if order_2_type == OrderType.STOP else None,
                time_in_force=TimeInForce.DAY,
                client_order_id=f"OCO_2_{uuid.uuid4().hex[:8]}"
            )
            
            oco_order.order_1_id = order_1.id
            oco_order.order_2_id = order_2.id
            oco_order.status = OrderStatus.SUBMITTED
            
            # Store order
            order_id = f"OCO_{uuid.uuid4().hex[:8]}"
            self.active_orders[order_id] = oco_order
            
            self.logger.info(f"✅ OCO order placed for {symbol}: Order1={order_1_price}, Order2={order_2_price}")
            
            return oco_order
            
        except Exception as e:
            self.logger.error(f"❌ OCO order failed for {symbol}: {e}")
            raise
    
    async def place_iceberg_order(
        self,
        symbol: str,
        side: OrderSide,
        total_quantity: int,
        visible_quantity: int,
        price: float
    ) -> IcebergOrder:
        """Place an iceberg order"""
        
        try:
            # Create iceberg order
            iceberg_order = IcebergOrder(
                symbol=symbol,
                side=side,
                total_quantity=total_quantity,
                visible_quantity=visible_quantity,
                price=price,
                remaining_quantity=total_quantity,
                created_at=datetime.now()
            )
            
            # Place initial order with visible quantity
            initial_order = await self.broker.place_order(
                symbol=symbol,
                side=side,
                qty=visible_quantity,
                type=OrderType.LIMIT,
                limit_price=price,
                time_in_force=TimeInForce.DAY,
                client_order_id=f"ICEBERG_{uuid.uuid4().hex[:8]}"
            )
            
            iceberg_order.order_id = initial_order.id
            iceberg_order.status = OrderStatus.SUBMITTED
            
            # Store order
            order_id = f"ICEBERG_{uuid.uuid4().hex[:8]}"
            self.active_orders[order_id] = iceberg_order
            
            self.logger.info(f"✅ Iceberg order placed for {symbol}: Total={total_quantity}, Visible={visible_quantity}, Price={price}")
            
            return iceberg_order
            
        except Exception as e:
            self.logger.error(f"❌ Iceberg order failed for {symbol}: {e}")
            raise
    
    async def place_trailing_stop_order(
        self,
        symbol: str,
        side: OrderSide,
        quantity: int,
        trail_amount: float,
        trail_percent: Optional[float] = None
    ) -> TrailingStopOrder:
        """Place a trailing stop order"""
        
        try:
            # Get current price
            quotes = await self.market_data_provider.get_quotes([symbol])
            if symbol not in quotes:
                raise ValueError(f"No quote available for {symbol}")
            
            current_price = quotes[symbol].price
            
            # Create trailing stop order
            trailing_stop = TrailingStopOrder(
                symbol=symbol,
                side=side,
                quantity=quantity,
                trail_amount=trail_amount,
                trail_percent=trail_percent,
                current_stop_price=current_price - trail_amount if side == OrderSide.BUY else current_price + trail_amount,
                highest_price=current_price if side == OrderSide.BUY else 0,
                lowest_price=current_price if side == OrderSide.SELL else float('inf'),
                created_at=datetime.now()
            )
            
            # Place initial stop order
            stop_order = await self.broker.place_order(
                symbol=symbol,
                side=OrderSide.SELL if side == OrderSide.BUY else OrderSide.BUY,
                qty=quantity,
                type=OrderType.STOP,
                stop_price=trailing_stop.current_stop_price,
                time_in_force=TimeInForce.DAY,
                client_order_id=f"TRAILING_{uuid.uuid4().hex[:8]}"
            )
            
            trailing_stop.order_id = stop_order.id
            trailing_stop.status = OrderStatus.SUBMITTED
            
            # Store order
            order_id = f"TRAILING_{uuid.uuid4().hex[:8]}"
            self.active_orders[order_id] = trailing_stop
            
            self.logger.info(f"✅ Trailing stop placed for {symbol}: Trail={trail_amount}, Stop={trailing_stop.current_stop_price}")
            
            return trailing_stop
            
        except Exception as e:
            self.logger.error(f"❌ Trailing stop failed for {symbol}: {e}")
            raise
    
    async def execute_twap_order(
        self,
        symbol: str,
        side: OrderSide,
        total_quantity: int,
        duration_minutes: int,
        price_limit: Optional[float] = None
    ) -> Dict[str, Any]:
        """Execute TWAP (Time-Weighted Average Price) order"""
        
        try:
            self.logger.info(f"🕐 Starting TWAP execution for {symbol}: {total_quantity} shares over {duration_minutes} minutes")
            
            # Calculate execution schedule
            num_intervals = min(10, duration_minutes // 2)  # Max 10 intervals, min 2 minutes each
            interval_minutes = duration_minutes // num_intervals
            quantity_per_interval = total_quantity // num_intervals
            
            execution_results = []
            total_filled = 0
            
            for i in range(num_intervals):
                try:
                    # Wait for interval
                    if i > 0:
                        await asyncio.sleep(interval_minutes * 60)
                    
                    # Get current market price
                    quotes = await self.market_data_provider.get_quotes([symbol])
                    if symbol not in quotes:
                        continue
                    
                    current_price = quotes[symbol].price
                    
                    # Check price limit
                    if price_limit:
                        if side == OrderSide.BUY and current_price > price_limit:
                            continue
                        elif side == OrderSide.SELL and current_price < price_limit:
                            continue
                    
                    # Place market order for this interval
                    order = await self.broker.place_order(
                        symbol=symbol,
                        side=side,
                        qty=quantity_per_interval,
                        type=OrderType.MARKET,
                        time_in_force=TimeInForce.DAY,
                        client_order_id=f"TWAP_{i}_{uuid.uuid4().hex[:8]}"
                    )
                    
                    execution_results.append({
                        "interval": i + 1,
                        "quantity": quantity_per_interval,
                        "price": current_price,
                        "order_id": order.id,
                        "timestamp": datetime.now()
                    })
                    
                    total_filled += quantity_per_interval
                    
                    self.logger.info(f"✅ TWAP interval {i+1}/{num_intervals}: {quantity_per_interval} shares at {current_price}")
                    
                except Exception as e:
                    self.logger.error(f"❌ TWAP interval {i+1} failed: {e}")
                    continue
            
            return {
                "symbol": symbol,
                "side": side,
                "total_quantity": total_quantity,
                "total_filled": total_filled,
                "execution_results": execution_results,
                "average_price": sum(r["price"] * r["quantity"] for r in execution_results) / total_filled if total_filled > 0 else 0,
                "duration_minutes": duration_minutes,
                "completed_at": datetime.now()
            }
            
        except Exception as e:
            self.logger.error(f"❌ TWAP execution failed for {symbol}: {e}")
            raise
    
    async def execute_vwap_order(
        self,
        symbol: str,
        side: OrderSide,
        total_quantity: int,
        duration_minutes: int,
        price_limit: Optional[float] = None
    ) -> Dict[str, Any]:
        """Execute VWAP (Volume-Weighted Average Price) order"""
        
        try:
            self.logger.info(f"📊 Starting VWAP execution for {symbol}: {total_quantity} shares over {duration_minutes} minutes")
            
            # Get historical volume data for VWAP calculation
            ohlcv_data = await self.market_data_provider.get_ohlcv(symbol, "1m", limit=duration_minutes)
            
            if len(ohlcv_data) < 10:
                # Fallback to TWAP if insufficient data
                return await self.execute_twap_order(symbol, side, total_quantity, duration_minutes, price_limit)
            
            # Calculate volume-weighted schedule
            total_volume = sum(candle.volume for candle in ohlcv_data)
            volume_weights = [candle.volume / total_volume for candle in ohlcv_data]
            
            # Calculate quantity per interval based on volume weights
            quantities_per_interval = [int(weight * total_quantity) for weight in volume_weights]
            
            execution_results = []
            total_filled = 0
            
            for i, (candle, quantity) in enumerate(zip(ohlcv_data, quantities_per_interval)):
                if quantity <= 0:
                    continue
                
                try:
                    # Wait for interval (1 minute)
                    if i > 0:
                        await asyncio.sleep(60)
                    
                    # Use candle's typical price (HLC3)
                    typical_price = (candle.high + candle.low + candle.close) / 3
                    
                    # Check price limit
                    if price_limit:
                        if side == OrderSide.BUY and typical_price > price_limit:
                            continue
                        elif side == OrderSide.SELL and typical_price < price_limit:
                            continue
                    
                    # Place limit order at typical price
                    order = await self.broker.place_order(
                        symbol=symbol,
                        side=side,
                        qty=quantity,
                        type=OrderType.LIMIT,
                        limit_price=typical_price,
                        time_in_force=TimeInForce.DAY,
                        client_order_id=f"VWAP_{i}_{uuid.uuid4().hex[:8]}"
                    )
                    
                    execution_results.append({
                        "interval": i + 1,
                        "quantity": quantity,
                        "price": typical_price,
                        "volume_weight": volume_weights[i],
                        "order_id": order.id,
                        "timestamp": datetime.now()
                    })
                    
                    total_filled += quantity
                    
                    self.logger.info(f"✅ VWAP interval {i+1}: {quantity} shares at {typical_price}")
                    
                except Exception as e:
                    self.logger.error(f"❌ VWAP interval {i+1} failed: {e}")
                    continue
            
            return {
                "symbol": symbol,
                "side": side,
                "total_quantity": total_quantity,
                "total_filled": total_filled,
                "execution_results": execution_results,
                "average_price": sum(r["price"] * r["quantity"] for r in execution_results) / total_filled if total_filled > 0 else 0,
                "duration_minutes": duration_minutes,
                "completed_at": datetime.now()
            }
            
        except Exception as e:
            self.logger.error(f"❌ VWAP execution failed for {symbol}: {e}")
            raise
    
    async def start_order_monitoring(self):
        """Start monitoring active orders"""
        
        if self.is_monitoring:
            return
        
        self.is_monitoring = True
        self.order_monitor_task = asyncio.create_task(self._monitor_orders())
        self.logger.info("🔍 Started order monitoring")
    
    async def stop_order_monitoring(self):
        """Stop monitoring active orders"""
        
        if not self.is_monitoring:
            return
        
        self.is_monitoring = False
        if self.order_monitor_task:
            self.order_monitor_task.cancel()
            try:
                await self.order_monitor_task
            except asyncio.CancelledError:
                pass
        
        self.logger.info("🛑 Stopped order monitoring")
    
    async def _monitor_orders(self):
        """Monitor active orders and handle updates"""
        
        while self.is_monitoring:
            try:
                # Check each active order
                for order_id, order in list(self.active_orders.items()):
                    await self._update_order_status(order_id, order)
                
                # Wait before next check
                await asyncio.sleep(5)  # Check every 5 seconds
                
            except Exception as e:
                self.logger.error(f"❌ Order monitoring error: {e}")
                await asyncio.sleep(10)  # Wait longer on error
    
    async def _update_order_status(self, order_id: str, order: Any):
        """Update status of a specific order"""
        
        try:
            # This would integrate with broker's order status API
            # For now, we'll simulate order updates
            
            if isinstance(order, BracketOrder):
                await self._update_bracket_order(order_id, order)
            elif isinstance(order, OCOOrder):
                await self._update_oco_order(order_id, order)
            elif isinstance(order, IcebergOrder):
                await self._update_iceberg_order(order_id, order)
            elif isinstance(order, TrailingStopOrder):
                await self._update_trailing_stop_order(order_id, order)
                
        except Exception as e:
            self.logger.error(f"❌ Order status update failed for {order_id}: {e}")
    
    async def _update_bracket_order(self, order_id: str, bracket_order: BracketOrder):
        """Update bracket order status"""
        
        # Check if entry order is filled
        if bracket_order.status == OrderStatus.SUBMITTED:
            # Simulate order fill (in reality, would check broker API)
            if np.random.random() < 0.1:  # 10% chance of fill per check
                bracket_order.status = OrderStatus.FILLED
                bracket_order.filled_quantity = bracket_order.quantity
                bracket_order.average_fill_price = bracket_order.entry_price
                
                # Place stop loss and take profit orders
                await self._place_bracket_exit_orders(bracket_order)
                
                self.logger.info(f"✅ Bracket entry filled for {bracket_order.symbol}")
    
    async def _place_bracket_exit_orders(self, bracket_order: BracketOrder):
        """Place stop loss and take profit orders for bracket"""
        
        try:
            # Place stop loss order
            stop_loss_side = OrderSide.SELL if bracket_order.side == OrderSide.BUY else OrderSide.BUY
            stop_loss_order = await self.broker.place_order(
                symbol=bracket_order.symbol,
                side=stop_loss_side,
                qty=bracket_order.quantity,
                type=OrderType.STOP,
                stop_price=bracket_order.stop_loss,
                time_in_force=TimeInForce.DAY,
                client_order_id=f"BRACKET_SL_{uuid.uuid4().hex[:8]}"
            )
            
            bracket_order.stop_loss_order_id = stop_loss_order.id
            
            # Place take profit order
            take_profit_side = OrderSide.SELL if bracket_order.side == OrderSide.BUY else OrderSide.BUY
            take_profit_order = await self.broker.place_order(
                symbol=bracket_order.symbol,
                side=take_profit_side,
                qty=bracket_order.quantity,
                type=OrderType.LIMIT,
                limit_price=bracket_order.take_profit_1,
                time_in_force=TimeInForce.DAY,
                client_order_id=f"BRACKET_TP_{uuid.uuid4().hex[:8]}"
            )
            
            bracket_order.take_profit_1_order_id = take_profit_order.id
            
            self.logger.info(f"✅ Bracket exit orders placed for {bracket_order.symbol}")
            
        except Exception as e:
            self.logger.error(f"❌ Bracket exit orders failed for {bracket_order.symbol}: {e}")
    
    async def _update_oco_order(self, order_id: str, oco_order: OCOOrder):
        """Update OCO order status"""
        
        # Simulate one order filling and cancelling the other
        if oco_order.status == OrderStatus.SUBMITTED:
            if np.random.random() < 0.05:  # 5% chance per check
                # Simulate order 1 filling
                oco_order.status = OrderStatus.FILLED
                oco_order.active_order_id = oco_order.order_1_id
                
                # Cancel order 2
                try:
                    await self.broker.cancel_order(oco_order.order_2_id)
                    self.logger.info(f"✅ OCO order completed for {oco_order.symbol}")
                except:
                    pass
    
    async def _update_iceberg_order(self, order_id: str, iceberg_order: IcebergOrder):
        """Update iceberg order status"""
        
        # Simulate iceberg order execution
        if iceberg_order.status == OrderStatus.SUBMITTED:
            if np.random.random() < 0.2:  # 20% chance per check
                # Simulate partial fill
                fill_quantity = min(iceberg_order.visible_quantity, iceberg_order.remaining_quantity)
                iceberg_order.filled_quantity += fill_quantity
                iceberg_order.remaining_quantity -= fill_quantity
                
                if iceberg_order.remaining_quantity > 0:
                    # Place next iceberg order
                    await self._place_next_iceberg_order(iceberg_order)
                else:
                    iceberg_order.status = OrderStatus.FILLED
                    self.logger.info(f"✅ Iceberg order completed for {iceberg_order.symbol}")
    
    async def _place_next_iceberg_order(self, iceberg_order: IcebergOrder):
        """Place next iceberg order"""
        
        try:
            next_quantity = min(iceberg_order.visible_quantity, iceberg_order.remaining_quantity)
            
            next_order = await self.broker.place_order(
                symbol=iceberg_order.symbol,
                side=iceberg_order.side,
                qty=next_quantity,
                type=OrderType.LIMIT,
                limit_price=iceberg_order.price,
                time_in_force=TimeInForce.DAY,
                client_order_id=f"ICEBERG_NEXT_{uuid.uuid4().hex[:8]}"
            )
            
            iceberg_order.order_id = next_order.id
            self.logger.info(f"✅ Next iceberg order placed for {iceberg_order.symbol}: {next_quantity} shares")
            
        except Exception as e:
            self.logger.error(f"❌ Next iceberg order failed for {iceberg_order.symbol}: {e}")
    
    async def _update_trailing_stop_order(self, order_id: str, trailing_stop: TrailingStopOrder):
        """Update trailing stop order"""
        
        try:
            # Get current price
            quotes = await self.market_data_provider.get_quotes([trailing_stop.symbol])
            if trailing_stop.symbol not in quotes:
                return
            
            current_price = quotes[trailing_stop.symbol].price
            
            # Update highest/lowest prices
            if trailing_stop.side == OrderSide.BUY:
                if current_price > trailing_stop.highest_price:
                    trailing_stop.highest_price = current_price
                    # Update stop price
                    new_stop_price = current_price - trailing_stop.trail_amount
                    if new_stop_price > trailing_stop.current_stop_price:
                        trailing_stop.current_stop_price = new_stop_price
                        # Update the order (would need broker API support)
                        self.logger.info(f"📈 Trailing stop updated for {trailing_stop.symbol}: {new_stop_price}")
            else:  # SELL
                if current_price < trailing_stop.lowest_price:
                    trailing_stop.lowest_price = current_price
                    # Update stop price
                    new_stop_price = current_price + trailing_stop.trail_amount
                    if new_stop_price < trailing_stop.current_stop_price:
                        trailing_stop.current_stop_price = new_stop_price
                        # Update the order (would need broker API support)
                        self.logger.info(f"📉 Trailing stop updated for {trailing_stop.symbol}: {new_stop_price}")
            
        except Exception as e:
            self.logger.error(f"❌ Trailing stop update failed for {trailing_stop.symbol}: {e}")
    
    async def cancel_order(self, order_id: str) -> bool:
        """Cancel an order"""
        
        try:
            if order_id in self.active_orders:
                order = self.active_orders[order_id]
                
                # Cancel based on order type
                if isinstance(order, BracketOrder):
                    # Cancel all bracket orders
                    if order.entry_order_id:
                        await self.broker.cancel_order(order.entry_order_id)
                    if order.stop_loss_order_id:
                        await self.broker.cancel_order(order.stop_loss_order_id)
                    if order.take_profit_1_order_id:
                        await self.broker.cancel_order(order.take_profit_1_order_id)
                    if order.take_profit_2_order_id:
                        await self.broker.cancel_order(order.take_profit_2_order_id)
                
                elif isinstance(order, OCOOrder):
                    # Cancel both OCO orders
                    if order.order_1_id:
                        await self.broker.cancel_order(order.order_1_id)
                    if order.order_2_id:
                        await self.broker.cancel_order(order.order_2_id)
                
                else:
                    # Cancel single order
                    if hasattr(order, 'order_id') and order.order_id:
                        await self.broker.cancel_order(order.order_id)
                
                # Update status
                order.status = OrderStatus.CANCELLED
                order.updated_at = datetime.now()
                
                # Move to history
                self.order_history.append(order)
                del self.active_orders[order_id]
                
                self.logger.info(f"✅ Order cancelled: {order_id}")
                return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"❌ Order cancellation failed for {order_id}: {e}")
            return False
    
    def get_active_orders(self) -> Dict[str, Any]:
        """Get all active orders"""
        return self.active_orders
    
    def get_order_history(self) -> List[Any]:
        """Get order history"""
        return self.order_history


# Factory function
async def create_advanced_order_engine(alpaca_api_key: str, alpaca_secret: str, polygon_api_key: str) -> AdvancedOrderEngine:
    """Create advanced order engine with real providers"""
    from ..broker.adapters.alpaca_paper import AlpacaPaperBroker
    from ..market.providers.polygon import PolygonProvider
    
    broker = AlpacaPaperBroker(
        api_key_id=alpaca_api_key,
        api_secret_key=alpaca_secret
    )
    
    market_provider = PolygonProvider(api_key=polygon_api_key)
    
    engine = AdvancedOrderEngine(broker, market_provider)
    await engine.start_order_monitoring()
    
    return engine
