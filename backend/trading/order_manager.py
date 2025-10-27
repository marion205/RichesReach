from typing import Dict, List, Any, Optional, Union
from datetime import datetime, timedelta
from enum import Enum
import random
import json

class OrderType(Enum):
    MARKET = "market"
    LIMIT = "limit"
    STOP = "stop"
    STOP_LIMIT = "stop_limit"
    TRAILING_STOP = "trailing_stop"
    BRACKET = "bracket"
    OCO = "oco"  # One-Cancels-Other
    ICEBERG = "iceberg"
    TWAP = "twap"  # Time-Weighted Average Price
    VWAP = "vwap"  # Volume-Weighted Average Price

class OrderSide(Enum):
    BUY = "buy"
    SELL = "sell"

class OrderStatus(Enum):
    PENDING = "pending"
    SUBMITTED = "submitted"
    PARTIALLY_FILLED = "partially_filled"
    FILLED = "filled"
    CANCELLED = "cancelled"
    REJECTED = "rejected"
    EXPIRED = "expired"

class TimeInForce(Enum):
    DAY = "day"
    GTC = "gtc"  # Good Till Cancelled
    IOC = "ioc"  # Immediate or Cancel
    FOK = "fok"  # Fill or Kill
    GTD = "gtd"  # Good Till Date

