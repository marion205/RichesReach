"""
AI Tutor API Router
Exposes endpoints for ask, explain, quiz, evaluate, and dynamic content generation.
"""

from __future__ import annotations

import asyncio
import logging
import uuid
from functools import lru_cache
from typing import Any, Dict, Optional

from fastapi import APIRouter, HTTPException, Depends, Header, Response
from pydantic import BaseModel, Field

from .ai_tutor_service import AITutorService
from .genai_education_service import GenAIEducationService, DifficultyLevel
from .dynamic_content_service import DynamicContentService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/tutor", tags=["AI Tutor"])

# ------------------- Dependency Injection (singletons) -------------------

@lru_cache
def get_tutor() -> AITutorService:
    return AITutorService()

@lru_cache
def get_edu() -> GenAIEducationService:
    return GenAIEducationService()

@lru_cache
def get_dynamic() -> DynamicContentService:
    return DynamicContentService()


# ------------------- Request/Response Models -------------------

class AskRequest(BaseModel):
    user_id: str = Field(..., description="User identifier")
    question: str = Field(..., description="Question to ask")
    context: Optional[Dict[str, Any]] = None

class AskResponse(BaseModel):
    response: str
    model: Optional[str] = None
    confidence_score: Optional[float] = None


class ExplainRequest(BaseModel):
    user_id: str = Field(..., description="User identifier")
    concept: str = Field(..., description="Concept to explain")
    extra_context: Optional[Dict[str, Any]] = None


class QuizRequest(BaseModel):
    user_id: str = Field(..., description="User identifier")
    topic: str = Field(..., description="Quiz topic")
    difficulty: DifficultyLevel = Field(DifficultyLevel.BEGINNER, description="Difficulty enum")
    num_questions: int = Field(3, ge=1, le=10, description="Number of questions (1–10)")


class EvaluateRequest(BaseModel):
    user_id: str
    question: str
    user_answer: str
    correct_answer: Optional[str] = None
    rubric: Optional[str] = None


class DynamicContentRequest(BaseModel):
    user_id: str
    content_type: str = Field(..., description="text|interactive|quiz|example|simulation|video")
    topic: str
    market_context: Optional[Dict[str, Any]] = None


class ModuleRequest(BaseModel):
    user_id: str
    topic: str
    difficulty: DifficultyLevel = DifficultyLevel.BEGINNER
    content_types: Optional[list[str]] = None
    learning_objectives: Optional[list[str]] = None


class MarketCommentaryRequest(BaseModel):
    user_id: Optional[str] = None
    horizon: Optional[str] = Field("daily", description="daily|weekly|monthly")
    tone: Optional[str] = Field("neutral", description="neutral|bullish|bearish|educational")
    market_context: Optional[Dict[str, Any]] = None


# ------------------- Error Mapping -------------------

def _raise_http(e: Exception) -> None:
    if isinstance(e, asyncio.TimeoutError):
        raise HTTPException(status_code=504, detail="Request to AI router timed out") from e
    if isinstance(e, ValueError):
        raise HTTPException(status_code=400, detail=str(e)) from e
    logger.exception("Unhandled error in AI Tutor route: %s", e)
    raise HTTPException(status_code=500, detail="Internal server error") from e


# ------------------- Endpoints -------------------

@router.post(
    "/ask",
    response_model=AskResponse,
    response_model_exclude_none=True,
    summary="Ask a question",
)
async def ask(
    req: AskRequest,
    response: Response,
    tutor: AITutorService = Depends(get_tutor),
    x_request_id: Optional[str] = Header(default=None, convert_underscores=False),
):
    try:
        request_id = x_request_id or str(uuid.uuid4())
        response.headers["X-Request-ID"] = request_id
        ai_resp = await tutor.ask_question(
            user_id=req.user_id,
            question=req.question,
            context={**(req.context or {}), "request_id": request_id},
        )
        return AskResponse(
            response=ai_resp.response,
            model=getattr(ai_resp, "model", None),
            confidence_score=getattr(ai_resp, "confidence_score", None),
        )
    except Exception as e:
        _raise_http(e)


