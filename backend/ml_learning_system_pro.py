# ml_learning_system_pro.py (drop-in replacement of your MLLearningSystem + ModelTrainer cores)
import os, json, sqlite3, numpy as np, pandas as pd
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Tuple
import logging, pathlib

try:
    import xgboost as xgb
    from sklearn.calibration import CalibratedClassifierCV
    from sklearn.metrics import roc_auc_score, precision_recall_curve
    from sklearn.model_selection import TimeSeriesSplit
    from skl2onnx import to_onnx
    from onnxconverter_common.data_types import FloatTensorType
    ML_AVAILABLE = True
except Exception as e:
    ML_AVAILABLE = False

L = logging.getLogger(__name__)
FEATURES = ["momentum_15m","rvol_10m","vwap_dist","breakout_pct","spread_bps","catalyst_score"]

def _ensure_sqlite_pragmas(db_path: str):
    with sqlite3.connect(db_path) as con:
        con.execute("PRAGMA journal_mode=WAL;")
        con.execute("PRAGMA synchronous=NORMAL;")

@dataclass
class ModelMetrics:
    model_id: str; mode: str; auc: float; p_at_3: float; hit_rate: float; avg_return: float
    sharpe: float; max_dd: float; n_train: int; n_val: int; created_at: str

class OutcomeTracker:
    def __init__(self, db_path="trading_outcomes.db"):
        self.db_path = db_path
        pathlib.Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        _ensure_sqlite_pragmas(db_path); self.init_schema()

    def init_schema(self):
        with sqlite3.connect(self.db_path) as con:
            cur = con.cursor()
            cur.execute("""CREATE TABLE IF NOT EXISTS trading_outcomes(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol TEXT, side TEXT CHECK(side IN ('LONG','SHORT')),
                entry_price REAL, exit_price REAL,
                entry_time TEXT, exit_time TEXT,
                mode TEXT CHECK(mode IN ('SAFE','AGGRESSIVE')),
                outcome TEXT, features TEXT, score REAL, timestamp TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )""")
            cur.execute("""CREATE TABLE IF NOT EXISTS model_metrics(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                model_id TEXT UNIQUE, mode TEXT, auc REAL, p_at_3 REAL, hit_rate REAL,
                avg_return REAL, sharpe REAL, max_dd REAL, n_train INTEGER, n_val INTEGER, created_at TEXT,
                is_active BOOLEAN DEFAULT 0
            )""")
            cur.execute("""CREATE TABLE IF NOT EXISTS model_versions(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                model_id TEXT, mode TEXT, model_path TEXT, feature_names TEXT, created_at TEXT, is_active BOOLEAN DEFAULT 0
            )""")

    def get_training_data(self, mode: str, days: int = 60) -> pd.DataFrame:
        cutoff = (datetime.utcnow() - timedelta(days=days)).isoformat()
        with sqlite3.connect(self.db_path) as con:
            df = pd.read_sql_query("""
                SELECT symbol, side, entry_price, exit_price, entry_time, exit_time,
                       mode, outcome, features, score, timestamp
                FROM trading_outcomes WHERE mode = ? AND timestamp >= ? ORDER BY timestamp
            """, con, params=(mode, cutoff))
        if df.empty: return df
        df["features"] = df["features"].apply(json.loads)

        # Correct returns for long/short
        ret = (df["exit_price"] - df["entry_price"]) / df["entry_price"]
        long_mask = (df["side"] == "LONG").astype(int)
        short_adj = -1 * (1 - long_mask)
        df["return_pct"] = ret * long_mask + (-ret) * (1 - long_mask)

        # Label thresholds (explicitly different per mode)
        thr = 0.005 if mode == "SAFE" else 0.012
        df["label"] = (df["return_pct"] >= thr).astype(int)
        return df

