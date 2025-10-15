#!/usr/bin/env python3
"""
AWS Batch Training Script

This script runs inside AWS Batch containers to train ML models.
It downloads training data from S3, trains the model, and uploads results back to S3.
"""

import os
import sys
import json
import logging
import pandas as pd
import numpy as np
from datetime import datetime
import boto3
import joblib
import mlflow
import mlflow.sklearn
import mlflow.xgboost
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, roc_auc_score
import xgboost as xgb
from sklearn.ensemble import RandomForestClassifier
import hashlib

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def download_training_data(s3_path: str, local_path: str) -> bool:
    """Download training data from S3"""
    try:
        s3_client = boto3.client('s3')
        
        # Parse S3 path
        if s3_path.startswith('s3://'):
            s3_path = s3_path[5:]
        
        bucket, key = s3_path.split('/', 1)
        
        # Download file
        s3_client.download_file(bucket, key, local_path)
        logger.info(f"✅ Downloaded training data to {local_path}")
        return True
        
    except Exception as e:
        logger.error(f"❌ Failed to download training data: {e}")
        return False

def upload_results(s3_path: str, local_path: str) -> bool:
    """Upload results to S3"""
    try:
        s3_client = boto3.client('s3')
        
        # Parse S3 path
        if s3_path.startswith('s3://'):
            s3_path = s3_path[5:]
        
        bucket, key = s3_path.split('/', 1)
        
        # Upload file
        s3_client.upload_file(local_path, bucket, key)
        logger.info(f"✅ Uploaded results to s3://{bucket}/{key}")
        return True
        
    except Exception as e:
        logger.error(f"❌ Failed to upload results: {e}")
        return False

def calculate_performance_metrics(y_true: np.ndarray, y_pred: np.ndarray, y_prob: np.ndarray = None) -> dict:
    """Calculate comprehensive performance metrics"""
    metrics = {
        'accuracy': accuracy_score(y_true, y_pred),
        'precision': precision_score(y_true, y_pred, average='weighted', zero_division=0),
        'recall': recall_score(y_true, y_pred, average='weighted', zero_division=0),
        'f1_score': f1_score(y_true, y_pred, average='weighted', zero_division=0)
    }
    
    if y_prob is not None:
        try:
            metrics['auc'] = roc_auc_score(y_true, y_prob)
        except ValueError:
            metrics['auc'] = 0.0
    
    return metrics

def train_model(model_type: str, X_train: pd.DataFrame, y_train: pd.Series, hyperparameters: dict):
    """Train a machine learning model"""
    try:
        logger.info(f"Training {model_type} model with hyperparameters: {hyperparameters}")
        
        if model_type == 'xgboost':
            model = xgb.XGBClassifier(**hyperparameters)
        elif model_type == 'random_forest':
            model = RandomForestClassifier(**hyperparameters)
        else:
            raise ValueError(f"Unsupported model type: {model_type}")
        
        # Train the model
        model.fit(X_train, y_train)
        
        logger.info(f"✅ {model_type} model training completed")
        return model
        
    except Exception as e:
        logger.error(f"❌ Failed to train {model_type} model: {e}")
        raise

def evaluate_model(model, X_test: pd.DataFrame, y_test: pd.Series) -> dict:
    """Evaluate model performance"""
    try:
        # Make predictions
        y_pred = model.predict(X_test)
        y_prob = model.predict_proba(X_test)[:, 1] if hasattr(model, 'predict_proba') else None
        
        # Calculate metrics
        metrics = calculate_performance_metrics(y_test, y_pred, y_prob)
        
        logger.info(f"Model performance: {metrics}")
        return metrics
        
    except Exception as e:
        logger.error(f"❌ Failed to evaluate model: {e}")
        raise

def save_model_and_metadata(model, metrics: dict, hyperparameters: dict, output_dir: str, model_type: str):
    """Save model and metadata"""
    try:
        # Create output directory
        os.makedirs(output_dir, exist_ok=True)
        
        # Save model
        model_path = os.path.join(output_dir, 'model.pkl')
        joblib.dump(model, model_path)
        
        # Save metadata
        metadata = {
            'model_type': model_type,
            'hyperparameters': hyperparameters,
            'performance_metrics': metrics,
            'training_timestamp': datetime.now().isoformat(),
            'model_size_bytes': os.path.getsize(model_path)
        }
        
        metadata_path = os.path.join(output_dir, 'metadata.json')
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f, indent=2)
        
        logger.info(f"✅ Model and metadata saved to {output_dir}")
        
    except Exception as e:
        logger.error(f"❌ Failed to save model and metadata: {e}")
        raise

