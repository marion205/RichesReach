"""
ML Learning System for Day Trading
Implements outcome tracking, model training, and advanced ML features
"""

import os
import json
import sqlite3
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
import logging
from dataclasses import dataclass, asdict
import hashlib
import pickle
from pathlib import Path

# ML Libraries
try:
    import xgboost as xgb
    from sklearn.calibration import CalibratedClassifierCV
    from sklearn.metrics import roc_auc_score, precision_recall_curve, auc
    from skl2onnx import to_onnx
    from onnxconverter_common.data_types import FloatTensorType
    ML_AVAILABLE = True
except (ImportError, AttributeError) as e:
    ML_AVAILABLE = False
    logging.warning(f"ML libraries not available: {e}. Install xgboost, scikit-learn, skl2onnx")

logger = logging.getLogger(__name__)

@dataclass
class TradingOutcome:
    """Trading outcome record for ML training"""
    symbol: str
    side: str  # LONG or SHORT
    entry_price: float
    exit_price: float
    entry_time: str
    exit_time: str
    mode: str  # SAFE or AGGRESSIVE
    outcome: str  # +1R, -1R, time_stop, etc.
    features: Dict[str, float]  # Original features used for prediction
    score: float  # Original prediction score
    timestamp: str

@dataclass
class ModelMetrics:
    """Model performance metrics"""
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

class OutcomeTracker:
    """Tracks trading outcomes for ML training"""
    
    def __init__(self, db_path: str = "trading_outcomes.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Initialize SQLite database for outcome tracking"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Trading outcomes table
        cursor.execute("""
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
                features TEXT NOT NULL,  -- JSON string
                score REAL NOT NULL,
                timestamp TEXT NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Model metrics table
        cursor.execute("""
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
            )
        """)
        
        # Model versions table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS model_versions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                model_id TEXT NOT NULL,
                mode TEXT NOT NULL,
                model_path TEXT NOT NULL,
                feature_names TEXT NOT NULL,  -- JSON string
                created_at TEXT NOT NULL,
                is_active BOOLEAN DEFAULT FALSE
            )
        """)
        
        conn.commit()
        conn.close()
    
    def log_outcome(self, outcome: TradingOutcome) -> bool:
        """Log a trading outcome"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO trading_outcomes 
                (symbol, side, entry_price, exit_price, entry_time, exit_time, 
                 mode, outcome, features, score, timestamp)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                outcome.symbol,
                outcome.side,
                outcome.entry_price,
                outcome.exit_price,
                outcome.entry_time,
                outcome.exit_time,
                outcome.mode,
                outcome.outcome,
                json.dumps(outcome.features),
                outcome.score,
                outcome.timestamp
            ))
            
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            logger.error(f"Error logging outcome: {e}")
            return False
    
    def get_training_data(self, mode: str, days: int = 60) -> pd.DataFrame:
        """Get training data for model training"""
        try:
            conn = sqlite3.connect(self.db_path)
            
            # Get outcomes from last N days
            cutoff_date = (datetime.now() - timedelta(days=days)).isoformat()
            
            query = """
                SELECT symbol, side, entry_price, exit_price, entry_time, exit_time,
                       mode, outcome, features, score, timestamp
                FROM trading_outcomes 
                WHERE mode = ? AND timestamp >= ?
                ORDER BY timestamp
            """
            
            df = pd.read_sql_query(query, conn, params=(mode, cutoff_date))
            conn.close()
            
            if df.empty:
                return df
            
            # Parse features JSON
            df['features'] = df['features'].apply(json.loads)
            
            # Calculate returns and labels
            df['return_pct'] = (df['exit_price'] - df['entry_price']) / df['entry_price']
            if mode == 'SAFE':
                df['return_pct'] = df['return_pct'] * (df['side'] == 'LONG').astype(int) * 2 - 1
            else:  # AGGRESSIVE
                df['return_pct'] = df['return_pct'] * (df['side'] == 'LONG').astype(int) * 2 - 1
            
            # Create binary labels (hit +1R before -1R)
            if mode == 'SAFE':
                df['label'] = (df['return_pct'] >= 0.005).astype(int)  # 0.5% threshold
            else:  # AGGRESSIVE
                df['label'] = (df['return_pct'] >= 0.012).astype(int)  # 1.2% threshold
            
            return df
            
        except Exception as e:
            logger.error(f"Error getting training data: {e}")
            return pd.DataFrame()
    
    def save_model_metrics(self, metrics: ModelMetrics) -> bool:
        """Save model performance metrics"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT OR REPLACE INTO model_metrics 
                (model_id, mode, auc, precision_at_3, hit_rate, avg_return, 
                 sharpe_ratio, max_drawdown, training_samples, validation_samples, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                metrics.model_id,
                metrics.mode,
                metrics.auc,
                metrics.precision_at_3,
                metrics.hit_rate,
                metrics.avg_return,
                metrics.sharpe_ratio,
                metrics.max_drawdown,
                metrics.training_samples,
                metrics.validation_samples,
                metrics.created_at
            ))
            
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            logger.error(f"Error saving model metrics: {e}")
            return False

