#!/usr/bin/env python3
"""
Quick test server for RichesReach mobile app
Provides basic authentication and API endpoints for immediate testing
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn
import json
from fastapi.responses import JSONResponse

app = FastAPI(title="RichesReach Quick Test Server", version="1.0.0")

# Enable CORS for mobile app
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mock data
MOCK_USERS = {
    "test@example.com": {
        "password": "password123",
        "name": "Test User",
        "id": 1
    }
}

MOCK_STOCKS = [
    {"symbol": "AAPL", "price": 150.25, "change": 2.15, "changePercent": 1.45},
    {"symbol": "GOOGL", "price": 2800.50, "change": -15.25, "changePercent": -0.54},
    {"symbol": "MSFT", "price": 350.75, "change": 5.30, "changePercent": 1.53},
    {"symbol": "TSLA", "price": 250.80, "change": -8.20, "changePercent": -3.17},
]

class LoginRequest(BaseModel):
    email: str
    password: str

class LoginResponse(BaseModel):
    success: bool
    token: str = None
    user: dict = None
    message: str = None

@app.get("/health")
async def health_check():
    return {"status": "healthy", "message": "RichesReach Quick Test Server is running"}

@app.post("/api/auth/login", response_model=LoginResponse)
async def login(request: LoginRequest):
    """Mock login endpoint"""
    if request.email in MOCK_USERS and MOCK_USERS[request.email]["password"] == request.password:
        user = MOCK_USERS[request.email]
        return LoginResponse(
            success=True,
            token="mock_jwt_token_12345",
            user={
                "id": user["id"],
                "email": request.email,
                "name": user["name"]
            },
            message="Login successful"
        )
    else:
        raise HTTPException(status_code=401, detail="Invalid credentials")

@app.get("/api/stocks")
async def get_stocks():
    """Mock stocks endpoint"""
    return {"stocks": MOCK_STOCKS}

@app.get("/api/portfolio")
async def get_portfolio():
    """Mock portfolio endpoint"""
    return {
        "portfolio": {
            "totalValue": 50000.00,
            "totalGain": 2500.00,
            "totalGainPercent": 5.26,
            "holdings": [
                {"symbol": "AAPL", "shares": 100, "value": 15025.00},
                {"symbol": "GOOGL", "shares": 10, "value": 28005.00},
                {"symbol": "MSFT", "shares": 50, "value": 17537.50}
            ]
        }
    }

@app.get("/api/crypto")
async def get_crypto():
    """Mock crypto endpoint"""
    return {
        "crypto": [
            {"symbol": "BTC", "price": 45000.00, "change": 1200.00, "changePercent": 2.74},
            {"symbol": "ETH", "price": 3200.00, "change": -50.00, "changePercent": -1.54},
            {"symbol": "SOL", "price": 95.50, "change": 5.25, "changePercent": 5.82}
        ]
    }

@app.post("/graphql/")
async def graphql_endpoint(request: dict):
    """Mock GraphQL endpoint for mobile app compatibility"""
    query = request.get("query", "")
    variables = request.get("variables", {})
    
    # Debug logging
    print(f"🔍 GraphQL Request: {query[:100]}...")
    print(f"📝 Variables: {variables}")
    print(f"🔍 Query contains 'tokenauth': {'tokenauth' in query.lower()}")
    print(f"🔍 Query contains 'mutation': {'mutation' in query.lower()}")
    print(f"🔍 Full query: {query}")
    
    # Handle introspection queries (but only if it's NOT a tokenAuth mutation)
    if ("__schema" in query or "__type" in query) and "tokenauth" not in query.lower():
        return JSONResponse(content={
            "data": {
                "__schema": {
                    "queryType": {"name": "Query"},
                    "mutationType": {"name": "Mutation"},
                    "types": []
                }
            }
        })
    
    # Handle tokenAuth mutation (the actual mutation the mobile app uses)
    if "tokenauth" in query.lower() and "mutation" in query.lower():
        # Always return consistent shape - never return None/null for required fields
        response = {
            "data": {
                "tokenAuth": {
                    "token": "mock_jwt_token_12345",
                    "payload": {
                        "email": "test@example.com",
                        "exp": 9999999999,
                        "origIat": 1234567890
                    },
                    "refreshToken": "mock_refresh_token_67890"
                }
            }
        }
        print(f"✅ Returning tokenAuth response: {response}")
        return JSONResponse(content=response)
    
    # Handle any other tokenAuth requests (fallback)
    if "tokenauth" in query.lower():
        response = {
            "data": {
                "tokenAuth": {
                    "token": "mock_jwt_token_12345",
                    "payload": {
                        "email": "test@example.com",
                        "exp": 9999999999,
                        "origIat": 1234567890
                    },
                    "refreshToken": "mock_refresh_token_67890"
                }
            }
        }
        print(f"✅ Returning tokenAuth response (fallback): {response}")
        return JSONResponse(content=response)
    
    # Handle login mutation (fallback)
    if "login" in query.lower():
        return JSONResponse(content={
            "data": {
                "login": {
                    "success": True,
                    "token": "mock_jwt_token_12345",
                    "user": {
                        "id": 1,
                        "email": "test@example.com",
                        "name": "Test User"
                    }
                }
            }
        })
    
    # Handle refreshToken mutation
    if "refreshtoken" in query.lower():
        return JSONResponse(content={
            "data": {
                "refreshToken": {
                    "token": "mock_refreshed_jwt_token_67890",
                    "payload": {
                        "email": "test@example.com",
                        "exp": 9999999999,
                        "origIat": 1234567890
                    }
                }
            }
        })
    
    # Handle user query
    if "me" in query.lower():
        return JSONResponse(content={
            "data": {
                "me": {
                    "id": 1,
                    "email": "test@example.com",
                    "name": "Test User",
                    "hasPremiumAccess": True,
                    "subscriptionTier": "premium"
                }
            }
        })
    
    # Handle myWatchlist query
    if "mywatchlist" in query.lower():
        return JSONResponse(content={
            "data": {
                "myWatchlist": [
                    {
                        "id": 1,
                        "stock": {
                            "id": 1,
                            "symbol": "AAPL",
                            "companyName": "Apple Inc.",
                            "sector": "Technology",
                            "beginnerFriendlyScore": 8,
                            "currentPrice": 150.25
                        },
                        "addedAt": "2024-01-01T00:00:00Z",
                        "notes": "Strong fundamentals",
                        "targetPrice": 160.00
                    }
                ]
            }
        })
    
    # Handle portfolioMetrics query
    if "portfoliometrics" in query.lower():
        return JSONResponse(content={
            "data": {
                "portfolioMetrics": {
                    "totalValue": 50000.00,
                    "totalCost": 45000.00,
                    "totalReturn": 5000.00,
                    "totalReturnPercent": 11.11,
                    "holdings": [
                        {
                            "symbol": "AAPL",
                            "companyName": "Apple Inc.",
                            "shares": 100,
                            "currentPrice": 150.25,
                            "totalValue": 15025.00,
                            "costBasis": 14000.00,
                            "returnAmount": 1025.00,
                            "returnPercent": 7.32,
                            "sector": "Technology"
                        }
                    ]
                }
            }
        })
    
    # Handle advancedStockScreening query
    if "advancedstockscreening" in query.lower():
        return JSONResponse(content={
            "data": {
                "advancedStockScreening": [
                    {
                        "symbol": "AAPL",
                        "companyName": "Apple Inc.",
                        "sector": "Technology",
                        "marketCap": 2500000000000,
                        "peRatio": 25.5,
                        "dividendYield": 0.5,
                        "beginnerFriendlyScore": 8,
                        "currentPrice": 150.25,
                        "volatility": 0.25,
                        "debtRatio": 0.15,
                        "reasoning": "Strong fundamentals and market position",
                        "score": 85,
                        "mlScore": 0.87
                    },
                    {
                        "symbol": "MSFT",
                        "companyName": "Microsoft Corporation",
                        "sector": "Technology",
                        "marketCap": 2200000000000,
                        "peRatio": 28.3,
                        "dividendYield": 0.7,
                        "beginnerFriendlyScore": 9,
                        "currentPrice": 350.75,
                        "volatility": 0.22,
                        "debtRatio": 0.12,
                        "reasoning": "Excellent cloud business and dividend growth",
                        "score": 92,
                        "mlScore": 0.91
                    }
                ]
            }
        })
    
    # Handle stocks query
    if "stocks" in query.lower():
        return JSONResponse(content={
            "data": {
                "stocks": [
                    {"id": 1, "symbol": "AAPL", "companyName": "Apple Inc.", "sector": "Technology", "marketCap": 2500000000000, "peRatio": 25.5, "dividendYield": 0.5, "beginnerFriendlyScore": 8},
                    {"id": 2, "symbol": "GOOGL", "companyName": "Alphabet Inc.", "sector": "Technology", "marketCap": 1800000000000, "peRatio": 22.1, "dividendYield": 0.0, "beginnerFriendlyScore": 7},
                    {"id": 3, "symbol": "MSFT", "companyName": "Microsoft Corporation", "sector": "Technology", "marketCap": 2200000000000, "peRatio": 28.3, "dividendYield": 0.7, "beginnerFriendlyScore": 9}
                ]
            }
        })
    
    # Default response
    return JSONResponse(content={
        "data": {
            "message": "Mock GraphQL endpoint working"
        }
    })

if __name__ == "__main__":
    print("🚀 Starting RichesReach Quick Test Server...")
    print("📱 Mobile app can now connect to: http://127.0.0.1:8000")
    print("🔑 Test login: test@example.com / password123")
    uvicorn.run(app, host="0.0.0.0", port=8000)
