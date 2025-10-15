#!/usr/bin/env python3
"""
Simple test server for RichesReach mobile app
Provides basic authentication and API endpoints for testing
"""

from fastapi import FastAPI, HTTPException
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

if __name__ == "__main__":
    print("🚀 Starting RichesReach Test Server...")
    print("📱 Mobile app can now connect to: http://localhost:8000")
    print("🔑 Test login: test@example.com / password123")
    uvicorn.run(app, host="0.0.0.0", port=8000)
