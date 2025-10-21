"""
AI Trading Coach & Strategy Advisor Service
Provides personalized guidance and strategy suggestions (educational only).
"""

from __future__ import annotations

import asyncio
import json
import uuid
import logging
from datetime import datetime, timezone
from typing import Any, Dict, Optional, List, TypedDict, Callable, Tuple

from .advanced_ai_router import get_advanced_ai_router, AIRequest, RequestType, AIModel
from .genai_education_service import GenAIEducationService, UserLearningProfile

logger = logging.getLogger(__name__)

# ----------------------------- Typed payloads -----------------------------

class AdvicePayload(TypedDict, total=False):
    overview: str
    risk_considerations: List[str]
    controls: List[str]
    next_steps: List[str]
    disclaimer: str
    generated_at: str
    model: Optional[str]
    confidence_score: Optional[float]

class StrategyOption(TypedDict, total=False):
    name: str
    when_to_use: str
    pros: List[str]
    cons: List[str]
    risk_controls: List[str]
    metrics: List[str]

class StrategyPayload(TypedDict, total=False):
    strategies: List[StrategyOption]
    disclaimer: str
    generated_at: str
    model: Optional[str]
    confidence_score: Optional[float]


# ----------------------------- Helpers -----------------------------

_DEF_DISCLAIMER = (
    "For educational purposes only; not financial advice. "
    "Discuss any decisions with a qualified advisor and consider your own circumstances."
)

def _now_iso_utc() -> str:
    return datetime.now(timezone.utc).isoformat()

def _safe_json_loads(text: str) -> Optional[Dict[str, Any]]:
    try:
        return json.loads(text)
    except Exception:
        return None

def _extract_json_block(text: str) -> Optional[Dict[str, Any]]:
    """Minimal JSON repair: take outermost {...} block if present."""
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

