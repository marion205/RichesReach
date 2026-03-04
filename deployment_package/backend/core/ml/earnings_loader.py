"""
earnings_loader.py
==================
Fetches historical earnings with surprise from Polygon.io (Massive) Benzinga
partner endpoint. Used by the ML pipeline to add earnings_surprise and PEAD signals.

Requires POLYGON_API_KEY (or MASSIVE_API_KEY). If unset or API unavailable,
returns None so the pipeline runs with technical features only.

Endpoint (Polygon/Massive): Benzinga Earnings
  https://api.polygon.io/v3/reference/partners/benzinga/earnings
  Fields: actual_eps, estimated_eps, eps_surprise_percent, date, time, etc.
"""

from __future__ import annotations

import logging
import os
from typing import Optional

import pandas as pd
import requests

logger = logging.getLogger(__name__)

# Canonical column names for downstream earnings_features
EARNINGS_COL_EFFECTIVE_DATE = "effective_date"
EARNINGS_COL_EPS_SURPRISE_PCT = "eps_surprise_pct"
EARNINGS_COL_REVENUE_SURPRISE_PCT = "revenue_surprise_pct"

_BASE_URL = "https://api.polygon.io"
_EARNINGS_PATH = "/v3/reference/partners/benzinga/earnings"


def fetch_earnings(
    ticker: str,
    start_date: str,
    end_date: str,
    api_key: Optional[str] = None,
) -> Optional[pd.DataFrame]:
    """
    Fetch historical earnings with surprise for one ticker.

    Parameters
    ----------
    ticker : str
        Stock symbol (e.g. AAPL).
    start_date : str
        ISO date (YYYY-MM-DD).
    end_date : str
        ISO date (YYYY-MM-DD).
    api_key : str, optional
        Polygon/Massive API key. Defaults to POLYGON_API_KEY or MASSIVE_API_KEY env.

    Returns
    -------
    pd.DataFrame or None
        Columns: effective_date, eps_surprise_pct, revenue_surprise_pct (if available).
        effective_date is the first tradeable date after the report (anti-leakage).
        None if no key, request fails, or no data.
    """
    key = api_key or os.getenv("POLYGON_API_KEY") or os.getenv("MASSIVE_API_KEY")
    if not key:
        logger.debug("No POLYGON_API_KEY / MASSIVE_API_KEY — skipping earnings fetch for %s", ticker)
        return None

    url = _BASE_URL + _EARNINGS_PATH
    params = {
        "ticker": ticker,
        "date.gte": start_date,
        "date.lte": end_date,
        "limit": 250,
        "apiKey": key,
    }

    try:
        resp = requests.get(url, params=params, timeout=15)
        resp.raise_for_status()
        data = resp.json()
    except Exception as e:
        logger.debug("Earnings fetch failed for %s: %s", ticker, e)
        return None

    results = data.get("results") if isinstance(data, dict) else None
    if not results:
        return None

    rows = []
    for r in results:
        # Report timestamp: date + time (e.g. "Before Market Open" vs "After Market Close")
        report_date = r.get("date")
        report_time = r.get("time") or "00:00:00"
        if not report_date:
            continue
        try:
            report_dt = pd.to_datetime(f"{report_date} {report_time}", utc=True)
        except Exception:
            report_dt = pd.to_datetime(report_date, utc=True)

        # Effective date: first tradeable bar. If report after ~9:30 ET, next calendar day.
        # Simplified: if hour >= 16 (4 PM) treat as next day; else same day.
        if report_dt.hour >= 16:
            effective = (report_dt + pd.Timedelta(days=1)).date()
        else:
            effective = report_dt.date()

        # Surprise: prefer pre-calculated; fallback to (actual - est) / |est|
        eps_surprise_pct = r.get("eps_surprise_percent")
        if eps_surprise_pct is None and r.get("actual_eps") is not None and r.get("estimated_eps") is not None:
            est = float(r["estimated_eps"])
            act = float(r["actual_eps"])
            if est != 0:
                eps_surprise_pct = 100.0 * (act - est) / abs(est)
            else:
                eps_surprise_pct = 0.0

        rev_surprise_pct = r.get("revenue_surprise_percent")

        rows.append({
            EARNINGS_COL_EFFECTIVE_DATE: effective,
            EARNINGS_COL_EPS_SURPRISE_PCT: eps_surprise_pct if eps_surprise_pct is not None else float("nan"),
            EARNINGS_COL_REVENUE_SURPRISE_PCT: rev_surprise_pct if rev_surprise_pct is not None else float("nan"),
        })

    if not rows:
        return None

    df = pd.DataFrame(rows)
    df[EARNINGS_COL_EFFECTIVE_DATE] = pd.to_datetime(df[EARNINGS_COL_EFFECTIVE_DATE])
    df = df.sort_values(EARNINGS_COL_EFFECTIVE_DATE).drop_duplicates(subset=[EARNINGS_COL_EFFECTIVE_DATE], keep="last")
    return df
