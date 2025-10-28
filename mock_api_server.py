#!/usr/bin/env python3

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import json
from datetime import datetime

app = FastAPI(title="RichesReach Mock API Server")

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
    return {"status": "ok", "timestamp": datetime.now().isoformat()}

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

@app.post("/api/pump-fun/launch")
async def pump_fun_launch(request: Request):
    """Pump.fun meme launch endpoint."""
    try:
        body = await request.json()
        print(f"DEBUG: Pump.fun launch request: {body}")
        
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
        print(f"Pump.fun Error: {e}")
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

if __name__ == "__main__":
    print("🚀 Starting RichesReach Mock API Server...")
    print("📡 Available endpoints:")
    print("   • POST /graphql/ - GraphQL endpoint")
    print("   • POST /api/pump-fun/launch - Meme launch")
    print("   • GET /api/trading/quote/{symbol} - Trading quotes")
    print("   • GET /api/portfolio/recommendations - Portfolio recommendations")
    print("   • POST /api/kyc/workflow - KYC workflow")
    print("   • POST /api/alpaca/account - Alpaca account")
    print("   • GET /health - Health check")
    print("")
    print("🌐 Server running on http://localhost:8002")
    print("📊 GraphQL Playground: http://localhost:8002/graphql")
    print("❤️  Health Check: http://localhost:8002/health")
    print("")
    print("Press Ctrl+C to stop the server")
    
    uvicorn.run(app, host="0.0.0.0", port=8002)
