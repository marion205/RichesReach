"""
Interactive AI Tutor Service
============================

Provides real-time Q&A, explanations, quizzes, and answer evaluation using AdvancedAIRouter.

Key Features:
- Personalized explanations based on user learning profiles
- Parallel quiz generation for efficiency
- Robust answer evaluation with JSON parsing and fallback mechanisms
- All timestamps in UTC ISO8601 format for consistency

Dependencies:
- advanced_ai_router: For AI request routing and responses
- genai_education_service: For educational content generation and profiles
"""

from __future__ import annotations

import asyncio
import json
import uuid
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, TypedDict

from .advanced_ai_router import get_advanced_ai_router, AIRequest, AIResponse, RequestType, AIModel
from .genai_education_service import (
    GenAIEducationService,
    UserLearningProfile,
    DifficultyLevel,
)

logger = logging.getLogger(__name__)
# =============================================================================
# Typed Payloads for Safer API Returns
# =============================================================================

class ExplanationPayload(TypedDict, total=False):
    """Payload for concept explanations."""
    concept: str
    explanation: str
    examples: List[str]
    analogies: List[str]
    visual_aids: List[str]
    generated_at: str  # ISO8601 (UTC)
class QuizQuestion(TypedDict, total=False):
    """Single quiz question structure."""
    id: str
    question: str
    question_type: str
    options: Optional[List[str]]
    correct_answer: Optional[str]
    explanation: Optional[str]
    hints: Optional[List[str]]
class QuizPayload(TypedDict, total=False):
    """Payload for generated quizzes."""
    topic: str
    difficulty: str
    questions: List[QuizQuestion]
    generated_at: str  # ISO8601 (UTC)
class EvaluationResult(TypedDict, total=False):
    """Payload for answer evaluations."""
    score: int
    strengths: List[str]
    mistakes: List[str]
    ideal_answer: str
    improvement_tips: List[str]
    confidence_score: Optional[float]
    evaluated_at: str  # ISO8601 (UTC)
# =============================================================================
# Utility Functions
# =============================================================================

def _now_iso_utc() -> str:
    """Generate current UTC timestamp in ISO8601 format."""
    return datetime.now(timezone.utc).isoformat()
def _safe_json_loads(s: str) -> Optional[Dict[str, Any]]:
    """Safely parse JSON string, returning None on failure."""
    try:
        return json.loads(s)
    except Exception:
        return None
# =============================================================================
# Main Service Class
# =============================================================================