class OrderManager:
    """
    Advanced order management system with sophisticated order types,
    risk management, and execution algorithms.
    """
    
    def __init__(self):
        self.orders = {}
        self.order_counter = 1000
        self.execution_algorithms = {
            "twap": self._execute_twap,
            "vwap": self._execute_vwap,
            "iceberg": self._execute_iceberg,
            "bracket": self._execute_bracket,
            "oco": self._execute_oco
        }
        
    def place_order(self, order_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Place a new order with advanced order types and risk management.
        """
        order_id = f"ORD_{self.order_counter}"
        self.order_counter += 1
        
        # Validate order data
        validation_result = self._validate_order(order_data)
        if not validation_result["valid"]:
            return {
                "success": False,
                "order_id": None,
                "error": validation_result["error"],
                "rejection_reason": validation_result["rejection_reason"]
            }
        
        # Create order object
        order = {
            "order_id": order_id,
            "symbol": order_data["symbol"],
            "side": order_data["side"],
            "quantity": order_data["quantity"],
            "order_type": order_data["order_type"],
            "price": order_data.get("price"),
            "stop_price": order_data.get("stop_price"),
            "time_in_force": order_data.get("time_in_force", "day"),
            "status": OrderStatus.PENDING.value,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "filled_quantity": 0,
            "average_fill_price": None,
            "commission": 0.0,
            "fees": 0.0,
            "metadata": order_data.get("metadata", {}),
            "risk_checks": self._perform_risk_checks(order_data),
            "execution_plan": self._create_execution_plan(order_data)
        }
        
        # Store order
        self.orders[order_id] = order
        
        # Execute order based on type
        execution_result = self._execute_order(order)
        
        return {
            "success": True,
            "order_id": order_id,
            "order": order,
            "execution_result": execution_result
        }
    
    def _validate_order(self, order_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate order data and perform compliance checks."""
        required_fields = ["symbol", "side", "quantity", "order_type"]
        
        for field in required_fields:
            if field not in order_data:
                return {
                    "valid": False,
                    "error": f"Missing required field: {field}",
                    "rejection_reason": "INVALID_ORDER_DATA"
                }
        
        # Validate order type
        try:
            OrderType(order_data["order_type"])
        except ValueError:
            return {
                "valid": False,
                "error": f"Invalid order type: {order_data['order_type']}",
                "rejection_reason": "INVALID_ORDER_TYPE"
            }
        
        # Validate side
        try:
            OrderSide(order_data["side"])
        except ValueError:
            return {
                "valid": False,
                "error": f"Invalid order side: {order_data['side']}",
                "rejection_reason": "INVALID_ORDER_SIDE"
            }
        
        # Validate quantity
        if order_data["quantity"] <= 0:
            return {
                "valid": False,
                "error": "Quantity must be positive",
                "rejection_reason": "INVALID_QUANTITY"
            }
        
        # Validate price for limit orders
        if order_data["order_type"] in ["limit", "stop_limit"] and not order_data.get("price"):
            return {
                "valid": False,
                "error": "Price required for limit orders",
                "rejection_reason": "MISSING_PRICE"
            }
        
        # Validate stop price for stop orders
        if order_data["order_type"] in ["stop", "stop_limit"] and not order_data.get("stop_price"):
            return {
                "valid": False,
                "error": "Stop price required for stop orders",
                "rejection_reason": "MISSING_STOP_PRICE"
            }
        
        return {"valid": True, "error": None, "rejection_reason": None}
    
    def _perform_risk_checks(self, order_data: Dict[str, Any]) -> Dict[str, Any]:
        """Perform comprehensive risk checks on the order."""
        symbol = order_data["symbol"]
        quantity = order_data["quantity"]
        side = order_data["side"]
        
        # Mock risk checks
        risk_score = random.uniform(0.1, 0.9)
        position_size_limit = random.uniform(1000, 10000)
        daily_loss_limit = random.uniform(5000, 50000)
        
        checks = {
            "risk_score": risk_score,
            "position_size_check": {
                "passed": quantity <= position_size_limit,
                "limit": position_size_limit,
                "current_position": random.uniform(0, position_size_limit * 0.8)
            },
            "daily_loss_check": {
                "passed": True,  # Mock - would check actual daily P&L
                "limit": daily_loss_limit,
                "current_loss": random.uniform(0, daily_loss_limit * 0.3)
            },
            "volatility_check": {
                "passed": risk_score < 0.8,
                "volatility": random.uniform(0.1, 0.5),
                "threshold": 0.5
            },
            "liquidity_check": {
                "passed": True,
                "average_volume": random.uniform(1000000, 10000000),
                "order_size_percentage": (quantity / random.uniform(1000000, 10000000)) * 100
            },
            "market_hours_check": {
                "passed": True,  # Mock - would check actual market hours
                "is_market_open": True
            }
        }
        
        return checks
    
    def _create_execution_plan(self, order_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create execution plan based on order type and market conditions."""
        order_type = order_data["order_type"]
        
        if order_type == "twap":
            return {
                "algorithm": "twap",
                "duration_minutes": order_data.get("duration_minutes", 60),
                "slices": order_data.get("slices", 10),
                "min_slice_size": order_data["quantity"] // 20,
                "max_slice_size": order_data["quantity"] // 5
            }
        elif order_type == "vwap":
            return {
                "algorithm": "vwap",
                "participation_rate": order_data.get("participation_rate", 0.1),
                "max_slice_size": order_data["quantity"] // 10,
                "min_slice_interval": 30  # seconds
            }
        elif order_type == "iceberg":
            return {
                "algorithm": "iceberg",
                "display_size": order_data.get("display_size", order_data["quantity"] // 10),
                "refresh_threshold": 0.8,
                "min_refresh_size": order_data["quantity"] // 20
            }
        elif order_type == "bracket":
            return {
                "algorithm": "bracket",
                "take_profit_price": order_data.get("take_profit_price"),
                "stop_loss_price": order_data.get("stop_loss_price"),
                "take_profit_quantity": order_data["quantity"],
                "stop_loss_quantity": order_data["quantity"]
            }
        elif order_type == "oco":
            return {
                "algorithm": "oco",
                "take_profit_order": {
                    "price": order_data.get("take_profit_price"),
                    "quantity": order_data["quantity"]
                },
                "stop_loss_order": {
                    "stop_price": order_data.get("stop_loss_price"),
                    "quantity": order_data["quantity"]
                }
            }
        else:
            return {
                "algorithm": "immediate",
                "execution_type": "market" if order_type == "market" else "limit"
            }
    
    def _execute_order(self, order: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the order based on its type and execution plan."""
        order_type = order["order_type"]
        
        if order_type in self.execution_algorithms:
            return self.execution_algorithms[order_type](order)
        else:
            return self._execute_immediate(order)
    
    def _execute_immediate(self, order: Dict[str, Any]) -> Dict[str, Any]:
        """Execute immediate orders (market, limit, stop)."""
        # Mock immediate execution
        fill_probability = random.uniform(0.7, 0.95)
        
        if random.random() < fill_probability:
            # Order filled
            filled_quantity = order["quantity"]
            fill_price = self._get_fill_price(order)
            
            order["status"] = OrderStatus.FILLED.value
            order["filled_quantity"] = filled_quantity
            order["average_fill_price"] = fill_price
            order["updated_at"] = datetime.now().isoformat()
            
            return {
                "execution_type": "immediate",
                "status": "filled",
                "filled_quantity": filled_quantity,
                "fill_price": fill_price,
                "execution_time": datetime.now().isoformat()
            }
        else:
            # Order pending
            order["status"] = OrderStatus.SUBMITTED.value
            order["updated_at"] = datetime.now().isoformat()
            
            return {
                "execution_type": "immediate",
                "status": "submitted",
                "filled_quantity": 0,
                "fill_price": None,
                "execution_time": datetime.now().isoformat()
            }
    
    def _execute_twap(self, order: Dict[str, Any]) -> Dict[str, Any]:
        """Execute TWAP (Time-Weighted Average Price) order."""
        execution_plan = order["execution_plan"]
        duration_minutes = execution_plan["duration_minutes"]
        slices = execution_plan["slices"]
        slice_size = order["quantity"] // slices
        
        # Mock TWAP execution
        total_filled = 0
        slice_fills = []
        
        for i in range(slices):
            slice_fill_probability = random.uniform(0.8, 0.95)
            if random.random() < slice_fill_probability:
                slice_fill = slice_size
                total_filled += slice_fill
                slice_fills.append({
                    "slice": i + 1,
                    "quantity": slice_fill,
                    "price": self._get_fill_price(order),
                    "timestamp": datetime.now().isoformat()
                })
        
        if total_filled > 0:
            order["status"] = OrderStatus.PARTIALLY_FILLED.value if total_filled < order["quantity"] else OrderStatus.FILLED.value
            order["filled_quantity"] = total_filled
            order["average_fill_price"] = sum(s["price"] for s in slice_fills) / len(slice_fills)
            order["updated_at"] = datetime.now().isoformat()
        
        return {
            "execution_type": "twap",
            "status": "executing",
            "total_slices": slices,
            "completed_slices": len(slice_fills),
            "filled_quantity": total_filled,
            "slice_fills": slice_fills,
            "execution_time": datetime.now().isoformat()
        }
    
    def _execute_vwap(self, order: Dict[str, Any]) -> Dict[str, Any]:
        """Execute VWAP (Volume-Weighted Average Price) order."""
        execution_plan = order["execution_plan"]
        participation_rate = execution_plan["participation_rate"]
        
        # Mock VWAP execution
        market_volume = random.uniform(1000000, 5000000)
        target_volume = market_volume * participation_rate
        filled_quantity = min(order["quantity"], int(target_volume))
        
        if filled_quantity > 0:
            order["status"] = OrderStatus.PARTIALLY_FILLED.value if filled_quantity < order["quantity"] else OrderStatus.FILLED.value
            order["filled_quantity"] = filled_quantity
            order["average_fill_price"] = self._get_fill_price(order)
            order["updated_at"] = datetime.now().isoformat()
        
        return {
            "execution_type": "vwap",
            "status": "executing",
            "participation_rate": participation_rate,
            "market_volume": market_volume,
            "target_volume": target_volume,
            "filled_quantity": filled_quantity,
            "execution_time": datetime.now().isoformat()
        }
    
    def _execute_iceberg(self, order: Dict[str, Any]) -> Dict[str, Any]:
        """Execute Iceberg order."""
        execution_plan = order["execution_plan"]
        display_size = execution_plan["display_size"]
        
        # Mock iceberg execution
        filled_quantity = min(display_size, order["quantity"])
        
        if filled_quantity > 0:
            order["status"] = OrderStatus.PARTIALLY_FILLED.value if filled_quantity < order["quantity"] else OrderStatus.FILLED.value
            order["filled_quantity"] = filled_quantity
            order["average_fill_price"] = self._get_fill_price(order)
            order["updated_at"] = datetime.now().isoformat()
        
        return {
            "execution_type": "iceberg",
            "status": "executing",
            "display_size": display_size,
            "hidden_quantity": order["quantity"] - display_size,
            "filled_quantity": filled_quantity,
            "execution_time": datetime.now().isoformat()
        }
    
    def _execute_bracket(self, order: Dict[str, Any]) -> Dict[str, Any]:
        """Execute Bracket order."""
        execution_plan = order["execution_plan"]
        
        # Create main order
        main_order_result = self._execute_immediate(order)
        
        # Create take profit and stop loss orders
        take_profit_price = execution_plan["take_profit_price"]
        stop_loss_price = execution_plan["stop_loss_price"]
        
        bracket_orders = {
            "main_order": {
                "order_id": order["order_id"],
                "status": main_order_result["status"],
                "filled_quantity": main_order_result["filled_quantity"]
            },
            "take_profit_order": {
                "order_id": f"{order['order_id']}_TP",
                "price": take_profit_price,
                "quantity": execution_plan["take_profit_quantity"],
                "status": "pending"
            },
            "stop_loss_order": {
                "order_id": f"{order['order_id']}_SL",
                "stop_price": stop_loss_price,
                "quantity": execution_plan["stop_loss_quantity"],
                "status": "pending"
            }
        }
        
        return {
            "execution_type": "bracket",
            "status": "active",
            "bracket_orders": bracket_orders,
            "execution_time": datetime.now().isoformat()
        }
    
    def _execute_oco(self, order: Dict[str, Any]) -> Dict[str, Any]:
        """Execute OCO (One-Cancels-Other) order."""
        execution_plan = order["execution_plan"]
        
        # Mock OCO execution
        take_profit_order = execution_plan["take_profit_order"]
        stop_loss_order = execution_plan["stop_loss_order"]
        
        # Simulate one order triggering
        triggered_order = random.choice(["take_profit", "stop_loss"])
        
        oco_orders = {
            "take_profit_order": {
                "order_id": f"{order['order_id']}_TP",
                "price": take_profit_order["price"],
                "quantity": take_profit_order["quantity"],
                "status": "filled" if triggered_order == "take_profit" else "cancelled"
            },
            "stop_loss_order": {
                "order_id": f"{order['order_id']}_SL",
                "stop_price": stop_loss_order["stop_price"],
                "quantity": stop_loss_order["quantity"],
                "status": "filled" if triggered_order == "stop_loss" else "cancelled"
            }
        }
        
        return {
            "execution_type": "oco",
            "status": "completed",
            "triggered_order": triggered_order,
            "oco_orders": oco_orders,
            "execution_time": datetime.now().isoformat()
        }
    
    def _get_fill_price(self, order: Dict[str, Any]) -> float:
        """Get realistic fill price based on order type and market conditions."""
        base_price = random.uniform(100, 500)  # Mock base price
        
        if order["order_type"] == "market":
            # Market orders get filled at current market price with slight slippage
            slippage = random.uniform(-0.01, 0.01)
            return base_price * (1 + slippage)
        elif order["order_type"] == "limit":
            # Limit orders get filled at or better than limit price
            limit_price = order.get("price", base_price)
            if order["side"] == "buy":
                return min(limit_price, base_price * random.uniform(0.995, 1.005))
            else:
                return max(limit_price, base_price * random.uniform(0.995, 1.005))
        else:
            return base_price
    
    def get_order_status(self, order_id: str) -> Dict[str, Any]:
        """Get current status of an order."""
        if order_id not in self.orders:
            return {
                "success": False,
                "error": "Order not found",
                "order": None
            }
        
        order = self.orders[order_id]
        return {
            "success": True,
            "order": order
        }
    
    def cancel_order(self, order_id: str) -> Dict[str, Any]:
        """Cancel an existing order."""
        if order_id not in self.orders:
            return {
                "success": False,
                "error": "Order not found"
            }
        
        order = self.orders[order_id]
        
        if order["status"] in ["filled", "cancelled", "rejected"]:
            return {
                "success": False,
                "error": f"Cannot cancel order in {order['status']} status"
            }
        
        order["status"] = OrderStatus.CANCELLED.value
        order["updated_at"] = datetime.now().isoformat()
        
        return {
            "success": True,
            "order_id": order_id,
            "status": "cancelled",
            "cancelled_at": datetime.now().isoformat()
        }
    
    def get_orders(self, filters: Dict[str, Any] = None) -> Dict[str, Any]:
        """Get orders with optional filtering."""
        orders = list(self.orders.values())
        
        if filters:
            if "status" in filters:
                orders = [o for o in orders if o["status"] == filters["status"]]
            if "symbol" in filters:
                orders = [o for o in orders if o["symbol"] == filters["symbol"]]
            if "side" in filters:
                orders = [o for o in orders if o["side"] == filters["side"]]
            if "order_type" in filters:
                orders = [o for o in orders if o["order_type"] == filters["order_type"]]
        
        return {
            "success": True,
            "orders": orders,
            "total_count": len(orders)
        }
    
    def get_order_analytics(self) -> Dict[str, Any]:
        """Get comprehensive order analytics."""
        orders = list(self.orders.values())
        
        if not orders:
            return {
                "success": True,
                "analytics": {
                    "total_orders": 0,
                    "filled_orders": 0,
                    "pending_orders": 0,
                    "cancelled_orders": 0,
                    "fill_rate": 0.0,
                    "average_fill_time": 0.0,
                    "order_types": {},
                    "symbols": {},
                    "execution_algorithms": {}
                }
            }
        
        # Calculate analytics
        total_orders = len(orders)
        filled_orders = len([o for o in orders if o["status"] == "filled"])
        pending_orders = len([o for o in orders if o["status"] in ["pending", "submitted", "partially_filled"]])
        cancelled_orders = len([o for o in orders if o["status"] == "cancelled"])
        
        fill_rate = filled_orders / total_orders if total_orders > 0 else 0.0
        
        # Order types distribution
        order_types = {}
        for order in orders:
            order_type = order["order_type"]
            order_types[order_type] = order_types.get(order_type, 0) + 1
        
        # Symbols distribution
        symbols = {}
        for order in orders:
            symbol = order["symbol"]
            symbols[symbol] = symbols.get(symbol, 0) + 1
        
        # Execution algorithms distribution
        execution_algorithms = {}
        for order in orders:
            if "execution_plan" in order:
                algorithm = order["execution_plan"].get("algorithm", "immediate")
                execution_algorithms[algorithm] = execution_algorithms.get(algorithm, 0) + 1
        
        return {
            "success": True,
            "analytics": {
                "total_orders": total_orders,
                "filled_orders": filled_orders,
                "pending_orders": pending_orders,
                "cancelled_orders": cancelled_orders,
                "fill_rate": fill_rate,
                "average_fill_time": random.uniform(30, 300),  # Mock average fill time in seconds
                "order_types": order_types,
                "symbols": symbols,
                "execution_algorithms": execution_algorithms,
                "risk_metrics": {
                    "average_risk_score": random.uniform(0.3, 0.7),
                    "high_risk_orders": len([o for o in orders if o.get("risk_checks", {}).get("risk_score", 0) > 0.7]),
                    "rejected_orders": len([o for o in orders if o["status"] == "rejected"])
                }
            }
        }
    
    def get_position_summary(self, symbol: str = None) -> Dict[str, Any]:
        """Get position summary for a symbol or all symbols."""
        orders = list(self.orders.values())
        
        if symbol:
            orders = [o for o in orders if o["symbol"] == symbol]
        
        # Calculate positions
        positions = {}
        for order in orders:
            sym = order["symbol"]
            if sym not in positions:
                positions[sym] = {"quantity": 0, "average_price": 0, "unrealized_pnl": 0}
            
            if order["status"] == "filled":
                filled_qty = order["filled_quantity"]
                fill_price = order["average_fill_price"]
                
                if order["side"] == "buy":
                    positions[sym]["quantity"] += filled_qty
                    positions[sym]["average_price"] = (
                        (positions[sym]["average_price"] * (positions[sym]["quantity"] - filled_qty) + 
                         fill_price * filled_qty) / positions[sym]["quantity"]
                    )
                else:
                    positions[sym]["quantity"] -= filled_qty
        
        # Calculate unrealized P&L (mock)
        for sym, pos in positions.items():
            current_price = random.uniform(100, 500)  # Mock current price
            pos["unrealized_pnl"] = (current_price - pos["average_price"]) * pos["quantity"]
            pos["current_price"] = current_price
        
        return {
            "success": True,
            "positions": positions,
            "total_positions": len(positions),
            "total_unrealized_pnl": sum(pos["unrealized_pnl"] for pos in positions.values())
        }
