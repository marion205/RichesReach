#!/usr/bin/env python3
"""
Complete Integration Example
============================
Shows how all performance optimizations work together in a FastAPI app.

This is a reference implementation showing best practices.
"""

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import time

# Performance Optimizations
from core.performance_integration import (
    initialize_performance_optimizations,
    add_performance_middleware
)

# Core performance components
from core.onnx_runtime import get_onnx_session, run_onnx_inference
from core.batcher import MicroBatcher
from core.cache_wrapper import get_feature_cache
from core.llm_cache import get_llm_cache
from core.feast_integration import get_feast_client
from core.metrics_exporter import get_metrics_exporter
from core.performance_slo import get_slo_monitor

# Create FastAPI app
app = FastAPI(title="RichesReach Performance Demo")

# Initialize all performance optimizations
initialize_performance_optimizations(app)
add_performance_middleware(app)

# Initialize components
feature_cache = get_feature_cache()
llm_cache = get_llm_cache()
feast_client = get_feast_client()
metrics_exporter = get_metrics_exporter()
slo_monitor = get_slo_monitor()


# Example: ML Inference with ONNX + Caching + Batching
def ml_model_inference(features):
    """Example ML inference function."""
    # In production, this would use ONNX Runtime
    return {"prediction": 0.85, "confidence": 0.92}

# Create batcher
ml_batcher = MicroBatcher(
    runner=lambda batch: [ml_model_inference(f) for f in batch],
    max_wait_ms=5,
    max_batch_size=64
)


@app.get("/api/ml/predict")
async def ml_predict_endpoint(features: dict):
    """
    ML prediction endpoint using all optimizations:
    - Feature caching (Redis)
    - Micro-batching
    - ONNX Runtime (if available)
    """
    # Use cached prediction
    result = feature_cache.cached_predict(
        model="regime_predictor",
        features=features,
        infer_fn=lambda f: ml_model_inference(f),
        ttl=300
    )
    
    # Record ML latency
    start = time.perf_counter()
    # ... inference happens ...
    latency_ms = (time.perf_counter() - start) * 1000
    metrics_exporter.record_ml_latency("regime_predictor", latency_ms)
    
    return result


@app.get("/api/ai/ask")
async def ai_ask_endpoint(prompt: str):
    """
    AI endpoint using LLM caching.
    """
    def call_llm(model, prompt):
        # Your LLM call here
        return f"Response to: {prompt}"
    
    # Use cached LLM response
    response = llm_cache.cached_call(
        model="gpt-4o-mini",
        payload={"messages": [{"role": "user", "content": prompt}]},
        caller=call_llm,
        ttl=21600
    )
    
    return {"response": response}


@app.get("/api/features/{user_id}")
async def get_features_endpoint(user_id: int):
    """
    Get features from Feast feature store.
    """
    # Get portfolio features
    portfolio_features = feast_client.get_portfolio_features(user_id)
    
    return portfolio_features


@app.get("/api/slo/stats")
async def slo_stats_endpoint():
    """
    Get current SLO statistics.
    """
    stats = slo_monitor.get_stats()
    checks = slo_monitor.check_slo_compliance()
    
    return {
        "stats": stats,
        "slo_compliance": checks,
        "compliant": all(checks.values())
    }


@app.get("/health")
async def health_check():
    """Health check with performance metrics."""
    stats = slo_monitor.get_stats()
    
    return {
        "status": "healthy",
        "performance": {
            "api_p50_ms": stats.get("api_p50_ms"),
            "api_p95_ms": stats.get("api_p95_ms"),
            "success_rate": stats.get("success_rate"),
            "slo_compliant": stats.get("slo_compliant", False)
        }
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

