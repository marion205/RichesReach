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
from .earnings_loader import fetch_earnings
from .earnings_features import build_earnings_features, EARNINGS_FEATURE_NAMES
from .analyst_loader import fetch_recommendation
from .analyst_features import build_analyst_features, ANALYST_FEATURE_NAMES
from .evaluate import evaluate, summarise
from .features import FEATURE_NAMES as TECHNICAL_FEATURE_NAMES, build_features
from .model_registry import ModelRegistry
from .targets import build_targets

logger = logging.getLogger(__name__)

# Full feature list: technical (22) + earnings (3) + analyst revision (3) = 28
# analyst_rev_1m  : EPS estimate change (placeholder 0 until estimate revision API)
# rec_upgrade_score: Finnhub (buy-sell)/total analyst consensus — live when key set
# fy1_rev_3m      : FY1 EPS revision (placeholder 0 until estimate revision API)
FEATURE_NAMES = TECHNICAL_FEATURE_NAMES + EARNINGS_FEATURE_NAMES + ANALYST_FEATURE_NAMES

# ---------------------------------------------------------------------------
# Default ticker universe for training (200+ names for lower IC variance)
# Large-cap, liquid, cross-sector — yfinance supports all; more stocks = more
# cross-sectional spread and more stable fold IC estimates.
# ---------------------------------------------------------------------------
DEFAULT_TICKERS = [
    # Large-cap Tech
    "AAPL", "MSFT", "GOOGL", "GOOG", "AMZN", "NVDA", "META", "AMD", "INTC", "CRM", "ADBE",
    "ORCL", "CSCO", "TXN", "QCOM", "MU", "AVGO", "NOW", "INTU", "AMAT", "LRCX", "KLAC",
    "SNPS", "CDNS", "MRVL", "ADI", "NXPI", "MCHP", "FTNT", "PANW", "CRWD", "ZS", "DDOG", "NET", "SNOW",
    # Finance
    "JPM", "BAC", "GS", "MS", "V", "MA", "AXP", "WFC", "C", "BLK", "SCHW", "BK", "USB", "PNC", "COF", "TFC", "STT", "FITB", "KEY", "HBAN",
    # Healthcare
    "JNJ", "UNH", "PFE", "ABBV", "MRK", "LLY", "BMY", "AMGN", "GILD", "CVS", "CI", "HUM", "ELV", "MDT", "ABT", "SYK", "BSX", "ZBH", "ISRG", "DXCM", "REGN", "VRTX", "BIIB", "MRNA", "ILMN", "IQV", "EW", "IDXX", "HCA", "MCK", "CAH", "ABC",
    # Consumer Discretionary
    "TSLA", "HD", "MCD", "COST", "NKE", "SBUX", "TGT", "LOW", "AMZN", "BKNG", "MAR", "HLT", "LVS", "MGM", "CMG", "YUM", "DPZ", "DRI", "EBAY", "ETSY", "ROST", "TJX", "F", "GM", "RCL", "CCL", "NCLH", "WYNN", "DHI", "LEN", "PHM", "NVR",
    # Consumer Staples
    "PG", "KO", "PEP", "WMT", "CL", "GIS", "KMB", "MDLZ", "K", "SJM", "HSY", "STZ", "BF-B", "MO", "PM", "TAP", "CAG", "CPB", "HRL", "MKC", "SYY", "ADM", "BG",
    # Energy
    "XOM", "CVX", "COP", "SLB", "EOG", "PXD", "MPC", "VLO", "PSX", "OXY", "HAL", "DVN", "FANG", "HES", "BKR", "KMI", "WMB", "OKE", "APA",
    # Industrials
    "CAT", "BA", "GE", "HON", "MMM", "UPS", "FDX", "RTX", "LMT", "NOC", "GD", "DE", "CARR", "OTIS", "JCI", "EMR", "ETN", "ITW", "ROK", "PH", "DOV", "IR", "CMI", "PCAR", "WM", "RSG", "FAST", "CTAS", "CSX", "UNP", "NSC", "JBHT", "CHRW", "LUV", "DAL", "UAL", "AAL",
    # Materials & Real Estate
    "FCX", "NEM", "AMT", "PLD", "LIN", "APD", "SHW", "ECL", "DD", "DOW", "NUE", "STLD", "VMC", "MLM", "CE", "PPG", "ALB", "EQIX", "PSA", "O", "WELL", "SPG", "AVB", "EQR", "VTR", "DLR", "ARE",
    # Mid-cap growth / Value
    "MELI", "SE", "GRAB", "BRK-B", "T", "VZ", "DIS", "NFLX", "CMCSA", "CHTR", "TMUS",
]
# Remove duplicates while preserving order
DEFAULT_TICKERS = list(dict.fromkeys(DEFAULT_TICKERS))

