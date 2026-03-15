"""
Phase 3: Bias-from-behavior signal.
Uses engagement (which recs clicked vs ignored) to suggest possible bias types.
Rules still own the final bias flag and coaching; this is an input signal only.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List

from .behavioral_events import get_recent_clicks_by_rec_type


# Minimum interactions before we suggest any bias (avoid noise)
_MIN_CLICKS_FOR_SIGNAL = 3
_DAYS = 30

# Rec-type buckets for rule-based bias inference
_SAFETY_REC_TYPES = {"cancel_leak", "build_emergency_fund", "pay_debt"}
_GROWTH_REC_TYPES = {
    "start_investing",
    "increase_contribution",
    "reduce_concentration",
    "tax_loss_harvest",
    "rebalance",
    "redirect_savings",
}
# Strong signal for "chasing" / action-oriented
_ACTION_ORIENTED_REC_TYPES = {"start_investing", "reduce_concentration", "tax_loss_harvest"}


@dataclass
class BiasSignalResult:
    """Suggested bias types from behavior; rules still own final flag and message."""
    suggested_bias_types: List[str]  # e.g. ["recency", "overconfidence"]
    confidence: float  # 0-1
    show_in_ui: bool  # Only show when we have enough signal and confidence


def get_behavioral_bias_signal(
    user_id: str,
    days: int = _DAYS,
    min_clicks: int = _MIN_CLICKS_FOR_SIGNAL,
) -> BiasSignalResult:
    """
    Rule-based: infer possible bias types from which recommendations the user acts on.
    Safety-heavy engagement → loss_aversion signal. Growth-heavy → recency/overconfidence.
    """
    clicks = get_recent_clicks_by_rec_type(user_id, days=days)
    total = sum(clicks.values())
    if total < min_clicks:
        return BiasSignalResult(
            suggested_bias_types=[],
            confidence=0.0,
            show_in_ui=False,
        )

    safety_clicks = sum(clicks.get(rt, 0) for rt in _SAFETY_REC_TYPES)
    growth_clicks = sum(clicks.get(rt, 0) for rt in _GROWTH_REC_TYPES)
    action_clicks = sum(clicks.get(rt, 0) for rt in _ACTION_ORIENTED_REC_TYPES)

    suggested: List[str] = []
    confidence = 0.0

    # Growth/action heavy → may align with recency or overconfidence (chasing, overconfident)
    if growth_clicks > 0 and safety_clicks >= 0:
        ratio = growth_clicks / (safety_clicks + 1)
        if ratio >= 2.0:
            suggested.extend(["recency", "overconfidence"])
            confidence = min(0.85, 0.5 + 0.1 * (ratio - 2))
        elif action_clicks >= 2 and total >= 4:
            suggested.append("recency")
            confidence = 0.55

    # Safety heavy → may align with loss aversion (staying very safe)
    if safety_clicks > 0 and growth_clicks >= 0:
        ratio = safety_clicks / (growth_clicks + 1)
        if ratio >= 2.0 and "loss_aversion" not in suggested:
            suggested.append("loss_aversion")
            confidence = max(confidence, min(0.75, 0.5 + 0.1 * (ratio - 2)))

    # Reduce concentration engagement often means we're nudging them (concentration risk)
    if clicks.get("reduce_concentration", 0) >= 2 and total >= 4:
        if "concentration" not in suggested:
            suggested.append("concentration")
        confidence = max(confidence, 0.5)

    # Dedupe and cap confidence
    suggested = list(dict.fromkeys(suggested))[:3]
    confidence = round(min(1.0, max(0.0, confidence)), 2)
    show_in_ui = len(suggested) > 0 and confidence >= 0.5

    return BiasSignalResult(
        suggested_bias_types=suggested,
        confidence=confidence,
        show_in_ui=show_in_ui,
    )
