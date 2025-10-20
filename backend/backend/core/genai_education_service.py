"""
GenAI Education Service - Advanced AI-Powered Learning System
Implements personalized education, AI tutoring, and dynamic content generation
"""

from __future__ import annotations

import os
import asyncio
import json
import logging
import uuid
from dataclasses import dataclass, asdict, field
from datetime import datetime, timezone, timedelta
from enum import Enum
from typing import Dict, List, Optional, Any, Tuple, Union, Callable

from .advanced_ai_router import get_advanced_ai_router, AIRequest, AIResponse, RequestType, AIModel

logger = logging.getLogger(__name__)


# ----------------------------- Enums -----------------------------

class LearningStyle(Enum):
    VISUAL = "visual"
    AUDITORY = "auditory"
    KINESTHETIC = "kinesthetic"
    READING_WRITING = "reading_writing"


class DifficultyLevel(Enum):
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"
    EXPERT = "expert"


class ContentType(Enum):
    TEXT = "text"
    INTERACTIVE = "interactive"
    QUIZ = "quiz"
    EXAMPLE = "example"
    SIMULATION = "simulation"
    VIDEO = "video"


# ----------------------------- Dataclasses -----------------------------

@dataclass
class UserLearningProfile:
    user_id: str
    learning_style: LearningStyle
    current_level: DifficultyLevel
    interests: List[str]
    goals: List[str]
    time_available: int  # minutes per session
    preferred_topics: List[str]
    weak_areas: List[str]
    strong_areas: List[str]
    learning_pace: str  # slow, medium, fast
    last_updated: datetime


@dataclass
class LearningModule:
    id: str
    title: str
    description: str
    content_type: ContentType
    difficulty: DifficultyLevel
    estimated_time: int  # minutes
    prerequisites: List[str]
    learning_objectives: List[str]
    content: Dict[str, Any]
    ai_generated: bool = False
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class PersonalizedLearningPath:
    user_id: str
    path_id: str
    title: str
    description: str
    modules: List[LearningModule]
    estimated_completion_time: int  # minutes
    difficulty_progression: List[DifficultyLevel]
    learning_goals: List[str]
    created_at: datetime
    ai_confidence_score: float


@dataclass
class AIQuestion:
    id: str
    question: str
    question_type: str  # multiple_choice, open_ended, scenario
    difficulty: DifficultyLevel
    topic: str
    options: Optional[List[str]] = None
    correct_answer: Optional[str] = None
    explanation: Optional[str] = None
    hints: Optional[List[str]] = None


@dataclass
class AIExplanation:
    concept: str
    explanation: str
    examples: List[str]
    analogies: List[str]
    visual_aids: List[str]
    difficulty_level: DifficultyLevel
    learning_style_adapted: LearningStyle


# ----------------------------- Helpers -----------------------------

def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()

def _to_iso(dt: datetime) -> str:
    return (dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)).isoformat()

def _enum_parse(enum_cls: Enum, value: Any, default: Enum) -> Enum:
    if isinstance(value, enum_cls):
        return value
    if isinstance(value, str):
        val = value.strip().lower()
        for e in enum_cls:
            if e.value == val or e.name.lower() == val:
                return e
    return default

def _safe_json_loads(text: str) -> Optional[Dict[str, Any]]:
    try:
        return json.loads(text)
    except Exception:
        return None

def _extract_json_block(text: str) -> Optional[Dict[str, Any]]:
    """
    Naive JSON repair: try to find a top-level {...} block.
    Keeps response local (no second model call).
    """
    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1 and end > start:
        return _safe_json_loads(text[start:end+1])
    return None

def _dataclass_to_dict(obj: Any) -> Any:
    """
    Convert dataclasses to JSON-ready dicts:
    - Enums -> .value
    - datetime -> ISO8601 UTC
    - Recurse lists/dicts
    """
    if isinstance(obj, Enum):
        return obj.value
    if isinstance(obj, datetime):
        return _to_iso(obj)
    if hasattr(obj, "__dataclass_fields__"):
        d = {}
        for k, v in asdict(obj).items():
            d[k] = _dataclass_to_dict(v)
        return d
    if isinstance(obj, list):
        return [_dataclass_to_dict(x) for x in obj]
    if isinstance(obj, dict):
        return {k: _dataclass_to_dict(v) for k, v in obj.items()}
    return obj

