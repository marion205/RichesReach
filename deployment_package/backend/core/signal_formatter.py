"""
signal_formatter.py
===================
Converts raw FSS/ML numeric scores into structured, human-readable signal output.

Output contract (SignalOutput TypedDict):
  {
      "signal":      "Bullish" | "Neutral" | "Bearish",
      "confidence":  "High" | "Medium" | "Low",
      "reasons":     ["Price above 50D MA", ...],   # 2-5 plain-English bullet points
      "regime":      str,                            # e.g. "Expansion", "Crisis"
      "fss_score":   float,   # 0-100  (kept for power-user / debugging)
      "ml_score":    float | None,  # 0-10  (None until model trained)
      "data_source": "live" | "cache" | "unavailable",
      "fallback_used": bool,
      "passed_safety_filters": bool,
      "safety_reason": str,
  }

Usage
-----
    from .signal_formatter import format_signal
    output = format_signal(fss_result, ml_result)

    # Or from raw dicts (e.g. coming out of score_stocks_production_r2):
    from .signal_formatter import format_signal_from_dicts
    output = format_signal_from_dicts(scored_stock_dict)
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional, TypedDict

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Output type
# ---------------------------------------------------------------------------

class SignalOutput(TypedDict):
    """Structured signal output — the canonical response shape across all endpoints."""
    signal: str           # "Bullish" | "Neutral" | "Bearish"
    confidence: str       # "High" | "Medium" | "Low"
    reasons: List[str]    # 2-5 plain-English bullet points
    regime: str
    fss_score: float
    ml_score: Optional[float]
    data_source: str      # "live" | "cache" | "unavailable"
    fallback_used: bool
    passed_safety_filters: bool
    safety_reason: str


# ---------------------------------------------------------------------------
# Signal thresholds
# ---------------------------------------------------------------------------

# FSS score → directional signal
_FSS_BULLISH_THRESHOLD = 60.0   # score ≥ 60 → Bullish
_FSS_BEARISH_THRESHOLD = 40.0   # score < 40 → Bearish

# Component score descriptors (same scale: 0-100)
_STRONG = 65.0
_WEAK   = 35.0

# Confidence label mapping (FSS engine uses lowercase; we surface Title Case)
_CONFIDENCE_MAP = {
    "high":   "High",
    "medium": "Medium",
    "low":    "Low",
}


# ---------------------------------------------------------------------------
# Main entry points
# ---------------------------------------------------------------------------

def format_signal(
    fss_result: Any,
    ml_result: Optional[Dict[str, Any]] = None,
    data_source: str = "live",
) -> SignalOutput:
    """
    Build a SignalOutput from an FSSResult dataclass (from fss_engine.py)
    and an optional ML result dict (from ml_service.score_stocks_production_r2).

    Parameters
    ----------
    fss_result : FSSResult
        Output of fss_engine.get_stock_fss().
    ml_result : dict, optional
        Dict with keys: ml_score, ml_confidence, ml_reasoning, predicted_return.
    data_source : str
        "live" | "cache" | "unavailable"

    Returns
    -------
    SignalOutput
    """
    try:
        fss_score   = float(getattr(fss_result, "fss_score", 0.0) or 0.0)
        trend       = float(getattr(fss_result, "trend_score", 50.0) or 50.0)
        fundamental = float(getattr(fss_result, "fundamental_score", 50.0) or 50.0)
        capital     = float(getattr(fss_result, "capital_flow_score", 50.0) or 50.0)
        risk        = float(getattr(fss_result, "risk_score", 50.0) or 50.0)
        regime      = str(getattr(fss_result, "regime", "Unknown") or "Unknown")
        safety_ok   = bool(getattr(fss_result, "passed_safety_filters", True))
        safety_txt  = str(getattr(fss_result, "safety_reason", "OK") or "OK")
        raw_conf    = str(getattr(fss_result, "confidence", "low") or "low").lower()
    except Exception as exc:
        logger.warning("format_signal: could not parse FSSResult — %s", exc)
        return _unavailable_signal()

    signal     = _derive_signal(fss_score, safety_ok)
    confidence = _CONFIDENCE_MAP.get(raw_conf, "Low")
    reasons    = _build_reasons(
        signal, trend, fundamental, capital, risk, regime,
        safety_ok, safety_txt, ml_result
    )

    ml_score: Optional[float] = None
    if ml_result:
        raw = ml_result.get("ml_score") or ml_result.get("predicted_return")
        if raw is not None:
            try:
                ml_score = float(raw)
            except (ValueError, TypeError):
                pass

    return SignalOutput(
        signal=signal,
        confidence=confidence,
        reasons=reasons,
        regime=regime,
        fss_score=round(fss_score, 1),
        ml_score=round(ml_score, 2) if ml_score is not None else None,
        data_source=data_source,
        fallback_used=(data_source != "live"),
        passed_safety_filters=safety_ok,
        safety_reason=safety_txt,
    )


def format_signal_from_dicts(
    scored_stock: Dict[str, Any],
    data_source: str = "live",
) -> SignalOutput:
    """
    Build a SignalOutput directly from the flat dict produced by
    ml_service.score_stocks_production_r2() / score_stocks_ml().

    Expected keys (all optional with graceful defaults):
        fss_score, fss_confidence, fss_regime,
        trend_score, fundamental_score, capital_flow_score, risk_score,
        passed_safety_filters, safety_reason,
        ml_score, ml_confidence, ml_reasoning, predicted_return,
        fallback_used
    """
    fss_score   = float(scored_stock.get("fss_score", 0.0) or 0.0)
    trend       = float(scored_stock.get("trend_score", 50.0) or 50.0)
    fundamental = float(scored_stock.get("fundamental_score", 50.0) or 50.0)
    capital     = float(scored_stock.get("capital_flow_score", 50.0) or 50.0)
    risk        = float(scored_stock.get("risk_score", 50.0) or 50.0)
    regime      = str(scored_stock.get("fss_regime") or scored_stock.get("regime", "Unknown"))
    safety_ok   = bool(scored_stock.get("passed_safety_filters", True))
    safety_txt  = str(scored_stock.get("safety_reason", "OK") or "OK")
    raw_conf    = str(
        scored_stock.get("fss_confidence") or scored_stock.get("ml_confidence") or "low"
    ).lower()

    fallback_used = bool(scored_stock.get("fallback_used", False))
    if fallback_used:
        data_source = "unavailable"

    signal     = _derive_signal(fss_score, safety_ok)
    confidence = _CONFIDENCE_MAP.get(raw_conf, "Low")

    ml_result: Optional[Dict[str, Any]] = None
    if "ml_score" in scored_stock or "ml_reasoning" in scored_stock:
        ml_result = {
            "ml_score":     scored_stock.get("ml_score"),
            "ml_reasoning": scored_stock.get("ml_reasoning"),
            "predicted_return": scored_stock.get("predicted_return"),
        }

    reasons = _build_reasons(
        signal, trend, fundamental, capital, risk, regime,
        safety_ok, safety_txt, ml_result
    )

    ml_score: Optional[float] = None
    if scored_stock.get("ml_score") is not None:
        try:
            ml_score = float(scored_stock["ml_score"])
        except (ValueError, TypeError):
            pass

    return SignalOutput(
        signal=signal,
        confidence=confidence,
        reasons=reasons,
        regime=regime,
        fss_score=round(fss_score, 1),
        ml_score=round(ml_score, 2) if ml_score is not None else None,
        data_source=data_source,
        fallback_used=fallback_used,
        passed_safety_filters=safety_ok,
        safety_reason=safety_txt,
    )


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _derive_signal(fss_score: float, safety_ok: bool) -> str:
    """Map FSS score + safety to directional signal label."""
    if not safety_ok:
        return "Bearish"
    if fss_score >= _FSS_BULLISH_THRESHOLD:
        return "Bullish"
    if fss_score < _FSS_BEARISH_THRESHOLD:
        return "Bearish"
    return "Neutral"


def _build_reasons(
    signal: str,
    trend: float,
    fundamental: float,
    capital: float,
    risk: float,
    regime: str,
    safety_ok: bool,
    safety_txt: str,
    ml_result: Optional[Dict[str, Any]],
) -> List[str]:
    """
    Generate 2–5 plain-English reason strings from component scores.

    Rules:
    - For Bullish: report what's strong (T, F, C scores > _STRONG).
    - For Bearish: report what's weak (T, F, C, R scores < _WEAK) or safety failure.
    - For Neutral: report the strongest and weakest components.
    - Always cap at 5 reasons.
    - If ML model adds conviction, append one ML reason.
    """
    reasons: List[str] = []

    # --- Safety first --------------------------------------------------------
    if not safety_ok:
        reasons.append(f"⚠ Safety filter: {safety_txt}")

    # --- Component-based reasons ----------------------------------------------
    # Trend
    if trend >= _STRONG:
        reasons.append(_trend_reason_bullish(trend))
    elif trend <= _WEAK:
        reasons.append(_trend_reason_bearish(trend))
    else:
        if signal == "Bullish":
            reasons.append("Momentum is building but not yet decisive")
        elif signal == "Bearish":
            reasons.append("Trend is mixed — no strong directional signal")

    # Fundamental
    if fundamental >= _STRONG:
        reasons.append(_fundamental_reason_bullish(fundamental))
    elif fundamental <= _WEAK:
        reasons.append(_fundamental_reason_bearish(fundamental))

    # Capital Flow
    if capital >= _STRONG:
        reasons.append(_capital_reason_bullish(capital))
    elif capital <= _WEAK:
        reasons.append(_capital_reason_bearish(capital))

    # Risk
    if risk >= _STRONG:
        reasons.append("Low volatility with resilient price action near recent highs")
    elif risk <= _WEAK:
        reasons.append("Elevated volatility or significant drawdown from recent peak")

    # --- Regime context -------------------------------------------------------
    regime_note = _regime_note(regime, signal)
    if regime_note:
        reasons.append(regime_note)

    # --- ML model addendum (only if informative) ------------------------------
    if ml_result:
        ml_reason = _ml_reason(ml_result)
        if ml_reason:
            reasons.append(ml_reason)

    # --- Fallback: if no reasons generated ------------------------------------
    if not reasons:
        if signal == "Bullish":
            reasons.append("FSS composite score above neutral — overall signal is positive")
        elif signal == "Bearish":
            reasons.append("FSS composite score below neutral — overall signal is negative")
        else:
            reasons.append("Mixed signals across trend, fundamentals and capital flow")

    return reasons[:5]  # cap at 5


def _trend_reason_bullish(score: float) -> str:
    if score >= 80:
        return "Strong price momentum with consistent outperformance vs the market"
    if score >= 65:
        return "Price above 50-day MA with positive risk-adjusted momentum"
    return "Upward trend developing — price action improving vs benchmark"


def _trend_reason_bearish(score: float) -> str:
    if score <= 20:
        return "Sharp downtrend — stock materially underperforming the market"
    if score <= 35:
        return "Price below key moving averages with negative momentum"
    return "Trend weakening — momentum fading relative to benchmark"


def _fundamental_reason_bullish(score: float) -> str:
    if score >= 80:
        return "Accelerating EPS and strong revenue growth with expanding margins"
    if score >= 65:
        return "Solid earnings growth with improving fundamental backdrop"
    return "Fundamentals above average — earnings trend is positive"


def _fundamental_reason_bearish(score: float) -> str:
    if score <= 20:
        return "Deteriorating fundamentals: EPS deceleration and revenue pressure"
    if score <= 35:
        return "Earnings growth slowing — fundamental headwinds present"
    return "Fundamental backdrop mixed — limited earnings catalyst near-term"


def _capital_reason_bullish(score: float) -> str:
    if score >= 80:
        return "Strong institutional accumulation with high-conviction volume breakout"
    if score >= 65:
        return "Volume-price trend shows net institutional buying pressure"
    return "Positive capital flow — more accumulation than distribution"


def _capital_reason_bearish(score: float) -> str:
    if score <= 20:
        return "Heavy distribution: volume confirms institutional selling pressure"
    if score <= 35:
        return "Capital flow negative — selling volume outweighs buying"
    return "Volume-price trend weakening — limited buying conviction"


def _regime_note(regime: str, signal: str) -> Optional[str]:
    """Return a short regime context note, or None if not informative."""
    regime_lower = regime.lower()

    if "crisis" in regime_lower:
        return "Market in crisis regime — defensive positioning favoured across the board"
    if "deflation" in regime_lower or "bear" in regime_lower:
        if signal == "Bullish":
            return "Bear market regime: strong conviction required — signal swimming against the tide"
        return "Bear market regime adds tailwind to bearish signal"
    if "parabolic" in regime_lower:
        if signal == "Bullish":
            return "Parabolic / high-vol regime: momentum signals elevated but reversal risk is high"
        return None
    if "expansion" in regime_lower or "bull" in regime_lower:
        if signal == "Bearish":
            return "Expansion regime: bearish signal is counter-trend — use tighter stops"
        return None

    return None


def _ml_reason(ml_result: Dict[str, Any]) -> Optional[str]:
    """
    Return a single ML addendum reason, or None.
    Only surfaces a reason when the model has actionable signal.
    """
    raw_pred = ml_result.get("predicted_return")
    ml_score = ml_result.get("ml_score")
    reasoning = ml_result.get("ml_reasoning", "")

    # Don't surface ML if it's a fallback / zero prediction
    if raw_pred is None and ml_score is None:
        return None

    try:
        pred_val = float(raw_pred) if raw_pred is not None else (float(ml_score) - 5.0) / 2.5
    except (ValueError, TypeError):
        return None

    if pred_val > 0.5:
        return f"LightGBM model signals positive vol-adjusted return (signal={pred_val:+.2f})"
    if pred_val < -0.5:
        return f"LightGBM model signals negative vol-adjusted return (signal={pred_val:+.2f})"

    # Signal too weak to be informative
    return None


def _unavailable_signal() -> SignalOutput:
    """Return a safe default when signal data is unavailable."""
    return SignalOutput(
        signal="Neutral",
        confidence="Low",
        reasons=["Insufficient data to generate a signal — please try again shortly"],
        regime="Unknown",
        fss_score=0.0,
        ml_score=None,
        data_source="unavailable",
        fallback_used=True,
        passed_safety_filters=True,
        safety_reason="No data",
    )
