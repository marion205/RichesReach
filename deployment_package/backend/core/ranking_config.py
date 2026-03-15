"""
Ranking and A/B config for behavioral ML.
Shadow mode: log ML vs rule order, show rule order.
A/B: fraction of traffic to ML order (0=rule only, 100=full ML).
Weights: updated by feedback job (recency, archetype, popularity, urgency).
"""

from __future__ import annotations

import json
import logging
import os
from pathlib import Path
from typing import Any, Dict

logger = logging.getLogger(__name__)

# Default path for feedback-written weights (relative to project or cwd)
_DEFAULT_WEIGHTS_PATH = os.environ.get(
    "RANKING_WEIGHTS_PATH",
    str(Path(__file__).resolve().parent / "ranking_weights.json"),
)

# In-memory cache so we don't read file every request
_cached_weights: Dict[str, float] | None = None


def get_shadow_mode() -> bool:
    """If True, we log shadow (rule + ml order) but always return rule order."""
    return os.environ.get("SHADOW_RANKING", "false").lower() in ("1", "true", "yes")


def get_ml_traffic_fraction() -> float:
    """Fraction of traffic (0.0–1.0) that gets ML-ranked order. 0=shadow only (rule), 1=full ML."""
    try:
        v = float(os.environ.get("RANKING_ML_TRAFFIC_FRACTION", "0"))
        return max(0.0, min(1.0, v))
    except ValueError:
        return 0.0


def _user_to_bucket(user_id: str) -> int:
    """Stable bucket 0-99 for A/B assignment (same user same day gets same arm)."""
    from datetime import datetime
    day = datetime.utcnow().strftime("%Y-%m-%d")
    h = hash((user_id, day)) % 100
    return (h + 100) % 100


def should_serve_ml_order(user_id: str) -> bool:
    """True if this user should get ML-ranked order (for A/B)."""
    frac = get_ml_traffic_fraction()
    if frac <= 0:
        return False
    if frac >= 1:
        return True
    return _user_to_bucket(user_id) < int(frac * 100)


def get_ranking_weights() -> Dict[str, Any]:
    """Weights for ranking (recency, archetype, popularity, urgency). Optional 'segments' for Phase 3 overrides."""
    global _cached_weights
    if _cached_weights is not None:
        return _cached_weights
    try:
        with open(_DEFAULT_WEIGHTS_PATH, "r") as f:
            data = json.load(f)
            w = data.get("weights", {})
            base = {k: float(v) for k, v in w.items() if k in ("recency", "archetype", "popularity", "urgency")}
            if len(base) == 4:
                _cached_weights = {**base, "segments": w.get("segments", {})}
                return _cached_weights
    except Exception as e:
        logger.debug("Could not load ranking weights: %s", e)
    _cached_weights = {
        "recency": 0.4,
        "archetype": 0.3,
        "popularity": 0.2,
        "urgency": 0.1,
        "segments": {},
    }
    return _cached_weights


def set_ranking_weights(weights: Dict[str, float]) -> None:
    """Write weights to file (feedback job). Merges with existing so 'segments' is preserved."""
    global _cached_weights
    _cached_weights = None
    try:
        current = {}
        with open(_DEFAULT_WEIGHTS_PATH, "r") as f:
            current = json.load(f).get("weights", {})
        merged = {**current, **{k: v for k, v in weights.items() if k in ("recency", "archetype", "popularity", "urgency")}}
        with open(_DEFAULT_WEIGHTS_PATH, "w") as f:
            json.dump({"weights": merged}, f, indent=2)
    except FileNotFoundError:
        with open(_DEFAULT_WEIGHTS_PATH, "w") as f:
            json.dump({"weights": weights}, f, indent=2)
    except Exception as e:
        logger.warning("Could not write ranking weights: %s", e)


def invalidate_weights_cache() -> None:
    """Force next get_ranking_weights() to read from file."""
    global _cached_weights
    _cached_weights = None