class ModelTrainer:
    """Trains and manages ML models for day trading"""
    
    def __init__(self, models_dir: str = "models"):
        self.models_dir = Path(models_dir)
        self.models_dir.mkdir(exist_ok=True)
        self.outcome_tracker = OutcomeTracker()
        self.ml_available = ML_AVAILABLE
        
        if not ML_AVAILABLE:
            logger.warning("ML libraries not available. Model training will be disabled.")
            # Don't raise an error, just set ml_available to False
    
    def train_model(self, mode: str) -> Optional[ModelMetrics]:
        """Train a new model for the specified mode"""
        try:
            if not self.ml_available:
                logger.warning(f"ML libraries not available. Cannot train {mode} model.")
                return None
                
            # Get training data
            df = self.outcome_tracker.get_training_data(mode, days=60)
            
            if len(df) < 50:  # Need minimum samples
                logger.warning(f"Insufficient training data for {mode} mode: {len(df)} samples")
                return None
            
            # Prepare features
            feature_names = ['momentum_15m', 'rvol_10m', 'vwap_dist', 'breakout_pct', 'spread_bps', 'catalyst_score']
            
            # Extract features from JSON
            X = np.array([list(row['features'].values()) for row in df['features']])
            y = df['label'].values
            
            # Split data (80/20)
            split_idx = int(0.8 * len(X))
            X_train, X_val = X[:split_idx], X[split_idx:]
            y_train, y_val = y[:split_idx], y[split_idx:]
            
            # Train XGBoost model
            model = xgb.XGBClassifier(
                n_estimators=300,
                max_depth=4,
                learning_rate=0.07,
                subsample=0.9,
                colsample_bytree=0.8,
                reg_lambda=2.0,
                tree_method="hist",
                n_jobs=4,
                random_state=42
            )
            
            # Calibrate probabilities
            calibrated_model = CalibratedClassifierCV(model, method="sigmoid", cv=3)
            calibrated_model.fit(X_train, y_train)
            
            # Evaluate model
            y_pred_proba = calibrated_model.predict_proba(X_val)[:, 1]
            y_pred = calibrated_model.predict(X_val)
            
            # Calculate metrics
            auc_score = roc_auc_score(y_val, y_pred_proba)
            precision, recall, _ = precision_recall_curve(y_val, y_pred_proba)
            precision_at_3 = precision[np.argmax(recall >= 0.3)] if len(precision) > 0 else 0.0
            
            hit_rate = np.mean(y_val)
            avg_return = df['return_pct'].mean()
            
            # Calculate Sharpe ratio and max drawdown
            returns = df['return_pct'].values
            sharpe_ratio = np.mean(returns) / (np.std(returns) + 1e-8) * np.sqrt(252)
            
            cumulative_returns = np.cumprod(1 + returns)
            running_max = np.maximum.accumulate(cumulative_returns)
            drawdowns = (cumulative_returns - running_max) / running_max
            max_drawdown = np.min(drawdowns)
            
            # Generate model ID
            model_id = f"{mode.lower()}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            # Save model
            model_path = self.models_dir / f"{model_id}.onnx"
            onnx_model = to_onnx(
                calibrated_model, 
                initial_types=[("input", FloatTensorType([None, len(feature_names)]))]
            )
            
            with open(model_path, "wb") as f:
                f.write(onnx_model.SerializeToString())
            
            # Save feature names
            feature_path = self.models_dir / f"{model_id}_features.json"
            with open(feature_path, "w") as f:
                json.dump(feature_names, f)
            
            # Create metrics
            metrics = ModelMetrics(
                model_id=model_id,
                mode=mode,
                auc=float(auc_score),
                precision_at_3=float(precision_at_3),
                hit_rate=float(hit_rate),
                avg_return=float(avg_return),
                sharpe_ratio=float(sharpe_ratio),
                max_drawdown=float(max_drawdown),
                training_samples=len(X_train),
                validation_samples=len(X_val),
                created_at=datetime.now().isoformat()
            )
            
            # Save metrics
            self.outcome_tracker.save_model_metrics(metrics)
            
            logger.info(f"Trained {mode} model: {model_id}, AUC: {auc_score:.3f}, Hit Rate: {hit_rate:.3f}")
            return metrics
            
        except Exception as e:
            logger.error(f"Error training {mode} model: {e}")
            return None
    
    def get_best_model(self, mode: str) -> Optional[str]:
        """Get the best performing model for a mode"""
        try:
            conn = sqlite3.connect(self.outcome_tracker.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT model_id, auc, hit_rate, sharpe_ratio
                FROM model_metrics 
                WHERE mode = ? AND is_active = TRUE
                ORDER BY (auc * 0.4 + hit_rate * 0.3 + sharpe_ratio * 0.3) DESC
                LIMIT 1
            """, (mode,))
            
            result = cursor.fetchone()
            conn.close()
            
            return result[0] if result else None
            
        except Exception as e:
            logger.error(f"Error getting best model: {e}")
            return None

class ContextualBandit:
    """Contextual bandit for strategy selection"""
    
    def __init__(self, strategies: List[str] = None):
        self.strategies = strategies or ["breakout", "mean_reversion", "momentum", "etf_rotation"]
        self.arms = {strategy: {"alpha": 1.0, "beta": 1.0} for strategy in self.strategies}
        self.context_features = ["vix_level", "market_trend", "volatility_regime", "time_of_day"]
    
    def select_strategy(self, context: Dict[str, float]) -> str:
        """Select strategy using Thompson Sampling"""
        try:
            # Sample from Beta distributions
            samples = {}
            for strategy, params in self.arms.items():
                samples[strategy] = np.random.beta(params["alpha"], params["beta"])
            
            # Select strategy with highest sample
            selected_strategy = max(samples, key=samples.get)
            
            logger.info(f"Selected strategy: {selected_strategy} (samples: {samples})")
            return selected_strategy
            
        except Exception as e:
            logger.error(f"Error in strategy selection: {e}")
            return "momentum"  # Default fallback
    
    def update_reward(self, strategy: str, reward: float):
        """Update strategy performance"""
        try:
            if strategy in self.arms:
                if reward > 0:
                    self.arms[strategy]["alpha"] += 1
                else:
                    self.arms[strategy]["beta"] += 1
                
                logger.info(f"Updated {strategy}: alpha={self.arms[strategy]['alpha']}, beta={self.arms[strategy]['beta']}")
        except Exception as e:
            logger.error(f"Error updating reward: {e}")
    
    def get_strategy_performance(self) -> Dict[str, Dict[str, float]]:
        """Get current strategy performance estimates"""
        performance = {}
        for strategy, params in self.arms.items():
            total = params["alpha"] + params["beta"]
            performance[strategy] = {
                "win_rate": params["alpha"] / total if total > 0 else 0.5,
                "confidence": total,
                "alpha": params["alpha"],
                "beta": params["beta"]
            }
        return performance

class DriftDetector:
    """Detects data drift and model degradation"""
    
    def __init__(self, window_size: int = 100):
        self.window_size = window_size
        self.reference_data = None
        self.drift_threshold = 0.1  # PSI threshold
    
    def update_reference(self, data: np.ndarray):
        """Update reference distribution"""
        self.reference_data = data.copy()
    
    def detect_drift(self, current_data: np.ndarray) -> Dict[str, Any]:
        """Detect drift using Population Stability Index (PSI)"""
        try:
            if self.reference_data is None:
                self.update_reference(current_data)
                return {"drift_detected": False, "psi": 0.0, "message": "Reference data updated"}
            
            # Calculate PSI for each feature
            psi_scores = []
            for i in range(current_data.shape[1]):
                psi = self._calculate_psi(
                    self.reference_data[:, i], 
                    current_data[:, i]
                )
                psi_scores.append(psi)
            
            max_psi = max(psi_scores)
            drift_detected = max_psi > self.drift_threshold
            
            return {
                "drift_detected": drift_detected,
                "max_psi": max_psi,
                "psi_scores": psi_scores,
                "message": f"Drift detected: {max_psi:.3f} > {self.drift_threshold}" if drift_detected else "No drift detected"
            }
            
        except Exception as e:
            logger.error(f"Error detecting drift: {e}")
            return {"drift_detected": False, "error": str(e)}
    
    def _calculate_psi(self, expected: np.ndarray, actual: np.ndarray) -> float:
        """Calculate Population Stability Index"""
        try:
            # Create bins
            bins = np.linspace(
                min(np.min(expected), np.min(actual)),
                max(np.max(expected), np.max(actual)),
                11
            )
            
            # Calculate distributions
            expected_hist, _ = np.histogram(expected, bins=bins)
            actual_hist, _ = np.histogram(actual, bins=bins)
            
            # Normalize
            expected_pct = expected_hist / (np.sum(expected_hist) + 1e-8)
            actual_pct = actual_hist / (np.sum(actual_hist) + 1e-8)
            
            # Calculate PSI
            psi = np.sum((actual_pct - expected_pct) * np.log((actual_pct + 1e-8) / (expected_pct + 1e-8)))
            
            return psi
            
        except Exception as e:
            logger.error(f"Error calculating PSI: {e}")
            return 0.0

class MLLearningSystem:
    """Main ML Learning System coordinator"""
    
    def __init__(self):
        self.outcome_tracker = OutcomeTracker()
        self.ml_available = ML_AVAILABLE
        
        if ML_AVAILABLE:
            try:
                self.model_trainer = ModelTrainer()
                self.bandit = ContextualBandit()
                self.drift_detector = DriftDetector()
            except Exception as e:
                logger.error(f"Error initializing ML components: {e}")
                self.ml_available = False
                self.model_trainer = None
                self.bandit = None
                self.drift_detector = None
        else:
            self.model_trainer = None
            self.bandit = None
            self.drift_detector = None
            
        self.last_training = {"SAFE": None, "AGGRESSIVE": None}
    
    def log_trading_outcome(self, outcome_data: Dict[str, Any]) -> bool:
        """Log a trading outcome"""
        try:
            outcome = TradingOutcome(**outcome_data)
            success = self.outcome_tracker.log_outcome(outcome)
            
            if success:
                logger.info(f"Logged outcome for {outcome.symbol} {outcome.side}: {outcome.outcome}")
            
            return success
        except Exception as e:
            logger.error(f"Error logging trading outcome: {e}")
            return False
    
    def should_retrain(self, mode: str) -> bool:
        """Check if model should be retrained"""
        try:
            # Check if enough time has passed since last training
            last_training = self.last_training.get(mode)
            if last_training:
                time_since_training = datetime.now() - datetime.fromisoformat(last_training)
                if time_since_training < timedelta(hours=6):  # Minimum 6 hours between training
                    return False
            
            # Check if we have enough new data
            df = self.outcome_tracker.get_training_data(mode, days=7)  # Last 7 days
            if len(df) < 20:  # Need at least 20 new samples
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error checking retrain condition: {e}")
            return False
    
    def train_models_if_needed(self) -> Dict[str, Optional[ModelMetrics]]:
        """Train models if conditions are met"""
        results = {}
        
        if not self.ml_available or not self.model_trainer:
            logger.warning("ML system not available. Cannot train models.")
            return {"SAFE": None, "AGGRESSIVE": None}
        
        for mode in ["SAFE", "AGGRESSIVE"]:
            if self.should_retrain(mode):
                logger.info(f"Training {mode} model...")
                metrics = self.model_trainer.train_model(mode)
                results[mode] = metrics
                
                if metrics:
                    self.last_training[mode] = metrics.created_at
            else:
                results[mode] = None
        
        return results
    
    def get_system_status(self) -> Dict[str, Any]:
        """Get overall system status"""
        try:
            status = {
                "outcome_tracking": {
                    "total_outcomes": self._count_outcomes(),
                    "recent_outcomes": self._count_recent_outcomes()
                },
                "models": {
                    "safe_model": self.model_trainer.get_best_model("SAFE") if self.model_trainer else None,
                    "aggressive_model": self.model_trainer.get_best_model("AGGRESSIVE") if self.model_trainer else None
                },
                "bandit": self.bandit.get_strategy_performance() if self.bandit else {},
                "last_training": self.last_training,
                "ml_available": self.ml_available
            }
            
            return status
            
        except Exception as e:
            logger.error(f"Error getting system status: {e}")
            return {"error": str(e)}
    
    def _count_outcomes(self) -> int:
        """Count total outcomes in database"""
        try:
            conn = sqlite3.connect(self.outcome_tracker.db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM trading_outcomes")
            count = cursor.fetchone()[0]
            conn.close()
            return count
        except:
            return 0
    
    def _count_recent_outcomes(self) -> int:
        """Count outcomes from last 7 days"""
        try:
            cutoff_date = (datetime.now() - timedelta(days=7)).isoformat()
            conn = sqlite3.connect(self.outcome_tracker.db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM trading_outcomes WHERE timestamp >= ?", (cutoff_date,))
            count = cursor.fetchone()[0]
            conn.close()
            return count
        except:
            return 0

# Global instance
ml_system = MLLearningSystem()
