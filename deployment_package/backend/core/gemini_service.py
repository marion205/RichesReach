# core/gemini_service.py
"""
Google Gemini AI Service Integration
Handles requests that require large context windows, OCR, and real-time market data.

Gemini strengths:
- Massive context window (up to 2M tokens)
- Excellent for document analysis and OCR
- Real-time data processing
- Cost-effective for large inputs
"""
import os
import asyncio
import time
import logging
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from django.conf import settings

logger = logging.getLogger(__name__)

# Optional Google Generative AI SDK
try:
    import google.generativeai as genai
    from google.generativeai.types import HarmCategory, HarmBlockThreshold
    GEMINI_AVAILABLE = True
except Exception as e:
    GEMINI_AVAILABLE = False
    genai = None  # type: ignore
    HarmCategory = HarmBlockThreshold = None  # type: ignore
    logger.warning("Google Generative AI SDK not available; Gemini features disabled. (%s)", e)


@dataclass(frozen=True)
class GeminiConfig:
    """Configuration for Gemini client"""
    api_key: Optional[str]
    model: str = "gemini-1.5-pro"  # or "gemini-1.5-flash" for faster responses
    max_output_tokens: int = 8192
    temperature: float = 0.7
    timeout_s: float = 30.0  # Longer timeout for large documents
    max_retries: int = 2
    max_concurrency: int = 5  # Lower than ChatGPT (Gemini can be slower for large docs)


