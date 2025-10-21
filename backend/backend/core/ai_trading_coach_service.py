"""
AI Trading Coach Service - GenAI-Powered Strategy Advisor
=========================================================

Advanced AI coach for trading education and guidance.
Integrates with AdvancedAIRouter for multi-model AI and GenAIEducationService for personalization.

Key Features:
- Personalized strategy recommendations based on user profile, risk, goals, and market data
- Real-time step-by-step trading guidance
- Post-trade analysis for mistakes and successes
- Confidence-building explanations with rationale and simulations

Design Notes:
- Builds on UserLearningProfile for personalization
- Uses structured JSON prompts for reliable AI outputs
- Integrates Redis caching from GenAIEducationService (optional injection)
- All timestamps in UTC ISO8601
- Fallbacks for API errors or low-confidence responses

Dependencies:
- advanced_ai_router: For AI routing
- genai_education_service: For user profiles and content gen
"""

import asyncio
import json
import uuid
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, TypedDict
from dataclasses import dataclass, asdict

from .advanced_ai_router import AdvancedAIRouter, AIRequest, AIResponse, RequestType, AIModel
from .genai_education_service import GenAIEducationService, UserLearningProfile, DifficultyLevel

logger = logging.getLogger(__name__)


# =============================================================================
# Typed Payloads
# =============================================================================

class StrategyRecommendation(TypedDict, total=False):
    """Payload for personalized trading strategies."""
    strategy_name: str
    description: str
    risk_level: str  # "low", "medium", "high"
    expected_return: Optional[float]
    suitable_for: List[str]  # e.g., ["beginner options traders"]
    steps: List[str]
    market_conditions: Dict[str, Any]
    confidence_score: float
    generated_at: str  # ISO8601 UTC


class TradingGuidance(TypedDict, total=False):
    """Payload for real-time trading steps."""
    current_step: int
    total_steps: int
    action: str
    rationale: str
    risk_check: str
    next_decision_point: str
    session_id: str
    updated_at: str  # ISO8601 UTC


class TradeAnalysis(TypedDict, total=False):
    """Payload for post-trade review."""
    trade_id: str
    entry: Dict[str, Any]  # price, time, etc.
    exit: Dict[str, Any]
    pnl: float  # profit/loss
    strengths: List[str]
    mistakes: List[str]
    lessons_learned: List[str]
    improved_strategy: str
    confidence_boost: str  # motivational note
    analyzed_at: str  # ISO8601 UTC


# =============================================================================
# Data Models
# =============================================================================

@dataclass
class TradingSession:
    """Active trading session state."""
    session_id: str
    user_id: str
    asset: str
    strategy: str
    risk_tolerance: str  # "conservative", "moderate", "aggressive"
    goals: List[str]
    current_step: int = 0
    history: List[Dict[str, Any]] = None
    started_at: datetime = None
    ai_confidence: float = 0.0

    def __post_init__(self):
        if self.history is None:
            self.history = []
        if self.started_at is None:
            self.started_at = datetime.now(timezone.utc)


# =============================================================================
# Utility Functions
# =============================================================================

def _now_iso_utc() -> str:
    """Current UTC ISO timestamp."""
    return datetime.now(timezone.utc).isoformat()


def _safe_json_loads(s: str) -> Optional[Dict[str, Any]]:
    """Safe JSON parsing."""
    try:
        return json.loads(s)
    except json.JSONDecodeError:
        logger.warning(f"JSON parse failed: {s[:100]}...")
        return None


# =============================================================================
# Main Service Class
# =============================================================================

