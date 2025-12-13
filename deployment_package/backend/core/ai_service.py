# core/ai_service.py
import os
import time
import logging
import uuid
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from django.conf import settings
from django.core.cache import cache
from django.utils import timezone

logger = logging.getLogger(__name__)

# Try to get request ID from thread-local storage (set by middleware)
try:
    from threading import local
    _thread_local = local()
    
    def get_request_id() -> Optional[str]:
        """Get request ID from thread-local storage if available"""
        return getattr(_thread_local, 'request_id', None)
    
    def set_request_id(request_id: Optional[str] = None) -> str:
        """Set request ID in thread-local storage"""
        if request_id is None:
            request_id = str(uuid.uuid4())[:8]
        _thread_local.request_id = request_id
        return request_id
except Exception:
    # Fallback if threading not available
    def get_request_id() -> Optional[str]:
        return None
    
    def set_request_id(request_id: Optional[str] = None) -> str:
        return request_id or str(uuid.uuid4())[:8]

# Optional OpenAI SDK
try:
    from openai import OpenAI
    from openai import APIError, RateLimitError, APITimeoutError
    OPENAI_AVAILABLE = True
except Exception as e:
    OPENAI_AVAILABLE = False
    OpenAI = None  # type: ignore
    APIError = RateLimitError = APITimeoutError = Exception  # type: ignore
    logger.warning("OpenAI SDK not available; AI chat will use fallback. (%s)", e)

# Optional ML services
try:
    from .ml_service import MLService
    from .market_data_service import MarketDataService
    ML_AVAILABLE = True
except Exception as e:
    ML_AVAILABLE = False
    MLService = MarketDataService = None  # type: ignore
    logger.warning("ML services not available: %s", e)


@dataclass(frozen=True)
class OpenAIConfig:
    api_key: Optional[str]
    model: str
    max_tokens: int
    temperature: float
    timeout_s: float
    max_retries: int


