#!/usr/bin/env python3

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import json
from datetime import datetime
from typing import List, Optional

app = FastAPI(title="RichesReach Main Server", version="1.0.0")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
async def health():
    return {"status": "ok", "schemaVersion": "1.0.0", "timestamp": datetime.now().isoformat()}

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

@app.post("/graphql/")
async def graphql_endpoint(request: Request):
    """GraphQL endpoint for Apollo Client."""
    try:
        body = await request.json()
        query_str = body.get("query", "")
        variables = body.get("variables", {})
        
        print(f"DEBUG: GraphQL query received: {query_str[:100]}...")
        
        # Handle common GraphQL queries
        if "createIncomeProfile" in query_str:
            return {
                "data": {
                    "createIncomeProfile": {
                        "success": True,
                        "message": "Profile created successfully"
                    }
                }
            }
        
        elif "placeStockOrder" in query_str:
            return {
                "data": {
                    "placeStockOrder": {
                        "success": True,
                        "message": "Order placed successfully",
                        "orderId": "ORD-12345"
                    }
                }
            }
        
        elif "createAlpacaAccount" in query_str:
            return {
                "data": {
                    "createAlpacaAccount": {
                        "success": True,
                        "message": "Account created successfully",
                        "alpacaAccountId": "ACC-67890"
                    }
                }
            }
        
        elif "createPosition" in query_str:
            return {
                "data": {
                    "createPosition": {
                        "success": True,
                        "message": "Position created successfully",
                        "position": {
                            "symbol": variables.get("symbol", "AAPL"),
                            "side": variables.get("side", "buy"),
                            "entryPrice": variables.get("price", 150.0),
                            "quantity": variables.get("quantity", 10)
                        }
                    }
                }
            }
        
        # Handle user profile queries
        elif "me" in query_str:
            return {
                "data": {
                    "me": {
                        "id": "1",
                        "name": "Test User",
                        "email": "test@example.com",
                        "hasPremiumAccess": True,
                        "subscriptionTier": "premium",
                        "incomeProfile": {
                            "incomeBracket": "Under $30,000",
                            "age": 28,
                            "investmentGoals": ["Emergency Fund", "Wealth Building"],
                            "riskTolerance": "Moderate",
                            "investmentHorizon": "5-10 years"
                        }
                    }
                }
            }
        
        # Handle stock queries
        elif "stocks" in query_str:
            return {
                "data": {
                    "stocks": [
                        {
                            "symbol": "AAPL",
                            "name": "Apple Inc.",
                            "price": 150.0,
                            "change": 2.5,
                            "changePercent": 1.69
                        },
                        {
                            "symbol": "TSLA",
                            "name": "Tesla Inc.",
                            "price": 200.0,
                            "change": -5.0,
                            "changePercent": -2.44
                        }
                    ]
                }
            }
        
        # Handle AI recommendations
        elif "aiRecommendations" in query_str:
            return {
                "data": {
                    "aiRecommendations": {
                        "buyRecommendations": [
                            {
                                "symbol": "AAPL",
                                "companyName": "Apple Inc.",
                                "recommendation": "BUY",
                                "confidence": 0.85,
                                "reasoning": "Strong earnings growth",
                                "targetPrice": 160.0,
                                "currentPrice": 150.0,
                                "expectedReturn": 0.067
                            }
                        ]
                    }
                }
            }
        
        # Handle watchlist queries
        elif "myWatchlist" in query_str:
            return {
                "data": {
                    "myWatchlist": [
                        {
                            "id": "1",
                            "stock": {
                                "symbol": "AAPL",
                                "__typename": "Stock"
                            }
                        }
                    ]
                }
            }
        
        # Default response for any other GraphQL query
        return {
            "data": {},
            "errors": []
        }
        
    except Exception as e:
        print(f"GraphQL Error: {e}")
        return {
            "data": None,
            "errors": [{"message": str(e)}]
        }

if __name__ == "__main__":
    print("🚀 Starting RichesReach Main Server...")
    print("📡 Available endpoints:")
    print("   • GET /health - Health check")
    print("   • GET /api/market/quotes - Market quotes")
    print("   • POST /api/pump-fun/launch - Meme launch")
    print("   • GET /api/trading/quote/{symbol} - Trading quotes")
    print("   • GET /api/portfolio/recommendations - Portfolio recommendations")
    print("   • POST /api/kyc/workflow - KYC workflow")
    print("   • POST /api/alpaca/account - Alpaca account")
    print("   • POST /graphql/ - GraphQL endpoint")
    print("")
    print("🌐 Server running on http://localhost:8000")
    print("📊 GraphQL Playground: http://localhost:8000/graphql")
    print("❤️  Health Check: http://localhost:8000/health")
    print("")
    print("Press Ctrl+C to stop the server")
    
    uvicorn.run(app, host="0.0.0.0", port=8000)
