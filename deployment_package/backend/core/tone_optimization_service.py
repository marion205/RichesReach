"""
Phase 1 Messenger: Tone optimization for recommendations.
Maps rec (or rec_type) + user history to a template variant (e.g. "direct" vs "encouraging").
Content still comes from rules; this only picks which variant to use.
"""

from __future__ import annotations

from collections import defaultdict
from typing import List, Optional

from .behavioral_events import get_events

# Variant keys the app can use to select copy (rules still own the actual content).
TONE_VARIANTS = ("default", "direct", "encouraging", "minimal")


def get_tone_variant(
    user_id: str,
    rec_id: str,
    rec_type: Optional[str] = None,
) -> str:
    """
    Which tone variant to use for this recommendation for this user.
    Uses engagement: which variant led to clicks for this user/rec_type.
    """
    best = _best_variant_for_user_rec(user_id, rec_type or rec_id)
    return best if best in TONE_VARIANTS else "default"


def _best_variant_for_user_rec(user_id: str, rec_type: str) -> str:
    """From events: which variant had highest CTR for this user + rec_type."""
    events = get_events(user_id, since_days=30)
    # Impressions with variant
    impressions_per_variant: dict[str, int] = defaultdict(int)
    clicks_per_variant: dict[str, int] = defaultdict(int)
    for e in events:
        if e.get("event_type") == "impression":
            rt = e.get("rec_type") or e.get("rec_id")
            if rt != rec_type:
                continue
            v = e.get("tone_variant") or "default"
            impressions_per_variant[v] += 1
        elif e.get("event_type") == "interaction" and e.get("action") == "click":
            rt = e.get("rec_type") or e.get("rec_id")
            if rt != rec_type:
                continue
            v = e.get("tone_variant") or "default"
            clicks_per_variant[v] += 1
    # Best variant = highest CTR; if no data, default
    best_v = "default"
    best_ctr = -1.0
    for v in TONE_VARIANTS:
        imp = impressions_per_variant.get(v, 0)
        clk = clicks_per_variant.get(v, 0)
        if imp < 3:
            continue
        ctr = clk / imp
        if ctr > best_ctr:
            best_ctr = ctr
            best_v = v
    return best_v


def get_tone_variants_for_recs(
    user_id: str,
    rec_ids: List[str],
    rec_types: Optional[List[str]] = None,
) -> List[str]:
    """Return one variant per rec (for logging impressions)."""
    types = rec_types or []
    return [
        get_tone_variant(user_id, rid, types[i] if i < len(types) else None)
        for i, rid in enumerate(rec_ids)
    ]
