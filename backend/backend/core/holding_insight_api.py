"""
Holding Insight API - AI insights for individual portfolio holdings
Phase 3: Fast, cached, human-readable insights
"""

from fastapi import APIRouter, HTTPException, Query
from typing import Optional, Dict, Tuple
from pydantic import BaseModel, ValidationError
from datetime import datetime, timedelta
import asyncio
import json
import logging
import os

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/coach", tags=["Holding Insights"])

_CACHE_TTL_SECONDS = int(os.getenv("HOLDING_INSIGHT_CACHE_TTL", "600"))
_INSIGHT_CACHE: Dict[str, Tuple[datetime, Dict[str, object]]] = {}


class HoldingInsight(BaseModel):
    """AI insight response for a holding"""
    headline: str  # One-line "Why now" insight
    drivers: list[str]  # Up to 3 key drivers


class HoldingInsightLLMResponse(BaseModel):
    headline: str
    drivers: list[str]


def _normalize_insight(ticker: str, insight: Dict[str, object]) -> Dict[str, object]:
    headline = (insight.get("headline") or "").strip()
    drivers = insight.get("drivers") or []

    if not headline:
        headline = f"{ticker} analysis available"
    if not isinstance(drivers, list):
        drivers = []

    cleaned_drivers = [str(d).strip() for d in drivers if str(d).strip()]
    if not cleaned_drivers:
        cleaned_drivers = ["Market analysis", "Sector trends", "Performance metrics"]

    return {
        "headline": headline,
        "drivers": cleaned_drivers[:3],
    }


def _get_cached_insight(ticker: str) -> Optional[Dict[str, object]]:
    cached = _INSIGHT_CACHE.get(ticker)
    if not cached:
        return None
    expires_at, insight = cached
    if datetime.utcnow() >= expires_at:
        _INSIGHT_CACHE.pop(ticker, None)
        return None
    return insight


def _set_cached_insight(ticker: str, insight: Dict[str, object]) -> None:
    expires_at = datetime.utcnow() + timedelta(seconds=_CACHE_TTL_SECONDS)
    _INSIGHT_CACHE[ticker] = (expires_at, insight)


def _extract_json_object(text: str) -> Optional[str]:
    if not text:
        return None
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1 or end <= start:
        return None
    return text[start:end + 1]


def _fallback_insight(ticker: str) -> Dict[str, object]:
    """Generate a generic fallback insight when the LLM is unavailable."""
    return {
        "headline": f"{ticker} — AI insight temporarily unavailable",
        "drivers": ["Market analysis pending", "Check back shortly"],
    }


async def _call_llm_insight(ticker: str) -> Optional[Dict[str, object]]:
    openai_api_key = os.getenv("OPENAI_API_KEY")
    if not openai_api_key:
        return None

    try:
        from openai import OpenAI
    except Exception as e:
        logger.warning(f"OpenAI client unavailable: {e}")
        return None

    model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    client = OpenAI(api_key=openai_api_key)

    system_prompt = (
        "You are a financial insights assistant. Provide a concise, neutral, "
        "non-advisory insight about a stock ticker. Avoid price predictions or "
        "buy/sell advice. Respond ONLY as JSON with keys: headline (string), "
        "drivers (array of 1-3 strings)."
    )
    user_prompt = (
        f"Generate a short insight for {ticker}. "
        "The headline must be a single sentence. Drivers must be short noun phrases."
    )

    def _invoke_llm():
        return client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.4,
        )

    try:
        response = await asyncio.to_thread(_invoke_llm)
        content = response.choices[0].message.content if response.choices else ""
        json_blob = _extract_json_object(content or "")
        if not json_blob:
            return None
        data = json.loads(json_blob)
        parsed = HoldingInsightLLMResponse(**data)
        return {"headline": parsed.headline, "drivers": parsed.drivers}
    except (json.JSONDecodeError, ValidationError) as e:
        logger.warning(f"Failed to parse LLM insight for {ticker}: {e}")
        return None
    except Exception as e:
        logger.error(f"LLM insight generation failed for {ticker}: {e}")
        return None


@router.get("/holding-insight", response_model=HoldingInsight)
async def get_holding_insight(ticker: str = Query(..., description="Stock ticker symbol")):
    """
    Get AI-powered insight for a specific holding.
    
    Returns a quick, actionable insight about why this holding might be
    interesting right now. Cached for 5-15 minutes.
    
    Example:
        GET /api/coach/holding-insight?ticker=AAPL
        {
            "headline": "Strong earnings beat expected",
            "drivers": ["Revenue growth", "iPhone sales", "Services expansion"]
        }
    """
    try:
        ticker = ticker.upper().strip()

        cached = _get_cached_insight(ticker)
        if cached:
            return HoldingInsight(**cached)
        
        insight = await _call_llm_insight(ticker)
        if not insight:
            insight = _fallback_insight(ticker)

        insight = _normalize_insight(ticker, insight)
        _set_cached_insight(ticker, insight)
        
        logger.info(f"Generated insight for {ticker}: {insight['headline']}")
        
        return HoldingInsight(**insight)
        
    except Exception as e:
        logger.error(f"Error generating insight for {ticker}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to generate insight: {str(e)}")

