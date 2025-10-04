#!/usr/bin/env python3
"""
Simple test server for RichesReach mobile app
Provides basic authentication and API endpoints for testing
"""

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn
import json

app = FastAPI(title="RichesReach Test Server", version="1.0.0")

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
    return {"status": "healthy", "message": "RichesReach Test Server is running"}

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

@app.get("/graphql")
@app.get("/graphql/")
@app.post("/graphql")
@app.post("/graphql/")
async def graphql_endpoint(request: Request):
    """Mock GraphQL endpoint for user profile and portfolio data"""
    if request.method == "GET":
        query = request.query_params.get("query", "")
    else:
        body = await request.json()
        query = body.get("query", "")
    
    # Mock user profile data
    if "GetMe" in query or "me" in query:
        return {
            "data": {
                "me": {
                    "id": "1",
                    "name": "Test User",
                    "email": "test@example.com",
                    "profilePic": None,
                    "followersCount": 0,
                    "followingCount": 0,
                    "isFollowingUser": False,
                    "isFollowedByUser": False,
                    "hasPremiumAccess": True,
                    "subscriptionTier": "premium",
                    "incomeProfile": {
                        "age": 28,
                        "incomeBracket": "Under $30,000",
                        "investmentGoals": ["Emergency Fund", "Wealth Building"],
                        "riskTolerance": "Moderate",
                        "investmentHorizon": "5-10 years"
                    }
                }
            }
        }
    
    # Mock portfolio data
    if "GetPortfolioMetrics" in query or "portfolioMetrics" in query:
        return {
            "data": {
                "portfolioMetrics": {
                    "totalValue": 50000.00,
                    "totalGain": 2500.00,
                    "totalGainPercent": 5.26,
                    "positions": [
                        {"symbol": "AAPL", "shares": 100, "value": 15025.00, "gain": 1025.00, "gainPercent": 7.33},
                        {"symbol": "GOOGL", "shares": 10, "value": 28005.00, "gain": 1005.00, "gainPercent": 3.73},
                        {"symbol": "MSFT", "shares": 50, "value": 17537.50, "gain": 537.50, "gainPercent": 3.16}
                    ]
                }
            }
        }
    
    # Mock AI recommendations
    if "GetAIRecommendations" in query or "aiRecommendations" in query:
        return {
            "data": {
                "aiRecommendations": {
                    "portfolioAnalysis": {
                        "totalValue": 50000.00,
                        "riskScore": 0.65,
                        "diversificationScore": 0.78
                    },
                    "recommendations": [
                        {
                            "symbol": "VTI",
                            "action": "BUY",
                            "confidence": 0.85,
                            "reason": "Diversification improvement"
                        },
                        {
                            "symbol": "AAPL",
                            "action": "HOLD",
                            "confidence": 0.72,
                            "reason": "Strong fundamentals"
                        }
                    ]
                }
            }
        }
    
    # Default response
    return {"data": {}}

if __name__ == "__main__":
    print("🚀 Starting RichesReach Test Server...")
    print("📱 Mobile app can now connect to: http://192.168.1.236:8000")
    print("🔑 Test login: test@example.com / password123")
    print("🌐 Server binding to all interfaces (0.0.0.0:8000)")
    uvicorn.run(app, host="0.0.0.0", port=8000)
