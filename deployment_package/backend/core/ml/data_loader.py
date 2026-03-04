"""
data_loader.py
==============
Fetches adjusted daily OHLCV data via yfinance and attaches SPY/QQQ
as market-context columns.  All data is split/dividend-adjusted.

Design rules
------------
* Every row has an "as-of" timestamp (the trading date).
* Market-context columns (spy_close, spy_volume, qqq_close) are added so
  features.py can compute cross-asset signals without a separate fetch.
* Returns only rows where BOTH the ticker AND SPY have non-null closes,
  preventing silent NaN leakage downstream.
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import Dict

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

# Minimum rows required before we consider a ticker usable
_MIN_ROWS = 100

# Market context tickers always fetched alongside the target
_CONTEXT_TICKERS = ["SPY", "QQQ"]

# Sector ETFs for rotation context (tech, financials, energy, healthcare, consumer disc, staples)
_SECTOR_ETFS = ["XLK", "XLF", "XLE", "XLV", "XLY", "XLP"]


class DataLoader:
    """Fetch adjusted OHLCV for a list of tickers using yfinance."""

    def fetch(
        self,
        tickers: list[str],
        start_date: str = "2019-01-01",
        end_date: str | None = None,
    ) -> Dict[str, pd.DataFrame]:
        """
        Fetch adjusted daily OHLCV for each ticker in *tickers*.

        Parameters
        ----------
        tickers : list[str]
            Target tickers to model (e.g. ["AAPL", "MSFT"]).
        start_date : str
            ISO date string for the start of the history window.
        end_date : str | None
            ISO date string for the end. Defaults to today.

        Returns
        -------
        dict[str, pd.DataFrame]
            Keyed by ticker symbol.  Each DataFrame has columns:
              open, high, low, close, volume,
              spy_close, spy_volume, qqq_close
            Index: DatetimeIndex (UTC midnight, trading days only).
        """
        try:
            import yfinance as yf
        except ImportError as exc:
            raise ImportError("yfinance is required: pip install yfinance>=0.2.0") from exc

        end_date = end_date or datetime.utcnow().strftime("%Y-%m-%d")

        all_tickers = list(dict.fromkeys(tickers + _CONTEXT_TICKERS + _SECTOR_ETFS))  # deduplicate, preserve order

        logger.info("Fetching %d tickers from %s to %s", len(all_tickers), start_date, end_date)

        # Batch download is much faster than per-ticker calls
        raw = yf.download(
            tickers=all_tickers,
            start=start_date,
            end=end_date,
            auto_adjust=True,       # adjusts for splits + dividends
            progress=False,
            threads=True,
        )

        if raw.empty:
            raise ValueError(f"yfinance returned no data for {all_tickers}")

        # yfinance returns a MultiIndex columns df when multiple tickers are requested
        # Normalise to {ticker: single-level-df}
        dfs = self._split_by_ticker(raw, all_tickers)

        # Build context columns from SPY / QQQ and sector ETFs
        spy_df = dfs.get("SPY")
        qqq_df = dfs.get("QQQ")
        sector_dfs = {etf: dfs.get(etf) for etf in _SECTOR_ETFS}

        results: Dict[str, pd.DataFrame] = {}
        for ticker in tickers:
            if ticker not in dfs:
                logger.warning("No data returned for %s — skipping", ticker)
                continue

            df = dfs[ticker].copy()
            df.columns = [c.lower() for c in df.columns]  # normalise column names

            # Attach market context
            if spy_df is not None:
                df["spy_close"] = spy_df["Close"].reindex(df.index)
                df["spy_volume"] = spy_df["Volume"].reindex(df.index)
            else:
                df["spy_close"] = np.nan
                df["spy_volume"] = np.nan

            if qqq_df is not None:
                df["qqq_close"] = qqq_df["Close"].reindex(df.index)
            else:
                df["qqq_close"] = np.nan

            # Sector ETF closes for rotation context
            for etf in _SECTOR_ETFS:
                sec_df = sector_dfs.get(etf)
                col = f"{etf.lower()}_close"
                if sec_df is not None and "Close" in sec_df.columns:
                    df[col] = sec_df["Close"].reindex(df.index)
                else:
                    df[col] = np.nan

            # Keep only rows where both ticker close and SPY close are valid
            df = df.dropna(subset=["close", "spy_close"])

            if len(df) < _MIN_ROWS:
                logger.warning(
                    "%s: only %d valid rows after alignment (need %d) — skipping",
                    ticker, len(df), _MIN_ROWS,
                )
                continue

            results[ticker] = df
            logger.debug("%s: %d rows loaded (%s → %s)", ticker, len(df), df.index[0].date(), df.index[-1].date())

        if not results:
            raise ValueError("No tickers had sufficient data. Check ticker symbols and date range.")

        logger.info("DataLoader: loaded %d/%d tickers successfully", len(results), len(tickers))
        return results

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _split_by_ticker(raw: pd.DataFrame, tickers: list[str]) -> Dict[str, pd.DataFrame]:
        """Split a multi-ticker yfinance DataFrame into per-ticker DataFrames."""
        if isinstance(raw.columns, pd.MultiIndex):
            result = {}
            for ticker in tickers:
                try:
                    df = raw.xs(ticker, axis=1, level=1).copy()
                    df = df.dropna(how="all")
                    if not df.empty:
                        result[ticker] = df
                except KeyError:
                    logger.debug("Ticker %s not found in downloaded data", ticker)
            return result
        else:
            # Single ticker — yfinance returns flat columns
            assert len(tickers) == 1
            return {tickers[0]: raw.copy()}
