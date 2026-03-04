# Production ML Features

## Current feature set (27)

- **Momentum (3):** mom_21d, mom_63d, mom_126d  
- **Trend (3):** dist_sma_50, dist_sma_200, adx_14  
- **Volatility (3):** rvol_20d, rvol_60d, atr_pct  
- **Volume/Flow (3):** vpt_zscore, obv_zscore, vol_zscore_20d  
- **Cross-asset (4):** spy_mom_21d, spy_rvol_20d, qqq_mom_21d, vix_proxy  
- **Sector rotation (6):** xlk_mom_21d, xlf_mom_21d, xle_mom_21d, xlv_mom_21d, xly_mom_21d, xlp_mom_21d  
- **Alpha (5):** rev_1w, high_52w_prox, idio_vol, ret_skew_20d, vol_ratio  

All features are strictly causal (no look-ahead). Cross-sectional z-scoring is applied at training time and the same params are used at inference (see `train.py` / `model_registry.py`).

---

## Adding earnings momentum and analyst revision signals

These move stocks independently of the market but require external data (e.g. IBES, Refinitiv, or yfinance earnings).

### Earnings momentum

- **Source ideas:** yfinance `Ticker(ticker).earnings_dates` (surprise, next date), or IBES actual vs estimate.
- **Causal signal:** e.g. last quarter’s surprise (standardised), or “days since last earnings” to capture event drift.
- **Steps:**
  1. In `data_loader.py`, fetch/store earnings data per ticker (or attach a column per date, e.g. `earnings_surprise_1q`).
  2. In `features.py`, add the feature to `FEATURE_NAMES` and compute it in `build_features(df)` using only data available at time `t`.
  3. Retrain; the bundle’s feature schema will include the new name and inference will expect it.

### Analyst revision signals

- **Source:** IBES/Refinitiv consensus revision (e.g. 1m change in FY1 EPS estimate).
- **Causal signal:** e.g. `analyst_rev_1m` = revision over the past 21 trading days, standardised cross-sectionally (or raw; XS z-score is applied in training).
- **Steps:**
  1. In `data_loader.py`, attach a column (e.g. `analyst_rev_1m`) to each ticker’s DataFrame, aligned by date.
  2. In `features.py`, append to `FEATURE_NAMES` and in `build_features()` set `feat["analyst_rev_1m"] = df["analyst_rev_1m"]` (or derive from raw revision data).
  3. Retrain and redeploy; `ModelRegistry.predict()` will require the new column at inference.

Adding these will increase the feature count (e.g. 27 → 29). Ensure inference call sites provide the new columns or the registry will raise.