async def _with_timeout(coro, timeout_s: int):
    return await asyncio.wait_for(coro, timeout=timeout_s)

async def _retry(
    op: Callable[[], Any],
    attempts: int = 3,
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

class GenAIEducationService:
    """Advanced AI-powered education service with robust parsing, caching, and DI."""

    # Tunables
    DEFAULT_PROFILE_MODEL = AIModel.CLAUDE_3_5_SONNET
    DEFAULT_PATH_MODEL = AIModel.GPT_5
    DEFAULT_QUESTION_MODEL = AIModel.CLAUDE_3_5_SONNET
    DEFAULT_EXPLANATION_MODEL = AIModel.GPT_5
    DEFAULT_DYNAMIC_MODEL = AIModel.CLAUDE_3_5_SONNET

    TOKENS_PROFILE = 2000
    TOKENS_PATH = 4000
    TOKENS_QUESTION = 1500
    TOKENS_EXPLANATION = 2000
    TOKENS_DYNAMIC = 3000

    REQUEST_TIMEOUT_S = 35
    RETRY_ATTEMPTS = 2

    # Simple TTL cache for dynamic content (topic/profile/type)
    CACHE_TTL = timedelta(minutes=20)

    def __init__(self, ai_router: Optional["AdvancedAIRouter"] = None):
        self.ai_router = ai_router or get_advanced_ai_router()
        self.user_profiles: Dict[str, UserLearningProfile] = {}
        self.learning_paths: Dict[str, PersonalizedLearningPath] = {}
        # Cache key -> (expires_at, payload)
        self.content_cache: Dict[str, Tuple[datetime, Dict[str, Any]]] = {}

    # ------------------------- Public API -------------------------

    async def create_user_learning_profile(
        self,
        user_id: str,
        initial_data: Dict[str, Any]
    ) -> UserLearningProfile:
        """Create an AI-powered learning profile for the user."""
        initial_data = initial_data or {}
        prompt = (
            "Analyze this user data and create a comprehensive learning profile.\n\n"
            f"User Data: {json.dumps(initial_data, indent=2)}\n\n"
            "Include:\n"
            "1) learning_style (visual, auditory, kinesthetic, reading_writing)\n"
            "2) current_level (beginner, intermediate, advanced, expert)\n"
            "3) interests, goals\n"
            "4) weak_areas, strong_areas\n"
            "5) time_available (minutes/session)\n"
            "6) learning_pace (slow/medium/fast)\n\n"
            "Return STRICT JSON with those keys only."
        )
        req = AIRequest(
            request_id=str(uuid.uuid4()),
            request_type=RequestType.GENERAL_CHAT,
            prompt=prompt,
            context={"user_id": user_id, "task": "create_learning_profile"},
            model_preference=self.DEFAULT_PROFILE_MODEL,
            requires_reasoning=True,
            max_tokens=self.TOKENS_PROFILE,
        )

        async def _op():
            return await _with_timeout(self.ai_router.route_request(req), self.REQUEST_TIMEOUT_S)

        try:
            resp = await _retry(_op, attempts=self.RETRY_ATTEMPTS)
            data = _safe_json_loads(resp.response) or _extract_json_block(resp.response) or {}
            profile = UserLearningProfile(
                user_id=user_id,
                learning_style=_enum_parse(LearningStyle, data.get("learning_style"), LearningStyle.VISUAL),
                current_level=_enum_parse(DifficultyLevel, data.get("current_level"), DifficultyLevel.BEGINNER),
                interests=list(data.get("interests", [])),
                goals=list(data.get("goals", [])),
                time_available=int(data.get("time_available", 30)),
                preferred_topics=list(data.get("preferred_topics", [])),
                weak_areas=list(data.get("weak_areas", [])),
                strong_areas=list(data.get("strong_areas", [])),
                learning_pace=str(data.get("learning_pace", "medium")),
                last_updated=datetime.now(timezone.utc),
            )
            self.user_profiles[user_id] = profile
            return profile
        except Exception as e:
            logger.exception("create_user_learning_profile failed: %s", e)
            return self._create_default_profile(user_id)

    async def generate_personalized_learning_path(
        self,
        user_id: str,
        topic: str,
        time_available: int = 60
    ) -> PersonalizedLearningPath:
        """Generate an AI-powered personalized learning path."""
        topic = (topic or "").strip()
        if not topic:
            raise ValueError("topic must be a non-empty string")

        profile = self.user_profiles.get(user_id) or await self.create_user_learning_profile(user_id, {})

        path_prompt = f"""
Create a personalized learning path for financial education.

User Profile:
- Learning Style: {profile.learning_style.value}
- Current Level: {profile.current_level.value}
- Interests: {profile.interests}
- Goals: {profile.goals}
- Time Available: {time_available} minutes
- Weak Areas: {profile.weak_areas}
- Strong Areas: {profile.strong_areas}
- Learning Pace: {profile.learning_pace}

Topic: {topic}

Requirements:
1) 3–8 modules with building progression
2) Difficulty progression aligned to profile
3) Content types that match learning style
4) Real-world examples & applications
5) Interactive elements & assessments
6) Estimated time for each module (minutes)

Return STRICT JSON: title, description, learning_goals, modules:[{{
  title, description, content_type, difficulty, estimated_time,
  prerequisites[], learning_objectives[], content
}}].
        """.strip()

        req = AIRequest(
            request_id=str(uuid.uuid4()),
            request_type=RequestType.GENERAL_CHAT,
            prompt=path_prompt,
            context={"user_id": user_id, "topic": topic, "profile": _dataclass_to_dict(profile)},
            model_preference=self.DEFAULT_PATH_MODEL,
            requires_reasoning=True,
            max_tokens=self.TOKENS_PATH,
        )

        async def _op():
            return await _with_timeout(self.ai_router.route_request(req), self.REQUEST_TIMEOUT_S)

        try:
            resp = await _retry(_op, attempts=self.RETRY_ATTEMPTS)
            data = _safe_json_loads(resp.response) or _extract_json_block(resp.response) or {}
            modules: List[LearningModule] = []
            for m in data.get("modules", []):
                content_type = _enum_parse(ContentType, m.get("content_type", "text"), ContentType.TEXT)
                difficulty = _enum_parse(DifficultyLevel, m.get("difficulty", "beginner"), DifficultyLevel.BEGINNER)
                est = int(m.get("estimated_time", 10))
                est = max(3, min(240, est))  # clamp 3min..4h
                module = LearningModule(
                    id=str(uuid.uuid4()),
                    title=str(m.get("title", "Untitled Module")).strip(),
                    description=str(m.get("description", "")).strip(),
                    content_type=content_type,
                    difficulty=difficulty,
                    estimated_time=est,
                    prerequisites=list(m.get("prerequisites", [])),
                    learning_objectives=list(m.get("learning_objectives", [])),
                    content=dict(m.get("content", {})),
                    ai_generated=True,
                )
                modules.append(module)

            learning_path = PersonalizedLearningPath(
                user_id=user_id,
                path_id=str(uuid.uuid4()),
                title=str(data.get("title", f"Learning Path: {topic}")),
                description=str(data.get("description", "")),
                modules=modules,
                estimated_completion_time=sum(m.estimated_time for m in modules) if modules else 60,
                difficulty_progression=[m.difficulty for m in modules] or [profile.current_level],
                learning_goals=list(data.get("learning_goals", [])),
                created_at=datetime.now(timezone.utc),
                ai_confidence_score=float(getattr(resp, "confidence_score", 0.0) or 0.0),
            )
            self.learning_paths[learning_path.path_id] = learning_path
            return learning_path

        except Exception as e:
            logger.exception("generate_personalized_learning_path failed: %s", e)
            return self._create_fallback_learning_path(user_id, topic)

    async def generate_ai_question(
        self,
        topic: str,
        difficulty: DifficultyLevel,
        user_profile: UserLearningProfile
    ) -> AIQuestion:
        """Generate an AI-powered educational question."""
        topic = (topic or "").strip()
        if not topic:
            raise ValueError("topic must be a non-empty string")

        prompt = f"""
Create an educational question about "{topic}".

Difficulty: {difficulty.value}
Learning Style: {user_profile.learning_style.value}
User Level: {user_profile.current_level.value}

Requirements:
1) Test a key concept
2) Match learning style
3) Fit the user's level
4) Include clear explanation
5) Provide 1–2 helpful hints

Return STRICT JSON with keys: question, question_type, options (if multiple_choice), correct_answer, explanation, hints.
        """.strip()

        req = AIRequest(
            request_id=str(uuid.uuid4()),
            request_type=RequestType.GENERAL_CHAT,
            prompt=prompt,
            context={"topic": topic, "difficulty": difficulty.value, "user_profile": _dataclass_to_dict(user_profile)},
            model_preference=self.DEFAULT_QUESTION_MODEL,
            requires_reasoning=True,
            max_tokens=self.TOKENS_QUESTION,
        )

        async def _op():
            return await _with_timeout(self.ai_router.route_request(req), self.REQUEST_TIMEOUT_S)

        try:
            resp = await _retry(_op, attempts=self.RETRY_ATTEMPTS)
            data = _safe_json_loads(resp.response) or _extract_json_block(resp.response) or {}
            qtext = str(data.get("question", f"What is the basic concept of {topic}?")).strip()
            qtype = str(data.get("question_type", "multiple_choice")).strip()
            options = data.get("options")
            if options is not None:
                options = [str(o) for o in options][:8] or None
            hints = data.get("hints")
            if hints is not None:
                hints = [str(h) for h in hints][:4] or None
            return AIQuestion(
                id=str(uuid.uuid4()),
                question=qtext,
                question_type=qtype,
                difficulty=difficulty,
                topic=topic,
                options=options,
                correct_answer=(str(data.get("correct_answer")) if data.get("correct_answer") is not None else None),
                explanation=str(data.get("explanation", "")) or None,
                hints=hints,
            )
        except Exception as e:
            logger.exception("generate_ai_question failed: %s", e)
            return self._create_fallback_question(topic, difficulty)

    async def generate_ai_explanation(
        self,
        concept: str,
        user_profile: UserLearningProfile,
        context: Optional[Dict[str, Any]] = None
    ) -> AIExplanation:
        """Generate an AI explanation tailored to the user."""
        concept = (concept or "").strip()
        if not concept:
            raise ValueError("concept must be a non-empty string")

        prompt = f"""
Explain the financial concept "{concept}" for this user.

User Profile:
- Learning Style: {user_profile.learning_style.value}
- Level: {user_profile.current_level.value}
- Interests: {user_profile.interests}
- Weak Areas: {user_profile.weak_areas}

Context: {json.dumps(context or {}, indent=2)}

Requirements:
1) Match learning style (visual analogies, step-by-step, etc.)
2) Fit user's level
3) Use examples relevant to interests
4) Address weak areas
5) Include multiple analogies & examples
6) Suggest visual aids if helpful

Return STRICT JSON: explanation, examples[], analogies[], visual_aids[].
        """.strip()

        req = AIRequest(
            request_id=str(uuid.uuid4()),
            request_type=RequestType.GENERAL_CHAT,
            prompt=prompt,
            context={"concept": concept, "user_profile": _dataclass_to_dict(user_profile), "context": context},
            model_preference=self.DEFAULT_EXPLANATION_MODEL,
            requires_reasoning=True,
            max_tokens=self.TOKENS_EXPLANATION,
        )

        async def _op():
            return await _with_timeout(self.ai_router.route_request(req), self.REQUEST_TIMEOUT_S)

        try:
            resp = await _retry(_op, attempts=self.RETRY_ATTEMPTS)
            data = _safe_json_loads(resp.response) or _extract_json_block(resp.response) or {}
            return AIExplanation(
                concept=concept,
                explanation=str(data.get("explanation", f"{concept} is an important financial concept.")),
                examples=[str(x) for x in data.get("examples", [])][:8],
                analogies=[str(x) for x in data.get("analogies", [])][:6],
                visual_aids=[str(x) for x in data.get("visual_aids", [])][:6],
                difficulty_level=user_profile.current_level,
                learning_style_adapted=user_profile.learning_style,
            )
        except Exception as e:
            logger.exception("generate_ai_explanation failed: %s", e)
            return self._create_fallback_explanation(concept, user_profile)

    async def generate_dynamic_content(
        self,
        content_type: Union[str, ContentType],
        topic: str,
        user_profile: UserLearningProfile,
        market_context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Generate dynamic educational content based on current market conditions.
        Uses simple TTL caching to reduce latency and cost.
        """
        topic = (topic or "").strip()
        if not topic:
            raise ValueError("topic must be a non-empty string")

        ctype = _enum_parse(ContentType, content_type, ContentType.TEXT)
        cache_key = f"{user_profile.user_id}:{ctype.value}:{topic}"

        # TTL cache check
        cached = self.content_cache.get(cache_key)
        now = datetime.now(timezone.utc)
        if cached and cached[0] > now:
            return cached[1]

        prompt = f"""
Create {ctype.value} educational content about "{topic}".

User Profile:
- Learning Style: {user_profile.learning_style.value}
- Level: {user_profile.current_level.value}
- Interests: {user_profile.interests}

Current Market Context: {json.dumps(market_context or {}, indent=2)}

Requirements:
1) Relevance to current market conditions
2) Real examples from today's market (or simulated if unavailable)
3) Match user's learning style
4) Fit user's level
5) Include interactive elements if applicable
6) Provide actionable insights

