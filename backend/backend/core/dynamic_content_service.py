"""
Dynamic Content Service
Generates AI-powered educational modules and market commentary.
"""

from __future__ import annotations

import asyncio
import json
import uuid
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, TypedDict, Callable, Tuple

from .advanced_ai_router import get_advanced_ai_router, AIRequest, RequestType, AIModel
from .genai_education_service import GenAIEducationService, UserLearningProfile, DifficultyLevel

logger = logging.getLogger(__name__)


# ----------------------------- Typed payloads -----------------------------

class ModuleSection(TypedDict, total=False):
    type: str
    title: str
    content: str
    media: List[str]

class ModuleQuizQuestion(TypedDict, total=False):
    id: str
    question: str
    options: List[str]
    correct_answer: str
    explanation: str

class ModulePayload(TypedDict, total=False):
    id: str
    title: str
    description: str
    difficulty: str
    estimated_time: int
    learning_objectives: List[str]
    sections: List[ModuleSection]
    quiz: Dict[str, List[ModuleQuizQuestion]]
    generated_at: str
    confidence_score: Optional[float]

class MarketCommentaryPayload(TypedDict, total=False):
    headline: str
    summary: str
    drivers: List[str]
    sectors: List[str]
    movers: List[str]
    macro: List[str]
    risks: List[str]
    opportunities: List[str]
    explanations: Dict[str, str]
    generated_at: str
    confidence_score: Optional[float]


# ----------------------------- Helpers -----------------------------

def _now_iso_utc() -> str:
    return datetime.now(timezone.utc).isoformat()

def _safe_json_loads(text: str) -> Optional[Dict[str, Any]]:
    try:
        return json.loads(text)
    except Exception:
        return None

def _extract_json_block(text: str) -> Optional[Dict[str, Any]]:
    """
    Minimal JSON repair: grab the outermost {...}.
    Avoids a second model round-trip.
    """
    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1 and end > start:
        return _safe_json_loads(text[start:end+1])
    return None

async def _with_timeout(coro, timeout_s: int):
    return await asyncio.wait_for(coro, timeout=timeout_s)

async def _retry(
    op: Callable[[], Any],
    attempts: int = 2,
    base_delay: float = 0.25,
    factor: float = 2.0,
    exceptions: Tuple[type, ...] = (Exception,),
):
    last = None
    for i in range(attempts):
        try:
            return await op()
        except exceptions as e:
            last = e
            if i == attempts - 1:
                raise
            await asyncio.sleep(base_delay * (factor ** i))
    if last:
        raise last


# ----------------------------- Service -----------------------------

class DynamicContentService:
    """Service to generate educational modules and market commentary (robust, typed, UTC)."""

    # Tunables
    TOKENS_MODULE = 4000
    TOKENS_COMMENTARY = 2000
    REQUEST_TIMEOUT_S = 35
    RETRY_ATTEMPTS = 2

    DEFAULT_MODULE_MODEL = AIModel.GPT_5
    DEFAULT_COMMENTARY_MODEL = AIModel.CLAUDE_3_5_SONNET

    def __init__(
        self,
        ai_router: Optional["AdvancedAIRouter"] = None,
        education: Optional[GenAIEducationService] = None,
    ) -> None:
        self.ai_router = ai_router or get_advanced_ai_router()
        self.education = education or GenAIEducationService()

    # ------------------------- Public API -------------------------

    async def generate_module(
        self,
        user_profile: UserLearningProfile,
        topic: str,
        *,
        difficulty: DifficultyLevel = DifficultyLevel.BEGINNER,
        content_types: Optional[List[str]] = None,
        learning_objectives: Optional[List[str]] = None,
    ) -> ModulePayload:
        """
        Generate a single educational module tailored to the user.
        Returns a structured JSON payload with metadata and content blocks.
        """
        topic = (topic or "").strip()
        if not topic:
            raise ValueError("topic must be a non-empty string")

        preferred_types = content_types or ["text", "example", "quiz"]
        objectives = learning_objectives or [
            "Understand key concepts",
            "Apply with one real example",
            "Assess with a short quiz",
        ]

        prompt = {
            "task": "generate_learning_module",
            "topic": topic,
            "difficulty": difficulty.value,
            "user_profile": {
                "learning_style": user_profile.learning_style.value,
                "level": user_profile.current_level.value,
                "interests": user_profile.interests,
                "weak_areas": user_profile.weak_areas,
                "strong_areas": user_profile.strong_areas,
                "pace": user_profile.learning_pace,
                "time_available": user_profile.time_available,
            },
            "preferred_content_types": preferred_types,
            "learning_objectives": objectives,
            "interactive_requirements": {
                "include_practical_exercises": True,
                "include_real_world_examples": True,
                "include_calculator_tools": True,
                "include_decision_trees": True,
                "include_progressive_challenges": True,
                "include_personal_application": True,
            },
            "output_format": {
                "id": "string",
                "title": "string",
                "description": "string",
                "difficulty": "string",
                "estimated_time": "integer",
                "learning_objectives": ["string"],
                "sections": [
                    {
                        "type": "string (concept|example|exercise|calculator|decision_tree|challenge)",
                        "title": "string",
                        "content": "string",
                        "key_points": ["string"],
                        "examples": ["string"],
                        "media": ["string"],
                        "interactive_elements": {
                            "calculator": {
                                "formula": "string",
                                "variables": ["string"],
                                "example_inputs": ["string"],
                                "description": "string"
                            },
                            "decision_tree": {
                                "question": "string",
                                "options": [
                                    {
                                        "choice": "string",
                                        "outcome": "string",
                                        "next_question": "string"
                                    }
                                ]
                            },
                            "exercise": {
                                "instructions": "string",
                                "steps": ["string"],
                                "expected_output": "string",
                                "hints": ["string"]
                            },
                            "challenge": {
                                "scenario": "string",
                                "goals": ["string"],
                                "constraints": ["string"],
                                "success_criteria": ["string"]
                            }
                        }
                    }
                ],
                "quiz": {
                    "questions": [
                        {
                            "id": "string",
                            "question": "string",
                            "options": ["string"],
                            "correct_answer": "string",
                            "explanation": "string",
                        }
                    ]
                },
                "practical_application": {
                    "real_world_scenario": "string",
                    "your_situation": "string",
                    "action_plan": ["string"],
                    "next_steps": ["string"],
                    "resources": ["string"]
                }
            },
            "response_style": "Return ONLY valid JSON matching output_format. No markdown. Include interactive elements based on user profile and topic complexity.",
        }

        req = AIRequest(
            request_id=str(uuid.uuid4()),
            request_type=RequestType.GENERAL_CHAT,
            prompt=json.dumps(prompt),
            context={
                "topic": topic,
                "difficulty": difficulty.value,
                "request_id": str(uuid.uuid4()),
            },
            model_preference=self.DEFAULT_MODULE_MODEL,
            requires_reasoning=True,
            max_tokens=self.TOKENS_MODULE,
        )

        async def _op():
            return await _with_timeout(self.ai_router.route_request(req), self.REQUEST_TIMEOUT_S)

        try:
            resp = await _retry(_op, attempts=self.RETRY_ATTEMPTS)
            raw = _safe_json_loads(resp.response) or _extract_json_block(resp.response)
            data: ModulePayload

            if not isinstance(raw, dict):
                data = self._fallback_module(topic, difficulty, objectives)
            else:
                # Sanitize and clamp fields
                est = raw.get("estimated_time", 15)
                try:
                    est = int(est)
                except Exception:
                    est = 15
                est = max(3, min(240, est))  # 3 minutes .. 4 hours

                sections_in = raw.get("sections") or []
                sections: List[ModuleSection] = []
                for s in sections_in[:12]:
                    sections.append(
                        ModuleSection(
                            type=str(s.get("type", "text")),
                            title=str(s.get("title", "Section")).strip(),
                            content=str(s.get("content", "")).strip(),
                            media=[str(m) for m in (s.get("media") or [])][:6],
                        )
                    )

                quiz_in = (raw.get("quiz") or {}).get("questions") or []
                quiz_questions: List[ModuleQuizQuestion] = []
                for q in quiz_in[:10]:
                    qq = ModuleQuizQuestion(
                        id=str(q.get("id") or uuid.uuid4()),
                        question=str(q.get("question", "")).strip(),
                        options=[str(o) for o in (q.get("options") or [])][:8],
                        correct_answer=str(q.get("correct_answer", "")).strip(),
                        explanation=str(q.get("explanation", "")).strip(),
                    )
                    quiz_questions.append(qq)

                data = ModulePayload(
                    id=str(raw.get("id") or uuid.uuid4()),
                    title=str(raw.get("title", f"{topic} - {difficulty.value.title()} Module")).strip(),
                    description=str(raw.get("description", f"Learn the fundamentals of {topic}. ")).strip(),
                    difficulty=str(raw.get("difficulty", difficulty.value)),
                    estimated_time=est,
                    learning_objectives=[str(x) for x in (raw.get("learning_objectives") or objectives)][:10],
                    sections=sections,
                    quiz={"questions": quiz_questions},
                )

            data["generated_at"] = _now_iso_utc()
            data["confidence_score"] = float(getattr(resp, "confidence_score", 0.0) or 0.0)
            return data

        except Exception as e:
            logger.exception("generate_module failed: %s", e)
            data = self._fallback_module(topic, difficulty, objectives)
            data["generated_at"] = _now_iso_utc()
            data["confidence_score"] = 0.0
            return data

    async def generate_market_commentary(
        self,
        user_profile: Optional[UserLearningProfile],
        market_context: Optional[Dict[str, Any]] = None,
        *,
        horizon: str = "daily",
        tone: str = "neutral",
    ) -> MarketCommentaryPayload:
        """
        Generate personalized market commentary based on optional market context.
        market_context can include indexes, movers, sector performance, rates, VIX, news.
        """
        allowed_horizon = {"daily", "weekly", "monthly"}
        allowed_tone = {"neutral", "bullish", "bearish", "educational"}
        horizon = (horizon or "daily").lower()
        tone = (tone or "neutral").lower()
        if horizon not in allowed_horizon:
            horizon = "daily"
        if tone not in allowed_tone:
            tone = "neutral"

        prompt = {
            "task": "market_commentary",
            "horizon": horizon,
            "tone": tone,
            "user_profile": {
                "level": getattr(getattr(user_profile, "current_level", None), "value", None),
                "interests": getattr(user_profile, "interests", None) if user_profile else None,
            },
            "market_context": market_context or {},
            "requirements": [
                "Explain key market drivers in plain English",
                "Summarize sector and factor performance",
                "Call out notable movers and macro indicators",
                "Tie insights to user interests/holdings if provided",
                "Provide 2-3 risks and 2-3 opportunities",
            ],
            "output_format": {
                "headline": "string",
                "summary": "string",
                "drivers": ["string"],
                "sectors": ["string"],
                "movers": ["string"],
                "macro": ["string"],
                "risks": ["string"],
                "opportunities": ["string"],
                "explanations": {
                    "beginner": "string",
                    "advanced": "string",
                },
            },
            "response_style": "Return ONLY valid JSON matching output_format. No markdown.",
        }

        req = AIRequest(
            request_id=str(uuid.uuid4()),
            request_type=RequestType.MARKET_ANALYSIS,
            prompt=json.dumps(prompt),
            context={"horizon": horizon, "request_id": str(uuid.uuid4())},
            model_preference=self.DEFAULT_COMMENTARY_MODEL,
            requires_reasoning=True,
            max_tokens=self.TOKENS_COMMENTARY,
        )

        async def _op():
            return await _with_timeout(self.ai_router.route_request(req), self.REQUEST_TIMEOUT_S)

        try:
            resp = await _retry(_op, attempts=self.RETRY_ATTEMPTS)
            raw = _safe_json_loads(resp.response) or _extract_json_block(resp.response)

            if not isinstance(raw, dict):
                data = self._fallback_commentary()
            else:
                data = MarketCommentaryPayload(
                    headline=str(raw.get("headline", "Market Overview")),
                    summary=str(raw.get("summary", "Summary unavailable; using fallback.")),
                    drivers=[str(x) for x in (raw.get("drivers") or [])][:10],
                    sectors=[str(x) for x in (raw.get("sectors") or [])][:12],
                    movers=[str(x) for x in (raw.get("movers") or [])][:12],
                    macro=[str(x) for x in (raw.get("macro") or [])][:12],
                    risks=[str(x) for x in (raw.get("risks") or [])][:6],
                    opportunities=[str(x) for x in (raw.get("opportunities") or [])][:6],
                    explanations={
                        "beginner": str((raw.get("explanations") or {}).get("beginner", "")),
                        "advanced": str((raw.get("explanations") or {}).get("advanced", "")),
                    },
                )

            data["generated_at"] = _now_iso_utc()
            data["confidence_score"] = float(getattr(resp, "confidence_score", 0.0) or 0.0)
            return data

        except Exception as e:
            logger.exception("generate_market_commentary failed: %s", e)
            data = self._fallback_commentary()
            data["generated_at"] = _now_iso_utc()
            data["confidence_score"] = 0.0
            return data

    # ------------------------- Fallbacks -------------------------

    def _fallback_module(
        self,
        topic: str,
        difficulty: DifficultyLevel,
        objectives: List[str],
    ) -> ModulePayload:
        return ModulePayload(
            id=str(uuid.uuid4()),
            title=f"{topic} - {difficulty.value.title()} Module",
            description=f"Learn the fundamentals of {topic}.",
            difficulty=difficulty.value,
            estimated_time=15,
            learning_objectives=objectives[:5],
            sections=[
                ModuleSection(
                    type="text",
                    title="Overview",
                    content=f"This module introduces {topic} with simple examples.",
                    media=[],
                )
            ],
            quiz={"questions": []},
        )

    def _fallback_commentary(self) -> MarketCommentaryPayload:
        return MarketCommentaryPayload(
            headline="Market Overview",
            summary="Summary unavailable; using fallback.",
            drivers=[],
            sectors=[],
            movers=[],
            macro=[],
            risks=[],
            opportunities=[],
            explanations={"beginner": "", "advanced": ""},
        )


# Singleton (optional)
dynamic_content_service = DynamicContentService()
