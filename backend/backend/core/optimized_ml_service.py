"""
Optimized ML Service with model persistence and cross-validation
"""
import os
import logging
import pickle
import numpy as np
from typing import Dict, List, Any, Optional, Tuple
from sklearn.ensemble import RandomForestRegressor, RandomForestClassifier
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.model_selection import cross_val_score, GridSearchCV
from sklearn.metrics import mean_squared_error, accuracy_score

logger = logging.getLogger(__name__)

class OptimizedMLService:
    """
    Optimized ML Service with model persistence and cross-validation
    """
    def __init__(self, models_dir: str = "ml_models"):
        # Initialize models directory
        self.models_dir = os.path.join(os.getcwd(), 'ml_models')
        self._ensure_models_directory()
        # Initialize model storage
        self.models = {}
        self.scalers = {}
        self.encoders = {}
        self.is_trained = False
        # Load existing models if available
        try:
            self._load_existing_models()
            logger.info("Optimized ML Service initialized with model persistence")
        except Exception as e:
            logger.warning(f"Could not load existing models: {e}")
            logger.info("Will train new models on first use")
    
    def _ensure_models_directory(self):
        """Ensure the models directory exists"""
        if not os.path.exists(self.models_dir):
            os.makedirs(self.models_dir)
            logger.info(f"Created models directory: {self.models_dir}")
    
    def _load_existing_models(self):
        """Load existing trained models from disk"""
        try:
            # Load market regime model
            regime_path = os.path.join(self.models_dir, 'market_regime_model.pkl')
            if os.path.exists(regime_path):
                with open(regime_path, 'rb') as f:
                    self.models['market_regime'] = pickle.load(f)
            
            # Load portfolio optimization model
            portfolio_path = os.path.join(self.models_dir, 'portfolio_optimization_model.pkl')
            if os.path.exists(portfolio_path):
                with open(portfolio_path, 'rb') as f:
                    self.models['portfolio_optimization'] = pickle.load(f)
            
            # Load scalers
            scaler_path = os.path.join(self.models_dir, 'scalers.pkl')
            if os.path.exists(scaler_path):
                with open(scaler_path, 'rb') as f:
                    self.scalers = pickle.load(f)
            
            self.is_trained = True
            logger.info("Successfully loaded existing models")
            
        except Exception as e:
            logger.error(f"Error loading existing models: {e}")
            raise
    
    def _save_models(self):
        """Save trained models to disk"""
        try:
            # Save market regime model
            if 'market_regime' in self.models:
                regime_path = os.path.join(self.models_dir, 'market_regime_model.pkl')
                with open(regime_path, 'wb') as f:
                    pickle.dump(self.models['market_regime'], f)
            
            # Save portfolio optimization model
            if 'portfolio_optimization' in self.models:
                portfolio_path = os.path.join(self.models_dir, 'portfolio_optimization_model.pkl')
                with open(portfolio_path, 'wb') as f:
                    pickle.dump(self.models['portfolio_optimization'], f)
            
            # Save scalers
            scaler_path = os.path.join(self.models_dir, 'scalers.pkl')
            with open(scaler_path, 'wb') as f:
                pickle.dump(self.scalers, f)
            
            logger.info("Successfully saved models to disk")
            
        except Exception as e:
            logger.error(f"Error saving models: {e}")
            raise
    
    def train_market_regime_model(self, X: np.ndarray, y: np.ndarray) -> Dict[str, Any]:
        """Train market regime classification model"""
        try:
            # Initialize scaler
            scaler = StandardScaler()
            X_scaled = scaler.fit_transform(X)
            self.scalers['market_regime'] = scaler
            
            # Initialize model with hyperparameter tuning
            model = RandomForestClassifier(
                n_estimators=100,
                max_depth=10,
                random_state=42
            )
            
            # Cross-validation
            cv_scores = cross_val_score(model, X_scaled, y, cv=5, scoring='accuracy')
            
            # Train final model
            model.fit(X_scaled, y)
            self.models['market_regime'] = model
            
            # Calculate performance metrics
            y_pred = model.predict(X_scaled)
            accuracy = accuracy_score(y, y_pred)
            
            logger.info(f"Market regime model trained with accuracy: {accuracy:.3f}")
            logger.info(f"Cross-validation scores: {cv_scores.mean():.3f} (+/- {cv_scores.std() * 2:.3f})")
            
            return {
                'accuracy': accuracy,
                'cv_scores': cv_scores.tolist(),
                'cv_mean': cv_scores.mean(),
                'cv_std': cv_scores.std()
            }
            
        except Exception as e:
            logger.error(f"Error training market regime model: {e}")
            raise
    
    def train_portfolio_optimization_model(self, X: np.ndarray, y: np.ndarray) -> Dict[str, Any]:
        """Train portfolio optimization regression model"""
        try:
            # Initialize scaler
            scaler = StandardScaler()
            X_scaled = scaler.fit_transform(X)
            self.scalers['portfolio_optimization'] = scaler
            
            # Initialize model
            model = RandomForestRegressor(
                n_estimators=100,
                max_depth=10,
                random_state=42
            )
            
            # Cross-validation
            cv_scores = cross_val_score(model, X_scaled, y, cv=5, scoring='neg_mean_squared_error')
            
            # Train final model
            model.fit(X_scaled, y)
            self.models['portfolio_optimization'] = model
            
            # Calculate performance metrics
            y_pred = model.predict(X_scaled)
            mse = mean_squared_error(y, y_pred)
            rmse = np.sqrt(mse)
            
            logger.info(f"Portfolio optimization model trained with RMSE: {rmse:.3f}")
            logger.info(f"Cross-validation scores: {-cv_scores.mean():.3f} (+/- {cv_scores.std() * 2:.3f})")
            
            return {
                'mse': mse,
                'rmse': rmse,
                'cv_scores': cv_scores.tolist(),
                'cv_mean': -cv_scores.mean(),
                'cv_std': cv_scores.std()
            }
            
        except Exception as e:
            logger.error(f"Error training portfolio optimization model: {e}")
            raise
    
    def predict_market_regime(self, X: np.ndarray) -> np.ndarray:
        """Predict market regime"""
        try:
            if 'market_regime' not in self.models:
                raise ValueError("Market regime model not trained")
            
            scaler = self.scalers['market_regime']
            X_scaled = scaler.transform(X)
            
            predictions = self.models['market_regime'].predict(X_scaled)
            probabilities = self.models['market_regime'].predict_proba(X_scaled)
            
            return predictions, probabilities
            
        except Exception as e:
            logger.error(f"Error predicting market regime: {e}")
            raise
    
    def predict_portfolio_optimization(self, X: np.ndarray) -> np.ndarray:
        """Predict portfolio optimization"""
        try:
            if 'portfolio_optimization' not in self.models:
                raise ValueError("Portfolio optimization model not trained")
            
            scaler = self.scalers['portfolio_optimization']
            X_scaled = scaler.transform(X)
            
            predictions = self.models['portfolio_optimization'].predict(X_scaled)
            
            return predictions
            
        except Exception as e:
            logger.error(f"Error predicting portfolio optimization: {e}")
            raise
    
    def get_feature_importance(self, model_name: str) -> Dict[str, float]:
        """Get feature importance for a model"""
        try:
            if model_name not in self.models:
                raise ValueError(f"Model {model_name} not found")
            
            model = self.models[model_name]
            if hasattr(model, 'feature_importances_'):
                return dict(zip(range(len(model.feature_importances_)), model.feature_importances_))
            else:
                return {}
                
        except Exception as e:
            logger.error(f"Error getting feature importance: {e}")
            return {}
    
    def get_model_status(self) -> Dict[str, Any]:
        """Get status of all models"""
        return {
            'is_trained': self.is_trained,
            'models_available': list(self.models.keys()),
            'scalers_available': list(self.scalers.keys()),
            'models_directory': self.models_dir
        }