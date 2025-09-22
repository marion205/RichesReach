"""
ML Learning System for Day Trading (Improved)
- Deterministic features, correct returns, day-level precision@3
- Chronological validation, WAL SQLite, ONNX + pickle fallback
- Model promotion with guardrails, stable PSI bins
"""

from __future__ import annotations
import os, json, sqlite3, logging
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

# ==== ML libs (optional) ====
try:
    import xgboost as xgb
    from sklearn.calibration import CalibratedClassifierCV
    from sklearn.metrics import roc_auc_score
    from skl2onnx import convert_sklearn
    from onnxconverter_common.data_types import FloatTensorType
    ML_AVAILABLE = True
except Exception as e:
    logging.warning(f"ML libs missing or partial: {e}")
    ML_AVAILABLE = False

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# ==== CONFIG ====
DB_PATH = os.getenv("RR_ML_DB", "trading_outcomes.db")
MODELS_DIR = Path(os.getenv("RR_MODELS_DIR", "models"))
MODELS_DIR.mkdir(exist_ok=True)

FEATURES_ORDER = [
    "momentum_15m",
    "rvol_10m",
    "vwap_dist",
    "breakout_pct",
    "spread_bps",
    "catalyst_score",
]

SAFE_LABEL_PCT = 0.005    # +0.5% within horizon ≈ +1R proxy for SAFE
AGG_LABEL_PCT = 0.012     # +1.2% proxy for AGG
MIN_TRAIN_SAMPLES = 200   # avoid overfitting
VAL_SPLIT_RATIO = 0.2     # last 20% by time
PROMOTION_MIN_AUC = 0.55  # guardrail: don't promote junk
PROMOTION_MIN_P3 = 0.45   # guardrail: precision@3 >= 45%
RETRAIN_MIN_HOURS = 6
RETRAIN_MIN_NEW_SAMPLES = 50

# ==== DATA CLASSES ====
@dataclass
class TradingOutcome:
    symbol: str
    side: str           # LONG | SHORT
    entry_price: float
    exit_price: float
    entry_time: str     # ISO8601
    exit_time: str      # ISO8601
    mode: str           # SAFE | AGGRESSIVE
    outcome: str        # +1R | -1R | time_stop | ...
    features: Dict[str, float]
    score: float        # prediction at decision time
    timestamp: str      # ISO8601 (decision time)

@dataclass
class ModelMetrics:
    model_id: str
    mode: str
    auc: float
    precision_at_3: float
    hit_rate: float
    avg_return: float
    sharpe_ratio: float
    max_drawdown: float
    training_samples: int
    validation_samples: int
    created_at: str

# ==== DB UTILS ====
def _connect(db_path=DB_PATH):
    conn = sqlite3.connect(db_path, timeout=30, isolation_level=None)  # autocommit
    with conn:
        conn.execute("PRAGMA journal_mode=WAL;")
        conn.execute("PRAGMA synchronous=NORMAL;")
    return conn

def _exec(conn: sqlite3.Connection, sql: str, params: tuple = ()):
    with conn:
        conn.execute(sql, params)

def _query_df(conn: sqlite3.Connection, sql: str, params: tuple = ()) -> pd.DataFrame:
    return pd.read_sql_query(sql, conn, params=params)

