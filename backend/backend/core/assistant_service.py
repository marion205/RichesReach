"""
Conversational Financial Assistant Service
Handles natural language financial queries with optional user and market context.
"""

from __future__ import annotations

import json
import uuid
import logging
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from .advanced_ai_router import get_advanced_ai_router, AIRequest, RequestType, AIModel

logger = logging.getLogger(__name__)


def _now_iso_utc() -> str:
    return datetime.now(timezone.utc).isoformat()


class AssistantService:
    """Natural language financial assistant backed by the AdvancedAIRouter."""

    def __init__(self, ai_router: Optional["AdvancedAIRouter"] = None) -> None:
        self.ai_router = ai_router or get_advanced_ai_router()

    async def query(
        self,
        user_id: Optional[str],
        prompt: str,
        *,
        context: Optional[Dict[str, Any]] = None,
        market_context: Optional[Dict[str, Any]] = None,
        model: AIModel = AIModel.GPT_5,
        requires_reasoning: bool = True,
        max_tokens: int = 1200,
    ) -> Dict[str, Any]:
        if not prompt or not prompt.strip():
            raise ValueError("prompt must be a non-empty string")

        structured_prompt = {
            "task": "assistant_query",
            "prompt": prompt,
            "user_context": context or {},
            "market_context": market_context or {},
            "requirements": [
                "Be clear and concise",
                "If uncertain, state assumptions",
                "Avoid personalized investment advice",
                "Include actionable educational guidance when applicable",
            ],
            "output_format": {
                "answer": "string",
                "assumptions": ["string"],
                "suggested_followups": ["string"],
                "disclaimer": "string"
            },
            "response_style": "Return ONLY valid JSON matching output_format. No markdown.",
        }
        req = AIRequest(
            request_id=str(uuid.uuid4()),
            request_type=RequestType.GENERAL_CHAT,
            prompt=json.dumps(structured_prompt),
            context={"user_id": user_id},
            model_preference=model,
            requires_reasoning=requires_reasoning,
            max_tokens=max_tokens,
        )
        resp = await self.ai_router.route_request(req)
        try:
            data = json.loads(resp.response)
        except Exception:
            data = {
                "answer": prompt,
                "assumptions": [],
                "suggested_followups": [],
                "disclaimer": "Educational purposes only; not financial advice.",
            }
        data["model"] = getattr(resp, "model", None)
        data["confidence_score"] = getattr(resp, "confidence_score", None)
        data["generated_at"] = _now_iso_utc()
        return data


assistant_service = AssistantService()
