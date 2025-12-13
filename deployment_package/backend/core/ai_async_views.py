# core/ai_async_views.py
"""
Async Django views for AI chat endpoints.
Compatible with Django 3.1+ async views and ASGI.

Endpoints:
- POST /api/ai/chat/ - Non-streaming JSON response (Oracle-style format)
- POST /api/ai/chat/stream/ - Streaming SSE response (token-by-token)
- GET /api/ai/health/ - Health check with connectivity tests

Features:
- Per-user rate limiting (30 requests/minute default)
- Unified response format matching Rust Oracle (one_sentence, why, risk_note)
- Proper SSE headers for nginx/proxy compatibility
- User authentication extraction from JWT tokens
"""
import json
import asyncio
import logging
from typing import Any, Dict, Optional

from django.http import JsonResponse, StreamingHttpResponse
from django.core.cache import cache
from asgiref.sync import sync_to_async

from .ai_service_async import AIServiceAsync
from .async_decorators import async_csrf_exempt, async_require_http_methods

logger = logging.getLogger(__name__)


# Singleton instance (reused across requests)
_ai_service: AIServiceAsync = None


async def get_ai_service() -> AIServiceAsync:
    """Get singleton AI service instance"""
    global _ai_service
    if _ai_service is None:
        _ai_service = await AIServiceAsync.get_instance()
    return _ai_service


def _rate_limit_user(user_id: str, limit: Optional[int] = None, window_s: Optional[int] = None) -> bool:
    """
    Per-user rate limiting (sync helper for cache).
    Returns True if request allowed, False if rate limited.
    """
    from django.conf import settings
    limit = limit or getattr(settings, "AI_RATE_LIMIT_PER_USER", 30)
    window_s = window_s or getattr(settings, "AI_RATE_LIMIT_WINDOW_S", 60)
    
    key = f"ai:rate:{user_id}"
    count = cache.get(key, 0)
    if count >= limit:
        return False
    cache.set(key, count + 1, timeout=window_s)
    return True


async def get_user_id_from_request(request) -> Optional[str]:
    """
    Extract user ID from request (JWT token or session).
    Returns None if unauthenticated.
    """
    try:
        # Try JWT token from Authorization header
        auth_header = request.headers.get("Authorization", "")
        if auth_header:
            token = auth_header.replace("Bearer ", "").replace("JWT ", "").strip()
            if token:
                # Import auth helper (sync, so wrap it)
                from .authentication import get_user_from_token
                try:
                    user = await sync_to_async(get_user_from_token)(token)
                    if user:
                        return str(user.id)
                except Exception:
                    pass
        
        # Fallback to session
        if hasattr(request, "user") and request.user.is_authenticated:
            return str(request.user.id)
        
        # Fallback to IP for anonymous users
        return request.META.get("REMOTE_ADDR", "anonymous")
    except Exception:
        return "anonymous"


# Decorator order matters: csrf_exempt must be on top (applied last)
# so it marks the final wrapper that Django sees
@async_csrf_exempt
@async_require_http_methods(["POST"])
async def chat_view(request):
    """
    Non-streaming chat endpoint with Oracle-style response format.
    POST /api/ai/chat/
    
    Request body:
    {
        "messages": [
            {"role": "user", "content": "What should I invest in?"}
        ],
        "user_context": "optional context string"
    }
    
    Response (Oracle-style, matches Rust UnifiedSignal format):
    {
        "one_sentence": "Jobs-style summary",
        "content": "full response text",
        "confidence": 0.9,
        "why": ["reason 1", "reason 2"],
        "risk_note": "Risk-aware guidance",
        "tokens_used": 150,
        "model_used": "gpt-4o-mini",
        "latency_ms": 850,
        "fallback_used": false,
        "error_type": null
    }
    """
    try:
        # Rate limiting
        user_id = await get_user_id_from_request(request)
        if not await sync_to_async(_rate_limit_user)(user_id):
            return JsonResponse(
                {"error": "Rate limit exceeded", "retry_after": 60},
                status=429
            )
        
        # Read request body (Django async views support request.body directly)
        body = request.body
        if not body:
            return JsonResponse({"error": "Request body required"}, status=400)
        
        try:
            data = json.loads(body.decode('utf-8') if isinstance(body, bytes) else body)
        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON"}, status=400)

        messages = data.get("messages", [])
        if not messages:
            return JsonResponse({"error": "messages array required"}, status=400)
        
        user_context = data.get("user_context")
        
        ai_service = await get_ai_service()
        resp = await ai_service.get_chat_response_async(messages, user_context=user_context)
        
        # Transform to Oracle-style format (matches Rust UnifiedSignal)
        oracle_resp = await ai_service._format_oracle_response(resp, messages)
        
        return JsonResponse(oracle_resp)
    
    except Exception as e:
        logger.exception("chat_view error")
        return JsonResponse(
            {"error": "Internal server error", "detail": str(e)},
            status=500
        )


