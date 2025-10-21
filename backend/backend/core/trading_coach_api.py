"""
Trading Coach API Router
"""

from __future__ import annotations

import asyncio
import logging
import uuid
from functools import lru_cache
from typing import Any, Dict, List, Optional, Literal

from fastapi import APIRouter, Depends, Header, HTTPException, Response
from pydantic import BaseModel, Field

from .trading_coach_service import TradingCoachService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/coach", tags=["Trading Coach"])

@router.get("/test")
async def test_endpoint():
    return {"message": "Trading Coach API is working!", "strategies_count": 3}

# ---------------- DI singleton ----------------
# @lru_cache  # Removed cache to allow hot-reloading
def get_coach() -> TradingCoachService:
    return TradingCoachService()

# ---------------- Schemas ----------------
RiskTol = Literal["low", "medium", "high"]
Horizon = Literal["short", "medium", "long"]

class AdviseRequest(BaseModel):
    user_id: str = Field(..., description="User identifier")
    goal: str = Field(..., description="High-level goal (e.g., 'grow capital steadily')")
    risk_tolerance: RiskTol = Field(..., description="low|medium|high")
    horizon: Horizon = Field(..., description="short|medium|long")
    context: Optional[Dict[str, Any]] = Field(None, description="Optional portfolio/market context")

class AdviceResponse(BaseModel):
    overview: str = ""
    risk_considerations: List[str] = []
    controls: List[str] = []
    next_steps: List[str] = []
    disclaimer: str
    generated_at: str
    model: Optional[str] = None
    confidence_score: Optional[float] = None

class StrategyRequest(BaseModel):
    user_id: str
    objective: str = Field(..., description="Objective (e.g., 'income', 'growth', 'hedge')")
    market_view: str = Field(..., description="Plain-English view (e.g., 'moderately bullish 3-6m')")
    constraints: Optional[Dict[str, Any]] = Field(None, description="E.g., max drawdown, max leverage, etc.")

class StrategyOption(BaseModel):
    name: str = ""
    when_to_use: str = ""
    pros: List[str] = []
    cons: List[str] = []
    risk_controls: List[str] = []
    metrics: List[str] = []

class StrategyResponse(BaseModel):
    strategies: List[StrategyOption] = []
    disclaimer: str
    generated_at: str
    model: Optional[str] = None
    confidence_score: Optional[float] = None

# ---------------- Error mapping ----------------
def _raise_http(e: Exception) -> None:
    if isinstance(e, HTTPException):
        raise e
    if isinstance(e, asyncio.TimeoutError):
        raise HTTPException(status_code=504, detail="Request to AI router timed out") from e
    if isinstance(e, ValueError):
        raise HTTPException(status_code=400, detail=str(e)) from e
    logger.exception("Trading Coach API error: %s", e)
    raise HTTPException(status_code=500, detail="Internal server error") from e

# ---------------- Endpoints ----------------
@router.post(
    "/advise",
    response_model=AdviceResponse,
    response_model_exclude_none=True,
    summary="Educational guidance with risks, controls, and next steps",
)
async def advise(
    req: AdviseRequest,
    response: Response,
    coach: TradingCoachService = Depends(get_coach),
    x_request_id: Optional[str] = Header(default=None, convert_underscores=False),
):
    try:
        request_id = x_request_id or str(uuid.uuid4())
        response.headers["X-Request-ID"] = request_id
        payload = await coach.advise(
            user_id=req.user_id,
            goal=req.goal.strip(),
            risk_tolerance=req.risk_tolerance,
            horizon=req.horizon,
            context={**(req.context or {}), "request_id": request_id},
        )
        return AdviceResponse(**payload)
    except Exception as e:
        # Check if this is a retryable error that should be handled by the AI router
        if "temperature" in str(e) or "credit balance" in str(e) or "unsupported" in str(e):
            # Let the AI router handle retries, don't convert to HTTP exception
            raise e
        _raise_http(e)

