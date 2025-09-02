"""
Deep Learning Service for Advanced ML Techniques
Includes LSTM for time series, ensemble methods, and online learning
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Any, Optional, Tuple
import logging
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

# Deep Learning imports
try:
    import tensorflow as tf
    from tensorflow import keras
    from tensorflow.keras.models import Sequential, Model
    from tensorflow.keras.layers import LSTM, Dense, Dropout, Bidirectional, Conv1D, MaxPooling1D, Flatten
    from tensorflow.keras.optimizers import Adam
    from tensorflow.keras.callbacks import EarlyStopping, ReduceLROnPlateau
    from sklearn.ensemble import VotingRegressor, StackingRegressor, BaggingRegressor
    from sklearn.model_selection import TimeSeriesSplit
    from sklearn.metrics import mean_squared_error, mean_absolute_error
    DEEP_LEARNING_AVAILABLE = True
except ImportError as e:
    logging.warning(f"Deep learning libraries not available: {e}")
    DEEP_LEARNING_AVAILABLE = False

logger = logging.getLogger(__name__)

class DeepLearningService:
    """
    Service for deep learning models and advanced ML techniques
    """
    
    def __init__(self):
        self.deep_learning_available = DEEP_LEARNING_AVAILABLE
        if not self.deep_learning_available:
            logger.warning("Deep Learning Service initialized in fallback mode")
        
        # Initialize models
        self.lstm_models = {}
        self.ensemble_models = {}
        self.online_models = {}
        
        # Model configurations
        self.model_configs = {
            'lstm': {
                'sequence_length': 60,
                'features': 20,
                'lstm_units': [128, 64],
                'dropout_rate': 0.2,
                'learning_rate': 0.001,
                'epochs': 100,
                'batch_size': 32
            },
            'ensemble': {
                'n_estimators': 10,
                'max_depth': 15,
                'learning_rate': 0.1,
                'random_state': 42
            },
            'online': {
                'learning_rate': 0.01,
                'regularization': 0.001,
                'update_frequency': 100
            }
        }
        
        # Performance tracking
        self.model_performance = {}
        self.training_history = {}
    
    def is_available(self) -> bool:
        """Check if deep learning capabilities are available"""
        return self.deep_learning_available
    
    def create_lstm_model(self, model_name: str, config: Optional[Dict] = None) -> bool:
        """
        Create and train an LSTM model for time series forecasting
        
        Args:
            model_name: Name for the model
            config: Optional configuration overrides
            
        Returns:
            True if model created successfully
        """
        if not self.deep_learning_available:
            logger.warning("Deep learning not available for LSTM model creation")
            return False
        
        try:
            # Use default config or override
            model_config = self.model_configs['lstm'].copy()
            if config:
                model_config.update(config)
            
            # Create LSTM model architecture
            model = Sequential()
            
            # First LSTM layer
            model.add(LSTM(
                units=model_config['lstm_units'][0],
                return_sequences=True,
                input_shape=(model_config['sequence_length'], model_config['features'])
            ))
            model.add(Dropout(model_config['dropout_rate']))
            
            # Additional LSTM layers
            for units in model_config['lstm_units'][1:]:
                model.add(LSTM(units=units, return_sequences=True))
                model.add(Dropout(model_config['dropout_rate']))
            
            # Final LSTM layer
            model.add(LSTM(units=32))
            model.add(Dropout(model_config['dropout_rate']))
            
            # Output layer
            model.add(Dense(1, activation='linear'))
            
            # Compile model
            model.compile(
                optimizer=Adam(learning_rate=model_config['learning_rate']),
                loss='mse',
                metrics=['mae']
            )
            
            # Store model
            self.lstm_models[model_name] = {
                'model': model,
                'config': model_config,
                'trained': False,
                'created_at': datetime.now()
            }
            
            logger.info(f"LSTM model '{model_name}' created successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error creating LSTM model: {e}")
            return False
    
    def train_lstm_model(self, model_name: str, training_data: np.ndarray, 
                        target_data: np.ndarray, validation_split: float = 0.2) -> bool:
        """
        Train an LSTM model with time series data
        
        Args:
            model_name: Name of the model to train
            training_data: 3D array (samples, sequence_length, features)
            target_data: 1D array of target values
            validation_split: Fraction of data to use for validation
            
        Returns:
            True if training successful
        """
        if not self.deep_learning_available:
            return False
        
        if model_name not in self.lstm_models:
            logger.error(f"LSTM model '{model_name}' not found")
            return False
        
        try:
            model_info = self.lstm_models[model_name]
            model = model_info['model']
            config = model_info['config']
            
            # Prepare callbacks
            callbacks = [
                EarlyStopping(monitor='val_loss', patience=10, restore_best_weights=True),
                ReduceLROnPlateau(monitor='val_loss', factor=0.5, patience=5, min_lr=1e-7)
            ]
            
            # Train model
            history = model.fit(
                training_data,
                target_data,
                epochs=config['epochs'],
                batch_size=config['batch_size'],
                validation_split=validation_split,
                callbacks=callbacks,
                verbose=1
            )
            
            # Update model info
            model_info['trained'] = True
            model_info['trained_at'] = datetime.now()
            model_info['training_history'] = history.history
            
            # Store performance metrics
            val_loss = min(history.history['val_loss'])
            val_mae = min(history.history['val_mae'])
            
            self.model_performance[model_name] = {
                'val_loss': val_loss,
                'val_mae': val_mae,
                'training_samples': len(training_data),
                'trained_at': datetime.now()
            }
            
            logger.info(f"LSTM model '{model_name}' trained successfully. Val Loss: {val_loss:.4f}, Val MAE: {val_mae:.4f}")
            return True
            
        except Exception as e:
            logger.error(f"Error training LSTM model '{model_name}': {e}")
            return False
    
    def predict_with_lstm(self, model_name: str, input_data: np.ndarray) -> Optional[np.ndarray]:
        """
        Make predictions using a trained LSTM model
        
        Args:
            model_name: Name of the model to use
            input_data: 3D array (samples, sequence_length, features)
            
        Returns:
            Predictions array or None if error
        """
        if not self.deep_learning_available:
            return None
        
        if model_name not in self.lstm_models:
            logger.error(f"LSTM model '{model_name}' not found")
            return None
        
        model_info = self.lstm_models[model_name]
        if not model_info['trained']:
            logger.error(f"LSTM model '{model_name}' not trained yet")
            return None
        
        try:
            model = model_info['model']
            predictions = model.predict(input_data)
            return predictions.flatten()
            
        except Exception as e:
            logger.error(f"Error making LSTM predictions: {e}")
            return None
    
    def create_ensemble_model(self, model_name: str, base_models: List, 
                             ensemble_type: str = 'voting') -> bool:
        """
        Create an ensemble model for better predictions
        
        Args:
            model_name: Name for the ensemble model
            base_models: List of base model names
            ensemble_type: Type of ensemble ('voting', 'stacking', 'bagging')
            
        Returns:
            True if ensemble created successfully
        """
        try:
            if ensemble_type == 'voting':
                ensemble = VotingRegressor(
                    estimators=[(name, self._get_model(name)) for name in base_models],
                    n_jobs=-1
                )
            elif ensemble_type == 'stacking':
                ensemble = StackingRegressor(
                    estimators=[(name, self._get_model(name)) for name in base_models],
                    final_estimator=self._get_model('default'),
                    n_jobs=-1
                )
            elif ensemble_type == 'bagging':
                base_model = self._get_model(base_models[0])
                ensemble = BaggingRegressor(
                    base_estimator=base_model,
                    n_estimators=self.model_configs['ensemble']['n_estimators'],
                    random_state=self.model_configs['ensemble']['random_state']
                )
            else:
                logger.error(f"Unknown ensemble type: {ensemble_type}")
                return False
            
            self.ensemble_models[model_name] = {
                'model': ensemble,
                'type': ensemble_type,
                'base_models': base_models,
                'created_at': datetime.now()
            }
            
            logger.info(f"Ensemble model '{model_name}' created successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error creating ensemble model: {e}")
            return False
    
    def train_ensemble_model(self, model_name: str, X: np.ndarray, y: np.ndarray) -> bool:
        """
        Train an ensemble model
        
        Args:
            model_name: Name of the ensemble model
            X: Training features
            y: Training targets
            
        Returns:
            True if training successful
        """
        if model_name not in self.ensemble_models:
            logger.error(f"Ensemble model '{model_name}' not found")
            return False
        
        try:
            ensemble_info = self.ensemble_models[model_name]
            ensemble = ensemble_info['model']
            
            # Train ensemble
            ensemble.fit(X, y)
            
            # Update info
            ensemble_info['trained'] = True
            ensemble_info['trained_at'] = datetime.now()
            
            logger.info(f"Ensemble model '{model_name}' trained successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error training ensemble model: {e}")
            return False
    
    def predict_with_ensemble(self, model_name: str, X: np.ndarray) -> Optional[np.ndarray]:
        """
        Make predictions using an ensemble model
        
        Args:
            model_name: Name of the ensemble model
            X: Input features
            
        Returns:
            Predictions array or None if error
        """
        if model_name not in self.ensemble_models:
            logger.error(f"Ensemble model '{model_name}' not found")
            return None
        
        ensemble_info = self.ensemble_models[model_name]
        if not ensemble_info.get('trained', False):
            logger.error(f"Ensemble model '{model_name}' not trained yet")
            return None
        
        try:
            ensemble = ensemble_info['model']
            predictions = ensemble.predict(X)
            return predictions
            
        except Exception as e:
            logger.error(f"Error making ensemble predictions: {e}")
            return None
    
    def create_online_model(self, model_name: str, model_type: str = 'sgd') -> bool:
        """
        Create an online learning model for continuous updates
        
        Args:
            model_name: Name for the online model
            model_type: Type of online model ('sgd', 'perceptron', 'passive_aggressive')
            
        Returns:
            True if model created successfully
        """
        try:
            from sklearn.linear_model import SGDRegressor, PassiveAggressiveRegressor
            from sklearn.neural_network import MLPRegressor
            
            if model_type == 'sgd':
                model = SGDRegressor(
                    learning_rate='constant',
                    eta0=self.model_configs['online']['learning_rate'],
                    alpha=self.model_configs['online']['regularization'],
                    random_state=42
                )
            elif model_type == 'passive_aggressive':
                model = PassiveAggressiveRegressor(
                    C=1.0 / self.model_configs['online']['regularization'],
                    random_state=42
                )
            elif model_type == 'mlp':
                model = MLPRegressor(
                    hidden_layer_sizes=(100, 50),
                    learning_rate_init=self.model_configs['online']['learning_rate'],
                    alpha=self.model_configs['online']['regularization'],
                    max_iter=1,  # Online learning
                    random_state=42
                )
            else:
                logger.error(f"Unknown online model type: {model_type}")
                return False
            
            self.online_models[model_name] = {
                'model': model,
                'type': model_type,
                'update_count': 0,
                'last_update': datetime.now(),
                'created_at': datetime.now()
            }
            
            logger.info(f"Online model '{model_name}' created successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error creating online model: {e}")
            return False
    
    def update_online_model(self, model_name: str, X: np.ndarray, y: np.ndarray) -> bool:
        """
        Update an online learning model with new data
        
        Args:
            model_name: Name of the online model
            X: New features
            y: New targets
            
        Returns:
            True if update successful
        """
        if model_name not in self.online_models:
            logger.error(f"Online model '{model_name}' not found")
            return False
        
        try:
            online_info = self.online_models[model_name]
            model = online_info['model']
            
            # Update model
            if online_info['type'] == 'mlp':
                # For MLP, we need to fit with all data
                model.fit(X, y)
            else:
                # For SGD and Passive Aggressive, partial_fit works
                model.partial_fit(X, y)
            
            # Update info
            online_info['update_count'] += 1
            online_info['last_update'] = datetime.now()
            
            logger.info(f"Online model '{model_name}' updated successfully (update #{online_info['update_count']})")
            return True
            
        except Exception as e:
            logger.error(f"Error updating online model: {e}")
            return False
    
    def predict_with_online_model(self, model_name: str, X: np.ndarray) -> Optional[np.ndarray]:
        """
        Make predictions using an online model
        
        Args:
            model_name: Name of the online model
            X: Input features
            
        Returns:
            Predictions array or None if error
        """
        if model_name not in self.online_models:
            logger.error(f"Online model '{model_name}' not found")
            return None
        
        try:
            online_info = self.online_models[model_name]
            model = online_info['model']
            
            predictions = model.predict(X)
            return predictions
            
        except Exception as e:
            logger.error(f"Error making online model predictions: {e}")
            return None
    
    def get_model_performance(self, model_name: str) -> Optional[Dict[str, Any]]:
        """Get performance metrics for a model"""
        return self.model_performance.get(model_name)
    
    def get_all_models(self) -> Dict[str, Any]:
        """Get information about all models"""
        return {
            'lstm_models': list(self.lstm_models.keys()),
            'ensemble_models': list(self.ensemble_models.keys()),
            'online_models': list(self.online_models.keys()),
            'total_models': len(self.lstm_models) + len(self.ensemble_models) + len(self.online_models)
        }
    
    def _get_model(self, model_name: str):
        """Helper to get a model by name"""
        if model_name in self.lstm_models:
            return self.lstm_models[model_name]['model']
        elif model_name in self.ensemble_models:
            return self.ensemble_models[model_name]['model']
        elif model_name in self.online_models:
            return self.online_models[model_name]['model']
        else:
            # Return a default model
            from sklearn.ensemble import RandomForestRegressor
            return RandomForestRegressor(n_estimators=100, random_state=42)
    
    def prepare_time_series_data(self, data: np.ndarray, sequence_length: int) -> Tuple[np.ndarray, np.ndarray]:
        """
        Prepare time series data for LSTM models
        
        Args:
            data: 2D array (samples, features)
            sequence_length: Number of time steps to look back
            
        Returns:
            Tuple of (X, y) for LSTM training
        """
        try:
            X, y = [], []
            
            for i in range(sequence_length, len(data)):
                X.append(data[i-sequence_length:i])
                y.append(data[i, 0])  # Assume first column is target
            
            return np.array(X), np.array(y)
            
        except Exception as e:
            logger.error(f"Error preparing time series data: {e}")
            return np.array([]), np.array([])
    
    def evaluate_model(self, model_name: str, X_test: np.ndarray, y_test: np.ndarray) -> Optional[Dict[str, float]]:
        """
        Evaluate a model's performance
        
        Args:
            model_name: Name of the model to evaluate
            X_test: Test features
            y_test: Test targets
            
        Returns:
            Dictionary of performance metrics
        """
        try:
            if model_name in self.lstm_models:
                predictions = self.predict_with_lstm(model_name, X_test)
            elif model_name in self.ensemble_models:
                predictions = self.predict_with_ensemble(model_name, X_test)
            elif model_name in self.online_models:
                predictions = self.predict_with_online_model(model_name, X_test)
            else:
                logger.error(f"Model '{model_name}' not found")
                return None
            
            if predictions is None:
                return None
            
            # Calculate metrics
            mse = mean_squared_error(y_test, predictions)
            mae = mean_absolute_error(y_test, predictions)
            rmse = np.sqrt(mse)
            
            metrics = {
                'mse': mse,
                'mae': mae,
                'rmse': rmse,
                'evaluated_at': datetime.now()
            }
            
            # Update performance tracking
            if model_name in self.model_performance:
                self.model_performance[model_name].update(metrics)
            
            return metrics
            
        except Exception as e:
            logger.error(f"Error evaluating model '{model_name}': {e}")
            return None
