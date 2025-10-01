#!/usr/bin/env python3
"""
AWS Production Server - Simple FastAPI server for RichesReach
This is a minimal server that runs on AWS ECS with all the essential endpoints.
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import os
import json
from typing import Dict, Any

# Create FastAPI app
app = FastAPI(
    title="RichesReach API",
    description="Production API for RichesReach trading platform",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "RichesReach API",
        "status": "operational",
        "version": "1.0.0",
        "environment": os.getenv("ENVIRONMENT", "production")
    }

@app.get("/health/")
async def health():
    """Health check endpoint"""
    return {
        "ok": True,
        "mode": "production",
        "env": os.getenv("ENVIRONMENT", "unknown"),
        "status": "healthy"
    }

@app.get("/live/")
async def live():
    """Liveness check endpoint"""
    return {
        "status": "alive",
        "service": "richesreach",
        "timestamp": "2025-09-30T21:56:00Z"
    }

@app.post("/api/ai-options/recommendations")
async def ai_options_recommendations(data: Dict[str, Any]):
    """AI Options Recommendations endpoint"""
    try:
        symbol = data.get("symbol", "AAPL")
        time_horizon = data.get("time_horizon", 30)
        portfolio_value = data.get("portfolio_value", 10000)
        risk_tolerance = data.get("user_risk_tolerance", "medium")
        
        # Mock recommendations
        recommendations = [
            {
                "strategy": "Covered Call",
                "symbol": symbol,
                "expirationDays": time_horizon,
                "strike": f"${150.0 * 1.02:.0f}",
                "rationale": "Income generation with upside participation"
            },
            {
                "strategy": "Cash-Secured Put",
                "symbol": symbol,
                "expirationDays": time_horizon,
                "strike": f"${150.0 * 0.98:.0f}",
                "rationale": "Income with potential stock acquisition"
            }
        ]
        
        return {
            "ok": True,
            "symbol": symbol,
            "current_price": 150.0,
            "recommendations": recommendations,
            "api_keys_configured": bool(os.getenv("POLYGON_API_KEY")),
            "data_providers": {
                "quote": "mock",
                "options": "mock"
            },
            "market_data_available": False
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/ai-status")
async def ai_status():
    """AI status endpoint for feature flags"""
    return {
        "ai_enabled": os.getenv("USE_OPENAI", "false").lower() == "true",
        "model": os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
        "fallback_enabled": os.getenv("OPENAI_ENABLE_FALLBACK", "true").lower() == "true",
        "environment": "production",
        "status": "operational"
    }

if __name__ == "__main__":
    # Get port from environment or default to 8000
    port = int(os.getenv("PORT", 8000))
    
    # Run the server
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=port,
        log_level="info"
    )
