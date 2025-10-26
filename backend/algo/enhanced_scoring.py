"""
Enhanced Scoring Algorithm with Machine Learning
Sophisticated pick scoring with adaptive learning
"""

import asyncio
import logging
import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timedelta
from dataclasses import dataclass
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.linear_model import Ridge
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error, r2_score
import joblib
import os

from .advanced_features import AdvancedFeatures, AdvancedIntradayCalculator
from ..market.providers.base import MarketDataProvider


@dataclass
class ScoringModel:
    """Scoring model configuration"""
    name: str
    model_type: str
    features: List[str]
    weights: Dict[str, float]
    performance_metrics: Dict[str, float]
    last_trained: datetime
    is_active: bool


@dataclass
class PickScore:
    """Enhanced pick score with confidence intervals"""
    symbol: str
    side: str
    base_score: float
    confidence_score: float
    risk_score: float
    
    # Model predictions
    ml_score: float
    ensemble_score: float
    
    # Confidence intervals
    score_lower_bound: float
    score_upper_bound: float
    
    # Feature contributions
    feature_contributions: Dict[str, float]
    
    # Model metadata
    model_used: str
    prediction_confidence: float
    
    # Timestamp
    timestamp: datetime


class EnhancedScoringEngine:
    """Enhanced scoring engine with ML capabilities"""
    
    def __init__(self, market_data_provider: MarketDataProvider):
        self.market_data_provider = market_data_provider
        self.logger = logging.getLogger(__name__)
        
        # Initialize models
        self.models = {}
        self.scalers = {}
        self.feature_importance = {}
        
        # Model configurations
        self.model_configs = {
            "momentum_model": {
                "type": "RandomForestRegressor",
                "params": {"n_estimators": 100, "max_depth": 10, "random_state": 42},
                "features": ["momentum_5", "momentum_10", "momentum_20", "rsi_14", "macd_signal"]
            },
            "volume_model": {
                "type": "GradientBoostingRegressor", 
                "params": {"n_estimators": 100, "learning_rate": 0.1, "random_state": 42},
                "features": ["rvol_10", "volume_spike", "vwap_distance", "volume_stability"]
            },
            "technical_model": {
                "type": "Ridge",
                "params": {"alpha": 1.0, "random_state": 42},
                "features": ["rsi_14", "macd_signal", "bb_position", "atr_percent"]
            },
            "ensemble_model": {
                "type": "ensemble",
                "params": {},
                "features": ["momentum_score", "volume_score", "technical_score", "microstructure_score"]
            }
        }
        
        # Historical performance tracking
        self.performance_history = []
        self.model_performance = {}
        
        # Feature engineering
        self.feature_engineering = FeatureEngineering()
        
        # Load existing models if available
        self._load_models()
    
    async def calculate_enhanced_score(
        self, 
        symbol: str, 
        side: str, 
        features: AdvancedFeatures
    ) -> PickScore:
        """Calculate enhanced score with ML predictions"""
        
        try:
            # Extract features for scoring
            scoring_features = self.feature_engineering.extract_scoring_features(features)
            
            # Calculate base scores
            base_score = self._calculate_base_score(scoring_features, side)
            confidence_score = self._calculate_confidence_score(scoring_features)
            risk_score = self._calculate_risk_score(scoring_features)
            
            # ML predictions
            ml_score = await self._predict_ml_score(scoring_features, side)
            ensemble_score = await self._predict_ensemble_score(scoring_features, side)
            
            # Confidence intervals
            score_lower, score_upper = self._calculate_confidence_intervals(
                scoring_features, ensemble_score
            )
            
            # Feature contributions
            feature_contributions = self._calculate_feature_contributions(scoring_features)
            
            # Prediction confidence
            prediction_confidence = self._calculate_prediction_confidence(scoring_features)
            
            return PickScore(
                symbol=symbol,
                side=side,
                base_score=base_score,
                confidence_score=confidence_score,
                risk_score=risk_score,
                ml_score=ml_score,
                ensemble_score=ensemble_score,
                score_lower_bound=score_lower,
                score_upper_bound=score_upper,
                feature_contributions=feature_contributions,
                model_used="ensemble_model",
                prediction_confidence=prediction_confidence,
                timestamp=datetime.now()
            )
            
        except Exception as e:
            self.logger.error(f"❌ Enhanced scoring failed for {symbol}: {e}")
            # Return fallback score
            return PickScore(
                symbol=symbol,
                side=side,
                base_score=0.5,
                confidence_score=0.5,
                risk_score=0.5,
                ml_score=0.5,
                ensemble_score=0.5,
                score_lower_bound=0.3,
                score_upper_bound=0.7,
                feature_contributions={},
                model_used="fallback",
                prediction_confidence=0.3,
                timestamp=datetime.now()
            )
    
    def _calculate_base_score(self, features: Dict[str, float], side: str) -> float:
        """Calculate base score using traditional methods"""
        
        # Momentum component
        momentum_score = 0
        if side == "LONG":
            momentum_score = max(0, features.get('momentum_5', 0) * 0.4 + 
                               features.get('momentum_10', 0) * 0.3 + 
                               features.get('momentum_20', 0) * 0.3)
        else:  # SHORT
            momentum_score = max(0, -features.get('momentum_5', 0) * 0.4 + 
                               -features.get('momentum_10', 0) * 0.3 + 
                               -features.get('momentum_20', 0) * 0.3)
        
        # Volume component
        volume_score = min(1, features.get('rvol_10', 1) / 2)  # Cap at 2x volume
        
        # Technical component
        rsi_score = 0
        if side == "LONG":
            rsi_score = max(0, (features.get('rsi_14', 50) - 30) / 40)  # RSI > 30
        else:  # SHORT
            rsi_score = max(0, (70 - features.get('rsi_14', 50)) / 40)  # RSI < 70
        
        # Microstructure component
        spread_score = max(0, 1 - features.get('spread_bps', 10) / 20)  # Penalty for wide spreads
        
        # Composite base score
        base_score = (
            momentum_score * 0.3 +
            volume_score * 0.25 +
            rsi_score * 0.25 +
            spread_score * 0.2
        )
        
        return max(0, min(1, base_score))
    
    def _calculate_confidence_score(self, features: Dict[str, float]) -> float:
        """Calculate confidence score based on feature quality"""
        
        confidence_factors = []
        
        # Volume confirmation
        if features.get('rvol_10', 1) > 1.5:
            confidence_factors.append(0.2)
        
        # Technical confirmation
        if abs(features.get('macd_signal', 0)) > 0.1:
            confidence_factors.append(0.2)
        
        # Spread quality
        if features.get('spread_bps', 10) < 5:
            confidence_factors.append(0.2)
        
        # Momentum strength
        if abs(features.get('momentum_5', 0)) > 0.01:
            confidence_factors.append(0.2)
        
        # Volatility regime
        if features.get('volatility_regime', 'NORMAL') == 'NORMAL':
            confidence_factors.append(0.2)
        
        confidence_score = sum(confidence_factors)
        return max(0.3, min(0.95, confidence_score))
    
    def _calculate_risk_score(self, features: Dict[str, float]) -> float:
        """Calculate risk score"""
        
        risk_factors = []
        
        # Volatility risk
        volatility = features.get('volatility_5', 0.02)
        if volatility > 0.03:
            risk_factors.append(0.3)
        elif volatility > 0.02:
            risk_factors.append(0.2)
        else:
            risk_factors.append(0.1)
        
        # Spread risk
        spread_bps = features.get('spread_bps', 5)
        if spread_bps > 10:
            risk_factors.append(0.3)
        elif spread_bps > 5:
            risk_factors.append(0.2)
        else:
            risk_factors.append(0.1)
        
        # Volume risk
        volume_stability = features.get('volume_stability', 0.5)
        risk_factors.append(1 - volume_stability)
        
        # Technical risk
        rsi = features.get('rsi_14', 50)
        if rsi > 80 or rsi < 20:
            risk_factors.append(0.3)
        else:
            risk_factors.append(0.1)
        
        risk_score = np.mean(risk_factors)
        return max(0.05, min(0.95, risk_score))
    
    async def _predict_ml_score(self, features: Dict[str, float], side: str) -> float:
        """Predict score using ML models"""
        
        try:
            # Prepare features for ML
            feature_vector = self._prepare_feature_vector(features)
            
            if len(feature_vector) == 0:
                return 0.5
            
            # Get predictions from different models
            predictions = {}
            
            for model_name, config in self.model_configs.items():
                if model_name == "ensemble_model":
                    continue
                
                if model_name in self.models:
                    try:
                        model = self.models[model_name]
                        scaler = self.scalers.get(model_name)
                        
                        # Scale features
                        if scaler:
                            feature_scaled = scaler.transform([feature_vector])
                        else:
                            feature_scaled = [feature_vector]
                        
                        # Get prediction
                        prediction = model.predict(feature_scaled)[0]
                        predictions[model_name] = max(0, min(1, prediction))
                        
                    except Exception as e:
                        self.logger.warning(f"Model {model_name} prediction failed: {e}")
                        predictions[model_name] = 0.5
            
            # Weighted average of predictions
            if predictions:
                weights = {"momentum_model": 0.3, "volume_model": 0.3, "technical_model": 0.4}
                ml_score = sum(predictions.get(name, 0.5) * weights.get(name, 0.33) for name in weights.keys())
                return max(0, min(1, ml_score))
            else:
                return 0.5
                
        except Exception as e:
            self.logger.error(f"ML prediction failed: {e}")
            return 0.5
    
    async def _predict_ensemble_score(self, features: Dict[str, float], side: str) -> float:
        """Predict score using ensemble methods"""
        
        # Get individual model scores
        base_score = self._calculate_base_score(features, side)
        ml_score = await self._predict_ml_score(features, side)
        
        # Ensemble weights (can be learned from historical performance)
        ensemble_weights = {
            "base_score": 0.4,
            "ml_score": 0.6
        }
        
        # Calculate ensemble score
        ensemble_score = (
            base_score * ensemble_weights["base_score"] +
            ml_score * ensemble_weights["ml_score"]
        )
        
        return max(0, min(1, ensemble_score))
    
    def _calculate_confidence_intervals(
        self, 
        features: Dict[str, float], 
        point_estimate: float
    ) -> Tuple[float, float]:
        """Calculate confidence intervals for score prediction"""
        
        # Estimate prediction uncertainty based on feature quality
        uncertainty_factors = []
        
        # Volume uncertainty
        volume_stability = features.get('volume_stability', 0.5)
        uncertainty_factors.append(1 - volume_stability)
        
        # Spread uncertainty
        spread_bps = features.get('spread_bps', 5)
        uncertainty_factors.append(min(1, spread_bps / 20))
        
        # Volatility uncertainty
        volatility = features.get('volatility_5', 0.02)
        uncertainty_factors.append(min(1, volatility / 0.05))
        
        # Average uncertainty
        avg_uncertainty = np.mean(uncertainty_factors)
        
        # Calculate confidence interval width
        interval_width = avg_uncertainty * 0.3  # 30% of uncertainty
        
        lower_bound = max(0, point_estimate - interval_width)
        upper_bound = min(1, point_estimate + interval_width)
        
        return lower_bound, upper_bound
    
    def _calculate_feature_contributions(self, features: Dict[str, float]) -> Dict[str, float]:
        """Calculate contribution of each feature to the final score"""
        
        contributions = {}
        
        # Momentum contribution
        momentum_contrib = abs(features.get('momentum_5', 0)) * 0.3
        contributions['momentum'] = momentum_contrib
        
        # Volume contribution
        volume_contrib = min(1, features.get('rvol_10', 1) / 2) * 0.25
        contributions['volume'] = volume_contrib
        
        # Technical contribution
        rsi_contrib = abs(features.get('rsi_14', 50) - 50) / 50 * 0.25
        contributions['technical'] = rsi_contrib
        
        # Microstructure contribution
        spread_contrib = max(0, 1 - features.get('spread_bps', 10) / 20) * 0.2
        contributions['microstructure'] = spread_contrib
        
        # Normalize contributions
        total_contrib = sum(contributions.values())
        if total_contrib > 0:
            contributions = {k: v / total_contrib for k, v in contributions.items()}
        
        return contributions
    
    def _calculate_prediction_confidence(self, features: Dict[str, float]) -> float:
        """Calculate confidence in the prediction"""
        
        confidence_factors = []
        
        # Feature completeness
        required_features = ['momentum_5', 'rsi_14', 'rvol_10', 'spread_bps']
        completeness = sum(1 for f in required_features if f in features) / len(required_features)
        confidence_factors.append(completeness)
        
        # Feature quality
        if features.get('volume_stability', 0.5) > 0.7:
            confidence_factors.append(0.2)
        
        if features.get('spread_bps', 10) < 5:
            confidence_factors.append(0.2)
        
        # Model performance (if available)
        if 'ensemble_model' in self.model_performance:
            model_r2 = self.model_performance['ensemble_model'].get('r2_score', 0.5)
            confidence_factors.append(model_r2)
        
        prediction_confidence = np.mean(confidence_factors)
        return max(0.3, min(0.95, prediction_confidence))
    
    def _prepare_feature_vector(self, features: Dict[str, float]) -> List[float]:
        """Prepare feature vector for ML models"""
        
        # Define feature order for consistency
        feature_order = [
            'momentum_5', 'momentum_10', 'momentum_20',
            'rsi_14', 'macd_signal', 'bb_position',
            'rvol_10', 'volume_spike', 'vwap_distance',
            'spread_bps', 'volume_stability', 'volatility_5'
        ]
        
        feature_vector = []
        for feature in feature_order:
            value = features.get(feature, 0)
            # Handle NaN values
            if pd.isna(value):
                value = 0
            feature_vector.append(float(value))
        
        return feature_vector
    
    async def train_models(self, training_data: List[Dict[str, Any]]):
        """Train ML models on historical data"""
        
        try:
            self.logger.info("🤖 Training ML models...")
            
            # Prepare training data
            X, y = self._prepare_training_data(training_data)
            
            if len(X) < 100:  # Need minimum data
                self.logger.warning("Insufficient training data")
                return
            
            # Train individual models
            for model_name, config in self.model_configs.items():
                if model_name == "ensemble_model":
                    continue
                
                try:
                    # Get model features
                    model_features = config['features']
                    X_model = X[[f for f in model_features if f in X.columns]]
                    
                    if X_model.empty:
                        continue
                    
                    # Initialize model
                    if config['type'] == 'RandomForestRegressor':
                        model = RandomForestRegressor(**config['params'])
                    elif config['type'] == 'GradientBoostingRegressor':
                        model = GradientBoostingRegressor(**config['params'])
                    elif config['type'] == 'Ridge':
                        model = Ridge(**config['params'])
                    else:
                        continue
                    
                    # Train model
                    model.fit(X_model, y)
                    
                    # Store model and scaler
                    self.models[model_name] = model
                    
                    # Calculate feature importance
                    if hasattr(model, 'feature_importances_'):
                        self.feature_importance[model_name] = dict(
                            zip(X_model.columns, model.feature_importances_)
                        )
                    
                    # Evaluate model
                    y_pred = model.predict(X_model)
                    r2 = r2_score(y, y_pred)
                    mse = mean_squared_error(y, y_pred)
                    
                    self.model_performance[model_name] = {
                        'r2_score': r2,
                        'mse': mse,
                        'last_trained': datetime.now()
                    }
                    
                    self.logger.info(f"✅ Trained {model_name}: R²={r2:.3f}, MSE={mse:.3f}")
                    
                except Exception as e:
                    self.logger.error(f"❌ Failed to train {model_name}: {e}")
            
            # Save models
            self._save_models()
            
        except Exception as e:
            self.logger.error(f"❌ Model training failed: {e}")
    
    def _prepare_training_data(self, training_data: List[Dict[str, Any]]) -> Tuple[pd.DataFrame, pd.Series]:
        """Prepare training data for ML models"""
        
        # Convert to DataFrame
        df = pd.DataFrame(training_data)
        
        # Extract features and target
        feature_columns = [col for col in df.columns if col not in ['symbol', 'side', 'actual_return', 'timestamp']]
        X = df[feature_columns]
        y = df['actual_return']  # Target variable
        
        # Handle missing values
        X = X.fillna(0)
        y = y.fillna(0)
        
        return X, y
    
    def _load_models(self):
        """Load pre-trained models from disk"""
        
        model_dir = "backend/models"
        if not os.path.exists(model_dir):
            os.makedirs(model_dir)
        
        for model_name in self.model_configs.keys():
            if model_name == "ensemble_model":
                continue
            
            model_path = os.path.join(model_dir, f"{model_name}.joblib")
            scaler_path = os.path.join(model_dir, f"{model_name}_scaler.joblib")
            
            try:
                if os.path.exists(model_path):
                    self.models[model_name] = joblib.load(model_path)
                    self.logger.info(f"✅ Loaded model: {model_name}")
                
                if os.path.exists(scaler_path):
                    self.scalers[model_name] = joblib.load(scaler_path)
                    
            except Exception as e:
                self.logger.warning(f"Failed to load {model_name}: {e}")
    
    def _save_models(self):
        """Save trained models to disk"""
        
        model_dir = "backend/models"
        if not os.path.exists(model_dir):
            os.makedirs(model_dir)
        
        for model_name, model in self.models.items():
            try:
                model_path = os.path.join(model_dir, f"{model_name}.joblib")
                joblib.dump(model, model_path)
                
                if model_name in self.scalers:
                    scaler_path = os.path.join(model_dir, f"{model_name}_scaler.joblib")
                    joblib.dump(self.scalers[model_name], scaler_path)
                
                self.logger.info(f"✅ Saved model: {model_name}")
                
            except Exception as e:
                self.logger.error(f"Failed to save {model_name}: {e}")


