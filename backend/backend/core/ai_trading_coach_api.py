"""
AI Trading Coach API - FastAPI Router
=====================================

RESTful API endpoints for the AI Trading Coach service.
Provides personalized strategy recommendations, real-time guidance, trade analysis, and confidence building.

Endpoints:
- POST /coach/recommend-strategy: Get personalized trading strategies
- POST /coach/start-session: Start a new trading session
- POST /coach/guidance: Get next step in active session
- POST /coach/end-session: End trading session
- POST /coach/analyze-trade: Analyze completed trade
- POST /coach/build-confidence: Get confidence-building explanation

Design Notes:
- Uses dependency injection for service instances
- Includes request ID tracing for debugging
- Validates inputs with Pydantic models
- Maps exceptions to appropriate HTTP status codes
- Returns structured JSON responses
"""

import uuid
import logging
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Response, Header
from pydantic import BaseModel, Field, validator

from .ai_trading_coach_service import (
    AITradingCoachService,
    StrategyRecommendation,
    TradingGuidance,
    TradeAnalysis,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/coach", tags=["AI Trading Coach"])


# =============================================================================
# Dependency Injection
# =============================================================================

def get_trading_coach() -> AITradingCoachService:
    """Get trading coach service instance."""
    from .ai_trading_coach_service import ai_trading_coach_service
    return ai_trading_coach_service


# =============================================================================
# Request/Response Models
# =============================================================================

class StrategyRequest(BaseModel):
    """Request for strategy recommendation."""
    user_id: str = Field(..., description="User identifier")
    asset: str = Field(..., description="Asset to trade (e.g., 'AAPL options')")
    risk_tolerance: str = Field("moderate", description="Risk level: conservative, moderate, aggressive")
    goals: Optional[List[str]] = Field(None, description="Trading goals (e.g., ['income', 'hedging'])")
    market_data: Optional[Dict[str, Any]] = Field(None, description="Current market conditions")

    @validator('risk_tolerance')
    def validate_risk_tolerance(cls, v):
        if v not in ['conservative', 'moderate', 'aggressive']:
            raise ValueError('risk_tolerance must be conservative, moderate, or aggressive')
        return v


class StrategyResponse(BaseModel):
    """Response for strategy recommendation."""
    strategy_name: str
    description: str
    risk_level: str
    expected_return: Optional[float]
    suitable_for: List[str]
    steps: List[str]
    market_conditions: Dict[str, Any]
    confidence_score: float
    generated_at: str


class StartSessionRequest(BaseModel):
    """Request to start trading session."""
    user_id: str = Field(..., description="User identifier")
    asset: str = Field(..., description="Asset to trade")
    strategy: str = Field(..., description="Strategy to use")
    risk_tolerance: str = Field(..., description="Risk level")
    goals: List[str] = Field(..., description="Trading goals")


class StartSessionResponse(BaseModel):
    """Response for starting session."""
    session_id: str
    message: str


class GuidanceRequest(BaseModel):
    """Request for trading guidance."""
    session_id: str = Field(..., description="Active session ID")
    market_update: Optional[Dict[str, Any]] = Field(None, description="Latest market data")


class GuidanceResponse(BaseModel):
    """Response for trading guidance."""
    current_step: int
    total_steps: int
    action: str
    rationale: str
    risk_check: str
    next_decision_point: str
    session_id: str
    updated_at: str


class EndSessionRequest(BaseModel):
    """Request to end trading session."""
    session_id: str = Field(..., description="Session ID to end")


class EndSessionResponse(BaseModel):
    """Response for ending session."""
    session_id: str
    total_steps: int
    final_confidence: float
    history_length: int
    ended_at: str


class AnalyzeTradeRequest(BaseModel):
    """Request for trade analysis."""
    user_id: str = Field(..., description="User identifier")
    trade_data: Dict[str, Any] = Field(..., description="Trade details including entry/exit")


class AnalyzeTradeResponse(BaseModel):
    """Response for trade analysis."""
    trade_id: str
    entry: Dict[str, Any]
    exit: Dict[str, Any]
    pnl: float
    strengths: List[str]
    mistakes: List[str]
    lessons_learned: List[str]
    improved_strategy: str
    confidence_boost: str
    analyzed_at: str


class BuildConfidenceRequest(BaseModel):
    """Request for confidence building."""
    user_id: str = Field(..., description="User identifier")
    context: str = Field(..., description="Question or scenario")
    trade_simulation: Optional[Dict[str, Any]] = Field(None, description="Hypothetical trade data")


class BuildConfidenceResponse(BaseModel):
    """Response for confidence building."""
    context: str
    explanation: str
    rationale: str
    tips: List[str]
    motivation: str
    generated_at: str


# =============================================================================
# API Endpoints
# =============================================================================

@router.post(
    "/recommend-strategy",
    response_model=StrategyResponse,
    response_model_exclude_none=True,
    summary="Get personalized trading strategy recommendation",
    description="Generate AI-powered strategy recommendations based on user profile, risk tolerance, and market conditions"
)
async def recommend_strategy(
    req: StrategyRequest,
    response: Response,
    coach: AITradingCoachService = Depends(get_trading_coach),
    x_request_id: Optional[str] = Header(default=None, convert_underscores=False),
):
    """Get personalized trading strategy recommendation."""
    try:
        request_id = x_request_id or str(uuid.uuid4())
        response.headers["X-Request-ID"] = request_id
        
        logger.info(f"Strategy recommendation request: user={req.user_id}, asset={req.asset}, risk={req.risk_tolerance}")
        
        recommendation = await coach.recommend_strategy(
            user_id=req.user_id,
            asset=req.asset,
            risk_tolerance=req.risk_tolerance,
            goals=req.goals,
            market_data=req.market_data,
        )
        
        return StrategyResponse(**recommendation)
        
    except ValueError as e:
        logger.warning(f"Invalid strategy request: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Strategy recommendation failed: {e}")
        raise HTTPException(status_code=500, detail="Strategy recommendation failed")


@router.post(
    "/start-session",
    response_model=StartSessionResponse,
    response_model_exclude_none=True,
    summary="Start new trading session",
    description="Initialize a new AI-guided trading session"
)
async def start_session(
    req: StartSessionRequest,
    response: Response,
    coach: AITradingCoachService = Depends(get_trading_coach),
    x_request_id: Optional[str] = Header(default=None, convert_underscores=False),
):
    """Start a new trading session."""
    try:
        request_id = x_request_id or str(uuid.uuid4())
        response.headers["X-Request-ID"] = request_id
        
        logger.info(f"Starting session: user={req.user_id}, asset={req.asset}, strategy={req.strategy}")
        
        session_id = await coach.start_trading_session(
            user_id=req.user_id,
            asset=req.asset,
            strategy=req.strategy,
            risk_tolerance=req.risk_tolerance,
            goals=req.goals,
        )
        
        return StartSessionResponse(
            session_id=session_id,
            message=f"Trading session started for {req.asset} using {req.strategy}"
        )
        
    except Exception as e:
        logger.error(f"Start session failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to start trading session")


@router.post(
    "/guidance",
    response_model=GuidanceResponse,
    response_model_exclude_none=True,
    summary="Get next trading guidance step",
    description="Get AI-powered step-by-step guidance for active trading session"
)
async def get_guidance(
    req: GuidanceRequest,
    response: Response,
    coach: AITradingCoachService = Depends(get_trading_coach),
    x_request_id: Optional[str] = Header(default=None, convert_underscores=False),
):
    """Get next trading guidance step."""
    try:
        request_id = x_request_id or str(uuid.uuid4())
        response.headers["X-Request-ID"] = request_id
        
        logger.info(f"Guidance request: session={req.session_id}")
        
        guidance = await coach.provide_trading_guidance(
            session_id=req.session_id,
            current_market_update=req.market_update,
        )
        
        return GuidanceResponse(**guidance)
        
    except ValueError as e:
        logger.warning(f"Invalid guidance request: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Guidance request failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to get trading guidance")


@router.post(
    "/end-session",
    response_model=EndSessionResponse,
    response_model_exclude_none=True,
    summary="End trading session",
    description="End active trading session and get summary"
)
async def end_session(
    req: EndSessionRequest,
    response: Response,
    coach: AITradingCoachService = Depends(get_trading_coach),
    x_request_id: Optional[str] = Header(default=None, convert_underscores=False),
):
    """End trading session."""
    try:
        request_id = x_request_id or str(uuid.uuid4())
        response.headers["X-Request-ID"] = request_id
        
        logger.info(f"Ending session: {req.session_id}")
        
        summary = await coach.end_trading_session(req.session_id)
        
        return EndSessionResponse(**summary)
        
    except ValueError as e:
        logger.warning(f"Invalid end session request: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"End session failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to end trading session")


@router.post(
    "/analyze-trade",
    response_model=AnalyzeTradeResponse,
    response_model_exclude_none=True,
    summary="Analyze completed trade",
    description="Get AI-powered analysis of completed trade with insights and lessons"
)
async def analyze_trade(
    req: AnalyzeTradeRequest,
    response: Response,
    coach: AITradingCoachService = Depends(get_trading_coach),
    x_request_id: Optional[str] = Header(default=None, convert_underscores=False),
):
    """Analyze completed trade."""
    try:
        request_id = x_request_id or str(uuid.uuid4())
        response.headers["X-Request-ID"] = request_id
        
        logger.info(f"Trade analysis request: user={req.user_id}")
        
        analysis = await coach.analyze_trade(
            user_id=req.user_id,
            trade_data=req.trade_data,
        )
        
        return AnalyzeTradeResponse(**analysis)
        
    except ValueError as e:
        logger.warning(f"Invalid trade analysis request: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Trade analysis failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to analyze trade")


@router.post(
    "/build-confidence",
    response_model=BuildConfidenceResponse,
    response_model_exclude_none=True,
    summary="Build trading confidence",
    description="Get AI-powered explanation and motivation for trading decisions"
)
async def build_confidence(
    req: BuildConfidenceRequest,
    response: Response,
    coach: AITradingCoachService = Depends(get_trading_coach),
    x_request_id: Optional[str] = Header(default=None, convert_underscores=False),
):
    """Build trading confidence."""
    try:
        request_id = x_request_id or str(uuid.uuid4())
        response.headers["X-Request-ID"] = request_id
        
        logger.info(f"Confidence building request: user={req.user_id}, context={req.context[:50]}...")
        
        explanation = await coach.build_confidence(
            user_id=req.user_id,
            context=req.context,
            trade_simulation=req.trade_simulation,
        )
        
        return BuildConfidenceResponse(**explanation)
        
    except Exception as e:
        logger.error(f"Confidence building failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to build confidence")
