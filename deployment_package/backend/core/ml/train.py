"""
train.py
========
Full walk-forward training pipeline for the production ML model.

Usage (run from repo root)
--------------------------
    python -m deployment_package.backend.core.ml.train

Or call programmatically:
    from deployment_package.backend.core.ml.train import run_pipeline
    results, model = run_pipeline(
        tickers=["AAPL", "MSFT", "GOOGL", "AMZN", "NVDA",
                 "META", "TSLA", "NFLX", "AMD", "INTC"],
        start_date="2019-01-01",
        n_splits=4,
    )
    print(results)

Pipeline steps
--------------
1. Fetch adjusted OHLCV via yfinance (DataLoader)
2. Build strictly causal features (features.build_features)
3. Build vol-adjusted 20D forward-return targets (targets.build_targets)
4. Stack all tickers into a single (X, y) matrix
5. Walk-forward CV with embargo (cv.walk_forward_splits)
6. Train LightGBM per fold, evaluate on test fold
7. Print fold-by-fold R², IC, decile spread
8. Retrain final model on ALL data
9. Save model + feature schema to ml_models/production_r2.pkl
10. Return (fold_metrics_df, final_model)
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any

import numpy as np
import pandas as pd

from .cv import walk_forward_splits
from .data_loader import DataLoader
from .evaluate import evaluate, summarise
from .features import FEATURE_NAMES, build_features
from .model_registry import ModelRegistry
from .targets import build_targets

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Default ticker universe for training
# Large-cap, liquid names across sectors — good signal-to-noise ratio
# ---------------------------------------------------------------------------
DEFAULT_TICKERS = [
    # Tech
    "AAPL", "MSFT", "GOOGL", "AMZN", "NVDA", "META", "AMD", "INTC", "CRM", "ADBE",
    # Finance
    "JPM", "BAC", "GS", "MS", "V", "MA",
    # Healthcare
    "JNJ", "UNH", "PFE", "ABBV",
    # Consumer
    "TSLA", "HD", "MCD", "COST", "NKE",
    # Energy / Industrial
    "XOM", "CVX", "CAT", "BA",
    # ETFs (add market context variety)
    "QQQ", "IWM",
]

# ---------------------------------------------------------------------------
# LightGBM hyperparameters
# Conservative settings: low learning rate + early stopping prevents overfit
# ---------------------------------------------------------------------------
_LGBM_PARAMS = dict(
    n_estimators=500,
    learning_rate=0.01,
    max_depth=5,
    num_leaves=31,
    subsample=0.8,
    colsample_bytree=0.8,
    reg_alpha=0.1,          # L1 regularisation
    reg_lambda=1.0,         # L2 regularisation
    min_child_samples=20,   # avoids overfitting on tiny leaf nodes
    random_state=42,
    n_jobs=-1,
    verbose=-1,             # suppress LightGBM training output
)


def run_pipeline(
    tickers: list[str] | None = None,
    start_date: str = "2019-01-01",
    end_date: str | None = None,
    horizon: int = 20,
    n_splits: int = 4,
    embargo_periods: int = 20,
    save_model: bool = True,
    vol_adjust: bool = True,
) -> tuple[pd.DataFrame, Any]:
    """
    Run the full walk-forward ML pipeline.

    Parameters
    ----------
    tickers : list[str] | None
        Tickers to train on.  Defaults to DEFAULT_TICKERS (30 large-caps).
    start_date : str
        Start of the historical window.  At least 3 years recommended.
    end_date : str | None
        End of the window.  Defaults to today.
    horizon : int
        Forward-return horizon in trading days (default 20 = ~1 month).
    n_splits : int
        Number of walk-forward folds.
    embargo_periods : int
        Rows to drop from the end of each training fold (should equal horizon).
    save_model : bool
        If True, saves the final model to ml_models/production_r2.pkl.
    vol_adjust : bool
        If True, target = forward_log_ret / realised_vol (recommended).

    Returns
    -------
    (fold_metrics_df, final_model)
        fold_metrics_df : pd.DataFrame with R², IC, decile_spread per fold + mean/std
        final_model     : fitted LGBMRegressor trained on all data
    """
    tickers = tickers or DEFAULT_TICKERS
    end_date = end_date or datetime.utcnow().strftime("%Y-%m-%d")

    logger.info(
        "run_pipeline: %d tickers, %s→%s, horizon=%d, n_splits=%d, embargo=%d",
        len(tickers), start_date, end_date, horizon, n_splits, embargo_periods,
    )

    # ------------------------------------------------------------------
    # Step 1: Fetch data
    # ------------------------------------------------------------------
    loader = DataLoader()
    ticker_dfs = loader.fetch(tickers, start_date=start_date, end_date=end_date)
    logger.info("Fetched data for %d/%d tickers", len(ticker_dfs), len(tickers))

    # ------------------------------------------------------------------
    # Step 2-4: Build features + targets, stack all tickers
    # ------------------------------------------------------------------
    X_parts, y_parts = [], []

    for ticker, df in ticker_dfs.items():
        try:
            feat = build_features(df)
            targ = build_targets(df, horizon=horizon, vol_adjust=vol_adjust)

            # Align on common index (inner join — drops NaN rows from both)
            common_idx = feat.dropna().index.intersection(targ.index)
            if len(common_idx) < 50:
                logger.warning("%s: only %d aligned rows — skipping", ticker, len(common_idx))
                continue

            X_parts.append(feat.loc[common_idx])
            y_parts.append(targ.loc[common_idx])

        except Exception as exc:
            logger.warning("Error processing %s: %s — skipping", ticker, exc)
            continue

    if not X_parts:
        raise RuntimeError("No tickers produced usable data. Check data fetch and feature build.")

    # Stack: rows = (ticker × date), features = FEATURE_NAMES
    # We sort by date so walk-forward splits respect time order across tickers
    X_all = pd.concat(X_parts).sort_index()
    y_all = pd.concat(y_parts).sort_index()

    # Clip extreme target values (>5σ) to reduce the influence of data errors
    y_std = y_all.std()
    y_all = y_all.clip(lower=-5 * y_std, upper=5 * y_std)

    logger.info(
        "Dataset: %d rows × %d features (from %d tickers)",
        len(X_all), len(FEATURE_NAMES), len(X_parts),
    )

    # ------------------------------------------------------------------
    # Step 5-6: Walk-forward CV
    # ------------------------------------------------------------------
    try:
        import lightgbm as lgb
    except ImportError as exc:
        raise ImportError(
            "LightGBM is required: add 'lightgbm>=4.0.0' to requirements.txt "
            "and run: pip install lightgbm"
        ) from exc

    X_np = X_all.values
    y_np = y_all.values

    fold_results = []

    for fold_num, (train_idx, test_idx) in enumerate(
        walk_forward_splits(len(X_np), n_splits=n_splits, embargo_periods=embargo_periods),
        start=1,
    ):
        X_train, X_test = X_np[train_idx], X_np[test_idx]
        y_train, y_test = y_np[train_idx], y_np[test_idx]

        model = lgb.LGBMRegressor(**_LGBM_PARAMS)
        model.fit(
            X_train, y_train,
            eval_set=[(X_test, y_test)],
            callbacks=[lgb.early_stopping(stopping_rounds=50, verbose=False)],
        )

        preds = model.predict(X_test)
        metrics = evaluate(y_test, preds, fold=fold_num)
        fold_results.append(metrics)

    fold_metrics_df = summarise(fold_results)

    # ------------------------------------------------------------------
    # Step 7: Log summary
    # ------------------------------------------------------------------
    mean_r2 = fold_metrics_df.loc["mean", "r2"] if "mean" in fold_metrics_df.index else np.nan
    mean_ic = fold_metrics_df.loc["mean", "ic"] if "mean" in fold_metrics_df.index else np.nan
    logger.info(
        "Walk-forward complete: mean R²=%.4f  mean IC=%.4f",
        mean_r2, mean_ic,
    )
    print("\n=== Walk-Forward Results ===")
    print(fold_metrics_df.to_string(float_format="{:.4f}".format))
    print()

    # ------------------------------------------------------------------
    # Step 8: Retrain final model on ALL data
    # ------------------------------------------------------------------
    logger.info("Retraining final model on all %d rows ...", len(X_np))
    final_model = lgb.LGBMRegressor(**_LGBM_PARAMS)
    final_model.fit(X_np, y_np)

    # ------------------------------------------------------------------
    # Step 9: Save
    # ------------------------------------------------------------------
    if save_model:
        ModelRegistry.save(
            model=final_model,
            feature_names=FEATURE_NAMES,
            horizon=horizon,
            fold_metrics=fold_metrics_df.loc["mean"].to_dict() if "mean" in fold_metrics_df.index else {},
            n_tickers=len(X_parts),
            n_rows=len(X_np),
        )
        logger.info("Model saved to ml_models/production_r2.pkl")

    return fold_metrics_df, final_model


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import sys

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s  %(levelname)s  %(name)s  %(message)s",
        datefmt="%H:%M:%S",
    )

    # Allow overriding tickers via command-line: python -m ml.train AAPL MSFT GOOGL
    cli_tickers = sys.argv[1:] if len(sys.argv) > 1 else None

    results, _ = run_pipeline(
        tickers=cli_tickers,
        start_date="2019-01-01",
        n_splits=4,
    )

    print("\nFinal fold-by-fold metrics:")
    print(results[["r2", "ic", "decile_spread", "hit_rate"]].to_string(float_format="{:.4f}".format))
