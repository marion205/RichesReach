"""
features.py
===========
Strictly causal feature engineering for the production ML pipeline.

Every feature uses ONLY data available at time t (past/current prices,
volumes, and market context).  No look-ahead, no shift(-n) on inputs.

Feature groups
--------------
Momentum (3)   : log-returns over 21d, 63d, 126d windows
Trend (3)      : distance from 50/200-day SMA, ADX-14
Volatility (3) : realised vol 20d/60d, ATR% 14d
Volume/Flow (3): windowed VPT, windowed OBV, volume z-score 20d
Cross-asset (4): SPY 21d return, SPY vol 20d, QQQ 21d return, vix_proxy
Alpha (5)      : short-term reversal (1w), 52-week high proximity,
                 idiosyncratic vol, return skewness 20d, vol ratio (5d/60d)

NOTE on sector ETF features (removed):
  Raw sector ETF momentum (e.g. xlk_mom_21d) is constant across ALL tickers
  on a given date — after XS z-scoring (which normalises within each date's
  cross-section) a constant-valued feature collapses to 0 for every row.
  It adds zero signal but consumes model capacity and regularisation budget.
  The correct sector-relative signal would be stock_mom - sector_mom, but
  that requires a sector mapping table per ticker, which is not yet available.
  Removed until a per-ticker sector assignment is implemented.

Total: 21 named features — no padding zeros, no ESG, no user-profile.

Naming convention: all lowercase with underscores, units in the name
where non-obvious (e.g. atr_pct, rvol_20d).
"""

from __future__ import annotations

import logging

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

# Canonical list of feature names produced by build_features().
# model_registry.py saves this alongside the model so we can enforce
# the same feature schema at inference time.
FEATURE_NAMES: list[str] = [
    # Momentum
    "mom_21d",
    "mom_63d",
    "mom_126d",
    # Trend
    "dist_sma_50",
    "dist_sma_200",
    "adx_14",
    # Volatility
    "rvol_20d",
    "rvol_60d",
    "atr_pct",
    # Volume / Flow
    "vpt_zscore",
    "obv_zscore",
    "vol_zscore_20d",
    # Cross-asset
    "spy_mom_21d",
    "spy_rvol_20d",
    "qqq_mom_21d",
    "vix_proxy",
    # Alpha
    "rev_1w",          # short-term 1-week reversal (contrarian signal)
    "high_52w_prox",   # proximity to 52-week high (momentum continuation)
    "idio_vol",        # idiosyncratic vol: residual after removing SPY beta
    "ret_skew_20d",    # 20-day return skewness (crash risk / positive skew)
    "vol_ratio",       # rvol_5d / rvol_60d (vol regime: expanding vs contracting)
]