class AIService:
    def __init__(self) -> None:
        self._config = OpenAIConfig(
            api_key=os.getenv("OPENAI_API_KEY") or getattr(settings, "OPENAI_API_KEY", None),
            model=getattr(settings, "OPENAI_MODEL", "gpt-4o-mini"),
            max_tokens=int(getattr(settings, "OPENAI_MAX_TOKENS", 1000)),
            temperature=float(getattr(settings, "OPENAI_TEMPERATURE", 0.7)),
            timeout_s=float(getattr(settings, "OPENAI_TIMEOUT_S", 15.0)),
            max_retries=int(getattr(settings, "OPENAI_MAX_RETRIES", 2)),
        )

        self._client: Optional["OpenAI"] = None

        self.ml_service = MLService() if ML_AVAILABLE else None
        self.market_data_service = MarketDataService() if ML_AVAILABLE else None

        if not (OPENAI_AVAILABLE and self._config.api_key):
            logger.warning("OpenAI not configured; using fallback responses.")
        if not ML_AVAILABLE:
            logger.warning("ML services not available; using fallback ML responses.")

    # ---------- Public API ----------

    def get_chat_response(self, messages: List[Dict[str, Any]], user_context: Optional[str] = None) -> Dict[str, Any]:
        """
        Get a response from OpenAI's chat completion API
        
        Args:
            messages: List of message dictionaries with 'role' and 'content'
            user_context: Optional user context information
            
        Returns:
            Dictionary containing response content, confidence, and token usage:
            {
                "content": str,
                "confidence": float,
                "tokens_used": int,
                "model_used": str
            }
        """
        last_user_text = self._safe_last_user_text(messages)

        if not (OPENAI_AVAILABLE and self._config.api_key):
            return self._get_fallback_response(last_user_text)

        prompt = self._normalize_messages(messages, user_context=user_context)

        t0 = time.perf_counter()
        try:
            resp = self._chat_complete(prompt)
            dt_ms = int((time.perf_counter() - t0) * 1000)

            content = (resp.get("content") or "").strip()
            tokens = int(resp.get("tokens_used") or 0)

            request_id = get_request_id()
            logger.info(
                "openai.chat ok model=%s tokens=%s ms=%s request_id=%s",
                self._config.model, tokens, dt_ms, request_id or "none"
            )

            return {
                "content": content or "I couldn't generate a response.",
                "confidence": 0.9,
                "tokens_used": tokens,
                "model_used": self._config.model,
                "latency_ms": dt_ms,
                "fallback_used": False,
                "error_type": None,
            }

        except Exception as e:
            dt_ms = int((time.perf_counter() - t0) * 1000)
            error_type = type(e).__name__
            request_id = get_request_id()
            logger.exception(
                "openai.chat failed ms=%s err=%s request_id=%s",
                dt_ms, str(e), request_id or "none"
            )
            fallback = self._get_fallback_response(last_user_text)
            fallback["latency_ms"] = dt_ms
            fallback["fallback_used"] = True
            fallback["error_type"] = error_type
            return fallback

    def predict_market_regime(self, market_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Predict market regime using ML models
        
        Args:
            market_data: Optional market data, will fetch if not provided
            
        Returns:
            Dictionary with regime prediction and confidence
        """
        if not (ML_AVAILABLE and self.ml_service and self.market_data_service):
            return self._get_fallback_market_regime()

        try:
            if market_data is None:
                market_data = self._cached_regime_indicators()

            prediction = self.ml_service.predict_market_regime(market_data)
            return {
                **prediction,
                "ai_service": "ml_enhanced",
                "timestamp": self._get_current_timestamp(),
            }
        except Exception as e:
            logger.exception("market_regime_prediction failed err=%s", str(e))
            return self._get_fallback_market_regime()

    def optimize_portfolio_ml(
        self,
        user_profile: Dict[str, Any],
        available_stocks: Optional[List[Dict[str, Any]]] = None,
        spending_analysis: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Optimize portfolio using ML models with spending habits analysis
        
        Args:
            user_profile: User's financial profile
            available_stocks: Optional list of available stocks
            spending_analysis: Optional spending habits analysis from transactions
            
        Returns:
            Optimized portfolio allocation
        """
        if not (ML_AVAILABLE and self.ml_service and self.market_data_service):
            return self._get_fallback_portfolio_optimization(user_profile)

        # Validate inputs
        try:
            self._validate_user_profile(user_profile)
        except ValueError as e:
            logger.error(f"Invalid user_profile: {e}")
            return self._get_fallback_portfolio_optimization(user_profile)

        try:
            market_conditions = self._cached_regime_indicators()
            optimization = self.ml_service.optimize_portfolio_allocation(
                user_profile,
                market_conditions,
                available_stocks or [],
                spending_analysis
            )
            return {
                **optimization,
                "ai_service": "ml_enhanced",
                "market_conditions": market_conditions,
                "timestamp": self._get_current_timestamp(),
            }
        except Exception as e:
            logger.exception("portfolio_optimization failed err=%s", str(e))
            return self._get_fallback_portfolio_optimization(user_profile)

    def score_stocks_ml(
        self,
        stocks: List[Dict[str, Any]],
        user_profile: Dict[str, Any],
        spending_analysis: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Score stocks using ML models with spending habits analysis
        
        Args:
            stocks: List of stocks to score
            user_profile: User's financial profile
            spending_analysis: Optional spending habits analysis from transactions
            
        Returns:
            List of scored stocks with ML scores
        """
        if not (ML_AVAILABLE and self.ml_service and self.market_data_service):
            return self._get_fallback_stock_scoring(stocks, user_profile)

        # Validate inputs
        try:
            self._validate_user_profile(user_profile)
            if not stocks:
                logger.warning("score_stocks_ml called with empty stocks list")
                return []
        except ValueError as e:
            logger.error(f"Invalid inputs for stock scoring: {e}")
            return self._get_fallback_stock_scoring(stocks, user_profile)

        try:
            market_conditions = self._cached_regime_indicators()
            return self.ml_service.score_stocks_ml(stocks, market_conditions, user_profile, spending_analysis)
        except Exception as e:
            logger.exception("stock_scoring failed err=%s", str(e))
            return self._get_fallback_stock_scoring(stocks, user_profile)

    def get_enhanced_market_analysis(self) -> Dict[str, Any]:
        """
        Get enhanced market analysis using ML models
        
        Returns:
            Comprehensive market analysis
        """
        if not (ML_AVAILABLE and self.market_data_service):
            return self._get_fallback_market_analysis()

        try:
            # Cache each piece briefly
            overview = self._cache_get_or_set("market_overview", 60, self.market_data_service.get_market_overview)
            sectors = self._cache_get_or_set("sector_performance", 300, self.market_data_service.get_sector_performance)
            econ = self._cache_get_or_set("economic_indicators", 300, self.market_data_service.get_economic_indicators)
            regime_ind = self._cached_regime_indicators()

            regime_prediction = self.predict_market_regime(regime_ind)

            return {
                "market_overview": overview,
                "sector_performance": sectors,
                "economic_indicators": econ,
                "regime_indicators": regime_ind,
                "ml_regime_prediction": regime_prediction,
                "ai_service": "ml_enhanced",
                "timestamp": self._get_current_timestamp(),
            }
        except Exception as e:
            logger.exception("enhanced_market_analysis failed err=%s", str(e))
            return self._get_fallback_market_analysis()

    def generate_session_title(self, first_message: str) -> str:
        """Generate a title for a chat session based on the first message"""
        if not (OPENAI_AVAILABLE and self._config.api_key):
            return "Financial Chat Session"

        prompt = [
            {"role": "system", "content": "Generate a short, descriptive title (max 50 chars) for a financial chat session."},
            {"role": "user", "content": f"First message: {first_message[:500]}"},
        ]

        try:
            resp = self._chat_complete(prompt, max_tokens=24, temperature=0.3)
            title = (resp.get("content") or "").strip().strip('"').strip("'")
            return (title[:47] + "...") if len(title) > 50 else (title or "Financial Chat Session")
        except Exception as e:
            logger.exception("generate_session_title failed err=%s", str(e))
            return "Financial Chat Session"

    # ---------- OpenAI helpers ----------

    def _client_or_raise(self) -> "OpenAI":
        if self._client is None:
            if not (OPENAI_AVAILABLE and self._config.api_key):
                raise RuntimeError("OpenAI not configured")
            self._client = OpenAI(api_key=self._config.api_key)
        return self._client

    def _chat_complete(
        self,
        messages: List[Dict[str, str]],
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Minimal wrapper w/ retries on transient errors.
        
        Returns dict: {content, tokens_used}
        """
        client = self._client_or_raise()
        attempts = self._config.max_retries + 1
        last_err: Optional[Exception] = None

        for i in range(attempts):
            try:
                r = client.chat.completions.create(
                    model=self._config.model,
                    messages=messages,
                    max_tokens=max_tokens or self._config.max_tokens,
                    temperature=temperature if temperature is not None else self._config.temperature,
                    timeout=self._config.timeout_s,
                )
                content = r.choices[0].message.content if r.choices else ""
                tokens_used = getattr(r.usage, "total_tokens", 0) if getattr(r, "usage", None) else 0
                return {"content": content, "tokens_used": tokens_used}

            except RateLimitError as e:
                last_err = e
                # Extract retry-after header if available
                retry_after = None
                if hasattr(e, "response") and e.response:
                    retry_after = e.response.headers.get("Retry-After")
                    if retry_after:
                        try:
                            retry_after = int(retry_after)
                        except (ValueError, TypeError):
                            retry_after = None
                
                sleep_s = retry_after if retry_after else (0.5 * (2 ** i))
                logger.warning(
                    "openai rate limit attempt=%s/%s sleep=%ss retry_after=%s",
                    i+1, attempts, sleep_s, retry_after
                )
                time.sleep(sleep_s)
            except (APITimeoutError, APIError) as e:
                last_err = e
                # simple backoff: 0.5s, 1s, 2s
                sleep_s = 0.5 * (2 ** i)
                logger.warning("openai transient err attempt=%s/%s sleep=%ss err=%s", i+1, attempts, sleep_s, str(e))
                time.sleep(sleep_s)

        raise last_err or RuntimeError("OpenAI call failed")

    # ---------- Message hygiene ----------

    def _normalize_messages(self, messages: List[Dict[str, Any]], user_context: Optional[str]) -> List[Dict[str, str]]:
        safe: List[Dict[str, str]] = []

        # Sanitize user_context to prevent prompt injection
        sanitized_context = self._sanitize_user_context(user_context) if user_context else None

        # Always include a system message (and include safety disclaimers)
        sys = (
            "You are a helpful financial assistant. Provide educational information, not personalized financial advice. "
            "Encourage risk awareness. "
            "If user asks what to buy/sell, provide education about risks and suggest consulting a licensed professional. "
            "Avoid guaranteeing returns. "
            "If user indicates financial distress, suggest professional help."
        )
        if sanitized_context:
            sys += f" User context: {sanitized_context[:1000]}"
        safe.append({"role": "system", "content": sys})

        # Keep only last N messages to avoid runaway prompts
        tail = (messages or [])[-20:]
        for m in tail:
            role = (m.get("role") or "user").strip()
            content = (m.get("content") or "").strip()
            if role not in ("system", "user", "assistant"):
                role = "user"
            if content:
                safe.append({"role": role, "content": content[:8000]})

        return safe

    def _safe_last_user_text(self, messages: List[Dict[str, Any]]) -> str:
        if not messages:
            return ""
        # Prefer last user role content if present
        for m in reversed(messages):
            if (m.get("role") == "user") and m.get("content"):
                return str(m.get("content"))
        return str(messages[-1].get("content") or "")

    def _sanitize_user_context(self, user_context: str) -> str:
        """
        Sanitize user context to prevent prompt injection.
        Removes suspicious patterns that could inject system instructions.
        """
        if not user_context:
            return ""
        
        # Remove potential prompt injection patterns
        forbidden_patterns = [
            'role": "system',
            '<<SYS>>',
            '[/INST]',
            '### System:',
            'SYSTEM:',
        ]
        
        sanitized = user_context
        for pattern in forbidden_patterns:
            if pattern.lower() in sanitized.lower():
                logger.warning(f"Potential prompt injection detected in user_context, removing pattern: {pattern}")
                # Remove the pattern and surrounding context
                sanitized = sanitized.replace(pattern, "").replace(pattern.lower(), "")
        
        return sanitized.strip()

    # ---------- Caching helpers ----------

    def _cached_regime_indicators(self) -> Dict[str, Any]:
        return self._cache_get_or_set(
            "market_regime_indicators",
            ttl_s=int(getattr(settings, "MARKET_REGIME_CACHE_TTL_S", 60)),
            fn=self.market_data_service.get_market_regime_indicators,  # type: ignore
        )

    def _cache_get_or_set(self, key: str, ttl_s: int, fn):
        """
        Cache with dogpile protection (stampede prevention).
        If cache expires and multiple requests hit simultaneously,
        only one computes while others wait or get stale value.
        """
        cache_key = f"ai:{key}"
        lock_key = f"{cache_key}:lock"
        
        v = cache.get(cache_key)
        if v is not None:
            return v

        # Prevent stampede: try to acquire lock
        got_lock = cache.add(lock_key, 1, timeout=10)
        if not got_lock:
            # Someone else is computing; small wait then try again
            time.sleep(0.05)
            v2 = cache.get(cache_key)
            if v2 is not None:
                return v2
            # Fall through and compute if still missing

        try:
            v = fn()
            cache.set(cache_key, v, ttl_s)
            return v
        finally:
            cache.delete(lock_key)

    # ---------- Fallbacks (unchanged behavior) ----------

    def _get_fallback_response(self, user_message: str) -> Dict[str, Any]:
        return {
            "content": (
                "I'm currently in offline mode. "
                f"You asked: '{user_message}'.\n\n"
                "General tips:\n"
                "• Diversify\n"
                "• Match risk to time horizon\n"
                "• Watch fees\n"
                "• Use investor.gov for education"
            ),
            "confidence": 0.5,
            "tokens_used": 0,
            "model_used": "fallback",
            "latency_ms": 0,
            "fallback_used": True,
            "error_type": None,
        }

    def _get_fallback_market_regime(self) -> Dict[str, Any]:
        """Fallback market regime prediction"""
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
        }

    def _get_fallback_portfolio_optimization(self, user_profile: Dict[str, Any]) -> Dict[str, Any]:
        """Fallback portfolio optimization"""
        risk_tolerance = user_profile.get("risk_tolerance", "Moderate")
        base_allocations = {
            "Conservative": {"stocks": 40, "bonds": 45, "etfs": 12, "cash": 3},
            "Moderate": {"stocks": 60, "bonds": 25, "etfs": 12, "cash": 3},
            "Aggressive": {"stocks": 80, "bonds": 10, "etfs": 8, "cash": 2},
        }
        allocation = base_allocations.get(risk_tolerance, base_allocations["Moderate"])
        return {
            "allocation": allocation,
            "expected_return": "8-12%",
            "risk_score": 0.6,
            "method": "fallback",
            "ai_service": "fallback",
        }

    def _get_fallback_stock_scoring(self, stocks: List[Dict[str, Any]], user_profile: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Fallback stock scoring"""
        scored = []
        for s in stocks:
            base_score = float(s.get("beginner_friendly_score", 5.0))
            scored.append({
                **s,
                "ml_score": base_score,
                "ml_confidence": 0.5,
                "ml_reasoning": f"Fallback score based on beginner-friendly rating: {base_score}",
            })
        return sorted(scored, key=lambda x: x["ml_score"], reverse=True)

    def _get_fallback_market_analysis(self) -> Dict[str, Any]:
        """Fallback market analysis"""
        return {
            "market_overview": {"sp500_return": 0.0, "volatility": 0.15, "method": "fallback"},
            "sector_performance": {"technology": "neutral", "healthcare": "neutral", "financials": "neutral"},
            "economic_indicators": {"interest_rate": 0.05, "gdp_growth": 0.02, "method": "fallback"},
            "regime_indicators": {"market_regime": "sideways", "method": "fallback"},
            "ai_service": "fallback",
        }

    # ---------- Input validation ----------

    def _validate_user_profile(self, user_profile: Dict[str, Any]) -> None:
        """
        Validate user profile input for ML methods.
        Ensures required keys exist and values are in valid ranges.
        """
        if not isinstance(user_profile, dict):
            raise ValueError("user_profile must be a dictionary")

        # Check for required risk_tolerance
        risk_tolerance = user_profile.get("risk_tolerance")
        if risk_tolerance:
            valid_risks = ["Conservative", "Moderate", "Aggressive", "Low", "Medium", "High"]
            if risk_tolerance not in valid_risks:
                logger.warning(f"Invalid risk_tolerance: {risk_tolerance}, using default")
                user_profile["risk_tolerance"] = "Moderate"

        # Validate numeric fields if present
        numeric_fields = ["age", "income", "investment_horizon_years"]
        for field in numeric_fields:
            if field in user_profile:
                value = user_profile[field]
                if not isinstance(value, (int, float)) or value < 0:
                    logger.warning(f"Invalid {field}: {value}, must be non-negative number")
                    # Set safe defaults
                    if field == "age":
                        user_profile[field] = 35
                    elif field == "income":
                        user_profile[field] = 50000
                    elif field == "investment_horizon_years":
                        user_profile[field] = 10

    def _get_current_timestamp(self) -> str:
        """Get current timestamp in ISO format"""
        return timezone.now().isoformat()

    def get_service_status(self) -> Dict[str, Any]:
        """Get status of all AI services (configuration state only)"""
        return {
            "openai_available": OPENAI_AVAILABLE and bool(self._config.api_key),
            "ml_available": ML_AVAILABLE and bool(self.ml_service),
            "market_data_available": ML_AVAILABLE and bool(self.market_data_service),
            "api_key_configured": bool(self._config.api_key),
            "timestamp": self._get_current_timestamp(),
        }

    def ping(self) -> Dict[str, Any]:
        """
        Health check with actual connectivity tests.
        Tests OpenAI and ML services with real API calls.
        
        Returns:
            Dict with ping results including latency and error details
        """
        status = self.get_service_status()
        out = {**status, "openai_ping": None, "ml_ping": None}

        # OpenAI ping
        if status["openai_available"]:
            t0 = time.perf_counter()
            try:
                self._chat_complete(
                    [
                        {"role": "system", "content": "Return 'ok'."},
                        {"role": "user", "content": "ok"}
                    ],
                    max_tokens=2,
                    temperature=0.0,
                )
                out["openai_ping"] = {
                    "ok": True,
                    "latency_ms": int((time.perf_counter() - t0) * 1000)
                }
            except Exception as e:
                out["openai_ping"] = {
                    "ok": False,
                    "error": str(e),
                    "latency_ms": int((time.perf_counter() - t0) * 1000)
                }

        # ML ping
        if status["ml_available"] and self.market_data_service:
            t0 = time.perf_counter()
            try:
                _ = self._cached_regime_indicators()
                out["ml_ping"] = {
                    "ok": True,
                    "latency_ms": int((time.perf_counter() - t0) * 1000)
                }
            except Exception as e:
                out["ml_ping"] = {
                    "ok": False,
                    "error": str(e),
                    "latency_ms": int((time.perf_counter() - t0) * 1000)
                }

        return out
