"""
brief_views.py
==============
REST endpoint for the Daily AI Market Brief.

GET  /api/market/brief/
    Returns the latest cached brief, or generates one on-demand if the cache
    is empty (first request of the day before the scheduler has run).

Response (200 OK):
{
    "regime":       "Expansion",
    "top_bullish":  ["NVDA", "MSFT", "AAPL"],
    "top_bearish":  ["XOM"],
    "narrative":    "Markets are in an Expansion regime...",
    "generated_at": "2025-01-15T09:30:00+00:00",
    "from_cache":   true
}

Authentication: optional — unauthenticated requests get the same brief
(brief is market-wide, not personalised).
"""

from __future__ import annotations

import json
import logging

from django.http import JsonResponse
from django.views import View

logger = logging.getLogger(__name__)

_CACHE_KEY = "daily_market_brief"
_CACHE_TTL  = 86_400   # 24 hours — management command refreshes daily


class DailyMarketBriefView(View):
    """
    GET /api/market/brief/

    Returns the cached daily brief or generates one on-demand.
    Optional query param: ?regime=Crisis   (override for on-demand generation)
    """

    def get(self, request, *args, **kwargs):
        # Try cache first
        try:
            from django.core.cache import cache
            cached = cache.get(_CACHE_KEY)
            if cached:
                cached["from_cache"] = True
                return JsonResponse(cached, status=200)
        except Exception as exc:
            logger.debug("Cache read failed: %s", exc)

        # On-demand generation (cache miss or cache unavailable)
        regime_override = request.GET.get("regime") or None
        brief_dict = self._generate_brief(regime_override)
        brief_dict["from_cache"] = False

        # Write to cache so the next request is fast
        try:
            from django.core.cache import cache
            cache.set(_CACHE_KEY, brief_dict, timeout=_CACHE_TTL)
        except Exception as exc:
            logger.debug("Cache write failed: %s", exc)

        return JsonResponse(brief_dict, status=200)

    def _generate_brief(self, regime_override: str | None = None) -> dict:
        """Generate a brief on-demand (no cache). Returns a safe fallback on error."""
        # Detect regime
        regime = regime_override
        if not regime:
            try:
                from .ai_service import AIService
                indicators = AIService()._cached_regime_indicators()
                regime = (
                    indicators.get("regime", "Unknown")
                    if isinstance(indicators, dict)
                    else "Unknown"
                )
            except Exception:
                regime = "Unknown"

        # Score a small representative universe for top signals
        top_signals = []
        _BRIEF_TICKERS = [
            "AAPL", "MSFT", "NVDA", "GOOGL", "AMZN",
            "META", "TSLA", "JPM", "V", "XOM",
        ]
        try:
            from django.db.models import Q
            from .models import Stock
            from .ai_service import AIService

            stocks_qs = list(
                Stock.objects.filter(symbol__in=_BRIEF_TICKERS)
                .values("id", "symbol", "name", "beginner_friendly_score", "current_price")
            )
            if stocks_qs:
                scored = AIService().score_stocks_ml(stocks_qs, {}, {})
                for s in scored:
                    sig = s.get("signal_output") or {}
                    top_signals.append({
                        "symbol":     s.get("symbol"),
                        "signal":     sig.get("signal", "Neutral"),
                        "confidence": sig.get("confidence", "Low"),
                        "fss_score":  s.get("fss_score"),
                        "ml_score":   s.get("ml_score"),
                    })
        except Exception as exc:
            logger.warning("on-demand brief: stock scoring failed: %s", exc)

        # Build brief
        try:
            from .daily_market_brief import build_daily_brief
            brief = build_daily_brief(
                regime=regime,
                top_signals=top_signals or None,
                use_llm=True,
            )
            return {
                "regime":       brief.regime,
                "top_bullish":  brief.top_bullish,
                "top_bearish":  brief.top_bearish,
                "narrative":    brief.narrative,
                "generated_at": brief.generated_at,
            }
        except Exception as exc:
            logger.error("on-demand brief generation failed: %s", exc)
            from datetime import datetime, timezone
            return {
                "regime":       regime or "Unknown",
                "top_bullish":  [],
                "top_bearish":  [],
                "narrative":    "Daily brief temporarily unavailable. Please try again shortly.",
                "generated_at": datetime.now(timezone.utc).isoformat(),
            }
