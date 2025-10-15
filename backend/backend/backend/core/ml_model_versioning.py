"""
Phase 2B: ML Model Versioning and A/B Testing

This module implements ML model versioning, A/B testing, and model lifecycle management
using MLflow and custom versioning logic.
"""

import os
import json
import logging
import pickle
import hashlib
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
import numpy as np
import pandas as pd
from pathlib import Path
import joblib
import mlflow
import mlflow.sklearn
import mlflow.xgboost
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score
from sklearn.model_selection import train_test_split
import xgboost as xgb

logger = logging.getLogger(__name__)

@dataclass
class ModelMetadata:
    """Metadata for model versioning"""
    model_id: str
    version: str
    model_type: str
    training_data_hash: str
    feature_columns: List[str]
    target_column: str
    training_timestamp: datetime
    performance_metrics: Dict[str, float]
    hyperparameters: Dict[str, Any]
    model_size_bytes: int
    training_duration_seconds: float
    data_splits: Dict[str, int]
    validation_strategy: str

@dataclass
class ModelExperiment:
    """Experiment configuration for A/B testing"""
    experiment_id: str
    name: str
    description: str
    start_date: datetime
    end_date: Optional[datetime]
    traffic_split: Dict[str, float]  # model_version -> traffic_percentage
    success_metric: str
    minimum_sample_size: int
    confidence_level: float
    status: str  # 'active', 'completed', 'paused'

@dataclass
class ModelPrediction:
    """Model prediction with versioning info"""
    model_version: str
    prediction: float
    confidence: float
    features: Dict[str, float]
    timestamp: datetime
    experiment_id: Optional[str] = None

