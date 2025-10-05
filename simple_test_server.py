#!/usr/bin/env python3
"""
Simple test server for AI Scans and Options Copilot
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import uvicorn
import asyncio
import random
from datetime import datetime

app = FastAPI(title="RichesReach Test Server")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mock data
MOCK_SCANS = [
    {
        "id": "scan_1",
        "name": "Momentum Scanner",
        "description": "Identifies stocks with strong momentum signals",
        "category": "MOMENTUM",
        "riskLevel": "MEDIUM",
        "timeHorizon": "SHORT_TERM",
        "isActive": True,
        "lastRun": "2024-01-15T10:30:00Z",
        "results": [
            {
                "id": "result_1",
                "symbol": "AAPL",
                "currentPrice": 175.50,
                "changePercent": 2.3,
                "confidence": 0.85
            },
            {
                "id": "result_2", 
                "symbol": "MSFT",
                "currentPrice": 378.90,
                "changePercent": 1.8,
                "confidence": 0.78
            }
        ],
        "playbook": {
            "id": "playbook_1",
            "name": "Momentum Strategy",
            "performance": {
                "successRate": 0.75,
                "averageReturn": 0.12
            }
        }
    }
]

MOCK_PLAYBOOKS = [
    {
        "id": "playbook_1",
        "name": "Momentum Strategy",
        "author": "AI System",
        "riskLevel": "MEDIUM",
        "performance": {
            "successRate": 0.75,
            "averageReturn": 0.12
        },
        "tags": ["momentum", "short-term", "technical"]
    },
    {
        "id": "playbook_2", 
        "name": "Value Hunter",
        "author": "AI System",
        "riskLevel": "LOW",
        "performance": {
            "successRate": 0.68,
            "averageReturn": 0.08
        },
        "tags": ["value", "long-term", "fundamental"]
    }
]

MOCK_OPTIONS_RECOMMENDATIONS = [
    {
        "strategy_name": "AAPL Covered Call Strategy",
        "strategy_type": "income",
        "confidence_score": 0.85,
        "symbol": "AAPL",
        "current_price": 175.50,
        "options": [
            {
                "type": "call",
                "action": "sell",
                "strike": 180,
                "expiration": "2024-02-16",
                "premium": 2.50,
                "quantity": 100
            }
        ],
        "analytics": {
            "max_profit": 2.50,
            "max_loss": 0.05,
            "probability_of_profit": 0.75,
            "expected_return": 0.08,
            "breakeven": 175.50
        },
        "reasoning": {
            "market_outlook": "AAPL shows strong bullish momentum with support at $170",
            "strategy_rationale": "Selling covered calls generates income while maintaining upside potential",
            "risk_factors": ["Earnings volatility", "Market correction risk"],
            "key_benefits": ["Income generation", "Reduced cost basis", "Limited downside"]
        },
        "risk_score": 3,
        "days_to_expiration": 30,
        "created_at": "2024-01-15T10:30:00Z"
    },
    {
        "strategy_name": "AAPL Bull Put Spread",
        "strategy_type": "speculation",
        "confidence_score": 0.72,
        "symbol": "AAPL",
        "current_price": 175.50,
        "options": [
            {
                "type": "put",
                "action": "sell",
                "strike": 170,
                "expiration": "2024-02-16",
                "premium": 1.20,
                "quantity": 100
            },
            {
                "type": "put",
                "action": "buy",
                "strike": 165,
                "expiration": "2024-02-16",
                "premium": 0.80,
                "quantity": 100
            }
        ],
        "analytics": {
            "max_profit": 0.40,
            "max_loss": 4.60,
            "probability_of_profit": 0.65,
            "expected_return": 0.12,
            "breakeven": 169.60
        },
        "reasoning": {
            "market_outlook": "AAPL maintains strong support levels with bullish technical indicators",
            "strategy_rationale": "Bull put spread profits from time decay and sideways to bullish movement",
            "risk_factors": ["Gap down risk", "Volatility expansion"],
            "key_benefits": ["High probability of profit", "Defined risk", "Time decay advantage"]
        },
        "risk_score": 6,
        "days_to_expiration": 30,
        "created_at": "2024-01-15T10:30:00Z"
    }
]

# Health check
@app.get("/health/")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

# AI Scans endpoints
@app.get("/api/ai-scans/")
async def get_ai_scans():
    return MOCK_SCANS

@app.get("/api/ai-scans/{scan_id}")
async def get_ai_scan(scan_id: str):
    for scan in MOCK_SCANS:
        if scan["id"] == scan_id:
            return scan
    raise HTTPException(status_code=404, detail="Scan not found")

@app.post("/api/ai-scans/{scan_id}/run")
async def run_scan(scan_id: str):
    # Simulate running a scan
    await asyncio.sleep(1)
    return {"status": "completed", "scan_id": scan_id, "results_count": 2}

@app.get("/api/ai-scans/playbooks/")
async def get_playbooks():
    return MOCK_PLAYBOOKS

@app.get("/api/ai-scans/playbooks/{playbook_id}")
async def get_playbook(playbook_id: str):
    for playbook in MOCK_PLAYBOOKS:
        if playbook["id"] == playbook_id:
            return playbook
    raise HTTPException(status_code=404, detail="Playbook not found")

# Options Copilot endpoints (removed old format)

# AI Options endpoints (for mobile app compatibility)
@app.post("/api/ai-options/recommendations")
async def get_ai_options_recommendations(request: Dict[str, Any]):
    # Simulate processing time
    await asyncio.sleep(0.5)
    return {
        "recommendations": MOCK_OPTIONS_RECOMMENDATIONS,
        "symbol": request.get("symbol", "AAPL"),
        "risk_tolerance": request.get("risk_tolerance", "medium"),
        "market_analysis": {
            "current_price": 175.50,
            "volatility": 0.25,
            "trend": "bullish"
        }
    }

@app.get("/api/options/copilot/chain")
async def get_options_chain(symbol: str = "AAPL"):
    return {
        "symbol": symbol,
        "underlyingPrice": 175.50,
        "calls": [
            {"strike": 175, "bid": 2.50, "ask": 2.60, "volume": 1000, "impliedVolatility": 0.25, "delta": 0.50, "gamma": 0.02},
            {"strike": 180, "bid": 1.20, "ask": 1.30, "volume": 800, "impliedVolatility": 0.24, "delta": 0.35, "gamma": 0.02}
        ],
        "puts": [
            {"strike": 170, "bid": 1.80, "ask": 1.90, "volume": 1200, "impliedVolatility": 0.26, "delta": -0.30, "gamma": 0.02},
            {"strike": 165, "bid": 0.90, "ask": 1.00, "volume": 600, "impliedVolatility": 0.27, "delta": -0.20, "gamma": 0.02}
        ]
    }

# Options chain endpoint (for mobile app compatibility)
@app.get("/api/options/chain")
async def get_options_chain_compat(symbol: str = "AAPL"):
    return {
        "symbol": symbol,
        "underlyingPrice": 175.50,
        "calls": [
            {"strike": 175, "bid": 2.50, "ask": 2.60, "volume": 1000, "impliedVolatility": 0.25, "delta": 0.50, "gamma": 0.02},
            {"strike": 180, "bid": 1.20, "ask": 1.30, "volume": 800, "impliedVolatility": 0.24, "delta": 0.35, "gamma": 0.02}
        ],
        "puts": [
            {"strike": 170, "bid": 1.80, "ask": 1.90, "volume": 1200, "impliedVolatility": 0.26, "delta": -0.30, "gamma": 0.02},
            {"strike": 165, "bid": 0.90, "ask": 1.00, "volume": 600, "impliedVolatility": 0.27, "delta": -0.20, "gamma": 0.02}
        ]
    }

# Options Copilot recommendations endpoint (proper structure)
@app.post("/api/options/copilot/recommendations")
async def get_copilot_recommendations(request: Dict[str, Any]):
    symbol = request.get("symbol", "AAPL")
    now = datetime.now().isoformat()
    
    return {
        "recommendedStrategies": [
            {
                "id": "bull_call_spread",
                "name": "Bull Call Spread",
                "symbol": symbol,
                "type": "bullish",
                "confidence": 0.74,
                "expectedPayoff": {
                    "maxProfit": 240,
                    "maxLoss": 160,
                    "breakeven": 198.5
                },
                "reasoning": "AI detected bullish momentum with moderate volatility",
                "riskMetrics": {
                    "delta": 0.42,
                    "theta": -0.25,
                    "vega": 0.15
                },
                "createdAt": now
            },
            {
                "id": "iron_condor",
                "name": "Iron Condor",
                "symbol": symbol,
                "type": "neutral",
                "confidence": 0.68,
                "expectedPayoff": {
                    "maxProfit": 125,
                    "maxLoss": 250,
                    "breakeven": [192, 208]
                },
                "reasoning": "Stable range pattern detected from volatility compression",
                "riskMetrics": {
                    "delta": 0.05,
                    "theta": 0.32,
                    "vega": -0.18
                },
                "createdAt": now
            },
            {
                "id": "covered_call_income",
                "name": "Covered Call Income",
                "symbol": symbol,
                "type": "income",
                "confidence": 0.82,
                "expectedPayoff": {
                    "maxProfit": 250,
                    "maxLoss": 50,
                    "breakeven": 175.50
                },
                "reasoning": "Strong bullish momentum with high probability of profit",
                "riskMetrics": {
                    "delta": 0.45,
                    "theta": -0.15,
                    "vega": 0.12
                },
                "createdAt": now
            }
        ],
        "riskAssessment": {
            "portfolioExposure": 0.12,
            "maxDrawdown": 0.08,
            "var99": 0.045
        },
        "marketAnalysis": {
            "volatilityIndex": 17.2,
            "trend": "upward",
            "sectorLeaders": ["AAPL", "NVDA", "MSFT"]
        }
    }

@app.get("/api/options/copilot/health")
async def options_health():
    return {"status": "healthy", "service": "options_copilot"}

# Additional endpoints for Options Copilot
@app.get("/api/options/chain")
async def get_options_chain_copilot(symbol: str = "AAPL", expiration: str = None):
    """Options chain endpoint for Options Copilot service"""
    return {
        "symbol": symbol,
        "underlyingPrice": 175.50,
        "expiration": expiration or "2024-02-16",
        "calls": [
            {"strike": 175, "bid": 2.50, "ask": 2.60, "volume": 1000, "impliedVolatility": 0.25, "delta": 0.50, "gamma": 0.02},
            {"strike": 180, "bid": 1.20, "ask": 1.30, "volume": 800, "impliedVolatility": 0.24, "delta": 0.35, "gamma": 0.02},
            {"strike": 185, "bid": 0.60, "ask": 0.70, "volume": 600, "impliedVolatility": 0.23, "delta": 0.25, "gamma": 0.02}
        ],
        "puts": [
            {"strike": 170, "bid": 1.80, "ask": 1.90, "volume": 1200, "impliedVolatility": 0.26, "delta": -0.30, "gamma": 0.02},
            {"strike": 165, "bid": 0.90, "ask": 1.00, "volume": 600, "impliedVolatility": 0.27, "delta": -0.20, "gamma": 0.02},
            {"strike": 160, "bid": 0.40, "ask": 0.50, "volume": 400, "impliedVolatility": 0.28, "delta": -0.15, "gamma": 0.02}
        ]
    }

# GraphQL endpoint (simple)
@app.post("/graphql/")
async def graphql_endpoint(request: Dict[str, Any]):
    query = request.get("query", "")
    
    if "aiScans" in query:
        return {"data": {"aiScans": MOCK_SCANS}}
    elif "playbooks" in query:
        return {"data": {"playbooks": MOCK_PLAYBOOKS}}
    elif "optionsChain" in query:
        return {"data": {"optionsChain": {
            "symbol": "AAPL",
            "underlyingPrice": 175.50,
            "calls": [
                {"strike": 175, "impliedVolatility": 0.25, "delta": 0.50, "gamma": 0.02},
                {"strike": 180, "impliedVolatility": 0.24, "delta": 0.35, "gamma": 0.02}
            ],
            "puts": [
                {"strike": 170, "impliedVolatility": 0.26, "delta": -0.30, "gamma": 0.02},
                {"strike": 165, "impliedVolatility": 0.27, "delta": -0.20, "gamma": 0.02}
            ]
        }}}
    else:
        return {"data": {}}

if __name__ == "__main__":
    print("🚀 Starting RichesReach Test Server...")
    print("📱 Mobile app should connect to: http://localhost:8000")
    print("🔍 Health check: http://localhost:8000/health/")
    print("📊 AI Scans: http://localhost:8000/api/ai-scans/")
    print("⚡ Options: http://localhost:8000/api/options/copilot/recommendations")
    
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