def log_to_mlflow(model, metrics: dict, hyperparameters: dict, model_type: str, job_name: str):
    """Log training results to MLflow"""
    try:
        # Set MLflow tracking URI
        mlflow_tracking_uri = os.getenv('MLFLOW_TRACKING_URI', 'file:./mlruns')
        mlflow.set_tracking_uri(mlflow_tracking_uri)
        
        # Set experiment
        experiment_name = os.getenv('MLFLOW_EXPERIMENT_NAME', 'riches-reach-ml')
        try:
            experiment_id = mlflow.create_experiment(experiment_name)
        except mlflow.exceptions.MlflowException:
            experiment_id = mlflow.get_experiment_by_name(experiment_name).experiment_id
        
        with mlflow.start_run(experiment_id=experiment_id):
            # Log parameters
            mlflow.log_params(hyperparameters)
            mlflow.log_param("model_type", model_type)
            mlflow.log_param("job_name", job_name)
            
            # Log metrics
            mlflow.log_metrics(metrics)
            
            # Log model
            if model_type == 'xgboost':
                mlflow.xgboost.log_model(model, "model")
            else:
                mlflow.sklearn.log_model(model, "model")
            
            # Log tags
            mlflow.set_tag("training_job", job_name)
            mlflow.set_tag("model_type", model_type)
            mlflow.set_tag("aws_batch", "true")
        
        logger.info("✅ Results logged to MLflow")
        
    except Exception as e:
        logger.error(f"❌ Failed to log to MLflow: {e}")
        # Don't raise - MLflow logging is optional

def main():
    """Main training function"""
    try:
        logger.info("🚀 Starting AWS Batch ML training job")
        
        # Get environment variables
        job_name = os.getenv('JOB_NAME', 'unknown')
        model_type = os.getenv('MODEL_TYPE', 'xgboost')
        training_data_path = os.getenv('TRAINING_DATA_PATH')
        hyperparameters_str = os.getenv('HYPERPARAMETERS', '{}')
        feature_columns_str = os.getenv('FEATURE_COLUMNS', '[]')
        target_column = os.getenv('TARGET_COLUMN', 'target')
        output_path = os.getenv('OUTPUT_PATH')
        
        logger.info(f"Job: {job_name}")
        logger.info(f"Model type: {model_type}")
        logger.info(f"Training data: {training_data_path}")
        logger.info(f"Output path: {output_path}")
        
        # Parse parameters
        hyperparameters = json.loads(hyperparameters_str)
        feature_columns = json.loads(feature_columns_str)
        
        # Download training data
        local_data_path = '/tmp/training_data.csv'
        if not download_training_data(training_data_path, local_data_path):
            sys.exit(1)
        
        # Load training data
        logger.info("Loading training data...")
        data = pd.read_csv(local_data_path)
        logger.info(f"Loaded {len(data)} rows, {len(data.columns)} columns")
        
        # Prepare features and target
        X = data[feature_columns]
        y = data[target_column]
        
        logger.info(f"Features: {feature_columns}")
        logger.info(f"Target: {target_column}")
        logger.info(f"Feature shape: {X.shape}")
        logger.info(f"Target shape: {y.shape}")
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42, stratify=y
        )
        
        logger.info(f"Training set: {X_train.shape}")
        logger.info(f"Test set: {X_test.shape}")
        
        # Train model
        model = train_model(model_type, X_train, y_train, hyperparameters)
        
        # Evaluate model
        metrics = evaluate_model(model, X_test, y_test)
        
        # Save model and metadata
        local_output_dir = '/tmp/model_output'
        save_model_and_metadata(model, metrics, hyperparameters, local_output_dir, model_type)
        
        # Upload results to S3
        if output_path:
            # Upload model
            model_s3_path = f"{output_path}model.pkl"
            upload_results(model_s3_path, os.path.join(local_output_dir, 'model.pkl'))
            
            # Upload metadata
            metadata_s3_path = f"{output_path}metadata.json"
            upload_results(metadata_s3_path, os.path.join(local_output_dir, 'metadata.json'))
        
        # Log to MLflow
        log_to_mlflow(model, metrics, hyperparameters, model_type, job_name)
        
        # Create summary
        summary = {
            'job_name': job_name,
            'model_type': model_type,
            'status': 'SUCCESS',
            'performance_metrics': metrics,
            'training_samples': len(X_train),
            'test_samples': len(X_test),
            'feature_count': len(feature_columns),
            'completed_at': datetime.now().isoformat()
        }
        
        # Save and upload summary
        summary_path = os.path.join(local_output_dir, 'summary.json')
        with open(summary_path, 'w') as f:
            json.dump(summary, f, indent=2)
        
        if output_path:
            summary_s3_path = f"{output_path}summary.json"
            upload_results(summary_s3_path, summary_path)
        
        logger.info("🎉 Training job completed successfully!")
        logger.info(f"Performance metrics: {metrics}")
        
        # Exit with success code
        sys.exit(0)
        
    except Exception as e:
        logger.error(f"❌ Training job failed: {e}")
        
        # Create error summary
        error_summary = {
            'job_name': os.getenv('JOB_NAME', 'unknown'),
            'status': 'FAILED',
            'error_message': str(e),
            'failed_at': datetime.now().isoformat()
        }
        
        # Try to upload error summary
        try:
            output_path = os.getenv('OUTPUT_PATH')
            if output_path:
                error_path = '/tmp/error_summary.json'
                with open(error_path, 'w') as f:
                    json.dump(error_summary, f, indent=2)
                
                error_s3_path = f"{output_path}error_summary.json"
                upload_results(error_s3_path, error_path)
        except:
            pass
        
        # Exit with error code
        sys.exit(1)

if __name__ == "__main__":
    main()
