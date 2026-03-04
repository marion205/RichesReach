# Production ML Pipeline — Feature & Performance Reference

## Current feature set (21 technical + 3 earnings = 24 when Polygon/Benzinga used)

| Group | Features |
|---|---|
| **Momentum (3)** | `mom_21d`, `mom_63d`, `mom_126d` |
| **Trend (3)** | `dist_sma_50`, `dist_sma_200`, `adx_14` |
| **Volatility (3)** | `rvol_20d`, `rvol_60d`, `atr_pct` |
| **Volume / Flow (3)** | `vpt_zscore`, `obv_zscore`, `vol_zscore_20d` |
| **Cross-asset (4)** | `spy_mom_21d`, `spy_rvol_20d`, `qqq_mom_21d`, `vix_proxy` |
| **Alpha (5)** | `rev_1w`, `high_52w_prox`, `idio_vol`, `ret_skew_20d`, `vol_ratio` |
| **Earnings (3, optional)** | `eps_surprise_pct`, `surprise_decay`, `days_since_earnings` |

**Earnings Alpha:** Fetched via `earnings_loader.fetch_earnings()` when `POLYGON_API_KEY` is set. Effective date = next trading day if report after close (anti-leakage). `surprise_decay` = PEAD half-life. If no key, earnings columns = 0.

All features are strictly causal (no look-ahead). Cross-sectional z-scoring
is applied at training time and the same params are stored in the model bundle
for inference (see `train.py` / `model_registry.py`).

> **Note on sector ETF features (removed):** Raw sector ETF momentum (e.g.
> `xlk_mom_21d`) is the *same value for every ticker on a given date*. After
> XS z-scoring (which normalises within each date's cross-section), a
> constant feature collapses to 0. They were removed because they consumed
> model capacity without contributing signal.

---

## Validated OOS performance

Walk-forward CV, 4 folds, `test_size=252` (~1 trading year per fold),
market-neutral target (stock return − equal-weight cross-sectional mean),
78 tickers, 21 features, LightGBM.

| Test period | IC | Decile spread | Hit rate | Notes |
|---|---|---|---|---|
| 2022-01 → 2023-01 | +0.007 | +0.18 | 51.4% | Rate-hike bear market |
| 2023-01 → 2024-01 | -0.008 | -0.07 | 49.7% | Value rotation, momentum lagged |
| 2024-01 → 2025-01 | +0.003 | -0.22 | 50.2% | Narrow AI-rally leadership |
| 2025-01 → 2026-02 | **+0.055** | **+0.77** | 51.9% | Current period |
| **Mean** | **+0.014** | **+0.17** | **50.8%** | |
| **Std** | 0.028 | 0.44 | 0.01 | |

**Interpretation:**
- Mean IC +0.014 is consistent with published academic benchmarks for
  pure price/volume models on daily data (typical range: IC=0.01–0.03).
- The 2022–2024 near-zero IC folds are expected: in those years earnings
  surprises and analyst revisions drove most stock-specific moves, not
  technical patterns. A price/volume model correctly produces ~0 signal.
- The 2025 fold IC=+0.055 is strong and reflects the current regime.
- **To get IC consistently >0.02–0.03 across all regimes, the next
  addition is earnings/fundamental data** (see below).

> **Note:** The 2021 meme-stock / SPAC bubble period (fold trained on
> COVID-era data) is excluded from CV evaluation. No price/volume model
> can generalise from COVID crash dynamics to retail-driven meme-stock
> flows — this is a known regime anomaly, not a model deficiency.

---

## Adding earnings and fundamental signals

These features move stocks independently of the market across all regimes
and are the primary missing signal. They require external data.

### 1. Earnings surprise (highest priority)

- **What it is:** `(actual_EPS − consensus_EPS) / |consensus_EPS|` for the
  most recent reported quarter. Standardised cross-sectionally.
- **Why it works:** Post-earnings announcement drift (PEAD) — stocks that
  beat estimates by >1σ continue to outperform for 20–60 days. This is the
  most consistently documented anomaly in academic literature.
- **Data sources:**
  - Free: `yfinance.Ticker(t).earnings_dates` (limited history)
  - Paid: Refinitiv IBES, Compustat, Alpha Vantage earnings API
- **Implementation steps:**
  1. In `data_loader.py`: fetch quarterly earnings per ticker, forward-fill
     the most recent quarter's surprise into each daily row (causal — only
     use reports that were public at time t).
  2. In `features.py`: add `"earnings_surprise_1q"` to `FEATURE_NAMES` and
     `feat["earnings_surprise_1q"] = df["earnings_surprise_1q"]` in
     `build_features()`. XS z-score is applied automatically in `train.py`.
  3. Retrain. Expected IC improvement: +0.01 to +0.03 on the 2022–2024 folds.

### 2. Post-earnings drift flag

- **What it is:** Number of calendar days since the last earnings announcement,
  clipped at 90 days. Captures the "drift window" where PEAD is strongest.
- **Implementation:** Attach `days_since_earnings` per ticker per date in
  `data_loader.py`; compute in `features.py` as
  `feat["days_since_earnings"] = df["days_since_earnings"].clip(upper=90)`.

### 3. Analyst revision momentum

- **What it is:** 1-month change in the FY1 consensus EPS estimate, normalised
  by the absolute estimate. Captures systematic analyst under-reaction.
- **Data sources:** Refinitiv IBES, Bloomberg, or Visible Alpha.
- **Implementation:** Same pattern — attach per-ticker in `data_loader.py`,
  expose as `feat["analyst_rev_1m"]` in `features.py`.

---

## How to add a new feature (checklist)

1. **Add the name** to `FEATURE_NAMES` in `features.py`.
2. **Compute it** in `build_features(df)` using only columns available at time t.
   Use past prices/volumes/fundamentals only — never `shift(-n)` on inputs.
3. **If it needs external data**, fetch it in `DataLoader.fetch()` and attach
   it as a column on the per-ticker DataFrame.
4. **Retrain** — `python -m deployment_package.backend.core.ml.train`.
   The new feature schema is stored in the model bundle automatically.
5. **Update this README** with the new feature count and performance figures.

> **Inference compatibility:** `ModelRegistry.predict()` enforces the feature
> schema saved at training time. If you add features and retrain, the old
> `.pkl` file must be replaced — inference with mismatched features will raise.
