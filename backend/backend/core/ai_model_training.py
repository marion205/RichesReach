"""
AI Model Training and Fine-tuning System - Phase 3
Advanced AI model training, fine-tuning, and optimization
"""

import os
import json
import logging
import asyncio
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score
import joblib
import torch
import transformers
from transformers import (
    AutoTokenizer, AutoModelForCausalLM, 
    TrainingArguments, Trainer, DataCollatorForLanguageModeling
)
import datasets
from datasets import Dataset
import wandb
import mlflow
import mlflow.transformers

logger = logging.getLogger("richesreach")

@dataclass
class TrainingConfig:
    """Training configuration"""
    model_name: str
    dataset_path: str
    output_dir: str
    num_epochs: int = 3
    batch_size: int = 8
    learning_rate: float = 5e-5
    warmup_steps: int = 100
    max_length: int = 512
    gradient_accumulation_steps: int = 4
    save_steps: int = 500
    eval_steps: int = 500
    logging_steps: int = 100
    evaluation_strategy: str = "steps"
    save_strategy: str = "steps"
    load_best_model_at_end: bool = True
    metric_for_best_model: str = "eval_loss"
    greater_is_better: bool = False

@dataclass
class ModelMetrics:
    """Model performance metrics"""
    accuracy: float
    precision: float
    recall: float
    f1_score: float
    loss: float
    perplexity: float
    training_time: float
    inference_time: float
    model_size_mb: float
    parameters_count: int

@dataclass
class TrainingResult:
    """Training result"""
    model_id: str
    model_name: str
    training_config: TrainingConfig
    metrics: ModelMetrics
    training_logs: List[Dict[str, Any]]
    model_path: str
    timestamp: datetime
    status: str  # success, failed, in_progress