class ModelTrainer:
    def __init__(self, models_dir="models", db_path="trading_outcomes.db"):
        self.models_dir = pathlib.Path(models_dir); self.models_dir.mkdir(exist_ok=True)
        self.tracker = OutcomeTracker(db_path=db_path); self.ml_ok = ML_AVAILABLE

    def _matrix(self, feat_rows: List[Dict[str, float]]) -> np.ndarray:
        # Deterministic feature order
        return np.array([[float(row.get(f, 0.0)) for f in FEATURES] for row in feat_rows], dtype=np.float32)

    def train(self, mode: str) -> Optional[ModelMetrics]:
        if not self.ml_ok: L.warning("ML not available"); return None
        df = self.tracker.get_training_data(mode, days=90)
        if len(df) < 200: L.warning("insufficient data: %s", len(df)); return None

        X = self._matrix(df["features"].tolist()); y = df["label"].values.astype(int)
        # Time-based split (last 20% = validation)
        split = int(0.8 * len(X)); X_tr, X_val = X[:split], X[split:]; y_tr, y_val = y[:split], y[split:]
        if len(np.unique(y_tr)) < 2 or len(np.unique(y_val)) < 2: L.warning("need class balance"); return None

        base = xgb.XGBClassifier(
            n_estimators=300, max_depth=4, learning_rate=0.07, subsample=0.9, colsample_bytree=0.8,
            reg_lambda=2.0, tree_method="hist", n_jobs=4, random_state=42, eval_metric="logloss"
        )
        model = CalibratedClassifierCV(base, method="sigmoid", cv=3)
        model.fit(X_tr, y_tr)
        prob = model.predict_proba(X_val)[:, 1]
        auc = float(roc_auc_score(y_val, prob))
        precision, recall, _ = precision_recall_curve(y_val, prob)
        p_at_3 = float(precision[np.argmax(recall >= 0.3)] if (recall >= 0.3).any() else 0.0)

        returns = df["return_pct"].values
        mu, sigma = float(np.mean(returns)), float(np.std(returns) + 1e-9)
        sharpe = (mu / sigma) * np.sqrt(252.0)
        eq = np.cumprod(1 + returns); dd = (eq / np.maximum.accumulate(eq)) - 1.0
        max_dd = float(np.min(dd))
        hit_rate = float(np.mean(y_val))
        avg_return = float(np.mean(returns))

        model_id = f"{mode.lower()}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
        onnx = to_onnx(model, initial_types=[("input", FloatTensorType([None, len(FEATURES)]))])
        onnx_path = self.models_dir / f"{model_id}.onnx"
        with open(onnx_path, "wb") as f: f.write(onnx.SerializeToString())
        with open(self.models_dir / f"{model_id}_features.json", "w") as f: json.dump(FEATURES, f)

        metrics = ModelMetrics(
            model_id=model_id, mode=mode, auc=auc, p_at_3=p_at_3, hit_rate=hit_rate, avg_return=avg_return,
            sharpe=sharpe, max_dd=max_dd, n_train=len(X_tr), n_val=len(X_val), created_at=datetime.utcnow().isoformat()
        )
        with sqlite3.connect(self.tracker.db_path) as con:
            con.execute("""INSERT OR REPLACE INTO model_metrics(model_id,mode,auc,p_at_3,hit_rate,avg_return,sharpe,max_dd,n_train,n_val,created_at)
                           VALUES(?,?,?,?,?,?,?,?,?,?,?)""",
                        (metrics.model_id, metrics.mode, metrics.auc, metrics.p_at_3, metrics.hit_rate,
                         metrics.avg_return, metrics.sharpe, metrics.max_dd, metrics.n_train, metrics.n_val, metrics.created_at))
            con.execute("""INSERT INTO model_versions(model_id, mode, model_path, feature_names, created_at, is_active)
                           VALUES(?,?,?,?,?,0)""", (metrics.model_id, mode, str(onnx_path), json.dumps(FEATURES), metrics.created_at))
        L.info("trained %s: auc=%.3f, p@0.3=%.2f, sharpe=%.2f, maxDD=%.2f", mode, auc, p_at_3, sharpe, max_dd)
        return metrics

    def get_best_model(self, mode: str) -> Optional[str]:
        with sqlite3.connect(self.tracker.db_path) as con:
            cur = con.cursor()
            cur.execute("""
                SELECT model_id FROM model_metrics 
                WHERE mode = ? AND is_active = 1 
                ORDER BY auc DESC, created_at DESC LIMIT 1
            """, (mode,))
            row = cur.fetchone()
            return row[0] if row else None

    def activate_model(self, model_id: str) -> bool:
        with sqlite3.connect(self.tracker.db_path) as con:
            con.execute("UPDATE model_metrics SET is_active = 0")
            con.execute("UPDATE model_metrics SET is_active = 1 WHERE model_id = ?", (model_id,))
            con.commit()
        return True

