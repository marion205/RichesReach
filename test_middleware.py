#!/usr/bin/env python3
"""
Test middleware issue
"""

from fastapi import FastAPI, Request
import uuid
from time import perf_counter

app = FastAPI()

@app.middleware("http")
async def test_middleware(request: Request, call_next):
    req_id = str(uuid.uuid4())
    t0 = perf_counter()
    
    try:
        response = await call_next(request)
        print(f"Request {req_id} completed in {perf_counter() - t0:.3f}s")
        return response
    except Exception as e:
        print(f"Request {req_id} failed: {e}")
        raise

@app.get("/")
async def root():
    return {"message": "Test with middleware"}

@app.get("/health")
async def health():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8005)
