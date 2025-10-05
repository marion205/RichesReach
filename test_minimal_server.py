#!/usr/bin/env python3
"""
Minimal test server to isolate the issue
"""

from fastapi import FastAPI
from datetime import datetime
import os

app = FastAPI()

BUILD_ID = os.getenv("BUILD_ID", "test-build")

@app.get("/")
async def root():
    return {"message": "Test Server", "status": "running", "build": BUILD_ID}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.now().isoformat(), "build": BUILD_ID}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8004)
