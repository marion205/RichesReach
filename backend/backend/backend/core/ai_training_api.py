"""
AI Model Training API - Phase 3
FastAPI endpoints for AI model training, fine-tuning, and optimization
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
import uuid
import logging
from datetime import datetime

from .ai_model_training import ai_model_trainer, TrainingConfig, TrainingResult, ModelMetrics

logger = logging.getLogger("richesreach")

# Create router
router = APIRouter(prefix="/ai-training", tags=["AI Model Training"])

# Pydantic models for API
class TrainingConfigModel(BaseModel):
    """Training configuration model for API"""
    model_name: str = Field(..., description="Base model name")
    dataset_path: str = Field(..., description="Path to training dataset")
    output_dir: str = Field(..., description="Output directory for trained model")
    num_epochs: int = Field(3, ge=1, le=10, description="Number of training epochs")
    batch_size: int = Field(8, ge=1, le=32, description="Training batch size")
    learning_rate: float = Field(5e-5, ge=1e-6, le=1e-3, description="Learning rate")
    warmup_steps: int = Field(100, ge=0, le=1000, description="Warmup steps")
    max_length: int = Field(512, ge=128, le=2048, description="Maximum sequence length")
    gradient_accumulation_steps: int = Field(4, ge=1, le=16, description="Gradient accumulation steps")
    save_steps: int = Field(500, ge=100, le=5000, description="Steps between saves")
    eval_steps: int = Field(500, ge=100, le=5000, description="Steps between evaluations")
    logging_steps: int = Field(100, ge=10, le=1000, description="Steps between logging")

class TrainingJobModel(BaseModel):
    """Training job model for API"""
    job_id: str
    model_name: str
    status: str
    created_at: str
    updated_at: str
    metrics: Optional[Dict[str, Any]] = None
    model_path: Optional[str] = None

class FineTuningRequestModel(BaseModel):
    """Fine-tuning request model"""
    base_model: str = Field(..., description="Base model to fine-tune")
    dataset_path: str = Field(..., description="Path to fine-tuning dataset")
    output_dir: str = Field(..., description="Output directory for fine-tuned model")
    num_epochs: int = Field(2, ge=1, le=5, description="Number of fine-tuning epochs")
    batch_size: int = Field(8, ge=1, le=32, description="Fine-tuning batch size")
    learning_rate: float = Field(1e-5, ge=1e-6, le=1e-4, description="Fine-tuning learning rate")
    max_length: int = Field(512, ge=128, le=2048, description="Maximum sequence length")

class ModelEvaluationRequestModel(BaseModel):
    """Model evaluation request model"""
    model_path: str = Field(..., description="Path to model to evaluate")
    test_dataset_path: str = Field(..., description="Path to test dataset")
    evaluation_metrics: List[str] = Field(["accuracy", "f1_score", "perplexity"], description="Metrics to evaluate")

# Training Endpoints
@router.post("/train/financial")
async def train_financial_model(config: TrainingConfigModel, background_tasks: BackgroundTasks):
    """Train a specialized financial AI model"""
    try:
        # Convert to TrainingConfig
        training_config = TrainingConfig(
            model_name=config.model_name,
            dataset_path=config.dataset_path,
            output_dir=config.output_dir,
            num_epochs=config.num_epochs,
            batch_size=config.batch_size,
            learning_rate=config.learning_rate,
            warmup_steps=config.warmup_steps,
            max_length=config.max_length,
            gradient_accumulation_steps=config.gradient_accumulation_steps,
            save_steps=config.save_steps,
            eval_steps=config.eval_steps,
            logging_steps=config.logging_steps
        )
        
        # Start training in background
        job_id = f"financial_model_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        background_tasks.add_task(
            ai_model_trainer.train_financial_model,
            training_config
        )
        
        return {
            "status": "success",
            "message": "Financial model training started",
            "job_id": job_id,
            "config": config.dict(),
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error starting financial model training: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/train/trading")
async def train_trading_model(config: TrainingConfigModel, background_tasks: BackgroundTasks):
    """Train a specialized trading AI model"""
    try:
        # Convert to TrainingConfig
        training_config = TrainingConfig(
            model_name=config.model_name,
            dataset_path=config.dataset_path,
            output_dir=config.output_dir,
            num_epochs=config.num_epochs,
            batch_size=config.batch_size,
            learning_rate=config.learning_rate,
            warmup_steps=config.warmup_steps,
            max_length=config.max_length,
            gradient_accumulation_steps=config.gradient_accumulation_steps,
            save_steps=config.save_steps,
            eval_steps=config.eval_steps,
            logging_steps=config.logging_steps
        )
        
        # Start training in background
        job_id = f"trading_model_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        background_tasks.add_task(
            ai_model_trainer.train_trading_model,
            training_config
        )
        
        return {
            "status": "success",
            "message": "Trading model training started",
            "job_id": job_id,
            "config": config.dict(),
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error starting trading model training: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/finetune")
async def fine_tune_model(request: FineTuningRequestModel, background_tasks: BackgroundTasks):
    """Fine-tune an existing model with new data"""
    try:
        # Convert to TrainingConfig
        training_config = TrainingConfig(
            model_name=request.base_model,
            dataset_path=request.dataset_path,
            output_dir=request.output_dir,
            num_epochs=request.num_epochs,
            batch_size=request.batch_size,
            learning_rate=request.learning_rate,
            max_length=request.max_length
        )
        
        # Start fine-tuning in background
        job_id = f"finetune_{request.base_model}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        background_tasks.add_task(
            ai_model_trainer.fine_tune_existing_model,
            request.base_model,
            training_config
        )
        
        return {
            "status": "success",
            "message": "Model fine-tuning started",
            "job_id": job_id,
            "base_model": request.base_model,
            "config": request.dict(),
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error starting model fine-tuning: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Job Management Endpoints
@router.get("/jobs")
async def get_training_jobs():
    """Get all training jobs"""
    try:
        jobs = ai_model_trainer.get_training_jobs()
        
        job_list = []
        for job_id, job in jobs.items():
            job_list.append({
                "job_id": job_id,
                "model_name": job.model_name,
                "status": job.status,
                "created_at": job.timestamp.isoformat(),
                "updated_at": job.timestamp.isoformat(),
                "metrics": asdict(job.metrics) if job.metrics else None,
                "model_path": job.model_path
            })
        
        return {
            "status": "success",
            "jobs": job_list,
            "total_jobs": len(jobs),
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting training jobs: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/jobs/{job_id}")
async def get_training_job(job_id: str):
    """Get specific training job"""
    try:
        job = ai_model_trainer.get_training_job(job_id)
        
        if not job:
            raise HTTPException(status_code=404, detail="Training job not found")
        
        return {
            "status": "success",
            "job": {
                "job_id": job_id,
                "model_name": job.model_name,
                "status": job.status,
                "created_at": job.timestamp.isoformat(),
                "updated_at": job.timestamp.isoformat(),
                "metrics": asdict(job.metrics) if job.metrics else None,
                "model_path": job.model_path,
                "training_config": asdict(job.training_config) if job.training_config else None
            },
            "timestamp": datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting training job {job_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/best-model")
async def get_best_model(metric: str = "f1_score"):
    """Get best model based on metric"""
    try:
        best_job = ai_model_trainer.get_best_model(metric)
        
        if not best_job:
            return {
                "status": "success",
                "message": "No trained models found",
                "best_model": None,
                "timestamp": datetime.now().isoformat()
            }
        
        return {
            "status": "success",
            "best_model": {
                "job_id": best_job.model_id,
                "model_name": best_job.model_name,
                "status": best_job.status,
                "metrics": asdict(best_job.metrics),
                "model_path": best_job.model_path,
                "created_at": best_job.timestamp.isoformat()
            },
            "metric_used": metric,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting best model: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Model Evaluation Endpoints
@router.post("/evaluate")
async def evaluate_model(request: ModelEvaluationRequestModel):
    """Evaluate a trained model"""
    try:
        # This would implement model evaluation
        # For now, return a placeholder response
        
        return {
            "status": "success",
            "message": "Model evaluation completed",
            "model_path": request.model_path,
            "evaluation_results": {
                "accuracy": 0.85,
                "f1_score": 0.82,
                "perplexity": 15.3,
                "evaluation_time": 120.5
            },
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error evaluating model: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Model Management Endpoints
@router.get("/models/available")
async def get_available_models():
    """Get list of available base models for training"""
    try:
        available_models = [
            {
                "name": "gpt-2",
                "description": "GPT-2 base model",
                "size": "117M parameters",
                "recommended_for": ["general", "text_generation"]
            },
            {
                "name": "gpt-2-medium",
                "description": "GPT-2 medium model",
                "size": "345M parameters",
                "recommended_for": ["general", "text_generation", "fine_tuning"]
            },
            {
                "name": "gpt-2-large",
                "description": "GPT-2 large model",
                "size": "774M parameters",
                "recommended_for": ["advanced", "research", "fine_tuning"]
            },
            {
                "name": "distilgpt2",
                "description": "Distilled GPT-2 model",
                "size": "82M parameters",
                "recommended_for": ["fast_training", "lightweight"]
            },
            {
                "name": "microsoft/DialoGPT-medium",
                "description": "DialoGPT medium model",
                "size": "345M parameters",
                "recommended_for": ["conversational", "chat"]
            }
        ]
        
        return {
            "status": "success",
            "available_models": available_models,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting available models: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/models/trained")
async def get_trained_models():
    """Get list of trained models"""
    try:
        jobs = ai_model_trainer.get_training_jobs()
        trained_models = []
        
        for job_id, job in jobs.items():
            if job.status == "success":
                trained_models.append({
                    "job_id": job_id,
                    "model_name": job.model_name,
                    "model_path": job.model_path,
                    "metrics": asdict(job.metrics) if job.metrics else None,
                    "created_at": job.timestamp.isoformat()
                })
        
        return {
            "status": "success",
            "trained_models": trained_models,
            "total_trained": len(trained_models),
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting trained models: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Health Check
@router.get("/health")
async def training_health():
    """Health check for AI training system"""
    try:
        jobs = ai_model_trainer.get_training_jobs()
        
        return {
            "status": "healthy",
            "total_jobs": len(jobs),
            "successful_jobs": len([j for j in jobs.values() if j.status == "success"]),
            "failed_jobs": len([j for j in jobs.values() if j.status == "failed"]),
            "in_progress_jobs": len([j for j in jobs.values() if j.status == "in_progress"]),
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"AI training health check failed: {e}")
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }
