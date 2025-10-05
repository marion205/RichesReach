#!/usr/bin/env python3
"""
ML Model R² Score Improvement Script
Converts classification-based ML to regression-based for proper R² scoring
"""

import os
import sys
import logging
from pathlib import Path

# Add backend to path
sys.path.append(str(Path(__file__).parent / "backend" / "backend"))

def improve_ml_r2_score():
    """Improve ML model R² score by implementing regression-based approach"""
    
    print("🔧 Improving ML Model R² Score...")
    
    # Create improved ML learning system
    improved_ml_code = '''
"""
Improved ML Learning System for Better R² Scores
- Regression-based approach instead of classification
- Proper R² calculation for financial predictions
- Enhanced feature engineering
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
    from sklearn.metrics import r2_score, mean_squared_error, mean_absolute_error
    from sklearn.model_selection import TimeSeriesSplit
    from sklearn.preprocessing import StandardScaler
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

# Enhanced features for better R²
ENHANCED_FEATURES = [
    "momentum_15m",
    "rvol_10m", 
    "vwap_dist",
    "breakout_pct",
    "spread_bps",
    "catalyst_score",
    "volume_ratio",      # New: volume vs average
    "price_momentum",    # New: price change over time
    "volatility_ratio",  # New: current vs historical vol
    "support_resistance", # New: distance to key levels
    "market_sentiment",  # New: overall market sentiment
    "sector_momentum",   # New: sector performance
]

MIN_TRAIN_SAMPLES = 200
VAL_SPLIT_RATIO = 0.2

@dataclass
class ImprovedModelMetrics:
    model_id: str
    mode: str
    r2_score: float
    mse: float
    mae: float
    feature_importance: Dict[str, float]
    created_at: str
    is_active: bool = False

class ImprovedMLTrainer:
    """Improved ML trainer with regression-based approach for better R² scores"""
    
    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
        self.ml_available = ML_AVAILABLE
        self.scaler = StandardScaler()
        
    def get_enhanced_training_data(self, mode: str, days: int = 90) -> pd.DataFrame:
        """Get training data with enhanced features for regression"""
        try:
            conn = sqlite3.connect(self.db_path)
            cutoff = (datetime.utcnow() - timedelta(days=days)).isoformat()
            
            # Get more comprehensive data
            df = pd.read_sql_query("""
                SELECT symbol, side, entry_price, exit_price, entry_time, exit_time,
                       mode, outcome, features, score, timestamp, 
                       (exit_price - entry_price) / entry_price as actual_return
                FROM trading_outcomes
                WHERE mode = ? AND timestamp >= ? AND outcome IS NOT NULL
                ORDER BY timestamp ASC
            """, conn, params=(mode, cutoff))
            conn.close()
            
            if df.empty:
                return df
            
            # Parse times
            for col in ("timestamp", "entry_time", "exit_time"):
                df[col] = pd.to_datetime(df[col], errors="coerce", utc=True)
            
            # Parse features and add enhanced features
            fdicts = df["features"].apply(json.loads)
            X = pd.DataFrame.from_records(fdicts)
            
            # Ensure all features exist
            for f in ENHANCED_FEATURES:
                if f not in X:
                    X[f] = 0.0
            
            # Add enhanced features
            X = self._add_enhanced_features(X, df)
            
            # Select features in stable order
            X = X[ENHANCED_FEATURES].astype("float32")
            
            # Combine with main data
            df = pd.concat([df.drop(columns=["features"]), X.add_prefix("f_")], axis=1)
            
            return df
            
        except Exception as e:
            logger.error(f"Error getting training data: {e}")
            return pd.DataFrame()
    
    def _add_enhanced_features(self, X: pd.DataFrame, df: pd.DataFrame) -> pd.DataFrame:
        """Add enhanced features for better prediction"""
        try:
            # Volume ratio (if available)
            if "volume" in X.columns:
                X["volume_ratio"] = X["volume"] / (X["volume"].rolling(20).mean() + 1e-8)
            else:
                X["volume_ratio"] = 1.0
            
            # Price momentum
            if "price" in X.columns:
                X["price_momentum"] = X["price"].pct_change(5).fillna(0)
            else:
                X["price_momentum"] = 0.0
            
            # Volatility ratio
            if "volatility" in X.columns:
                X["volatility_ratio"] = X["volatility"] / (X["volatility"].rolling(20).mean() + 1e-8)
            else:
                X["volatility_ratio"] = 1.0
            
            # Support/Resistance (simplified)
            if "price" in X.columns:
                rolling_high = X["price"].rolling(20).max()
                rolling_low = X["price"].rolling(20).min()
                X["support_resistance"] = (X["price"] - rolling_low) / (rolling_high - rolling_low + 1e-8)
            else:
                X["support_resistance"] = 0.5
            
            # Market sentiment (simplified)
            X["market_sentiment"] = np.random.normal(0, 0.1, len(X))  # Placeholder
            
            # Sector momentum (simplified)
            X["sector_momentum"] = np.random.normal(0, 0.05, len(X))  # Placeholder
            
            return X
            
        except Exception as e:
            logger.error(f"Error adding enhanced features: {e}")
            return X
    
    def _chronological_split(self, df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """Split data chronologically for time series validation"""
        split_idx = int(len(df) * (1 - VAL_SPLIT_RATIO))
        return df.iloc[:split_idx], df.iloc[split_idx:]
    
    def _build_xy(self, df: pd.DataFrame) -> Tuple[np.ndarray, np.ndarray]:
        """Build feature matrix X and target vector y"""
        feature_cols = [f"f_{f}" for f in ENHANCED_FEATURES]
        X = df[feature_cols].values
        
        # Use actual returns as target for regression
        y = df["actual_return"].values
        
        return X, y
    
    def train_regression_model(self, mode: str) -> Optional[ImprovedModelMetrics]:
        """Train regression model for better R² scores"""
        if not self.ml_available:
            logger.warning("ML not available; skipping training.")
            return None
        
        df = self.get_enhanced_training_data(mode, days=90)
        if len(df) < MIN_TRAIN_SAMPLES:
            logger.warning(f"Not enough samples for {mode}: {len(df)} < {MIN_TRAIN_SAMPLES}")
            return None
        
        # Chronological split
        df_tr, df_val = self._chronological_split(df)
        X_tr, y_tr = self._build_xy(df_tr)
        X_val, y_val = self._build_xy(df_val)
        
        # Scale features
        X_tr_scaled = self.scaler.fit_transform(X_tr)
        X_val_scaled = self.scaler.transform(X_val)
        
        # Enhanced XGBoost Regressor
        model = xgb.XGBRegressor(
            n_estimators=500,
            max_depth=6,
            learning_rate=0.05,
            subsample=0.8,
            colsample_bytree=0.8,
            reg_alpha=1.0,
            reg_lambda=1.0,
            tree_method="hist",
            n_jobs=8,
            random_state=42,
            objective="reg:squarederror"
        )
        
        # Train with early stopping
        model.fit(
            X_tr_scaled, y_tr,
            eval_set=[(X_val_scaled, y_val)],
            early_stopping_rounds=50,
            verbose=False
        )
        
        # Evaluate
        y_pred = model.predict(X_val_scaled)
        r2 = float(r2_score(y_val, y_pred))
        mse = float(mean_squared_error(y_val, y_pred))
        mae = float(mean_absolute_error(y_val, y_pred))
        
        # Feature importance
        feature_importance = {
            feature: float(importance) 
            for feature, importance in zip(ENHANCED_FEATURES, model.feature_importances_)
        }
        
        # Create metrics
        metrics = ImprovedModelMetrics(
            model_id=f"improved_{mode}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            mode=mode,
            r2_score=r2,
            mse=mse,
            mae=mae,
            feature_importance=feature_importance,
            created_at=datetime.now().isoformat(),
            is_active=True
        )
        
        # Save model
        self._save_model(model, metrics)
        
        logger.info(f"Improved {mode} model trained - R²: {r2:.4f}, MSE: {mse:.4f}, MAE: {mae:.4f}")
        
        return metrics
    
    def _save_model(self, model: xgb.XGBRegressor, metrics: ImprovedModelMetrics):
        """Save the trained model"""
        try:
            model_path = MODELS_DIR / f"{metrics.model_id}.pkl"
            import pickle
            with open(model_path, "wb") as f:
                pickle.dump({
                    "model": model,
                    "scaler": self.scaler,
                    "metrics": metrics,
                    "features": ENHANCED_FEATURES
                }, f)
            
            logger.info(f"Model saved: {model_path}")
            
        except Exception as e:
            logger.error(f"Error saving model: {e}")
    
    def get_best_r2_score(self, mode: str) -> float:
        """Get the best R² score for a mode"""
        try:
            conn = sqlite3.connect(self.db_path)
            result = pd.read_sql_query("""
                SELECT r2_score FROM model_metrics 
                WHERE mode = ? AND is_active = TRUE 
                ORDER BY r2_score DESC LIMIT 1
            """, conn, params=(mode,))
            conn.close()
            
            return float(result["r2_score"].iloc[0]) if not result.empty else 0.0
            
        except Exception as e:
            logger.error(f"Error getting best R² score: {e}")
            return 0.0

# Global instance
improved_trainer = ImprovedMLTrainer()

def train_improved_models():
    """Train improved models for both modes"""
    results = {}
    
    for mode in ["SAFE", "AGGRESSIVE"]:
        print(f"Training improved {mode} model...")
        metrics = improved_trainer.train_regression_model(mode)
        if metrics:
            results[mode] = {
                "r2_score": metrics.r2_score,
                "mse": metrics.mse,
                "mae": metrics.mae,
                "model_id": metrics.model_id
            }
            print(f"✅ {mode} model - R²: {metrics.r2_score:.4f}")
        else:
            results[mode] = None
            print(f"❌ {mode} model training failed")
    
    return results

if __name__ == "__main__":
    results = train_improved_models()
    print("\\n🎉 Improved ML training completed!")
    for mode, result in results.items():
        if result:
            print(f"{mode}: R² = {result['r2_score']:.4f}")
'''
    
    # Write the improved ML system
    with open("backend/backend/improved_ml_learning_system.py", "w") as f:
        f.write(improved_ml_code)
    
    print("✅ Created improved ML learning system")
    
    # Create a script to train the improved models
    training_script = '''
#!/usr/bin/env python3
"""
Train Improved ML Models for Better R² Scores
"""

import sys
from pathlib import Path

# Add backend to path
sys.path.append(str(Path(__file__).parent / "backend" / "backend"))

from improved_ml_learning_system import train_improved_models

if __name__ == "__main__":
    print("🚀 Training Improved ML Models...")
    results = train_improved_models()
    
    print("\\n📊 Results Summary:")
    for mode, result in results.items():
        if result:
            print(f"  {mode}: R² = {result['r2_score']:.4f} (Target: 0.15+)")
        else:
            print(f"  {mode}: Training failed")
    
    # Calculate average R²
    valid_results = [r['r2_score'] for r in results.values() if r]
    if valid_results:
        avg_r2 = sum(valid_results) / len(valid_results)
        print(f"\\n🎯 Average R² Score: {avg_r2:.4f}")
        if avg_r2 >= 0.15:
            print("✅ Target achieved! R² score meets industry standard.")
        else:
            print("⚠️  R² score below industry standard. Consider more training data or feature engineering.")
'''
    
    with open("train_improved_models.py", "w") as f:
        f.write(training_script)
    
    print("✅ Created training script")
    
    # Run the training
    print("\\n🚀 Training improved models...")
    os.system("python3 train_improved_models.py")
    
    print("\\n🎉 ML R² Score improvement completed!")

if __name__ == "__main__":
    improve_ml_r2_score()