class AIModelTrainer:
    """AI Model Training and Fine-tuning System"""
    
    def __init__(self):
        self.training_jobs: Dict[str, TrainingResult] = {}
        self.model_registry = {}
        self.dataset_cache = {}
        
        # Initialize MLflow
        self._initialize_mlflow()
        
        # Initialize Weights & Biases
        self._initialize_wandb()
    
    def _initialize_mlflow(self):
        """Initialize MLflow for experiment tracking"""
        try:
            mlflow.set_tracking_uri(os.getenv("MLFLOW_TRACKING_URI", "file:./mlruns"))
            mlflow.set_experiment("riches-reach-ai-models")
            logger.info("✅ MLflow initialized successfully")
        except Exception as e:
            logger.warning(f"⚠️ MLflow initialization failed: {e}")
    
    def _initialize_wandb(self):
        """Initialize Weights & Biases for experiment tracking"""
        try:
            wandb.init(project="riches-reach-ai", mode="disabled" if not os.getenv("WANDB_API_KEY") else "online")
            logger.info("✅ Weights & Biases initialized successfully")
        except Exception as e:
            logger.warning(f"⚠️ Weights & Biases initialization failed: {e}")
    
    async def train_financial_model(self, config: TrainingConfig) -> TrainingResult:
        """Train a specialized financial AI model"""
        try:
            job_id = f"financial_model_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            logger.info(f"Starting financial model training: {job_id}")
            
            # Load and prepare dataset
            dataset = await self._load_financial_dataset(config.dataset_path)
            
            # Initialize model and tokenizer
            model, tokenizer = self._initialize_model(config.model_name)
            
            # Prepare training data
            train_dataset, eval_dataset = self._prepare_training_data(dataset, tokenizer, config)
            
            # Set up training arguments
            training_args = self._setup_training_arguments(config)
            
            # Initialize trainer
            trainer = self._initialize_trainer(model, tokenizer, train_dataset, eval_dataset, training_args)
            
            # Start training
            start_time = datetime.now()
            training_result = trainer.train()
            training_time = (datetime.now() - start_time).total_seconds()
            
            # Evaluate model
            eval_results = trainer.evaluate()
            
            # Calculate metrics
            metrics = self._calculate_metrics(eval_results, training_time, model)
            
            # Save model
            model_path = await self._save_model(model, tokenizer, config.output_dir, job_id)
            
            # Create training result
            result = TrainingResult(
                model_id=job_id,
                model_name=config.model_name,
                training_config=config,
                metrics=metrics,
                training_logs=[],
                model_path=model_path,
                timestamp=datetime.now(),
                status="success"
            )
            
            # Store result
            self.training_jobs[job_id] = result
            
            # Log to MLflow
            await self._log_to_mlflow(result)
            
            logger.info(f"Financial model training completed: {job_id}")
            return result
            
        except Exception as e:
            logger.error(f"Error training financial model: {e}")
            # Create failed result
            result = TrainingResult(
                model_id=job_id if 'job_id' in locals() else "unknown",
                model_name=config.model_name,
                training_config=config,
                metrics=ModelMetrics(0, 0, 0, 0, float('inf'), float('inf'), 0, 0, 0, 0),
                training_logs=[],
                model_path="",
                timestamp=datetime.now(),
                status="failed"
            )
            self.training_jobs[result.model_id] = result
            raise
    
    async def train_trading_model(self, config: TrainingConfig) -> TrainingResult:
        """Train a specialized trading AI model"""
        try:
            job_id = f"trading_model_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            logger.info(f"Starting trading model training: {job_id}")
            
            # Load and prepare dataset
            dataset = await self._load_trading_dataset(config.dataset_path)
            
            # Initialize model and tokenizer
            model, tokenizer = self._initialize_model(config.model_name)
            
            # Prepare training data
            train_dataset, eval_dataset = self._prepare_trading_data(dataset, tokenizer, config)
            
            # Set up training arguments
            training_args = self._setup_training_arguments(config)
            
            # Initialize trainer
            trainer = self._initialize_trainer(model, tokenizer, train_dataset, eval_dataset, training_args)
            
            # Start training
            start_time = datetime.now()
            training_result = trainer.train()
            training_time = (datetime.now() - start_time).total_seconds()
            
            # Evaluate model
            eval_results = trainer.evaluate()
            
            # Calculate metrics
            metrics = self._calculate_metrics(eval_results, training_time, model)
            
            # Save model
            model_path = await self._save_model(model, tokenizer, config.output_dir, job_id)
            
            # Create training result
            result = TrainingResult(
                model_id=job_id,
                model_name=config.model_name,
                training_config=config,
                metrics=metrics,
                training_logs=[],
                model_path=model_path,
                timestamp=datetime.now(),
                status="success"
            )
            
            # Store result
            self.training_jobs[job_id] = result
            
            # Log to MLflow
            await self._log_to_mlflow(result)
            
            logger.info(f"Trading model training completed: {job_id}")
            return result
            
        except Exception as e:
            logger.error(f"Error training trading model: {e}")
            # Create failed result
            result = TrainingResult(
                model_id=job_id if 'job_id' in locals() else "unknown",
                model_name=config.model_name,
                training_config=config,
                metrics=ModelMetrics(0, 0, 0, 0, float('inf'), float('inf'), 0, 0, 0, 0),
                training_logs=[],
                model_path="",
                timestamp=datetime.now(),
                status="failed"
            )
            self.training_jobs[result.model_id] = result
            raise
    
    async def fine_tune_existing_model(self, base_model: str, config: TrainingConfig) -> TrainingResult:
        """Fine-tune an existing model with new data"""
        try:
            job_id = f"finetune_{base_model}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            logger.info(f"Starting model fine-tuning: {job_id}")
            
            # Load base model
            model, tokenizer = self._load_existing_model(base_model)
            
            # Load fine-tuning dataset
            dataset = await self._load_finetuning_dataset(config.dataset_path)
            
            # Prepare training data
            train_dataset, eval_dataset = self._prepare_training_data(dataset, tokenizer, config)
            
            # Set up training arguments for fine-tuning
            training_args = self._setup_finetuning_arguments(config)
            
            # Initialize trainer
            trainer = self._initialize_trainer(model, tokenizer, train_dataset, eval_dataset, training_args)
            
            # Start fine-tuning
            start_time = datetime.now()
            training_result = trainer.train()
            training_time = (datetime.now() - start_time).total_seconds()
            
            # Evaluate model
            eval_results = trainer.evaluate()
            
            # Calculate metrics
            metrics = self._calculate_metrics(eval_results, training_time, model)
            
            # Save fine-tuned model
            model_path = await self._save_model(model, tokenizer, config.output_dir, job_id)
            
            # Create training result
            result = TrainingResult(
                model_id=job_id,
                model_name=f"{base_model}_finetuned",
                training_config=config,
                metrics=metrics,
                training_logs=[],
                model_path=model_path,
                timestamp=datetime.now(),
                status="success"
            )
            
            # Store result
            self.training_jobs[job_id] = result
            
            # Log to MLflow
            await self._log_to_mlflow(result)
            
            logger.info(f"Model fine-tuning completed: {job_id}")
            return result
            
        except Exception as e:
            logger.error(f"Error fine-tuning model: {e}")
            # Create failed result
            result = TrainingResult(
                model_id=job_id if 'job_id' in locals() else "unknown",
                model_name=f"{base_model}_finetuned",
                training_config=config,
                metrics=ModelMetrics(0, 0, 0, 0, float('inf'), float('inf'), 0, 0, 0, 0),
                training_logs=[],
                model_path="",
                timestamp=datetime.now(),
                status="failed"
            )
            self.training_jobs[result.model_id] = result
            raise
    
    async def _load_financial_dataset(self, dataset_path: str) -> pd.DataFrame:
        """Load financial dataset for training"""
        try:
            if dataset_path.endswith('.csv'):
                dataset = pd.read_csv(dataset_path)
            elif dataset_path.endswith('.json'):
                dataset = pd.read_json(dataset_path)
            elif dataset_path.endswith('.parquet'):
                dataset = pd.read_parquet(dataset_path)
            else:
                raise ValueError(f"Unsupported dataset format: {dataset_path}")
            
            logger.info(f"Loaded financial dataset: {len(dataset)} samples")
            return dataset
            
        except Exception as e:
            logger.error(f"Error loading financial dataset: {e}")
            raise
    
    async def _load_trading_dataset(self, dataset_path: str) -> pd.DataFrame:
        """Load trading dataset for training"""
        try:
            if dataset_path.endswith('.csv'):
                dataset = pd.read_csv(dataset_path)
            elif dataset_path.endswith('.json'):
                dataset = pd.read_json(dataset_path)
            elif dataset_path.endswith('.parquet'):
                dataset = pd.read_parquet(dataset_path)
            else:
                raise ValueError(f"Unsupported dataset format: {dataset_path}")
            
            logger.info(f"Loaded trading dataset: {len(dataset)} samples")
            return dataset
            
        except Exception as e:
            logger.error(f"Error loading trading dataset: {e}")
            raise
    
    async def _load_finetuning_dataset(self, dataset_path: str) -> pd.DataFrame:
        """Load fine-tuning dataset"""
        try:
            if dataset_path.endswith('.csv'):
                dataset = pd.read_csv(dataset_path)
            elif dataset_path.endswith('.json'):
                dataset = pd.read_json(dataset_path)
            elif dataset_path.endswith('.parquet'):
                dataset = pd.read_parquet(dataset_path)
            else:
                raise ValueError(f"Unsupported dataset format: {dataset_path}")
            
            logger.info(f"Loaded fine-tuning dataset: {len(dataset)} samples")
            return dataset
            
        except Exception as e:
            logger.error(f"Error loading fine-tuning dataset: {e}")
            raise
    
    def _initialize_model(self, model_name: str) -> Tuple[Any, Any]:
        """Initialize model and tokenizer"""
        try:
            tokenizer = AutoTokenizer.from_pretrained(model_name)
            model = AutoModelForCausalLM.from_pretrained(model_name)
            
            # Add padding token if not present
            if tokenizer.pad_token is None:
                tokenizer.pad_token = tokenizer.eos_token
            
            logger.info(f"Initialized model: {model_name}")
            return model, tokenizer
            
        except Exception as e:
            logger.error(f"Error initializing model {model_name}: {e}")
            raise
    
    def _load_existing_model(self, model_path: str) -> Tuple[Any, Any]:
        """Load existing model and tokenizer"""
        try:
            tokenizer = AutoTokenizer.from_pretrained(model_path)
            model = AutoModelForCausalLM.from_pretrained(model_path)
            
            logger.info(f"Loaded existing model: {model_path}")
            return model, tokenizer
            
        except Exception as e:
            logger.error(f"Error loading existing model {model_path}: {e}")
            raise
    
    def _prepare_training_data(self, dataset: pd.DataFrame, tokenizer: Any, config: TrainingConfig) -> Tuple[Dataset, Dataset]:
        """Prepare training data"""
        try:
            # Convert to Hugging Face dataset format
            hf_dataset = Dataset.from_pandas(dataset)
            
            # Tokenize the dataset
            def tokenize_function(examples):
                return tokenizer(
                    examples["text"],
                    truncation=True,
                    padding=True,
                    max_length=config.max_length,
                    return_tensors="pt"
                )
            
            tokenized_dataset = hf_dataset.map(tokenize_function, batched=True)
            
            # Split into train and eval
            train_test_split = tokenized_dataset.train_test_split(test_size=0.1)
            train_dataset = train_test_split["train"]
            eval_dataset = train_test_split["test"]
            
            logger.info(f"Prepared training data: {len(train_dataset)} train, {len(eval_dataset)} eval")
            return train_dataset, eval_dataset
            
        except Exception as e:
            logger.error(f"Error preparing training data: {e}")
            raise
    
    def _prepare_trading_data(self, dataset: pd.DataFrame, tokenizer: Any, config: TrainingConfig) -> Tuple[Dataset, Dataset]:
        """Prepare trading-specific training data"""
        try:
            # Convert to Hugging Face dataset format
            hf_dataset = Dataset.from_pandas(dataset)
            
            # Tokenize the dataset
            def tokenize_function(examples):
                return tokenizer(
                    examples["text"],
                    truncation=True,
                    padding=True,
                    max_length=config.max_length,
                    return_tensors="pt"
                )
            
            tokenized_dataset = hf_dataset.map(tokenize_function, batched=True)
            
            # Split into train and eval
            train_test_split = tokenized_dataset.train_test_split(test_size=0.1)
            train_dataset = train_test_split["train"]
            eval_dataset = train_test_split["test"]
            
            logger.info(f"Prepared trading data: {len(train_dataset)} train, {len(eval_dataset)} eval")
            return train_dataset, eval_dataset
            
        except Exception as e:
            logger.error(f"Error preparing trading data: {e}")
            raise
    
    def _setup_training_arguments(self, config: TrainingConfig) -> TrainingArguments:
        """Set up training arguments"""
        return TrainingArguments(
            output_dir=config.output_dir,
            num_train_epochs=config.num_epochs,
            per_device_train_batch_size=config.batch_size,
            per_device_eval_batch_size=config.batch_size,
            warmup_steps=config.warmup_steps,
            learning_rate=config.learning_rate,
            gradient_accumulation_steps=config.gradient_accumulation_steps,
            save_steps=config.save_steps,
            eval_steps=config.eval_steps,
            logging_steps=config.logging_steps,
            evaluation_strategy=config.evaluation_strategy,
            save_strategy=config.save_strategy,
            load_best_model_at_end=config.load_best_model_at_end,
            metric_for_best_model=config.metric_for_best_model,
            greater_is_better=config.greater_is_better,
            report_to="wandb" if os.getenv("WANDB_API_KEY") else None,
            run_name=f"{config.model_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        )
    
    def _setup_finetuning_arguments(self, config: TrainingConfig) -> TrainingArguments:
        """Set up fine-tuning arguments"""
        return TrainingArguments(
            output_dir=config.output_dir,
            num_train_epochs=config.num_epochs,
            per_device_train_batch_size=config.batch_size,
            per_device_eval_batch_size=config.batch_size,
            warmup_steps=config.warmup_steps,
            learning_rate=config.learning_rate * 0.1,  # Lower learning rate for fine-tuning
            gradient_accumulation_steps=config.gradient_accumulation_steps,
            save_steps=config.save_steps,
            eval_steps=config.eval_steps,
            logging_steps=config.logging_steps,
            evaluation_strategy=config.evaluation_strategy,
            save_strategy=config.save_strategy,
            load_best_model_at_end=config.load_best_model_at_end,
            metric_for_best_model=config.metric_for_best_model,
            greater_is_better=config.greater_is_better,
            report_to="wandb" if os.getenv("WANDB_API_KEY") else None,
            run_name=f"finetune_{config.model_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        )
    
    def _initialize_trainer(self, model: Any, tokenizer: Any, train_dataset: Dataset, eval_dataset: Dataset, training_args: TrainingArguments) -> Trainer:
        """Initialize trainer"""
        try:
            data_collator = DataCollatorForLanguageModeling(
                tokenizer=tokenizer,
                mlm=False  # We're doing causal language modeling, not masked language modeling
            )
            
            trainer = Trainer(
                model=model,
                args=training_args,
                train_dataset=train_dataset,
                eval_dataset=eval_dataset,
                data_collator=data_collator,
                tokenizer=tokenizer
            )
            
            logger.info("Initialized trainer successfully")
            return trainer
            
        except Exception as e:
            logger.error(f"Error initializing trainer: {e}")
            raise
    
    def _calculate_metrics(self, eval_results: Dict[str, float], training_time: float, model: Any) -> ModelMetrics:
        """Calculate model metrics"""
        try:
            # Calculate model size
            model_size_mb = sum(p.numel() * p.element_size() for p in model.parameters()) / (1024 * 1024)
            parameters_count = sum(p.numel() for p in model.parameters())
            
            # Calculate perplexity from loss
            perplexity = np.exp(eval_results.get("eval_loss", float('inf')))
            
            # Calculate inference time (placeholder)
            inference_time = 0.1  # This would be measured in practice
            
            return ModelMetrics(
                accuracy=eval_results.get("eval_accuracy", 0.0),
                precision=eval_results.get("eval_precision", 0.0),
                recall=eval_results.get("eval_recall", 0.0),
                f1_score=eval_results.get("eval_f1", 0.0),
                loss=eval_results.get("eval_loss", float('inf')),
                perplexity=perplexity,
                training_time=training_time,
                inference_time=inference_time,
                model_size_mb=model_size_mb,
                parameters_count=parameters_count
            )
            
        except Exception as e:
            logger.error(f"Error calculating metrics: {e}")
            return ModelMetrics(0, 0, 0, 0, float('inf'), float('inf'), 0, 0, 0, 0)
    
    async def _save_model(self, model: Any, tokenizer: Any, output_dir: str, job_id: str) -> str:
        """Save trained model"""
        try:
            model_path = os.path.join(output_dir, job_id)
            os.makedirs(model_path, exist_ok=True)
            
            # Save model and tokenizer
            model.save_pretrained(model_path)
            tokenizer.save_pretrained(model_path)
            
            logger.info(f"Model saved to: {model_path}")
            return model_path
            
        except Exception as e:
            logger.error(f"Error saving model: {e}")
            raise
    
    async def _log_to_mlflow(self, result: TrainingResult):
        """Log training result to MLflow"""
        try:
            with mlflow.start_run(run_name=result.model_id):
                # Log parameters
                mlflow.log_params(asdict(result.training_config))
                
                # Log metrics
                mlflow.log_metrics(asdict(result.metrics))
                
                # Log model
                mlflow.transformers.log_model(
                    transformers_model={
                        "model": result.model_path,
                        "tokenizer": result.model_path
                    },
                    artifact_path="model",
                    registered_model_name=result.model_name
                )
                
                logger.info(f"Logged training result to MLflow: {result.model_id}")
                
        except Exception as e:
            logger.warning(f"Failed to log to MLflow: {e}")
    
    def get_training_jobs(self) -> Dict[str, TrainingResult]:
        """Get all training jobs"""
        return self.training_jobs
    
    def get_training_job(self, job_id: str) -> Optional[TrainingResult]:
        """Get specific training job"""
        return self.training_jobs.get(job_id)
    
    def get_best_model(self, metric: str = "f1_score") -> Optional[TrainingResult]:
        """Get best model based on metric"""
        if not self.training_jobs:
            return None
        
        best_job = None
        best_score = float('-inf')
        
        for job in self.training_jobs.values():
            if job.status == "success":
                score = getattr(job.metrics, metric, 0)
                if score > best_score:
                    best_score = score
                    best_job = job
        
        return best_job

# Global AI Model Trainer instance
ai_model_trainer = AIModelTrainer()
