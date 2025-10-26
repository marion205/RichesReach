"""
Alpaca Paper Trading Broker Integration
Real paper trading with Alpaca's sandbox environment
"""

import asyncio
import aiohttp
from typing import Dict, List, Optional
from datetime import datetime
import logging

from .base import Broker, Order, Position, Account, OrderSide, OrderType, TimeInForce, OrderStatus


class AlpacaPaperBroker(Broker):
    """Alpaca Paper Trading broker implementation"""
    
    def __init__(self, api_key_id: str, api_secret_key: str, base_url: str = "https://paper-api.alpaca.markets"):
        self.api_key_id = api_key_id
        self.api_secret_key = api_secret_key
        self.base_url = base_url
        self.session = None
        self.logger = logging.getLogger(__name__)
    
    async def _get_session(self):
        """Get or create aiohttp session with auth headers"""
        if self.session is None or self.session.closed:
            headers = {
                "APCA-API-KEY-ID": self.api_key_id,
                "APCA-API-SECRET-KEY": self.api_secret_key,
                "Content-Type": "application/json"
            }
            self.session = aiohttp.ClientSession(headers=headers)
        return self.session
    
    async def _make_request(self, method: str, endpoint: str, data: Dict = None) -> Dict:
        """Make authenticated request to Alpaca API"""
        session = await self._get_session()
        url = f"{self.base_url}{endpoint}"
        
        try:
            if method.upper() == "GET":
                async with session.get(url) as response:
                    if response.status == 200:
                        return await response.json()
                    else:
                        error_text = await response.text()
                        self.logger.error(f"Alpaca API error: {response.status} - {error_text}")
                        return {}
            elif method.upper() == "POST":
                async with session.post(url, json=data) as response:
                    if response.status in [200, 201]:
                        return await response.json()
                    else:
                        error_text = await response.text()
                        self.logger.error(f"Alpaca API error: {response.status} - {error_text}")
                        return {}
            elif method.upper() == "DELETE":
                async with session.delete(url) as response:
                    if response.status == 200:
                        return await response.json()
                    else:
                        error_text = await response.text()
                        self.logger.error(f"Alpaca API error: {response.status} - {error_text}")
                        return {}
        except Exception as e:
            self.logger.error(f"Alpaca request failed: {e}")
            return {}
    
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
        """Place an order through Alpaca"""
        
        # Map our enums to Alpaca format
        alpaca_side = "buy" if side == OrderSide.BUY else "sell"
        alpaca_type = order_type.value
        alpaca_tif = time_in_force.value
        
        order_data = {
            "symbol": symbol,
            "qty": str(quantity),
            "side": alpaca_side,
            "type": alpaca_type,
            "time_in_force": alpaca_tif
        }
        
        if limit_price:
            order_data["limit_price"] = str(limit_price)
        if stop_price:
            order_data["stop_price"] = str(stop_price)
        if client_order_id:
            order_data["client_order_id"] = client_order_id
        
        # Handle bracket orders (OCO)
        if bracket_orders:
            order_data["order_class"] = "bracket"
            order_data["take_profit"] = {
                "limit_price": str(bracket_orders.get("take_profit", 0))
            }
            order_data["stop_loss"] = {
                "stop_price": str(bracket_orders.get("stop_loss", 0))
            }
        
        response = await self._make_request("POST", "/v2/orders", order_data)
        
        if response:
            return Order(
                id=response["id"],
                symbol=response["symbol"],
                side=OrderSide.BUY if response["side"] == "buy" else OrderSide.SELL,
                type=OrderType(response["order_type"]),
                quantity=int(response["qty"]),
                status=OrderStatus(response["status"]),
                filled_quantity=int(response.get("filled_qty", 0)),
                remaining_quantity=int(response.get("qty", 0)) - int(response.get("filled_qty", 0)),
                limit_price=float(response["limit_price"]) if response.get("limit_price") else None,
                stop_price=float(response["stop_price"]) if response.get("stop_price") else None,
                average_fill_price=float(response["filled_avg_price"]) if response.get("filled_avg_price") else None,
                time_in_force=TimeInForce(response["time_in_force"]),
                created_at=datetime.fromisoformat(response["created_at"].replace("Z", "+00:00")),
                updated_at=datetime.fromisoformat(response["updated_at"].replace("Z", "+00:00")),
                client_order_id=response.get("client_order_id")
            )
        else:
            # Return a failed order
            return Order(
                id="failed",
                symbol=symbol,
                side=side,
                type=order_type,
                quantity=quantity,
                status=OrderStatus.REJECTED,
                created_at=datetime.now()
            )
    
    async def cancel_order(self, order_id: str) -> Dict[str, str]:
        """Cancel an order"""
        response = await self._make_request("DELETE", f"/v2/orders/{order_id}")
        
        if response:
            return {"status": "success", "message": "Order canceled"}
        return {"status": "error", "message": "Failed to cancel order"}
    
    async def get_order(self, order_id: str) -> Order:
        """Get order details"""
        response = await self._make_request("GET", f"/v2/orders/{order_id}")
        
        if response:
            return Order(
                id=response["id"],
                symbol=response["symbol"],
                side=OrderSide.BUY if response["side"] == "buy" else OrderSide.SELL,
                type=OrderType(response["order_type"]),
                quantity=int(response["qty"]),
                status=OrderStatus(response["status"]),
                filled_quantity=int(response.get("filled_qty", 0)),
                remaining_quantity=int(response.get("qty", 0)) - int(response.get("filled_qty", 0)),
                limit_price=float(response["limit_price"]) if response.get("limit_price") else None,
                stop_price=float(response["stop_price"]) if response.get("stop_price") else None,
                average_fill_price=float(response["filled_avg_price"]) if response.get("filled_avg_price") else None,
                time_in_force=TimeInForce(response["time_in_force"]),
                created_at=datetime.fromisoformat(response["created_at"].replace("Z", "+00:00")),
                updated_at=datetime.fromisoformat(response["updated_at"].replace("Z", "+00:00")),
                client_order_id=response.get("client_order_id")
            )
        return None
    
    async def get_orders(self, status: Optional[OrderStatus] = None) -> List[Order]:
        """Get all orders"""
        endpoint = "/v2/orders"
        if status:
            endpoint += f"?status={status.value}"
        
        response = await self._make_request("GET", endpoint)
        
        orders = []
        if response and isinstance(response, list):
            for order_data in response:
                orders.append(Order(
                    id=order_data["id"],
                    symbol=order_data["symbol"],
                    side=OrderSide.BUY if order_data["side"] == "buy" else OrderSide.SELL,
                    type=OrderType(order_data["order_type"]),
                    quantity=int(order_data["qty"]),
                    status=OrderStatus(order_data["status"]),
                    filled_quantity=int(order_data.get("filled_qty", 0)),
                    remaining_quantity=int(order_data.get("qty", 0)) - int(order_data.get("filled_qty", 0)),
                    limit_price=float(order_data["limit_price"]) if order_data.get("limit_price") else None,
                    stop_price=float(order_data["stop_price"]) if order_data.get("stop_price") else None,
                    average_fill_price=float(order_data["filled_avg_price"]) if order_data.get("filled_avg_price") else None,
                    time_in_force=TimeInForce(order_data["time_in_force"]),
                    created_at=datetime.fromisoformat(order_data["created_at"].replace("Z", "+00:00")),
                    updated_at=datetime.fromisoformat(order_data["updated_at"].replace("Z", "+00:00")),
                    client_order_id=order_data.get("client_order_id")
                ))
        
        return orders
    
    async def get_positions(self) -> List[Position]:
        """Get all positions"""
        response = await self._make_request("GET", "/v2/positions")
        
        positions = []
        if response and isinstance(response, list):
            for pos_data in response:
                positions.append(Position(
                    symbol=pos_data["symbol"],
                    quantity=int(pos_data["qty"]),
                    side="long" if int(pos_data["qty"]) > 0 else "short",
                    market_value=float(pos_data["market_value"]),
                    cost_basis=float(pos_data["cost_basis"]),
                    unrealized_pl=float(pos_data["unrealized_pl"]),
                    unrealized_plpc=float(pos_data["unrealized_plpc"]),
                    current_price=float(pos_data["current_price"]),
                    lastday_price=float(pos_data["lastday_price"]),
                    change_today=float(pos_data["change_today"])
                ))
        
        return positions
    
    async def get_position(self, symbol: str) -> Optional[Position]:
        """Get position for specific symbol"""
        response = await self._make_request("GET", f"/v2/positions/{symbol}")
        
        if response:
            return Position(
                symbol=response["symbol"],
                quantity=int(response["qty"]),
                side="long" if int(response["qty"]) > 0 else "short",
                market_value=float(response["market_value"]),
                cost_basis=float(response["cost_basis"]),
                unrealized_pl=float(response["unrealized_pl"]),
                unrealized_plpc=float(response["unrealized_plpc"]),
                current_price=float(response["current_price"]),
                lastday_price=float(response["lastday_price"]),
                change_today=float(response["change_today"])
            )
        return None
    
    async def get_account(self) -> Account:
        """Get account information"""
        response = await self._make_request("GET", "/v2/account")
        
        if response:
            return Account(
                account_id=response["id"],
                buying_power=float(response["buying_power"]),
                cash=float(response["cash"]),
                portfolio_value=float(response["portfolio_value"]),
                equity=float(response["equity"]),
                long_market_value=float(response["long_market_value"]),
                short_market_value=float(response["short_market_value"]),
                initial_margin=float(response["initial_margin"]),
                maintenance_margin=float(response["maintenance_margin"]),
                day_trade_count=int(response["day_trade_count"]),
                pattern_day_trader=response["pattern_day_trader"],
                day_trading_buying_power=float(response["day_trading_buying_power"])
            )
        return None
    
    async def get_market_data(self, symbols: List[str]) -> Dict[str, Dict]:
        """Get real-time market data"""
        symbols_str = ",".join(symbols)
        response = await self._make_request("GET", f"/v2/stocks/quotes/latest?symbols={symbols_str}")
        
        market_data = {}
        if response and "quotes" in response:
            for symbol, quote_data in response["quotes"].items():
                market_data[symbol] = {
                    "price": float(quote_data["ap"]),  # ask price
                    "bid": float(quote_data["bp"]),    # bid price
                    "ask": float(quote_data["ap"]),    # ask price
                    "volume": int(quote_data.get("v", 0)),
                    "timestamp": quote_data["t"]
                }
        
        return market_data
    
    async def close(self):
        """Close the session"""
        if self.session and not self.session.closed:
            await self.session.close()