class GeminiService:
    """
    Async Gemini Service for large context and document analysis.
    
    Features:
    - Large context window support (up to 2M tokens)
    - Document/PDF analysis
    - OCR capabilities
    - Real-time market data processing
    - Stateless requests (no data training)
    """
    
    _instance: Optional['GeminiService'] = None
    _lock = asyncio.Lock()
    
    def __init__(self) -> None:
        api_key = os.getenv("GEMINI_API_KEY") or getattr(settings, "GEMINI_API_KEY", None)
        
        self.cfg = GeminiConfig(
            api_key=api_key,
            model=getattr(settings, "GEMINI_MODEL", "gemini-1.5-pro"),
            max_output_tokens=int(getattr(settings, "GEMINI_MAX_OUTPUT_TOKENS", 8192)),
            temperature=float(getattr(settings, "GEMINI_TEMPERATURE", 0.7)),
            timeout_s=float(getattr(settings, "GEMINI_TIMEOUT_S", 30.0)),
            max_retries=int(getattr(settings, "GEMINI_MAX_RETRIES", 2)),
            max_concurrency=int(getattr(settings, "GEMINI_MAX_CONCURRENCY", 5)),
        )
        
        # Initialize Gemini client
        if GEMINI_AVAILABLE and self.cfg.api_key:
            try:
                genai.configure(api_key=self.cfg.api_key)
                self.model = genai.GenerativeModel(self.cfg.model)
                logger.info(f"Gemini service initialized with model: {self.cfg.model}")
            except Exception as e:
                logger.error(f"Failed to initialize Gemini: {e}")
                self.model = None
        else:
            self.model = None
            if not GEMINI_AVAILABLE:
                logger.warning("Gemini SDK not available")
            if not self.cfg.api_key:
                logger.warning("GEMINI_API_KEY not configured")
        
        # Semaphore for concurrency limiting
        self._sema = asyncio.Semaphore(self.cfg.max_concurrency)
    
    @classmethod
    async def get_instance(cls) -> 'GeminiService':
        """Get singleton instance (thread-safe)"""
        if cls._instance is None:
            async with cls._lock:
                if cls._instance is None:
                    cls._instance = cls()
        return cls._instance
    
    def _build_safety_settings(self) -> List[Dict[str, Any]]:
        """
        Build safety settings for Gemini API.
        Ensures appropriate content filtering for financial data.
        """
        if not GEMINI_AVAILABLE:
            return []
        
        return [
            {
                "category": HarmCategory.HARM_CATEGORY_HARASSMENT,
                "threshold": HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
            },
            {
                "category": HarmCategory.HARM_CATEGORY_HATE_SPEECH,
                "threshold": HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
            },
            {
                "category": HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT,
                "threshold": HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
            },
            {
                "category": HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT,
                "threshold": HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
            },
        ]
    
    def _normalize_messages(self, messages: List[Dict[str, Any]], user_context: Optional[str] = None) -> str:
        """
        Normalize messages for Gemini API.
        Gemini uses a single prompt string (not message array like OpenAI).
        """
        # Build system prompt
        system_prompt = (
            "You are RichesReach's AlphaOracle assistant specializing in financial analysis. "
            "You excel at analyzing large documents, extracting data from financial statements, "
            "and processing real-time market information. "
            "Be concise, plain-English, and non-hype. "
            "No guarantees. Provide risk-aware guidance. "
            "If user asks what to buy/sell, provide education about risks and suggest consulting a licensed professional. "
            "Avoid guaranteeing returns. "
            "If user indicates financial distress, suggest professional help."
        )
        
        if user_context:
            system_prompt += f"\n\nUser context: {user_context[:2000]}"
        
        # Convert message array to single prompt
        prompt_parts = [system_prompt]
        
        for msg in messages[-20:]:  # Keep last 20 messages
            role = str(msg.get("role", "")).lower().strip()
            content = str(msg.get("content", "")).strip()
            
            if not content:
                continue
            
            if role == "system":
                # System messages are already in the prompt
                continue
            elif role == "user":
                prompt_parts.append(f"User: {content[:8000]}")
            elif role == "assistant":
                prompt_parts.append(f"Assistant: {content[:8000]}")
        
        return "\n\n".join(prompt_parts)
    
    async def _with_retries(self, coro_factory):
        """Retry logic with exponential backoff for Gemini API."""
        delays = [1.0, 2.0, 4.0]
        last_err = None
        
        for attempt in range(self.cfg.max_retries + 1):
            try:
                return await coro_factory()
            except Exception as e:
                last_err = e
                error_str = str(e).lower()
                
                # Check for rate limiting
                if "quota" in error_str or "rate limit" in error_str:
                    if attempt >= self.cfg.max_retries:
                        break
                    sleep_s = delays[min(attempt, len(delays) - 1)]
                    logger.warning(
                        "gemini rate limit attempt=%s/%s sleep=%ss",
                        attempt + 1, self.cfg.max_retries + 1, sleep_s
                    )
                    await asyncio.sleep(sleep_s)
                elif "timeout" in error_str:
                    if attempt >= self.cfg.max_retries:
                        break
                    sleep_s = delays[min(attempt, len(delays) - 1)]
                    logger.warning(
                        "gemini timeout attempt=%s/%s sleep=%ss",
                        attempt + 1, self.cfg.max_retries + 1, sleep_s
                    )
                    await asyncio.sleep(sleep_s)
                else:
                    # Non-retryable errors
                    logger.exception("gemini non-retryable error: %s", str(e))
                    raise
        
        raise last_err or RuntimeError("Gemini call failed after retries")
    
    async def get_chat_response_async(
        self,
        messages: List[Dict[str, Any]],
        user_context: Optional[str] = None,
        tools: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """
        Get async chat response from Gemini.
        
        Args:
            messages: List of message dictionaries
            user_context: Optional user context
            
        Returns:
            Dictionary with response content and metadata
        """
        if not self.model:
            return self._fallback("Gemini not configured.", fallback_used=True)
        
        prompt = self._normalize_messages(messages, user_context)
        
        async with self._sema:
            t0 = time.perf_counter()
            
            async def call():
                # Run in executor since genai is sync
                loop = asyncio.get_event_loop()
                
                # Build generation config
                gen_config = {
                    "max_output_tokens": self.cfg.max_output_tokens,
                    "temperature": self.cfg.temperature,
                }
                
                # Add tools if provided (Gemini function calling)
                # Note: Gemini uses a different format - would need to convert
                # For now, tools are handled at orchestrator level
                
                return await loop.run_in_executor(
                    None,
                    lambda: self.model.generate_content(
                        prompt,
                        generation_config=gen_config,
                        safety_settings=self._build_safety_settings(),
                    )
                )
            
            try:
                resp = await self._with_retries(call)
                dt_ms = int((time.perf_counter() - t0) * 1000)
                
                content = resp.text if hasattr(resp, 'text') else ""
                # Estimate tokens (rough approximation)
                tokens_used = len(prompt.split()) + len(content.split())
                
                logger.info(
                    "gemini.chat ok model=%s tokens_est=%s ms=%s",
                    self.cfg.model, tokens_used, dt_ms
                )
                
                return {
                    "content": content or "I couldn't generate a response.",
                    "confidence": 0.9,
                    "tokens_used": tokens_used,
                    "model_used": self.cfg.model,
                    "latency_ms": dt_ms,
                    "fallback_used": False,
                    "error_type": None,
                }
            except Exception as e:
                dt_ms = int((time.perf_counter() - t0) * 1000)
                error_type = type(e).__name__
                logger.exception("gemini.chat failed ms=%s err=%s", dt_ms, str(e))
                return self._fallback(
                    "Temporarily unavailable. Try again.",
                    fallback_used=True,
                    error_type=error_type,
                    latency_ms=dt_ms
                )
    
    async def analyze_document_async(
        self,
        document_path: str,
        query: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Analyze a document (PDF, image) using Gemini's vision capabilities.
        
        Args:
            document_path: Path to document file
            query: Optional query about the document
            
        Returns:
            Analysis results
        """
        if not self.model:
            return self._fallback("Gemini not configured for document analysis.", fallback_used=True)
        
        try:
            # Load document
            import mimetypes
            mime_type, _ = mimetypes.guess_type(document_path)
            
            # For now, return placeholder (full implementation would use Gemini's file API)
            return {
                "content": "Document analysis feature requires file upload API integration.",
                "confidence": 0.5,
                "tokens_used": 0,
                "model_used": self.cfg.model,
                "latency_ms": 0,
                "fallback_used": True,
                "error_type": "NotImplemented",
            }
        except Exception as e:
            logger.exception("gemini.analyze_document failed err=%s", str(e))
            return self._fallback(
                "Document analysis failed.",
                fallback_used=True,
                error_type=type(e).__name__
            )
    
    async def ping(self) -> Dict[str, Any]:
        """Health check for Gemini service."""
        status = {
            "gemini_available": GEMINI_AVAILABLE and bool(self.cfg.api_key),
            "model_configured": self.model is not None,
        }
        
        if status["gemini_available"] and self.model:
            t0 = time.perf_counter()
            try:
                loop = asyncio.get_event_loop()
                await loop.run_in_executor(
                    None,
                    lambda: self.model.generate_content(
                        "Return 'ok'.",
                        generation_config={"max_output_tokens": 2, "temperature": 0.0}
                    )
                )
                status["gemini_ping"] = {
                    "ok": True,
                    "latency_ms": int((time.perf_counter() - t0) * 1000)
                }
            except Exception as e:
                status["gemini_ping"] = {
                    "ok": False,
                    "error": str(e),
                    "latency_ms": int((time.perf_counter() - t0) * 1000)
                }
        else:
            status["gemini_ping"] = {"ok": False, "error": "Not configured"}
        
        return status
    
    def _fallback(
        self,
        msg: str,
        fallback_used: bool = True,
        error_type: Optional[str] = None,
        latency_ms: int = 0
    ) -> Dict[str, Any]:
        """Fallback response when Gemini is unavailable"""
        return {
            "content": msg,
            "confidence": 0.3,
            "tokens_used": 0,
            "model_used": "gemini-fallback",
            "latency_ms": latency_ms,
            "fallback_used": fallback_used,
            "error_type": error_type,
        }

