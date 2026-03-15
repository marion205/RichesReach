"""
Behavioral ranking for Next Best Actions.
Reorders the rule-engine list using configurable weights (recency, archetype,
global popularity, financial urgency). Weights updated by feedback job.
Does not add/remove or outrank safety.
"""

from __future__ import annotations

from typing import List, Optional

from .behavioral_events import get_recent_dismissals_by_rec_type
from .next_best_action_service import NextBestAction
from .ranking_config import get_ranking_weights


# MVP: archetype affinity per action type (0–1). Which actions resonate with each archetype.
_ARCHETYPE_AFFINITY: dict[str, dict[str, float]] = {
    "cautious_protector": {
        "cancel_leak": 0.95,
        "build_emergency_fund": 0.95,
        "pay_debt": 0.9,
        "capture_match": 0.85,
        "start_investing": 0.7,
        "increase_contribution": 0.75,
        "rebalance": 0.8,
        "reduce_concentration": 0.85,
        "tax_loss_harvest": 0.6,
        "reduce_fees": 0.9,
        "redirect_savings": 0.85,
    },
    "steady_builder": {
        "cancel_leak": 0.85,
        "build_emergency_fund": 0.9,
        "pay_debt": 0.9,
        "capture_match": 0.95,
        "start_investing": 0.9,
        "increase_contribution": 0.95,
        "rebalance": 0.9,
        "reduce_concentration": 0.85,
        "tax_loss_harvest": 0.75,
        "reduce_fees": 0.85,
        "redirect_savings": 0.9,
    },
    "opportunity_hunter": {
        "cancel_leak": 0.7,
        "build_emergency_fund": 0.65,
        "pay_debt": 0.75,
        "capture_match": 0.9,
        "start_investing": 0.95,
        "increase_contribution": 0.9,
        "rebalance": 0.85,
        "reduce_concentration": 0.9,
        "tax_loss_harvest": 0.9,
        "reduce_fees": 0.8,
        "redirect_savings": 0.85,
    },
    "reactive_trader": {
        "cancel_leak": 0.8,
        "build_emergency_fund": 0.75,
        "pay_debt": 0.85,
        "capture_match": 0.8,
        "start_investing": 0.9,
        "increase_contribution": 0.85,
        "rebalance": 0.9,
        "reduce_concentration": 0.95,
        "tax_loss_harvest": 0.85,
        "reduce_fees": 0.85,
        "redirect_savings": 0.8,
    },
}

# Global popularity (MVP: same for everyone; could be from aggregate stats later).
_GLOBAL_POPULARITY: dict[str, float] = {
    "cancel_leak": 0.9,
    "build_emergency_fund": 0.85,
    "pay_debt": 0.88,
    "capture_match": 0.92,
    "start_investing": 0.85,
    "increase_contribution": 0.8,
    "rebalance": 0.75,
    "reduce_concentration": 0.7,
    "tax_loss_harvest": 0.65,
    "reduce_fees": 0.78,
    "redirect_savings": 0.82,
}


def reorder(
    actions: List[NextBestAction],
    user_id: str,
    archetype: str,
    recency_days: int = 7,
    segment: Optional[str] = None,
) -> List[NextBestAction]:
    """
    Reorder rule-engine actions by configurable weights. Same set, no add/remove.
    Weights come from ranking_config (updated by feedback job). Optional segment override.
    """
    if not actions:
        return actions

    w = get_ranking_weights()
    # Phase 3: segment-level overrides (e.g. by archetype or maturity)
    if segment:
        seg_weights = w.get("segments", {}).get(segment)
        if isinstance(seg_weights, dict):
            w = {**w, **seg_weights}

    rw = w.get("recency", 0.4)
    aw = w.get("archetype", 0.3)
    pw = w.get("popularity", 0.2)
    uw = w.get("urgency", 0.1)

    dismissed = get_recent_dismissals_by_rec_type(user_id, days=recency_days)
    arch_map = _ARCHETYPE_AFFINITY.get(archetype, {})
    default_affinity = 0.5
    default_pop = 0.5

    def score(a: NextBestAction) -> float:
        rec_type = a.action_type.value
        recency = 0.2 if dismissed.get(rec_type) else 1.0
        arch = arch_map.get(rec_type, default_affinity)
        pop = _GLOBAL_POPULARITY.get(rec_type, default_pop)
        urgency = min(1.0, max(0.0, a.priority_score / 100.0))
        return (
            rw * recency
            + aw * arch
            + pw * pop
            + uw * urgency
        )

    return sorted(actions, key=score, reverse=True)
