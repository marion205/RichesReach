"""
evaluate.py
===========
Out-of-sample evaluation metrics for the production ML pipeline.

Why R² alone is not enough
---------------------------
For individual-stock return prediction, OOS R² is inherently low (2–15%)
because realised returns are extremely noisy.  A model can have R² = 0.05
and still be highly profitable if its *ranking* is correct.

We track four complementary metrics:

1. R²  (sklearn)
   Classic goodness-of-fit.  Negative R² means the model is worse than
   predicting the mean.  Target: > 0 consistently across folds.

2. Spearman IC  (Information Coefficient)
   Rank correlation between predicted and realised returns.  Quant funds
   use this as the primary signal-quality metric because they rank stocks
   to build portfolios, not predict exact returns.
   Target: IC > 0.02 per fold (0.05+ is institutional-grade).

3. Decile spread
   Mean return of stocks in the top prediction decile minus mean return
   of stocks in the bottom decile.  Directly measures the model's ability
   to separate winners from losers.  Positive = actionable signal.

4. Hit rate
   Fraction of predictions with the correct sign.  Random = 0.50.
   Anything > 0.52 consistently is useful.
"""

from __future__ import annotations

import logging

import numpy as np
import pandas as pd
from scipy.stats import spearmanr
from sklearn.metrics import r2_score

logger = logging.getLogger(__name__)


def evaluate(
    y_true: pd.Series | np.ndarray,
    y_pred: np.ndarray,
    fold: int | None = None,
) -> dict[str, float]:
    """
    Compute all evaluation metrics for one fold.

    Parameters
    ----------
    y_true : array-like
        Realised target values (vol-adjusted forward returns).
    y_pred : array-like
        Model predictions.
    fold : int | None
        Fold number for logging.

    Returns
    -------
    dict with keys: r2, ic, ic_pvalue, decile_spread, hit_rate
    """
    y_true = np.asarray(y_true, dtype=float)
    y_pred = np.asarray(y_pred, dtype=float)

    # Remove any NaN pairs
    mask = np.isfinite(y_true) & np.isfinite(y_pred)
    y_true, y_pred = y_true[mask], y_pred[mask]

    if len(y_true) < 10:
        logger.warning("Fold %s: fewer than 10 valid samples — metrics unreliable", fold)
        return {"r2": np.nan, "ic": np.nan, "ic_pvalue": np.nan,
                "decile_spread": np.nan, "hit_rate": np.nan}

    r2 = float(r2_score(y_true, y_pred))

    ic_result = spearmanr(y_true, y_pred)
    ic = float(ic_result.correlation if hasattr(ic_result, "correlation") else ic_result[0])
    ic_pvalue = float(ic_result.pvalue if hasattr(ic_result, "pvalue") else ic_result[1])

    decile_spread = _decile_spread(y_true, y_pred)
    hit_rate = float(np.mean(np.sign(y_true) == np.sign(y_pred)))

    result = {
        "r2": r2,
        "ic": ic,
        "ic_pvalue": ic_pvalue,
        "decile_spread": decile_spread,
        "hit_rate": hit_rate,
        "n_samples": int(len(y_true)),
    }

    fold_label = f"Fold {fold}" if fold is not None else "Eval"
    logger.info(
        "%s: R²=%.4f  IC=%.4f (p=%.3f)  decile_spread=%.4f  hit_rate=%.3f  n=%d",
        fold_label, r2, ic, ic_pvalue, decile_spread, hit_rate, len(y_true),
    )

    return result


def _decile_spread(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    """
    Mean realised return of top-decile predictions minus bottom-decile.

    A positive value means the model successfully separates high-return
    stocks from low-return stocks — the most practically useful signal.
    """
    df = pd.DataFrame({"true": y_true, "pred": y_pred})

    # Need at least 20 samples to form 10 non-empty deciles
    if len(df) < 20:
        return np.nan

    try:
        df["decile"] = pd.qcut(df["pred"], q=10, labels=False, duplicates="drop")
    except ValueError:
        # Can happen if there are too many tied predictions
        return np.nan

    top_decile = df[df["decile"] == df["decile"].max()]["true"].mean()
    bot_decile = df[df["decile"] == df["decile"].min()]["true"].mean()
    return float(top_decile - bot_decile)


def summarise(fold_results: list[dict]) -> pd.DataFrame:
    """
    Convert a list of per-fold metric dicts into a summary DataFrame
    with mean ± std across folds.

    Parameters
    ----------
    fold_results : list[dict]
        Each dict is the output of evaluate() for one fold.

    Returns
    -------
    pd.DataFrame
        Rows: each fold + a 'mean' and 'std' summary row.
    """
    df = pd.DataFrame(fold_results)
    df.index = [f"fold_{i+1}" for i in range(len(df))]
    summary = pd.concat([
        df,
        pd.DataFrame(df.mean()).T.rename(index={0: "mean"}),
        pd.DataFrame(df.std()).T.rename(index={0: "std"}),
    ])
    return summary
