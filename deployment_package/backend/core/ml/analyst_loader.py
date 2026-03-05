"""
analyst_loader.py
=================
Fetches analyst recommendation and revision data from Finnhub for ML features.
Used for analyst_rev_1m, rec_upgrade_score, fy1_rev_3m (estimate revision momentum).

Finnhub: GET /stock/recommendation (aggregate buy/hold/sell), 60 calls/min free.
Optional: /stock/upgrade-downgrade for revision history.

If FINNHUB_API_KEY is unset or API fails, returns None so the pipeline uses zeros.
"""

from __future__ import annotations

import logging
import os
from typing import Optional

import pandas as pd
import requests

logger = logging.getLogger(__name__)

BASE_URL = "https://finnhub.io/api/v1"

# Column names for downstream analyst_features
REC_COL_DATE = "period"
REC_COL_BUY = "strongBuy"
REC_COL_HOLD = "hold"
REC_COL_SELL = "sell"


def fetch_recommendation(ticker: str, api_key: Optional[str] = None) -> Optional[pd.DataFrame]:
    """
    Fetch analyst recommendation trend (buy/hold/sell counts by period).

    Finnhub /stock/recommendation returns weekly buckets. We derive:
    - rec_upgrade_score: (buy - sell) / total, normalised to [-1, 1]
    - analyst_rev_1m: placeholder (would need estimate revision API)
    - fy1_rev_3m: placeholder (would need estimate revision API)

    Returns
    -------
    pd.DataFrame with columns period (date), strongBuy, hold, sell, rec_score,
    or None if no key / request fails.
    """
    key = api_key or os.getenv("FINNHUB_API_KEY")
    if not key:
        logger.debug("No FINNHUB_API_KEY — skipping analyst recommendation for %s", ticker)
        return None

    url = f"{BASE_URL}/stock/recommendation"
    params = {"symbol": ticker.upper(), "token": key}
    try:
        resp = requests.get(url, params=params, timeout=15)
        resp.raise_for_status()
        data = resp.json()
    except Exception as e:
        logger.debug("Analyst recommendation fetch failed for %s: %s", ticker, e)
        return None

    if not isinstance(data, list) or not data:
        return None

    rows = []
    for r in data:
        period = r.get("period")
        buy = int(r.get("strongBuy", 0) or 0) + int(r.get("buy", 0) or 0)
        hold = int(r.get("hold", 0) or 0)
        sell = int(r.get("sell", 0) or 0) + int(r.get("strongSell", 0) or 0)
        total = buy + hold + sell
        rec_score = (buy - sell) / total if total else 0.0
        rows.append({
            REC_COL_DATE: period,
            "rec_score": rec_score,
            "buy": buy,
            "hold": hold,
            "sell": sell,
        })
    df = pd.DataFrame(rows)
    df[REC_COL_DATE] = pd.to_datetime(df[REC_COL_DATE], errors="coerce")
    df = df.dropna(subset=[REC_COL_DATE]).sort_values(REC_COL_DATE)
    return df if not df.empty else None
