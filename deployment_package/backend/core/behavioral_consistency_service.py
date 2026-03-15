"""
Phase 2: Behavioral consistency score and archetype drift signal.
Rule-based from engagement events; optional data-driven drift via centroid similarity.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional

from .behavioral_events import get_recent_clicks_by_rec_type
from .behavioral_ranking_service import _ARCHETYPE_AFFINITY

# Fixed rec_type order for vector representation (clustering / data-driven drift)
REC_TYPES_ORDER = [
    "cancel_leak", "build_emergency_fund", "pay_debt", "capture_match",
    "start_investing", "increase_contribution", "rebalance", "reduce_concentration",
    "tax_loss_harvest", "reduce_fees", "redirect_savings",
]

# Minimum clicks in window before we report drift (avoid overreacting to tiny sample)
_MIN_CLICKS_FOR_DRIFT = 5
_DRIFT_DAYS = 30
_CONSISTENCY_DAYS = 30
_LEARNED_CENTROIDS_PATH = os.environ.get(
    "DRIFT_CENTROIDS_PATH",
    str(Path(__file__).resolve().parent / "drift_centroids.json"),
)


@dataclass
class DriftSignal:
    """Suggested behavioral archetype from recent engagement; never overwrites quiz profile."""
    suggested_archetype: str
    confidence_match: float  # 0-1: how well quiz archetype matches behavior (1 = perfect match)
    message_key: str  # App uses for copy: style_evolving, consider_retake, etc.
    show_nudge: bool  # Whether to show a gentle nudge in UI


@dataclass
class ConsistencyResult:
    """Consistency score and optional drift for a user."""
    consistency_score: float  # 0-1, 1 = behavior matches stated profile
    drift: Optional[DriftSignal] = None


def compute_consistency_score(
    user_id: str,
    profile_archetype: str,
    days: int = _CONSISTENCY_DAYS,
) -> float:
    """
    Rule-based consistency: how much do this user's clicks align with their quiz archetype?
    Uses same affinity map as ranking: high affinity = aligned, low = less aligned.
    Returns 0-1 (1 = very consistent).
    """
    clicks = get_recent_clicks_by_rec_type(user_id, days=days)
    if not clicks:
        return 1.0  # No behavior yet → assume consistent

    arch_affinity = _ARCHETYPE_AFFINITY.get(profile_archetype, {})
    total_weighted = 0.0
    total_clicks = 0
    for rec_type, count in clicks.items():
        aff = arch_affinity.get(rec_type, 0.5)
        total_weighted += count * aff
        total_clicks += count
    if total_clicks == 0:
        return 1.0
    # Normalize: average affinity is in [0,1]; use it as consistency
    avg_affinity = total_weighted / total_clicks
    return round(min(1.0, max(0.0, avg_affinity)), 2)


def get_engagement_vector(user_id: str, days: int = _DRIFT_DAYS) -> List[float]:
    """User's click counts per REC_TYPES_ORDER, L2-normalized. For clustering/classifier."""
    clicks = get_recent_clicks_by_rec_type(user_id, days=days)
    vec = [float(clicks.get(rt, 0)) for rt in REC_TYPES_ORDER]
    norm = (sum(x * x for x in vec)) ** 0.5
    if norm <= 0:
        return vec
    return [x / norm for x in vec]


def _rule_based_centroids() -> Dict[str, List[float]]:
    """Centroid per archetype from fixed affinity (normalized)."""
    out = {}
    for arch, aff_map in _ARCHETYPE_AFFINITY.items():
        vec = [aff_map.get(rt, 0.5) for rt in REC_TYPES_ORDER]
        norm = (sum(x * x for x in vec)) ** 0.5 or 1.0
        out[arch] = [x / norm for x in vec]
    return out


def _load_learned_centroids() -> Optional[Dict[str, List[float]]]:
    """Load learned centroids from file (from prior clustering on many users)."""
    try:
        with open(_LEARNED_CENTROIDS_PATH, "r") as f:
            data = json.load(f)
        return data.get("centroids")
    except Exception:
        return None


def _cosine_sim(a: List[float], b: List[float]) -> float:
    if len(a) != len(b):
        return 0.0
    return sum(x * y for x, y in zip(a, b))


def get_drift_signal(
    user_id: str,
    profile_archetype: str,
    days: int = _DRIFT_DAYS,
    min_clicks: int = _MIN_CLICKS_FOR_DRIFT,
    use_data_driven: bool = True,
) -> Optional[DriftSignal]:
    """
    Which archetype best fits this user's recent clicks? If it differs from quiz,
    return a non-accusatory drift signal. use_data_driven: use centroid similarity
    (and learned centroids file if present); else pure rule-based dot product.
    """
    clicks = get_recent_clicks_by_rec_type(user_id, days=days)
    total_clicks = sum(clicks.values())
    if total_clicks < min_clicks:
        return None

    if use_data_driven:
        centroids = _load_learned_centroids() or _rule_based_centroids()
        user_vec = get_engagement_vector(user_id, days)
        best_archetype = profile_archetype
        best_score = -1.0
        quiz_score = -1.0
        for arch, cvec in centroids.items():
            sim = _cosine_sim(user_vec, cvec)
            if sim > best_score:
                best_score = sim
                best_archetype = arch
            if arch == profile_archetype:
                quiz_score = sim
    else:
        best_archetype = profile_archetype
        best_score = 0.0
        quiz_score = 0.0
        for arch, aff_map in _ARCHETYPE_AFFINITY.items():
            score = sum(clicks.get(rt, 0) * aff_map.get(rt, 0.5) for rt in clicks)
            if score > best_score:
                best_score = score
                best_archetype = arch
            if arch == profile_archetype:
                quiz_score = score

    if best_archetype == profile_archetype:
        return None

    confidence_match = quiz_score / best_score if best_score > 0 else 0.0
    confidence_match = round(min(1.0, max(0.0, confidence_match)), 2)
    show_nudge = confidence_match < 0.7
    message_key = "style_evolving" if show_nudge else "consider_retake"
    return DriftSignal(
        suggested_archetype=best_archetype,
        confidence_match=confidence_match,
        message_key=message_key,
        show_nudge=show_nudge,
    )


def get_consistency_result(
    user_id: str,
    profile_archetype: str,
    days: int = _CONSISTENCY_DAYS,
) -> ConsistencyResult:
    """Single entry point: consistency score + optional drift for GraphQL."""
    score = compute_consistency_score(user_id, profile_archetype, days)
    drift = get_drift_signal(user_id, profile_archetype, days)
    return ConsistencyResult(consistency_score=score, drift=drift)
