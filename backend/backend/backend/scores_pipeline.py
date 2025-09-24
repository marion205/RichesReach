# scores_pipeline.py
from __future__ import annotations
import pandas as pd
import numpy as np
from typing import Callable, Dict, Optional, Sequence
from datetime import datetime

# Self-identifying build tag
SCORING_BUILD = datetime.now().isoformat(timespec="seconds")

# =========================
# Config (tune as needed)
# =========================
BEGINNER_WEIGHTS: Dict[str, float] = {
    "market_cap": 0.30,
    "volatility": 0.20,
    "sector":     0.20,  # sector stability heuristic
    "peRatio":    0.15,
    "dividendYield": 0.10,
    "liquidity":  0.05,
}
BEGINNER_FLOORS = {
    "mega_cap": (1e12, 85),  # (cap, min score)
    "large_cap": (5e11, 75),
}

ML_WEIGHTS: Dict[str, float] = {
    "peRatio":       0.20,
    "revenueGrowth": 0.25,
    "profitMargin":  0.20,
    "debtToEquity":  0.15,
    "returnOnEquity":0.10,
    "currentRatio":  0.05,
    "priceToBook":   0.05,
}
SECTOR_MULT_BOUNDS = (0.5, 1.5)  # clamp sector multiplier


# =========================
# Helpers
# =========================
def _clamp(x: float, lo: float = 0.0, hi: float = 100.0) -> float:
    return float(max(lo, min(hi, x)))

def _zscore_sector(df: pd.DataFrame, cols: Sequence[str], sector_col: str) -> pd.DataFrame:
    out = df.copy()
    for c in cols:
        zname = f"{c}_z"
        def _z(s: pd.Series) -> pd.Series:
            mu = s.mean()
            sd = s.std(ddof=0)
            if sd is None or sd == 0 or (isinstance(sd, float) and np.isnan(sd)):
                sd = 1.0
            return (s - mu) / sd
        out[zname] = out.groupby(sector_col)[c].transform(_z)
    return out

def _z_to_score(z: float, slope: float = 1.0) -> float:
    """Logistic map of z-score to 0..100 (robust to outliers)."""
    return float(np.round(100.0 / (1.0 + np.exp(-slope * z)), 1))

def _apply_floors(score: float, market_cap: float) -> float:
    mega_cap, mega_floor = BEGINNER_FLOORS["mega_cap"]
    large_cap, large_floor = BEGINNER_FLOORS["large_cap"]
    if market_cap >= mega_cap:
        return max(score, mega_floor)
    if market_cap >= large_cap:
        return max(score, large_floor)
    return score


# =========================
# Public API
# =========================
def score_pipeline(
    df: pd.DataFrame,
    *,
    sector_col: str = "sector",
    symbol_col: str = "symbol",
    # Beginner inputs
    beginner_features: Sequence[str] = ("market_cap", "volatility", "peRatio", "dividendYield", "liquidity"),
    sector_beginner_fn: Optional[Callable[[pd.Series], float]] = None,
    # ML inputs
    ml_features: Sequence[str] = ("peRatio","revenueGrowth","profitMargin","debtToEquity","returnOnEquity","currentRatio","priceToBook"),
    sector_ml_multiplier_fn: Optional[Callable[[pd.Series], float]] = None,
    # Options
    logistic_slope: float = 1.0,
    return_breakdowns: bool = False,
) -> pd.DataFrame:
    """
    Compute BOTH beginner_score and ml_score cross-sectionally (sector-relative).

    Required columns:
      - symbol_col (default: 'symbol')
      - sector_col (default: 'sector')
      - beginner_features and ml_features listed above

    Optional callouts:
      - sector_beginner_fn(row)    -> 0..100 sector stability heuristic for beginner score
      - sector_ml_multiplier_fn(row)-> sector multiplier for ML score (clamped to SECTOR_MULT_BOUNDS)
    """
    missing_cols = {sector_col, symbol_col} | set(beginner_features) | set(ml_features)
    missing_cols = [c for c in missing_cols if c not in df.columns]
    if missing_cols:
        raise ValueError(f"Missing required columns: {missing_cols}")

    work = df.copy()

    # -------- Beginner (cross-sectional) --------
    b_cols = list(beginner_features)
    work = _zscore_sector(work, b_cols, sector_col)
    for c in b_cols:
        work[f"{c}_score_beg"] = work[f"{c}_z"].apply(lambda z: _z_to_score(z, logistic_slope))

    # sector heuristic (0..100). If none provided, default neutral 60.
    if sector_beginner_fn:
        work["sector_score_beg"] = work.apply(sector_beginner_fn, axis=1).clip(0, 100)
    else:
        work["sector_score_beg"] = 60.0

    # weighted sum
    work["beginner_score_raw"] = (
        work["market_cap_score_beg"] * BEGINNER_WEIGHTS["market_cap"]
        + work["volatility_score_beg"] * BEGINNER_WEIGHTS["volatility"]
        + work["sector_score_beg"]     * BEGINNER_WEIGHTS["sector"]
        + work["peRatio_score_beg"]    * BEGINNER_WEIGHTS["peRatio"]
        + work["dividendYield_score_beg"] * BEGINNER_WEIGHTS["dividendYield"]
        + work["liquidity_score_beg"]  * BEGINNER_WEIGHTS["liquidity"]
    )

    # floors for big caps
    work["beginner_score"] = pd.Series(
        [_clamp(_apply_floors(s, mc)) for s, mc in zip(
            work["beginner_score_raw"].to_numpy(), work["market_cap"].to_numpy()
        )],
        index=work.index,
    ).clip(0, 100).round(0).astype(int)

    # -------- ML (cross-sectional) --------
    m_cols = list(ml_features)
    work = _zscore_sector(work, m_cols, sector_col)
    # weighted z-sum
    zsum = np.zeros(len(work))
    for c in m_cols:
        w = ML_WEIGHTS.get(c, 0.0)
        if w == 0.0:  # ignore unweighted
            continue
        zsum += work[f"{c}_z"].fillna(0).to_numpy() * w

    # sector multiplier (bounded)
    if sector_ml_multiplier_fn:
        sec_mult = work.apply(sector_ml_multiplier_fn, axis=1).astype(float)
    else:
        sec_mult = pd.Series(1.0, index=work.index)
    sec_mult = sec_mult.clip(SECTOR_MULT_BOUNDS[0], SECTOR_MULT_BOUNDS[1])

    # map to 0..100 and apply multiplier, then clamp
    work["ml_score_raw"] = pd.Series([_z_to_score(z, logistic_slope) for z in zsum], index=work.index)
    work["ml_score"] = (work["ml_score_raw"] * sec_mult).clip(0, 100).round(1)

    # -------- Output shaping --------
    cols_out = [symbol_col, sector_col, "beginner_score", "ml_score"]
    if return_breakdowns:
        # include useful breakdown columns
        beg_parts = [
            "market_cap_score_beg","volatility_score_beg","sector_score_beg",
            "peRatio_score_beg","dividendYield_score_beg","liquidity_score_beg",
            "beginner_score_raw"
        ]
        ml_parts = [f"{c}_z" for c in m_cols] + ["ml_score_raw"]
        cols_out.extend(beg_parts + ml_parts)

    return work[cols_out].copy()
