"""
Futures Policy API - Phase 3
Expose suitability checks and guardrails
"""

from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Optional
from pydantic import BaseModel
import logging

from core.futures_policy import get_policy_engine, SuitabilityLevel
from core.futures_api import get_user_id

logger = logging.getLogger(__name__)

policy_router = APIRouter(prefix="/api/futures/policy", tags=["futures-policy"])


class SuitabilityCheckRequest(BaseModel):
    recommendation: Dict  # Futures recommendation


class SuitabilityCheckResponse(BaseModel):
    level: str  # approved, caution, restricted, blocked
    reason: str
    allowed: bool


@policy_router.post("/check")
async def check_suitability(
    request: SuitabilityCheckRequest,
    user_id: int = Depends(get_user_id),
) -> SuitabilityCheckResponse:
    """
    Check if user is suitable for a futures recommendation.
    Phase 3: Policy engine gate
    """
    try:
        policy = get_policy_engine()
        user_profile = policy.get_user_profile(user_id)
        
        level, reason = policy.check_suitability(
            user_profile=user_profile,
            recommendation=request.recommendation,
        )
        
        return SuitabilityCheckResponse(
            level=level.value,
            reason=reason,
            allowed=level in [SuitabilityLevel.APPROVED, SuitabilityLevel.CAUTION],
        )
    except Exception as e:
        logger.error(f"Error checking suitability: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@policy_router.get("/profile")
async def get_user_profile(user_id: int = Depends(get_user_id)) -> Dict:
    """
    Get user profile for policy checks.
    """
    try:
        policy = get_policy_engine()
        profile = policy.get_user_profile(user_id)
        return profile
    except Exception as e:
        logger.error(f"Error getting user profile: {e}")
        raise HTTPException(status_code=500, detail=str(e))

