import numpy as np
import pandas as pd
from quant.optimizer import mean_variance_tc

def test_optimizer_turnover_cap():
    tickers = ["A","B","C"]
    mu = pd.Series([0.1,0.08,0.06], index=tickers)
    cov = np.eye(3)*0.04
    prev = pd.Series([1.0,0,0], index=tickers)
    sec = pd.Series(["X","X","Y"], index=tickers)
    tc = pd.Series([0.001,0.001,0.001], index=tickers)

    w = mean_variance_tc(mu, cov, prev, sec, tc, 0.8, 0.9, 0.05)
    assert np.abs(w.sum()-1)<1e-6
    # turnover <= 10% by constraint
    assert (np.abs(w-prev).sum()/2) <= 0.05 + 1e-6