# ==== TRACKER ====
class OutcomeTracker:
    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        conn = _connect(self.db_path)
        _exec(conn, """
        CREATE TABLE IF NOT EXISTS trading_outcomes (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          symbol TEXT NOT NULL,
          side TEXT NOT NULL,
          entry_price REAL NOT NULL,
          exit_price REAL NOT NULL,
          entry_time TEXT NOT NULL,
          exit_time TEXT NOT NULL,
          mode TEXT NOT NULL,
          outcome TEXT NOT NULL,
          features TEXT NOT NULL,
          score REAL NOT NULL,
          timestamp TEXT NOT NULL,
          created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )""")
        _exec(conn, "CREATE INDEX IF NOT EXISTS idx_outcomes_mode_time ON trading_outcomes(mode, timestamp)")
        _exec(conn, """
        CREATE TABLE IF NOT EXISTS model_metrics (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          model_id TEXT UNIQUE NOT NULL,
          mode TEXT NOT NULL,
          auc REAL NOT NULL,
          precision_at_3 REAL NOT NULL,
          hit_rate REAL NOT NULL,
          avg_return REAL NOT NULL,
          sharpe_ratio REAL NOT NULL,
          max_drawdown REAL NOT NULL,
          training_samples INTEGER NOT NULL,
          validation_samples INTEGER NOT NULL,
          created_at TEXT NOT NULL,
          is_active BOOLEAN DEFAULT FALSE
        )""")
        _exec(conn, """
        CREATE TABLE IF NOT EXISTS model_versions (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          model_id TEXT NOT NULL,
          mode TEXT NOT NULL,
          model_path TEXT NOT NULL,
          feature_names TEXT NOT NULL,
          created_at TEXT NOT NULL,
          is_active BOOLEAN DEFAULT FALSE
        )""")
        conn.close()

    def log_outcome(self, outcome: TradingOutcome) -> bool:
        try:
            conn = _connect(self.db_path)
            _exec(conn, """
              INSERT INTO trading_outcomes
              (symbol, side, entry_price, exit_price, entry_time, exit_time, mode, outcome, features, score, timestamp)
              VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""", (
                outcome.symbol, outcome.side, outcome.entry_price, outcome.exit_price,
                outcome.entry_time, outcome.exit_time, outcome.mode, outcome.outcome,
                json.dumps(outcome.features, separators=(",", ":")), outcome.score, outcome.timestamp
            ))
            conn.close()
            return True
        except Exception as e:
            logger.exception("log_outcome failed")
            return False

    def get_training_frame(self, mode: str, days: int = 60) -> pd.DataFrame:
        """Returns df with parsed features, signed returns, labels, and datetime columns."""
        try:
            conn = _connect(self.db_path)
            cutoff = (datetime.utcnow() - timedelta(days=days)).isoformat()
            df = _query_df(conn, """
                SELECT symbol, side, entry_price, exit_price, entry_time, exit_time,
                       mode, outcome, features, score, timestamp
                FROM trading_outcomes
                WHERE mode = ? AND timestamp >= ?
                ORDER BY timestamp ASC
            """, (mode, cutoff))
            conn.close()
            if df.empty:
                return df

            # Parse times
            for col in ("timestamp", "entry_time", "exit_time"):
                df[col] = pd.to_datetime(df[col], errors="coerce", utc=True)
            df["date"] = df["timestamp"].dt.date

            # Parse features dict -> stable columns
            fdicts = df["features"].apply(json.loads)
            X = pd.DataFrame.from_records(fdicts)
            # Ensure stable order and fill missing/extra
            for f in FEATURES_ORDER:
                if f not in X:
                    X[f] = 0.0
            X = X[FEATURES_ORDER].astype("float32")
            df = pd.concat([df.drop(columns=["features"]), X.add_prefix("f_")], axis=1)

            # Signed return (LONG = +, SHORT = -)
            sign = np.where(df["side"].values == "LONG", 1.0, -1.0)
            ret = sign * (df["exit_price"].values - df["entry_price"].values) / np.maximum(df["entry_price"].values, 1e-8)
            df["return_pct"] = ret

            # Labels (proxy for +1R before -1R)
            thr = SAFE_LABEL_PCT if mode.upper() == "SAFE" else AGG_LABEL_PCT
            df["label"] = (df["return_pct"] >= thr).astype("int8")

            return df
        except Exception:
            logger.exception("get_training_frame failed")
            return pd.DataFrame()

# ==== METRIC HELPERS ====
def precision_at_3_by_day(df_val: pd.DataFrame, probs: np.ndarray) -> float:
    """Compute precision@3 per day: for each day take top-3 by prob, average true labels."""
    if df_val.empty:
        return 0.0
    tmp = df_val[["date", "label"]].copy()
    tmp["prob"] = probs
    p_list, days = [], 0
    for d, g in tmp.groupby("date", sort=True):
        g = g.sort_values("prob", ascending=False).head(3)
        if not g.empty:
            p_list.append(g["label"].mean())
            days += 1
    return float(np.mean(p_list)) if days > 0 else 0.0

def equity_curve_metrics_from_top3(df_val: pd.DataFrame, probs: np.ndarray) -> Tuple[float, float, float]:
    """
    Build daily strategy from top-3 picks by prob per day.
    Returns avg_return (daily mean of equal-weighted basket),
            sharpe (annualized, 252),
            max_drawdown (min drawdown of cumulative curve).
    """
    if df_val.empty:
        return 0.0, 0.0, 0.0
    tmp = df_val[["date", "return_pct"]].copy()
    tmp["prob"] = probs
    # Daily equal-weighted across top-3 selections
    daily_rets = []
    for d, g in tmp.groupby("date", sort=True):
        g = g.sort_values("prob", ascending=False).head(3)
        if g.empty:
            continue
        daily_rets.append(g["return_pct"].mean())
    if not daily_rets:
        return 0.0, 0.0, 0.0
    r = np.array(daily_rets, dtype=float)
    avg = float(np.mean(r))
    sharpe = float((np.mean(r) / (np.std(r) + 1e-12)) * np.sqrt(252)) if len(r) > 1 else 0.0
    curve = np.cumprod(1.0 + r)
    running_max = np.maximum.accumulate(curve)
    mdd = float(np.min((curve - running_max) / (running_max + 1e-12)))
    return avg, sharpe, mdd