class AITutorService:
    """
    Interactive AI Tutor for financial education.

    Core Functionality:
        - Real-time Q&A with reasoning
        - Tailored concept explanations
        - Quiz generation with deduplication
        - Answer evaluation with scoring and feedback

    Design Notes:
        - Router and education service are injectable for testing.
        - All timestamps returned in UTC (ISO8601).
        - Timeouts and token limits are configurable.
    """

    # Configuration Defaults
    DEFAULT_CHAT_TOKENS = 1200
    DEFAULT_GRADE_TOKENS = 800
    DEFAULT_TIMEOUT_SECONDS = 30
    DEFAULT_QUIZ_QUESTIONS = 3

    def __init__(
        self,
        ai_router: Optional["AdvancedAIRouter"] = None,
        education_service: Optional[GenAIEducationService] = None,
        *,
        default_chat_model: AIModel = AIModel.GPT_5,
        default_grade_model: AIModel = AIModel.CLAUDE_3_5_SONNET,
        request_timeout_s: int = DEFAULT_TIMEOUT_SECONDS,
    ) -> None:
        self.ai_router = ai_router or get_advanced_ai_router()
        self.education_service = education_service or GenAIEducationService()
        self.default_chat_model = default_chat_model
        self.default_grade_model = default_grade_model
        self.request_timeout_s = request_timeout_s

    # -------------------------------------------------------------------------
    # Public API Methods
    # -------------------------------------------------------------------------

    async def ask_question(
        self,
        user_id: str,
        question: str,
        context: Optional[Dict[str, Any]] = None,
        *,
        requires_reasoning: bool = True,
        max_tokens: int = DEFAULT_CHAT_TOKENS,
        model: Optional[AIModel] = None,
    ) -> AIResponse:
        """
        Answer a user's question with financial-aware reasoning.

        Args:
            user_id: Unique identifier for the user.
            question: The question to answer.
            context: Optional additional context for the AI.
            requires_reasoning: Whether to enable step-by-step reasoning.
            max_tokens: Maximum tokens for the response.
            model: Optional override for the AI model.

        Returns:
            Raw AIResponse from the router, preserving provenance.

        Raises:
            ValueError: If question is empty.
        """
        question = (question or "").strip()
        if not question:
            raise ValueError("question must be a non-empty string")

        req = AIRequest(
            request_id=str(uuid.uuid4()),
            request_type=RequestType.GENERAL_CHAT,
            prompt=question,
            context={"user_id": user_id, **(context or {})},
            model_preference=model or self.default_chat_model,
            requires_reasoning=requires_reasoning,
            max_tokens=max_tokens,
        )

        logger.debug(
            "AITutorService.ask_question",
            extra={"user_id": user_id, "request_id": req.request_id},
        )
        return await asyncio.wait_for(
            self.ai_router.route_request(req), timeout=self.request_timeout_s
        )

    async def explain_concept(
        self,
        user_id: str,
        concept: str,
        profile: Optional[UserLearningProfile] = None,
        extra_context: Optional[Dict[str, Any]] = None,
    ) -> ExplanationPayload:
        """
        Generate a tailored explanation for a financial concept.

        Args:
            user_id: Unique identifier for the user.
            concept: The concept to explain.
            profile: Optional user learning profile; auto-fetched if None.
            extra_context: Optional additional context.

        Returns:
            Structured explanation payload.

        Raises:
            ValueError: If concept is empty.
        """
        concept = (concept or "").strip()
        if not concept:
            raise ValueError("concept must be a non-empty string")

        if profile is None:
            profile = self.education_service.user_profiles.get(user_id)
            if profile is None:
                profile = await self.education_service.create_user_learning_profile(
                    user_id, {}
                )

        response = await self.education_service.generate_ai_explanation(
            concept=concept, user_profile=profile, context=extra_context or {}
        )

        payload: ExplanationPayload = {
            "concept": concept,
            "explanation": getattr(response, "explanation", "") or "",
            "examples": getattr(response, "examples", []) or [],
            "analogies": getattr(response, "analogies", []) or [],
            "visual_aids": getattr(response, "visual_aids", []) or [],
            "generated_at": _now_iso_utc(),
        }
        return payload

    async def generate_quiz(
        self,
        user_id: str,
        topic: str,
        *,
        difficulty: DifficultyLevel = DifficultyLevel.BEGINNER,
        num_questions: int = DEFAULT_QUIZ_QUESTIONS,
    ) -> QuizPayload:
        """
        Generate a quiz on a financial topic with parallel question creation.

        Args:
            user_id: Unique identifier for the user.
            topic: The quiz topic.
            difficulty: Difficulty level (default: BEGINNER).
            num_questions: Number of questions (1-10).

        Returns:
            Structured quiz payload with unique questions.

        Raises:
            ValueError: If topic is empty or num_questions is invalid.
        """
        topic = (topic or "").strip()
        if not topic:
            raise ValueError("topic must be a non-empty string")
        if num_questions < 1 or num_questions > 10:
            raise ValueError("num_questions must be between 1 and 10")

        profile = self.education_service.user_profiles.get(user_id)
        if profile is None:
            profile = await self.education_service.create_user_learning_profile(
                user_id, {}
            )

        async def _generate_one_question() -> QuizQuestion:
            """Helper to generate a single question."""
            q = await self.education_service.generate_ai_question(
                topic=topic, difficulty=difficulty, user_profile=profile
            )
            return {
                "id": getattr(q, "id", str(uuid.uuid4())),
                "question": getattr(q, "question", "") or "",
                "question_type": getattr(q, "question_type", "") or "",
                "options": getattr(q, "options", None),
                "correct_answer": getattr(q, "correct_answer", None),
                "explanation": getattr(q, "explanation", None),
                "hints": getattr(q, "hints", None),
            }

        # Generate questions concurrently
        questions: List[QuizQuestion] = await asyncio.gather(
            *[_generate_one_question() for _ in range(num_questions)]
        )

        # Deduplicate by question text (case-insensitive)
        seen = set()
        unique_questions: List[QuizQuestion] = []
        for q in questions:
            key = q.get("question", "").strip().lower()
            if key and key not in seen:
                unique_questions.append(q)
                seen.add(key)

        payload: QuizPayload = {
            "topic": topic,
            "difficulty": difficulty.value,
            "questions": unique_questions,
            "generated_at": _now_iso_utc(),
        }
        return payload

    async def evaluate_answer(
        self,
        user_id: str,
        question: str,
        user_answer: str,
        *,
        correct_answer: Optional[str] = None,
        rubric: Optional[str] = None,
        max_tokens: int = DEFAULT_GRADE_TOKENS,
        model: Optional[AIModel] = None,
    ) -> EvaluationResult:
        """
        Evaluate a user's answer against the question with detailed feedback.

        Args:
            user_id: Unique identifier for the user.
            question: The original question.
            user_answer: The user's submitted answer.
            correct_answer: Optional known correct answer.
            rubric: Optional evaluation rubric.
            max_tokens: Maximum tokens for evaluation.
            model: Optional override for the grading model.

        Returns:
            Structured evaluation result with score and tips.

        Raises:
            ValueError: If question or user_answer is empty.
        """
        question = (question or "").strip()
        user_answer = (user_answer or "").strip()
        if not question or not user_answer:
            raise ValueError("question and user_answer must be non-empty strings")

        # Structured prompt for consistent JSON output
        prompt = {
            "task": "grade_answer",
            "question": question,
            "user_answer": user_answer,
            "correct_answer": correct_answer,
            "rubric": rubric,
            "requirements": [
                "Assign a score from 0 to 100 (integer).",
                "Explain strengths and mistakes.",
                "Provide a corrected ideal answer.",
                "Give 1-2 actionable improvement tips.",
            ],
            "output_format": {
                "score": "int",
                "strengths": ["string"],
                "mistakes": ["string"],
                "ideal_answer": "string",
                "improvement_tips": ["string"],
            },
            "response_style": "Return ONLY valid JSON matching output_format. No markdown.",
        }

        req = AIRequest(
            request_id=str(uuid.uuid4()),
            request_type=RequestType.GENERAL_CHAT,
            prompt=json.dumps(prompt),
            context={"user_id": user_id},
            model_preference=model or self.default_grade_model,
            requires_reasoning=True,
            max_tokens=max_tokens,
        )

        logger.debug(
            "AITutorService.evaluate_answer",
            extra={"user_id": user_id, "request_id": req.request_id},
        )

        resp = await asyncio.wait_for(
            self.ai_router.route_request(req), timeout=self.request_timeout_s
        )

        # Parse response as JSON
        parsed = _safe_json_loads(resp.response)
        if parsed is None or not isinstance(parsed, dict):
            # Attempt JSON repair if parsing fails
            repair_prompt = {
                "task": "repair_json",
                "instructions": (
                    "You were asked to output strict JSON. Extract and return ONLY the JSON "
                    "for the evaluation with keys: score, strengths, mistakes, ideal_answer, "
                    "improvement_tips."
                ),
                "raw_model_output": resp.response,
                "schema": {
                    "type": "object",
                    "properties": {
                        "score": {"type": "integer", "minimum": 0, "maximum": 100},
                        "strengths": {"type": "array", "items": {"type": "string"}},
                        "mistakes": {"type": "array", "items": {"type": "string"}},
                        "ideal_answer": {"type": "string"},
                        "improvement_tips": {"type": "array", "items": {"type": "string"}},
                    },
                    "required": [
                        "score",
                        "strengths",
                        "mistakes",
                        "ideal_answer",
                        "improvement_tips",
                    ],
                },
            }
            try:
                repair_req = AIRequest(
                    request_id=str(uuid.uuid4()),
                    request_type=RequestType.TOOLING,  # Fallback to GENERAL_CHAT if needed
                    prompt=json.dumps(repair_prompt),
                    context={"user_id": user_id},
                    model_preference=model or self.default_grade_model,
                    requires_reasoning=False,
                    max_tokens=400,
                )
                repair_resp = await asyncio.wait_for(
                    self.ai_router.route_request(repair_req), timeout=self.request_timeout_s
                )
                parsed = _safe_json_loads(repair_resp.response)
            except Exception:
                parsed = None

        # Fallback if parsing still fails
        if parsed is None or not isinstance(parsed, dict):
            logger.warning(
                "Failed to parse evaluation response; using fallback",
                extra={"user_id": user_id, "response_snippet": resp.response[:100]},
            )
            fallback: EvaluationResult = {
                "score": 70,
                "strengths": ["Clear attempt to answer the question"],
                "mistakes": ["Missing key definition elements"],
                "ideal_answer": "",
                "improvement_tips": [
                    "Study the core definition and provide one concrete example."
                ],
                "confidence_score": getattr(resp, "confidence_score", None),
                "evaluated_at": _now_iso_utc(),
            }
            return fallback

        # Normalize and validate parsed data
        score = parsed.get("score", 0)
        try:
            score = int(score)
        except (ValueError, TypeError):
            score = 0
        score = max(0, min(100, score))

        strengths = parsed.get("strengths") or []
        mistakes = parsed.get("mistakes") or []
        ideal_answer = parsed.get("ideal_answer") or ""
        improvement_tips = parsed.get("improvement_tips") or []

        result: EvaluationResult = {
            "score": score,
            "strengths": [str(s) for s in strengths][:8],
            "mistakes": [str(m) for m in mistakes][:8],
            "ideal_answer": str(ideal_answer),
            "improvement_tips": [str(t) for t in improvement_tips][:4],
            "confidence_score": getattr(resp, "confidence_score", None),
            "evaluated_at": _now_iso_utc(),
        }
        return result
# =============================================================================
# Singleton Instance (Optional for Convenience)
# =============================================================================

aI_tutor_service = AITutorService()