@router.post(
    "/strategy",
    response_model=StrategyResponse,
    response_model_exclude_none=True,
    summary="Suggest 2–3 strategies (educational only)",
)
async def strategy(
    req: StrategyRequest,
    response: Response,
    coach: TradingCoachService = Depends(get_coach),
    x_request_id: Optional[str] = Header(default=None, convert_underscores=False),
):
    try:
        request_id = x_request_id or str(uuid.uuid4())
        response.headers["X-Request-ID"] = request_id
        
        # Use the real AI service with proper error handling
        payload = await coach.strategy(
            user_id=req.user_id,
            objective=req.objective.strip(),
            market_view=req.market_view.strip(),
            constraints=req.constraints,
        )
        return StrategyResponse(**payload)
    except Exception as e:
        # Check if this is a retryable error that should be handled by the AI router
        if "temperature" in str(e) or "credit balance" in str(e) or "unsupported" in str(e):
            # Let the AI router handle retries, don't convert to HTTP exception
            raise e
        _raise_http(e)

# TEMPORARY: Mock strategies fallback (remove once AI service is fully working)
def _get_mock_strategies():
    return {
            "strategies": [
                {
                    "name": "Dollar-Cost Averaging (DCA)",
                    "when_to_use": "When you want to reduce market timing risk and build wealth gradually over time",
                    "pros": [
                        "Reduces impact of market volatility",
                        "Simple to implement and maintain",
                        "Takes emotion out of investing",
                        "Works well for long-term goals"
                    ],
                    "cons": [
                        "May miss out on market dips",
                        "Requires consistent discipline",
                        "Lower potential returns than timing the market"
                    ],
                    "risk_controls": [
                        "Set up automatic investments",
                        "Diversify across asset classes",
                        "Review and adjust monthly",
                        "Maintain emergency fund"
                    ],
                    "metrics": [
                        "Monthly investment amount",
                        "Portfolio growth rate",
                        "Volatility reduction",
                        "Consistency score"
                    ]
                },
                {
                    "name": "Value Investing Strategy",
                    "when_to_use": "When you have time to research and want to buy undervalued quality companies",
                    "pros": [
                        "Focus on fundamental analysis",
                        "Potential for above-average returns",
                        "Builds deep market knowledge",
                        "Long-term wealth building"
                    ],
                    "cons": [
                        "Requires significant research time",
                        "Value traps can occur",
                        "May underperform in bull markets",
                        "Requires patience and discipline"
                    ],
                    "risk_controls": [
                        "Thorough fundamental analysis",
                        "Diversify across sectors",
                        "Set position size limits",
                        "Regular portfolio review"
                    ],
                    "metrics": [
                        "P/E ratio analysis",
                        "Debt-to-equity ratios",
                        "Revenue growth trends",
                        "Return on equity"
                    ]
                },
                {
                    "name": "Growth Investing Approach",
                    "when_to_use": "When you're comfortable with higher risk and want to invest in fast-growing companies",
                    "pros": [
                        "Potential for high returns",
                        "Invest in innovative companies",
                        "Capitalize on market trends",
                        "Suitable for younger investors"
                    ],
                    "cons": [
                        "Higher volatility and risk",
                        "May be overvalued",
                        "Requires market timing",
                        "Can lead to significant losses"
                    ],
                    "risk_controls": [
                        "Limit position sizes",
                        "Set stop-loss orders",
                        "Diversify across growth sectors",
                        "Regular profit-taking"
                    ],
                    "metrics": [
                        "Revenue growth rates",
                        "Market share expansion",
                        "Innovation pipeline",
                        "Management quality"
                    ]
                }
            ],
            "disclaimer": "For educational purposes only; not financial advice. Discuss any decisions with a qualified advisor and consider your own circumstances.",
            "generated_at": "2025-10-20T18:24:00.000000+00:00",
            "model": "fallback",
            "confidence_score": 0.8,
        }
        
        return StrategyResponse(**payload)
    except Exception as e:
        _raise_http(e)