# ==== TRAINER ====
class ModelTrainer:
    def __init__(self, models_dir: Path = MODELS_DIR, tracker: OutcomeTracker | None = None):
        self.dir = models_dir
        self.tracker = tracker or OutcomeTracker()
        self.ml_available = ML_AVAILABLE

    def _chronological_split(self, df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame]:
        n = len(df)
        k = max(1, int(n * (1 - VAL_SPLIT_RATIO)))
        return df.iloc[:k].copy(), df.iloc[k:].copy()

    def _build_xy(self, df: pd.DataFrame) -> Tuple[np.ndarray, np.ndarray]:
        X = df[[f"f_{f}" for f in FEATURES_ORDER]].astype("float32").values
        y = df["label"].astype("int8").values
        return X, y

    def _save_artifacts(self, mode: str, model, feature_names: List[str], platt_ab: Optional[Tuple[float,float]] = None) -> Tuple[str, Path]:
        mid = f"{mode.lower()}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
        onnx_path = self.dir / f"{mid}.onnx"
        pkl_path  = self.dir / f"{mid}.pkl"
        try:
            # Try ONNX for the calibrated model; if it fails, fallback below.
            onnx = convert_sklearn(model, initial_types=[("input", FloatTensorType([None, len(feature_names)]))])
            with open(onnx_path, "wb") as f:
                f.write(onnx.SerializeToString())
            logger.info(f"Saved ONNX → {onnx_path}")
        except Exception as e:
            logger.warning(f"ONNX export failed ({e}); saving pickle instead.")
            import pickle
            with open(pkl_path, "wb") as f:
                pickle.dump({"model": model, "features": feature_names, "platt": platt_ab}, f)
        # Manifest
        (self.dir / f"{mid}_features.json").write_text(json.dumps(feature_names))
        (self.dir / f"{mid}_manifest.json").write_text(json.dumps({
            "model_id": mid, "mode": mode, "exported": datetime.utcnow().isoformat(),
            "features": feature_names, "platt": platt_ab
        }))
        return mid, (onnx_path if onnx_path.exists() else pkl_path)

    def _record_version(self, model_id: str, mode: str, path: Path):
        conn = _connect()
        _exec(conn, """
           INSERT INTO model_versions(model_id, mode, model_path, feature_names, created_at, is_active)
           VALUES (?, ?, ?, ?, ?, FALSE)
        """, (model_id, mode, str(path), json.dumps(FEATURES_ORDER), datetime.utcnow().isoformat()))
        conn.close()

    def train(self, mode: str) -> Optional[ModelMetrics]:
        if not self.ml_available:
            logger.warning("ML not available; skipping training.")
            return None

        df = self.tracker.get_training_frame(mode, days=60)
        if len(df) < MIN_TRAIN_SAMPLES:
            logger.warning(f"Not enough samples for {mode}: {len(df)} < {MIN_TRAIN_SAMPLES}")
            return None

        # Chronological split
        df_tr, df_val = self._chronological_split(df)
        X_tr, y_tr = self._build_xy(df_tr)
        X_val, y_val = self._build_xy(df_val)

        # Base model
        booster = xgb.XGBClassifier(
            n_estimators=300, max_depth=4, learning_rate=0.07,
            subsample=0.9, colsample_bytree=0.8, reg_lambda=2.0,
            tree_method="hist", n_jobs=8, random_state=42
        )

        # Platt calibration
        model = CalibratedClassifierCV(booster, method="sigmoid", cv=3)
        model.fit(X_tr, y_tr)

        # Evaluate
        p_val = model.predict_proba(X_val)[:, 1]
        auc = float(roc_auc_score(y_val, p_val)) if len(np.unique(y_val)) > 1 else 0.5
        p3 = precision_at_3_by_day(df_val, p_val)
        avg_ret, sharpe, mdd = equity_curve_metrics_from_top3(df_val, p_val)
        hit_rate = float(y_val.mean()) if len(y_val) else 0.0

        # Save artifacts (with fallback)
        model_id, model_path = self._save_artifacts(mode, model, FEATURES_ORDER)
        self._record_version(model_id, mode, model_path)

        # Store metrics
        metrics = ModelMetrics(
            model_id=model_id, mode=mode, auc=auc, precision_at_3=p3,
            hit_rate=hit_rate, avg_return=float(avg_ret), sharpe_ratio=float(sharpe),
            max_drawdown=float(mdd), training_samples=len(df_tr), validation_samples=len(df_val),
            created_at=datetime.utcnow().isoformat()
        )
        self._save_metrics(metrics)
        logger.info(f"[{mode}] Trained {model_id} | AUC {auc:.3f} | P@3 {p3:.3f} | Sharpe {sharpe:.2f} | MDD {mdd:.2%}")
        return metrics

    def _save_metrics(self, m: ModelMetrics):
        conn = _connect()
        _exec(conn, """
          INSERT OR REPLACE INTO model_metrics
          (model_id, mode, auc, precision_at_3, hit_rate, avg_return, sharpe_ratio, max_drawdown,
           training_samples, validation_samples, created_at, is_active)
          VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, COALESCE(
            (SELECT is_active FROM model_metrics WHERE model_id=?), FALSE))
        """, (m.model_id, m.mode, m.auc, m.precision_at_3, m.hit_rate, m.avg_return,
              m.sharpe_ratio, m.max_drawdown, m.training_samples, m.validation_samples,
              m.created_at, m.model_id))
        conn.close()

    def promote_if_better(self, mode: str, new: ModelMetrics) -> bool:
        """Promote new model if it beats active and passes guardrails."""
        if new.auc < PROMOTION_MIN_AUC or new.precision_at_3 < PROMOTION_MIN_P3:
            logger.info(f"[{mode}] Guardrails block promotion: AUC {new.auc:.2f}, P@3 {new.precision_at_3:.2f}")
            return False
        conn = _connect()
        cur = conn.cursor()
        cur.execute("SELECT model_id, auc, precision_at_3, sharpe_ratio FROM model_metrics WHERE mode=? AND is_active=TRUE LIMIT 1", (mode,))
        row = cur.fetchone()
        def score(m: ModelMetrics | Dict[str, float]) -> float:
            return (m["auc"] if isinstance(m, dict) else m.auc) * 0.5 + \
                   (m["precision_at_3"] if isinstance(m, dict) else m.precision_at_3) * 0.4 + \
                   (m["sharpe_ratio"] if isinstance(m, dict) else m.sharpe_ratio) * 0.1
        better = row is None or score(new) > score({"auc": row[1], "precision_at_3": row[2], "sharpe_ratio": row[3]})
        if better:
            _exec(conn, "UPDATE model_metrics SET is_active=FALSE WHERE mode=?", (mode,))
            _exec(conn, "UPDATE model_metrics SET is_active=TRUE WHERE model_id=?", (new.model_id,))
            _exec(conn, "UPDATE model_versions SET is_active=FALSE WHERE mode=?", (mode,))
            _exec(conn, "UPDATE model_versions SET is_active=TRUE WHERE model_id=?", (new.model_id,))
            conn.close()
            logger.info(f"[{mode}] PROMOTED {new.model_id}")
            return True
        conn.close()
        logger.info(f"[{mode}] Not promoted (did not beat current active).")
        return False

