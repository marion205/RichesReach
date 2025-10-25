# core/ai_service.py
from __future__ import annotations

import os
import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional, TypedDict

from django.conf import settings

logger = logging.getLogger(__name__)

# ----------------------------- Optional imports ---------------------------- #

# OpenAI (optional)
try:
    import openai  # Legacy SDK still widely used
    OPENAI_AVAILABLE = True
except Exception as _e:
    OPENAI_AVAILABLE = False
    logger.warning(
        "OpenAI package not installed. AI features will use fallback responses."
    )

# ML services (optional)
try:
    from .optimized_ml_service import OptimizedMLService
    from .market_data_service import MarketDataService

    ML_AVAILABLE = True
except Exception as e:  # noqa: BLE001
    ML_AVAILABLE = False
    logger.warning("ML services not available: %s", e)


# ------------------------------- Type helpers ------------------------------ #

class ChatMessage(TypedDict):
    role: str  # "system" | "user" | "assistant"
    content: str


class ChatResponse(TypedDict, total=False):
    content: str
    confidence: float
    tokens_used: int
    model_used: str
    finish_reason: str


@dataclass(frozen=True)
class ServiceStatus:
    openai_available: bool
    ml_available: bool
    market_data_available: bool
    api_key_configured: bool
    timestamp: str


# --------------------------------- Service -------------------------------- #

