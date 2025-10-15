#!/usr/bin/env python3
"""
Mock Crypto Server for Development
Provides realistic crypto data for testing without hitting real APIs
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import random
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any

app = FastAPI(title="Mock Crypto API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mock data generators
def generate_crypto_price(symbol: str) -> Dict[str, Any]:
    """Generate realistic crypto price data"""
    base_prices = {
        'BTC': 45000,
        'ETH': 3200,
        'SOL': 150,
        'ADA': 0.6,
        'DOT': 8.5,
        'MATIC': 0.8,
        'AVAX': 25,
        'LINK': 15,
        'UNI': 12,
        'LTC': 120,
    }
    
    base_price = base_prices.get(symbol, 100)
    volatility = random.uniform(0.02, 0.08)  # 2-8% daily volatility
    
    # Generate price with some trend
    trend = random.uniform(-0.01, 0.01)  # -1% to +1% trend
    price_change = random.uniform(-volatility, volatility)
    current_price = base_price * (1 + trend + price_change)
    
    return {
        "symbol": symbol,
        "name": f"{symbol} Coin",
        "price_usd": round(current_price, 2),
        "price_btc": round(current_price / 45000, 8),
        "volume_24h": round(random.uniform(1e9, 10e9), 0),
        "market_cap": round(current_price * random.uniform(1e6, 100e6), 0),
        "price_change_24h": round(current_price * price_change, 2),
        "price_change_percentage_24h": round(price_change * 100, 2),
        "rsi_14": round(random.uniform(30, 70), 1),
        "volatility_7d": round(random.uniform(0.02, 0.06), 4),
        "volatility_30d": round(random.uniform(0.03, 0.08), 4),
        "momentum_score": round(random.uniform(40, 90), 1),
        "sentiment_score": round(random.uniform(30, 80), 1),
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }

def generate_ml_signal(symbol: str) -> Dict[str, Any]:
    """Generate realistic ML prediction data"""
    prediction_types = ['BIG_UP_DAY', 'BIG_DOWN_DAY', 'NEUTRAL', 'VOLATILITY_SPIKE']
    confidence_levels = ['HIGH', 'MEDIUM', 'LOW']
    sentiments = ['Bullish', 'Bearish', 'Neutral', 'Cautious']
    
    prediction_type = random.choice(prediction_types)
    probability = random.uniform(0.3, 0.9)
    confidence_level = random.choice(confidence_levels)
    sentiment = random.choice(sentiments)
    
    # Generate realistic features
    features = {
        "rsi_14": round(random.uniform(30, 70), 1),
        "macd_signal": round(random.uniform(-0.5, 0.5), 3),
        "volume_z": round(random.uniform(0.5, 2.0), 2),
        "volatility_compression": round(random.uniform(0.3, 0.9), 2),
        "momentum_5d": round(random.uniform(-0.1, 0.1), 3),
        "funding_rate": round(random.uniform(-0.001, 0.001), 4),
    }
    
    explanations = [
        "Price above MA200 with rising OBV; volatility contraction breakout.",
        "Breakdown below support with increasing selling pressure.",
        "Range-bound regime; no strong catalyst.",
        "Momentum and breadth improving across key timeframes.",
        "Weakness in key technical levels and declining momentum.",
        "Mixed signals; wait for confirmation before taking action.",
    ]
    
    return {
        "symbol": symbol,
        "predictionType": prediction_type,
        "probability": round(probability, 3),
        "confidenceLevel": confidence_level,
        "sentiment": sentiment,
        "sentimentDescription": f"{sentiment} market conditions with {confidence_level.lower()} confidence.",
        "featuresUsed": features,
        "explanation": random.choice(explanations),
        "createdAt": datetime.utcnow().isoformat() + "Z",
        "expiresAt": (datetime.utcnow() + timedelta(hours=6)).isoformat() + "Z",
    }

def generate_portfolio() -> Dict[str, Any]:
    """Generate realistic portfolio data"""
    holdings = [
        {
            "symbol": "BTC",
            "name": "Bitcoin",
            "quantity": round(random.uniform(0.1, 2.0), 4),
            "average_cost": round(random.uniform(40000, 50000), 2),
            "current_price": round(random.uniform(42000, 48000), 2),
        },
        {
            "symbol": "ETH",
            "name": "Ethereum",
            "quantity": round(random.uniform(1.0, 10.0), 2),
            "average_cost": round(random.uniform(2800, 3500), 2),
            "current_price": round(random.uniform(3000, 3400), 2),
        },
        {
            "symbol": "SOL",
            "name": "Solana",
            "quantity": round(random.uniform(10, 100), 2),
            "average_cost": round(random.uniform(120, 180), 2),
            "current_price": round(random.uniform(140, 170), 2),
        },
    ]
    
    # Calculate portfolio metrics
    total_value = sum(h["quantity"] * h["current_price"] for h in holdings)
    total_cost = sum(h["quantity"] * h["average_cost"] for h in holdings)
    total_pnl = total_value - total_cost
    total_pnl_percentage = (total_pnl / total_cost * 100) if total_cost > 0 else 0
    
    # Add calculated fields to holdings
    for holding in holdings:
        holding["current_value"] = round(holding["quantity"] * holding["current_price"], 2)
        holding["unrealized_pnl"] = round(holding["current_value"] - (holding["quantity"] * holding["average_cost"]), 2)
        holding["unrealized_pnl_percentage"] = round(
            (holding["unrealized_pnl"] / (holding["quantity"] * holding["average_cost"]) * 100) 
            if holding["quantity"] * holding["average_cost"] > 0 else 0, 2
        )
        holding["staked_quantity"] = 0.0
        holding["staking_rewards"] = 0.0
        holding["staking_apy"] = None
        holding["is_collateralized"] = False
        holding["collateral_value"] = 0.0
        holding["loan_amount"] = 0.0
    
    return {
        "total_value_usd": round(total_value, 2),
        "total_cost_basis": round(total_cost, 2),
        "total_pnl": round(total_pnl, 2),
        "total_pnl_percentage": round(total_pnl_percentage, 2),
        "portfolio_volatility": round(random.uniform(0.03, 0.08), 4),
        "sharpe_ratio": round(random.uniform(1.2, 2.5), 2),
        "max_drawdown": round(random.uniform(0.1, 0.25), 3),
        "diversification_score": round(random.uniform(60, 85), 1),
        "top_holding_percentage": round(random.uniform(35, 50), 1),
        "holdings": holdings,
        "created_at": datetime.utcnow().isoformat() + "Z",
        "updated_at": datetime.utcnow().isoformat() + "Z",
    }

# API Endpoints
@app.get("/")
async def root():
    return {"message": "Mock Crypto API Server", "status": "running", "version": "1.0.0"}

@app.get("/api/crypto/currencies")
async def get_currencies():
    """Get supported cryptocurrencies"""
    currencies = [
        {"symbol": "BTC", "name": "Bitcoin", "coingecko_id": "bitcoin", "is_staking_available": False, "min_trade_amount": 0.0001, "precision": 8, "volatility_tier": "HIGH", "is_sec_compliant": False, "regulatory_status": "UNKNOWN"},
        {"symbol": "ETH", "name": "Ethereum", "coingecko_id": "ethereum", "is_staking_available": True, "min_trade_amount": 0.001, "precision": 6, "volatility_tier": "HIGH", "is_sec_compliant": False, "regulatory_status": "UNKNOWN"},
        {"symbol": "SOL", "name": "Solana", "coingecko_id": "solana", "is_staking_available": True, "min_trade_amount": 0.01, "precision": 4, "volatility_tier": "EXTREME", "is_sec_compliant": False, "regulatory_status": "UNKNOWN"},
        {"symbol": "ADA", "name": "Cardano", "coingecko_id": "cardano", "is_staking_available": True, "min_trade_amount": 1.0, "precision": 2, "volatility_tier": "HIGH", "is_sec_compliant": False, "regulatory_status": "UNKNOWN"},
        {"symbol": "DOT", "name": "Polkadot", "coingecko_id": "polkadot", "is_staking_available": True, "min_trade_amount": 0.1, "precision": 3, "volatility_tier": "HIGH", "is_sec_compliant": False, "regulatory_status": "UNKNOWN"},
    ]
    return {"currencies": currencies}

@app.get("/api/crypto/prices/{symbol}")
async def get_crypto_price(symbol: str):
    """Get crypto price data"""
    return generate_crypto_price(symbol.upper())

@app.get("/api/crypto/portfolio")
async def get_crypto_portfolio():
    """Get crypto portfolio"""
    return generate_portfolio()

@app.get("/api/crypto/predictions/{symbol}")
async def get_crypto_predictions(symbol: str):
    """Get ML predictions"""
    return {
        "symbol": symbol.upper(),
        "predictions": [generate_ml_signal(symbol.upper())]
    }

@app.get("/api/crypto/ml/signal/{symbol}")
async def get_ml_signal(symbol: str):
    """Get ML signal (GraphQL compatible)"""
    return generate_ml_signal(symbol.upper())

@app.post("/api/crypto/generate-prediction")
async def generate_prediction(data: Dict[str, Any]):
    """Generate new ML prediction"""
    symbol = data.get("symbol", "BTC")
    signal = generate_ml_signal(symbol)
    return {
        "success": True,
        "predictionId": f"pred_{int(time.time())}",
        "probability": signal["probability"],
        "explanation": signal["explanation"],
        "message": f"Prediction generated for {symbol}"
    }

if __name__ == "__main__":
    print("🚀 Starting Mock Crypto API Server on port 8127...")
    print("📊 Endpoints available:")
    print("   GET  /api/crypto/currencies")
    print("   GET  /api/crypto/prices/{symbol}")
    print("   GET  /api/crypto/portfolio")
    print("   GET  /api/crypto/predictions/{symbol}")
    print("   GET  /api/crypto/ml/signal/{symbol}")
    print("   POST /api/crypto/generate-prediction")
    uvicorn.run(app, host="0.0.0.0", port=8127)