class MLLearningSystem:
    def __init__(self, models_dir="models", db_path="trading_outcomes.db"):
        self.trainer = ModelTrainer(models_dir, db_path)
        self.tracker = OutcomeTracker(db_path)

    def log_outcome(self, symbol: str, side: str, entry_price: float, exit_price: float,
                   entry_time: str, exit_time: str, mode: str, features: Dict[str, float], 
                   score: float) -> bool:
        try:
            with sqlite3.connect(self.tracker.db_path) as con:
                con.execute("""
                    INSERT INTO trading_outcomes 
                    (symbol, side, entry_price, exit_price, entry_time, exit_time, 
                     mode, features, score, timestamp)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (symbol, side, entry_price, exit_price, entry_time, exit_time,
                      mode, json.dumps(features), score, datetime.utcnow().isoformat()))
                con.commit()
            return True
        except Exception as e:
            L.error("Failed to log outcome: %s", e)
            return False

    def should_retrain(self, mode: str, days: int = 7) -> bool:
        cutoff = (datetime.utcnow() - timedelta(days=days)).isoformat()
        with sqlite3.connect(self.tracker.db_path) as con:
            cur = con.cursor()
            cur.execute("""
                SELECT COUNT(*) FROM trading_outcomes 
                WHERE mode = ? AND timestamp >= ?
            """, (mode, cutoff))
            count = cur.fetchone()[0]
        return count >= 50  # Retrain if 50+ new samples in last week

    def train_if_needed(self, mode: str) -> Optional[ModelMetrics]:
        if self.should_retrain(mode):
            L.info("Retraining %s model due to new data", mode)
            return self.trainer.train(mode)
        return None

    def get_model_metrics(self, mode: str) -> List[Dict[str, Any]]:
        with sqlite3.connect(self.tracker.db_path) as con:
            df = pd.read_sql_query("""
                SELECT * FROM model_metrics 
                WHERE mode = ? 
                ORDER BY created_at DESC LIMIT 10
            """, con, params=(mode,))
        return df.to_dict('records')

# Example usage and testing
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    # Initialize the system
    ml_system = MLLearningSystem()
    
    # Log some sample outcomes
    sample_features = {
        "momentum_15m": 0.75,
        "rvol_10m": 1.2,
        "vwap_dist": 0.05,
        "breakout_pct": 0.02,
        "spread_bps": 0.5,
        "catalyst_score": 0.8
    }
    
    # Log a successful trade
    ml_system.log_outcome(
        symbol="AAPL", side="LONG", entry_price=150.0, exit_price=155.0,
        entry_time="2024-01-01T10:00:00Z", exit_time="2024-01-01T15:00:00Z",
        mode="SAFE", features=sample_features, score=0.85
    )
    
    # Check if retraining is needed
    if ml_system.should_retrain("SAFE"):
        print("Retraining needed for SAFE mode")
        metrics = ml_system.train_if_needed("SAFE")
        if metrics:
            print(f"Trained model: {metrics.model_id}, AUC: {metrics.auc:.3f}")
    
    # Get model metrics
    metrics = ml_system.get_model_metrics("SAFE")
    print(f"Found {len(metrics)} models for SAFE mode")
