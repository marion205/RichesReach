#!/usr/bin/env python3
"""
RichesReach AI - FastAPI Application
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import os
import time
from datetime import datetime
# Create FastAPI app
app = FastAPI(
title="RichesReach AI",
description="AI-powered financial platform",
version="1.0.0",
docs_url="/docs",
redoc_url="/redoc"
)
# Add CORS middleware
app.add_middleware(
CORSMiddleware,
allow_origins=["*"],
allow_credentials=True,
allow_methods=["*"],
allow_headers=["*"],
)
# Startup event
@app.on_event("startup")
async def startup_event():
print(f" RichesReach AI starting up at {datetime.now()}")
print(" Application is ready!")
# Root endpoint
@app.get("/")
async def root():
return {
"message": "Welcome to RichesReach AI!",
"status": "healthy",
"version": "1.0.0",
"timestamp": datetime.now().isoformat()
}
# Health check endpoint
@app.get("/health")
async def health():
return {
"status": "healthy",
"service": "RichesReach AI",
"timestamp": datetime.now().isoformat(),
"uptime": "running"
}
# API test endpoint
@app.get("/api/test")
async def test():
return {
"message": "API is working perfectly!",
"timestamp": datetime.now().isoformat(),
"features": [
"AI-powered recommendations",
"Real-time portfolio tracking",
"Financial insights",
"Risk assessment"
]
}
# Status endpoint
@app.get("/api/status")
async def status():
return {
"service": "RichesReach AI",
"status": "operational",
"version": "1.0.0",
"environment": os.environ.get("ENVIRONMENT", "production"),
"timestamp": datetime.now().isoformat()
}
if __name__ == "__main__":
port = int(os.environ.get("PORT", 8000))
host = os.environ.get("HOST", "0.0.0.0")
print(f" Starting server on {host}:{port}")
uvicorn.run(
app, 
host=host, 
port=port,
log_level="info",
access_log=True
)
