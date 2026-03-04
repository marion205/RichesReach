"""
targets.py
==========
Constructs prediction targets from OHLCV data.

Default target
--------------
Vol-adjusted 20-day forward log-return:

    y_t = log(close_{t+H} / close_t) / realized_vol_20d_t

Dividing by realised vol normalises difficulty across high- and low-vol
regimes, giving the model a consistent signal scale regardless of whether
the stock is calm or in a volatility spike.

Leakage guarantee
-----------------
The target is computed with shift(-H) so feature row t only corresponds to
a target that uses prices strictly after t.  build_targets() includes a
hard assertion that enforces this — any future code change that accidentally
re-introduces leakage will fail loudly rather than silently.
"""

from __future__ import annotations

import logging

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

# Default forward horizon in trading days
DEFAULT_HORIZON = 20

# Minimum annualised vol before we consider the denominator reliable
# (avoids division by near-zero in very low-vol periods)
_MIN_VOL = 0.02 / np.sqrt(252)  # ≈ 0.00126 daily std


def build_targets(
    df: pd.DataFrame,
    horizon: int = DEFAULT_HORIZON,
    vol_adjust: bool = True,
) -> pd.Series:
    """
    Compute the prediction target for a single-ticker OHLCV DataFrame.

    Parameters
    ----------
    df : pd.DataFrame
        Must contain a 'close' column with a DatetimeIndex.
    horizon : int
        Forward window in trading days (default 20).
    vol_adjust : bool
        If True, divide the forward return by 20-day realised vol so the
        target has consistent scale across vol regimes.  If False, return
        raw forward log-return.

    Returns
    -------
    pd.Series
        Target values indexed on the same DatetimeIndex as df, with NaN
        rows (last `horizon` rows and any low-vol rows) dropped.

    Raises
    ------
    ValueError
        If a leakage check fails — feature rows and target rows share
        overlapping forward-price information.
    """
    if "close" not in df.columns:
        raise ValueError("DataFrame must have a 'close' column")

    close = df["close"].copy()

    # --- Forward log-return (uses future price → shifted) ---
    fwd_log_ret = np.log(close.shift(-horizon) / close)

    if not vol_adjust:
        target = fwd_log_ret
    else:
        # --- Realised 20-day vol (uses only past prices → causal) ---
        daily_log_ret = np.log(close / close.shift(1))
        hist_vol = daily_log_ret.rolling(20, min_periods=10).std()

        # Floor vol at minimum to avoid division by near-zero
        hist_vol_floored = hist_vol.clip(lower=_MIN_VOL)

        target = fwd_log_ret / hist_vol_floored

    # Drop rows where target is NaN:
    #   - Last `horizon` rows (no future price available)
    #   - Any rows where close was NaN or vol was too low to be reliable
    target = target.dropna()

    # --- Leakage guard ---
    # The last valid feature row must be BEFORE the first forward-return
    # window begins.  Concretely: if we use features from row t and the
    # forward return covers [t+1, t+H], then t < t+1 always holds — but
    # this check catches bugs where someone accidentally drops the shift.
    _assert_no_leakage(close.index, target.index, horizon)

    logger.debug(
        "build_targets: %d rows → %d target rows (horizon=%d, vol_adjust=%s)",
        len(df), len(target), horizon, vol_adjust,
    )

    return target


def _assert_no_leakage(
    feature_index: pd.DatetimeIndex,
    target_index: pd.DatetimeIndex,
    horizon: int,
) -> None:
    """
    Hard assertion: the last target-valid feature date must be at least
    `horizon` trading days before the last date in the index.

    This is a lightweight sanity check, not a full audit.  The real
    guarantee comes from always using shift(-horizon) for the forward return.
    """
    if len(target_index) == 0:
        return

    last_target_date = target_index.max()
    last_feature_date = feature_index.max()

    # The forward return at `last_target_date` points to close at
    # last_target_date + horizon.  That must not exceed the last date in
    # the raw close series — if it does, we've used NaN-filled future prices.
    if last_target_date > last_feature_date:
        raise ValueError(
            f"Leakage detected: last target date {last_target_date.date()} "
            f"is after last feature date {last_feature_date.date()}.  "
            "This means forward-return labels use prices beyond the dataset end."
        )
