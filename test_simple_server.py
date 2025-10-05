#!/usr/bin/env python3
"""
Simple test server without complex middleware
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
    return {"message": "RichesReach Test Server", "status": "running", "build": BUILD_ID}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.now().isoformat(), "build": BUILD_ID}

@app.get("/health/detailed/")
async def detailed_health_check():
    return {
        "ok": True, 
        "mode": "test",
        "timestamp": datetime.now().isoformat(),
        "build": BUILD_ID
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8006)
