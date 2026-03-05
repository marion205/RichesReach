"""
earnings_loader.py
==================
Fetches historical earnings with EPS surprise from Alpha Vantage.
Used by the ML pipeline to add PEAD (Post-Earnings Announcement Drift) features.

Requires ALPHAVANTAGE_API_KEY env var.  If unset or API unavailable,
returns None so the pipeline gracefully falls back to technical features only.

Alpha Vantage EARNINGS endpoint:
  https://www.alphavantage.co/query?function=EARNINGS&symbol=AAPL
  Returns quarterly history with reportedEPS, estimatedEPS, surprisePercentage, reportTime.
  Up to 120 quarters (~30 years) of history per ticker.

Rate limits:
  Free tier: 25 requests/day.  With 78 tickers this requires either:
    - A premium key (500+ req/day), or
    - A local cache (see _CACHE_DIR below) to avoid re-fetching on retrain.
  If the rate limit is hit, the ticker gets zeros for earnings features
  (the pipeline continues uninterrupted).
"""

from __future__ import annotations

import json
import logging
import os
import time
from pathlib import Path
from typing import Optional

import pandas as pd
import requests

logger = logging.getLogger(__name__)

# Canonical column names for downstream earnings_features
EARNINGS_COL_EFFECTIVE_DATE = "effective_date"
EARNINGS_COL_EPS_SURPRISE_PCT = "eps_surprise_pct"
EARNINGS_COL_REVENUE_SURPRISE_PCT = "revenue_surprise_pct"  # AV doesn't provide this; kept for schema compat

_BASE_URL = "https://www.alphavantage.co/query"

# Local on-disk cache: avoids re-fetching on every training run (25 req/day limit)
_CACHE_DIR = Path(__file__).parent.parent.parent.parent / "ml_models" / "earnings_cache"


def fetch_earnings(
    ticker: str,
    start_date: str,
    end_date: str,
    api_key: Optional[str] = None,
    use_cache: bool = True,
    sleep_between_requests: float = 0.0,
) -> Optional[pd.DataFrame]:
    """
    Fetch historical quarterly earnings with EPS surprise for one ticker.

    Parameters
    ----------
    ticker : str
        Stock symbol (e.g. AAPL).
    start_date : str
        ISO date (YYYY-MM-DD). Used to filter results.
    end_date : str
        ISO date (YYYY-MM-DD). Used to filter results.
    api_key : str, optional
        Alpha Vantage API key. Defaults to ALPHAVANTAGE_API_KEY env var.
    use_cache : bool
        If True, cache results to disk so repeated training runs don't hit API.
    sleep_between_requests : float
        Seconds to sleep after each API call (rate-limit courtesy delay).

    Returns
    -------
    pd.DataFrame or None
        Columns: effective_date (DatetimeIndex), eps_surprise_pct, revenue_surprise_pct.
        effective_date = next trading day after report if after-market; same day if pre-market.
        None if no key, request fails, rate limited, or no data for ticker.
    """
    key = api_key or os.getenv("ALPHAVANTAGE_API_KEY") or os.getenv("ALPHA_VANTAGE_KEY")
    if not key:
        logger.debug("No ALPHAVANTAGE_API_KEY — skipping earnings fetch for %s", ticker)
        return None

    # Check cache first
    if use_cache:
        cached = _load_from_cache(ticker)
        if cached is not None:
            return _filter_date_range(cached, start_date, end_date)

    params = {
        "function": "EARNINGS",
        "symbol": ticker,
        "apikey": key,
    }

    try:
        resp = requests.get(_BASE_URL, params=params, timeout=20)
        resp.raise_for_status()
        data = resp.json()
    except Exception as e:
        logger.debug("Earnings fetch failed for %s: %s", ticker, e)
        return None

    if sleep_between_requests > 0:
        time.sleep(sleep_between_requests)

    # Alpha Vantage rate-limit response (redact so API key never appears in logs)
    if "Note" in data or "Information" in data:
        msg = data.get("Note") or data.get("Information", "")
        try:
            from ..security_utils import redact_secrets_for_log
            msg = redact_secrets_for_log(msg)
        except Exception:
            msg = msg[:80].replace("API key as", "API key [REDACTED]")
        logger.warning("Alpha Vantage rate limit hit for %s: %s", ticker, (msg[:80] if len(msg) > 80 else msg))
        return None

    quarterly = data.get("quarterlyEarnings", [])
    if not quarterly:
        logger.debug("No quarterly earnings data for %s", ticker)
        return None

    rows = []
    for r in quarterly:
        reported_date_str = r.get("reportedDate")
        report_time = r.get("reportTime", "").lower()   # "pre-market" / "post-market"
        surprise_pct = r.get("surprisePercentage")

        if not reported_date_str or surprise_pct is None or surprise_pct == "None":
            continue

        try:
            reported_dt = pd.to_datetime(reported_date_str)
        except Exception:
            continue

        try:
            surprise_val = float(surprise_pct)
        except (ValueError, TypeError):
            continue

        # Leakage-proof effective date:
        # - Pre-market / Before Market Open: investors can trade on this info same day
        # - Post-market / After Market Close: info not tradeable until next open
        # We add 1 day for post-market reports; same day for pre-market.
        if "post" in report_time or "after" in report_time:
            effective = reported_dt + pd.Timedelta(days=1)
        else:
            effective = reported_dt

        rows.append({
            EARNINGS_COL_EFFECTIVE_DATE: effective,
            EARNINGS_COL_EPS_SURPRISE_PCT: surprise_val,
            EARNINGS_COL_REVENUE_SURPRISE_PCT: float("nan"),  # AV free tier doesn't provide revenue surprise
        })

    if not rows:
        return None

    df = pd.DataFrame(rows)
    df[EARNINGS_COL_EFFECTIVE_DATE] = pd.to_datetime(df[EARNINGS_COL_EFFECTIVE_DATE]).dt.tz_localize(None)
    df = df.sort_values(EARNINGS_COL_EFFECTIVE_DATE).drop_duplicates(
        subset=[EARNINGS_COL_EFFECTIVE_DATE], keep="last"
    )

    # Save to cache for future runs
    if use_cache:
        _save_to_cache(ticker, df)

    return _filter_date_range(df, start_date, end_date)


