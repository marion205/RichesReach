#!/usr/bin/env python3
"""
Simple test server to verify basic functionality
"""

from fastapi import FastAPI
import uvicorn

app = FastAPI()

@app.get("/health")
async def health():
    return {"status": "healthy", "timestamp": "2024-01-15T10:30:00Z"}

@app.get("/test")
async def test():
    return {"message": "Test endpoint working", "status": "success"}

@app.post("/graphql/")
async def graphql_test(request: dict = None):
    return {
        "data": {
            "dayTradingPicks": {
                "asOf": "2024-01-15T10:30:00Z",
                "mode": "SAFE",
                "picks": [
                    {
                        "symbol": "AAPL",
                        "side": "LONG",
                        "score": 0.85,
                        "features": {
                            "momentum_15m": 0.02,
                            "rvol_10m": 1.5,
                            "catalyst_score": 0.8,
                            "sentiment_score": 0.6,
                            "news_sentiment": 0.4,
                            "social_sentiment": 0.7
                        },
                        "risk": {
                            "atr_5m": 1.2,
                            "size_shares": 100,
                            "stop": 0.95
                        },
                        "notes": "Test pick with sentiment analysis"
                    }
                ],
                "regimeContext": {
                    "regimeType": "BULL",
                    "confidence": 0.85,
                    "strategyWeights": {"momentum": 0.4, "volatility": 0.3},
                    "recommendations": ["Focus on momentum strategies"],
                    "sentimentEnabled": True
                }
            }
        }
    }

if __name__ == "__main__":
    print("🚀 Starting Simple Test Server...")
    print("📡 Server will be available at: http://127.0.0.1:8000")
    uvicorn.run(app, host="127.0.0.1", port=8000)
