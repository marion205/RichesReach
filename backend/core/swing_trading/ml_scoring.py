"""
ML-based Signal Scoring and Pattern Recognition for Swing Trading
Professional implementation: leakage-safe, calibrated probabilities, consistent feature schema,
time-series validation, and ensemble blending.
"""

from __future__ import annotations

import os
import logging
from dataclasses import dataclass, asdict
from typing import Dict, List, Tuple, Optional, Any

import numpy as np
import pandas as pd
from sklearn.base import BaseEstimator
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.model_selection import TimeSeriesSplit
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.calibration import CalibratedClassifierCV
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score, roc_auc_score
)
import joblib

# Optional: silence benign sklearn warnings in prod logs
import warnings
warnings.filterwarnings("ignore")

# If you have these utilities, you can plug them in; they are optional here.
# from .indicators import calculate_all_indicators, validate_ohlcv_data

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

RANDOM_SEED = 42
np.random.seed(RANDOM_SEED)


# ----------------------------- Utilities -----------------------------

def _require_cols(df: pd.DataFrame, cols: List[str]) -> List[str]:
    missing = [c for c in cols if c not in df.columns]
    if missing:
        logger.warning(f"Missing required columns: {missing}")
    return missing


def _forward_max(series: pd.Series, n: int) -> pd.Series:
    # Max of next n periods EXCLUDING current bar
    return series.shift(-1)[::-1].rolling(n, min_periods=1).max()[::-1]


def _forward_min(series: pd.Series, n: int) -> pd.Series:
    return series.shift(-1)[::-1].rolling(n, min_periods=1).min()[::-1]


def _safe_pct(x: float) -> float:
    try:
        return float(x)
    except Exception:
        return 0.0


# ----------------------------- Data Artifacts -----------------------------

@dataclass
class FeatureSchema:
    feature_names: List[str]
    lookforward_days: int
    long_profit_threshold: float
    short_profit_threshold: float

@dataclass
class ModelReport:
    accuracy: float
    precision: float
    recall: float
    f1: float
    roc_auc: float

@dataclass
class EnsembleWeights:
    random_forest: float = 0.4
    gradient_boosting: float = 0.4
    logistic_regression: float = 0.2

# ----------------------------- Core Class -----------------------------