Return STRICT JSON content.
        """.strip()

        req = AIRequest(
            request_id=str(uuid.uuid4()),
            request_type=RequestType.GENERAL_CHAT,
            prompt=prompt,
            context={
                "content_type": ctype.value,
                "topic": topic,
                "user_profile": _dataclass_to_dict(user_profile),
                "market_context": market_context,
            },
            model_preference=self.DEFAULT_DYNAMIC_MODEL,
            requires_reasoning=True,
            max_tokens=self.TOKENS_DYNAMIC,
        )

        async def _op():
            return await _with_timeout(self.ai_router.route_request(req), self.REQUEST_TIMEOUT_S)

        try:
            resp = await _retry(_op, attempts=self.RETRY_ATTEMPTS)
            data = _safe_json_loads(resp.response) or _extract_json_block(resp.response) or {}
            data["ai_generated"] = True
            data["generated_at"] = _utc_now_iso()
            data["confidence_score"] = float(getattr(resp, "confidence_score", 0.0) or 0.0)
            # cache it
            self.content_cache[cache_key] = (now + self.CACHE_TTL, data)
            return data
        except Exception as e:
            logger.exception("generate_dynamic_content failed: %s", e)
            return self._create_fallback_content(ctype.value, topic)

    # ------------------------- Fallbacks -------------------------

    def _create_default_profile(self, user_id: str) -> UserLearningProfile:
        return UserLearningProfile(
            user_id=user_id,
            learning_style=LearningStyle.VISUAL,
            current_level=DifficultyLevel.BEGINNER,
            interests=["investing", "trading"],
            goals=["learn basics", "build portfolio"],
            time_available=30,
            preferred_topics=["stocks", "options"],
            weak_areas=["risk management"],
            strong_areas=[],
            learning_pace="medium",
            last_updated=datetime.now(timezone.utc),
        )

    def _create_fallback_learning_path(self, user_id: str, topic: str) -> PersonalizedLearningPath:
        return PersonalizedLearningPath(
            user_id=user_id,
            path_id=str(uuid.uuid4()),
            title=f"Basic {topic} Learning Path",
            description="A structured approach to learning the fundamentals.",
            modules=[],
            estimated_completion_time=60,
            difficulty_progression=[DifficultyLevel.BEGINNER],
            learning_goals=["Understand basics"],
            created_at=datetime.now(timezone.utc),
            ai_confidence_score=0.0,
        )

    def _create_fallback_question(self, topic: str, difficulty: DifficultyLevel) -> AIQuestion:
        return AIQuestion(
            id=str(uuid.uuid4()),
            question=f"What is the basic concept of {topic}?",
            question_type="open_ended",
            difficulty=difficulty,
            topic=topic,
            explanation="This is a fundamental concept in financial education.",
        )

    def _create_fallback_explanation(self, concept: str, user_profile: UserLearningProfile) -> AIExplanation:
        return AIExplanation(
            concept=concept,
            explanation=f"{concept} is an important financial concept to understand.",
            examples=[],
            analogies=[],
            visual_aids=[],
            difficulty_level=user_profile.current_level,
            learning_style_adapted=user_profile.learning_style,
        )

    def _create_fallback_content(self, content_type: str, topic: str) -> Dict[str, Any]:
        return {
            "content_type": content_type,
            "topic": topic,
            "content": f"Basic information about {topic}",
            "ai_generated": False,
            "generated_at": _utc_now_iso(),
            "confidence_score": 0.0,
        }


# Global instance (optional)
genai_education_service = GenAIEducationService()
