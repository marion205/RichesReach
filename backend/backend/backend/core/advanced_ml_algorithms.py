"""
Advanced ML Algorithms Service (institutional-grade)
- Reproducible (seeded), leak-safe (TimeSeriesSplit), and metadata-rich
- Proper model registry, compressed artifacts, input scaling pipelines
- LSTM random-search with early stopping
- Voting/Stacking ensembles with walk-forward CV
- Robust online learning with partial_fit + scaler
"""

from __future__ import annotations

import os
import time
import json
import math
import logging
import pickle
import hashlib
from dataclasses import dataclass, asdict
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple

import numpy as np

# Optional deps
try:
    import tensorflow as tf  # type: ignore
    from tensorflow.keras import Sequential  # type: ignore
    from tensorflow.keras.layers import LSTM, Dense, Dropout, BatchNormalization  # type: ignore
    from tensorflow.keras.optimizers import Adam  # type: ignore
    from tensorflow.keras.callbacks import EarlyStopping, ReduceLROnPlateau  # type: ignore
    TENSORFLOW_AVAILABLE = True
except Exception:
    TENSORFLOW_AVAILABLE = False

try:
    from sklearn.pipeline import Pipeline  # type: ignore
    from sklearn.preprocessing import StandardScaler  # type: ignore
    from sklearn.ensemble import (
        VotingRegressor,
        StackingRegressor,
    )  # type: ignore
    from sklearn.linear_model import LinearRegression, SGDRegressor  # type: ignore
    from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score  # type: ignore
    from sklearn.model_selection import TimeSeriesSplit, KFold  # type: ignore
    from sklearn.neural_network import MLPRegressor  # type: ignore
    from sklearn.svm import SVR  # type: ignore
    from sklearn.tree import DecisionTreeRegressor  # type: ignore
    import joblib  # type: ignore
    SKLEARN_AVAILABLE = True
except Exception:
    SKLEARN_AVAILABLE = False

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


# --------------------------- Data classes & utils -----------------------------

@dataclass
class ModelPerformance:
    mse: float
    mae: float
    r2: float
    training_time: float
    prediction_time: float
    model_size_mb: float
    extra: Dict[str, Any]


@dataclass
class LSTMSearchSpace:
    units: List[int] = None
    layers: List[int] = None
    dropout: List[float] = None
    learning_rate: List[float] = None
    batch_size: List[int] = None
    epochs: int = 150
    patience: int = 12
    n_trials: int = 10  # random search samples

    def __post_init__(self):
        if self.units is None:
            self.units = [64, 96, 128]
        if self.layers is None:
            self.layers = [1, 2, 3]
        if self.dropout is None:
            self.dropout = [0.1, 0.2, 0.3]
        if self.learning_rate is None:
            self.learning_rate = [1e-3, 5e-4, 2e-4]
        if self.batch_size is None:
            self.batch_size = [32, 64, 128]


def _seed_everything(seed: int = 42):
    os.environ["PYTHONHASHSEED"] = str(seed)
    np.random.seed(seed)
    if TENSORFLOW_AVAILABLE:
        tf.random.set_seed(seed)


def _sha256_of_array(arr: np.ndarray) -> str:
    # lightweight fingerprint for auditability
    m = hashlib.sha256()
    m.update(np.ascontiguousarray(arr).data)
    return m.hexdigest()


def _now() -> str:
    return datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")


# ------------------------------ Main service ---------------------------------

