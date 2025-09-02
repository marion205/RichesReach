"""
Advanced ML Algorithms Service with Deep Learning, Ensemble Methods, and Online Learning
Sophisticated machine learning techniques for financial predictions and portfolio optimization
"""

import os
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple, Union
import logging
import pickle
import joblib
from dataclasses import dataclass

# Try to import advanced ML libraries
try:
    import tensorflow as tf
    from tensorflow import keras
    from tensorflow.keras.models import Sequential
    from tensorflow.keras.layers import LSTM, Dense, Dropout, BatchNormalization
    from tensorflow.keras.optimizers import Adam
    from tensorflow.keras.callbacks import EarlyStopping, ReduceLROnPlateau
    TENSORFLOW_AVAILABLE = True
except ImportError:
    TENSORFLOW_AVAILABLE = False
    logging.warning("TensorFlow not available. Deep learning features will be limited.")

try:
    from sklearn.ensemble import VotingRegressor, VotingClassifier, StackingRegressor, StackingClassifier
    from sklearn.linear_model import LinearRegression, LogisticRegression
    from sklearn.svm import SVR, SVC
    from sklearn.tree import DecisionTreeRegressor, DecisionTreeClassifier
    from sklearn.neural_network import MLPRegressor, MLPClassifier
    from sklearn.linear_model import SGDRegressor, SGDClassifier, PassiveAggressiveRegressor, PassiveAggressiveClassifier
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False
    logging.warning("Scikit-learn not available. Ensemble and online learning features will be limited.")

logger = logging.getLogger(__name__)

@dataclass
class ModelPerformance:
    """Model performance metrics"""
    accuracy: float
    precision: float
    recall: float
    f1_score: float
    mse: float
    mae: float
    r2_score: float
    training_time: float
    prediction_time: float
    model_size: float  # MB

