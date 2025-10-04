#!/usr/bin/env python3
"""
Working test server for RichesReach mobile app
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

@app.get("/api/user/profile")
async def get_user_profile():
    """Mock user profile endpoint"""
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

@app.post("/graphql")
@app.post("/graphql/")
@app.get("/graphql")
@app.get("/graphql/")
async def graphql_endpoint(request: Request):
    """Mock GraphQL endpoint for user profile and portfolio data"""
    try:
        if request.method == "GET":
            query = request.query_params.get("query", "")
            variables = request.query_params.get("variables", "{}")
            body = {"query": query, "variables": json.loads(variables) if variables else {}}
        else:
            body = await request.json()
            query = body.get("query", "")
    except Exception as e:
        query = ""
        body = {}
        print(f"DEBUG: Failed to parse request body: {e}")
    
    # Mock user profile data - only for specific user queries
    if "GetMe" in query or (query.strip().startswith("query") and "me" in query and "beginnerFriendlyStocks" not in query and "researchHub" not in query and "stockChartData" not in query and "tradingAccount" not in query and "stocks" not in query):
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
    
    # Mock beginner friendly stocks
    if "beginnerFriendlyStocks" in query:
        return {
            "data": {
                "beginnerFriendlyStocks": [
                    {
                        "id": "1",
                        "symbol": "AAPL",
                        "companyName": "Apple Inc.",
                        "sector": "Technology",
                        "marketCap": 3000000000000,
                        "peRatio": 28.5,
                        "dividendYield": 0.44,
                        "beginnerFriendlyScore": 0.85,
                        "currentPrice": 150.25,
                        "beginnerScoreBreakdown": {
                            "score": 0.85,
                            "factors": [
                                {"name": "Stability", "weight": 0.3, "value": 0.9, "contrib": 0.27, "detail": "Large cap, stable business"},
                                {"name": "Growth", "weight": 0.25, "value": 0.8, "contrib": 0.20, "detail": "Consistent revenue growth"},
                                {"name": "Dividend", "weight": 0.2, "value": 0.7, "contrib": 0.14, "detail": "Regular dividend payments"},
                                {"name": "Volatility", "weight": 0.25, "value": 0.8, "contrib": 0.20, "detail": "Moderate price volatility"}
                            ],
                            "notes": "Excellent choice for beginners due to strong fundamentals and market position"
                        },
                        "__typename": "BeginnerFriendlyStock"
                    },
                    {
                        "id": "2",
                        "symbol": "MSFT",
                        "companyName": "Microsoft Corporation",
                        "sector": "Technology",
                        "marketCap": 2800000000000,
                        "peRatio": 32.1,
                        "dividendYield": 0.68,
                        "beginnerFriendlyScore": 0.82,
                        "currentPrice": 350.75,
                        "beginnerScoreBreakdown": {
                            "score": 0.82,
                            "factors": [
                                {"name": "Stability", "weight": 0.3, "value": 0.85, "contrib": 0.255, "detail": "Dominant market position"},
                                {"name": "Growth", "weight": 0.25, "value": 0.75, "contrib": 0.1875, "detail": "Cloud business growth"},
                                {"name": "Dividend", "weight": 0.2, "value": 0.8, "contrib": 0.16, "detail": "Growing dividend yield"},
                                {"name": "Volatility", "weight": 0.25, "value": 0.8, "contrib": 0.20, "detail": "Stable price movement"}
                            ],
                            "notes": "Strong cloud business and enterprise focus make it beginner-friendly"
                        },
                        "__typename": "BeginnerFriendlyStock"
                    },
                    {
                        "id": "3",
                        "symbol": "JNJ",
                        "companyName": "Johnson & Johnson",
                        "sector": "Healthcare",
                        "marketCap": 450000000000,
                        "peRatio": 15.2,
                        "dividendYield": 2.8,
                        "beginnerFriendlyScore": 0.88,
                        "currentPrice": 165.50,
                        "beginnerScoreBreakdown": {
                            "score": 0.88,
                            "factors": [
                                {"name": "Stability", "weight": 0.3, "value": 0.95, "contrib": 0.285, "detail": "Defensive healthcare stock"},
                                {"name": "Growth", "weight": 0.25, "value": 0.7, "contrib": 0.175, "detail": "Steady long-term growth"},
                                {"name": "Dividend", "weight": 0.2, "value": 0.95, "contrib": 0.19, "detail": "High dividend yield"},
                                {"name": "Volatility", "weight": 0.25, "value": 0.9, "contrib": 0.225, "detail": "Low volatility"}
                            ],
                            "notes": "Excellent defensive stock with high dividend yield"
                        },
                        "__typename": "BeginnerFriendlyStock"
                    }
                ]
            }
        }
    
    # Mock research hub data
    if "researchHub" in query:
        return {
            "data": {
                "researchHub": {
                    "symbol": "AAPL",
                    "company": {
                        "name": "Apple Inc.",
                        "sector": "Technology",
                        "marketCap": 3000000000000,
                        "country": "United States",
                        "website": "https://www.apple.com"
                    },
                    "quote": {
                        "currentPrice": 150.25,
                        "change": 2.15,
                        "changePercent": 1.45,
                        "high": 152.80,
                        "low": 148.90,
                        "volume": 45000000
                    },
                    "technicals": {
                        "rsi": 58.5,
                        "macd": 1.25,
                        "macdhistogram": 0.15,
                        "movingAverage50": 148.20,
                        "movingAverage200": 145.80,
                        "supportLevel": 145.00,
                        "resistanceLevel": 155.00,
                        "impliedVolatility": 0.22
                    },
                    "sentiment": {
                        "sentiment_label": "Bullish",
                        "sentiment_score": 0.75,
                        "article_count": 45,
                        "confidence": 0.82
                    },
                    "macro": {
                        "vix": 18.5,
                        "market_sentiment": "Neutral",
                        "risk_appetite": "Moderate"
                    },
                    "marketRegime": {
                        "market_regime": "Bull Market",
                        "confidence": 0.78,
                        "recommended_strategy": "Growth"
                    },
                    "peers": ["MSFT", "GOOGL", "AMZN", "META"],
                    "updatedAt": "2024-01-15T10:30:00Z"
                }
            }
        }
    
    # Mock stock chart data
    if "stockChartData" in query:
        return {
            "data": {
                "stockChartData": {
                    "symbol": "AAPL",
                    "interval": "1D",
                    "limit": 180,
                    "currentPrice": 150.25,
                    "change": 2.15,
                    "changePercent": 1.45,
                    "data": [
                        {"timestamp": "2024-01-15T16:00:00Z", "open": 148.50, "high": 152.80, "low": 148.20, "close": 150.25, "volume": 45000000},
                        {"timestamp": "2024-01-14T16:00:00Z", "open": 147.80, "high": 149.50, "low": 146.90, "close": 148.10, "volume": 42000000},
                        {"timestamp": "2024-01-13T16:00:00Z", "open": 146.20, "high": 148.80, "low": 145.50, "close": 147.80, "volume": 38000000}
                    ],
                    "indicators": {
                        "SMA20": 148.20,
                        "SMA50": 145.80,
                        "EMA12": 149.10,
                        "EMA26": 147.50,
                        "BBUpper": 152.50,
                        "BBMiddle": 148.20,
                        "BBLower": 143.90,
                        "RSI14": 58.5,
                        "MACD": 1.25,
                        "MACDSignal": 1.10,
                        "MACDHist": 0.15
                    }
                }
            }
        }
    
    # Mock trading account data
    if "tradingAccount" in query:
        return {
            "data": {
                "tradingAccount": {
                    "id": "1",
                    "buyingPower": 25000.00,
                    "cash": 15000.00,
                    "portfolioValue": 50000.00,
                    "equity": 50000.00,
                    "dayTradeCount": 2,
                    "patternDayTrader": False,
                    "tradingBlocked": False,
                    "dayTradingBuyingPower": 50000.00,
                    "isDayTradingEnabled": True,
                    "accountStatus": "ACTIVE",
                    "createdAt": "2024-01-01T00:00:00Z"
                }
            }
        }
    
    # Mock trading positions
    if "tradingPositions" in query:
        return {
            "data": {
                "tradingPositions": [
                    {
                        "id": "1",
                        "symbol": "AAPL",
                        "quantity": 100,
                        "marketValue": 15025.00,
                        "costBasis": 14000.00,
                        "unrealizedPl": 1025.00,
                        "unrealizedPlpc": 7.33,
                        "currentPrice": 150.25,
                        "side": "long"
                    },
                    {
                        "id": "2",
                        "symbol": "MSFT",
                        "quantity": 50,
                        "marketValue": 17537.50,
                        "costBasis": 17000.00,
                        "unrealizedPl": 537.50,
                        "unrealizedPlpc": 3.16,
                        "currentPrice": 350.75,
                        "side": "long"
                    }
                ]
            }
        }
    
    # Mock trading orders
    if "tradingOrders" in query:
        return {
            "data": {
                "tradingOrders": [
                    {
                        "id": "1",
                        "symbol": "AAPL",
                        "side": "buy",
                        "orderType": "market",
                        "quantity": 10,
                        "price": None,
                        "stopPrice": None,
                        "status": "filled",
                        "createdAt": "2024-01-15T10:30:00Z",
                        "filledAt": "2024-01-15T10:30:05Z",
                        "filledQuantity": 10,
                        "averageFillPrice": 150.25,
                        "commission": 0.00,
                        "notes": "Market order"
                    }
                ]
            }
        }
    
    # Mock trading quote
    if "tradingQuote" in query:
        return {
            "data": {
                "tradingQuote": {
                    "symbol": "AAPL",
                    "bid": 150.20,
                    "ask": 150.30,
                    "bidSize": 1000,
                    "askSize": 1500,
                    "timestamp": "2024-01-15T10:30:00Z"
                }
            }
        }
    
    # General stocks query (for Browse All tab)
    if "stocks" in query and "beginnerFriendlyStocks" not in query:
        try:
            # Get search parameters
            search = body.get("variables", {}).get("search", "")
            limit = body.get("variables", {}).get("limit", 10)
            offset = body.get("variables", {}).get("offset", 0)
            
            # Mock stock data with search filtering
            all_stocks = [
                {
                    "id": "1",
                    "symbol": "AAPL",
                    "companyName": "Apple Inc.",
                    "sector": "Technology",
                    "marketCap": 3000000000000,
                    "peRatio": 28.5,
                    "dividendYield": 0.44,
                    "beginnerFriendlyScore": 0.85,
                    "currentPrice": 150.25,
                    "beginnerScoreBreakdown": {
                        "score": 0.85,
                        "factors": [
                            {"name": "Stability", "weight": 0.3, "value": 0.9, "contrib": 0.27, "detail": "Large cap, stable business"},
                            {"name": "Growth", "weight": 0.25, "value": 0.8, "contrib": 0.2, "detail": "Consistent revenue growth"},
                            {"name": "Dividend", "weight": 0.2, "value": 0.7, "contrib": 0.14, "detail": "Regular dividend payments"},
                            {"name": "Volatility", "weight": 0.25, "value": 0.8, "contrib": 0.2, "detail": "Moderate price volatility"}
                        ],
                        "notes": "Excellent choice for beginners due to strong fundamentals and market position"
                    },
                    "__typename": "Stock"
                },
                {
                    "id": "2",
                    "symbol": "MSFT",
                    "companyName": "Microsoft Corporation",
                    "sector": "Technology",
                    "marketCap": 2800000000000,
                    "peRatio": 32.1,
                    "dividendYield": 0.68,
                    "beginnerFriendlyScore": 0.82,
                    "currentPrice": 350.75,
                    "beginnerScoreBreakdown": {
                        "score": 0.82,
                        "factors": [
                            {"name": "Stability", "weight": 0.3, "value": 0.85, "contrib": 0.255, "detail": "Dominant market position"},
                            {"name": "Growth", "weight": 0.25, "value": 0.75, "contrib": 0.1875, "detail": "Cloud business growth"},
                            {"name": "Dividend", "weight": 0.2, "value": 0.8, "contrib": 0.16, "detail": "Growing dividend yield"},
                            {"name": "Volatility", "weight": 0.25, "value": 0.8, "contrib": 0.2, "detail": "Stable price movement"}
                        ],
                        "notes": "Strong cloud business and enterprise focus make it beginner-friendly"
                    },
                    "__typename": "Stock"
                },
                {
                    "id": "3",
                    "symbol": "GOOGL",
                    "companyName": "Alphabet Inc.",
                    "sector": "Technology",
                    "marketCap": 1800000000000,
                    "peRatio": 25.8,
                    "dividendYield": 0.0,
                    "beginnerFriendlyScore": 0.78,
                    "currentPrice": 142.50,
                    "beginnerScoreBreakdown": {
                        "score": 0.78,
                        "factors": [
                            {"name": "Stability", "weight": 0.3, "value": 0.8, "contrib": 0.24, "detail": "Search dominance"},
                            {"name": "Growth", "weight": 0.25, "value": 0.85, "contrib": 0.2125, "detail": "Strong revenue growth"},
                            {"name": "Dividend", "weight": 0.2, "value": 0.0, "contrib": 0.0, "detail": "No dividend"},
                            {"name": "Volatility", "weight": 0.25, "value": 0.7, "contrib": 0.175, "detail": "Higher volatility"}
                        ],
                        "notes": "Growth stock with no dividend, suitable for growth-focused investors"
                    },
                    "__typename": "Stock"
                },
                {
                    "id": "4",
                    "symbol": "TSLA",
                    "companyName": "Tesla Inc.",
                    "sector": "Consumer Discretionary",
                    "marketCap": 800000000000,
                    "peRatio": 45.2,
                    "dividendYield": 0.0,
                    "beginnerFriendlyScore": 0.65,
                    "currentPrice": 250.80,
                    "beginnerScoreBreakdown": {
                        "score": 0.65,
                        "factors": [
                            {"name": "Stability", "weight": 0.3, "value": 0.6, "contrib": 0.18, "detail": "Volatile stock"},
                            {"name": "Growth", "weight": 0.25, "value": 0.9, "contrib": 0.225, "detail": "High growth potential"},
                            {"name": "Dividend", "weight": 0.2, "value": 0.0, "contrib": 0.0, "detail": "No dividend"},
                            {"name": "Volatility", "weight": 0.25, "value": 0.5, "contrib": 0.125, "detail": "High volatility"}
                        ],
                        "notes": "High-risk, high-reward growth stock"
                    },
                    "__typename": "Stock"
                },
                {
                    "id": "5",
                    "symbol": "AMZN",
                    "companyName": "Amazon.com Inc.",
                    "sector": "Consumer Discretionary",
                    "marketCap": 1600000000000,
                    "peRatio": 52.3,
                    "dividendYield": 0.0,
                    "beginnerFriendlyScore": 0.72,
                    "currentPrice": 155.40,
                    "beginnerScoreBreakdown": {
                        "score": 0.72,
                        "factors": [
                            {"name": "Stability", "weight": 0.3, "value": 0.75, "contrib": 0.225, "detail": "E-commerce leader"},
                            {"name": "Growth", "weight": 0.25, "value": 0.8, "contrib": 0.2, "detail": "Cloud and retail growth"},
                            {"name": "Dividend", "weight": 0.2, "value": 0.0, "contrib": 0.0, "detail": "No dividend"},
                            {"name": "Volatility", "weight": 0.25, "value": 0.7, "contrib": 0.175, "detail": "Moderate volatility"}
                        ],
                        "notes": "Diversified business model with strong growth prospects"
                    },
                    "__typename": "Stock"
                }
            ]
            
            # Filter by search if provided
            if search:
                filtered_stocks = [s for s in all_stocks if search.upper() in s["symbol"] or search.lower() in s["companyName"].lower()]
            else:
                filtered_stocks = all_stocks
            
            # Apply pagination
            start_idx = offset
            end_idx = offset + limit
            paginated_stocks = filtered_stocks[start_idx:end_idx]
        
            return {
                "data": {
                    "stocks": paginated_stocks
                }
            }
        except Exception as e:
            return {
                "data": {
                    "stocks": []
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
