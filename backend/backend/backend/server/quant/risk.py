# quant/risk.py
import numpy as np
import pandas as pd

def shrink_cov(returns: pd.DataFrame, shrink=0.1) -> np.ndarray:
    cov = returns.cov().values
    avg_var = np.trace(cov)/cov.shape[0]
    I = np.eye(cov.shape[0])
    return (1 - shrink)*cov + shrink*avg_var*I

def ex_ante_vol(weights: np.ndarray, cov: np.ndarray) -> float:
    return float(np.sqrt(weights @ cov @ weights) * np.sqrt(252))

def factor_exposures(weights: pd.Series, factor_loads: pd.DataFrame) -> pd.Series:
    # Weighted average exposure
    return (factor_loads.T @ weights).fillna(0.0)

def stress_scenarios(prices_now: pd.Series) -> dict:
    # simple stresses
    return {
        "market_-10pct": -0.10 * float(prices_now.sum()),
        "rates_+100bps": -0.02 * float(prices_now.sum()),   # crude proxy
    }
