"""
Futures API - Simple, Jobs-style
Tomorrow: Trade tomorrow's markets today
"""

from fastapi import APIRouter, HTTPException, Depends
from typing import List, Optional
from pydantic import BaseModel
import logging

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


# Mock data for now (will wire to IBKR adapter later)
MOCK_RECOMMENDATIONS = [
    {
        "symbol": "MESZ5",
        "name": "Micro E-mini S&P 500",
        "why_now": "Calm market. Hedge portfolio with micro contract—max loss $50.",
        "max_loss": 50.0,
        "max_gain": 250.0,
        "probability": 68.0,
        "action": "Buy",
    },
    {
        "symbol": "MNQZ5",
        "name": "Micro E-mini Nasdaq-100",
        "why_now": "Tech momentum strong. Small position for exposure.",
        "max_loss": 75.0,
        "max_gain": 300.0,
        "probability": 72.0,
        "action": "Buy",
    },
]


@futures_router.get("/recommendations")
async def get_recommendations() -> dict:
    """
    Get futures recommendations.
    Simple: One sentence, one visual, one action.
    """
    try:
        # TODO: Wire to policy engine + ML service
        # For now, return mock data
        return {
            "recommendations": [
                FuturesRecommendation(**rec) for rec in MOCK_RECOMMENDATIONS
            ]
        }
    except Exception as e:
        logger.error(f"Error getting futures recommendations: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@futures_router.post("/order")
async def place_order(order: FuturesOrderRequest) -> FuturesOrderResponse:
    """
    Place a futures order.
    Simple: Symbol, side, quantity.
    """
    try:
        # TODO: Wire to IBKR adapter
        # For now, return mock response
        logger.info(f"Futures order request: {order}")
        
        # Validate
        if order.side not in ["BUY", "SELL"]:
            raise HTTPException(status_code=400, detail="Side must be BUY or SELL")
        
        if order.quantity <= 0:
            raise HTTPException(status_code=400, detail="Quantity must be > 0")
        
        # Mock order placement
        order_id = f"FUT_{order.symbol}_{order.side}_{order.quantity}_{int(__import__('time').time())}"
        
        return FuturesOrderResponse(
            order_id=order_id,
            status="submitted",
            message=f"Order submitted: {order.side} {order.quantity} {order.symbol}",
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error placing futures order: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@futures_router.get("/positions")
async def get_positions() -> dict:
    """
    Get current futures positions.
    """
    try:
        # TODO: Wire to IBKR adapter
        return {"positions": []}
    except Exception as e:
        logger.error(f"Error getting futures positions: {e}")
        raise HTTPException(status_code=500, detail=str(e))