class AdvancedMLAlgorithms:
    """Production-ready ML service for financial forecasts & portfolio signals."""

    def __init__(self, models_dir: str = "advanced_ml_models", seed: int = 42, is_time_series: bool = True):
        self.models_dir = os.path.abspath(models_dir)
        os.makedirs(self.models_dir, exist_ok=True)

        _seed_everything(seed)
        self.seed = seed
        self.is_time_series = is_time_series

        self.models: Dict[str, Any] = {}
        self.performance_metrics: Dict[str, ModelPerformance] = {}
        self.lstm_config = LSTMSearchSpace()

        self.tensorflow_available = TENSORFLOW_AVAILABLE
        self.sklearn_available = SKLEARN_AVAILABLE

        logger.info(
            f"AdvancedMLAlgorithms initialized | TF:{'Y' if TENSORFLOW_AVAILABLE else 'N'} "
            f"SKL:{'Y' if SKLEARN_AVAILABLE else 'N'} | dir={self.models_dir}"
        )

    # ------------------------------ Deep Learning -----------------------------

    def create_lstm_model(
        self,
        input_shape: Tuple[int, int],
        output_size: int = 1,
        units: List[int] | None = None,
        dropout: float = 0.2,
        lr: float = 1e-3,
    ):
        if not self.tensorflow_available:
            raise ImportError("TensorFlow is required for LSTM models.")
        if units is None:
            units = [96, 64]

        model = Sequential()
        # First LSTM
        model.add(LSTM(units[0], return_sequences=(len(units) > 1), input_shape=input_shape))
        model.add(BatchNormalization())
        model.add(Dropout(dropout))

        # Middle LSTMs
        for u in units[1:-1]:
            model.add(LSTM(u, return_sequences=True))
            model.add(BatchNormalization())
            model.add(Dropout(dropout))

        # Final LSTM (no sequences)
        if len(units) > 1:
            model.add(LSTM(units[-1], return_sequences=False))
            model.add(BatchNormalization())
            model.add(Dropout(dropout))

        model.add(Dense(output_size, activation="linear"))
        model.compile(optimizer=Adam(learning_rate=lr), loss="mse", metrics=["mae"])
        return model

    @staticmethod
    def prepare_lstm_data(series: np.ndarray, lookback: int = 60) -> Tuple[np.ndarray, np.ndarray]:
        """Takes 1D array of values, returns X [N, lookback, 1], y [N, 1]."""
        series = np.asarray(series).reshape(-1)
        if len(series) <= lookback:
            raise ValueError("Series length must be greater than lookback.")
        X, y = [], []
        for i in range(lookback, len(series)):
            X.append(series[i - lookback : i])
            y.append(series[i])
        X = np.array(X, dtype=np.float32)[..., None]
        y = np.array(y, dtype=np.float32)[..., None]
        return X, y

    def train_lstm_model(
        self,
        X_train: np.ndarray,
        y_train: np.ndarray,
        X_val: Optional[np.ndarray] = None,
        y_val: Optional[np.ndarray] = None,
        model_name: str = "lstm_model",
        search_space: Optional[LSTMSearchSpace] = None,
    ) -> Dict[str, Any]:
        if not self.tensorflow_available:
            raise ImportError("TensorFlow is required for LSTM training.")
        cfg = search_space or self.lstm_config

        # Create validation split if not provided
        if X_val is None or y_val is None:
            split = int(len(X_train) * 0.8)
            X_train, X_val = X_train[:split], X_train[split:]
            y_train, y_val = y_train[:split], y_train[split:]

        best = {"val_loss": math.inf, "model": None, "params": None, "history": None}

        # Random-search over the grid (faster and stronger than exhaustive small loops)
        all_choices = []
        rng = np.random.default_rng(self.seed)
        for _ in range(cfg.n_trials):
            all_choices.append(
                {
                    "units": [rng.choice(cfg.units) for _ in range(rng.choice(cfg.layers))],
                    "dropout": float(rng.choice(cfg.dropout)),
                    "lr": float(rng.choice(cfg.learning_rate)),
                    "batch": int(rng.choice(cfg.batch_size)),
                }
            )

        for i, p in enumerate(all_choices, 1):
            logger.info(f"[LSTM] Trial {i}/{len(all_choices)}: {p}")

            model = self.create_lstm_model(
                input_shape=(X_train.shape[1], X_train.shape[2]),
                units=p["units"],
                dropout=p["dropout"],
                lr=p["lr"],
            )

            callbacks = [
                EarlyStopping(patience=self.lstm_config.patience, restore_best_weights=True),
                ReduceLROnPlateau(factor=0.5, patience=max(4, self.lstm_config.patience // 2)),
            ]

            t0 = time.time()
            hist = model.fit(
                X_train,
                y_train,
                validation_data=(X_val, y_val),
                epochs=self.lstm_config.epochs,
                batch_size=p["batch"],
                verbose=0,
                callbacks=callbacks,
            )
            train_time = time.time() - t0

            min_v = float(np.min(hist.history.get("val_loss", [np.inf])))
            if min_v < best["val_loss"]:
                best.update({"val_loss": min_v, "model": model, "params": {**p, "train_time": train_time}, "history": hist.history})

        if best["model"] is None:
            raise RuntimeError("LSTM search failed to produce a model.")

        # Persist best model
        path = os.path.join(self.models_dir, f"{model_name}.h5")
        best["model"].save(path)

        # Metrics on val
        val_pred = best["model"].predict(X_val, verbose=0)
        perf = ModelPerformance(
            mse=float(mean_squared_error(y_val, val_pred)),
            mae=float(mean_absolute_error(y_val, val_pred)),
            r2=float(r2_score(y_val, val_pred)),
            training_time=float(best["params"]["train_time"]),
            prediction_time=0.0,
            model_size_mb=os.path.getsize(path) / (1024 * 1024),
            extra={"val_loss": best["val_loss"], "params": best["params"], "created_at": _now()},
        )
        self.models[model_name] = best["model"]
        self.performance_metrics[model_name] = perf

        self._write_metadata(model_name, {
            "type": "lstm",
            "params": best["params"],
            "performance": asdict(perf),
            "tf": TENSORFLOW_AVAILABLE,
            "seed": self.seed,
        })

        logger.info(f"[LSTM] Saved {model_name} @ {path} | val_mse={perf.mse:.6f} r2={perf.r2:.4f}")
        return {"model": best["model"], "parameters": best["params"], "performance": perf, "history": best["history"]}

    def predict_lstm(self, model_name: str, X: np.ndarray) -> np.ndarray:
        if model_name not in self.models:
            self.load_model(model_name)
        model = self.models[model_name]
        t0 = time.time()
        pred = model.predict(X, verbose=0)
        dt = time.time() - t0
        # record last prediction latency
        if model_name in self.performance_metrics:
            self.performance_metrics[model_name].prediction_time = dt
        return pred

    # ------------------------------ Ensembles ---------------------------------

    def _cv(self, n_splits: int = 5):
        if not self.is_time_series:
            return KFold(n_splits=n_splits, shuffle=True, random_state=self.seed)
        return TimeSeriesSplit(n_splits=n_splits)

    def _fit_and_score_reg(self, pipeline, X, y, model_name: str) -> ModelPerformance:
        t0 = time.time()
        pipeline.fit(X, y)
        t_train = time.time() - t0

        # CV evaluation (walk-forward for TS)
        cv = self._cv(5)
        preds, trues = [], []
        for tr_idx, te_idx in cv.split(X):
            pipeline.fit(X[tr_idx], y[tr_idx])
            p = pipeline.predict(X[te_idx])
            preds.append(p)
            trues.append(y[te_idx])
        y_true = np.concatenate(trues)
        y_pred = np.concatenate(preds)

        mse = float(mean_squared_error(y_true, y_pred))
        mae = float(mean_absolute_error(y_true, y_pred))
        r2 = float(r2_score(y_true, y_pred))

        path = self.save_model(model_name, pipeline)
        perf = ModelPerformance(
            mse=mse,
            mae=mae,
            r2=r2,
            training_time=t_train,
            prediction_time=0.0,
            model_size_mb=os.path.getsize(path) / (1024 * 1024),
            extra={"cv_splits": 5, "created_at": _now()},
        )
        self.performance_metrics[model_name] = perf
        logger.info(f"[{model_name}] CV mse={mse:.6f} mae={mae:.6f} r2={r2:.4f}")
        return perf

    def create_voting_ensemble(self, X_train: np.ndarray, y_train: np.ndarray, model_name: str = "voting_ensemble") -> Dict[str, Any]:
        if not self.sklearn_available:
            raise ImportError("Scikit-learn is required for ensemble methods.")

        base = [
            ("linear", LinearRegression()),
            ("svr", SVR(kernel="rbf")),
            ("tree", DecisionTreeRegressor(random_state=self.seed)),
            ("mlp", MLPRegressor(hidden_layer_sizes=(96, 48), random_state=self.seed, max_iter=500)),
        ]
        ensemble = VotingRegressor(estimators=base)

        pipe = Pipeline([("scaler", StandardScaler(with_mean=True)), ("model", ensemble)])
        perf = self._fit_and_score_reg(pipe, X_train, y_train, model_name)

        self._write_metadata(model_name, {
            "type": "voting_regressor",
            "base_models": [n for n, _ in base],
            "performance": asdict(perf),
            "seed": self.seed,
        })

        self.models[model_name] = pipe
        return {"model": pipe, "performance": perf, "base_models": [n for n, _ in base]}

    def create_stacking_ensemble(self, X_train: np.ndarray, y_train: np.ndarray, model_name: str = "stacking_ensemble") -> Dict[str, Any]:
        if not self.sklearn_available:
            raise ImportError("Scikit-learn is required for ensemble methods.")

        base = [
            ("linear", LinearRegression()),
            ("svr", SVR(kernel="rbf")),
            ("tree", DecisionTreeRegressor(random_state=self.seed)),
        ]
        meta = LinearRegression()
        ensemble = StackingRegressor(estimators=base, final_estimator=meta, cv=self._cv(5))

        pipe = Pipeline([("scaler", StandardScaler(with_mean=True)), ("model", ensemble)])
        perf = self._fit_and_score_reg(pipe, X_train, y_train, model_name)

        self._write_metadata(model_name, {
            "type": "stacking_regressor",
            "base_models": [n for n, _ in base],
            "meta_learner": "LinearRegression",
            "performance": asdict(perf),
            "seed": self.seed,
        })

        self.models[model_name] = pipe
        return {"model": pipe, "performance": perf, "base_models": [n for n, _ in base], "meta_learner": "LinearRegression"}

    # ----------------------------- Online learning ----------------------------

    def create_online_learner(self, model_type: str = "sgd", model_name: str = "online_learner") -> Dict[str, Any]:
        if not self.sklearn_available:
            raise ImportError("Scikit-learn is required for online learning.")

        if model_type == "sgd":
            base = SGDRegressor(random_state=self.seed, learning_rate="adaptive", max_iter=1, warm_start=True)
        elif model_type == "mlp":
            base = MLPRegressor(hidden_layer_sizes=(50, 25), random_state=self.seed, learning_rate="adaptive", max_iter=1, warm_start=True)
        else:
            raise ValueError(f"Unknown model_type: {model_type}")

        pipe = Pipeline([("scaler", StandardScaler(with_mean=True)), ("model", base)])
        self.models[model_name] = pipe
        path = self.save_model(model_name, pipe)

        self._write_metadata(model_name, {"type": "online", "algo": model_type, "created_at": _now(), "path": path})
        logger.info(f"[online] created {model_name} ({model_type})")
        return {"model": pipe, "model_type": model_type, "path": path}

    def update_online_learner(self, model_name: str, X_new: np.ndarray, y_new: np.ndarray) -> Dict[str, Any]:
        if model_name not in self.models:
            self.load_model(model_name)
        pipe = self.models[model_name]
        # Ensure shapes (sklearn wants 2D X, 1D y)
        X_new = np.asarray(X_new)
        y_new = np.asarray(y_new).reshape(-1)
        if X_new.ndim == 1:
            X_new = X_new.reshape(-1, 1)

        t0 = time.time()
        # Fit in small batches to mimic streaming stability
        bs = max(32, min(1024, len(X_new)))
        for i in range(0, len(X_new), bs):
            Xi = X_new[i : i + bs]
            yi = y_new[i : i + bs]
            pipe.partial_fit(Xi, yi)
        dt = time.time() - t0

        path = self.save_model(model_name, pipe)
        logger.info(f"[online] updated {model_name} in {dt:.4f}s -> {path}")
        return {"model": pipe, "update_time": dt, "new_data_points": int(len(X_new))}

    # ------------------------------ Model I/O ---------------------------------

    def load_model(self, model_name: str) -> Any:
        pkl = os.path.join(self.models_dir, f"{model_name}.pkl")
        h5 = os.path.join(self.models_dir, f"{model_name}.h5")
        if os.path.exists(pkl) and self.sklearn_available:
            model = joblib.load(pkl)
            self.models[model_name] = model
            logger.info(f"Loaded {model_name} (.pkl)")
            return model
        if os.path.exists(h5) and self.tensorflow_available:
            model = tf.keras.models.load_model(h5)
            self.models[model_name] = model
            logger.info(f"Loaded {model_name} (.h5)")
            return model
        raise FileNotFoundError(f"Model {model_name} not found in {self.models_dir}")

    def save_model(self, model_name: str, model: Any) -> str:
        if self.tensorflow_available and hasattr(model, "save") and isinstance(model, tf.keras.Model):
            path = os.path.join(self.models_dir, f"{model_name}.h5")
            model.save(path)
        else:
            path = os.path.join(self.models_dir, f"{model_name}.pkl")
            joblib.dump(model, path, compress=("xz", 3))
        return path

    def list_models(self) -> List[str]:
        out = []
        for f in os.listdir(self.models_dir):
            if f.endswith((".pkl", ".h5")):
                out.append(os.path.splitext(f)[0])
        return sorted(set(out))

    def get_model_performance(self, model_name: str) -> Optional[ModelPerformance]:
        return self.performance_metrics.get(model_name)

    def delete_model(self, model_name: str) -> bool:
        try:
            self.models.pop(model_name, None)
            self.performance_metrics.pop(model_name, None)
            for ext in (".pkl", ".h5", ".meta.json"):
                p = os.path.join(self.models_dir, f"{model_name}{ext}")
                if os.path.exists(p):
                    os.remove(p)
            logger.info(f"Deleted model {model_name}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete {model_name}: {e}")
            return False

    def get_service_status(self) -> Dict[str, Any]:
        return {
            "tensorflow_available": self.tensorflow_available,
            "sklearn_available": self.sklearn_available,
            "models_directory": self.models_dir,
            "models_loaded": list(self.models.keys()),
            "models_available": self.list_models(),
            "performance_metrics": {
                name: asdict(mp) for name, mp in self.performance_metrics.items()
            },
            "seed": self.seed,
            "is_time_series": self.is_time_series,
        }

    # ------------------------------ Metadata ----------------------------------

    def _write_metadata(self, model_name: str, meta: Dict[str, Any]):
        try:
            path = os.path.join(self.models_dir, f"{model_name}.meta.json")
            with open(path, "w", encoding="utf-8") as f:
                json.dump(meta, f, indent=2, default=str)
        except Exception as e:
            logger.warning(f"Failed to write metadata for {model_name}: {e}")