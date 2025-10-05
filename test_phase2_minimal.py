#!/usr/bin/env python3
"""
Minimal Phase 2 test server
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime
import os

app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

BUILD_ID = datetime.now().isoformat(timespec="seconds")

@app.get("/")
async def root():
    return {"message": "RichesReach Phase 2 Test Server", "status": "running", "build": BUILD_ID}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.now().isoformat(), "build": BUILD_ID}

@app.get("/health/detailed/")
async def detailed_health_check():
    return {
        "ok": True, 
        "mode": "test",
        "timestamp": datetime.now().isoformat(),
        "build": BUILD_ID,
        "streaming_pipeline": {"available": True, "producer_initialized": False, "consumer_initialized": False},
        "ml_versioning": {"available": True, "model_manager_initialized": False, "ab_testing_initialized": False},
        "aws_batch": {"available": True, "batch_manager_initialized": False}
    }

@app.get("/metrics/")
async def metrics_endpoint():
    return {"message": "Prometheus metrics endpoint", "status": "available"}

@app.get("/phase2/streaming/status/")
async def streaming_status():
    return {
        "status": "success",
        "streaming_available": True,
        "producer_initialized": False,
        "consumer_initialized": False
    }

@app.get("/phase2/ml/models/")
async def list_ml_models():
    return {
        "status": "success",
        "models": [
            {"model_id": "xgboost_v1", "version": "1.0", "status": "active"},
            {"model_id": "random_forest_v1", "version": "1.0", "status": "active"}
        ]
    }

@app.get("/phase2/batch/status/")
async def batch_status():
    return {
        "status": "success",
        "infrastructure": {
            "compute_environment": {"exists": True, "status": "ENABLED"},
            "job_queue": {"exists": True, "status": "ENABLED"},
            "job_definition": {"exists": True, "status": "ACTIVE"},
            "s3_bucket": {"exists": True}
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8007)
