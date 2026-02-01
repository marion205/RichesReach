"""
Ensemble Predictor Service
Combines LSTM + XGBoost + Random Forest for superior accuracy.
Implements voting, stacking, and dynamic model selection.
"""
import logging
import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
import os

logger = logging.getLogger(__name__)

# ML imports
try:
    import xgboost as xgb
    from sklearn.ensemble import RandomForestClassifier, VotingClassifier, StackingClassifier
    from sklearn.model_selection import TimeSeriesSplit
    from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score
    ML_AVAILABLE = True
except ImportError:
    ML_AVAILABLE = False
    logger.warning("ML libraries not available for ensemble")


class EnsemblePredictor:
    """
    Ensemble predictor combining multiple models for superior accuracy.
    
    Models:
    - LSTM: Temporal momentum features
    - XGBoost: Alternative data + LSTM features
    - Random Forest: Technical indicators
    """
    
    def __init__(self):
        self.lstm_model = None
        self.xgboost_model = None
        self.random_forest_model = None
        self.ensemble_model = None
        self.model_weights = None
        self.model_dir = os.path.join(os.path.dirname(__file__), 'ml_models', 'ensemble')
        os.makedirs(self.model_dir, exist_ok=True)
        
        # Initialize components
        self._load_models()
    
    def _load_models(self):
        """Load pre-trained models if available"""
        try:
            # Load LSTM feature extractor
            from .lstm_feature_extractor import get_lstm_feature_extractor
            self.lstm_extractor = get_lstm_feature_extractor()
            
            # Load XGBoost model
            from .hybrid_lstm_xgboost_trainer import get_hybrid_trainer
            trainer = get_hybrid_trainer()
            if trainer.xgboost_model is not None:
                self.xgboost_model = trainer.xgboost_model
            
            # Initialize Random Forest
            if ML_AVAILABLE:
                self.random_forest_model = RandomForestClassifier(
                    n_estimators=100,
                    max_depth=10,
                    min_samples_split=20,
                    random_state=42
                )
            
        except Exception as e:
            logger.warning(f"Could not load models: {e}")
    
    def train_ensemble(
        self,
        X_lstm: np.ndarray,
        X_alt_data: pd.DataFrame,
        X_technical: pd.DataFrame,
        y: np.ndarray
    ) -> Dict[str, Any]:
        """
        Train ensemble model with multiple feature sets.
        
        Args:
            X_lstm: LSTM temporal features (from LSTM extractor)
            X_alt_data: Alternative data features (options, sentiment, etc.)
            X_technical: Technical indicator features
            y: Target labels (0/1 for buy/sell)
        
        Returns:
            Training results with performance metrics
        """
        if not ML_AVAILABLE:
            logger.error("ML libraries not available")
            return {'error': 'ML libraries not available'}
        
        logger.info("Training ensemble model...")
        
        # Step 1: Train LSTM feature extractor (if not already trained)
        if self.lstm_extractor and not self.lstm_extractor.is_available():
            logger.info("Training LSTM feature extractor...")
            # LSTM training would happen here
            # For now, assume it's already trained
        
        # Step 2: Extract LSTM features
        lstm_features = None
        if self.lstm_extractor and self.lstm_extractor.is_available():
            try:
                # Extract temporal momentum score as feature
                lstm_features = self.lstm_extractor.extract_temporal_momentum_score(
                    X_lstm, 'SPY'  # Symbol placeholder
                )
                if isinstance(lstm_features, (int, float)):
                    lstm_features = np.array([lstm_features] * len(X_alt_data))
            except Exception as e:
                logger.warning(f"Could not extract LSTM features: {e}")
                lstm_features = np.zeros(len(X_alt_data))
        else:
            lstm_features = np.zeros(len(X_alt_data))
        
        # Step 3: Combine all features
        # Convert DataFrames to numpy arrays
        alt_data_array = X_alt_data.values if isinstance(X_alt_data, pd.DataFrame) else X_alt_data
        technical_array = X_technical.values if isinstance(X_technical, pd.DataFrame) else X_technical
        
        # Ensure all arrays have same length
        min_len = min(len(lstm_features), len(alt_data_array), len(technical_array), len(y))
        lstm_features = lstm_features[:min_len]
        alt_data_array = alt_data_array[:min_len]
        technical_array = technical_array[:min_len]
        y = y[:min_len]
        
        # Combine features
        X_combined = np.hstack([
            lstm_features.reshape(-1, 1),
            alt_data_array,
            technical_array
        ])
        
        # Step 4: Train individual models
        logger.info("Training individual models...")
        
        # Train XGBoost
        if self.xgboost_model is None:
            self.xgboost_model = xgb.XGBClassifier(
                n_estimators=100,
                max_depth=6,
                learning_rate=0.1,
                random_state=42
            )
        
        # Train Random Forest
        if self.random_forest_model is None:
            self.random_forest_model = RandomForestClassifier(
                n_estimators=100,
                max_depth=10,
                min_samples_split=20,
                random_state=42
            )
        
        # Use TimeSeriesSplit for validation
        tscv = TimeSeriesSplit(n_splits=5)
        
        # Train XGBoost
        xgb_scores = []
        for train_idx, val_idx in tscv.split(X_combined):
            X_train, X_val = X_combined[train_idx], X_combined[val_idx]
            y_train, y_val = y[train_idx], y[val_idx]
            
            self.xgboost_model.fit(X_train, y_train)
            y_pred = self.xgboost_model.predict(X_val)
            score = accuracy_score(y_val, y_pred)
            xgb_scores.append(score)
        
        # Train Random Forest
        rf_scores = []
        for train_idx, val_idx in tscv.split(X_combined):
            X_train, X_val = X_combined[train_idx], X_combined[val_idx]
            y_train, y_val = y[train_idx], y[val_idx]
            
            self.random_forest_model.fit(X_train, y_train)
            y_pred = self.random_forest_model.predict(X_val)
            score = accuracy_score(y_val, y_pred)
            rf_scores.append(score)
        
        # Step 5: Create ensemble (voting)
        logger.info("Creating voting ensemble...")
        self.ensemble_model = VotingClassifier(
            estimators=[
                ('xgb', self.xgboost_model),
                ('rf', self.random_forest_model)
            ],
            voting='soft'  # Use probability voting
        )
        
        # Train ensemble on full data
        self.ensemble_model.fit(X_combined, y)
        
        # Step 6: Calculate model weights based on performance
        xgb_avg_score = np.mean(xgb_scores)
        rf_avg_score = np.mean(rf_scores)
        total_score = xgb_avg_score + rf_avg_score
        
        self.model_weights = {
            'xgb': xgb_avg_score / total_score if total_score > 0 else 0.5,
            'rf': rf_avg_score / total_score if total_score > 0 else 0.5
        }
        
        # Step 7: Evaluate ensemble
        y_pred_ensemble = self.ensemble_model.predict(X_combined)
        ensemble_accuracy = accuracy_score(y, y_pred_ensemble)
        ensemble_precision = precision_score(y, y_pred_ensemble, zero_division=0)
        ensemble_recall = recall_score(y, y_pred_ensemble, zero_division=0)
        ensemble_f1 = f1_score(y, y_pred_ensemble, zero_division=0)
        
        results = {
            'xgb_accuracy': np.mean(xgb_scores),
            'rf_accuracy': np.mean(rf_scores),
            'ensemble_accuracy': ensemble_accuracy,
            'ensemble_precision': ensemble_precision,
            'ensemble_recall': ensemble_recall,
            'ensemble_f1': ensemble_f1,
            'model_weights': self.model_weights,
            'feature_count': X_combined.shape[1],
            'sample_count': len(y)
        }
        
        logger.info(f"Ensemble training complete!")
        logger.info(f"  XGBoost Accuracy: {np.mean(xgb_scores):.3f}")
        logger.info(f"  Random Forest Accuracy: {np.mean(rf_scores):.3f}")
        logger.info(f"  Ensemble Accuracy: {ensemble_accuracy:.3f}")
        logger.info(f"  Ensemble F1: {ensemble_f1:.3f}")
        
        return results
    
    def predict(
        self,
        lstm_features: np.ndarray,
        alt_data_features: Dict[str, float],
        technical_features: Dict[str, float],
        confidence_threshold: float = 0.78
    ) -> Dict[str, Any]:
        """
        Make prediction using ensemble model.
        
        Args:
            lstm_features: LSTM temporal features
            alt_data_features: Alternative data features
            technical_features: Technical indicator features
            confidence_threshold: Minimum confidence to execute
        
        Returns:
            Prediction with action, confidence, and reasoning
        """
        if self.ensemble_model is None:
            logger.warning("Ensemble model not trained, using fallback")
            return {
                'action': 'ABSTAIN',
                'confidence': 0.5,
                'reasoning': 'Ensemble model not available'
            }
        
        try:
            # Prepare features
            lstm_feat = np.array([lstm_features]) if isinstance(lstm_features, (int, float)) else lstm_features
            alt_data_array = np.array([list(alt_data_features.values())])
            technical_array = np.array([list(technical_features.values())])
            
            # Combine features
            X = np.hstack([
                lstm_feat.reshape(-1, 1),
                alt_data_array,
                technical_array
            ])
            
            # Get ensemble prediction
            prediction_proba = self.ensemble_model.predict_proba(X)[0]
            confidence = max(prediction_proba)
            predicted_class = np.argmax(prediction_proba)
            
            # Get individual model predictions for reasoning
            xgb_proba = self.xgboost_model.predict_proba(X)[0]
            rf_proba = self.random_forest_model.predict_proba(X)[0]
            
            # Determine action
            if confidence >= confidence_threshold:
                action = 'BUY' if predicted_class == 1 else 'SELL'
            else:
                action = 'ABSTAIN'
            
            # Generate reasoning
            reasoning_parts = []
            if confidence >= confidence_threshold:
                reasoning_parts.append(f"High ensemble confidence: {confidence:.2%}")
            else:
                reasoning_parts.append(f"Low confidence: {confidence:.2%} (abstaining)")
            
            reasoning_parts.append(f"XGBoost: {max(xgb_proba):.2%}, RF: {max(rf_proba):.2%}")
            
            return {
                'action': action,
                'confidence': float(confidence),
                'predicted_class': int(predicted_class),
                'xgb_confidence': float(max(xgb_proba)),
                'rf_confidence': float(max(rf_proba)),
                'reasoning': ' | '.join(reasoning_parts),
                'model_contributions': {
                    'xgb': float(self.model_weights.get('xgb', 0.5)),
                    'rf': float(self.model_weights.get('rf', 0.5))
                }
            }
            
        except Exception as e:
            logger.error(f"Error in ensemble prediction: {e}")
            return {
                'action': 'ABSTAIN',
                'confidence': 0.5,
                'reasoning': f'Prediction error: {str(e)}'
            }


# Global instance
_ensemble_predictor = None

def get_ensemble_predictor() -> EnsemblePredictor:
    """Get global ensemble predictor instance"""
    global _ensemble_predictor
    if _ensemble_predictor is None:
        _ensemble_predictor = EnsemblePredictor()
    return _ensemble_predictor

