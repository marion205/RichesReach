#!/usr/bin/env python3
"""
Simple crypto API test - create a minimal working version
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"message": "Crypto API Test Server", "status": "running"}

@app.get("/api/crypto/currencies")
async def get_currencies():
    """Get supported cryptocurrencies"""
    return {
        "currencies": [
            {
                "symbol": "BTC",
                "name": "Bitcoin",
                "coingecko_id": "bitcoin",
                "is_staking_available": False,
                "min_trade_amount": 0.0001,
                "precision": 8,
                "volatility_tier": "HIGH",
                "is_sec_compliant": False,
                "regulatory_status": "UNKNOWN"
            },
            {
                "symbol": "ETH",
                "name": "Ethereum", 
                "coingecko_id": "ethereum",
                "is_staking_available": True,
                "min_trade_amount": 0.001,
                "precision": 6,
                "volatility_tier": "HIGH",
                "is_sec_compliant": False,
                "regulatory_status": "UNKNOWN"
            }
        ]
    }

@app.get("/api/crypto/prices/{symbol}")
async def get_crypto_price(symbol: str):
    """Get crypto price"""
    # Mock price data
    mock_prices = {
        "BTC": {
            "symbol": "BTC",
            "name": "Bitcoin",
            "price_usd": 45000.0,
            "price_btc": 1.0,
            "volume_24h": 25000000000,
            "market_cap": 850000000000,
            "price_change_24h": 1200.0,
            "price_change_percentage_24h": 2.75,
            "rsi_14": 65.5,
            "volatility_7d": 0.025,
            "volatility_30d": 0.035,
            "momentum_score": 75.0,
            "sentiment_score": 68.0,
            "timestamp": "2024-09-20T03:30:00Z"
        },
        "ETH": {
            "symbol": "ETH",
            "name": "Ethereum",
            "price_usd": 3200.0,
            "price_btc": 0.071,
            "volume_24h": 15000000000,
            "market_cap": 380000000000,
            "price_change_24h": 85.0,
            "price_change_percentage_24h": 2.73,
            "rsi_14": 62.0,
            "volatility_7d": 0.030,
            "volatility_30d": 0.040,
            "momentum_score": 70.0,
            "sentiment_score": 72.0,
            "timestamp": "2024-09-20T03:30:00Z"
        }
    }
    
    if symbol.upper() in mock_prices:
        return mock_prices[symbol.upper()]
    else:
        return {"error": "Cryptocurrency not found"}

@app.get("/api/crypto/portfolio")
async def get_crypto_portfolio():
    """Get mock crypto portfolio"""
    return {
        "total_value_usd": 15000.0,
        "total_cost_basis": 12000.0,
        "total_pnl": 3000.0,
        "total_pnl_percentage": 25.0,
        "portfolio_volatility": 0.045,
        "sharpe_ratio": 1.8,
        "max_drawdown": 0.15,
        "diversification_score": 75.0,
        "top_holding_percentage": 40.0,
        "holdings": [
            {
                "symbol": "BTC",
                "name": "Bitcoin",
                "quantity": 0.25,
                "average_cost": 40000.0,
                "current_price": 45000.0,
                "current_value": 11250.0,
                "unrealized_pnl": 1250.0,
                "unrealized_pnl_percentage": 12.5,
                "staked_quantity": 0.0,
                "staking_rewards": 0.0,
                "staking_apy": None,
                "is_collateralized": False,
                "collateral_value": 0.0,
                "loan_amount": 0.0
            },
            {
                "symbol": "ETH",
                "name": "Ethereum",
                "quantity": 1.2,
                "average_cost": 2800.0,
                "current_price": 3200.0,
                "current_value": 3840.0,
                "unrealized_pnl": 480.0,
                "unrealized_pnl_percentage": 14.3,
                "staked_quantity": 0.0,
                "staking_rewards": 0.0,
                "staking_apy": None,
                "is_collateralized": False,
                "collateral_value": 0.0,
                "loan_amount": 0.0
            }
        ],
        "created_at": "2024-09-20T03:30:00Z",
        "updated_at": "2024-09-20T03:30:00Z"
    }

@app.get("/api/crypto/predictions/{symbol}")
async def get_crypto_predictions(symbol: str):
    """Get mock ML predictions"""
    return {
        "symbol": symbol.upper(),
        "predictions": [
            {
                "prediction_type": "BIG_UP_DAY",
                "probability": 0.72,
                "confidence_level": "HIGH",
                "features_used": {
                    "momentum_5d": 0.15,
                    "volatility_compression": 0.8,
                    "rsi_14": 65.5,
                    "volume_spike": 1.3,
                    "funding_rate": 0.0001
                },
                "model_version": "v1.0",
                "prediction_horizon_hours": 24,
                "created_at": "2024-09-20T03:30:00Z",
                "expires_at": "2024-09-21T03:30:00Z",
                "was_correct": None,
                "actual_return": None
            }
        ]
    }

if __name__ == "__main__":
    print("🚀 Starting Crypto API Test Server on port 8126...")
    uvicorn.run(app, host="0.0.0.0", port=8126)
