"""
analyst_features.py
===================
Builds analyst revision / recommendation features for the ML pipeline:
- analyst_rev_1m: change in mean EPS estimate over last 30 days (placeholder 0 until estimate API).
- rec_upgrade_score: (buy - sell) / total from Finnhub recommendation, normalised.
- fy1_rev_3m: FY1 EPS estimate change over 90 days (placeholder 0 until estimate API).

Aligned to price index via merge_asof(..., direction='backward').
"""

from __future__ import annotations

import logging
from typing import Optional

import numpy as np
import pandas as pd

from .analyst_loader import REC_COL_DATE

logger = logging.getLogger(__name__)

ANALYST_FEATURE_NAMES = [
    "analyst_rev_1m",
    "rec_upgrade_score",
    "fy1_rev_3m",
]


def build_analyst_features(
    price_df: pd.DataFrame,
    recommendation_df: Optional[pd.DataFrame],
) -> pd.DataFrame:
    """
    Build analyst features aligned to the price DataFrame index.

    If recommendation_df is None or empty, returns zeros for all three features.
    """
    out = pd.DataFrame(index=price_df.index)
    out.index = pd.to_datetime(out.index)
    for c in ANALYST_FEATURE_NAMES:
        out[c] = 0.0

    if recommendation_df is None or recommendation_df.empty:
        return out[ANALYST_FEATURE_NAMES]

    if "rec_score" not in recommendation_df.columns or REC_COL_DATE not in recommendation_df.columns:
        return out[ANALYST_FEATURE_NAMES]

    rdf = recommendation_df[[REC_COL_DATE, "rec_score"]].copy()
    rdf[REC_COL_DATE] = pd.to_datetime(rdf[REC_COL_DATE])
    rdf = rdf.sort_values(REC_COL_DATE)
    sorted_idx = price_df.index.sort_values()
    left = pd.DataFrame({"trade_date": sorted_idx}, index=sorted_idx)
    merged = pd.merge_asof(
        left,
        rdf.rename(columns={REC_COL_DATE: "report_date"}),
        left_on="trade_date",
        right_on="report_date",
        direction="backward",
    )
    merged = merged.reindex(price_df.index)
    out["rec_upgrade_score"] = merged["rec_score"].fillna(0.0).values
    # analyst_rev_1m, fy1_rev_3m: reserved for estimate revision API
    return out[ANALYST_FEATURE_NAMES]