def build_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Build the canonical feature matrix from a single-ticker OHLCV DataFrame.

    Parameters
    ----------
    df : pd.DataFrame
        Must contain columns: open, high, low, close, volume
        Optional (added by DataLoader): spy_close, spy_volume, qqq_close
        Index: DatetimeIndex

    Returns
    -------
    pd.DataFrame
        Columns: exactly FEATURE_NAMES, same DatetimeIndex as input.
        Rows with insufficient history (warm-up period) are NaN — callers
        should dropna() or align with the target series which already drops NaN.
    """
    _validate_input(df)

    feat = pd.DataFrame(index=df.index)

    close = df["close"]
    high = df["high"]
    low = df["low"]
    volume = df["volume"].replace(0, np.nan)  # 0-volume days → NaN, not division by zero

    # ------------------------------------------------------------------
    # Momentum: log-returns over multiple horizons
    # log(P_t / P_{t-w}) uses only past prices — strictly causal
    # ------------------------------------------------------------------
    for w, name in [(21, "mom_21d"), (63, "mom_63d"), (126, "mom_126d")]:
        feat[name] = np.log(close / close.shift(w))

    # ------------------------------------------------------------------
    # Trend: distance from moving averages
    # SMA is computed on past closes only; dist = (close / SMA) - 1
    # ------------------------------------------------------------------
    feat["dist_sma_50"] = close / close.rolling(50).mean() - 1.0
    feat["dist_sma_200"] = close / close.rolling(200).mean() - 1.0

    # ADX-14 (Wilder's directional movement)
    feat["adx_14"] = _compute_adx(high, low, close, period=14)

    # ------------------------------------------------------------------
    # Volatility
    # ------------------------------------------------------------------
    daily_log_ret = np.log(close / close.shift(1))

    # Realised vol (annualised)
    feat["rvol_20d"] = daily_log_ret.rolling(20, min_periods=10).std() * np.sqrt(252)
    feat["rvol_60d"] = daily_log_ret.rolling(60, min_periods=20).std() * np.sqrt(252)

    # ATR% = Average True Range / close (normalises by price level)
    tr = _true_range(high, low, close)
    atr = tr.rolling(14, min_periods=5).mean()
    feat["atr_pct"] = atr / close

    # ------------------------------------------------------------------
    # Volume / Flow
    # Note: cumulative VPT and OBV are path-dependent and non-stationary
    # across tickers — their absolute levels are incomparable between a
    # $5B stock and a $500B stock.  We use short-window versions instead:
    #
    # vpt_20d  : 20-day rolling sum of (daily_log_ret * volume_ratio)
    #            measures recent institutional participation, not cumulative
    # obv_slope: slope of 10-day OBV, capturing *direction* of smart money flow
    # vol_zscore: dollar-volume vs 20-day average (event detection)
    # ------------------------------------------------------------------

    # VPT-20: recent price-weighted volume flow (stationary, comparable cross-sectionally)
    vol_avg_20 = volume.rolling(20, min_periods=5).mean().replace(0, np.nan)
    vol_norm_ratio = volume / vol_avg_20  # normalise by average to be comparable across stocks
    vpt_20 = (daily_log_ret * vol_norm_ratio).rolling(20, min_periods=10).sum()
    feat["vpt_zscore"] = vpt_20  # XS z-score applied in train.py; raw signal here is fine

    # OBV slope: linear trend of 10-day OBV direction (positive = accumulation)
    direction = np.sign(daily_log_ret).fillna(0)
    obv_10 = (direction * vol_norm_ratio).rolling(10, min_periods=5).sum()
    feat["obv_zscore"] = obv_10  # same — XS z-score applied at training time

    # Volume z-score: how unusual is today's dollar-volume vs 20-day average?
    dollar_vol = close * volume
    vol_mean = dollar_vol.rolling(20, min_periods=10).mean()
    vol_std = dollar_vol.rolling(20, min_periods=10).std().replace(0, np.nan)
    feat["vol_zscore_20d"] = (dollar_vol - vol_mean) / vol_std

    # ------------------------------------------------------------------
    # Cross-asset context (SPY, QQQ, VIX proxy)
    # These use the spy_close / qqq_close columns added by DataLoader
    # ------------------------------------------------------------------
    spy_close = df.get("spy_close")
    qqq_close = df.get("qqq_close")

    if spy_close is not None and spy_close.notna().sum() > 30:
        spy_log_ret = np.log(spy_close / spy_close.shift(1))
        feat["spy_mom_21d"] = np.log(spy_close / spy_close.shift(21))
        feat["spy_rvol_20d"] = spy_log_ret.rolling(20, min_periods=10).std() * np.sqrt(252)
        # VIX proxy: 20D SPY realised vol scaled to "VIX-like" 0-100 units
        feat["vix_proxy"] = feat["spy_rvol_20d"] * 100.0
    else:
        feat["spy_mom_21d"] = np.nan
        feat["spy_rvol_20d"] = np.nan
        feat["vix_proxy"] = np.nan

    if qqq_close is not None and qqq_close.notna().sum() > 30:
        feat["qqq_mom_21d"] = np.log(qqq_close / qqq_close.shift(21))
    else:
        feat["qqq_mom_21d"] = np.nan

    # ------------------------------------------------------------------
    # Alpha signals — high-information features that capture stock-specific
    # behaviour not explained by market or sector beta
    # ------------------------------------------------------------------

    # 1. Short-term reversal (1-week = 5 trading days)
    #    Stocks with strong 1-week gains tend to mean-revert over the next
    #    20 days (market microstructure + short-term overreaction).
    #    Negative sign: we SELL the last week's gain as a predictor of reversal.
    #    Causal: log(P_t / P_{t-5}) uses only past prices.
    feat["rev_1w"] = -np.log(close / close.shift(5))

    # 2. 52-week high proximity
    #    Distance of today's close from the trailing 252-day high.
    #    Values in (-∞, 0]: 0 means AT the 52-week high.
    #    Stocks near 52-week highs show momentum continuation (George & Hwang 2004).
    #    Causal: rolling max over past 252 closes only.
    rolling_max_252 = close.rolling(252, min_periods=126).max()
    feat["high_52w_prox"] = np.log(close / rolling_max_252)

    # 3. Idiosyncratic volatility (residual vol after removing SPY market beta)
    #    Captures stock-specific risk not priced by the market factor.
    #    High idio_vol stocks tend to underperform (Ang et al. 2006) — useful
    #    as a negative predictor or risk control.
    #    Method: rolling 60-day OLS beta → idio_ret = ret - beta * spy_ret
    #            idio_vol = std(idio_ret) over 20 days
    if spy_close is not None and spy_close.notna().sum() > 60:
        spy_log_ret_for_beta = np.log(spy_close / spy_close.shift(1))
        feat["idio_vol"] = _idio_vol(daily_log_ret, spy_log_ret_for_beta, window=60)
    else:
        # Fallback: use rvol_20d when SPY data unavailable
        feat["idio_vol"] = feat["rvol_20d"]

    # 4. Return skewness over 20 days
    #    Positive skew → occasional large up-moves → lottery-like stock.
    #    Negative skew → crash risk.
    #    Empirically: high positive-skew stocks are overpriced (investors love lotteries)
    #    and tend to underperform — useful contrarian signal.
    #    Causal: computed from past 20 daily log-returns only.
    feat["ret_skew_20d"] = daily_log_ret.rolling(20, min_periods=10).skew()

    # 5. Volatility ratio: short-term vol / long-term vol
    #    > 1: vol is expanding (regime change, event risk, earnings)
    #    < 1: vol is contracting (quiet trending market)
    #    Normalised: we divide by rvol_60d so the signal is scale-free.
    rvol_5d = daily_log_ret.rolling(5, min_periods=3).std() * np.sqrt(252)
    rvol_60d_raw = daily_log_ret.rolling(60, min_periods=20).std() * np.sqrt(252)
    feat["vol_ratio"] = rvol_5d / rvol_60d_raw.replace(0, np.nan)

    # ------------------------------------------------------------------
    # Final validation: ensure column order matches FEATURE_NAMES exactly
    # ------------------------------------------------------------------
    feat = feat[FEATURE_NAMES]

    # Forward-fill at most 5 consecutive NaNs (e.g. holidays, halts)
    # then leave remaining NaN for the caller to handle
    feat = feat.ffill(limit=5)

    logger.debug(
        "build_features: %d rows, %d features, %.1f%% non-null",
        len(feat), len(feat.columns),
        feat.notna().values.mean() * 100,
    )

    return feat


# ---------------------------------------------------------------------------
# Private helpers
# ---------------------------------------------------------------------------

def _validate_input(df: pd.DataFrame) -> None:
    required = {"open", "high", "low", "close", "volume"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"build_features: missing required columns: {missing}")
    if not isinstance(df.index, pd.DatetimeIndex):
        raise ValueError("build_features: DataFrame must have a DatetimeIndex")


def _true_range(high: pd.Series, low: pd.Series, close: pd.Series) -> pd.Series:
    """Wilder's True Range."""
    prev_close = close.shift(1)
    tr = pd.concat([
        high - low,
        (high - prev_close).abs(),
        (low - prev_close).abs(),
    ], axis=1).max(axis=1)
    return tr


