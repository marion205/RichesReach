# core/ai_service_async.py
"""
Async AI Service for RichesReach AlphaOracle
Production-grade async OpenAI integration with rate limiting, retries, and streaming support.

Designed for ASGI (not WSGI) - use with Django 3.1+ async views or FastAPI.
"""
import os
import asyncio
import time
import logging
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from django.conf import settings
from django.core.cache import cache

logger = logging.getLogger(__name__)

# Optional OpenAI SDK
try:
    from openai import AsyncOpenAI
    from openai import APIError, RateLimitError, APITimeoutError
    OPENAI_AVAILABLE = True
except Exception as e:
    OPENAI_AVAILABLE = False
    AsyncOpenAI = None  # type: ignore
    APIError = RateLimitError = APITimeoutError = Exception  # type: ignore
    logger.warning("OpenAI async SDK not available; AI chat will use fallback. (%s)", e)


@dataclass(frozen=True)
class OpenAIAsyncConfig:
    """Configuration for async OpenAI client"""
    api_key: Optional[str]
    model: str = "gpt-4o-mini"
    max_tokens: int = 1500
    temperature: float = 0.7
    timeout_s: float = 15.0
    max_retries: int = 2
    max_concurrency: int = 10
    max_history: int = 20


class AIServiceAsync:
    """
    Async AI Service with production-grade features:
    - Singleton client per process (reused across requests)
    - Semaphore-based concurrency limiting (prevents rate limit stampedes)
    - Deterministic retry logic
    - Message normalization (prevents prompt injection + bloat)
    - RAHA/AlphaOracle style: fast, deterministic, clean boundaries
    """
    
    _instance: Optional['AIServiceAsync'] = None
    _lock = asyncio.Lock()
    
    def __init__(self) -> None:
        api_key = os.getenv("OPENAI_API_KEY") or getattr(settings, "OPENAI_API_KEY", None)
        
        self.cfg = OpenAIAsyncConfig(
            api_key=api_key,
            model=getattr(settings, "OPENAI_MODEL", "gpt-4o-mini"),
            max_tokens=int(getattr(settings, "OPENAI_MAX_TOKENS", 1500)),
            temperature=float(getattr(settings, "OPENAI_TEMPERATURE", 0.7)),
            timeout_s=float(getattr(settings, "OPENAI_TIMEOUT_S", 15.0)),
            max_retries=int(getattr(settings, "OPENAI_MAX_RETRIES", 2)),
            max_concurrency=int(getattr(settings, "OPENAI_MAX_CONCURRENCY", 10)),
            max_history=int(getattr(settings, "OPENAI_MAX_HISTORY", 20)),
        )

        self.async_client: Optional[AsyncOpenAI] = (
            AsyncOpenAI(api_key=self.cfg.api_key, timeout=self.cfg.timeout_s)
            if self.cfg.api_key and OPENAI_AVAILABLE
            else None
        )
        
        # Semaphore to cap concurrent OpenAI calls (prevents stampedes)
        self._sema = asyncio.Semaphore(self.cfg.max_concurrency)

        if not self.async_client:
            logger.warning("OpenAI async client not configured (missing API key).")

    @classmethod
    async def get_instance(cls) -> 'AIServiceAsync':
        """Get singleton instance (thread-safe)"""
        if cls._instance is None:
            async with cls._lock:
                if cls._instance is None:
                    cls._instance = cls()
        return cls._instance

    def _normalize_messages(
        self, 
        messages: List[Dict[str, Any]], 
        user_context: Optional[str] = None
    ) -> List[Dict[str, str]]:
        """
        Normalize messages: deterministic, bounded, safe.
        Prevents prompt explosion and injection attacks.
        """
        # Keep it bounded (prevents "prompt explosion")
        trimmed = (messages or [])[-self.cfg.max_history:]
        norm: List[Dict[str, str]] = []

        # System/developer guardrail: keep it on-brand + compliant
        system = (
            "You are RichesReach's AlphaOracle assistant. "
            "Be concise, plain-English, and non-hype. "
            "No guarantees. Provide risk-aware guidance. "
            "If user asks what to buy/sell, provide education about risks and suggest consulting a licensed professional. "
            "Avoid guaranteeing returns. "
            "If user indicates financial distress, suggest professional help.\n\n"
            "Available capabilities:\n"
            "- Direct Indexing: Create tax-efficient portfolios that track ETFs using individual stocks (call create_direct_index tool)\n"
            "- Tax-Smart Transitions: Plan gradual diversification of concentrated positions (call create_tax_smart_transition tool)\n"
            "- Tax Alpha Dashboard: Show tax savings metrics from direct indexing (call get_tax_alpha_dashboard tool)\n"
            "- Tax-Loss Harvesting: Find opportunities to offset gains (call find_tax_loss_harvesting_opportunities tool)\n"
            "- Portfolio Optimization: Optimize asset allocation (call optimize_portfolio_allocation tool)\n"
            "- Goal Simulation: Calculate probability of reaching financial goals (call run_monte_carlo_goal_simulation tool)\n"
            "- Retirement Planning: Calculate retirement safety scores (call run_retirement_simulation tool)\n\n"
            "IMPORTANT: When users ask about 'tax alpha dashboard', 'show tax savings', 'show my tax alpha', "
            "'direct indexing', 'track SPY but exclude', 'diversify employer stock', or 'tax-smart transition', "
            "you MUST call the appropriate tool (get_tax_alpha_dashboard, create_direct_index, or create_tax_smart_transition). "
            "Do NOT respond without calling the tool - the tools provide the data and visualizations needed for accurate responses."
        )
        
        # Sanitize user_context to prevent prompt injection
        if user_context:
            sanitized = self._sanitize_user_context(user_context)
            if sanitized:
                system += f" User context: {sanitized[:1000]}"
        
        norm.append({"role": "system", "content": system})

        # Normalize message roles and content
        for m in trimmed:
            role = str(m.get("role", "")).lower().strip()
            # Map common variations
            if role in {"developer", "system"}:
                role = "system"
            elif role not in {"system", "user", "assistant"}:
                role = "user"
            
            content = str(m.get("content", "")).strip()
            if content:
                # Cap individual message length
                norm.append({"role": role, "content": content[:8000]})

        # Ensure at least one user message
        if not any(m["role"] == "user" for m in norm):
            norm.append({"role": "user", "content": "Hello."})
        
        return norm

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
            '### Instructions:',
        ]
        
        sanitized = user_context
        for pattern in forbidden_patterns:
            if pattern.lower() in sanitized.lower():
                logger.warning(f"Potential prompt injection detected, removing pattern: {pattern}")
                sanitized = sanitized.replace(pattern, "").replace(pattern.lower(), "")
        
        return sanitized.strip()

    async def _with_retries(self, coro_factory):
        """
        Deterministic retry logic with exponential backoff.
        Handles RateLimitError with Retry-After header support.
        """
        delays = [0.5, 1.0, 2.0]
        last_err = None
        
        for attempt in range(self.cfg.max_retries + 1):
            try:
                return await coro_factory()
            except RateLimitError as e:
                last_err = e
                # Extract retry-after header if available
                retry_after = None
                if hasattr(e, "response") and e.response:
                    retry_after = e.response.headers.get("Retry-After")
                    if retry_after:
                        try:
                            retry_after = float(retry_after)
                        except (ValueError, TypeError):
                            retry_after = None
                
                if attempt >= self.cfg.max_retries:
                    break
                
                sleep_s = retry_after if retry_after else delays[min(attempt, len(delays) - 1)]
                logger.warning(
                    "openai rate limit attempt=%s/%s sleep=%ss retry_after=%s",
                    attempt + 1, self.cfg.max_retries + 1, sleep_s, retry_after
                )
                await asyncio.sleep(sleep_s)
            except (APITimeoutError, APIError) as e:
                last_err = e
                if attempt >= self.cfg.max_retries:
                    break
                sleep_s = delays[min(attempt, len(delays) - 1)]
                logger.warning(
                    "openai transient err attempt=%s/%s sleep=%ss err=%s",
                    attempt + 1, self.cfg.max_retries + 1, sleep_s, str(e)
                )
                await asyncio.sleep(sleep_s)
            except Exception as e:
                # Non-retryable errors
                logger.exception("openai non-retryable error: %s", str(e))
                raise
        
        raise last_err or RuntimeError("OpenAI call failed after retries")

    async def get_chat_response_async(
        self,
        messages: List[Dict[str, Any]],
        user_context: Optional[str] = None,
        tools: Optional[List[Dict[str, Any]]] = None,
        tool_choice: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get async chat response from OpenAI.
        
        Args:
            messages: List of message dictionaries with 'role' and 'content'
            user_context: Optional user context information
            
        Returns:
            Dictionary containing response content, confidence, and token usage:
            {
                "content": str,
                "confidence": float,
                "tokens_used": int,
                "model_used": str,
                "latency_ms": int,
                "fallback_used": bool,
                "error_type": Optional[str]
            }
        """
        if not self.async_client:
            return self._fallback("OpenAI not configured.", fallback_used=True)

        payload = self._normalize_messages(messages, user_context)

        # Use semaphore to cap concurrent calls (prevents rate limit stampedes)
        async with self._sema:
            t0 = time.perf_counter()

            async def call():
                # Chat Completions API with optional function calling
                kwargs = {
                    "model": self.cfg.model,
                    "messages": payload,
                    "max_tokens": self.cfg.max_tokens,
                    "temperature": self.cfg.temperature,
                }
                
                # Add tools if provided
                if tools:
                    kwargs["tools"] = tools
                    if tool_choice:
                        kwargs["tool_choice"] = tool_choice
                
                return await self.async_client.chat.completions.create(**kwargs)

            try:
                resp = await self._with_retries(call)
                dt_ms = int((time.perf_counter() - t0) * 1000)
                
                choice = resp.choices[0] if resp.choices else None
                content = choice.message.content if choice and choice.message else ""
                tokens_used = resp.usage.total_tokens if resp.usage else 0
                
                # Check for function calls
                tool_calls = []
                if choice and choice.message.tool_calls:
                    tool_calls = [
                        {
                            "id": tc.id,
                            "name": tc.function.name,
                            "arguments": tc.function.arguments
                        }
                        for tc in choice.message.tool_calls
                    ]

                logger.info(
                    "openai.chat ok model=%s tokens=%s ms=%s tool_calls=%s",
                    self.cfg.model, tokens_used, dt_ms, len(tool_calls)
                )

                return {
                    "content": content or "I couldn't generate a response.",
                    "confidence": 0.9,
                    "tokens_used": tokens_used,
                    "model_used": self.cfg.model,
                    "latency_ms": dt_ms,
                    "fallback_used": False,
                    "error_type": None,
                    "tool_calls": tool_calls,  # Include tool calls in response
                }
            except Exception as e:
                dt_ms = int((time.perf_counter() - t0) * 1000)
                error_type = type(e).__name__
                logger.exception("openai.chat failed ms=%s err=%s", dt_ms, str(e))
                return self._fallback(
                    "Temporarily unavailable. Try again.",
                    fallback_used=True,
                    error_type=error_type,
                    latency_ms=dt_ms
                )

    async def stream_chat_response_async(
        self,
        messages: List[Dict[str, Any]],
        user_context: Optional[str] = None
    ):
        """
        Stream chat response token-by-token (for SSE/WebSocket).
        
        Yields dicts: {"type": "token|done|error", "content": str}
        """
        if not self.async_client:
            yield {"type": "error", "content": "OpenAI not configured."}
            return

        payload = self._normalize_messages(messages, user_context)

        async with self._sema:
            try:
                stream = await self.async_client.chat.completions.create(
                    model=self.cfg.model,
                    messages=payload,
                    max_tokens=self.cfg.max_tokens,
                    temperature=self.cfg.temperature,
                    stream=True,
                )
                
                async for chunk in stream:
                    if chunk.choices and len(chunk.choices) > 0:
                        delta = chunk.choices[0].delta
                        if delta and getattr(delta, "content", None):
                            yield {"type": "token", "content": delta.content}
                    
                    # Yield control to event loop
                    await asyncio.sleep(0)
                
                yield {"type": "done", "content": ""}
                
            except asyncio.CancelledError:
                # Client disconnected
                yield {"type": "error", "content": "Connection cancelled"}
            except Exception as e:
                logger.exception("openai.stream failed err=%s", str(e))
                yield {"type": "error", "content": f"Error: {str(e)}"}

    async def ping(self) -> Dict[str, Any]:
        """
        Health check with actual connectivity tests.
        Tests OpenAI with a minimal API call.
        """
        status = {
            "openai_available": OPENAI_AVAILABLE and bool(self.cfg.api_key),
            "async_client_configured": self.async_client is not None,
        }
        
        if status["openai_available"] and self.async_client:
            t0 = time.perf_counter()
            try:
                await self.async_client.chat.completions.create(
                    model=self.cfg.model,
                    messages=[
                        {"role": "system", "content": "Return 'ok'."},
                        {"role": "user", "content": "ok"}
                    ],
                    max_tokens=2,
                    temperature=0.0,
                )
                status["openai_ping"] = {
                    "ok": True,
                    "latency_ms": int((time.perf_counter() - t0) * 1000)
                }
            except Exception as e:
                status["openai_ping"] = {
                    "ok": False,
                    "error": str(e),
                    "latency_ms": int((time.perf_counter() - t0) * 1000)
                }
        else:
            status["openai_ping"] = {"ok": False, "error": "Not configured"}
        
        return status

    async def _format_oracle_response(
        self,
        raw_response: Dict[str, Any],
        original_messages: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Format response to match Rust Oracle style (UnifiedSignal format).
        Adds one_sentence, why, risk_note for consistent UI experience.
        """
        content = raw_response.get("content", "")
        confidence = raw_response.get("confidence", 0.5)
        
        # Extract one_sentence (first sentence or summary)
        one_sentence = content.split(".")[0].strip()
        if len(one_sentence) > 150:
            one_sentence = one_sentence[:147] + "..."
        if not one_sentence:
            one_sentence = "Analysis available."
        
        # Extract "why" reasons (look for bullet points or numbered lists)
        why = []
        lines = content.split("\n")
        for line in lines:
            line = line.strip()
            # Match bullet points or numbered items
            if line.startswith(("•", "-", "*", "1.", "2.", "3.")):
                clean = line.lstrip("•-*0123456789. ").strip()
                if clean and len(clean) > 10:
                    why.append(clean)
            if len(why) >= 3:
                break
        
        # If no bullets found, extract key sentences
        if not why:
            sentences = [s.strip() for s in content.split(".") if len(s.strip()) > 20]
            why = sentences[:2]
        
        # Generate risk_note (always include risk awareness)
        risk_note = (
            "This is educational information, not personalized financial advice. "
            "Consider your risk tolerance and consult a licensed professional for investment decisions. "
            "Past performance does not guarantee future results."
        )
        
        # Map confidence to conviction (matches Rust Oracle)
        conviction = "NEUTRAL"
        if confidence >= 0.8:
            conviction = "STRONG BUY"
        elif confidence >= 0.65:
            conviction = "BUY"
        elif confidence >= 0.5:
            conviction = "WEAK BUY"
        elif confidence < 0.3:
            conviction = "DUMP"
        
        return {
            "one_sentence": one_sentence,
            "content": content,
            "confidence": confidence,
            "conviction": conviction,
            "why": why,
            "risk_note": risk_note,
            "tokens_used": raw_response.get("tokens_used", 0),
            "model_used": raw_response.get("model_used", "fallback"),
            "latency_ms": raw_response.get("latency_ms", 0),
            "fallback_used": raw_response.get("fallback_used", False),
            "error_type": raw_response.get("error_type"),
        }

    def _fallback(
        self, 
        msg: str, 
        fallback_used: bool = True,
        error_type: Optional[str] = None,
        latency_ms: int = 0
    ) -> Dict[str, Any]:
        """Fallback response when OpenAI is unavailable"""
        return {
            "content": msg,
            "confidence": 0.3,
            "tokens_used": 0,
            "model_used": "fallback",
            "latency_ms": latency_ms,
            "fallback_used": fallback_used,
            "error_type": error_type,
        }