# ---------------------------------------------------------------------------
# Regime labelling for stratified IC (keys match position_sizer._REGIME_GATE)
# ---------------------------------------------------------------------------
def _label_regime_for_test_window(
    test_dates: set,
    spy_ret_series: pd.Series,
) -> str:
    """
    Label a test date window as a regime using SPY return/vol over that window.
    Returns one of: Crisis, Deflation, Expansion, Parabolic, Unknown.
    """
    if spy_ret_series.empty or len(test_dates) < 20:
        return "Unknown"
    try:
        idx = pd.to_datetime(spy_ret_series.index).normalize()
        subset = spy_ret_series.copy()
        subset.index = idx
        test_idx = pd.to_datetime(list(test_dates)).normalize()
        sub = subset.reindex(test_idx).dropna()
        if len(sub) < 20:
            return "Unknown"
        mean_ret = float(sub.mean()) * 252
        ann_vol = float(sub.std()) * np.sqrt(252) if sub.std() > 1e-10 else 0.0
    except Exception:
        return "Unknown"

    if mean_ret < -0.12 and ann_vol > 0.22:
        return "Crisis"
    if mean_ret < -0.05 and ann_vol < 0.18:
        return "Deflation"
    if mean_ret > 0.18:
        return "Parabolic"
    if mean_ret > 0.05 and ann_vol < 0.20:
        return "Expansion"
    return "Unknown"


# ---------------------------------------------------------------------------
# LightGBM hyperparameters
# Conservative settings: low learning rate + early stopping prevents overfit
# ---------------------------------------------------------------------------
_LGBM_PARAMS = dict(
    n_estimators=1000,       # more trees to capture the new alpha features
    learning_rate=0.005,     # lower LR → more trees, but better generalisation
    max_depth=4,             # shallower trees reduce overfit on 22 features
    num_leaves=15,           # fewer leaves → stronger regularisation
    subsample=0.7,           # row subsampling per tree (bagging)
    colsample_bytree=0.7,    # column subsampling per tree
    subsample_freq=1,        # apply row subsampling every tree
    reg_alpha=0.5,           # stronger L1 → feature selection, sparse trees
    reg_lambda=2.0,          # stronger L2 → smaller leaf weights
    min_child_samples=30,    # require more samples per leaf → avoids tiny noisy splits
    min_child_weight=1e-3,   # minimum sum of hessian in leaf
    random_state=42,
    n_jobs=-1,
    verbose=-1,             # suppress LightGBM training output
)