def _filter_date_range(df: pd.DataFrame, start_date: str, end_date: str) -> Optional[pd.DataFrame]:
    """Return only rows where effective_date falls within [start_date, end_date]."""
    if df is None or df.empty:
        return None
    mask = (
        (df[EARNINGS_COL_EFFECTIVE_DATE] >= pd.to_datetime(start_date)) &
        (df[EARNINGS_COL_EFFECTIVE_DATE] <= pd.to_datetime(end_date))
    )
    filtered = df[mask]
    return filtered if not filtered.empty else None


def _cache_path(ticker: str) -> Path:
    _CACHE_DIR.mkdir(parents=True, exist_ok=True)
    return _CACHE_DIR / f"{ticker.upper()}_earnings.json"


def get_cached_tickers() -> set[str]:
    """Return set of ticker symbols that have a valid earnings cache file."""
    if not _CACHE_DIR.exists():
        return set()
    out = set()
    for path in _CACHE_DIR.glob("*_earnings.json"):
        out.add(path.stem.replace("_earnings", "").upper())
    return out


def run_earnings_sprint(
    tickers: list[str],
    max_per_run: int = 25,
    start_date: str = "2010-01-01",
    end_date: str = "2026-12-31",
    use_cache: bool = True,
    sleep_between_requests: float = 12.0,
) -> dict:
    """
    Fetch earnings for up to max_per_run tickers that are not yet cached.
    Designed for Alpha Vantage free tier: 25 requests/day, 5 requests/minute.

    Parameters
    ----------
    tickers : list[str]
        Full universe (e.g. train.DEFAULT_TICKERS).
    max_per_run : int
        Max API calls per run (default 25 for free tier).
    start_date, end_date : str
        Date range for filtering; cache stores full history.
    use_cache : bool
        If True, skip already-cached tickers and write new results to cache.
    sleep_between_requests : float
        Seconds between API calls (default 12 = 5 req/min for free tier).

    Returns
    -------
    dict
        {"fetched": N, "ok": n_ok, "failed": n_failed, "remaining": M, "cached_total": C}
    """
    cached = get_cached_tickers()
    uncached = [t for t in tickers if t.upper() not in cached]
    to_fetch = uncached[:max_per_run]
    if not to_fetch:
        return {
            "fetched": 0,
            "ok": 0,
            "failed": 0,
            "remaining": 0,
            "cached_total": len(cached),
        }

    ok = 0
    failed = 0
    for i, ticker in enumerate(to_fetch):
        df = fetch_earnings(
            ticker,
            start_date,
            end_date,
            use_cache=use_cache,
            sleep_between_requests=sleep_between_requests,
        )
        if df is not None and not df.empty:
            ok += 1
        else:
            failed += 1

    return {
        "fetched": len(to_fetch),
        "ok": ok,
        "failed": failed,
        "remaining": len(uncached) - len(to_fetch),
        "cached_total": len(cached) + ok,
    }