# ==== CONTEXTUAL BANDIT (kept simple; add persistence if needed) ====
class ContextualBandit:
    def __init__(self, strategies: Optional[List[str]] = None):
        self.strategies = strategies or ["breakout", "mean_reversion", "momentum", "etf_rotation"]
        self.arms = {s: {"alpha": 1.0, "beta": 1.0} for s in self.strategies}

    def select(self, context: Dict[str, float]) -> str:
        samples = {s: np.random.beta(v["alpha"], v["beta"]) for s, v in self.arms.items()}
        return max(samples, key=samples.get)

    def update(self, strategy: str, reward: float):
        if strategy not in self.arms: return
        if reward > 0: self.arms[strategy]["alpha"] += 1.0
        else:          self.arms[strategy]["beta"]  += 1.0

    def snapshot(self) -> Dict[str, Dict[str, float]]:
        out = {}
        for s, v in self.arms.items():
            total = v["alpha"] + v["beta"]
            out[s] = {
                "win_rate": v["alpha"] / total,
                "confidence": total,
                "alpha": v["alpha"],
                "beta": v["beta"]
            }
        return out

# ==== DRIFT DETECTOR (quantile bins PSI) ====
class DriftDetector:
    def __init__(self, bins: int = 10, threshold: float = 0.1):
        self.ref: Optional[np.ndarray] = None
        self.bins = bins
        self.threshold = threshold

    def update_reference(self, data: np.ndarray):
        self.ref = data.copy()

    def detect(self, current: np.ndarray) -> Dict[str, Any]:
        if self.ref is None:
            self.update_reference(current)
            return {"drift_detected": False, "message": "reference set", "max_psi": 0.0, "psi_scores": []}
        psi_scores = [self._psi(self.ref[:, i], current[:, i]) for i in range(current.shape[1])]
        max_psi = float(np.max(psi_scores)) if psi_scores else 0.0
        return {"drift_detected": bool(max_psi > self.threshold), "max_psi": max_psi, "psi_scores": psi_scores}

    def _psi(self, a: np.ndarray, b: np.ndarray) -> float:
        try:
            qs = np.quantile(a[~np.isnan(a)], np.linspace(0, 1, self.bins + 1))
            qs[0], qs[-1] = -np.inf, np.inf
            exp, _ = np.histogram(a, bins=qs); act, _ = np.histogram(b, bins=qs)
            ep = exp / (exp.sum() + 1e-12); ap = act / (act.sum() + 1e-12)
            diff = ap - ep
            return float(np.sum(diff * np.log((ap + 1e-12) / (ep + 1e-12))))
        except Exception:
            return 0.0