def run_pipeline(
    tickers: list[str] | None = None,
    start_date: str = "2019-01-01",
    end_date: str | None = None,
    horizon: int = 20,
    n_splits: int = 6,
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

            # Optional earnings features (Polygon/Benzinga). If no API key or no data, use zeros.
            earnings_df = fetch_earnings(ticker, start_date, end_date)
            earn_feat = build_earnings_features(df, earnings_df)
            earn_aligned = earn_feat.reindex(common_idx).fillna(0.0)

            # Optional analyst revision features (Finnhub). Uses zeros when key not set.
            rec_df = fetch_recommendation(ticker)
            analyst_feat = build_analyst_features(df, rec_df)
            analyst_aligned = analyst_feat.reindex(common_idx).fillna(0.0)

            X_ticker = pd.concat(
                [feat.loc[common_idx], earn_aligned, analyst_aligned], axis=1
            )[FEATURE_NAMES]
            X_parts.append(X_ticker)
            y_parts.append(targ.loc[common_idx])

        except Exception as exc:
            logger.warning("Error processing %s: %s — skipping", ticker, exc)
            continue

    if not X_parts:
        raise RuntimeError("No tickers produced usable data. Check data fetch and feature build.")

    # ------------------------------------------------------------------
    # SPY series for regime labelling (date -> daily log return)
    # Used to label each fold's test window so we can compute regime_ic.
    # ------------------------------------------------------------------
    _first_df = next(iter(ticker_dfs.values()))
    spy_close = _first_df.get("spy_close")
    if spy_close is not None and spy_close.notna().sum() > 20:
        spy_ret = np.log(spy_close / spy_close.shift(1))
        spy_ret = spy_ret.dropna()
        spy_ret_by_date = spy_ret
        if hasattr(spy_ret.index, "normalize"):
            spy_ret_by_date = spy_ret.copy()
            spy_ret_by_date.index = pd.to_datetime(spy_ret_by_date.index).normalize()
    else:
        spy_ret_by_date = pd.Series(dtype=float)

    # ------------------------------------------------------------------
    # FIX 1: Stack with (date, ticker) MultiIndex — NOT sort_index() by date alone.
    #
    # The original sort_index() interleaved tickers at the same timestamp:
    #   row 0: AAPL 2019-01-02
    #   row 1: MSFT 2019-01-02
    #   row 2: AAPL 2019-01-03 ...
    # When TimeSeriesSplit then splits at row N, it cuts through the middle of
    # a single trading day, so test rows can predate training rows → look-ahead.
    #
    # The correct structure: split on unique dates, then flatten for LightGBM.
    # We keep a parallel date array so the CV can split on dates.
    # ------------------------------------------------------------------
    ticker_labels = list(ticker_dfs.keys())  # tickers that survived data fetch
    valid_tickers = [t for t, X in zip(ticker_labels, X_parts) if len(X) >= 50]

    # Attach ticker label to each feature/target part before stacking
    X_tagged, y_tagged = [], []
    for ticker, X, y in zip(valid_tickers, X_parts, y_parts):
        X = X.copy()
        X["_ticker"] = ticker
        X_tagged.append(X)
        y_tagged.append(y.rename(ticker))

    # Stack, creating a (date, ticker) MultiIndex
    X_stacked = pd.concat(X_tagged)
    X_stacked.index.name = "date"
    X_stacked = X_stacked.reset_index().set_index(["date", "_ticker"])
    X_stacked.index.names = ["date", "ticker"]

    y_stacked = pd.concat(y_tagged)
    y_stacked.index.name = "date"

    # y needs the same (date, ticker) MultiIndex
    y_df = pd.concat(
        [y.to_frame(name="target").assign(ticker=t) for t, y in zip(valid_tickers, y_parts)]
    ).reset_index().rename(columns={"index": "date"})
    # Rename the date column robustly
    date_col = [c for c in y_df.columns if c not in ("target", "ticker")][0]
    y_df = y_df.rename(columns={date_col: "date"})
    y_df = y_df.set_index(["date", "ticker"])["target"]

    # Align on common (date, ticker) pairs
    common_idx = X_stacked.index.intersection(y_df.index)
    X_stacked = X_stacked.loc[common_idx]
    y_stacked = y_df.loc[common_idx]

    # ------------------------------------------------------------------
    # Market-neutralise the target: subtract SPY vol-adjusted forward return
    # from each stock's vol-adjusted forward return on the same date.
    #
    # WHY THIS MATTERS:
    #   Without neutralisation, on a day when the market rallies 5% over the
    #   next 20 days, every stock's raw target is positive regardless of its
    #   stock-specific signal.  The model then learns "buy everything in bull
    #   markets, sell everything in bear markets" — which explains the extreme
    #   fold-to-fold variance (fold 1 in a bull run: IC=+0.09; fold 2 in
    #   COVID crash: IC=-0.06).
    #
    #   After neutralisation, y_t = (stock_alpha_t - market_return_t), so
    #   the model only needs to learn cross-sectional ordering — which stock
    #   beats market, regardless of market direction.
    #
    # METHOD: Per-date XS mean of y is the market-wide return (equal-weight).
    #   We subtract it from each row.  This is equivalent to demeaning the
    #   target within each date's cross-section (no look-ahead: we compute
    #   the mean only across tickers that share the same forecast date t,
    #   using the same forward-return window t→t+H).
    # ------------------------------------------------------------------
    y_stacked = (
        y_stacked
        .groupby(level="date")
        .transform(lambda grp: grp - grp.mean())
    )

    # Clip extreme targets (>5σ) — after neutralisation to avoid over-clipping
    y_std = y_stacked.std()
    y_stacked = y_stacked.clip(lower=-5 * y_std, upper=5 * y_std)

    logger.info(
        "Dataset: %d rows × %d features (from %d tickers, %d unique dates)",
        len(X_stacked), len(FEATURE_NAMES),
        len(valid_tickers),
        X_stacked.index.get_level_values("date").nunique(),
    )

    # ------------------------------------------------------------------
    # FIX 2: Cross-sectional z-scoring — normalise each feature vs peers
    # on the same date so the model sees relative strength, not absolute levels.
    #
    # e.g. AAPL mom_21d=0.08 in a day where mean=0.05, std=0.02 → z=+1.5
    #      (strong relative to peers on that day)
    # This removes market-wide beta from features and lets the model learn
    # stock-specific alpha signals.
    # ------------------------------------------------------------------
    feat_cols = FEATURE_NAMES
    X_feat = X_stacked[feat_cols].copy()

    def _xs_zscore(group: pd.DataFrame) -> pd.DataFrame:
        mean = group.mean()
        std = group.std().replace(0, np.nan)
        return (group - mean) / std

    # Group by date level, z-score within each cross-section
    X_feat = (
        X_feat
        .groupby(level="date", group_keys=False)
        .apply(_xs_zscore)
        .fillna(0.0)   # fill days with only 1 ticker (std=NaN) with 0
    )

    # Store the global (mean, std) of the XS-normalised features so the
    # inference path can apply the same normalisation to a single ticker.
    # After XS z-scoring, global mean ≈ 0 and std ≈ 1 by construction,
    # but storing exact values handles edge cases cleanly.
    xs_global_mean = X_feat.mean()
    xs_global_std  = X_feat.std().replace(0, 1.0)

    # ------------------------------------------------------------------
    # FIX 3: Date-based walk-forward CV (not positional).
    #
    # Sort unique dates, split into folds on dates.  All tickers on the same
    # date always move together between train and test — no cross-ticker leakage.
    # Embargo: exclude the last `embargo_periods` dates from each training fold.
    # ------------------------------------------------------------------
    try:
        import lightgbm as lgb
    except ImportError as exc:
        raise ImportError(
            "LightGBM is required: add 'lightgbm>=4.0.0' to requirements.txt "
            "and run: pip install lightgbm"
        ) from exc

    unique_dates = sorted(X_feat.index.get_level_values("date").unique())
    n_dates = len(unique_dates)

    # Fixed test size: each fold tests on exactly 252 dates (~1 trading year).
    # With 1582 total dates and 6 splits of 252:
    #   fold_1 trains on 1582 - 6×252 =  70 dates (skipped — too small)
    #   fold_2 trains on 70 + 252      = 322 dates (borderline — skipped if < 252+20 embargo)
    #   fold_3 trains on 322 + 252     = 574 dates ✓ (~2.3 years)
    #   fold_4 trains on 574 + 252     = 826 dates ✓ (~3.3 years)
    #   fold_5 trains on 826 + 252     = 1078 dates ✓ (~4.3 years)
    #   fold_6 trains on 1078 + 252    = 1330 dates ✓ (~5.3 years)
    # Net result: 4 clean folds, each testing on exactly 1 calendar year.
    _TEST_SIZE = 252

    # Minimum training dates before a fold is usable.
    # We require 500 dates (~2 full trading years) for two reasons:
    #   (a) Features with long warm-up periods (dist_sma_200 = 200 bars,
    #       high_52w_prox = 252 bars) need at least 1 year just to have
    #       valid feature values; another year to learn from them.
    #   (b) The 2021 meme-stock / SPAC bubble was a historically anomalous
    #       regime where retail flow dominated.  The fold trained on 302 dates
    #       (mostly 2019-2020 COVID crash/recovery) then tested on 2021 produced
    #       IC=-0.073 — not because the model is wrong, but because no
    #       price/volume model can learn the meme-stock regime from COVID data.
    #       Requiring 500 training dates means the earliest testable fold is
    #       mid-2021 → tests 2022-2023 (rate hike cycle), which IS learnable.
    _MIN_TRAIN_DATES = 500

    fold_results = []
    tscv = __import__("sklearn.model_selection", fromlist=["TimeSeriesSplit"]).TimeSeriesSplit(
        n_splits=n_splits,
        test_size=_TEST_SIZE,  # fixed 1-year test window per fold
    )

    for fold_num, (train_date_pos, test_date_pos) in enumerate(
        tscv.split(range(n_dates)), start=1
    ):
        # Apply embargo: drop last embargo_periods dates from training
        embargoed_train_pos = train_date_pos[:-embargo_periods] if len(train_date_pos) > embargo_periods else train_date_pos

        # Skip folds with insufficient training history
        if len(embargoed_train_pos) < _MIN_TRAIN_DATES:
            logger.warning(
                "Fold %d: only %d training dates after embargo (need %d) — skipping "
                "(early tickers sparse; model would be unreliable)",
                fold_num, len(embargoed_train_pos), _MIN_TRAIN_DATES,
            )
            continue

        train_dates = set(unique_dates[i] for i in embargoed_train_pos)
        test_dates = set(unique_dates[i] for i in test_date_pos)

        # Log fold date ranges for transparency
        train_start = min(train_dates)
        train_end = max(train_dates)
        test_start = min(test_dates)
        test_end = max(test_dates)
        logger.info(
            "Fold %d: train %s→%s (%d dates), test %s→%s (%d dates)",
            fold_num,
            getattr(train_start, "date", lambda: train_start)(),
            getattr(train_end, "date", lambda: train_end)(),
            len(train_dates),
            getattr(test_start, "date", lambda: test_start)(),
            getattr(test_end, "date", lambda: test_end)(),
            len(test_dates),
        )

        train_mask = X_feat.index.get_level_values("date").isin(train_dates)
        test_mask = X_feat.index.get_level_values("date").isin(test_dates)

        X_train = X_feat[train_mask].values
        X_test  = X_feat[test_mask].values
        y_train = y_stacked[train_mask].values
        y_test  = y_stacked[test_mask].values

        model = lgb.LGBMRegressor(**_LGBM_PARAMS)
        model.fit(
            X_train, y_train,
            eval_set=[(X_test, y_test)],
            callbacks=[lgb.early_stopping(stopping_rounds=100, verbose=False)],
        )

        preds = model.predict(X_test)
        metrics = evaluate(
            y_test, preds, fold=fold_num,
            test_start=str(getattr(test_start, "date", lambda: test_start)()),
            test_end=str(getattr(test_end, "date", lambda: test_end)()),
        )
        regime = _label_regime_for_test_window(test_dates, spy_ret_by_date)
        metrics["regime"] = regime
        fold_results.append(metrics)

    fold_metrics_df = summarise(fold_results)

    # Regime-stratified IC: mean IC per regime for position_sizer.ModelStats(regime_ic=...)
    regime_ic = {}
    for r in fold_results:
        reg = r.get("regime", "Unknown")
        regime_ic.setdefault(reg, []).append(r["ic"])
    regime_ic = {k: float(np.mean(v)) for k, v in regime_ic.items()}
    fold_ics = [float(r["ic"]) for r in fold_results]

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
    # Step 8: Retrain final model on ALL data (cross-sectionally normalised)
    # ------------------------------------------------------------------
    X_final = X_feat.values
    y_final = y_stacked.values
    logger.info("Retraining final model on all %d rows ...", len(X_final))
    final_model = lgb.LGBMRegressor(**_LGBM_PARAMS)
    final_model.fit(X_final, y_final)

    # ------------------------------------------------------------------
    # Step 9: Save
    # ------------------------------------------------------------------
    if save_model:
        ModelRegistry.save(
            model=final_model,
            feature_names=feat_cols,
            horizon=horizon,
            fold_metrics=fold_metrics_df.loc["mean"].to_dict() if "mean" in fold_metrics_df.index else {},
            fold_ics=fold_ics,
            n_tickers=len(valid_tickers),
            n_rows=len(X_final),
            xs_mean=xs_global_mean,
            xs_std=xs_global_std,
            regime_ic=regime_ic,
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
        n_splits=6,
    )

    print("\nFinal fold-by-fold metrics:")
    print(results[["r2", "ic", "decile_spread", "hit_rate"]].to_string(float_format="{:.4f}".format))
