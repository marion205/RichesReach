"""
ML Model Training Service for RAHA
Trains custom ML models on user's trading history to personalize signal confidence
"""
import logging
import json
import pickle
import numpy as np
from typing import Dict, List, Any, Optional, Tuple
from decimal import Decimal
from datetime import datetime, timedelta
from django.db.models import Q, Avg, Sum, Count
from django.utils import timezone

from .signal_performance_models import SignalPerformance, DayTradingSignal
from .raha_models import RAHASignal

logger = logging.getLogger(__name__)

try:
    import torch
    import torch.nn as nn
    from sklearn.model_selection import train_test_split
    from sklearn.preprocessing import StandardScaler
    from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, roc_auc_score
    ML_AVAILABLE = True
except ImportError:
    ML_AVAILABLE = False
    logger.warning("PyTorch/sklearn not available. ML training will use fallback methods.")


class MLTrainingService:
    """
    Service for training custom ML models on user's trading history.
    """
    
    def __init__(self):
        self.ml_available = ML_AVAILABLE
    
    def train_model(
        self,
        user,
        strategy_version_id: Optional[str] = None,
        symbol: Optional[str] = None,
        lookback_days: int = 90,
        model_type: str = 'confidence_predictor'
    ) -> Dict[str, Any]:
        """
        Train a custom ML model on user's trading history.
        
        Args:
            user: User instance
            strategy_version_id: Optional strategy version ID to filter signals
            symbol: Optional symbol to filter signals
            lookback_days: Number of days to look back for training data
            model_type: Type of model ('confidence_predictor', 'win_probability', 'pnl_predictor')
        
        Returns:
            Dictionary with training results, model metrics, and model data
        """
        try:
            # Extract features and labels from trading history
            features, labels = self._extract_training_data(
                user, strategy_version_id, symbol, lookback_days, model_type
            )
            
            if len(features) < 50:
                return {
                    'success': False,
                    'message': f'Insufficient data for training. Need at least 50 samples, got {len(features)}.',
                    'samples': len(features)
                }
            
            # Train model
            if self.ml_available:
                model, metrics = self._train_pytorch_model(features, labels, model_type)
            else:
                model, metrics = self._train_fallback_model(features, labels, model_type)
            
            # Serialize model
            model_data = self._serialize_model(model)
            
            return {
                'success': True,
                'message': 'Model trained successfully',
                'metrics': metrics,
                'model_data': model_data,
                'samples': len(features),
                'model_type': model_type,
                'trained_at': timezone.now().isoformat(),
            }
            
        except Exception as e:
            logger.error(f"Error training ML model: {e}", exc_info=True)
            return {
                'success': False,
                'message': f'Training failed: {str(e)}',
                'error': str(e)
            }
    
    def _extract_training_data(
        self,
        user,
        strategy_version_id: Optional[str],
        symbol: Optional[str],
        lookback_days: int,
        model_type: str
    ) -> Tuple[List[List[float]], List[float]]:
        """
        Extract features and labels from SignalPerformance data.
        
        Returns:
            Tuple of (features_list, labels_list)
        """
        # Get date range
        end_date = timezone.now()
        start_date = end_date - timedelta(days=lookback_days)
        
        # Get RAHA signals with performance data
        signals_query = RAHASignal.objects.filter(
            user=user,
            timestamp__gte=start_date,
            timestamp__lte=end_date
        )
        
        if strategy_version_id:
            signals_query = signals_query.filter(strategy_version_id=strategy_version_id)
        
        if symbol:
            signals_query = signals_query.filter(symbol=symbol)
        
        # Get linked SignalPerformance records
        day_trading_signal_ids = list(
            signals_query.filter(day_trading_signal__isnull=False)
            .values_list('day_trading_signal_id', flat=True)
        )
        
        if not day_trading_signal_ids:
            return [], []
        
        performances = SignalPerformance.objects.filter(
            signal_id__in=day_trading_signal_ids
        ).select_related('signal')
        
        features = []
        labels = []
        
        for perf in performances:
            signal = perf.signal
            
            # Extract features
            feature_vector = self._extract_features(signal, perf)
            
            # Extract label based on model type
            if model_type == 'confidence_predictor':
                # Predict confidence adjustment needed
                # Label: 1.0 if signal was profitable, 0.0 if not
                label = 1.0 if perf.pnl_dollars and perf.pnl_dollars > 0 else 0.0
            elif model_type == 'win_probability':
                # Predict win probability
                label = 1.0 if perf.outcome in ['WIN', 'TARGET_HIT'] else 0.0
            elif model_type == 'pnl_predictor':
                # Predict normalized P&L
                if perf.pnl_percent:
                    label = float(perf.pnl_percent) / 100.0  # Normalize to -1 to 1 range
                else:
                    label = 0.0
            else:
                label = 1.0 if perf.pnl_dollars and perf.pnl_dollars > 0 else 0.0
            
            features.append(feature_vector)
            labels.append(label)
        
        return features, labels
    
    def _extract_features(self, signal: DayTradingSignal, perf: SignalPerformance) -> List[float]:
        """
        Extract feature vector from signal and performance data.
        
        Features include:
        - Signal confidence score
        - Entry price
        - Stop loss distance
        - Take profit distance
        - R-multiple (risk/reward ratio)
        - Time of day
        - Day of week
        - Market regime indicators (if available)
        """
        features = []
        
        # Signal features
        if hasattr(signal, 'confidence_score') and signal.confidence_score:
            features.append(float(signal.confidence_score))
        else:
            features.append(0.5)  # Default confidence
        
        # Price features
        entry_price = float(signal.entry_price) if signal.entry_price else 0.0
        # DayTradingSignal uses stop_price, not stop_loss
        stop_loss = float(signal.stop_price) if hasattr(signal, 'stop_price') and signal.stop_price else entry_price * 0.98
        # DayTradingSignal uses target_prices (list), not take_profit
        if hasattr(signal, 'target_prices') and signal.target_prices:
            take_profit = float(signal.target_prices[0]) if isinstance(signal.target_prices, list) and len(signal.target_prices) > 0 else entry_price * 1.02
        elif hasattr(signal, 'take_profit') and signal.take_profit:
            take_profit = float(signal.take_profit)
        else:
            take_profit = entry_price * 1.02
        
        features.append(entry_price)
        features.append(stop_loss)
        features.append(take_profit)
        
        # Risk/reward ratio
        if entry_price > 0:
            risk = abs(entry_price - stop_loss)
            reward = abs(take_profit - entry_price)
            r_multiple = reward / risk if risk > 0 else 1.0
            features.append(r_multiple)
        else:
            features.append(1.0)
        
        # Time features
        if signal.generated_at:
            timestamp = signal.generated_at
            features.append(float(timestamp.hour) / 24.0)  # Hour of day (normalized)
            features.append(float(timestamp.weekday()) / 6.0)  # Day of week (normalized)
        else:
            features.extend([0.5, 0.5])
        
        # Performance features (if available)
        if perf:
            if perf.pnl_dollars:
                features.append(float(perf.pnl_dollars))
            else:
                features.append(0.0)
            
            if perf.pnl_percent:
                features.append(float(perf.pnl_percent))
            else:
                features.append(0.0)
        else:
            features.extend([0.0, 0.0])
        
        # Strategy type encoding (one-hot like)
        # DayTradingSignal uses 'side' field (LONG/SHORT), not 'signal_type'
        if hasattr(signal, 'side'):
            signal_side = signal.side
        elif hasattr(signal, 'signal_type'):
            signal_side = signal.signal_type
        else:
            signal_side = 'LONG'
        features.append(1.0 if signal_side == 'LONG' else 0.0)
        features.append(1.0 if signal_side == 'SHORT' else 0.0)
        
        return features
    
    def _train_pytorch_model(
        self,
        features: List[List[float]],
        labels: List[float],
        model_type: str
    ) -> Tuple[Any, Dict[str, float]]:
        """
        Train a PyTorch neural network model.
        """
        if not self.ml_available:
            raise ImportError("PyTorch is not available. Cannot train PyTorch model.")
        
        # Import here to ensure nn is available
        import torch
        import torch.nn as nn
        from sklearn.model_selection import train_test_split
        from sklearn.preprocessing import StandardScaler
        from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, roc_auc_score
        
        # Convert to numpy arrays
        X = np.array(features)
        y = np.array(labels)
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42
        )
        
        # Scale features
        scaler = StandardScaler()
        X_train_scaled = scaler.fit_transform(X_train)
        X_test_scaled = scaler.transform(X_test)
        
        # Convert to tensors
        X_train_tensor = torch.FloatTensor(X_train_scaled)
        y_train_tensor = torch.FloatTensor(y_train).reshape(-1, 1)
        X_test_tensor = torch.FloatTensor(X_test_scaled)
        y_test_tensor = torch.FloatTensor(y_test).reshape(-1, 1)
        
        # Define model
        input_size = X_train.shape[1]
        hidden_size = 64
        output_size = 1
        
        model = nn.Sequential(
            nn.Linear(input_size, hidden_size),
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(hidden_size, hidden_size // 2),
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(hidden_size // 2, output_size),
            nn.Sigmoid() if model_type in ['confidence_predictor', 'win_probability'] else nn.Tanh()
        )
        
        # Training
        criterion = nn.BCELoss() if model_type in ['confidence_predictor', 'win_probability'] else nn.MSELoss()
        optimizer = torch.optim.Adam(model.parameters(), lr=0.001)
        
        epochs = 100
        batch_size = 32
        
        for epoch in range(epochs):
            # Mini-batch training
            for i in range(0, len(X_train_tensor), batch_size):
                batch_X = X_train_tensor[i:i+batch_size]
                batch_y = y_train_tensor[i:i+batch_size]
                
                optimizer.zero_grad()
                outputs = model(batch_X)
                loss = criterion(outputs, batch_y)
                loss.backward()
                optimizer.step()
        
        # Evaluate
        model.eval()
        with torch.no_grad():
            y_pred = model(X_test_tensor).numpy().flatten()
            y_test_np = y_test_tensor.numpy().flatten()
        
        # Calculate metrics
        if model_type in ['confidence_predictor', 'win_probability']:
            y_pred_binary = (y_pred > 0.5).astype(int)
            metrics = {
                'accuracy': float(accuracy_score(y_test_np, y_pred_binary)),
                'precision': float(precision_score(y_test_np, y_pred_binary, zero_division=0)),
                'recall': float(recall_score(y_test_np, y_pred_binary, zero_division=0)),
                'f1_score': float(f1_score(y_test_np, y_pred_binary, zero_division=0)),
                'roc_auc': float(roc_auc_score(y_test_np, y_pred)) if len(np.unique(y_test_np)) > 1 else 0.0,
            }
        else:
            # Regression metrics
            mse = np.mean((y_test_np - y_pred) ** 2)
            mae = np.mean(np.abs(y_test_np - y_pred))
            metrics = {
                'mse': float(mse),
                'mae': float(mae),
                'rmse': float(np.sqrt(mse)),
            }
        
        # Store scaler with model
        model.scaler = scaler
        
        return model, metrics
    
    def _train_fallback_model(
        self,
        features: List[List[float]],
        labels: List[float],
        model_type: str
    ) -> Tuple[Dict[str, Any], Dict[str, float]]:
        """
        Fallback model training when ML libraries are not available.
        Uses simple rule-based approach.
        """
        # Simple average-based predictor
        avg_label = np.mean(labels) if labels else 0.5
        
        # Calculate basic metrics
        if model_type in ['confidence_predictor', 'win_probability']:
            metrics = {
                'accuracy': avg_label,  # Simple baseline
                'precision': avg_label,
                'recall': avg_label,
                'f1_score': avg_label,
                'roc_auc': 0.5,
            }
        else:
            metrics = {
                'mse': np.var(labels) if labels else 0.0,
                'mae': np.mean(np.abs(labels - avg_label)) if labels else 0.0,
                'rmse': np.sqrt(np.var(labels)) if labels else 0.0,
            }
        
        model = {
            'type': 'fallback',
            'avg_label': float(avg_label),
            'model_type': model_type
        }
        
        return model, metrics
    
    def _serialize_model(self, model: Any) -> str:
        """
        Serialize model to string for storage.
        """
        if self.ml_available:
            try:
                import torch.nn as nn
                if isinstance(model, nn.Module):
                    # Save PyTorch model state dict
                    model_state = {
                        'state_dict': model.state_dict(),
                        'scaler': model.scaler if hasattr(model, 'scaler') else None,
                        'input_size': model[0].in_features if hasattr(model[0], 'in_features') else None,
                    }
                    return pickle.dumps(model_state).hex()
            except ImportError:
                pass
        
        # JSON serializable fallback
        return json.dumps(model)
    
    def load_model(self, model_data: str) -> Any:
        """
        Load a serialized model.
        """
        try:
            if self.ml_available:
                # Try to load as PyTorch model
                try:
                    model_state = pickle.loads(bytes.fromhex(model_data))
                    # Reconstruct model (simplified - would need full architecture)
                    return model_state
                except:
                    pass
            
            # Fallback to JSON
            return json.loads(model_data)
        except Exception as e:
            logger.error(f"Error loading model: {e}")
            return None
    
    def predict(self, model: Any, features: List[float]) -> float:
        """
        Make a prediction using a trained model.
        """
        if self.ml_available and isinstance(model, dict) and 'state_dict' in model:
            # PyTorch model prediction
            try:
                model_obj = self._reconstruct_model(model)
                scaler = model.get('scaler')
                
                if scaler:
                    features_scaled = scaler.transform([features])
                else:
                    features_scaled = [features]
                
                X_tensor = torch.FloatTensor(features_scaled)
                model_obj.eval()
                with torch.no_grad():
                    prediction = model_obj(X_tensor).item()
                
                return float(prediction)
            except Exception as e:
                logger.error(f"Error in PyTorch prediction: {e}")
                return 0.5
        
        # Fallback prediction
        if isinstance(model, dict) and 'avg_label' in model:
            return model['avg_label']
        
        return 0.5
    
    def _reconstruct_model(self, model_state: Dict) -> Any:
        """
        Reconstruct PyTorch model from state dict.
        """
        if not self.ml_available:
            raise ImportError("PyTorch is not available. Cannot reconstruct PyTorch model.")
        
        import torch.nn as nn
        
        # Simplified - would need full architecture info
        input_size = model_state.get('input_size', 12)
        hidden_size = 64
        
        model = nn.Sequential(
            nn.Linear(input_size, hidden_size),
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(hidden_size, hidden_size // 2),
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(hidden_size // 2, 1),
            nn.Sigmoid()
        )
        
        if 'state_dict' in model_state:
            model.load_state_dict(model_state['state_dict'])
        
        return model

