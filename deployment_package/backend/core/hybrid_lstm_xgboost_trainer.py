"""
Hybrid LSTM + XGBoost Trainer
Production-grade training pipeline with net-of-costs labeling and proper scaling persistence.
"""
import logging
import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timedelta
import os
import joblib
import pickle

logger = logging.getLogger(__name__)

# Try to import ML libraries
try:
    import xgboost as xgb
    from sklearn.model_selection import TimeSeriesSplit
    from sklearn.preprocessing import StandardScaler
    from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score
    XGBOOST_AVAILABLE = True
except ImportError:
    XGBOOST_AVAILABLE = False
    logger.warning("XGBoost not available")

try:
    import tensorflow as tf
    TENSORFLOW_AVAILABLE = True
except ImportError:
    TENSORFLOW_AVAILABLE = False


class HybridLSTMXGBoostTrainer:
    """
    Trains hybrid LSTM + XGBoost model with net-of-costs labeling.
    LSTM extracts temporal momentum, XGBoost makes final decision.
    """
    
    def __init__(self):
        self.lstm_extractor = None
        self.xgboost_model = None
        self.scaler = None
        self.model_dir = os.path.join(os.path.dirname(__file__), 'ml_models', 'hybrid_lstm_xgboost')
        os.makedirs(self.model_dir, exist_ok=True)
        
        # Initialize LSTM extractor
        if TENSORFLOW_AVAILABLE:
            from .lstm_feature_extractor import get_lstm_feature_extractor
            self.lstm_extractor = get_lstm_feature_extractor()
    
    def label_net_of_costs(
        self,
        df: pd.DataFrame,
        price_col: str = 'close',
        fee_bps: float = 5.0,
        slippage_bps: float = 2.0,
        target_col: str = 'next_return'
    ) -> pd.DataFrame:
        """
        Label targets net of costs (CRITICAL for winning).
        Only labels as "win" if return > total friction costs.
        
        Args:
            df: DataFrame with price data
            price_col: Column name for price
            fee_bps: Broker commission in basis points
            slippage_bps: Expected slippage in basis points
            target_col: Column name for target (will be created)
        
        Returns:
            DataFrame with net-of-costs labels
        """
        df = df.copy()
        
        # Calculate total friction (fees + slippage)
        total_friction = (fee_bps + slippage_bps) / 10000.0  # Convert to decimal
        
        # Calculate raw return (next period)
        df['raw_return'] = df[price_col].pct_change().shift(-1)
        
        # Label: 1 if return > friction, else 0 (abstain/loss)
        df[target_col] = (df['raw_return'] > total_friction).astype(int)
        
        # Also store net return for analysis
        df['net_return'] = df['raw_return'] - total_friction
        
        logger.info(f"Net-of-costs labeling: {df[target_col].sum()} wins out of {len(df)} samples")
        logger.info(f"Win rate after costs: {df[target_col].mean():.2%}")
        
        return df
    
    def prepare_hybrid_dataset(
        self,
        price_sequences: np.ndarray,
        alt_data_df: pd.DataFrame,
        targets: np.ndarray = None
    ) -> Tuple[pd.DataFrame, Optional[np.ndarray]]:
        """
        Prepare hybrid dataset: LSTM features + alternative data.
        
        Args:
            price_sequences: 3D array (samples, timesteps, features) for LSTM
            alt_data_df: DataFrame with alternative data features
            targets: Optional target labels (for training)
        
        Returns:
            Tuple of (X_hybrid, y) where X_hybrid includes LSTM momentum score
        """
        try:
            # 1. Get temporal momentum scores from LSTM
            if self.lstm_extractor and self.lstm_extractor.lstm_available:
                temporal_scores = []
                for seq in price_sequences:
                    score = self.lstm_extractor.extract_temporal_momentum_score(seq)
                    temporal_scores.append(score)
                
                # Add LSTM momentum score to alternative data
                alt_data_df = alt_data_df.copy()
                alt_data_df['lstm_temporal_momentum_score'] = temporal_scores
            else:
                # No LSTM available, use default
                alt_data_df['lstm_temporal_momentum_score'] = 0.0
            
            # 2. Return hybrid features
            return alt_data_df, targets
            
        except Exception as e:
            logger.error(f"Error preparing hybrid dataset: {e}")
            return alt_data_df, targets
    
    def train_hybrid_model(
        self,
        X_hybrid: pd.DataFrame,
        y: np.ndarray,
        validation_split: float = 0.2
    ) -> Dict[str, Any]:
        """
        Train hybrid LSTM + XGBoost model.
        
        Args:
            X_hybrid: Hybrid features (alternative data + LSTM momentum score)
            y: Target labels (net-of-costs)
            validation_split: Fraction for validation
        
        Returns:
            Training results and metrics
        """
        if not XGBOOST_AVAILABLE:
            return {'error': 'XGBoost not available'}
        
        try:
            # Use TimeSeriesSplit for financial data (no look-ahead bias)
            tscv = TimeSeriesSplit(n_splits=5)
            
            # Split data
            split_idx = int(len(X_hybrid) * (1 - validation_split))
            X_train, X_val = X_hybrid[:split_idx], X_hybrid[split_idx:]
            y_train, y_val = y[:split_idx], y[split_idx:]
            
            # Train XGBoost model
            self.xgboost_model = xgb.XGBClassifier(
                n_estimators=1000,
                max_depth=6,
                learning_rate=0.01,
                subsample=0.8,
                colsample_bytree=0.8,
                eval_metric='logloss',
                random_state=42
            )
            
            # Cross-validation
            cv_scores = []
            for train_idx, val_idx in tscv.split(X_train):
                X_cv_train, X_cv_val = X_train.iloc[train_idx], X_train.iloc[val_idx]
                y_cv_train, y_cv_val = y_train[train_idx], y_train[val_idx]
                
                self.xgboost_model.fit(
                    X_cv_train, y_cv_train,
                    eval_set=[(X_cv_val, y_cv_val)],
                    early_stopping_rounds=50,
                    verbose=False
                )
                
                y_pred = self.xgboost_model.predict(X_cv_val)
                cv_score = accuracy_score(y_cv_val, y_pred)
                cv_scores.append(cv_score)
            
            # Train on full training set
            self.xgboost_model.fit(
                X_train, y_train,
                eval_set=[(X_val, y_val)],
                early_stopping_rounds=50,
                verbose=False
            )
            
            # Evaluate
            y_pred_train = self.xgboost_model.predict(X_train)
            y_pred_val = self.xgboost_model.predict(X_val)
            
            train_acc = accuracy_score(y_train, y_pred_train)
            val_acc = accuracy_score(y_val, y_pred_val)
            
            # Feature importance
            feature_importance = dict(zip(
                X_hybrid.columns,
                self.xgboost_model.feature_importances_
            ))
            
            # Save models
            self._save_models()
            
            results = {
                'train_accuracy': float(train_acc),
                'val_accuracy': float(val_acc),
                'cv_mean': float(np.mean(cv_scores)),
                'cv_std': float(np.std(cv_scores)),
                'feature_importance': {k: float(v) for k, v in feature_importance.items()},
                'model_saved': True
            }
            
            logger.info(f"✅ Hybrid model trained: CV accuracy = {np.mean(cv_scores):.3f} ± {np.std(cv_scores):.3f}")
            
            return results
            
        except Exception as e:
            logger.error(f"Error training hybrid model: {e}", exc_info=True)
            return {'error': str(e)}
    
    def predict_with_abstention(
        self,
        X_hybrid: pd.DataFrame,
        confidence_threshold: float = 0.78
    ) -> Tuple[str, float]:
        """
        Make prediction with abstention (only trade if high confidence).
        
        Args:
            X_hybrid: Hybrid features
            confidence_threshold: Minimum probability to execute (default: 0.78)
        
        Returns:
            Tuple of (action, confidence) where action is 'BUY', 'SELL', or 'ABSTAIN'
        """
        if self.xgboost_model is None:
            return 'ABSTAIN', 0.0
        
        try:
            # Get prediction probability
            proba = self.xgboost_model.predict_proba(X_hybrid)[0]
            confidence = float(max(proba))
            predicted_class = int(np.argmax(proba))
            
            # Apply abstention rule
            if confidence >= confidence_threshold:
                action = 'BUY' if predicted_class == 1 else 'SELL'
            else:
                action = 'ABSTAIN'
            
            return action, confidence
            
        except Exception as e:
            logger.error(f"Error in prediction: {e}")
            return 'ABSTAIN', 0.0
    
    def _save_models(self):
        """Save models and scaler for persistence"""
        try:
            # Save XGBoost model
            if self.xgboost_model:
                xgb_path = os.path.join(self.model_dir, 'xgboost_model.pkl')
                joblib.dump(self.xgboost_model, xgb_path)
            
            # Save LSTM scaler (if available)
            if self.lstm_extractor and self.lstm_extractor.scaler:
                scaler_path = os.path.join(self.model_dir, 'lstm_scaler.pkl')
                joblib.dump(self.lstm_extractor.scaler, scaler_path)
            
            logger.info("✅ Models saved for persistence")
            
        except Exception as e:
            logger.error(f"Error saving models: {e}")
    
    def _load_models(self):
        """Load saved models"""
        try:
            # Load XGBoost
            xgb_path = os.path.join(self.model_dir, 'xgboost_model.pkl')
            if os.path.exists(xgb_path):
                self.xgboost_model = joblib.load(xgb_path)
            
            # Load LSTM scaler
            if self.lstm_extractor:
                scaler_path = os.path.join(self.model_dir, 'lstm_scaler.pkl')
                if os.path.exists(scaler_path):
                    self.lstm_extractor.scaler = joblib.load(scaler_path)
            
            logger.info("✅ Models loaded from disk")
            
        except Exception as e:
            logger.error(f"Error loading models: {e}")


# Global instance
_hybrid_trainer = None

def get_hybrid_trainer() -> HybridLSTMXGBoostTrainer:
    """Get global hybrid trainer instance"""
    global _hybrid_trainer
    if _hybrid_trainer is None:
        _hybrid_trainer = HybridLSTMXGBoostTrainer()
    return _hybrid_trainer