class AdvancedMLAlgorithms:
    """
    Advanced ML Algorithms Service with deep learning, ensemble methods, and online learning
    """
    
    def __init__(self, models_dir: str = "advanced_ml_models"):
        self.models_dir = models_dir
        self._ensure_models_directory()
        
        # Model storage
        self.models = {}
        self.performance_metrics = {}
        
        # Configuration
        self.lstm_config = {
            'units': [50, 100, 200],
            'layers': [2, 3, 4],
            'dropout': [0.1, 0.2, 0.3],
            'learning_rate': [0.001, 0.01, 0.1],
            'batch_size': [16, 32, 64]
        }
        
        self.ensemble_config = {
            'voting_methods': ['hard', 'soft'],
            'stacking_methods': ['linear', 'non_linear'],
            'base_models': ['linear', 'svm', 'tree', 'neural_network']
        }
        
        self.online_config = {
            'learning_rates': [0.01, 0.1, 0.5],
            'regularization': [0.001, 0.01, 0.1],
            'max_iterations': [1000, 5000, 10000]
        }
        
        logger.info("🚀 Advanced ML Algorithms Service initialized")
        logger.info(f"   TensorFlow: {'✅ Available' if TENSORFLOW_AVAILABLE else '❌ Not Available'}")
        logger.info(f"   Scikit-learn: {'✅ Available' if SKLEARN_AVAILABLE else '❌ Not Available'}")
    
    def _ensure_models_directory(self):
        """Ensure the models directory exists"""
        if not os.path.exists(self.models_dir):
            os.makedirs(self.models_dir)
            logger.info(f"📁 Created advanced models directory: {self.models_dir}")
    
    # ============================================================================
    # DEEP LEARNING (LSTM) METHODS
    # ============================================================================
    
    def create_lstm_model(self, input_shape: Tuple[int, int], output_size: int = 1, 
                         units: List[int] = None, dropout: float = 0.2):
        """Create LSTM model for time series prediction"""
        if not TENSORFLOW_AVAILABLE:
            raise ImportError("TensorFlow is required for LSTM models")
        
        if units is None:
            units = [100, 50]
        
        # Import keras components only when needed
        from tensorflow.keras.models import Sequential
        from tensorflow.keras.layers import LSTM, Dense, Dropout, BatchNormalization
        from tensorflow.keras.optimizers import Adam
        
        model = Sequential()
        
        # First LSTM layer
        model.add(LSTM(units[0], return_sequences=True, input_shape=input_shape))
        model.add(BatchNormalization())
        model.add(Dropout(dropout))
        
        # Additional LSTM layers
        for i in range(1, len(units) - 1):
            model.add(LSTM(units[i], return_sequences=True))
            model.add(BatchNormalization())
            model.add(Dropout(dropout))
        
        # Final LSTM layer
        if len(units) > 1:
            model.add(LSTM(units[-1], return_sequences=False))
            model.add(BatchNormalization())
            model.add(Dropout(dropout))
        
        # Output layer
        model.add(Dense(output_size, activation='linear'))
        
        # Compile model
        optimizer = Adam(learning_rate=0.001)
        model.compile(optimizer=optimizer, loss='mse', metrics=['mae'])
        
        return model
    
    def prepare_lstm_data(self, data: np.ndarray, lookback: int = 60) -> Tuple[np.ndarray, np.ndarray]:
        """Prepare data for LSTM model"""
        X, y = [], []
        
        for i in range(lookback, len(data)):
            X.append(data[i-lookback:i])
            y.append(data[i])
        
        return np.array(X), np.array(y)
    
    def train_lstm_model(self, X_train: np.ndarray, y_train: np.ndarray, 
                        X_val: np.ndarray = None, y_val: np.ndarray = None,
                        model_name: str = "lstm_model") -> Dict[str, Any]:
        """Train LSTM model with hyperparameter optimization"""
        if not TENSORFLOW_AVAILABLE:
            raise ImportError("TensorFlow is required for LSTM training")
        
        logger.info(f"🚀 Training LSTM model: {model_name}")
        
        # Prepare validation data
        if X_val is None or y_val is None:
            # Split training data for validation
            split_idx = int(len(X_train) * 0.8)
            X_val = X_train[split_idx:]
            y_val = y_train[split_idx:]
            X_train = X_train[:split_idx]
            y_train = y_train[:split_idx]
        
        # Hyperparameter optimization
        best_model = None
        best_val_loss = float('inf')
        best_params = {}
        
        for units in self.lstm_config['units']:
            for layers in self.lstm_config['layers']:
                for dropout in self.lstm_config['dropout']:
                    for lr in self.lstm_config['learning_rate']:
                        for batch_size in self.lstm_config['batch_size']:
                            logger.info(f"   Testing: units={units}, layers={layers}, dropout={dropout}, lr={lr}, batch={batch_size}")
                            
                            # Create model
                            model_units = [units] * layers
                            model = self.create_lstm_model(
                                input_shape=(X_train.shape[1], X_train.shape[2]),
                                units=model_units,
                                dropout=dropout
                            )
                            
                            # Callbacks
                            from tensorflow.keras.callbacks import EarlyStopping, ReduceLROnPlateau
                            callbacks = [
                                EarlyStopping(patience=10, restore_best_weights=True),
                                ReduceLROnPlateau(factor=0.5, patience=5)
                            ]
                            
                            # Train model
                            start_time = time.time()
                            history = model.fit(
                                X_train, y_train,
                                validation_data=(X_val, y_val),
                                epochs=100,
                                batch_size=batch_size,
                                callbacks=callbacks,
                                verbose=0
                            )
                            training_time = time.time() - start_time
                            
                            # Evaluate
                            val_loss = min(history.history['val_loss'])
                            
                            if val_loss < best_val_loss:
                                best_val_loss = val_loss
                                best_model = model
                                best_params = {
                                    'units': units,
                                    'layers': layers,
                                    'dropout': dropout,
                                    'learning_rate': lr,
                                    'batch_size': batch_size,
                                    'training_time': training_time
                                }
        
        # Save best model
        if best_model:
            self.models[model_name] = best_model
            model_path = os.path.join(self.models_dir, f"{model_name}.h5")
            best_model.save(model_path)
            
            # Calculate performance metrics
            train_pred = best_model.predict(X_train)
            val_pred = best_model.predict(X_val)
            
            performance = ModelPerformance(
                accuracy=0.0,  # Not applicable for regression
                precision=0.0,  # Not applicable for regression
                recall=0.0,     # Not applicable for regression
                f1_score=0.0,   # Not applicable for regression
                mse=np.mean((y_val - val_pred) ** 2),
                mae=np.mean(np.abs(y_val - val_pred)),
                r2_score=1 - np.sum((y_val - val_pred) ** 2) / np.sum((y_val - np.mean(y_val)) ** 2),
                training_time=best_params['training_time'],
                prediction_time=0.0,  # Will be measured during prediction
                model_size=os.path.getsize(model_path) / (1024 * 1024)  # MB
            )
            
            self.performance_metrics[model_name] = performance
            
            logger.info(f"✅ LSTM model trained successfully!")
            logger.info(f"   Best validation loss: {best_val_loss:.6f}")
            logger.info(f"   Best parameters: {best_params}")
            logger.info(f"   Model saved: {model_path}")
            
            return {
                'model': best_model,
                'parameters': best_params,
                'performance': performance,
                'history': history.history if 'history' in locals() else None
            }
        
        return None
    
    def predict_lstm(self, model_name: str, X: np.ndarray) -> np.ndarray:
        """Make predictions using trained LSTM model"""
        if model_name not in self.models:
            raise ValueError(f"Model {model_name} not found")
        
        model = self.models[model_name]
        
        start_time = time.time()
        predictions = model.predict(X)
        prediction_time = time.time() - start_time
        
        # Update performance metrics
        if model_name in self.performance_metrics:
            self.performance_metrics[model_name].prediction_time = prediction_time
        
        return predictions
    
    # ============================================================================
    # ENSEMBLE METHODS
    # ============================================================================
    
    def create_voting_ensemble(self, X_train: np.ndarray, y_train: np.ndarray,
                              model_name: str = "voting_ensemble") -> Dict[str, Any]:
        """Create voting ensemble model"""
        if not SKLEARN_AVAILABLE:
            raise ImportError("Scikit-learn is required for ensemble methods")
        
        logger.info(f"🚀 Creating voting ensemble: {model_name}")
        
        # Base models
        base_models = [
            ('linear', LinearRegression()),
            ('svm', SVR(kernel='rbf')),
            ('tree', DecisionTreeRegressor(random_state=42)),
            ('neural', MLPRegressor(hidden_layer_sizes=(100, 50), random_state=42))
        ]
        
        # Create voting ensemble
        ensemble = VotingRegressor(estimators=base_models)
        
        # Train ensemble
        start_time = time.time()
        ensemble.fit(X_train, y_train)
        training_time = time.time() - start_time
        
        # Evaluate
        train_pred = ensemble.predict(X_train)
        train_mse = np.mean((y_train - train_pred) ** 2)
        
        # Save model
        self.models[model_name] = ensemble
        model_path = os.path.join(self.models_dir, f"{model_name}.pkl")
        with open(model_path, 'wb') as f:
            pickle.dump(ensemble, f)
        
        # Performance metrics
        performance = ModelPerformance(
            accuracy=0.0,
            precision=0.0,
            recall=0.0,
            f1_score=0.0,
            mse=train_mse,
            mae=np.mean(np.abs(y_train - train_pred)),
            r2_score=ensemble.score(X_train, y_train),
            training_time=training_time,
            prediction_time=0.0,
            model_size=os.path.getsize(model_path) / (1024 * 1024)
        )
        
        self.performance_metrics[model_name] = performance
        
        logger.info(f"✅ Voting ensemble created successfully!")
        logger.info(f"   Training MSE: {train_mse:.6f}")
        logger.info(f"   R² Score: {performance.r2_score:.6f}")
        
        return {
            'model': ensemble,
            'performance': performance,
            'base_models': [name for name, _ in base_models]
        }
    
    def create_stacking_ensemble(self, X_train: np.ndarray, y_train: np.ndarray,
                                model_name: str = "stacking_ensemble") -> Dict[str, Any]:
        """Create stacking ensemble model"""
        if not SKLEARN_AVAILABLE:
            raise ImportError("Scikit-learn is required for ensemble methods")
        
        logger.info(f"🚀 Creating stacking ensemble: {model_name}")
        
        # Base models
        base_models = [
            ('linear', LinearRegression()),
            ('svm', SVR(kernel='rbf')),
            ('tree', DecisionTreeRegressor(random_state=42))
        ]
        
        # Meta-learner
        meta_learner = LinearRegression()
        
        # Create stacking ensemble
        ensemble = StackingRegressor(
            estimators=base_models,
            final_estimator=meta_learner,
            cv=5
        )
        
        # Train ensemble
        start_time = time.time()
        ensemble.fit(X_train, y_train)
        training_time = time.time() - start_time
        
        # Evaluate
        train_pred = ensemble.predict(X_train)
        train_mse = np.mean((y_train - train_pred) ** 2)
        
        # Save model
        self.models[model_name] = ensemble
        model_path = os.path.join(self.models_dir, f"{model_name}.pkl")
        with open(model_path, 'wb') as f:
            pickle.dump(ensemble, f)
        
        # Performance metrics
        performance = ModelPerformance(
            accuracy=0.0,
            precision=0.0,
            recall=0.0,
            f1_score=0.0,
            mse=train_mse,
            mae=np.mean(np.abs(y_train - train_pred)),
            r2_score=ensemble.score(X_train, y_train),
            training_time=training_time,
            prediction_time=0.0,
            model_size=os.path.getsize(model_path) / (1024 * 1024)
        )
        
        self.performance_metrics[model_name] = performance
        
        logger.info(f"✅ Stacking ensemble created successfully!")
        logger.info(f"   Training MSE: {train_mse:.6f}")
        logger.info(f"   R² Score: {performance.r2_score:.6f}")
        
        return {
            'model': ensemble,
            'performance': performance,
            'base_models': [name for name, _ in base_models],
            'meta_learner': 'LinearRegression'
        }
    
    # ============================================================================
    # ONLINE LEARNING METHODS
    # ============================================================================
    
    def create_online_learner(self, model_type: str = "sgd", 
                             model_name: str = "online_learner") -> Dict[str, Any]:
        """Create online learning model"""
        if not SKLEARN_AVAILABLE:
            raise ImportError("Scikit-learn is required for online learning")
        
        logger.info(f"🚀 Creating online learner: {model_name} ({model_type})")
        
        # Create online model
        if model_type == "sgd":
            model = SGDRegressor(
                learning_rate='adaptive',
                max_iter=1000,
                random_state=42
            )
        elif model_type == "passive_aggressive":
            model = PassiveAggressiveRegressor(
                max_iter=1000,
                random_state=42
            )
        elif model_type == "neural_network":
            model = MLPRegressor(
                hidden_layer_sizes=(50, 25),
                learning_rate='adaptive',
                max_iter=1000,
                random_state=42
            )
        else:
            raise ValueError(f"Unknown model type: {model_type}")
        
        # Save model
        self.models[model_name] = model
        model_path = os.path.join(self.models_dir, f"{model_name}.pkl")
        with open(model_path, 'wb') as f:
            pickle.dump(model, f)
        
        logger.info(f"✅ Online learner created successfully!")
        logger.info(f"   Model type: {model_type}")
        logger.info(f"   Model saved: {model_path}")
        
        return {
            'model': model,
            'model_type': model_type,
            'path': model_path
        }
    
    def update_online_learner(self, model_name: str, X_new: np.ndarray, y_new: np.ndarray) -> Dict[str, Any]:
        """Update online learning model with new data"""
        if model_name not in self.models:
            raise ValueError(f"Model {model_name} not found")
        
        model = self.models[model_name]
        
        logger.info(f"🔄 Updating online learner: {model_name}")
        logger.info(f"   New data points: {len(X_new)}")
        
        # Update model
        start_time = time.time()
        
        if hasattr(model, 'partial_fit'):
            # Use partial_fit for online learning
            if len(X_new.shape) == 1:
                X_new = X_new.reshape(1, -1)
            if len(y_new.shape) == 1:
                y_new = y_new.reshape(1, -1)
            
            # Ensure y_new is 1D for regression models
            if len(y_new.shape) > 1:
                y_new = y_new.flatten()
            
            model.partial_fit(X_new, y_new)
        else:
            # Retrain with all data
            model.fit(X_new, y_new)
        
        update_time = time.time() - start_time
        
        # Save updated model
        model_path = os.path.join(self.models_dir, f"{model_name}.pkl")
        with open(model_path, 'wb') as f:
            pickle.dump(model, f)
        
        logger.info(f"✅ Online learner updated successfully!")
        logger.info(f"   Update time: {update_time:.4f}s")
        
        return {
            'model': model,
            'update_time': update_time,
            'new_data_points': len(X_new)
        }
    
    # ============================================================================
    # MODEL MANAGEMENT
    # ============================================================================
    
    def load_model(self, model_name: str) -> Any:
        """Load a saved model"""
        model_path = os.path.join(self.models_dir, f"{model_name}.pkl")
        h5_path = os.path.join(self.models_dir, f"{model_name}.h5")
        
        if os.path.exists(model_path):
            with open(model_path, 'rb') as f:
                model = pickle.load(f)
            logger.info(f"📥 Loaded model: {model_name} (.pkl)")
        elif os.path.exists(h5_path) and TENSORFLOW_AVAILABLE:
            from tensorflow import keras
            model = keras.models.load_model(h5_path)
            logger.info(f"📥 Loaded model: {model_name} (.h5)")
        else:
            raise FileNotFoundError(f"Model {model_name} not found")
        
        self.models[model_name] = model
        return model
    
    def save_model(self, model_name: str, model: Any) -> str:
        """Save a model"""
        if hasattr(model, 'save') and TENSORFLOW_AVAILABLE:
            # Keras model
            model_path = os.path.join(self.models_dir, f"{model_name}.h5")
            model.save(model_path)
        else:
            # Scikit-learn model
            model_path = os.path.join(self.models_dir, f"{model_name}.pkl")
            with open(model_path, 'wb') as f:
                pickle.dump(model, f)
        
        logger.info(f"💾 Saved model: {model_name}")
        return model_path
    
    def list_models(self) -> List[str]:
        """List all available models"""
        models = []
        for file in os.listdir(self.models_dir):
            if file.endswith(('.pkl', '.h5')):
                models.append(file.replace('.pkl', '').replace('.h5', ''))
        return models
    
    def get_model_performance(self, model_name: str) -> Optional[ModelPerformance]:
        """Get performance metrics for a model"""
        return self.performance_metrics.get(model_name)
    
    def delete_model(self, model_name: str) -> bool:
        """Delete a model"""
        try:
            # Remove from memory
            if model_name in self.models:
                del self.models[model_name]
            
            # Remove from performance metrics
            if model_name in self.performance_metrics:
                del self.performance_metrics[model_name]
            
            # Remove files
            pkl_path = os.path.join(self.models_dir, f"{model_name}.pkl")
            h5_path = os.path.join(self.models_dir, f"{model_name}.h5")
            
            if os.path.exists(pkl_path):
                os.remove(pkl_path)
            if os.path.exists(h5_path):
                os.remove(h5_path)
            
            logger.info(f"🗑️  Deleted model: {model_name}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error deleting model {model_name}: {e}")
            return False
    
    def get_service_status(self) -> Dict[str, Any]:
        """Get service status and available models"""
        return {
            'tensorflow_available': TENSORFLOW_AVAILABLE,
            'sklearn_available': SKLEARN_AVAILABLE,
            'models_directory': self.models_dir,
            'models_loaded': list(self.models.keys()),
            'models_available': self.list_models(),
            'performance_metrics': {
                name: {
                    'mse': metrics.mse,
                    'mae': metrics.mae,
                    'r2_score': metrics.r2_score,
                    'training_time': metrics.training_time,
                    'model_size_mb': metrics.model_size
                } for name, metrics in self.performance_metrics.items()
            }
        }

# Import time module for timing functions
import time
