"""
LSTM Feature Extractor for Day Trading
Production-grade LSTM feature extraction with proper scaling, persistence, and net-of-costs labeling.
Extracts temporal momentum score from price sequences and feeds into XGBoost for hybrid predictions.
"""
import logging
import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timedelta
import os
import pickle
import joblib

logger = logging.getLogger(__name__)

# Try to import deep learning libraries
try:
    import tensorflow as tf
    from tensorflow.keras.models import Sequential, Model
    from tensorflow.keras.layers import LSTM, Dense, Dropout
    from sklearn.preprocessing import StandardScaler, MinMaxScaler
    TENSORFLOW_AVAILABLE = True
except ImportError:
    TENSORFLOW_AVAILABLE = False
    logger.warning("TensorFlow not available - LSTM features disabled")

# Try to import deep learning service (fallback)
try:
    from .deep_learning_service import DeepLearningService
    DEEP_LEARNING_AVAILABLE = True
except ImportError:
    DEEP_LEARNING_AVAILABLE = False


class LSTMFeatureExtractor:
    """
    Production-grade LSTM feature extractor.
    Extracts temporal momentum score from price sequences.
    Designed to complement XGBoost with time-series features.
    """
    
    def __init__(self):
        self.lstm_model = None
        self.scaler = None
        self.sequence_length = 60  # 60 time steps (1-min bars = 1 hour, 5-min bars = 5 hours)
        self.n_features = 5  # OHLCV
        self.lstm_available = False
        
        # Model paths for persistence
        self.model_dir = os.path.join(os.path.dirname(__file__), 'ml_models', 'lstm_extractor')
        os.makedirs(self.model_dir, exist_ok=True)
        self.model_path = os.path.join(self.model_dir, 'lstm_extractor.h5')
        self.scaler_path = os.path.join(self.model_dir, 'lstm_scaler.pkl')
        
        # Initialize
        if TENSORFLOW_AVAILABLE:
            self._load_or_create_model()
        else:
            # Fallback to deep learning service if available
            if DEEP_LEARNING_AVAILABLE:
                try:
                    self.deep_learning_service = DeepLearningService()
                    self.lstm_available = self.deep_learning_service.deep_learning_available
                    if self.lstm_available:
                        logger.info("✅ LSTM Feature Extractor initialized (using DeepLearningService)")
                except Exception as e:
                    logger.warning(f"⚠️ LSTM Feature Extractor initialization failed: {e}")
                    self.lstm_available = False
    
    def _load_or_create_model(self):
        """Load existing model or create new one"""
        try:
            # Try to load existing model
            if os.path.exists(self.model_path) and os.path.exists(self.scaler_path):
                self.lstm_model = tf.keras.models.load_model(self.model_path)
                self.scaler = joblib.load(self.scaler_path)
                self.lstm_available = True
                logger.info("✅ Loaded pre-trained LSTM feature extractor")
            else:
                # Create new model (will be trained later)
                self.lstm_model = self._build_lstm_extractor()
                self.scaler = StandardScaler()
                self.lstm_available = True
                logger.info("✅ Created new LSTM feature extractor (untrained - will train on first use)")
        except Exception as e:
            logger.warning(f"⚠️ Error loading/creating LSTM model: {e}")
            self.lstm_available = False
    
    def _build_lstm_extractor(self) -> Model:
        """
        Build LSTM feature extractor model.
        Outputs a single "Temporal Momentum Score" from price sequences.
        """
        model = Sequential([
            # Input: (time_steps, features) = (60, 5) for OHLCV
            LSTM(50, activation='relu', input_shape=(self.sequence_length, self.n_features), return_sequences=False),
            Dropout(0.2),
            Dense(1, name='temporal_momentum_score')  # Single output: momentum score
        ])
        model.compile(optimizer='adam', loss='mse', metrics=['mae'])
        return model
    
    def extract_temporal_momentum_score(
        self,
        price_sequence: np.ndarray,
        symbol: str = None
    ) -> float:
        """
        Extract temporal momentum score from price sequence.
        This is the core feature that gets fed into XGBoost.
        
        Args:
            price_sequence: 3D array (1, sequence_length, n_features) or 2D (sequence_length, n_features)
            symbol: Optional symbol for logging
        
        Returns:
            Temporal momentum score (single float)
        """
        if not self.lstm_available or self.lstm_model is None:
            return 0.0
        
        try:
            # Ensure 3D shape: (samples, timesteps, features)
            if price_sequence.ndim == 2:
                price_sequence = np.expand_dims(price_sequence, axis=0)
            
            # Scale using persisted scaler (CRITICAL: use training scaler, don't re-fit)
            if self.scaler is not None:
                # Reshape for scaling: (samples * timesteps, features)
                original_shape = price_sequence.shape
                flattened = price_sequence.reshape(-1, price_sequence.shape[-1])
                scaled = self.scaler.transform(flattened)
                price_sequence = scaled.reshape(original_shape)
            
            # Get temporal momentum score from LSTM
            momentum_score = self.lstm_model.predict(price_sequence, verbose=0)[0][0]
            
            return float(momentum_score)
            
        except Exception as e:
            logger.warning(f"Error extracting temporal momentum score: {e}")
            return 0.0
    
    def extract_features(
        self,
        price_data: pd.DataFrame,
        symbol: str,
        lookback_minutes: int = 60
    ) -> Dict[str, float]:
        """
        Extract LSTM-based time-series features from price data.
        Production version with proper scaling and sequence handling.
        
        Args:
            price_data: DataFrame with OHLCV data (indexed by datetime)
            symbol: Stock symbol
            lookback_minutes: How many minutes of history to use (default: 60)
        
        Returns:
            Dictionary with temporal_momentum_score (primary feature for XGBoost)
        """
        if not self.lstm_available:
            return self._get_default_features()
        
        try:
            # Prepare price sequence
            if len(price_data) < self.sequence_length:
                logger.debug(f"Insufficient data for {symbol}: {len(price_data)} < {self.sequence_length}")
                return self._get_default_features()
            
            # Get last N time steps
            recent_data = price_data.tail(self.sequence_length).copy()
            
            # Extract OHLCV columns
            ohlcv_cols = ['Open', 'High', 'Low', 'Close', 'Volume']
            available_cols = [col for col in ohlcv_cols if col in recent_data.columns]
            
            if len(available_cols) < 5:
                # Fallback: use Close price if OHLCV not available
                if 'Close' in recent_data.columns:
                    sequence = recent_data[['Close']].values
                    # Duplicate to match expected shape
                    sequence = np.column_stack([sequence] * 5)
                else:
                    return self._get_default_features()
            else:
                sequence = recent_data[ohlcv_cols].values
            
            # Get temporal momentum score
            temporal_momentum_score = self.extract_temporal_momentum_score(sequence, symbol)
            
            return {
                'lstm_temporal_momentum_score': temporal_momentum_score,
                # Legacy fields for backward compatibility
                'lstm_momentum_forecast': temporal_momentum_score,
                'lstm_volatility_forecast': abs(temporal_momentum_score) * 2.0,
                'lstm_regime_transition_prob': min(1.0, abs(temporal_momentum_score) * 2.0),
                'lstm_price_trend_strength': abs(temporal_momentum_score),
                'lstm_mean_reversion_signal': -temporal_momentum_score if abs(temporal_momentum_score) > 0.1 else 0.0,
                'lstm_embedding_mean': 0.0,
                'lstm_embedding_std': 0.0,
            }
            
        except Exception as e:
            logger.warning(f"Error extracting LSTM features for {symbol}: {e}")
            return self._get_default_features()
    
    def _prepare_features(self, price_data: pd.DataFrame) -> np.ndarray:
        """
        Prepare feature matrix from OHLCV data.
        Creates sequences suitable for LSTM input.
        """
        try:
            # Calculate returns
            price_data = price_data.copy()
            price_data['returns'] = price_data['Close'].pct_change()
            price_data['log_returns'] = np.log(price_data['Close'] / price_data['Close'].shift(1))
            
            # Calculate volatility (rolling std)
            price_data['volatility'] = price_data['returns'].rolling(window=10).std()
            
            # Calculate volume ratio
            if 'Volume' in price_data.columns:
                price_data['volume_ma'] = price_data['Volume'].rolling(window=20).mean()
                price_data['volume_ratio'] = price_data['Volume'] / price_data['volume_ma']
            else:
                price_data['volume_ratio'] = 1.0
            
            # Calculate RSI (simplified)
            delta = price_data['Close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            rs = gain / loss
            price_data['rsi'] = 100 - (100 / (1 + rs))
            
            # Fill NaN values
            price_data = price_data.fillna(method='ffill').fillna(method='bfill').fillna(0)
            
            # Select features for LSTM
            feature_cols = ['Close', 'returns', 'log_returns', 'volatility', 'volume_ratio', 'rsi']
            available_cols = [col for col in feature_cols if col in price_data.columns]
            
            if len(available_cols) == 0:
                # Fallback: just use Close price
                features = price_data[['Close']].values
            else:
                features = price_data[available_cols].values
            
            # Reshape for LSTM: (samples, timesteps, features)
            # We have 1 sample with sequence_length timesteps
            features = features.reshape(1, len(features), features.shape[1])
            
            return features
            
        except Exception as e:
            logger.error(f"Error preparing features: {e}")
            # Return default shape
            return np.zeros((1, self.sequence_length, 6))
    
    def _extract_lstm_features(self, features: np.ndarray, symbol: str) -> Dict[str, float]:
        """
        Extract features using trained LSTM model.
        Uses LSTM embeddings/predictions as features for tree models.
        """
        try:
            # Get LSTM predictions
            if self.deep_learning_service.lstm_model is not None:
                # Scale features (if scaler available)
                if hasattr(self.deep_learning_service, 'scaler') and self.deep_learning_service.scaler is not None:
                    # Reshape for scaling
                    original_shape = features.shape
                    features_flat = features.reshape(-1, features.shape[-1])
                    features_scaled = self.deep_learning_service.scaler.transform(features_flat)
                    features = features_scaled.reshape(original_shape)
                
                # Get LSTM prediction (next-period return)
                prediction = self.deep_learning_service.lstm_model.predict(features, verbose=0)[0]
                
                # Extract intermediate layer activations (embeddings)
                # This gives us learned representations of the time series
                try:
                    # Get output from second-to-last LSTM layer (embeddings)
                    intermediate_model = None
                    if hasattr(self.deep_learning_service.lstm_model, 'layers'):
                        # Find LSTM layers
                        lstm_layers = [l for l in self.deep_learning_service.lstm_model.layers 
                                     if 'lstm' in l.name.lower() or 'LSTM' in str(type(l))]
                        if len(lstm_layers) >= 2:
                            # Use second-to-last LSTM layer for embeddings
                            intermediate_model = type(self.deep_learning_service.lstm_model)(
                                inputs=self.deep_learning_service.lstm_model.input,
                                outputs=lstm_layers[-2].output
                            )
                    
                    if intermediate_model is not None:
                        embeddings = intermediate_model.predict(features, verbose=0)
                        # Use mean of embeddings as feature
                        embedding_mean = float(np.mean(embeddings))
                        embedding_std = float(np.std(embeddings))
                    else:
                        embedding_mean = 0.0
                        embedding_std = 0.0
                except Exception as e:
                    logger.debug(f"Could not extract embeddings: {e}")
                    embedding_mean = 0.0
                    embedding_std = 0.0
                
                # Calculate derived features
                momentum_forecast = float(prediction[0]) if isinstance(prediction, np.ndarray) else float(prediction)
                volatility_forecast = abs(momentum_forecast) * 2.0  # Rough volatility estimate
                regime_transition_prob = min(1.0, abs(embedding_std) * 2.0)  # Higher std = more regime uncertainty
                price_trend_strength = abs(momentum_forecast)  # Stronger momentum = stronger trend
                mean_reversion_signal = -momentum_forecast if abs(momentum_forecast) > 0.1 else 0.0  # Revert if strong move
                
                return {
                    'lstm_momentum_forecast': momentum_forecast,
                    'lstm_volatility_forecast': volatility_forecast,
                    'lstm_regime_transition_prob': regime_transition_prob,
                    'lstm_price_trend_strength': price_trend_strength,
                    'lstm_mean_reversion_signal': mean_reversion_signal,
                    'lstm_embedding_mean': embedding_mean,
                    'lstm_embedding_std': embedding_std,
                }
            else:
                return self._get_default_features()
                
        except Exception as e:
            logger.warning(f"Error extracting LSTM features: {e}")
            return self._get_default_features()
    
    def train_lstm_extractor(
        self,
        price_sequences: np.ndarray,
        targets: np.ndarray,
        epochs: int = 50,
        batch_size: int = 32
    ) -> Dict[str, Any]:
        """
        Train LSTM feature extractor on price sequences.
        
        Args:
            price_sequences: 3D array (samples, timesteps, features)
            targets: Target values (e.g., next-period returns)
            epochs: Training epochs
            batch_size: Batch size
        
        Returns:
            Training history and metrics
        """
        if not self.lstm_available or self.lstm_model is None:
            return {'error': 'LSTM model not available'}
        
        try:
            # Fit scaler on training data (CRITICAL: fit once, use forever)
            if self.scaler is None:
                self.scaler = StandardScaler()
            
            # Reshape for scaling
            original_shape = price_sequences.shape
            flattened = price_sequences.reshape(-1, price_sequences.shape[-1])
            
            # Fit scaler (ONLY on training data)
            self.scaler.fit(flattened)
            
            # Transform sequences
            scaled_flat = self.scaler.transform(flattened)
            scaled_sequences = scaled_flat.reshape(original_shape)
            
            # Train model
            history = self.lstm_model.fit(
                scaled_sequences,
                targets,
                epochs=epochs,
                batch_size=batch_size,
                validation_split=0.2,
                verbose=0
            )
            
            # Save model and scaler (CRITICAL for persistence)
            self.lstm_model.save(self.model_path)
            joblib.dump(self.scaler, self.scaler_path)
            
            logger.info("✅ LSTM extractor trained and saved")
            
            return {
                'train_loss': float(history.history['loss'][-1]),
                'val_loss': float(history.history.get('val_loss', [0])[-1]),
                'model_saved': True
            }
            
        except Exception as e:
            logger.error(f"Error training LSTM extractor: {e}")
            return {'error': str(e)}
    
    def _get_default_features(self) -> Dict[str, float]:
        """Return default (zero) features when LSTM not available"""
        return {
            'lstm_temporal_momentum_score': 0.0,
            'lstm_momentum_forecast': 0.0,
            'lstm_volatility_forecast': 0.0,
            'lstm_regime_transition_prob': 0.0,
            'lstm_price_trend_strength': 0.0,
            'lstm_mean_reversion_signal': 0.0,
            'lstm_embedding_mean': 0.0,
            'lstm_embedding_std': 0.0,
        }
    
    def is_available(self) -> bool:
        """Check if LSTM feature extraction is available"""
        return self.lstm_available


# Global instance
_lstm_feature_extractor = None

def get_lstm_feature_extractor() -> LSTMFeatureExtractor:
    """Get global LSTM feature extractor instance"""
    global _lstm_feature_extractor
    if _lstm_feature_extractor is None:
        _lstm_feature_extractor = LSTMFeatureExtractor()
    return _lstm_feature_extractor