def _compute_adx(
    high: pd.Series,
    low: pd.Series,
    close: pd.Series,
    period: int = 14,
) -> pd.Series:
    """
    Wilder's Average Directional Index (ADX).
    Returns values in [0, 100]; higher = stronger trend.
    """
    tr = _true_range(high, low, close)
    up_move = high - high.shift(1)
    down_move = low.shift(1) - low

    plus_dm = np.where((up_move > down_move) & (up_move > 0), up_move, 0.0)
    minus_dm = np.where((down_move > up_move) & (down_move > 0), down_move, 0.0)

    plus_dm_s = pd.Series(plus_dm, index=high.index).ewm(span=period, adjust=False).mean()
    minus_dm_s = pd.Series(minus_dm, index=high.index).ewm(span=period, adjust=False).mean()
    atr_s = tr.ewm(span=period, adjust=False).mean().replace(0, np.nan)

    plus_di = 100 * plus_dm_s / atr_s
    minus_di = 100 * minus_dm_s / atr_s
    dx = 100 * (plus_di - minus_di).abs() / (plus_di + minus_di).replace(0, np.nan)
    adx = dx.ewm(span=period, adjust=False).mean()
    return adx


def _rolling_zscore(series: pd.Series, window: int = 252) -> pd.Series:
    """
    Z-score of a cumulative series over a rolling window.
    Used for VPT and OBV to make them stationary and cross-sectionally comparable.
    """
    mean = series.rolling(window, min_periods=max(30, window // 4)).mean()
    std = series.rolling(window, min_periods=max(30, window // 4)).std().replace(0, np.nan)
    return (series - mean) / std


def _idio_vol(
    stock_ret: pd.Series,
    market_ret: pd.Series,
    window: int = 60,
    idio_window: int = 20,
) -> pd.Series:
    """
    Idiosyncratic volatility: annualised std of residuals after removing
    the rolling OLS market beta.

    idio_ret_t = stock_ret_t - beta_t * market_ret_t
    idio_vol_t = std(idio_ret_{t-idio_window+1 .. t}) * sqrt(252)

    beta_t is estimated via rolling OLS over the past `window` days.
    This is fully causal: at time t we only use data up to t.

    Parameters
    ----------
    stock_ret : pd.Series
        Daily log-returns of the stock.
    market_ret : pd.Series
        Daily log-returns of the market (e.g. SPY).
    window : int
        Rolling window (in days) for beta estimation.
    idio_window : int
        Rolling window for computing the std of residuals.

    Returns
    -------
    pd.Series
        Annualised idiosyncratic volatility, same index as stock_ret.
    """
    min_p = max(20, window // 3)

    # Rolling covariance and market variance → rolling beta
    cov = stock_ret.rolling(window, min_periods=min_p).cov(market_ret)
    var_m = market_ret.rolling(window, min_periods=min_p).var().replace(0, np.nan)
    beta = cov / var_m  # rolling OLS beta

    # Idiosyncratic return = stock return - systematic return
    idio_ret = stock_ret - beta * market_ret

    # Annualised std of idiosyncratic return
    return idio_ret.rolling(idio_window, min_periods=max(5, idio_window // 2)).std() * np.sqrt(252)
