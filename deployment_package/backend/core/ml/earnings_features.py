"""
earnings_features.py
====================
Builds leakage-proof earnings features for the ML pipeline:
- eps_surprise_pct: consensus surprise (only known after report effective_date).
- days_since_earnings: days since last report (PEAD decay).
- surprise_decay: eps_surprise_pct * exp(-days_since_earnings/20) so model can learn half-life.

All features are aligned to the price index via merge_asof(..., direction='backward')
so we only use information known by the open of that bar.
"""

from __future__ import annotations

import logging
from typing import Optional

import numpy as np
import pandas as pd

from .earnings_loader import (
    EARNINGS_COL_EFFECTIVE_DATE,
    EARNINGS_COL_EPS_SURPRISE_PCT,
    EARNINGS_COL_REVENUE_SURPRISE_PCT,
)

logger = logging.getLogger(__name__)

EARNINGS_FEATURE_NAMES = [
    "eps_surprise_pct",
    "surprise_decay",
    "days_since_earnings",
]

# Half-life in days for exponential decay of surprise (PEAD literature: 20–40 days)
_SURPRISE_HALFLIFE_DAYS = 20.0


def build_earnings_features(
    price_df: pd.DataFrame,
    earnings_df: Optional[pd.DataFrame],
) -> pd.DataFrame:
    """
    Build earnings features aligned to the price DataFrame index (daily bars).

    Parameters
    ----------
    price_df : pd.DataFrame
        Daily OHLCV (or any DataFrame with DatetimeIndex). Index = trade date.
    earnings_df : pd.DataFrame or None
        Output of earnings_loader.fetch_earnings: effective_date, eps_surprise_pct, etc.
        If None or empty, returns a DataFrame of zeros with same index and EARNINGS_FEATURE_NAMES.

    Returns
    -------
    pd.DataFrame
        Index = price_df.index. Columns = EARNINGS_FEATURE_NAMES.
        Values are 0 when no earnings data; otherwise leakage-proof (only use report
        on/after effective_date).
    """
    out = pd.DataFrame(index=price_df.index)
    out.index = pd.to_datetime(out.index)
    for c in EARNINGS_FEATURE_NAMES:
        out[c] = 0.0

    if earnings_df is None or earnings_df.empty:
        return out[EARNINGS_FEATURE_NAMES]

    if EARNINGS_COL_EFFECTIVE_DATE not in earnings_df.columns or EARNINGS_COL_EPS_SURPRISE_PCT not in earnings_df.columns:
        return out[EARNINGS_FEATURE_NAMES]

    edf = earnings_df[[EARNINGS_COL_EFFECTIVE_DATE, EARNINGS_COL_EPS_SURPRISE_PCT]].copy()
    edf = edf.sort_values(EARNINGS_COL_EFFECTIVE_DATE)
    edf[EARNINGS_COL_EFFECTIVE_DATE] = pd.to_datetime(edf[EARNINGS_COL_EFFECTIVE_DATE])

    # Align to price dates: for each bar we only know the most recent report on or before that date
    price_dates = price_df.index.to_series()
    if price_dates.dt.tz is not None and edf[EARNINGS_COL_EFFECTIVE_DATE].dt.tz is None:
        edf[EARNINGS_COL_EFFECTIVE_DATE] = edf[EARNINGS_COL_EFFECTIVE_DATE].dt.tz_localize(price_dates.dt.tz, ambiguous="NaT")
    elif price_dates.dt.tz is None and edf[EARNINGS_COL_EFFECTIVE_DATE].dt.tz is not None:
        edf[EARNINGS_COL_EFFECTIVE_DATE] = edf[EARNINGS_COL_EFFECTIVE_DATE].dt.tz_localize(None)

    edf_renamed = edf.rename(columns={EARNINGS_COL_EFFECTIVE_DATE: "report_date", EARNINGS_COL_EPS_SURPRISE_PCT: "eps_surprise_pct"})
    sorted_idx = price_df.index.sort_values()
    left = pd.DataFrame({"trade_date": sorted_idx}, index=sorted_idx)
    merged = pd.merge_asof(
        left,
        edf_renamed,
        left_on="trade_date",
        right_on="report_date",
        direction="backward",
    )
    merged = merged.reindex(price_df.index)

    out["eps_surprise_pct"] = merged["eps_surprise_pct"].fillna(0.0).values
    report_dt = pd.to_datetime(merged["report_date"], errors="coerce")
    td = merged.index - report_dt
    if hasattr(td, "dt"):
        days_val = td.dt.days
    else:
        days_val = np.array([getattr(x, "days", 0) if pd.notna(x) else 0 for x in td])
    out["days_since_earnings"] = np.clip(days_val, 0, None)
    # Decay: surprise * exp(-days / half_life)
    out["surprise_decay"] = out["eps_surprise_pct"] * np.exp(-out["days_since_earnings"] / _SURPRISE_HALFLIFE_DAYS)

    return out[EARNINGS_FEATURE_NAMES]
