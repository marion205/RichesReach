#!/usr/bin/env python3
# Health Check Endpoint for Production
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
import psycopg2
import redis
import boto3
import os
import time
app = FastAPI(title="RichesReach AI Health Check")
@app.get("/health")
async def health_check():
"""Comprehensive health check for production"""
health_status = {
"status": "healthy",
"timestamp": time.time(),
"checks": {}
}
# Database health check
try:
conn = psycopg2.connect(os.getenv("DATABASE_URL"))
conn.close()
health_status["checks"]["database"] = "healthy"
except Exception as e:
health_status["checks"]["database"] = f"unhealthy: {str(e)}"
health_status["status"] = "unhealthy"
# Redis health check
try:
r = redis.from_url(os.getenv("REDIS_URL"))
r.ping()
health_status["checks"]["redis"] = "healthy"
except Exception as e:
health_status["checks"]["redis"] = f"unhealthy: {str(e)}"
health_status["status"] = "unhealthy"
# AWS services health check
try:
s3 = boto3.client('s3')
s3.list_buckets()
health_status["checks"]["aws_s3"] = "healthy"
except Exception as e:
health_status["checks"]["aws_s3"] = f"unhealthy: {str(e)}"
health_status["status"] = "unhealthy"
# ML models health check
try:
models_dir = "/app/models"
if os.path.exists(models_dir):
model_files = [f for f in os.listdir(models_dir) if f.endswith(('.pkl', '.h5'))]
health_status["checks"]["ml_models"] = f"healthy: {len(model_files)} models loaded"
else:
health_status["checks"]["ml_models"] = "unhealthy: models directory not found"
health_status["status"] = "unhealthy"
except Exception as e:
health_status["checks"]["ml_models"] = f"unhealthy: {str(e)}"
health_status["status"] = "unhealthy"
# Return appropriate HTTP status
if health_status["status"] == "healthy":
return JSONResponse(content=health_status, status_code=200)
else:
return JSONResponse(content=health_status, status_code=503)
@app.get("/metrics")
async def metrics():
"""Prometheus metrics endpoint"""
# This would include custom metrics for ML models, API performance, etc.
return {"message": "Metrics endpoint - implement Prometheus metrics here"}
if __name__ == "__main__":
import uvicorn
uvicorn.run(app, host="0.0.0.0", port=8000)