# IMPORTANT: csrf_exempt on top (applied last) so it marks the final wrapper
@async_csrf_exempt
@async_require_http_methods(["POST"])
async def stream_chat_view(request):
    """
    Streaming chat endpoint (SSE format).
    POST /api/ai/chat/stream/
    
    Request body: Same as chat_view
    
    Response: Server-Sent Events (text/event-stream)
    data: {"type": "token", "content": "Hello"}
    data: {"type": "token", "content": " there"}
    data: {"type": "done", "content": ""}
    """
    try:
        # Read request body (Django async views support request.body directly)
        body = request.body
        if not body:
            async def error_stream():
                yield "data: " + json.dumps({"type": "error", "content": "Request body required"}) + "\n\n"
            return StreamingHttpResponse(
                error_stream(),
                content_type="text/event-stream",
                status=400
            )
        
        try:
            data = json.loads(body.decode('utf-8') if isinstance(body, bytes) else body)
        except json.JSONDecodeError:
            async def error_stream():
                yield "data: " + json.dumps({"type": "error", "content": "Invalid JSON"}) + "\n\n"
            return StreamingHttpResponse(
                error_stream(),
                content_type="text/event-stream",
                status=400
            )

        messages = data.get("messages", [])
        if not messages:
            async def error_stream():
                yield "data: " + json.dumps({"type": "error", "content": "messages array required"}) + "\n\n"
            return StreamingHttpResponse(
                error_stream(),
                content_type="text/event-stream",
                status=400
            )

        
        # Rate limiting
        user_id = await get_user_id_from_request(request)
        if not await sync_to_async(_rate_limit_user)(user_id):
            async def error_stream():
                yield f"data: {json.dumps({'type': 'error', 'content': 'Rate limit exceeded'})}\n\n"
            return StreamingHttpResponse(
                error_stream(),
                content_type="text/event-stream",
                status=429
            )
        
        user_context = data.get("user_context")
        
        ai_service = await get_ai_service()
        
        async def event_stream():
            try:
                async for chunk in ai_service.stream_chat_response_async(messages, user_context=user_context):
                    # Format as SSE
                    yield f"data: {json.dumps(chunk)}\n\n"
                    
                    # Yield control to event loop
                    await asyncio.sleep(0)
            except asyncio.CancelledError:
                # Client disconnected
                logger.info("Stream cancelled by client")
            except Exception as e:
                logger.exception("stream_chat_view error")
                yield f"data: {json.dumps({'type': 'error', 'content': str(e)})}\n\n"
        
        resp = StreamingHttpResponse(event_stream(), content_type="text/event-stream")
        # Critical headers for streaming behind nginx/proxies
        resp["Cache-Control"] = "no-cache"
        resp["X-Accel-Buffering"] = "no"  # Disable nginx buffering
        resp["Connection"] = "keep-alive"  # Keep connection alive for streaming
        return resp
    
    except Exception as e:
        logger.exception("stream_chat_view error")
        async def error_stream():
            yield f"data: {json.dumps({'type': 'error', 'content': str(e)})}\n\n"
        return StreamingHttpResponse(
            error_stream(),
            content_type="text/event-stream",
            status=500
        )


@async_require_http_methods(["GET"])
async def health_view(request):
    """
    Health check endpoint with connectivity tests.
    GET /api/ai/health/
    
    Response:
    {
        "status": "healthy",
        "openai_available": true,
        "async_client_configured": true,
        "streaming_supported": true,
        "model": "gpt-4o-mini",
        "openai_ping": {
            "ok": true,
            "latency_ms": 150
        },
        "asgi": true
    }
    """
    try:
        ai_service = await get_ai_service()
        status = await ai_service.ping()
        
        # Enhanced health response
        enhanced_status = {
            "status": "healthy" if status.get("openai_ping", {}).get("ok") else "degraded",
            "streaming_supported": True,
            "model": ai_service.cfg.model,
            "asgi": True,  # Indicates ASGI is being used
            **status
        }
        
        return JsonResponse(enhanced_status)
    except Exception as e:
        logger.exception("health_view error")
        return JsonResponse(
            {
                "status": "unhealthy",
                "error": "Internal server error",
                "detail": str(e),
                "asgi": True
            },
            status=500
        )