def _load_from_cache(ticker: str) -> Optional[pd.DataFrame]:
    path = _cache_path(ticker)
    if not path.exists():
        return None
    try:
        with open(path) as f:
            records = json.load(f)
        df = pd.DataFrame(records)
        df[EARNINGS_COL_EFFECTIVE_DATE] = pd.to_datetime(df[EARNINGS_COL_EFFECTIVE_DATE])
        logger.debug("Earnings cache hit for %s (%d records)", ticker, len(df))
        return df
    except Exception as e:
        logger.debug("Cache read failed for %s: %s", ticker, e)
        return None


def _save_to_cache(ticker: str, df: pd.DataFrame) -> None:
    path = _cache_path(ticker)
    try:
        records = df.copy()
        records[EARNINGS_COL_EFFECTIVE_DATE] = records[EARNINGS_COL_EFFECTIVE_DATE].astype(str)
        with open(path, "w") as f:
            json.dump(records.to_dict(orient="records"), f)
        logger.debug("Earnings cached for %s → %s", ticker, path)
    except Exception as e:
        logger.debug("Cache write failed for %s: %s", ticker, e)


# ---------------------------------------------------------------------------
# CLI: run as python -m deployment_package.backend.core.ml.earnings_loader
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    import argparse
    from .train import DEFAULT_TICKERS

    parser = argparse.ArgumentParser(
        description="Alpha Vantage earnings sprint: fetch up to N tickers/day, persist to cache."
    )
    parser.add_argument(
        "--max",
        type=int,
        default=25,
        help="Max API requests this run (default 25 for free tier).",
    )
    parser.add_argument("--start", type=str, default="2010-01-01", help="Start date for filter.")
    parser.add_argument("--end", type=str, default="2026-12-31", help="End date for filter.")
    parser.add_argument(
        "--sleep",
        type=float,
        default=12.0,
        help="Seconds between API calls (default 12 = 5 req/min free tier).",
    )
    parser.add_argument(
        "tickers",
        nargs="*",
        default=None,
        help="Tickers to fetch (default: training universe).",
    )
    args = parser.parse_args()
    tickers = args.tickers or DEFAULT_TICKERS

    logging.basicConfig(level=logging.INFO, format="%(message)s")
    if not os.getenv("ALPHAVANTAGE_API_KEY") and not os.getenv("ALPHA_VANTAGE_KEY"):
        print("Set ALPHAVANTAGE_API_KEY (or ALPHA_VANTAGE_KEY) and re-run.")
        raise SystemExit(1)

    result = run_earnings_sprint(
        tickers,
        max_per_run=args.max,
        start_date=args.start,
        end_date=args.end,
        use_cache=True,
        sleep_between_requests=args.sleep,
    )
    print(
        f"Earnings sprint: fetched {result['fetched']} (ok={result['ok']}, failed={result['failed']}). "
        f"Cached total: {result['cached_total']}. Remaining: {result['remaining']}."
    )
    if result["remaining"] > 0:
        print("Run again tomorrow for the next batch (25/day on free tier).")
    else:
        print("Full universe cached. You can retrain with earnings coverage.")