class SwingTradingML:
    """
    Leakage-safe ML for swing trading signals with calibrated probabilities and consistent feature schema.
    """

    def __init__(
        self,
        model_dir: str = "ml_models",
        lookforward_days: int = 5,
        long_profit_threshold: float = 0.02,   # +2% within horizon => 1
        short_profit_threshold: float = 0.02,  # -2% within horizon => 1 for short target (optional)
        use_stacker: bool = False
    ) -> None:
        self.model_dir = model_dir
        os.makedirs(self.model_dir, exist_ok=True)

        self.lookforward_days = lookforward_days
        self.long_profit_threshold = long_profit_threshold
        self.short_profit_threshold = short_profit_threshold
        self.use_stacker = use_stacker

        self._models: Dict[str, BaseEstimator] = {}
        self._reports: Dict[str, ModelReport] = {}
        self._schema: Optional[FeatureSchema] = None
        self._weights = EnsembleWeights()

        self._init_models()

    def _init_models(self) -> None:
        # Trees don't need scaling; linear model benefits from scaling.
        rf = RandomForestClassifier(
            n_estimators=300,
            max_depth=10,
            min_samples_split=5,
            min_samples_leaf=2,
            class_weight="balanced",
            random_state=RANDOM_SEED,
            n_jobs=-1,
        )
        gb = GradientBoostingClassifier(
            n_estimators=200,
            learning_rate=0.05,
            max_depth=3,
            random_state=RANDOM_SEED,
        )
        lr = Pipeline([
            ("scaler", StandardScaler(with_mean=True, with_std=True)),
            ("clf", LogisticRegression(
                max_iter=2000,
                class_weight="balanced",
                random_state=RANDOM_SEED
            ))
        ])

        # Calibrate probabilities (sigmoid) using cross-validation folds
        self._models["random_forest"] = CalibratedClassifierCV(rf, cv=3, method="sigmoid")
        self._models["gradient_boosting"] = CalibratedClassifierCV(gb, cv=3, method="sigmoid")
        self._models["logistic_regression"] = CalibratedClassifierCV(lr, cv=3, method="sigmoid")
        logger.info("Initialized calibrated models.")

    # ----------------------------- Feature Engineering -----------------------------

    def extract_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Build engineered features. Assumes df has: open, high, low, close, volume and
        indicator columns like ema_12, ema_26, rsi_14, atr_14, volume_sma_20, macd, macd_signal,
        bb_upper, bb_lower, bb_middle, stoch_k, support, resistance.
        """
        req = ["open", "high", "low", "close", "volume"]
        missing = _require_cols(df, req)
        if missing:
            raise ValueError(f"extract_features: missing {missing}")

        f = pd.DataFrame(index=df.index)

        # Basic price/volatility
        f["price_change_1"] = df["close"].pct_change()
        f["price_change_2"] = df["close"].pct_change(2)
        f["price_change_5"] = df["close"].pct_change(5)
        f["hl_ratio"] = (df["high"] / df["low"]).replace([np.inf, -np.inf], np.nan)
        f["co_ratio"] = (df["close"] / df["open"]).replace([np.inf, -np.inf], np.nan)

        f["vol_std_5"] = df["close"].rolling(5).std()
        f["vol_std_20"] = df["close"].rolling(20).std()

        if "atr_14" in df.columns:
            f["atr_ratio"] = df["atr_14"] / df["close"]
        else:
            f["atr_ratio"] = np.nan

        # Volume features
        f["vol_change_1"] = df["volume"].pct_change()
        f["vpt"] = df["volume"] * f["price_change_1"]
        f["vol_surge"] = (df["volume"] / df.get("volume_sma_20", df["volume"].rolling(20).mean())).replace([np.inf, -np.inf], np.nan)

        # RSI / EMA / MACD
        rsi = df.get("rsi_14")
        if rsi is not None:
            f["rsi"] = rsi
            f["rsi_oversold"] = (rsi < 30).astype(int)
            f["rsi_overbought"] = (rsi > 70).astype(int)
            f["rsi_neutral"] = ((rsi >= 40) & (rsi <= 60)).astype(int)
        else:
            f["rsi"] = np.nan
            f["rsi_oversold"] = 0
            f["rsi_overbought"] = 0
            f["rsi_neutral"] = 0

        ema12, ema26 = df.get("ema_12"), df.get("ema_26")
        if ema12 is not None and ema26 is not None:
            f["ema_bull"] = (ema12 > ema26).astype(int)
            f["ema_bear"] = (ema12 < ema26).astype(int)
            f["ema_cross_up"] = ((ema12 > ema26) & (ema12.shift(1) <= ema26.shift(1))).astype(int)
            f["ema_cross_dn"] = ((ema12 < ema26) & (ema12.shift(1) >= ema26.shift(1))).astype(int)
        else:
            f["ema_bull"] = f["ema_bear"] = f["ema_cross_up"] = f["ema_cross_dn"] = 0

        macd, macd_sig = df.get("macd"), df.get("macd_signal")
        if macd is not None and macd_sig is not None:
            f["macd_gt"] = (macd > macd_sig).astype(int)
            f["macd_lt"] = (macd < macd_sig).astype(int)
            f["macd_cross"] = ((macd > macd_sig) & (macd.shift(1) <= macd_sig.shift(1))).astype(int)
        else:
            f["macd_gt"] = f["macd_lt"] = f["macd_cross"] = 0

        # Bollinger / Stoch
        if {"bb_upper", "bb_lower", "bb_middle"}.issubset(df.columns):
            width = (df["bb_upper"] - df["bb_lower"]) / df["bb_middle"].replace(0, np.nan)
            f["bb_squeeze"] = (width < 0.1).astype(int)
            f["bb_break_up"] = (df["close"] > df["bb_upper"]).astype(int)
            f["bb_break_dn"] = (df["close"] < df["bb_lower"]).astype(int)
        else:
            f["bb_squeeze"] = f["bb_break_up"] = f["bb_break_dn"] = 0

        stoch_k = df.get("stoch_k")
        if stoch_k is not None:
            f["stoch_oversold"] = (stoch_k < 20).astype(int)
            f["stoch_overbought"] = (stoch_k > 80).astype(int)
        else:
            f["stoch_oversold"] = f["stoch_overbought"] = 0

        # Support/Resistance markers if present (boolean-like)
        f["near_support"] = df.get("support", 0).astype(int) if "support" in df.columns else 0
        f["near_resistance"] = df.get("resistance", 0).astype(int) if "resistance" in df.columns else 0

        # Time encodings (minimal leakage risk)
        idx = pd.to_datetime(df.index)
        f["dow"] = idx.dayofweek
        f["month"] = idx.month
        f["month_end"] = (idx.day > 25).astype(int)

        # Lag & rolling stats
        for lag in (1, 2, 3, 5):
            f[f"rsi_lag_{lag}"] = f["rsi"].shift(lag)
            f[f"vol_lag_{lag}"] = df["volume"].shift(lag)
            f[f"ret_lag_{lag}"] = f["price_change_1"].shift(lag)

        for window in (5, 10, 20):
            f[f"rsi_mean_{window}"] = f["rsi"].rolling(window).mean()
            f[f"vol_mean_{window}"] = df["volume"].rolling(window).mean()
            f[f"volat_{window}"] = df["close"].rolling(window).std()

        f = f.replace([np.inf, -np.inf], np.nan).fillna(0.0)
        return f

    # ----------------------------- Targets -----------------------------

    def create_targets(
        self,
        df: pd.DataFrame,
        lookforward_days: Optional[int] = None,
        long_profit_threshold: Optional[float] = None,
        short_profit_threshold: Optional[float] = None,
    ) -> pd.DataFrame:
        """
        Create long/short targets using forward rolling windows, excluding current bar.
        Returns a DataFrame with:
          - target_long (1 if future max >= +threshold)
          - target_short (1 if future min <= -threshold)
          - target (defaults to long for training unless you handle separately)
        """
        lf = lookforward_days or self.lookforward_days
        long_thr = long_profit_threshold or self.long_profit_threshold
        short_thr = short_profit_threshold or self.short_profit_threshold

        if "close" not in df.columns:
            raise ValueError("create_targets requires 'close' column")

        future_max = _forward_max(df["close"], lf)
        future_min = _forward_min(df["close"], lf)

        ret_to_max = (future_max / df["close"]) - 1.0
        ret_to_min = (future_min / df["close"]) - 1.0

        target_long = (ret_to_max >= long_thr).astype(int)
        target_short = (ret_to_min <= -short_thr).astype(int)

        # Primary target (long) by default; you can train separate short model if desired.
        target = target_long.copy()

        return pd.DataFrame(
            {
                "target": target,
                "target_long": target_long,
                "target_short": target_short,
            },
            index=df.index,
        )

    # ----------------------------- Training -----------------------------

    def _build_dataset(
        self, features: pd.DataFrame, targets: pd.Series
    ) -> Tuple[pd.DataFrame, pd.Series]:
        # Align and drop NaNs in target
        X = features.copy()
        y = targets.reindex(X.index)
        mask = (~y.isna())
        X = X[mask].astype(float)
        y = y[mask].astype(int)
        return X, y

    def train(self, df: pd.DataFrame) -> None:
        """
        Train all models with time-series validation and persist artifacts.
        df must include OHLCV (+ indicators). Index must be chronological.
        """
        # if validate_ohlcv_data:
        #     validate_ohlcv_data(df)

        features = self.extract_features(df)
        t = self.create_targets(df)
        X, y = self._build_dataset(features, t["target"])

        if len(X) < 300:
            logger.warning(f"Insufficient samples ({len(X)}) to train robust models.")
            return

        # Persist feature schema for future inference
        self._schema = FeatureSchema(
            feature_names=list(X.columns),
            lookforward_days=self.lookforward_days,
            long_profit_threshold=self.long_profit_threshold,
            short_profit_threshold=self.short_profit_threshold,
        )

        # TimeSeriesSplit evaluation; keep the last split as holdout-ish
        tscv = TimeSeriesSplit(n_splits=5)
        reports: Dict[str, ModelReport] = {}
        fitted: Dict[str, BaseEstimator] = {}

        for name, model in self._models.items():
            fold_preds, fold_truth = [], []
            last_train_idx, last_test_idx = None, None

            for train_idx, test_idx in tscv.split(X):
                X_train, X_test = X.iloc[train_idx], X.iloc[test_idx]
                y_train, y_test = y.iloc[train_idx], y.iloc[test_idx]

                m = model
                m.fit(X_train, y_train)
                proba = m.predict_proba(X_test)[:, 1]
                preds = (proba >= 0.5).astype(int)

                fold_preds.append((preds, proba))
                fold_truth.append(y_test.values)

                last_train_idx, last_test_idx = train_idx, test_idx

            # Aggregate metrics across folds
            y_true_all = np.concatenate(fold_truth)
            y_pred_all = np.concatenate([p for p, _ in fold_preds])
            y_proba_all = np.concatenate([pr for _, pr in fold_preds])

            rep = ModelReport(
                accuracy=float(accuracy_score(y_true_all, y_pred_all)),
                precision=float(precision_score(y_true_all, y_pred_all, zero_division=0)),
                recall=float(recall_score(y_true_all, y_pred_all, zero_division=0)),
                f1=float(f1_score(y_true_all, y_pred_all, zero_division=0)),
                roc_auc=float(roc_auc_score(y_true_all, y_proba_all)),
            )
            reports[name] = rep

            # Refit on all data for production
            model.fit(X, y)
            fitted[name] = model

            logger.info(
                f"[{name}] acc={rep.accuracy:.3f} f1={rep.f1:.3f} "
                f"prec={rep.precision:.3f} rec={rep.recall:.3f} auc={rep.roc_auc:.3f}"
            )

        self._reports = reports
        self._models = fitted
        self._save_artifacts()

    # ----------------------------- Inference -----------------------------

    def _ensure_schema(self) -> None:
        if not self._schema:
            self._load_artifacts()
        if not self._schema:
            raise RuntimeError("No feature schema available; train() or load artifacts first.")

    def predict_proba_row(self, feature_row: Dict[str, float]) -> Dict[str, float]:
        """
        Predict probabilities for a single observation (dict of feature_name -> value).
        Returns per-model probabilities and 'ensemble'.
        """
        self._ensure_schema()
        assert self._schema is not None

        # Build ordered vector
        vec = np.array([_safe_pct(feature_row.get(c, 0.0)) for c in self._schema.feature_names], dtype=float).reshape(1, -1)

        out: Dict[str, float] = {}
        for name, model in self._models.items():
            try:
                proba = float(model.predict_proba(vec)[:, 1][0])
            except Exception as e:
                logger.error(f"predict_proba_row [{name}] failed: {e}")
                proba = 0.0
            out[name] = proba

        # Weighted ensemble
        w = self._weights
        out["ensemble"] = (
            out.get("random_forest", 0.0) * w.random_forest +
            out.get("gradient_boosting", 0.0) * w.gradient_boosting +
            out.get("logistic_regression", 0.0) * w.logistic_regression
        )
        return out

    def predict_proba_df(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Vectorized prediction for a feature DataFrame (same schema used at train time).
        Returns a DataFrame with per-model columns and 'ensemble'.
        """
        self._ensure_schema()
        assert self._schema is not None

        # Align and fill missing columns in correct order
        X = df.reindex(columns=self._schema.feature_names, fill_value=0.0).astype(float)
        probs = pd.DataFrame(index=X.index)

        for name, model in self._models.items():
            try:
                probs[name] = model.predict_proba(X)[:, 1]
            except Exception as e:
                logger.error(f"predict_proba_df [{name}] failed: {e}")
                probs[name] = 0.0

        w = self._weights
        probs["ensemble"] = (
            probs.get("random_forest", 0.0) * w.random_forest +
            probs.get("gradient_boosting", 0.0) * w.gradient_boosting +
            probs.get("logistic_regression", 0.0) * w.logistic_regression
        )
        return probs

    # ----------------------------- Pattern Detection -----------------------------

    def detect_swing_patterns(self, df: pd.DataFrame, symbol: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Lightweight detectors; safe with missing columns.
        """
        patterns: List[Dict[str, Any]] = []
        sym = symbol or (df.get("symbol")[0] if "symbol" in df.columns else "UNKNOWN")

        # Volume surge + ±2% day move
        vol_surge = (df.get("volume", pd.Series(index=df.index, dtype=float)) /
                     df.get("volume_sma_20", df["volume"].rolling(20).mean())).fillna(0.0)
        price_chg = df["close"].pct_change().fillna(0.0).abs()

        mask = (vol_surge > 3.0) & (price_chg > 0.02)
        for ts in df.index[mask]:
            direction = "long" if df["close"].pct_change().loc[ts] > 0 else "short"
            patterns.append({
                "pattern_type": f"volume_surge_{direction}",
                "timestamp": ts,
                "symbol": sym,
                "confidence": float(min(0.85, vol_surge.loc[ts] / 4)),
                "features": {
                    "volume_surge": float(vol_surge.loc[ts]),
                    "price_change": float(df["close"].pct_change().loc[ts]),
                    "rsi_14": float(df.get("rsi_14", pd.Series(50, index=df.index)).loc[ts]),
                    "atr_14": float(df.get("atr_14", pd.Series(0, index=df.index)).loc[ts]),
                },
            })

        # EMA cross with volume
        ema12, ema26 = df.get("ema_12"), df.get("ema_26")
        if ema12 is not None and ema26 is not None:
            cross_up = (ema12 > ema26) & (ema12.shift(1) <= ema26.shift(1))
            vol_conf = vol_surge > 1.2
            for ts in df.index[cross_up & vol_conf]:
                patterns.append({
                    "pattern_type": "ema_crossover_long",
                    "timestamp": ts,
                    "symbol": sym,
                    "confidence": float(min(0.8, vol_surge.loc[ts] / 2)),
                    "features": {
                        "ema_12": float(ema12.loc[ts]), "ema_26": float(ema26.loc[ts]),
                        "volume_surge": float(vol_surge.loc[ts]),
                        "rsi_14": float(df.get("rsi_14", pd.Series(50, index=df.index)).loc[ts]),
                    },
                })
            cross_dn = (ema12 < ema26) & (ema12.shift(1) >= ema26.shift(1))
            for ts in df.index[cross_dn & vol_conf]:
                patterns.append({
                    "pattern_type": "ema_crossover_short",
                    "timestamp": ts,
                    "symbol": sym,
                    "confidence": float(min(0.8, vol_surge.loc[ts] / 2)),
                    "features": {
                        "ema_12": float(ema12.loc[ts]), "ema_26": float(ema26.loc[ts]),
                        "volume_surge": float(vol_surge.loc[ts]),
                        "rsi_14": float(df.get("rsi_14", pd.Series(50, index=df.index)).loc[ts]),
                    },
                })

        # RSI rebound (oversold/overbought) with volume
        rsi = df.get("rsi_14")
        if rsi is not None:
            oversold_cross = (rsi < 30) & (rsi.shift(1) >= 30) & (vol_surge > 1.5)
            for ts in df.index[oversold_cross]:
                patterns.append({
                    "pattern_type": "rsi_rebound_long",
                    "timestamp": ts,
                    "symbol": sym,
                    "confidence": float(min(0.9, (30 - rsi.loc[ts]) / 30 + 0.3)),
                    "features": {
                        "rsi_14": float(rsi.loc[ts]),
                        "volume_surge": float(vol_surge.loc[ts]),
                        "ema_trend": "bullish" if (ema12 is not None and ema26 is not None and ema12.loc[ts] > ema26.loc[ts]) else "bearish"
                    },
                })
            overbought_cross = (rsi > 70) & (rsi.shift(1) <= 70) & (vol_surge > 1.5)
            for ts in df.index[overbought_cross]:
                patterns.append({
                    "pattern_type": "rsi_rebound_short",
                    "timestamp": ts,
                    "symbol": sym,
                    "confidence": float(min(0.9, (rsi.loc[ts] - 70) / 30 + 0.3)),
                    "features": {
                        "rsi_14": float(rsi.loc[ts]),
                        "volume_surge": float(vol_surge.loc[ts]),
                        "ema_trend": "bullish" if (ema12 is not None and ema26 is not None and ema12.loc[ts] > ema26.loc[ts]) else "bearish"
                    },
                })

        # Bollinger breakout
        if {"bb_upper", "bb_lower"}.issubset(df.columns):
            up_break = (df["close"] > df["bb_upper"]) & (df["close"].shift(1) <= df["bb_upper"].shift(1)) & (vol_surge > 2.0)
            dn_break = (df["close"] < df["bb_lower"]) & (df["close"].shift(1) >= df["bb_lower"].shift(1)) & (vol_surge > 2.0)
            for ts in df.index[up_break]:
                patterns.append({
                    "pattern_type": "breakout_long",
                    "timestamp": ts,
                    "symbol": sym,
                    "confidence": float(min(0.9, vol_surge.loc[ts] / 3)),
                    "features": {
                        "close": float(df["close"].loc[ts]),
                        "bb_upper": float(df["bb_upper"].loc[ts]),
                        "volume_surge": float(vol_surge.loc[ts]),
                        "atr_14": float(df.get("atr_14", pd.Series(0, index=df.index)).loc[ts]),
                    },
                })
            for ts in df.index[dn_break]:
                patterns.append({
                    "pattern_type": "breakout_short",
                    "timestamp": ts,
                    "symbol": sym,
                    "confidence": float(min(0.9, vol_surge.loc[ts] / 3)),
                    "features": {
                        "close": float(df["close"].loc[ts]),
                        "bb_lower": float(df["bb_lower"].loc[ts]),
                        "volume_surge": float(vol_surge.loc[ts]),
                        "atr_14": float(df.get("atr_14", pd.Series(0, index=df.index)).loc[ts]),
                    },
                })

        logger.info(f"Detected {len(patterns)} swing patterns for {sym}.")
        return patterns

    # ----------------------------- Artifacts -----------------------------

    def _save_artifacts(self) -> None:
        os.makedirs(self.model_dir, exist_ok=True)
        # Models
        for name, model in self._models.items():
            joblib.dump(model, os.path.join(self.model_dir, f"{name}.joblib"))
        # Schema & reports
        if self._schema:
            joblib.dump(asdict(self._schema), os.path.join(self.model_dir, "feature_schema.joblib"))
        joblib.dump({k: asdict(v) for k, v in self._reports.items()}, os.path.join(self.model_dir, "reports.joblib"))
        joblib.dump(asdict(self._weights), os.path.join(self.model_dir, "weights.joblib"))
        logger.info("Saved models, schema, reports, and weights.")

    def _load_artifacts(self) -> None:
        try:
            loaded: Dict[str, BaseEstimator] = {}
            for name in ["random_forest", "gradient_boosting", "logistic_regression"]:
                path = os.path.join(self.model_dir, f"{name}.joblib")
                if os.path.exists(path):
                    loaded[name] = joblib.load(path)
            if loaded:
                self._models = loaded

            schema_path = os.path.join(self.model_dir, "feature_schema.joblib")
            if os.path.exists(schema_path):
                raw = joblib.load(schema_path)
                self._schema = FeatureSchema(**raw)

            reports_path = os.path.join(self.model_dir, "reports.joblib")
            if os.path.exists(reports_path):
                raw = joblib.load(reports_path)
                self._reports = {k: ModelReport(**v) for k, v in raw.items()}

            weights_path = os.path.join(self.model_dir, "weights.joblib")
            if os.path.exists(weights_path):
                self._weights = EnsembleWeights(**joblib.load(weights_path))

            logger.info("Loaded ML artifacts from disk.")
        except Exception as e:
            logger.error(f"Failed to load artifacts: {e}")


# ----------------------------- Scoring & Thesis (kept, tuned) -----------------------------

def generate_signal_score(features: Dict[str, float], pattern_type: str) -> float:
    """
    Heuristic score 0..1 to complement ML probability (for UI sorting / tie-breaks).
    """
    try:
        if pattern_type == "rsi_rebound_long":
            rsi = features.get("rsi_14", 50.0)
            vol = features.get("volume_surge", 1.0)
            trend = 0.2 if features.get("ema_trend") == "bullish" else 0.0
            rsi_score = max(0.0, (30 - rsi) / 30.0)
            vol_score = min(1.0, vol / 2.0)
            return float(np.clip(rsi_score * 0.5 + vol_score * 0.3 + trend, 0.0, 1.0))

        if pattern_type == "rsi_rebound_short":
            rsi = features.get("rsi_14", 50.0)
            vol = features.get("volume_surge", 1.0)
            trend = 0.2 if features.get("ema_trend") == "bearish" else 0.0
            rsi_score = max(0.0, (rsi - 70) / 30.0)
            vol_score = min(1.0, vol / 2.0)
            return float(np.clip(rsi_score * 0.5 + vol_score * 0.3 + trend, 0.0, 1.0))

        if pattern_type in {"ema_crossover_long", "ema_crossover_short"}:
            vol = features.get("volume_surge", 1.0)
            rsi = features.get("rsi_14", 50.0)
            vol_score = min(1.0, vol / 1.5)
            rsi_mid = 0.3 if 30 < rsi < 70 else 0.1
            return float(np.clip(vol_score * 0.6 + rsi_mid, 0.0, 1.0))

        if pattern_type in {"breakout_long", "breakout_short"}:
            vol = features.get("volume_surge", 1.0)
            close = features.get("close", 1.0)
            atr = features.get("atr_14", 0.0)
            vol_score = min(1.0, vol / 3.0)
            atr_score = min(1.0, (atr / close) * 100.0) if close > 0 else 0.0
            return float(np.clip(vol_score * 0.7 + atr_score * 0.3, 0.0, 1.0))

        if pattern_type in {"volume_surge_long", "volume_surge_short"}:
            vol = features.get("volume_surge", 1.0)
            pc = abs(features.get("price_change", 0.0))
            vol_score = min(1.0, vol / 4.0)
            price_score = min(1.0, pc * 50.0)
            return float(np.clip(vol_score * 0.6 + price_score * 0.4, 0.0, 1.0))

        return 0.0
    except Exception as e:
        logger.error(f"generate_signal_score error: {e}")
        return 0.0


def create_signal_thesis(pattern_type: str, features: Dict[str, float]) -> str:
    """Human-readable thesis for UI / logs."""
    try:
        if pattern_type == "rsi_rebound_long":
            return f"RSI oversold at {features.get('rsi_14', 0):.1f} with {features.get('volume_surge', 0):.1f}× volume; potential bounce."
        if pattern_type == "rsi_rebound_short":
            return f"RSI overbought at {features.get('rsi_14', 0):.1f} with {features.get('volume_surge', 0):.1f}× volume; potential pullback."
        if pattern_type == "ema_crossover_long":
            return f"EMA bullish crossover with {features.get('volume_surge', 0):.1f}× volume; RSI {features.get('rsi_14', 0):.1f}."
        if pattern_type == "ema_crossover_short":
            return f"EMA bearish crossover with {features.get('volume_surge', 0):.1f}× volume; RSI {features.get('rsi_14', 0):.1f}."
        if pattern_type == "breakout_long":
            return f"Bollinger-band breakout with {features.get('volume_surge', 0):.1f}× volume; momentum expansion."
        if pattern_type == "breakout_short":
            return f"Bollinger-band breakdown with {features.get('volume_surge', 0):.1f}× volume; momentum expansion."
        if pattern_type in {"volume_surge_long", "volume_surge_short"}:
            return f"Volume surge of {features.get('volume_surge', 0):.1f}× with {features.get('price_change', 0):+.1%} price move."
        return f"Pattern detected: {pattern_type}"
    except Exception:
        return f"Pattern detected: {pattern_type}"
