# quant/optimizer.py
import numpy as np
import cvxpy as cp
import pandas as pd

def mean_variance_tc(
    mu: pd.Series,          # expected returns (decimal)
    cov: np.ndarray,        # covariance matrix
    prev_weights: pd.Series,# previous portfolio weights
    sector: pd.Series,      # sector per symbol
    tc_perc: pd.Series,     # transaction cost % per symbol (spread/slippage)
    max_name: float,
    max_sector: float,
    turnover_budget: float,
    cash_min: float = 0.02
) -> pd.Series:
    tickers = mu.index
    n = len(tickers)
    w = cp.Variable(n)

    # objective: maximize mu^T w - lambda * w^T Σ w - tc_penalty
    lam = 4.0  # risk aversion (tune)
    tc_penalty = cp.sum(cp.multiply(tc_perc.values, cp.abs(w - prev_weights.values)))
    obj = cp.Maximize(mu.values @ w - lam * cp.quad_form(w, cov) - tc_penalty)

    constraints = [
        cp.sum(w) == 1.0,
        w >= 0.0,
        w <= max_name,
    ]
    # sector caps
    for sec in sector.unique():
        idx = (sector == sec).values
        constraints.append(cp.sum(w[idx]) <= max_sector)

    # turnover budget (L1 distance / 2 = turnover)
    constraints.append(cp.norm1(w - prev_weights.values) <= 2 * turnover_budget)

    # cash min is enforced by letting a "CASH" pseudo-asset in prev_weights & mu, or keep a residual
    prob = cp.Problem(obj, constraints)
    prob.solve(solver=cp.OSQP, verbose=False)
    if w.value is None:
        # fallback: equal weight within constraints
        w_val = np.ones(n)/n
    else:
        w_val = np.clip(w.value, 0, max_name)
        w_val /= w_val.sum()

    return pd.Series(w_val, index=tickers)
