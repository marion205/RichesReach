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
from .ml_service import MLService

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
    regime_context: Optional[Dict[str, Any]]  # Market regime context for adaptive quizzes
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

    async def generate_regime_adaptive_quiz(
        self,
        user_id: str,
        market_data: Optional[Dict[str, Any]] = None,
        *,
        difficulty: Optional[DifficultyLevel] = None,
        num_questions: int = 3,
        max_tokens: int = 1500,
        model: Optional[AIModel] = None,
    ) -> QuizPayload:
        """
        Generate a quiz that adapts to current market regime conditions.
        
        This is the key differentiator - creates educational content that's
        immediately relevant to current market conditions, helping users
        understand why certain strategies work in specific regimes.
        
        Args:
            user_id: User identifier for personalization
            market_data: Current market data for regime detection
            difficulty: Quiz difficulty level
            num_questions: Number of questions to generate
            max_tokens: Maximum tokens for AI response
            model: AI model to use for generation
            
        Returns:
            QuizPayload with regime-specific questions and context
        """
        try:
            # Get current market regime
            ml_service = MLService()
            regime_prediction = ml_service.predict_market_regime(market_data or {})
            current_regime = regime_prediction.get('regime', 'sideways_consolidation')
            regime_confidence = regime_prediction.get('confidence', 0.5)
            
            # Get user learning profile for personalization
            user_profile = await self.education_service.get_user_learning_profile(user_id)
            if difficulty is None:
                difficulty = user_profile.get('preferred_difficulty', DifficultyLevel.INTERMEDIATE)
            
            # Create regime-specific quiz prompt
            regime_context = {
                'current_regime': current_regime,
                'regime_confidence': regime_confidence,
                'regime_description': self._get_regime_description(current_regime),
                'relevant_strategies': self._get_regime_strategies(current_regime),
                'common_mistakes': self._get_regime_mistakes(current_regime)
            }
            
            prompt = self._build_regime_quiz_prompt(
                current_regime, regime_context, difficulty, num_questions
            )
            
            # Generate quiz using AI
            request = AIRequest(
                prompt=prompt,
                max_tokens=max_tokens,
                model=model or self.default_chat_model,
                request_type=RequestType.GENERAL_CHAT,
                temperature=0.7,  # Slightly creative for engaging questions
            )
            
            resp = await self.ai_router.route_request(request)
            if not resp or not resp.response:
                raise ValueError("Failed to generate regime-adaptive quiz")
            
            # Parse and structure the response
            parsed = _safe_json_loads(resp.response)
            if not parsed:
                # Fallback to structured generation
                parsed = await self._generate_fallback_regime_quiz(
                    current_regime, regime_context, difficulty, num_questions
                )
            
            # Build quiz payload with regime context
            quiz_id = str(uuid.uuid4())
            questions = self._parse_quiz_questions(parsed.get('questions', []), quiz_id)
            
            payload: QuizPayload = {
                "topic": f"Market Regime: {current_regime.replace('_', ' ').title()}",
                "difficulty": difficulty.value,
                "questions": questions,
                "generated_at": _now_iso_utc(),
                "regime_context": regime_context,
            }
            
            logger.info(f"Generated regime-adaptive quiz for user {user_id}: {current_regime} regime")
            return payload
            
        except Exception as e:
            logger.error(f"Error generating regime-adaptive quiz: {e}")
            # Return a fallback quiz
            return await self._generate_fallback_regime_quiz(
                'sideways_consolidation', {}, difficulty or DifficultyLevel.INTERMEDIATE, num_questions
            )

    def _get_regime_description(self, regime: str) -> str:
        """Get human-readable description of market regime."""
        descriptions = {
            'early_bull_market': 'Strong growth phase with low volatility and rising prices',
            'late_bull_market': 'High growth phase with increasing volatility and potential overvaluation',
            'correction': 'Temporary pullback in an overall bull market trend',
            'bear_market': 'Sustained decline with high volatility and negative sentiment',
            'sideways_consolidation': 'Range-bound market with low volatility and uncertain direction',
            'high_volatility': 'Uncertain market conditions with elevated volatility',
            'recovery': 'Market bouncing back from a previous decline',
            'bubble_formation': 'Excessive optimism with high valuations and speculation'
        }
        return descriptions.get(regime, 'Uncertain market conditions')

    def _get_regime_strategies(self, regime: str) -> List[str]:
        """Get relevant trading strategies for the current regime."""
        strategies = {
            'early_bull_market': ['Growth investing', 'Momentum trading', 'Buy and hold'],
            'late_bull_market': ['Value investing', 'Defensive positioning', 'Profit taking'],
            'correction': ['Dollar-cost averaging', 'Quality stock selection', 'Sector rotation'],
            'bear_market': ['Short selling', 'Put options', 'Defensive stocks', 'Cash positions'],
            'sideways_consolidation': ['Range trading', 'Options strategies', 'Dividend investing'],
            'high_volatility': ['Volatility trading', 'Options strategies', 'Risk management'],
            'recovery': ['Value investing', 'Cyclical stocks', 'Gradual re-entry'],
            'bubble_formation': ['Contrarian investing', 'Risk management', 'Exit strategies']
        }
        return strategies.get(regime, ['General investing principles'])

    def _get_regime_mistakes(self, regime: str) -> List[str]:
        """Get common mistakes to avoid in the current regime."""
        mistakes = {
            'early_bull_market': ['FOMO buying', 'Ignoring fundamentals', 'Over-leveraging'],
            'late_bull_market': ['Chasing momentum', 'Ignoring valuations', 'No exit strategy'],
            'correction': ['Panic selling', 'Trying to time the bottom', 'Ignoring quality'],
            'bear_market': ['Buying the dip too early', 'Ignoring risk management', 'Emotional trading'],
            'sideways_consolidation': ['Overtrading', 'Ignoring fundamentals', 'Poor timing'],
            'high_volatility': ['Panic reactions', 'Poor risk management', 'Ignoring position sizing'],
            'recovery': ['Missing the opportunity', 'Being too cautious', 'Poor stock selection'],
            'bubble_formation': ['FOMO investing', 'Ignoring valuations', 'No risk management']
        }
        return mistakes.get(regime, ['Poor risk management', 'Emotional trading'])

    def _build_regime_quiz_prompt(
        self, 
        regime: str, 
        regime_context: Dict[str, Any], 
        difficulty: DifficultyLevel, 
        num_questions: int
    ) -> str:
        """Build a comprehensive prompt for regime-adaptive quiz generation."""
        return f"""
You are an expert financial educator creating a quiz about trading and investing in a {regime.replace('_', ' ')} market.

CURRENT MARKET REGIME: {regime.replace('_', ' ').title()}
DESCRIPTION: {regime_context['regime_description']}
CONFIDENCE: {regime_context['regime_confidence']:.1%}

RELEVANT STRATEGIES: {', '.join(regime_context['relevant_strategies'])}
COMMON MISTAKES: {', '.join(regime_context['common_mistakes'])}

Create {num_questions} quiz questions at {difficulty.value} level that help users understand:
1. Why certain strategies work in this market regime
2. How to identify and avoid common mistakes
3. Practical applications of regime-specific knowledge
4. Risk management considerations

Each question should be:
- Directly relevant to the current market regime
- Educational and practical
- Include clear explanations
- Test understanding, not memorization

Format your response as JSON:
{{
    "questions": [
        {{
            "id": "q1",
            "question": "Question text here",
            "question_type": "multiple_choice",
            "options": ["A", "B", "C", "D"],
            "correct_answer": "B",
            "explanation": "Detailed explanation of why this is correct and how it applies to {regime} markets",
            "hints": ["Hint 1", "Hint 2"]
        }}
    ]
}}

Make the questions immediately actionable for someone trading in this market regime.
"""

    async def _generate_fallback_regime_quiz(
        self, 
        regime: str, 
        regime_context: Dict[str, Any], 
        difficulty: DifficultyLevel, 
        num_questions: int
    ) -> Dict[str, Any]:
        """Generate a fallback quiz when AI generation fails."""
        quiz_id = str(uuid.uuid4())
        questions = []
        
        # Create regime-specific fallback questions
        for i in range(num_questions):
            question_id = f"{quiz_id}_q{i+1}"
            questions.append({
                "id": question_id,
                "question": f"In a {regime.replace('_', ' ')} market, what is the most important consideration?",
                "question_type": "multiple_choice",
                "options": [
                    "Maximize returns at all costs",
                    "Manage risk appropriately",
                    "Follow the crowd",
                    "Ignore market conditions"
                ],
                "correct_answer": "Manage risk appropriately",
                "explanation": f"In {regime.replace('_', ' ')} markets, risk management is crucial. This regime requires careful consideration of position sizing, stop losses, and portfolio allocation.",
                "hints": ["Think about what changes in different market conditions", "Consider the importance of capital preservation"]
            })
        
        return {"questions": questions}

    def _parse_quiz_questions(self, questions_data: List[Dict], quiz_id: str) -> List[QuizQuestion]:
        """Parse and validate quiz questions from AI response."""
        questions = []
        for i, q_data in enumerate(questions_data):
            question: QuizQuestion = {
                "id": q_data.get("id", f"{quiz_id}_q{i+1}"),
                "question": str(q_data.get("question", "")),
                "question_type": str(q_data.get("question_type", "multiple_choice")),
                "options": q_data.get("options", []),
                "correct_answer": str(q_data.get("correct_answer", "")),
                "explanation": str(q_data.get("explanation", "")),
                "hints": q_data.get("hints", []) or [],
            }
            questions.append(question)
        return questions
# =============================================================================
# Singleton Instance (Optional for Convenience)
# =============================================================================

aI_tutor_service = AITutorService()