# ==== COORDINATOR ====
class MLLearningSystem:
    def __init__(self):
        self.tracker = OutcomeTracker()
        self.ml_ok = ML_AVAILABLE
        self.trainer = ModelTrainer(tracker=self.tracker) if self.ml_ok else None
        self.bandit = ContextualBandit()
        self.drift = DriftDetector()
        self.last_train: Dict[str, Optional[str]] = {"SAFE": None, "AGGRESSIVE": None}

    # --- API-like helpers ---
    def log_trading_outcome(self, outcome: Dict[str, Any]) -> bool:
        try:
            ok = self.tracker.log_outcome(TradingOutcome(**outcome))
            if ok:
                logger.info(f"Logged {outcome['symbol']} {outcome['side']} {outcome['outcome']}")
            return ok
        except Exception:
            logger.exception("log_trading_outcome failed")
            return False

    def _enough_new_data(self, mode: str) -> bool:
        conn = _connect()
        cutoff = (datetime.utcnow() - timedelta(days=7)).isoformat()
        df = _query_df(conn, "SELECT COUNT(*) as n FROM trading_outcomes WHERE mode=? AND timestamp>=?", (mode, cutoff))
        conn.close()
        return int(df["n"].iloc[0]) >= RETRAIN_MIN_NEW_SAMPLES

    def should_retrain(self, mode: str) -> bool:
        last = self.last_train.get(mode)
        if last:
            if datetime.utcnow() - datetime.fromisoformat(last) < timedelta(hours=RETRAIN_MIN_HOURS):
                return False
        return self._enough_new_data(mode)

    def train_if_needed(self) -> Dict[str, Optional[ModelMetrics]]:
        if not self.ml_ok or not self.trainer:
            logger.warning("ML not available; skip training.")
            return {"SAFE": None, "AGGRESSIVE": None}
        res: Dict[str, Optional[ModelMetrics]] = {"SAFE": None, "AGGRESSIVE": None}
        for mode in ("SAFE", "AGGRESSIVE"):
            if self.should_retrain(mode):
                m = self.trainer.train(mode)
                res[mode] = m
                if m:
                    self.last_train[mode] = m.created_at
                    self.trainer.promote_if_better(mode, m)
        return res

    def best_model_id(self, mode: str) -> Optional[str]:
        conn = _connect()
        df = _query_df(conn, "SELECT model_id FROM model_metrics WHERE mode=? AND is_active=TRUE LIMIT 1", (mode,))
        conn.close()
        return df["model_id"].iloc[0] if not df.empty else None

    def status(self) -> Dict[str, Any]:
        try:
            conn = _connect()
            total = int(_query_df(conn, "SELECT COUNT(*) c FROM trading_outcomes")["c"].iloc[0])
            recent = int(_query_df(conn, "SELECT COUNT(*) c FROM trading_outcomes WHERE timestamp>=?",
                                   ((datetime.utcnow() - timedelta(days=7)).isoformat(),))["c"].iloc[0])
            conn.close()
            return {
                "ml_available": self.ml_ok,
                "outcomes": {"total": total, "last_7d": recent},
                "models": {m: self.best_model_id(m) for m in ("SAFE", "AGGRESSIVE")},
                "bandit": self.bandit.snapshot(),
                "last_training": self.last_train,
            }
        except Exception as e:
            logger.exception("status failed")
            return {"error": str(e)}

# Global instance
ml_system = MLLearningSystem()
