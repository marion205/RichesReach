"""
Futures API - Simple, Jobs-style
Tomorrow: Trade tomorrow's markets today

Phase 1: Paper trading with realistic mock data
"""

from fastapi import APIRouter, HTTPException, Depends, Header
from typing import List, Optional
from pydantic import BaseModel
import logging
import time
import random
from datetime import datetime

from core.futures_service import (
    get_paper_account,
    get_recommendation_engine,
    FUTURES_CONTRACTS,
)
from core.futures_policy import get_policy_engine, SuitabilityLevel
from core.ibkr_adapter import get_ibkr_adapter
from core.futures.order_ids import client_order_id, is_duplicate_order
from core.futures.state import OrderStateMachine, OrderState
from core.futures.why_not import WhyNotResponse
from core.futures.slippage import simulate_fill, get_quote_for_symbol

logger = logging.getLogger(__name__)

futures_router = APIRouter(prefix="/api/futures", tags=["futures"])


# Simple Models
class FuturesRecommendation(BaseModel):
    symbol: str
    name: str
    why_now: str
    max_loss: float
    max_gain: float
    probability: float
    action: str  # "Buy" or "Sell"


class FuturesOrderRequest(BaseModel):
    symbol: str
    side: str  # "BUY" or "SELL"
    quantity: int
    order_type: Optional[str] = "MARKET"
    limit_price: Optional[float] = None


class FuturesOrderResponse(BaseModel):
    order_id: str
    status: str
    message: str
    client_order_id: Optional[str] = None
    why_not: Optional[Dict[str, Any]] = None  # If blocked, explains why


class FuturesPosition(BaseModel):
    symbol: str
    side: str
    quantity: int
    entry_price: float
    current_price: float
    pnl: float
    pnl_percent: float


def get_user_id(x_user_id: Optional[str] = Header(None)) -> int:
    """Get user ID from header (or default to 1 for testing)"""
    if x_user_id:
        try:
            return int(x_user_id)
        except ValueError:
            pass
    return 1  # Default for paper trading