class FeatureEngineering:
    """Feature engineering for ML models"""
    
    def extract_scoring_features(self, features: AdvancedFeatures) -> Dict[str, float]:
        """Extract features relevant for scoring"""
        
        scoring_features = {}
        
        # Price momentum features
        if features.price_momentum:
            for period, value in features.price_momentum.items():
                scoring_features[f"momentum_{period}"] = value
        
        # Volume features
        if features.volume_profile:
            scoring_features.update(features.volume_profile)
        
        # Technical indicators
        if features.oscillators:
            scoring_features.update(features.oscillators)
        
        if features.trend_indicators:
            scoring_features.update(features.trend_indicators)
        
        if features.volatility_indicators:
            scoring_features.update(features.volatility_indicators)
        
        # Microstructure features
        if features.spread_analysis:
            scoring_features.update(features.spread_analysis)
        
        # ML features
        if features.ml_features:
            scoring_features.update(features.ml_features)
        
        # Market regime features
        if features.market_regime:
            scoring_features.update(features.market_regime)
        
        return scoring_features


# Factory function
async def create_enhanced_scoring_engine(api_key: str) -> EnhancedScoringEngine:
    """Create enhanced scoring engine"""
    from ..market.providers.polygon import PolygonProvider
    provider = PolygonProvider(api_key=api_key)
    return EnhancedScoringEngine(provider)