class TradingCoachService:
    """Personalized trading guidance using multi-model AI (educational only)."""

    # Tunables
    TOKENS_ADVISE = 1600
    TOKENS_STRATEGY = 2000
    REQUEST_TIMEOUT_S = 35
    RETRY_ATTEMPTS = 2

    MODEL_ADVISE = AIModel.GPT_4O
    MODEL_STRATEGY = AIModel.GPT_4O

    _ALLOWED_RISK = {"low", "medium", "high"}
    _ALLOWED_HORIZON = {"short", "medium", "long"}  # interpret as short=<6m, etc.

    def __init__(
        self,
        ai_router: Optional["AdvancedAIRouter"] = None,
        education: Optional[GenAIEducationService] = None,
    ) -> None:
        self.ai_router = ai_router or get_advanced_ai_router()
        self.education = education or GenAIEducationService()

    async def advise(
        self,
        user_id: str,
        goal: str,
        risk_tolerance: str,
        horizon: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> AdvicePayload:
        """Return an educational guidance summary with risks, controls, next steps."""
        goal = (goal or "").strip()
        if not goal:
            raise ValueError("goal must be a non-empty string")

        risk = (risk_tolerance or "medium").strip().lower()
        if risk not in self._ALLOWED_RISK:
            risk = "medium"

        hz = (horizon or "medium").strip().lower()
        if hz not in self._ALLOWED_HORIZON:
            hz = "medium"

        profile: UserLearningProfile = self.education.user_profiles.get(user_id) or await self.education.create_user_learning_profile(user_id, {})

        prompt = {
            "task": "trading_advice",
            "goal": goal,
            "risk_tolerance": risk,
            "investment_horizon": hz,
            "user_profile": {
                "level": profile.current_level.value,
                "interests": profile.interests,
            },
            "context": context or {},
            "requirements": [
                "Educational tone; DO NOT give personalized investment advice.",
                "Explain trade-offs and key risks clearly.",
                "Provide concrete risk controls (position sizing, stops, diversification).",
                "Offer 2-3 optional next steps to learn or simulate, not to trade.",
                "Include a clear disclaimer."
            ],
            "output_format": {
                "overview": "string",
                "risk_considerations": ["string"],
                "controls": ["string"],
                "next_steps": ["string"],
                "disclaimer": "string"
            },
            "response_style": "Return ONLY valid JSON matching output_format. No markdown.",
        }

        req = AIRequest(
            request_id=str(uuid.uuid4()),
            request_type=RequestType.RISK_ASSESSMENT,
            prompt=json.dumps(prompt),
            context={"user_id": user_id, "request_id": str(uuid.uuid4())},
            model_preference=self.MODEL_ADVISE,
            requires_reasoning=True,
            max_tokens=self.TOKENS_ADVISE,
        )

        async def _op():
            return await _with_timeout(self.ai_router.route_request(req), self.REQUEST_TIMEOUT_S)

        try:
            resp = await _retry(_op, attempts=self.RETRY_ATTEMPTS)
            raw = _safe_json_loads(resp.response) or _extract_json_block(resp.response)
            if not isinstance(raw, dict):
                data: AdvicePayload = {
                    "overview": "",
                    "risk_considerations": [],
                    "controls": [],
                    "next_steps": [],
                    "disclaimer": _DEF_DISCLAIMER,
                }
            else:
                data = AdvicePayload(
                    overview=str(raw.get("overview", "")).strip(),
                    risk_considerations=[str(x) for x in (raw.get("risk_considerations") or [])][:10],
                    controls=[str(x) for x in (raw.get("controls") or [])][:10],
                    next_steps=[str(x) for x in (raw.get("next_steps") or [])][:6],
                    disclaimer=str(raw.get("disclaimer") or _DEF_DISCLAIMER),
                )

            data["generated_at"] = _now_iso_utc()
            data["model"] = getattr(resp, "model", None)
            data["confidence_score"] = float(getattr(resp, "confidence_score", 0.0) or 0.0)
            # harden: always ensure a disclaimer
            if not data.get("disclaimer"):
                data["disclaimer"] = _DEF_DISCLAIMER
            return data

        except Exception as e:
            logger.exception("TradingCoachService.advise failed: %s", e)
            # Check if this is a retryable error (temperature, credits, etc.)
            if "temperature" in str(e) or "credit balance" in str(e) or "unsupported" in str(e):
                # Let the AI router handle retries, don't return empty response
                raise e
            # For other errors, return empty response
            return AdvicePayload(
                overview="",
                risk_considerations=[],
                controls=[],
                next_steps=[],
                disclaimer=_DEF_DISCLAIMER,
                generated_at=_now_iso_utc(),
                model=None,
                confidence_score=0.0,
            )

    async def strategy(
        self,
        user_id: str,
        objective: str,
        market_view: str,
        constraints: Optional[Dict[str, Any]] = None,
    ) -> StrategyPayload:
        """Suggest 2–3 strategy outlines with pros/cons and risk controls (educational)."""
        objective = (objective or "").strip()
        market_view = (market_view or "").strip()
        if not objective or not market_view:
            raise ValueError("objective and market_view must be non-empty strings")

        profile: UserLearningProfile = self.education.user_profiles.get(user_id) or await self.education.create_user_learning_profile(user_id, {})

        prompt = {
            "task": "strategy_suggestion",
            "objective": objective,
            "market_view": market_view,
            "constraints": constraints or {},
            "user_profile": {
                "level": profile.current_level.value,
                "interests": profile.interests,
            },
            "requirements": [
                "Suggest 2–3 strategies with pros/cons (no personalized advice).",
                "Explain why each fits the stated market view.",
                "Outline risk controls and key metrics to track.",
                "Include 1 learning resource (title + what to learn), no external links required.",
                "Include a clear disclaimer."
            ],
            "output_format": {
                "strategies": [
                    {
                        "name": "string",
                        "when_to_use": "string",
                        "pros": ["string"],
                        "cons": ["string"],
                        "risk_controls": ["string"],
                        "metrics": ["string"]
                    }
                ],
                "disclaimer": "string"
            },
            "response_style": "Return ONLY valid JSON matching output_format. No markdown.",
        }

        req = AIRequest(
            request_id=str(uuid.uuid4()),
            request_type=RequestType.GENERAL_CHAT,
            prompt=json.dumps(prompt),
            context={"user_id": user_id, "request_id": str(uuid.uuid4())},
            model_preference=self.MODEL_STRATEGY,
            requires_reasoning=True,
            max_tokens=self.TOKENS_STRATEGY,
        )

        async def _op():
            return await _with_timeout(self.ai_router.route_request(req), self.REQUEST_TIMEOUT_S)

        try:
            resp = await _retry(_op, attempts=self.RETRY_ATTEMPTS)
            logger.info(f"AI Response received: {resp.response[:200]}...")
            
            # Parse the AI response
            raw = json.loads(resp.response)
            data = {
                "strategies": raw.get("strategies", []),
                "disclaimer": str(raw.get("disclaimer") or _DEF_DISCLAIMER),
            }

            data["generated_at"] = _now_iso_utc()
            data["model"] = getattr(resp, "model", None)
            data["confidence_score"] = float(getattr(resp, "confidence_score", 0.0) or 0.0)
            
            # harden: always ensure a disclaimer
            if not data.get("disclaimer"):
                data["disclaimer"] = _DEF_DISCLAIMER
            return data

        except Exception as e:
            logger.exception("TradingCoachService.strategy failed: %s", e)
            # Check if this is a retryable error (temperature, credits, etc.)
            if "temperature" in str(e) or "credit balance" in str(e) or "unsupported" in str(e):
                # Let the AI router handle retries, don't return mock strategies
                raise e
            # For other errors, return mock strategies
            mock_strategies = [
                {
                    "name": "Dollar-Cost Averaging (DCA)",
                    "when_to_use": "When you want to reduce market timing risk and build wealth gradually over time",
                    "pros": [
                        "Reduces impact of market volatility",
                        "Simple to implement and maintain",
                        "Takes emotion out of investing",
                        "Works well for long-term goals"
                    ],
                    "cons": [
                        "May miss out on market dips",
                        "Requires consistent discipline",
                        "Lower potential returns than timing the market"
                    ],
                    "risk_controls": [
                        "Set up automatic investments",
                        "Diversify across asset classes",
                        "Review and adjust monthly",
                        "Maintain emergency fund"
                    ],
                    "metrics": [
                        "Monthly investment amount",
                        "Portfolio growth rate",
                        "Volatility reduction",
                        "Consistency score"
                    ]
                },
                {
                    "name": "Value Investing Strategy",
                    "when_to_use": "When you have time to research and want to buy undervalued quality companies",
                    "pros": [
                        "Focus on fundamental analysis",
                        "Potential for above-average returns",
                        "Builds deep market knowledge",
                        "Long-term wealth building"
                    ],
                    "cons": [
                        "Requires significant research time",
                        "Value traps can occur",
                        "May underperform in bull markets",
                        "Requires patience and discipline"
                    ],
                    "risk_controls": [
                        "Thorough fundamental analysis",
                        "Diversify across sectors",
                        "Set position size limits",
                        "Regular portfolio review"
                    ],
                    "metrics": [
                        "P/E ratio analysis",
                        "Debt-to-equity ratios",
                        "Revenue growth trends",
                        "Return on equity"
                    ]
                },
                {
                    "name": "Growth Investing Approach",
                    "when_to_use": "When you're comfortable with higher risk and want to invest in fast-growing companies",
                    "pros": [
                        "Potential for high returns",
                        "Invest in innovative companies",
                        "Capitalize on market trends",
                        "Suitable for younger investors"
                    ],
                    "cons": [
                        "Higher volatility and risk",
                        "May be overvalued",
                        "Requires market timing",
                        "Can lead to significant losses"
                    ],
                    "risk_controls": [
                        "Limit position sizes",
                        "Set stop-loss orders",
                        "Diversify across growth sectors",
                        "Regular profit-taking"
                    ],
                    "metrics": [
                        "Revenue growth rates",
                        "Market share expansion",
                        "Innovation pipeline",
                        "Management quality"
                    ]
                }
            ]
            return StrategyPayload(
                strategies=mock_strategies,
                disclaimer=_DEF_DISCLAIMER,
                generated_at=_now_iso_utc(),
                model="mock-fallback",
                confidence_score=0.8,
            )


# Global instance (optional)
trading_coach_service = TradingCoachService()
