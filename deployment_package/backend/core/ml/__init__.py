"""
RichesReach Production ML Pipeline
====================================
Walk-forward, leakage-resistant stock return prediction pipeline.

Quick start
-----------
from deployment_package.backend.core.ml.train import run_pipeline

results, model = run_pipeline(
    tickers=["AAPL", "MSFT", "GOOGL", "AMZN", "NVDA"],
    start_date="2019-01-01",
    n_splits=4,
)
print(results)   # fold-by-fold R², IC, decile spread
"""

from .train import run_pipeline  # noqa: F401

__all__ = ["run_pipeline"]
