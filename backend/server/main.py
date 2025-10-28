# main.py
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from starlette_graphene3 import GraphQLApp, make_graphiql_handler
from settings import settings
from schema import schema
from observability import observe
from prometheus_client import make_asgi_app
import json
from datetime import datetime
from typing import List, Optional

app = FastAPI(title="RichesReach", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], allow_methods=["*"], allow_headers=["*"], allow_credentials=True
)

# Attach user to context (mock); replace with real auth
@app.middleware("http")
async def attach_user(request: Request, call_next):
    request.state.user = {
        "email": "test@example.com",
        "incomeProfile": {
            "incomeBracket": "Under $30,000",
            "age": 28,
            "investmentGoals": ["Emergency Fund","Wealth Building"],
            "riskTolerance": "Moderate",
            "investmentHorizon": "5-10 years",
        },
        "liquidCashUSD": 1800,   # drives suitability
        "monthlyContributionUSD": 150
    }
    with observe(route=request.url.path):
        response = await call_next(request)
        return response

@app.get("/health")
async def health():
    return {"status":"ok","schemaVersion": settings.SCHEMA_VERSION}

app.mount("/metrics", make_asgi_app())

app.add_route(
    "/graphql", GraphQLApp(schema=schema, on_get=make_graphiql_handler())
)

# Additional API endpoints that the mobile app needs
@app.get("/api/market/quotes")
async def get_market_quotes(symbols: str):
    """Get market quotes for multiple symbols."""
    try:
        symbol_list = symbols.split(',')
        quotes = []
        
        for symbol in symbol_list:
            symbol = symbol.strip().upper()
            # Mock data - replace with real market data
            quotes.append({
                "symbol": symbol,
                "price": 150.0 + hash(symbol) % 100,  # Mock price
                "change": (hash(symbol) % 20) - 10,   # Mock change
                "changePercent": ((hash(symbol) % 20) - 10) / 100,
                "volume": hash(symbol) % 1000000,
                "marketCap": hash(symbol) % 1000000000,
                "timestamp": datetime.now().isoformat()
            })
        
        return {"quotes": quotes}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/pump-fun/launch")
async def pump_fun_launch(request: Request):
    """Pump.fun meme launch endpoint."""
    try:
        body = await request.json()
        
        # Validate required fields
        required_fields = ["name", "symbol", "description", "template", "culturalTheme"]
        missing_fields = [field for field in required_fields if not body.get(field)]
        
        if missing_fields:
            raise HTTPException(
                status_code=400, 
                detail=f"Missing required fields: {', '.join(missing_fields)}"
            )
        
        return {
            "success": True,
            "message": "Meme launched successfully!",
            "contractAddress": "0x" + "".join([f"{ord(c):02x}" for c in body["name"]])[:40],
            "symbol": body["symbol"],
            "name": body["name"]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/trading/quote/{symbol}")
async def trading_quote(symbol: str):
    """Trading quote endpoint."""
    return {
        "symbol": symbol,
        "bid": 149.50,
        "ask": 150.00,
        "bidSize": 100,
        "askSize": 200,
        "timestamp": datetime.now().isoformat()
    }

@app.get("/api/portfolio/recommendations")
async def portfolio_recommendations():
    """Portfolio recommendations endpoint."""
    return {
        "recommendations": [
            {
                "symbol": "AAPL",
                "action": "buy",
                "confidence": 0.85,
                "reason": "Strong earnings growth"
            },
            {
                "symbol": "TSLA",
                "action": "hold",
                "confidence": 0.70,
                "reason": "Volatile but trending up"
            }
        ]
    }

@app.post("/api/kyc/workflow")
async def kyc_workflow(request: Request):
    """KYC workflow endpoint."""
    return {
        "success": True,
        "workflowId": "KYC-12345",
        "status": "pending",
        "nextStep": "document_upload"
    }

@app.post("/api/alpaca/account")
async def alpaca_account(request: Request):
    """Alpaca account creation endpoint."""
    return {
        "success": True,
        "accountId": "ALP-67890",
        "status": "pending_approval"
    }