@futures_router.get("/recommendations")
async def get_recommendations(user_id: int = Depends(get_user_id)) -> dict:
    """
    Get futures recommendations.
    Phase 1: Realistic mock data based on market conditions
    """
    try:
        engine = get_recommendation_engine()
        recs = engine.get_recommendations(user_id=user_id)
        
        return {
            "recommendations": [FuturesRecommendation(**rec) for rec in recs]
        }
    except Exception as e:
        logger.error(f"Error getting futures recommendations: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@futures_router.post("/order")
async def place_order(
    order: FuturesOrderRequest,
    user_id: int = Depends(get_user_id),
) -> FuturesOrderResponse:
    """
    Place a futures order.
    Phase 2: Policy engine checks + IBKR adapter routing
    Phase 1 fallback: Paper trading if IBKR not connected
    """
    try:
        logger.info(f"Futures order request: {order} (user_id={user_id})")
        
        # Validate
        if order.side not in ["BUY", "SELL"]:
            raise HTTPException(status_code=400, detail="Side must be BUY or SELL")
        
        if order.quantity <= 0:
            raise HTTPException(status_code=400, detail="Quantity must be > 0")
        
        # Get contract info
        symbol_base = order.symbol[:3]
        if symbol_base not in FUTURES_CONTRACTS:
            raise HTTPException(status_code=400, detail=f"Unknown contract: {symbol_base}")
        
        contract = FUTURES_CONTRACTS[symbol_base]
        
        # Generate idempotent client order ID
        client_oid = client_order_id({
            "symbol": order.symbol,
            "side": order.side,
            "quantity": order.quantity,
            "order_type": order.order_type or "MARKET",
            "limit_price": order.limit_price,
        })
        
        # Check for duplicate orders (in production, use Redis/DB)
        account = get_paper_account(user_id)
        if is_duplicate_order(client_oid, account._seen_order_ids):
            return FuturesOrderResponse(
                order_id=client_oid,
                status="duplicate",
                message="Order already submitted (idempotent check)",
                client_order_id=client_oid,
            )
        
        # Phase 3: Policy engine checks
        policy = get_policy_engine()
        user_profile = policy.get_user_profile(user_id)
        
        # Get recommendation for max_loss check
        engine = get_recommendation_engine()
        recs = engine.get_recommendations(user_id=user_id)
        recommendation = next((r for r in recs if r["symbol"] == order.symbol), None)
        
        # Get existing positions for guardrail checks
        existing_positions = account.get_positions({})  # Empty prices for guardrail check
        
        # Check guardrails with "Why not" messages
        allowed, why_not = policy.check_guardrails(
            user_profile=user_profile,
            order={
                "symbol": order.symbol,
                "side": order.side,
                "quantity": order.quantity,
            },
            existing_positions=existing_positions,
            recommendation=recommendation,
        )
        
        if not allowed:
            # Return "Why not" response
            return FuturesOrderResponse(
                order_id=client_oid,
                status="blocked",
                message=why_not.reason if why_not else "Order blocked by policy",
                client_order_id=client_oid,
                why_not=why_not.dict() if why_not else None,
            )
        
        # Phase 2: Try IBKR adapter first
        ibkr = get_ibkr_adapter()
        use_ibkr = ibkr.is_connected()
        
        # Create state machine for order
        state_machine = OrderStateMachine(client_oid, OrderState.NEW)
        state_machine.transition(OrderState.SUBMITTED, "Order submitted")
        
        if use_ibkr:
            # Route to IBKR
            try:
                ibkr_result = await ibkr.place_order(
                    symbol=order.symbol,
                    side=order.side,
                    quantity=order.quantity,
                    order_type=order.order_type or "MKT",
                    limit_price=order.limit_price,
                    client_order_id=client_oid,
                )
                
                # Update state machine
                status_map = {
                    "submitted": OrderState.SUBMITTED,
                    "filled": OrderState.FILLED,
                    "partial": OrderState.PARTIAL,
                    "canceled": OrderState.CANCELED,
                    "rejected": OrderState.REJECTED,
                }
                ibkr_state = status_map.get(ibkr_result.get("status", "submitted"), OrderState.SUBMITTED)
                state_machine.transition(ibkr_state, f"IBKR order {ibkr_result['status']}")
                
                logger.info(f"IBKR order placed: {ibkr_result['order_id']}")
                
                return FuturesOrderResponse(
                    order_id=ibkr_result.get("order_id", client_oid),
                    status=ibkr_state.value.lower(),
                    message=f"Order {ibkr_result['status']} via IBKR: {order.side} {order.quantity} {order.symbol}",
                    client_order_id=client_oid,
                )
            except Exception as e:
                logger.warning(f"IBKR order failed, falling back to paper: {e}")
                state_machine.transition(OrderState.REJECTED, f"IBKR error: {e}")
                use_ibkr = False
        
        # Phase 1 fallback: Paper trading with realistic slippage
        quote = get_quote_for_symbol(order.symbol)
        fill_price = simulate_fill(
            quote=quote,
            side=order.side,
            quantity=order.quantity,
            order_type=order.order_type or "MARKET",
            limit_price=order.limit_price,
        )
        
        # Add position to paper account
        account.add_position(
            symbol=order.symbol,
            side=order.side,
            quantity=order.quantity,
            entry_price=fill_price,
        )
        
        # Record order
        state_machine.transition(OrderState.FILLED, "Paper order filled")
        account.order_history.append({
            "order_id": client_oid,
            "client_order_id": client_oid,
            "symbol": order.symbol,
            "side": order.side,
            "quantity": order.quantity,
            "fill_price": fill_price,
            "state": state_machine.state.value,
            "timestamp": datetime.now().isoformat(),
        })
        
        logger.info(f"Paper order executed: {client_oid} @ {fill_price}")
        
        return FuturesOrderResponse(
            order_id=client_oid,
            status="filled",
            message=f"Order filled (paper): {order.side} {order.quantity} {order.symbol} @ ${fill_price:.2f}",
            client_order_id=client_oid,
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error placing futures order: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@futures_router.get("/positions")
async def get_positions(user_id: int = Depends(get_user_id)) -> dict:
    """
    Get current futures positions.
    Phase 2: Try IBKR first, fallback to paper trading
    """
    try:
        # Phase 2: Try IBKR first
        ibkr = get_ibkr_adapter()
        if ibkr.is_connected():
            try:
                ibkr_positions = await ibkr.get_positions()
                if ibkr_positions:
                    return {
                        "positions": [FuturesPosition(**pos) for pos in ibkr_positions],
                        "source": "ibkr",
                    }
            except Exception as e:
                logger.warning(f"Failed to get IBKR positions: {e}")
        
        # Phase 1 fallback: Paper trading
        account = get_paper_account(user_id)
        
        # Get market data from IBKR if available, otherwise simulate
        current_prices = {}
        for symbol in account.positions.keys():
            if ibkr.is_connected():
                market_data = await ibkr.get_market_data(symbol)
                current_prices[symbol] = market_data.get("last", 5000.0)
            else:
                # Simulate current prices
                symbol_base = symbol[:3]
                if symbol_base in FUTURES_CONTRACTS:
                    base_price = 5000.0
                    price_change = random.uniform(-10, 10)
                    current_prices[symbol] = base_price + price_change
        
        positions = account.get_positions(current_prices)
        
        return {
            "positions": [FuturesPosition(**pos) for pos in positions],
            "account_balance": account.balance,
            "total_pnl": sum(p["pnl"] for p in positions),
            "source": "paper",
        }
    except Exception as e:
        logger.error(f"Error getting futures positions: {e}")
        raise HTTPException(status_code=500, detail=str(e))

