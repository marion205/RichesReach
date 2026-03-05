"""
daily_market_brief.py
=====================
Generates a short AI market brief: regime + top signals + LLM synthesis (~200 words).
Uses existing infra: regime detector, FSS/ML signals, and configured LLM (OpenAI/Anthropic).

Run via scheduler (e.g. Celery beat at market open) or on-demand.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class DailyMarketBrief:
    """Morning brief output."""
    regime: str
    top_bullish: List[str]   # symbols or labels
    top_bearish: List[str]
    narrative: str            # 150–250 word LLM-generated summary
    generated_at: str         # ISO timestamp


def build_daily_brief(
    regime: str,
    top_signals: Optional[List[Dict[str, Any]]] = None,
    max_bullish: int = 5,
    max_bearish: int = 5,
    use_llm: bool = True,
) -> DailyMarketBrief:
    """
    Build a morning market brief from current regime and optional signal list.

    Parameters
    ----------
    regime : str
        Current market regime (e.g. Expansion, Crisis).
    top_signals : list[dict], optional
        Each dict: symbol, signal (Bullish/Bearish/Neutral), confidence, fss_score, ml_score.
        If None, bullish/bearish lists are empty.
    max_bullish, max_bearish : int
        Cap on symbols to include in the brief.
    use_llm : bool
        If True, call LLM to generate narrative; else return a template sentence.

    Returns
    -------
    DailyMarketBrief
    """
    from datetime import datetime, timezone
    top_bullish: List[str] = []
    top_bearish: List[str] = []
    if top_signals:
        for s in top_signals:
            sym = s.get("symbol") or s.get("ticker") or "?"
            sig = (s.get("signal") or "").lower()
            if "bull" in sig and len(top_bullish) < max_bullish:
                top_bullish.append(sym)
            elif "bear" in sig and len(top_bearish) < max_bearish:
                top_bearish.append(sym)

    if use_llm:
        narrative = _synthesise_brief_with_llm(regime, top_bullish, top_bearish)
    else:
        narrative = (
            f"Market regime: {regime}. "
            + (f"Top bullish names: {', '.join(top_bullish[:5]) or 'None'}. " if top_bullish else "")
            + (f"Top bearish: {', '.join(top_bearish[:5])}. " if top_bearish else "")
        )

    return DailyMarketBrief(
        regime=regime,
        top_bullish=top_bullish,
        top_bearish=top_bearish,
        narrative=narrative,
        generated_at=datetime.now(timezone.utc).isoformat(),
    )


def _synthesise_brief_with_llm(regime: str, bullish: List[str], bearish: List[str]) -> str:
    """Call configured LLM to produce a short morning brief. Fallback to template on failure."""
    try:
        from .trade_debrief_formatter import _call_llm
        prompt = (
            f"You are a quantitative market commentator. In 2–4 short sentences (under 80 words total), "
            f"summarise today's context: regime={regime}, "
            f"top bullish symbols: {bullish or 'none'}, top bearish: {bearish or 'none'}. "
            "Do not give specific buy/sell advice. Output a single JSON object: {\"narrative\": \"...\"}."
        )
        out = _call_llm(prompt)
        if isinstance(out, dict) and out.get("narrative"):
            return str(out["narrative"]).strip()
    except Exception as e:
        logger.warning("Daily brief LLM failed: %s — using template", e)
    return (
        f"Regime: {regime}. "
        + (f"Notable bullish: {', '.join(bullish[:5])}. " if bullish else "")
        + (f"Notable bearish: {', '.join(bearish[:5])}. " if bearish else "")
    )
