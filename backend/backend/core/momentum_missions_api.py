"""
Momentum Missions API Router
Exposes endpoints for gamified daily challenges and streak management.
"""

from __future__ import annotations

import asyncio
import logging
import uuid
from functools import lru_cache
from typing import Any, Dict, Optional

from fastapi import APIRouter, HTTPException, Depends, Header, Response
from pydantic import BaseModel, Field

from .momentum_missions_service import MomentumMissionsService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/missions", tags=["Momentum Missions"])

# ------------------- Dependency Injection (singletons) -------------------

@lru_cache
def get_missions_service() -> MomentumMissionsService:
    return MomentumMissionsService()

# ------------------- Request/Response Models -------------------

class UserProgressRequest(BaseModel):
    user_id: str = Field(..., description="User identifier")
    include_current_mission: bool = Field(True, description="Include current mission details")

class DailyMissionRequest(BaseModel):
    user_id: str = Field(..., description="User identifier")
    day_number: int = Field(..., ge=1, le=21, description="Day number in 21-day cycle")
    market_data: Optional[Dict[str, Any]] = Field(None, description="Current market data for regime adaptation")

class RecoveryRitualRequest(BaseModel):
    user_id: str = Field(..., description="User identifier")
    missed_day: int = Field(..., ge=1, le=21, description="The day number that was missed")

# ------------------- Error Handling -------------------

def _raise_http(e: Exception) -> None:
    """Convert exceptions to HTTP responses."""
    if isinstance(e, ValueError):
        raise HTTPException(status_code=400, detail=str(e))
    elif isinstance(e, TimeoutError):
        raise HTTPException(status_code=504, detail="Request timeout")
    else:
        logger.error(f"Unexpected error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

# ------------------- API Endpoints -------------------

@router.get(
    "/progress/{user_id}",
    response_model_exclude_none=True,
    summary="Get user's momentum mission progress",
)
async def get_user_progress(
    user_id: str,
    include_current_mission: bool = True,
    missions_service: MomentumMissionsService = Depends(get_missions_service),
    x_request_id: Optional[str] = Header(default=None, convert_underscores=False),
):
    """
    Get user's momentum mission progress and current status.
    
    This endpoint provides:
    - Current streak and longest streak
    - Total missions completed
    - Current mission details (if active)
    - Available recovery ritual (if streak broken)
    - Achievement badges and progress
    - Streak multiplier for rewards
    
    Features:
    - 21-day habit loop tracking
    - Progressive difficulty system
    - Achievement and badge system
    - Streak multiplier rewards
    """
    try:
        request_id = x_request_id or str(uuid.uuid4())
        
        progress = await missions_service.get_user_progress(
            user_id=user_id,
            include_current_mission=include_current_mission,
        )
        
        return progress
    except Exception as e:
        _raise_http(e)

@router.post(
    "/daily",
    response_model_exclude_none=True,
    summary="Generate daily momentum mission",
)
async def generate_daily_mission(
    req: DailyMissionRequest,
    response: Response,
    missions_service: MomentumMissionsService = Depends(get_missions_service),
    x_request_id: Optional[str] = Header(default=None, convert_underscores=False),
):
    """
    Generate a daily momentum mission for the specified day.
    
    This creates progressive challenges that build over 21 days:
    - Days 1-7: Basic concepts and quizzes
    - Days 8-14: Intermediate analysis and simulations  
    - Days 15-21: Advanced strategies and real-world application
    
    Features:
    - Progressive difficulty over 21 days
    - Regime-adaptive mission content
    - 3-7 minute completion time
    - Immediate feedback and learning
    - Streak multiplier rewards
    """
    try:
        request_id = x_request_id or str(uuid.uuid4())
        response.headers["X-Request-ID"] = request_id
        
        mission = await missions_service.generate_daily_mission(
            user_id=req.user_id,
            day_number=req.day_number,
            market_data=req.market_data,
        )
        return mission
    except Exception as e:
        _raise_http(e)

@router.post(
    "/recovery",
    response_model_exclude_none=True,
    summary="Generate recovery ritual for missed mission",
)
async def generate_recovery_ritual(
    req: RecoveryRitualRequest,
    response: Response,
    missions_service: MomentumMissionsService = Depends(get_missions_service),
    x_request_id: Optional[str] = Header(default=None, convert_underscores=False),
):
    """
    Generate a recovery ritual for a missed mission.
    
    Recovery rituals help users get back on track after missing a day,
    providing a shorter, easier challenge to rebuild momentum.
    
    Features:
    - 2-3 minute completion time
    - Confidence-building content
    - Streak recovery mechanism
    - Encouraging and supportive tone
    """
    try:
        request_id = x_request_id or str(uuid.uuid4())
        response.headers["X-Request-ID"] = request_id
        
        ritual = await missions_service.generate_recovery_ritual(
            user_id=req.user_id,
            missed_day=req.missed_day,
        )
        return ritual
    except Exception as e:
        _raise_http(e)

@router.get(
    "/health",
    summary="Health check for momentum missions service",
)
async def health_check(
    missions_service: MomentumMissionsService = Depends(get_missions_service),
):
    """Check if the momentum missions service is healthy."""
    try:
        # Test basic functionality
        test_progress = await missions_service.get_user_progress("test-user", include_current_mission=False)
        test_mission = await missions_service.generate_daily_mission("test-user", 1)
        test_recovery = await missions_service.generate_recovery_ritual("test-user", 1)
        
        return {
            "status": "healthy",
            "service": "momentum_missions",
            "features": {
                "progressive_challenges": True,
                "recovery_rituals": True,
                "streak_tracking": True,
                "achievement_system": True,
                "regime_adaptation": True
            },
            "test_results": {
                "progress_retrieval": test_progress is not None,
                "mission_generation": test_mission is not None,
                "recovery_generation": test_recovery is not None
            }
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=503, detail="Service unhealthy")