@router.post(
    "/explain",
    response_model_exclude_none=True,
    summary="Explain a concept tailored to the user",
)
async def explain(
    req: ExplainRequest,
    response: Response,
    tutor: AITutorService = Depends(get_tutor),
    x_request_id: Optional[str] = Header(default=None, convert_underscores=False),
):
    try:
        request_id = x_request_id or str(uuid.uuid4())
        response.headers["X-Request-ID"] = request_id
        payload = await tutor.explain_concept(
            user_id=req.user_id,
            concept=req.concept,
            extra_context={**(req.extra_context or {}), "request_id": request_id},
        )
        return payload
    except Exception as e:
        _raise_http(e)


@router.post(
    "/quiz",
    response_model_exclude_none=True,
    summary="Generate a short quiz",
)
async def quiz(
    req: QuizRequest,
    response: Response,
    tutor: AITutorService = Depends(get_tutor),
    x_request_id: Optional[str] = Header(default=None, convert_underscores=False),
):
    try:
        request_id = x_request_id or str(uuid.uuid4())
        response.headers["X-Request-ID"] = request_id
        payload = await tutor.generate_quiz(
            user_id=req.user_id,
            topic=req.topic,
            difficulty=req.difficulty,
            num_questions=req.num_questions,
        )
        return payload
    except Exception as e:
        _raise_http(e)


@router.post(
    "/evaluate",
    response_model_exclude_none=True,
    summary="Evaluate an answer and return score + feedback",
)
async def evaluate(
    req: EvaluateRequest,
    response: Response,
    tutor: AITutorService = Depends(get_tutor),
    x_request_id: Optional[str] = Header(default=None, convert_underscores=False),
):
    try:
        request_id = x_request_id or str(uuid.uuid4())
        response.headers["X-Request-ID"] = request_id
        payload = await tutor.evaluate_answer(
            user_id=req.user_id,
            question=req.question,
            user_answer=req.user_answer,
            correct_answer=req.correct_answer,
            rubric=req.rubric,
        )
        return payload
    except Exception as e:
        _raise_http(e)


@router.post(
    "/dynamic-content",
    response_model_exclude_none=True,
    summary="Generate dynamic content (topic + market context)",
)
async def dynamic_content(
    req: DynamicContentRequest,
    response: Response,
    edu: GenAIEducationService = Depends(get_edu),
    x_request_id: Optional[str] = Header(default=None, convert_underscores=False),
):
    try:
        request_id = x_request_id or str(uuid.uuid4())
        response.headers["X-Request-ID"] = request_id

        profile = edu.user_profiles.get(req.user_id) or await edu.create_user_learning_profile(req.user_id, {})
        payload = await edu.generate_dynamic_content(
            content_type=req.content_type,
            topic=req.topic,
            user_profile=profile,
            market_context={**(req.market_context or {}), "request_id": request_id},
        )
        return payload
    except Exception as e:
        _raise_http(e)


@router.post(
    "/module",
    response_model_exclude_none=True,
    summary="Generate a learning module (content types + objectives)",
)
async def generate_module(
    req: ModuleRequest,
    response: Response,
    edu: GenAIEducationService = Depends(get_edu),
    dynamic: DynamicContentService = Depends(get_dynamic),
    x_request_id: Optional[str] = Header(default=None, convert_underscores=False),
):
    try:
        request_id = x_request_id or str(uuid.uuid4())
        response.headers["X-Request-ID"] = request_id

        profile = edu.user_profiles.get(req.user_id) or await edu.create_user_learning_profile(req.user_id, {})
        payload = await dynamic.generate_module(
            user_profile=profile,
            topic=req.topic,
            difficulty=req.difficulty,
            content_types=req.content_types,
            learning_objectives=req.learning_objectives,
        )
        return payload
    except Exception as e:
        _raise_http(e)


@router.post(
    "/market-commentary",
    response_model_exclude_none=True,
    summary="Generate market commentary",
)
async def market_commentary(
    req: MarketCommentaryRequest,
    response: Response,
    edu: GenAIEducationService = Depends(get_edu),
    dynamic: DynamicContentService = Depends(get_dynamic),
    x_request_id: Optional[str] = Header(default=None, convert_underscores=False),
):
    try:
        request_id = x_request_id or str(uuid.uuid4())
        response.headers["X-Request-ID"] = request_id

        profile = None
        if req.user_id:
            profile = edu.user_profiles.get(req.user_id) or await edu.create_user_learning_profile(req.user_id, {})

        return await dynamic.generate_market_commentary(
            user_profile=profile,
            market_context={**(req.market_context or {}), "request_id": request_id},
            horizon=req.horizon or "daily",
            tone=req.tone or "neutral",
        )
    except Exception as e:
        _raise_http(e)
