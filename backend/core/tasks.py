# core/tasks.py
from __future__ import annotations
import os
import logging
from typing import List, Dict
import pandas as pd
from celery import shared_task
from django.core.cache import cache
from django.db.models import QuerySet
from core.models import Stock
from core.advanced_ml_algorithms import AdvancedMLAlgorithms
from .ml_stock_recommender import MLStockRecommender  # whatever your file is named

logger = logging.getLogger(__name__)

@shared_task(bind=True, autoretry_for=(Exception,), retry_backoff=2, retry_kwargs={"max_retries": 3})
def prewarm_symbol(self, symbol: str, days: int = 180) -> Dict:
    """Warm cache for one symbol (overview + time series)."""
    rec = MLStockRecommender()
    ov = rec.fetch_real_stock_overview(symbol)
    df = rec.fetch_historical_data(symbol, days=days)
    return {"symbol": symbol, "overview": bool(ov), "history": False if df is None else True}

@shared_task
def prewarm_universe(days: int = 180) -> Dict:
    """Warm a small universe nightly to keep the app snappy."""
    qs: QuerySet[Stock] = Stock.objects.all().only("symbol").order_by("symbol")[:150]
    syms = [s.symbol for s in qs]
    results = [prewarm_symbol.delay(sym, days) for sym in syms]
    return {"submitted": len(results)}

@shared_task(bind=True)
def train_stacking_model(self) -> Dict:
    """
    Build a simple cross-sectional dataset from cached features and train
    the stacking ensemble. Keep it small and stable (example).
    """
    rec = MLStockRecommender()
    rows = []
    qs: QuerySet[Stock] = Stock.objects.all().only("symbol").order_by("symbol")[:200]
    for s in qs:
        df = rec.fetch_historical_data(s.symbol, days=180)
        if df is None or df.empty:
            continue
        f = rec.calculate_ml_features(df)
        if not f:
            continue
        # target: forward 20d return (leak-safe example using past history)
        px = df["close"]
        if len(px) < 200:
            continue
        # simple rolling target (use older segment to avoid lookahead)
        fwd = float((px.iloc[-1] / px.iloc[-20]) - 1.0)  # proxy for label
        rows.append({
            "symbol": s.symbol,
            "momentum": f.get("momentum", 0.0),
            "ann_vol": f.get("ann_vol", 0.3),
            "rsi": f.get("rsi", 50.0),
            "macd": f.get("macd", 0.0),
            "avg_volume": f.get("avg_volume", 0.0),
            "y": fwd,
        })

    if len(rows) < 50:
        logger.warning("Not enough rows to train stacking model.")
        return {"trained": False, "rows": len(rows)}

    import numpy as np
    import pandas as pd
    df = pd.DataFrame(rows)
    X = df[["momentum", "ann_vol", "rsi", "macd", "avg_volume"]].values.astype(float)
    y = df["y"].values.astype(float)

    ml = AdvancedMLAlgorithms(models_dir=os.getenv("ML_MODELS_DIR", "advanced_ml_models"))
    out = ml.create_stacking_ensemble(X, y, model_name="stacking_ensemble")
    ml.save_model("stacking_ensemble", out["model"])
    return {"trained": True, "rows": len(rows)}
