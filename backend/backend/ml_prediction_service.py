#!/usr/bin/env python3
"""
ML Prediction Service for Streaming Pipeline
"""

import asyncio
import json
import logging
import pickle
import numpy as np
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
from dataclasses import dataclass

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class MLPrediction:
    """ML prediction result"""
    symbol: str
    timestamp: str
    model_version: str
    prediction: float
    confidence: float
    features: Dict[str, float]
    source: str = "ml_model"

class MLPredictionService:
    """ML prediction service for streaming pipeline"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.models = {}
        self.scaler = None
        self.feature_history = {}
        self._load_models()
    
    def _load_models(self):
        """Load ML models"""
        try:
            # Load feature scaler
            with open('models/feature_scaler.pkl', 'rb') as f:
                self.scaler = pickle.load(f)
            
            # Load models
            model_files = {
                'price_prediction': 'models/price_prediction_model.pkl',
                'trend_classification': 'models/trend_classification_model.pkl',
                'volatility_prediction': 'models/volatility_prediction_model.pkl'
            }
            
            for model_name, model_file in model_files.items():
                try:
                    with open(model_file, 'rb') as f:
                        self.models[model_name] = pickle.load(f)
                    logger.info(f"✅ Loaded {model_name} model")
                except FileNotFoundError:
                    logger.warning(f"⚠️ Model file not found: {model_file}")
                except Exception as e:
                    logger.error(f"❌ Failed to load {model_name} model: {e}")
            
        except Exception as e:
            logger.error(f"❌ Failed to load models: {e}")
    
    def _extract_features(self, market_data: Dict[str, Any], technical_indicators: Dict[str, Any]) -> np.ndarray:
        """Extract features for ML models"""
        try:
            features = []
            
            # Technical indicators
            indicators = technical_indicators.get('indicators', {})
            feature_names = self.config['feature_engineering']['real_time_features']
            
            for feature_name in feature_names:
                if feature_name in indicators:
                    features.append(indicators[feature_name])
                else:
                    features.append(0.0)  # Default value
            
            # Derived features
            derived_features = self.config['feature_engineering']['derived_features']
            for feature_name in derived_features:
                # Calculate derived features (simplified)
                if 'price_change' in feature_name:
                    features.append(np.random.normal(0, 0.01))  # Placeholder
                elif 'volume_change' in feature_name:
                    features.append(np.random.normal(0, 0.1))  # Placeholder
                elif 'volatility' in feature_name:
                    features.append(np.random.exponential(0.1))  # Placeholder
                else:
                    features.append(0.0)  # Default value
            
            return np.array(features).reshape(1, -1)
            
        except Exception as e:
            logger.error(f"❌ Failed to extract features: {e}")
            return np.zeros((1, 14))  # Return zeros if extraction fails
    
    async def predict_price_movement(self, market_data: Dict[str, Any], technical_indicators: Dict[str, Any]) -> Optional[MLPrediction]:
        """Predict price movement"""
        try:
            if 'price_prediction' not in self.models:
                return None
            
            # Extract features
            features = self._extract_features(market_data, technical_indicators)
            
            # Scale features
            if self.scaler:
                features = self.scaler.transform(features)
            
            # Make prediction
            prediction = self.models['price_prediction'].predict(features)[0]
            confidence = min(abs(prediction) * 10, 1.0)  # Simple confidence calculation
            
            return MLPrediction(
                symbol=market_data['symbol'],
                timestamp=datetime.now(timezone.utc).isoformat(),
                model_version='v1.0',
                prediction=prediction,
                confidence=confidence,
                features={f'feature_{i}': float(features[0][i]) for i in range(len(features[0]))},
                source='ml_model'
            )
            
        except Exception as e:
            logger.error(f"❌ Price prediction failed: {e}")
            return None
    
    async def predict_trend(self, market_data: Dict[str, Any], technical_indicators: Dict[str, Any]) -> Optional[MLPrediction]:
        """Predict trend direction"""
        try:
            if 'trend_classification' not in self.models:
                return None
            
            # Extract features
            features = self._extract_features(market_data, technical_indicators)
            
            # Scale features
            if self.scaler:
                features = self.scaler.transform(features)
            
            # Make prediction
            prediction_proba = self.models['trend_classification'].predict_proba(features)[0]
            prediction_class = np.argmax(prediction_proba)
            confidence = prediction_proba[prediction_class]
            
            # Convert class to trend direction
            trend_map = {0: -1, 1: 0, 2: 1}  # bearish, neutral, bullish
            prediction_value = trend_map[prediction_class]
            
            return MLPrediction(
                symbol=market_data['symbol'],
                timestamp=datetime.now(timezone.utc).isoformat(),
                model_version='v1.0',
                prediction=prediction_value,
                confidence=confidence,
                features={f'feature_{i}': float(features[0][i]) for i in range(len(features[0]))},
                source='ml_model'
            )
            
        except Exception as e:
            logger.error(f"❌ Trend prediction failed: {e}")
            return None
    
    async def predict_volatility(self, market_data: Dict[str, Any], technical_indicators: Dict[str, Any]) -> Optional[MLPrediction]:
        """Predict volatility"""
        try:
            if 'volatility_prediction' not in self.models:
                return None
            
            # Extract features
            features = self._extract_features(market_data, technical_indicators)
            
            # Scale features
            if self.scaler:
                features = self.scaler.transform(features)
            
            # Make prediction
            prediction = self.models['volatility_prediction'].predict(features)[0]
            confidence = min(prediction * 5, 1.0)  # Simple confidence calculation
            
            return MLPrediction(
                symbol=market_data['symbol'],
                timestamp=datetime.now(timezone.utc).isoformat(),
                model_version='v1.0',
                prediction=prediction,
                confidence=confidence,
                features={f'feature_{i}': float(features[0][i]) for i in range(len(features[0]))},
                source='ml_model'
            )
            
        except Exception as e:
            logger.error(f"❌ Volatility prediction failed: {e}")
            return None
    
    async def process_market_data(self, market_data: Dict[str, Any], technical_indicators: Dict[str, Any]) -> List[MLPrediction]:
        """Process market data and generate ML predictions"""
        predictions = []
        
        # Generate all predictions
        price_pred = await self.predict_price_movement(market_data, technical_indicators)
        if price_pred:
            predictions.append(price_pred)
        
        trend_pred = await self.predict_trend(market_data, technical_indicators)
        if trend_pred:
            predictions.append(trend_pred)
        
        vol_pred = await self.predict_volatility(market_data, technical_indicators)
        if vol_pred:
            predictions.append(vol_pred)
        
        return predictions

# Global ML prediction service instance
ml_service = None

def get_ml_service() -> Optional[MLPredictionService]:
    """Get the global ML prediction service instance"""
    return ml_service

def initialize_ml_service(config: Dict[str, Any]) -> MLPredictionService:
    """Initialize the ML prediction service"""
    global ml_service
    ml_service = MLPredictionService(config)
    return ml_service

if __name__ == "__main__":
    # Test the ML service
    config = {
        'feature_engineering': {
            'real_time_features': ['sma_20', 'sma_50', 'ema_12', 'ema_26', 'rsi', 'macd'],
            'derived_features': ['price_change_1m', 'volume_change_1m', 'volatility_1h']
        }
    }
    
    service = initialize_ml_service(config)
    print("✅ ML Prediction Service initialized")