class AIService:
    """
    Central AI orchestrator.

    - Gracefully degrades when OpenAI or ML services are unavailable.
    - Adds retries and timeouts around OpenAI calls.
    - Keeps the same public interface as your original implementation.
    """

    # Reasonable defaults if settings are missing
    DEFAULT_MODEL = "gpt-3.5-turbo"
    DEFAULT_MAX_TOKENS = 1000
    DEFAULT_TEMPERATURE = 1.0  # GPT-5 compatible
    OPENAI_TIMEOUT = 25  # seconds
    OPENAI_MAX_RETRIES = 2

    def __init__(self) -> None:
        # Config
        self.api_key: Optional[str] = os.getenv("OPENAI_API_KEY") or getattr(
            settings, "OPENAI_API_KEY", None
        )
        self.model: str = getattr(settings, "OPENAI_MODEL", self.DEFAULT_MODEL)
        self.max_tokens: int = getattr(
            settings, "OPENAI_MAX_TOKENS", self.DEFAULT_MAX_TOKENS
        )
        self.temperature: float = getattr(
            settings, "OPENAI_TEMPERATURE", self.DEFAULT_TEMPERATURE
        )

        # OpenAI wiring (optional)
        if self.api_key and OPENAI_AVAILABLE:
            try:
                openai.api_key = self.api_key  # legacy SDK pattern
                logger.info("OpenAI configured (model=%s).", self.model)
            except Exception as e:  # noqa: BLE001
                logger.warning("Failed to configure OpenAI: %s", e)
        else:
            logger.warning(
                "OpenAI is unavailable or API key missing. Falling back to offline responses."
            )

        # ML services wiring (optional)
        if ML_AVAILABLE:
            try:
                self.ml_service = OptimizedMLService()
                self.market_data_service = MarketDataService()
                logger.info("Optimized ML services initialized successfully.")
            except Exception as e:  # noqa: BLE001
                self.ml_service = None
                self.market_data_service = None
                logger.warning("Failed to initialize ML services: %s", e)
        else:
            self.ml_service = None
            self.market_data_service = None

    # ------------------------------- OpenAI IO ------------------------------ #

    def _chat_completion(self, messages: List[ChatMessage]) -> Optional[Dict[str, Any]]:
        """
        Thin wrapper over OpenAI API with retries & timeouts.
        Returns the raw OpenAI response dict or None on failure.
        """
        if not (self.api_key and OPENAI_AVAILABLE):
            return None

        # Simple manual retry loop (keeps deps minimal)
        last_error: Optional[Exception] = None
        for attempt in range(1, self.OPENAI_MAX_RETRIES + 2):  # e.g., 1 + retries
            try:
                # Use new OpenAI API format (compatible with openai>=1.0.0)
                client = openai.OpenAI(api_key=self.api_key)
                resp = client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    max_tokens=self.max_tokens,
                    temperature=self.temperature,
                    timeout=self.OPENAI_TIMEOUT,
                )
                # Convert to legacy format for compatibility
                return {
                    'choices': [{
                        'message': {
                            'content': resp.choices[0].message.content,
                            'role': resp.choices[0].message.role
                        }
                    }],
                    'model': resp.model,
                    'usage': {
                        'total_tokens': resp.usage.total_tokens if resp.usage else 0
                    }
                }
            except Exception as e:  # noqa: BLE001
                last_error = e
                logger.warning(
                    "OpenAI chat attempt %s/%s failed: %s",
                    attempt,
                    self.OPENAI_MAX_RETRIES + 1,
                    e,
                )
        logger.error("OpenAI chat failed after retries: %s", last_error)
        return None

    # ------------------------------ Public API ------------------------------ #

    def get_chat_response(
        self, messages: List[ChatMessage], user_context: Optional[str] = None
    ) -> ChatResponse:
        """
        Get a response from OpenAI (if available) with graceful fallback.

        Args:
            messages: list of {"role", "content"} dicts
            user_context: optional short string about the user to prime the model
        """
        if not messages:
            return self._get_fallback_response("")

        # Prepend a light system primer if the caller passes context
        openai_messages: List[ChatMessage] = []
        if user_context:
            openai_messages.append(
                {
                    "role": "system",
                    "content": (
                        "You are a helpful, educational personal-finance assistant. "
                        "When giving guidance, prefer practical, step-by-step tips. "
                        f"User context: {user_context}"
                    ),
                }
            )
        openai_messages.extend(messages)

        raw = self._chat_completion(openai_messages)
        if not raw:
            # Fall back to deterministic guidance
            last_user = messages[-1]["content"] if messages else ""
            return self._get_fallback_response(last_user)

        # Parse legacy SDK response
        try:
            choice = raw["choices"][0]
            msg = choice["message"]["content"]
            tokens = int(raw.get("usage", {}).get("total_tokens", 0))
            finish = choice.get("finish_reason", "stop") or "stop"
            return {
                "content": msg,
                "confidence": 0.9,  # OpenAI doesn't return confidence
                "tokens_used": tokens,
                "model_used": self.model,
                "finish_reason": finish,
            }
        except Exception as e:  # noqa: BLE001
            logger.error("Failed to parse OpenAI response: %s", e)
            last_user = messages[-1]["content"] if messages else ""
            return self._get_fallback_response(last_user)

    def predict_market_regime(self, market_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Predict market regime via ML service (if available) with fallback.
        """
        if not (self.ml_service and self.market_data_service):
            return self._get_fallback_market_regime()

        try:
            indicators = market_data or self.market_data_service.get_market_regime_indicators()
            prediction = self.ml_service.predict_market_regime(indicators)
            return {
                **prediction,
                "ai_service": "ml_enhanced",
                "timestamp": self._now_iso(),
            }
        except Exception as e:  # noqa: BLE001
            logger.error("Error in market regime prediction: %s", e)
            return self._get_fallback_market_regime()

    def optimize_portfolio_ml(
        self,
        user_profile: Dict[str, Any],
        available_stocks: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        """
        Optimize portfolio via ML (if available) with fallback.
        """
        if not (self.ml_service and self.market_data_service):
            return self._get_fallback_portfolio_optimization(user_profile)

        try:
            market_conditions = self.market_data_service.get_market_regime_indicators()
            optimization = self.ml_service.optimize_portfolio_allocation(
                user_profile, market_conditions, available_stocks or []
            )
            return {
                **optimization,
                "ai_service": "ml_enhanced",
                "market_conditions": market_conditions,
                "timestamp": self._now_iso(),
            }
        except Exception as e:  # noqa: BLE001
            logger.error("Error in ML portfolio optimization: %s", e)
            return self._get_fallback_portfolio_optimization(user_profile)

    def score_stocks_ml(
        self, stocks: List[Dict[str, Any]], user_profile: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Score stocks via ML (if available) with fallback.
        """
        if not (self.ml_service and self.market_data_service):
            return self._get_fallback_stock_scoring(stocks, user_profile)

        try:
            market_conditions = self.market_data_service.get_market_regime_indicators()
            return self.ml_service.score_stocks_ml(stocks, market_conditions, user_profile)
        except Exception as e:  # noqa: BLE001
            logger.error("Error in ML stock scoring: %s", e)
            return self._get_fallback_stock_scoring(stocks, user_profile)

    def get_enhanced_market_analysis(self) -> Dict[str, Any]:
        """
        Aggregate market overview + ML regime prediction with fallback.
        """
        if not (self.market_data_service and self.ml_service):
            return self._get_fallback_market_analysis()

        try:
            market_overview = self.market_data_service.get_market_overview()
            sector_performance = self.market_data_service.get_sector_performance()
            economic_indicators = self.market_data_service.get_economic_indicators()
            regime_indicators = self.market_data_service.get_market_regime_indicators()

            regime_prediction = self.predict_market_regime(regime_indicators)

            return {
                "market_overview": market_overview,
                "sector_performance": sector_performance,
                "economic_indicators": economic_indicators,
                "regime_indicators": regime_indicators,
                "ml_regime_prediction": regime_prediction,
                "ai_service": "ml_enhanced",
                "timestamp": self._now_iso(),
            }
        except Exception as e:  # noqa: BLE001
            logger.error("Error in enhanced market analysis: %s", e)
            return self._get_fallback_market_analysis()

    def generate_session_title(self, first_message: str) -> str:
        """
        Short descriptive title for a chat session. Falls back to a safe default.
        """
        prompt: List[ChatMessage] = [
            {
                "role": "system",
                "content": (
                    "Generate a short, descriptive title (<= 50 chars) for a "
                    "personal-finance chat session based on the user's first message. "
                    "No quotes or punctuation at the ends."
                ),
            },
            {"role": "user", "content": f"First message: {first_message}"},
        ]

        raw = self._chat_completion(prompt)
        if not raw:
            return "Financial Chat Session"

        try:
            title = (raw["choices"][0]["message"]["content"] or "").strip().strip('"').strip("'")
            return (title[:50]).rstrip()
        except Exception as e:  # noqa: BLE001
            logger.error("Error parsing title: %s", e)
            return "Financial Chat Session"

    def get_service_status(self) -> Dict[str, Any]:
        status = ServiceStatus(
            openai_available=bool(self.api_key) and OPENAI_AVAILABLE,
            ml_available=bool(self.ml_service),
            market_data_available=bool(self.market_data_service),
            api_key_configured=bool(self.api_key),
            timestamp=self._now_iso(),
        )
        return {
            "openai_available": status.openai_available,
            "ml_available": status.ml_available,
            "market_data_available": status.market_data_available,
            "api_key_configured": status.api_key_configured,
            "timestamp": status.timestamp,
        }

    # ------------------------------- Fallbacks ------------------------------ #

    def _get_fallback_response(self, user_message: str) -> ChatResponse:
        tips = (
            "• Diversify across index funds/ETFs\n"
            "• Match investments to time horizon + risk tolerance\n"
            "• Keep fees/taxes low; automate contributions\n"
            "• Build/keep a 3–6 month emergency fund"
        )
        content = (
            f"I'm currently in offline mode. You asked: “{user_message}”.\n\n"
            f"Here are some general personal-finance tips:\n{tips}\n\n"
            "More learning: investor.gov (free, non-commercial)."
        )
        return {
            "content": content,
            "confidence": 0.5,
            "tokens_used": 0,
            "model_used": "fallback",
            "finish_reason": "fallback",
        }

    def _get_fallback_market_regime(self) -> Dict[str, Any]:
        return {
            "regime": "sideways",
            "confidence": 0.5,
            "all_probabilities": {
                "bull_market": 0.25,
                "bear_market": 0.25,
                "sideways": 0.30,
                "volatile": 0.20,
            },
            "method": "fallback",
            "ai_service": "fallback",
            "timestamp": self._now_iso(),
        }

    def _get_fallback_portfolio_optimization(self, user_profile: Dict[str, Any]) -> Dict[str, Any]:
        risk = user_profile.get("risk_tolerance", "Moderate")
        base = {
            "Conservative": {"stocks": 40, "bonds": 45, "etfs": 12, "cash": 3},
            "Moderate": {"stocks": 60, "bonds": 25, "etfs": 12, "cash": 3},
            "Aggressive": {"stocks": 80, "bonds": 10, "etfs": 8, "cash": 2},
        }
        allocation = base.get(risk, base["Moderate"])
        return {
            "allocation": allocation,
            "expected_return": "8–12%",
            "risk_score": 0.6,
            "method": "fallback",
            "ai_service": "fallback",
            "timestamp": self._now_iso(),
        }

    def _get_fallback_stock_scoring(
        self, stocks: List[Dict[str, Any]], user_profile: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        scored: List[Dict[str, Any]] = []
        for s in stocks:
            base_score = float(s.get("beginner_friendly_score", 5.0))
            scored.append(
                {
                    **s,
                    "ml_score": base_score,
                    "ml_confidence": 0.5,
                    "ml_reasoning": f"Fallback score based on beginner-friendly rating: {base_score}",
                }
            )
        scored.sort(key=lambda x: x.get("ml_score", 0.0), reverse=True)
        return scored

    def _get_fallback_market_analysis(self) -> Dict[str, Any]:
        return {
            "market_overview": {"sp500_return": 0.0, "volatility": 0.15, "method": "fallback"},
            "sector_performance": {"technology": "neutral", "healthcare": "neutral", "financials": "neutral"},
            "economic_indicators": {"interest_rate": 0.05, "gdp_growth": 0.02, "method": "fallback"},
            "regime_indicators": {"market_regime": "sideways", "method": "fallback"},
            "ai_service": "fallback",
            "timestamp": self._now_iso(),
        }

    # --------------------------------- Utils -------------------------------- #

    @staticmethod
    def _now_iso() -> str:
        return datetime.now().isoformat()