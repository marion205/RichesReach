# quant/factors.py
import numpy as np
import pandas as pd

def zscore(s: pd.Series) -> pd.Series:
    return (s - s.mean()) / (s.std(ddof=0) + 1e-9)

def compute_factors(df: pd.DataFrame) -> pd.DataFrame:
    """
    df columns (per symbol):
      mcap, pe, pb, roe, gross_margin, vol_60d, ret_12m, ret_1m
    Returns standardized factors: size, value, quality, momentum, low_vol
    """
    out = pd.DataFrame(index=df.index)
    out["size"] = -zscore(np.log1p(df["mcap"]))                # smaller = positive "size" exposure
    value_proxy = (1/df["pe"].replace(0, np.nan)) + (1/df["pb"].replace(0, np.nan))
    out["value"] = zscore(value_proxy.fillna(value_proxy.median()))
    quality_proxy = df["roe"] + df["gross_margin"]
    out["quality"] = zscore(quality_proxy.fillna(quality_proxy.median()))
    momentum_proxy = df["ret_12m"] - df["ret_1m"]              # 12-1 momentum
    out["momentum"] = zscore(momentum_proxy.fillna(0))
    out["low_vol"] = zscore(-df["vol_60d"])                    # lower vol is better
    return out

def blend_signal(factors: pd.DataFrame, weights: dict[str, float]) -> pd.Series:
    w = pd.Series(weights).reindex(factors.columns).fillna(0.0)
    s = (factors * w).sum(axis=1)
    return zscore(s)