class AITradingCoachService:
    """
    GenAI-powered trading coach for personalized guidance and analysis.
    """

    # Defaults
    DEFAULT_MAX_TOKENS_STRATEGY = 1500
    DEFAULT_MAX_TOKENS_GUIDANCE = 800
    DEFAULT_MAX_TOKENS_ANALYSIS = 1200
    DEFAULT_TIMEOUT_SECONDS = 30
    DEFAULT_CONFIDENCE_THRESHOLD = 0.7

    def __init__(
        self,
        ai_router: Optional[AdvancedAIRouter] = None,
        education_service: Optional[GenAIEducationService] = None,
        *,
        default_strategy_model: AIModel = AIModel.GPT_5,
        default_guidance_model: AIModel = AIModel.CLAUDE_3_5_SONNET,
        default_analysis_model: AIModel = AIModel.GEMINI_PRO,
        request_timeout_s: int = DEFAULT_TIMEOUT_SECONDS,
    ) -> None:
        self.ai_router = ai_router or AdvancedAIRouter()
        self.education_service = education_service or GenAIEducationService()
        self.default_strategy_model = default_strategy_model
        self.default_guidance_model = default_guidance_model
        self.default_analysis_model = default_analysis_model
        self.request_timeout_s = request_timeout_s
        self.active_sessions: Dict[str, TradingSession] = {}  # In-memory session store

    # -------------------------------------------------------------------------
    # Public API: Personalized Strategy Recommendations
    # -------------------------------------------------------------------------

    async def recommend_strategy(
        self,
        user_id: str,
        asset: str,
        risk_tolerance: str = "moderate",
        goals: Optional[List[str]] = None,
        market_data: Optional[Dict[str, Any]] = None,  # e.g., {"volatility": "high", "trend": "bullish"}
    ) -> StrategyRecommendation:
        """
        Generate personalized options trading strategies.

        Args:
            user_id: User identifier.
            asset: e.g., "AAPL options".
            risk_tolerance: "conservative", "moderate", "aggressive".
            goals: e.g., ["income generation", "hedging"].
            market_data: Current market snapshot.

        Returns:
            Structured strategy recommendation.
        """
        if not asset or not user_id:
            raise ValueError("user_id and asset required")

        profile = self.education_service.user_profiles.get(user_id)
        if not profile:
            profile = await self.education_service.create_user_learning_profile(user_id, {})

        prompt = self._build_strategy_prompt(profile, asset, risk_tolerance, goals or [], market_data or {})

        # Convert profile to dict for JSON serialization
        profile_dict = {
            "learning_style": profile.learning_style.value,
            "current_level": profile.current_level.value,
            "interests": profile.interests,
            "weak_areas": profile.weak_areas,
            "strong_areas": profile.strong_areas,
            "learning_pace": profile.learning_pace,
            "time_available": profile.time_available,
        }

        req = AIRequest(
            request_id=str(uuid.uuid4()),
            request_type=RequestType.GENERAL_CHAT,
            prompt=prompt,
            context={
                "user_id": user_id,
                "asset": asset,
                "risk_tolerance": risk_tolerance,
                "profile": profile_dict,
            },
            model_preference=self.default_strategy_model,
            requires_reasoning=True,
            max_tokens=self.DEFAULT_MAX_TOKENS_STRATEGY,
        )

        logger.debug(f"Generating strategy for user {user_id}, asset {asset}")
        resp = await asyncio.wait_for(self.ai_router.route_request(req), timeout=self.request_timeout_s)

        recommendation = self._parse_strategy_response(resp, asset)
        if recommendation and recommendation.get("confidence_score", 0) < self.DEFAULT_CONFIDENCE_THRESHOLD:
            logger.warning(f"Low confidence strategy for {user_id}: {recommendation['confidence_score']}")
            # Optional: Regenerate with alternative model

        return recommendation or self._create_fallback_strategy(asset, risk_tolerance)

    # -------------------------------------------------------------------------
    # Public API: Real-time Trading Guidance
    # -------------------------------------------------------------------------

    async def provide_trading_guidance(
        self,
        session_id: str,
        current_market_update: Optional[Dict[str, Any]] = None,  # e.g., {"price": 150.5, "volume": 1000000}
    ) -> TradingGuidance:
        """
        Step-by-step guidance for an active trading session.

        Args:
            session_id: Active session ID.
            current_market_update: Latest market data.

        Returns:
            Next guidance step.
        """
        session = self.active_sessions.get(session_id)
        if not session:
            raise ValueError(f"Session {session_id} not found. Start a new one.")

        prompt = self._build_guidance_prompt(session, current_market_update or {})

        req = AIRequest(
            request_id=str(uuid.uuid4()),
            request_type=RequestType.GENERAL_CHAT,
            prompt=prompt,
            context={
                "session_id": session_id,
                "current_step": session.current_step,
                "market_update": current_market_update or {},
            },
            model_preference=self.default_guidance_model,
            requires_reasoning=True,
            max_tokens=self.DEFAULT_MAX_TOKENS_GUIDANCE,
        )

        logger.debug(f"Guidance for session {session_id}, step {session.current_step}")
        resp = await asyncio.wait_for(self.ai_router.route_request(req), timeout=self.request_timeout_s)

        guidance = self._parse_guidance_response(resp, session_id)
        if guidance:
            session.current_step = guidance["current_step"]
            session.ai_confidence = guidance.get("confidence_score", session.ai_confidence)
            session.history.append({"step": session.current_step, "guidance": guidance})
            self.active_sessions[session_id] = session  # Update state

        return guidance or self._create_fallback_guidance(session_id, session.current_step)

    async def start_trading_session(
        self,
        user_id: str,
        asset: str,
        strategy: str,
        risk_tolerance: str,
        goals: List[str],
    ) -> str:
        """Initialize a new trading session."""
        session_id = str(uuid.uuid4())
        session = TradingSession(
            session_id=session_id,
            user_id=user_id,
            asset=asset,
            strategy=strategy,
            risk_tolerance=risk_tolerance,
            goals=goals,
        )
        self.active_sessions[session_id] = session
        logger.info(f"Started session {session_id} for user {user_id}")
        return session_id

    async def end_trading_session(self, session_id: str) -> Dict[str, Any]:
        """End session and return summary."""
        session = self.active_sessions.pop(session_id, None)
        if not session:
            raise ValueError(f"Session {session_id} not found")
        summary = {
            "session_id": session_id,
            "total_steps": session.current_step,
            "final_confidence": session.ai_confidence,
            "history_length": len(session.history),
            "ended_at": _now_iso_utc(),
        }
        logger.info(f"Ended session {session_id}")
        return summary

    # -------------------------------------------------------------------------
    # Public API: Mistake Analysis
    # -------------------------------------------------------------------------

    async def analyze_trade(
        self,
        user_id: str,
        trade_data: Dict[str, Any],  # e.g., {"entry_price": 100, "exit_price": 105, "pnl": 5, "notes": "..."}
    ) -> TradeAnalysis:
        """
        Analyze a completed trade for insights.

        Args:
            user_id: User identifier.
            trade_data: Details of the trade.

        Returns:
            Structured analysis.
        """
        if not trade_data.get("entry") or not trade_data.get("exit"):
            raise ValueError("Trade data must include entry and exit details")

        profile = self.education_service.user_profiles.get(user_id)
        if not profile:
            profile = await self.education_service.create_user_learning_profile(user_id, {})

        trade_id = trade_data.get("trade_id", str(uuid.uuid4()))
        prompt = self._build_analysis_prompt(profile, trade_data, trade_id)

        # Convert profile to dict for JSON serialization
        profile_dict = {
            "learning_style": profile.learning_style.value,
            "current_level": profile.current_level.value,
            "interests": profile.interests,
            "weak_areas": profile.weak_areas,
            "strong_areas": profile.strong_areas,
            "learning_pace": profile.learning_pace,
            "time_available": profile.time_available,
        }

        req = AIRequest(
            request_id=str(uuid.uuid4()),
            request_type=RequestType.GENERAL_CHAT,
            prompt=prompt,
            context={
                "user_id": user_id,
                "trade_id": trade_id,
                "trade_data": trade_data,
                "profile": profile_dict,
            },
            model_preference=self.default_analysis_model,
            requires_reasoning=True,
            max_tokens=self.DEFAULT_MAX_TOKENS_ANALYSIS,
        )

        logger.debug(f"Analyzing trade {trade_id} for user {user_id}")
        resp = await asyncio.wait_for(self.ai_router.route_request(req), timeout=self.request_timeout_s)

        analysis = self._parse_analysis_response(resp, trade_id, trade_data)
        return analysis or self._create_fallback_analysis(trade_id, trade_data)

    # -------------------------------------------------------------------------
    # Public API: Confidence Building
    # -------------------------------------------------------------------------

    async def build_confidence(
        self,
        user_id: str,
        context: str,  # e.g., "Why should I buy this call option?"
        trade_simulation: Optional[Dict[str, Any]] = None,  # Hypothetical trade data
    ) -> Dict[str, Any]:
        """
        Provide explanatory rationale to build user confidence.

        Args:
            user_id: User identifier.
            context: Specific question or scenario.
            trade_simulation: Optional sim data for "what-if" analysis.

        Returns:
            Explanation with rationale and tips.
        """
        profile = self.education_service.user_profiles.get(user_id)
        if not profile:
            profile = await self.education_service.create_user_learning_profile(user_id, {})

        prompt = self._build_confidence_prompt(profile, context, trade_simulation or {})

        # Convert profile to dict for JSON serialization
        profile_dict = {
            "learning_style": profile.learning_style.value,
            "current_level": profile.current_level.value,
            "interests": profile.interests,
            "weak_areas": profile.weak_areas,
            "strong_areas": profile.strong_areas,
            "learning_pace": profile.learning_pace,
            "time_available": profile.time_available,
        }

        req = AIRequest(
            request_id=str(uuid.uuid4()),
            request_type=RequestType.GENERAL_CHAT,
            prompt=prompt,
            context={
                "user_id": user_id,
                "context": context,
                "profile": profile_dict,
            },
            model_preference=self.default_strategy_model,  # Reuse for explanatory depth
            requires_reasoning=True,
            max_tokens=self.DEFAULT_MAX_TOKENS_GUIDANCE,
        )

        logger.debug(f"Building confidence for user {user_id}: {context[:50]}...")
        resp = await asyncio.wait_for(self.ai_router.route_request(req), timeout=self.request_timeout_s)

        explanation = self._parse_confidence_response(resp, context)
        return explanation or self._create_fallback_confidence(context)

    # -------------------------------------------------------------------------
    # Internal Prompt Builders
    # -------------------------------------------------------------------------

    def _build_strategy_prompt(
        self,
        profile: UserLearningProfile,
        asset: str,
        risk_tolerance: str,
        goals: List[str],
        market_data: Dict[str, Any],
    ) -> str:
        """Prompt for strategy recommendation."""
        return f"""
        As a certified trading coach with 15+ years in options, recommend a strategy for {asset}.

        User Profile:
        - Learning Style: {profile.learning_style.value}
        - Experience Level: {profile.current_level.value}
        - Risk Tolerance: {risk_tolerance}
        - Goals: {', '.join(goals)}
        - Market Data: {json.dumps(market_data, indent=2)}

        Recommend 1 primary strategy (e.g., covered call, iron condor) that:
        1. Matches risk tolerance and goals
        2. Adapts to current market (e.g., high vol -> spreads)
        3. Includes 3-5 implementation steps
        4. Estimates expected return (realistic range)
        5. Explains suitability for user's level

        Output ONLY valid JSON:
        {{
            "strategy_name": "string",
            "description": "string",
            "risk_level": "low|medium|high",
            "expected_return": float,
            "suitable_for": ["string"],
            "steps": ["string"],
            "market_conditions": {{}},
            "confidence_score": float (0-1)
        }}
        Think step-by-step: Analyze market -> Match profile -> Select strategy -> Validate.
        """

    def _build_guidance_prompt(
        self,
        session: TradingSession,
        market_update: Dict[str, Any],
    ) -> str:
        """Prompt for next trading step."""
        return f"""
        Provide next guidance step for trading session on {session.asset} using {session.strategy}.

        Session State:
        - Current Step: {session.current_step}
        - Risk Tolerance: {session.risk_tolerance}
        - Goals: {', '.join(session.goals)}
        - Market Update: {json.dumps(market_update, indent=2)}
        - History: {json.dumps(session.history[-2:], indent=2)}  # Last 2 steps

        Guidance should:
        1. Be actionable (e.g., "Place limit order at $X")
        2. Include rationale and risk check
        3. Suggest next decision point (e.g., "If price > $Y, exit")
        4. Advance to next logical step

        Output ONLY valid JSON:
        {{
            "current_step": int,
            "total_steps": int (estimate total),
            "action": "string",
            "rationale": "string",
            "risk_check": "string",
            "next_decision_point": "string",
            "confidence_score": float
        }}
        """

    def _build_analysis_prompt(
        self,
        profile: UserLearningProfile,
        trade_data: Dict[str, Any],
        trade_id: str,
    ) -> str:
        """Prompt for trade analysis."""
        pnl = trade_data.get("pnl", 0)
        return f"""
        Analyze this completed trade for user with profile: {profile.current_level.value} level.

        Trade Details (ID: {trade_id}):
        - Entry: {json.dumps(trade_data.get('entry', {}), indent=2)}
        - Exit: {json.dumps(trade_data.get('exit', {}), indent=2)}
        - P&L: {pnl:+.2f}%
        - Notes: {trade_data.get('notes', 'N/A')}

        Analysis should:
        1. Calculate/confirm P&L impact
        2. Highlight 2-3 strengths (what went right)
        3. Identify 1-2 mistakes (what to avoid)
        4. Suggest 2-3 lessons learned
        5. Propose improved strategy variant
        6. End with motivational confidence note

        Output ONLY valid JSON:
        {{
            "trade_id": "string",
            "pnl": float,
            "strengths": ["string"],
            "mistakes": ["string"],
            "lessons_learned": ["string"],
            "improved_strategy": "string",
            "confidence_boost": "string"
        }}
        Think step-by-step: Review timeline -> Assess decisions -> Tie to profile.
        """

    def _build_confidence_prompt(
        self,
        profile: UserLearningProfile,
        context: str,
        trade_simulation: Dict[str, Any],
    ) -> str:
        """Prompt for confidence-building explanation."""
        sim_str = json.dumps(trade_simulation, indent=2)
        return f"""
        Build user confidence on trading decision: "{context}"

        User Profile: {profile.current_level.value} level, {profile.learning_style.value} style.
        Simulation: {sim_str}

        Response should:
        1. Explain why this makes sense (pros, alignment with goals)
        2. Address common fears (e.g., "Volatility is normal here because...")
        3. Use simple analogies/examples for user's style
        4. Include 1-2 quick tips for execution
        5. Motivate with "You've got this because..."

        Output as JSON:
        {{
            "explanation": "string",
            "rationale": "string",
            "tips": ["string"],
            "motivation": "string"
        }}
        """

    # -------------------------------------------------------------------------
    # Internal Parsers
    # -------------------------------------------------------------------------

    def _parse_strategy_response(
        self,
        resp: AIResponse,
        asset: str,
    ) -> Optional[StrategyRecommendation]:
        """Parse AI response to strategy payload."""
        parsed = _safe_json_loads(resp.response)
        if not isinstance(parsed, dict) or "strategy_name" not in parsed:
            logger.error(f"Invalid strategy JSON for {asset}: {resp.response[:200]}")
            return None

        return {
            **parsed,
            "generated_at": _now_iso_utc(),
        }

    def _parse_guidance_response(
        self,
        resp: AIResponse,
        session_id: str,
    ) -> Optional[TradingGuidance]:
        """Parse AI response to guidance payload."""
        parsed = _safe_json_loads(resp.response)
        if not isinstance(parsed, dict) or "action" not in parsed:
            logger.error(f"Invalid guidance JSON for {session_id}: {resp.response[:200]}")
            return None

        return {
            **parsed,
            "session_id": session_id,
            "updated_at": _now_iso_utc(),
        }

    def _parse_analysis_response(
        self,
        resp: AIResponse,
        trade_id: str,
        trade_data: Dict[str, Any],
    ) -> Optional[TradeAnalysis]:
        """Parse AI response to analysis payload."""
        parsed = _safe_json_loads(resp.response)
        if not isinstance(parsed, dict) or "pnl" not in parsed:
            logger.error(f"Invalid analysis JSON for {trade_id}: {resp.response[:200]}")
            return None

        return {
            **parsed,
            "entry": trade_data.get("entry", {}),
            "exit": trade_data.get("exit", {}),
            "pnl": float(parsed.get("pnl", 0)),
            "analyzed_at": _now_iso_utc(),
        }

    def _parse_confidence_response(
        self,
        resp: AIResponse,
        context: str,
    ) -> Optional[Dict[str, Any]]:
        """Parse AI response to confidence payload."""
        parsed = _safe_json_loads(resp.response)
        if not isinstance(parsed, dict):
            logger.error(f"Invalid confidence JSON for '{context}': {resp.response[:200]}")
            return None

        parsed["context"] = context
        parsed["generated_at"] = _now_iso_utc()
        return parsed

    # -------------------------------------------------------------------------
    # Fallbacks
    # -------------------------------------------------------------------------

    def _create_fallback_strategy(
        self,
        asset: str,
        risk_tolerance: str,
    ) -> StrategyRecommendation:
        """Basic fallback strategy."""
        return {
            "strategy_name": "Buy and Hold",
            "description": f"Simple long position in {asset} for {risk_tolerance} risk.",
            "risk_level": risk_tolerance,
            "expected_return": 0.05,  # 5%
            "suitable_for": ["beginners"],
            "steps": ["Research asset", "Set stop-loss at 10%", "Hold 3-6 months"],
            "market_conditions": {},
            "confidence_score": 0.6,
            "generated_at": _now_iso_utc(),
        }

    def _create_fallback_guidance(
        self,
        session_id: str,
        current_step: int,
    ) -> TradingGuidance:
        """Basic next step fallback."""
        return {
            "current_step": current_step + 1,
            "total_steps": 5,
            "action": "Monitor price action",
            "rationale": "Assess if entry conditions are met.",
            "risk_check": "Ensure position size < 2% of portfolio.",
            "next_decision_point": "Enter if price breaks $X.",
            "session_id": session_id,
            "updated_at": _now_iso_utc(),
        }

    def _create_fallback_analysis(
        self,
        trade_id: str,
        trade_data: Dict[str, Any],
    ) -> TradeAnalysis:
        """Basic trade review fallback."""
        pnl = trade_data.get("pnl", 0)
        return {
            "trade_id": trade_id,
            "entry": trade_data.get("entry", {}),
            "exit": trade_data.get("exit", {}),
            "pnl": pnl,
            "strengths": ["Timely entry/exit"],
            "mistakes": ["Could improve risk sizing"] if pnl < 0 else [],
            "lessons_learned": ["Review market context next time"],
            "improved_strategy": "Add trailing stop",
            "confidence_boost": "Every trade is a learning opportunity—keep going!",
            "analyzed_at": _now_iso_utc(),
        }

    def _create_fallback_confidence(
        self,
        context: str,
    ) -> Dict[str, Any]:
        """Basic confidence booster."""
        return {
            "context": context,
            "explanation": "This aligns with your risk profile and market trends.",
            "rationale": "Based on historical data, similar setups succeed 60% of the time.",
            "tips": ["Start small", "Set clear exits"],
            "motivation": "You've prepared well—trust your analysis!",
            "generated_at": _now_iso_utc(),
        }


# =============================================================================
# Singleton Instance
# =============================================================================

ai_trading_coach_service = AITradingCoachService()
