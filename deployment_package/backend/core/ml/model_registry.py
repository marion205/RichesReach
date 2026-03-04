"""
model_registry.py
=================
Save, load, and serve the production ML model with feature-schema versioning.

Design goals
------------
* A saved bundle always includes the feature schema (column names + order)
  so inference time can validate inputs and catch schema drift.
* Models are saved alongside a human-readable metadata dict (trained_at,
  fold metrics, feature count) so you can audit what's running in prod.
* Inference is a single function call: ModelRegistry.predict(ticker_df)
  → returns a raw vol-adjusted return prediction.

Storage layout
--------------
The model is stored in the existing ml_models/ directory alongside the
day_trading_predictor.pkl files:

    deployment_package/backend/core/ml_models/
        production_r2.pkl   ← the bundle this module manages
        day_trading_predictor.pkl
        ...

Bundle schema
-------------
    {
        "model": <lgbm.LGBMRegressor>,
        "feature_names": ["mom_21d", "mom_63d", ...],   # from features.FEATURE_NAMES
        "trained_at": "2024-03-04T12:00:00",
        "model_type": "lgbm",
        "horizon": 20,
        "fold_metrics": {...},     # mean R², IC, decile spread across CV folds
        "n_tickers": 50,
        "n_rows": 12000,
    }
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd

from .features import build_features, FEATURE_NAMES

logger = logging.getLogger(__name__)

# Canonical path: sits alongside the existing day_trading_predictor.pkl
_MODEL_DIR = Path(__file__).parent.parent / "ml_models"
_DEFAULT_NAME = "production_r2"


class ModelRegistry:
    """Save, load, and serve the production LightGBM model."""

    # ------------------------------------------------------------------
    # Save
    # ------------------------------------------------------------------

    @staticmethod
    def save(
        model: Any,
        feature_names: list[str] | None = None,
        name: str = _DEFAULT_NAME,
        horizon: int = 20,
        fold_metrics: dict | None = None,
        n_tickers: int = 0,
        n_rows: int = 0,
    ) -> Path:
        """
        Persist the trained model and its feature schema.

        Parameters
        ----------
        model : Any
            Fitted LGBMRegressor (or any sklearn-compatible regressor).
        feature_names : list[str] | None
            Column names the model was trained on.  Defaults to FEATURE_NAMES.
        name : str
            Filename stem (without .pkl).
        horizon : int
            The forward-return horizon the model was trained for.
        fold_metrics : dict | None
            Summary statistics from walk-forward CV (r2, ic, etc.).
        n_tickers, n_rows : int
            Training dataset size info for the metadata record.

        Returns
        -------
        Path to the saved .pkl file.
        """
        _MODEL_DIR.mkdir(parents=True, exist_ok=True)
        path = _MODEL_DIR / f"{name}.pkl"

        bundle = {
            "model": model,
            "feature_names": feature_names or FEATURE_NAMES,
            "trained_at": datetime.now(timezone.utc).isoformat(),
            "model_type": type(model).__name__,
            "horizon": horizon,
            "fold_metrics": fold_metrics or {},
            "n_tickers": n_tickers,
            "n_rows": n_rows,
        }

        joblib.dump(bundle, path)
        logger.info("ModelRegistry.save: wrote %s (%.1f MB)", path, path.stat().st_size / 1e6)
        return path

    # ------------------------------------------------------------------
    # Load
    # ------------------------------------------------------------------

    @staticmethod
    def load(name: str = _DEFAULT_NAME) -> dict:
        """
        Load a saved model bundle.

        Returns
        -------
        dict with keys: model, feature_names, trained_at, model_type, horizon, fold_metrics
        """
        path = _MODEL_DIR / f"{name}.pkl"
        if not path.exists():
            raise FileNotFoundError(
                f"No model found at {path}.  "
                "Run ml.train.run_pipeline() first to train and save the model."
            )
        bundle = joblib.load(path)
        logger.debug(
            "ModelRegistry.load: loaded %s (trained_at=%s)", name, bundle.get("trained_at")
        )
        return bundle

    # ------------------------------------------------------------------
    # Predict
    # ------------------------------------------------------------------

    @staticmethod
    def predict(
        ticker_df: pd.DataFrame,
        name: str = _DEFAULT_NAME,
    ) -> float:
        """
        Make a prediction for a single ticker using the saved model.

        Parameters
        ----------
        ticker_df : pd.DataFrame
            Recent OHLCV history for the ticker (ideally 252+ rows).
            Must include columns: open, high, low, close, volume.
            Optionally: spy_close, qqq_close (for cross-asset features).

        Returns
        -------
        float
            Vol-adjusted predicted forward return.  Typical range: ±2.0.
            Positive = bullish signal, negative = bearish signal.
            Map to 0-10 score: score = max(0, min(10, 5 + pred * 2.5))
        """
        bundle = ModelRegistry.load(name)
        model = bundle["model"]
        expected_features = bundle["feature_names"]

        # Build full feature matrix, take only the most recent row
        feat = build_features(ticker_df)

        # Validate feature schema
        missing = [f for f in expected_features if f not in feat.columns]
        if missing:
            raise ValueError(f"ModelRegistry.predict: missing features: {missing}")

        X = feat[expected_features].iloc[[-1]]  # shape (1, n_features)

        if X.isnull().any(axis=1).values[0]:
            n_null = X.isnull().sum().sum()
            logger.warning(
                "ModelRegistry.predict: %d feature(s) are NaN on the most recent row — "
                "model will use LightGBM's native NaN handling", n_null
            )

        pred = model.predict(X)
        return float(pred[0])

    # ------------------------------------------------------------------
    # Metadata
    # ------------------------------------------------------------------

    @staticmethod
    def metadata(name: str = _DEFAULT_NAME) -> dict:
        """Return the bundle metadata without loading the full model object."""
        bundle = ModelRegistry.load(name)
        return {k: v for k, v in bundle.items() if k != "model"}

    @staticmethod
    def exists(name: str = _DEFAULT_NAME) -> bool:
        """Check whether a saved model exists."""
        return (_MODEL_DIR / f"{name}.pkl").exists()