class ModelVersionManager:
    """Manages ML model versioning and lifecycle"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.models_dir = Path(config.get('models_dir', 'models'))
        self.models_dir.mkdir(exist_ok=True)
        
        # Initialize MLflow
        mlflow.set_tracking_uri(config.get('mlflow_tracking_uri', 'file:./mlruns'))
        self.experiment_name = config.get('experiment_name', 'riches-reach-ml')
        
        # Create experiment if it doesn't exist
        try:
            self.experiment_id = mlflow.create_experiment(self.experiment_name)
        except mlflow.exceptions.MlflowException:
            self.experiment_id = mlflow.get_experiment_by_name(self.experiment_name).experiment_id
        
        # Model registry
        self.model_registry = {}
        self.active_models = {}
        self.experiments = {}
        
        logger.info(f"✅ Model version manager initialized with experiment: {self.experiment_name}")
    
    def _calculate_data_hash(self, data: pd.DataFrame) -> str:
        """Calculate hash of training data for versioning"""
        data_str = data.to_string()
        return hashlib.md5(data_str.encode()).hexdigest()
    
    def _generate_model_id(self, model_type: str, feature_columns: List[str]) -> str:
        """Generate unique model ID"""
        features_str = "_".join(sorted(feature_columns))
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return f"{model_type}_{features_str}_{timestamp}"
    
    def _calculate_performance_metrics(self, y_true: np.ndarray, y_pred: np.ndarray, y_prob: Optional[np.ndarray] = None) -> Dict[str, float]:
        """Calculate comprehensive performance metrics"""
        metrics = {
            'accuracy': accuracy_score(y_true, y_pred),
            'precision': precision_score(y_true, y_pred, average='weighted', zero_division=0),
            'recall': recall_score(y_true, y_pred, average='weighted', zero_division=0),
            'f1_score': f1_score(y_true, y_pred, average='weighted', zero_division=0)
        }
        
        # Add probability-based metrics if available
        if y_prob is not None:
            # Calculate AUC for binary classification
            if len(np.unique(y_true)) == 2:
                from sklearn.metrics import roc_auc_score
                metrics['auc'] = roc_auc_score(y_true, y_prob)
            
            # Calculate log loss
            from sklearn.metrics import log_loss
            metrics['log_loss'] = log_loss(y_true, y_prob)
        
        return metrics
    
    def train_and_version_model(
        self,
        model_type: str,
        X: pd.DataFrame,
        y: pd.Series,
        hyperparameters: Dict[str, Any],
        feature_columns: List[str],
        target_column: str,
        validation_strategy: str = 'time_split'
    ) -> ModelMetadata:
        """Train a new model and create a version"""
        
        start_time = datetime.now()
        
        # Generate model ID and version
        model_id = self._generate_model_id(model_type, feature_columns)
        version = f"v{len(self.model_registry.get(model_id, [])) + 1}"
        
        # Calculate data hash
        data_hash = self._calculate_data_hash(X)
        
        # Prepare data
        X_features = X[feature_columns]
        
        # Split data based on validation strategy
        if validation_strategy == 'time_split':
            # Time-based split (last 20% for validation)
            split_idx = int(len(X_features) * 0.8)
            X_train, X_val = X_features[:split_idx], X_features[split_idx:]
            y_train, y_val = y[:split_idx], y[split_idx:]
        else:
            # Random split
            X_train, X_val, y_train, y_val = train_test_split(
                X_features, y, test_size=0.2, random_state=42
            )
        
        # Train model
        if model_type == 'xgboost':
            model = xgb.XGBClassifier(**hyperparameters)
        elif model_type == 'random_forest':
            from sklearn.ensemble import RandomForestClassifier
            model = RandomForestClassifier(**hyperparameters)
        else:
            raise ValueError(f"Unsupported model type: {model_type}")
        
        model.fit(X_train, y_train)
        
        # Make predictions
        y_pred = model.predict(X_val)
        y_prob = model.predict_proba(X_val)[:, 1] if hasattr(model, 'predict_proba') else None
        
        # Calculate metrics
        metrics = self._calculate_performance_metrics(y_val, y_pred, y_prob)
        
        # Calculate training duration
        training_duration = (datetime.now() - start_time).total_seconds()
        
        # Create model metadata
        metadata = ModelMetadata(
            model_id=model_id,
            version=version,
            model_type=model_type,
            training_data_hash=data_hash,
            feature_columns=feature_columns,
            target_column=target_column,
            training_timestamp=start_time,
            performance_metrics=metrics,
            hyperparameters=hyperparameters,
            model_size_bytes=len(pickle.dumps(model)),
            training_duration_seconds=training_duration,
            data_splits={
                'train_size': len(X_train),
                'validation_size': len(X_val),
                'total_size': len(X_features)
            },
            validation_strategy=validation_strategy
        )
        
        # Save model and metadata
        self._save_model(model, metadata)
        
        # Log to MLflow
        self._log_to_mlflow(model, metadata, X_train, y_train, X_val, y_val)
        
        # Register model
        if model_id not in self.model_registry:
            self.model_registry[model_id] = []
        self.model_registry[model_id].append(metadata)
        
        logger.info(f"✅ Model trained and versioned: {model_id} {version}")
        return metadata
    
    def _save_model(self, model: Any, metadata: ModelMetadata):
        """Save model and metadata to disk"""
        model_dir = self.models_dir / metadata.model_id / metadata.version
        model_dir.mkdir(parents=True, exist_ok=True)
        
        # Save model
        model_path = model_dir / 'model.pkl'
        joblib.dump(model, model_path)
        
        # Save metadata
        metadata_path = model_dir / 'metadata.json'
        with open(metadata_path, 'w') as f:
            json.dump(asdict(metadata), f, default=str, indent=2)
        
        logger.debug(f"Model saved to: {model_dir}")
    
    def _log_to_mlflow(self, model: Any, metadata: ModelMetadata, X_train: pd.DataFrame, y_train: pd.Series, X_val: pd.DataFrame, y_val: pd.Series):
        """Log model to MLflow"""
        with mlflow.start_run(experiment_id=self.experiment_id):
            # Log parameters
            mlflow.log_params(metadata.hyperparameters)
            mlflow.log_param("model_type", metadata.model_type)
            mlflow.log_param("feature_count", len(metadata.feature_columns))
            mlflow.log_param("training_samples", len(X_train))
            mlflow.log_param("validation_samples", len(X_val))
            
            # Log metrics
            mlflow.log_metrics(metadata.performance_metrics)
            mlflow.log_metric("training_duration_seconds", metadata.training_duration_seconds)
            mlflow.log_metric("model_size_bytes", metadata.model_size_bytes)
            
            # Log model
            if metadata.model_type == 'xgboost':
                mlflow.xgboost.log_model(model, "model")
            else:
                mlflow.sklearn.log_model(model, "model")
            
            # Log tags
            mlflow.set_tag("model_id", metadata.model_id)
            mlflow.set_tag("version", metadata.version)
            mlflow.set_tag("data_hash", metadata.training_data_hash)
    
    def load_model(self, model_id: str, version: str) -> Tuple[Any, ModelMetadata]:
        """Load a specific model version"""
        model_dir = self.models_dir / model_id / version
        
        if not model_dir.exists():
            raise FileNotFoundError(f"Model not found: {model_id} {version}")
        
        # Load model
        model_path = model_dir / 'model.pkl'
        model = joblib.load(model_path)
        
        # Load metadata
        metadata_path = model_dir / 'metadata.json'
        with open(metadata_path, 'r') as f:
            metadata_dict = json.load(f)
        
        # Convert timestamp strings back to datetime
        metadata_dict['training_timestamp'] = datetime.fromisoformat(metadata_dict['training_timestamp'])
        metadata = ModelMetadata(**metadata_dict)
        
        return model, metadata
    
    def get_best_model(self, model_id: str, metric: str = 'f1_score') -> Tuple[Any, ModelMetadata]:
        """Get the best performing model version"""
        if model_id not in self.model_registry:
            raise ValueError(f"Model ID not found: {model_id}")
        
        versions = self.model_registry[model_id]
        best_version = max(versions, key=lambda v: v.performance_metrics.get(metric, 0))
        
        return self.load_model(model_id, best_version.version)
    
    def list_models(self) -> Dict[str, List[ModelMetadata]]:
        """List all models and their versions"""
        return self.model_registry.copy()
    
    def delete_model_version(self, model_id: str, version: str) -> bool:
        """Delete a specific model version"""
        try:
            model_dir = self.models_dir / model_id / version
            if model_dir.exists():
                import shutil
                shutil.rmtree(model_dir)
                
                # Remove from registry
                if model_id in self.model_registry:
                    self.model_registry[model_id] = [
                        v for v in self.model_registry[model_id] if v.version != version
                    ]
                
                logger.info(f"✅ Deleted model version: {model_id} {version}")
                return True
            return False
        except Exception as e:
            logger.error(f"❌ Failed to delete model version: {e}")
            return False

class ABTestingManager:
    """Manages A/B testing for ML models"""
    
    def __init__(self, model_manager: ModelVersionManager):
        self.model_manager = model_manager
        self.experiments = {}
        self.traffic_splits = {}
        self.experiment_results = {}
    
    def create_experiment(
        self,
        name: str,
        description: str,
        model_versions: List[Tuple[str, str]],  # (model_id, version)
        traffic_split: List[float],
        success_metric: str = 'f1_score',
        minimum_sample_size: int = 1000,
        confidence_level: float = 0.95
    ) -> ModelExperiment:
        """Create a new A/B testing experiment"""
        
        if len(model_versions) != len(traffic_split):
            raise ValueError("Number of model versions must match traffic split")
        
        if abs(sum(traffic_split) - 1.0) > 0.001:
            raise ValueError("Traffic split must sum to 1.0")
        
        experiment_id = f"exp_{int(datetime.now().timestamp())}"
        
        # Create traffic split dictionary
        traffic_dict = {}
        for (model_id, version), percentage in zip(model_versions, traffic_split):
            traffic_dict[f"{model_id}_{version}"] = percentage
        
        experiment = ModelExperiment(
            experiment_id=experiment_id,
            name=name,
            description=description,
            start_date=datetime.now(),
            end_date=None,
            traffic_split=traffic_dict,
            success_metric=success_metric,
            minimum_sample_size=minimum_sample_size,
            confidence_level=confidence_level,
            status='active'
        )
        
        self.experiments[experiment_id] = experiment
        self.traffic_splits[experiment_id] = traffic_dict
        self.experiment_results[experiment_id] = {
            'predictions': [],
            'outcomes': [],
            'metrics': {}
        }
        
        logger.info(f"✅ Created A/B testing experiment: {experiment_id}")
        return experiment
    
    def get_model_for_prediction(self, experiment_id: str, user_id: str) -> Tuple[Any, ModelMetadata, str]:
        """Get model for prediction based on traffic split"""
        if experiment_id not in self.experiments:
            raise ValueError(f"Experiment not found: {experiment_id}")
        
        experiment = self.experiments[experiment_id]
        if experiment.status != 'active':
            raise ValueError(f"Experiment is not active: {experiment.status}")
        
        # Use user_id hash for consistent traffic splitting
        user_hash = int(hashlib.md5(user_id.encode()).hexdigest(), 16)
        traffic_value = (user_hash % 10000) / 10000.0
        
        # Determine which model to use
        cumulative = 0.0
        selected_model = None
        
        for model_version, percentage in experiment.traffic_split.items():
            cumulative += percentage
            if traffic_value <= cumulative:
                selected_model = model_version
                break
        
        if not selected_model:
            # Fallback to first model
            selected_model = list(experiment.traffic_split.keys())[0]
        
        # Parse model_id and version
        model_id, version = selected_model.rsplit('_', 1)
        
        # Load model
        model, metadata = self.model_manager.load_model(model_id, version)
        
        return model, metadata, selected_model
    
    def record_prediction(self, experiment_id: str, prediction: ModelPrediction):
        """Record a prediction for experiment tracking"""
        if experiment_id not in self.experiment_results:
            self.experiment_results[experiment_id] = {
                'predictions': [],
                'outcomes': [],
                'metrics': {}
            }
        
        self.experiment_results[experiment_id]['predictions'].append(prediction)
    
    def record_outcome(self, experiment_id: str, prediction_id: str, outcome: float):
        """Record the outcome of a prediction"""
        if experiment_id not in self.experiment_results:
            return
        
        # Find the prediction and record outcome
        for pred in self.experiment_results[experiment_id]['predictions']:
            if pred.timestamp.isoformat() == prediction_id:
                self.experiment_results[experiment_id]['outcomes'].append({
                    'prediction_id': prediction_id,
                    'outcome': outcome,
                    'timestamp': datetime.now()
                })
                break
    
    def analyze_experiment(self, experiment_id: str) -> Dict[str, Any]:
        """Analyze experiment results"""
        if experiment_id not in self.experiment_results:
            return {}
        
        results = self.experiment_results[experiment_id]
        experiment = self.experiments[experiment_id]
        
        # Group predictions by model version
        model_predictions = {}
        for pred in results['predictions']:
            model_version = pred.model_version
            if model_version not in model_predictions:
                model_predictions[model_version] = []
            model_predictions[model_version].append(pred)
        
        # Calculate metrics for each model
        analysis = {
            'experiment_id': experiment_id,
            'total_predictions': len(results['predictions']),
            'total_outcomes': len(results['outcomes']),
            'model_performance': {},
            'statistical_significance': {},
            'recommendation': 'continue'  # continue, promote, stop
        }
        
        for model_version, predictions in model_predictions.items():
            # Calculate basic metrics
            pred_values = [p.prediction for p in predictions]
            conf_values = [p.confidence for p in predictions]
            
            analysis['model_performance'][model_version] = {
                'prediction_count': len(predictions),
                'avg_prediction': np.mean(pred_values),
                'avg_confidence': np.mean(conf_values),
                'prediction_std': np.std(pred_values)
            }
        
        # Check if we have enough data for statistical significance
        if len(results['outcomes']) >= experiment.minimum_sample_size:
            # Perform statistical significance testing
            # This is a simplified version - in production, you'd use proper statistical tests
            analysis['statistical_significance'] = {
                'sufficient_data': True,
                'confidence_level': experiment.confidence_level
            }
        
        return analysis
    
    def end_experiment(self, experiment_id: str) -> bool:
        """End an experiment"""
        if experiment_id not in self.experiments:
            return False
        
        self.experiments[experiment_id].end_date = datetime.now()
        self.experiments[experiment_id].status = 'completed'
        
        logger.info(f"✅ Ended experiment: {experiment_id}")
        return True

# Global instances
model_version_manager = None
ab_testing_manager = None

def get_model_version_manager() -> Optional[ModelVersionManager]:
    """Get the global model version manager"""
    return model_version_manager

def get_ab_testing_manager() -> Optional[ABTestingManager]:
    """Get the global A/B testing manager"""
    return ab_testing_manager

def initialize_ml_versioning(config: Dict[str, Any]) -> Tuple[ModelVersionManager, ABTestingManager]:
    """Initialize ML versioning system"""
    global model_version_manager, ab_testing_manager
    
    model_version_manager = ModelVersionManager(config)
    ab_testing_manager = ABTestingManager(model_version_manager)
    
    logger.info("✅ ML versioning system initialized")
    return model_version_manager, ab_testing_manager
