"""
Assistant API Router
Exposes a single /assistant/query endpoint that forwards prompts to AssistantService.
"""

from __future__ import annotations

import asyncio
import logging
import uuid
from functools import lru_cache
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, Header, HTTPException, Response
from pydantic import BaseModel, Field
try:
    # Pydantic v2
    from pydantic import field_validator as _pv_validator
except Exception:  # pragma: no cover - fallback for pydantic v1
    from pydantic import validator as _pv_validator  # type: ignore

from .assistant_service import AssistantService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/assistant", tags=["Assistant"])

MAX_PROMPT_CHARS = 8000  # guard against runaway token costs


# ------------------- DI singleton -------------------

@lru_cache
def get_assistant() -> AssistantService:
    return AssistantService()


# ------------------- Schemas -------------------

class AssistantQueryRequest(BaseModel):
    user_id: Optional[str] = Field(None, description="User identifier (optional)")
    prompt: str = Field(..., description="Natural language prompt to the assistant")
    context: Optional[Dict[str, Any]] = Field(None, description="Arbitrary context to include")
    market_context: Optional[Dict[str, Any]] = Field(None, description="Optional market data/context")

    @_pv_validator("prompt")
    def _prompt_not_empty(cls, v: str) -> str:  # type: ignore[override]
        if not v or not v.strip():
            raise ValueError("prompt must be a non-empty string")
        v = v.strip()
        if len(v) > MAX_PROMPT_CHARS:
            raise ValueError(f"prompt too long (max {MAX_PROMPT_CHARS} chars)")
        return v


# ------------------- Error mapping -------------------

def _raise_http(e: Exception) -> None:
    # Allow deliberate HTTPExceptions to pass through unchanged
    if isinstance(e, HTTPException):
        raise e
    if isinstance(e, asyncio.TimeoutError):
        raise HTTPException(status_code=504, detail="Request to AI router timed out") from e
    if isinstance(e, ValueError):
        raise HTTPException(status_code=400, detail=str(e)) from e
    logger.exception("assistant.query.unhandled", extra={"error": str(e)})
    raise HTTPException(status_code=500, detail="Internal server error") from e


# ------------------- Endpoint -------------------

@router.post(
    "/query",
    summary="General assistant query",
    response_model_exclude_none=True,
)
async def assistant_query(
    req: AssistantQueryRequest,
    response: Response,
    assistant: AssistantService = Depends(get_assistant),
    x_request_id: Optional[str] = Header(default=None, convert_underscores=False),
):
    """
    Forwards a user prompt (plus optional context/market_context) to AssistantService.
    Returns the service's raw payload to keep flexibility.
    """
    try:
        request_id = x_request_id or str(uuid.uuid4())
        response.headers["X-Request-ID"] = request_id

        # Merge/propagate request ID into context for traceability
        merged_context: Dict[str, Any] = {"request_id": request_id}
        if req.context:
            merged_context.update(req.context)

        # Structured logs
        logger.info("assistant.query.start", extra={"request_id": request_id, "user_id": req.user_id})
        payload = await assistant.query(
            user_id=req.user_id,
            prompt=req.prompt,
            context=merged_context,
            market_context=req.market_context,
        )
        logger.info("assistant.query.ok", extra={"request_id": request_id})
        return payload
    except Exception as e:
        logger.info("assistant.query.err", extra={"error": str(e)})
        _raise_http(e)
