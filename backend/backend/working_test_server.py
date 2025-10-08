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
    print(f"🔍 GraphQL Request: {request.method} {request.url}")
    print(f"📱 Client IP: {request.client.host}")
    print(f"📋 Headers: {dict(request.headers)}")
    
    try:
        if request.method == "GET":
            query = request.query_params.get("query", "")
            variables = request.query_params.get("variables", "{}")
            body = {"query": query, "variables": json.loads(variables) if variables else {}}
        else:
            body = await request.json()
            query = body.get("query", "")
        
        print(f"📝 Query: {query[:100]}...")
        print(f"📊 Variables: {body.get('variables', {})}")
    except Exception as e:
        query = ""
        body = {}
        print(f"❌ DEBUG: Failed to parse request body: {e}")
    
    # Mock user profile data - only for specific user queries
    if "GetMe" in query or (query.strip().startswith("query") and "me {" in query and "beginnerFriendlyStocks" not in query and "researchHub" not in query and "stockChartData" not in query and "tradingAccount" not in query and "stocks" not in query and "myWatchlist" not in query and "myPortfolios" not in query and "portfolioMetrics" not in query and "dayTradingPicks" not in query and "stockDiscussions" not in query and "availableBenchmarks" not in query and "benchmarkSeries" not in query and "advancedStockScreening" not in query and "rustStockAnalysis" not in query and "optionOrders" not in query and "cryptoMlSignal" not in query and "aiRecommendations" not in query and "cryptoPortfolio" not in query and "supportedCurrencies" not in query and "cryptoRecommendations" not in query and "tickerPostCreated" not in query and "quotes" not in query and "generateAiRecommendations" not in query and "aiRebalancePortfolio" not in query and "bankAccounts" not in query and "fundingHistory" not in query and "sblocOffer" not in query and "sblocBanks" not in query and "notifications" not in query and "notificationSettings" not in query and "optionsAnalysis" not in query and "feedByTickers" not in query):
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
                    "followedTickers": ["AAPL", "MSFT", "GOOGL"],
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
    
    
    # Mock AI recommendations
    if "GetAIRecommendations" in query or (query.strip().startswith("query") and "aiRecommendations {" in query and "notificationSettings" not in query):
        return {
            "data": {
                "aiRecommendations": {
                    "portfolioAnalysis": {
                        "totalValue": 50000.00,
                        "numHoldings": 8,
                        "sectorBreakdown": {
                            "Technology": 0.45,
                            "Healthcare": 0.25,
                            "Financial": 0.15,
                            "Consumer": 0.15
                        },
                        "riskScore": 0.65,
                        "diversificationScore": 0.78,
                        "expectedImpact": {
                            "evPct": 0.12,
                            "evAbs": 6000.00,
                            "per10k": 1200.00
                        },
                        "risk": {
                            "volatilityEstimate": 0.18,
                            "maxDrawdownPct": 0.25
                        },
                        "assetAllocation": {
                            "stocks": 0.80,
                            "bonds": 0.15,
                            "cash": 0.05
                        }
                    },
                    "buyRecommendations": [
                        {
                            "symbol": "VTI",
                            "companyName": "Vanguard Total Stock Market ETF",
                            "recommendation": "BUY",
                            "confidence": 0.85,
                            "reasoning": "Diversification improvement",
                            "targetPrice": 250.00,
                            "currentPrice": 240.00,
                            "expectedReturn": 0.12,
                            "allocation": 15.0
                        },
                        {
                            "symbol": "MSFT",
                            "companyName": "Microsoft Corporation",
                            "recommendation": "BUY",
                            "confidence": 0.78,
                            "reasoning": "Cloud growth momentum",
                            "targetPrice": 380.00,
                            "currentPrice": 350.75,
                            "expectedReturn": 0.15,
                            "allocation": 10.0
                        }
                    ],
                    "sellRecommendations": [
                        {
                            "symbol": "TSLA",
                            "reasoning": "High volatility, consider reducing position"
                        }
                    ],
                    "rebalanceSuggestions": [
                        {
                            "action": "REDUCE",
                            "currentAllocation": 0.25,
                            "suggestedAllocation": 0.20,
                            "reasoning": "Technology overweight",
                            "priority": "HIGH"
                        }
                    ],
                    "riskAssessment": {
                        "overallRisk": "MODERATE",
                        "volatilityEstimate": 0.18,
                        "recommendations": [
                            "Consider adding more bonds for stability",
                            "Monitor technology sector concentration"
                        ]
                    },
                    "marketOutlook": {
                        "overallSentiment": "Bullish",
                        "confidence": 0.78,
                        "keyFactors": [
                            "Strong earnings growth",
                            "Low interest rates",
                            "Technology sector momentum",
                            "Consumer spending resilience"
                        ]
                    }
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
                        "beginnerFriendlyScore": 85,
                        "currentPrice": 150.25,
                        "beginnerScoreBreakdown": {
                            "score": 0.85,
                            "factors": [
                                {"name": "Stability", "weight": 0.3, "value": 0.9, "contrib": 0.27, "detail": "Large cap, stable business"},
                                {"name": "Growth", "weight": 0.25, "value": 0.8, "contrib": 0.20, "detail": "Consistent revenue growth"},
                                {"name": "Dividend", "weight": 0.2, "value": 0.7, "contrib": 0.14, "detail": "Regular dividend payments"},
                                {"name": "Volatility", "weight": 0.25, "value": 0.8, "contrib": 0.20, "detail": "Moderate price volatility"}
                            ],
                            "notes": ["Excellent choice for beginners due to strong fundamentals and market position"]
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
                        "beginnerFriendlyScore": 82,
                        "currentPrice": 350.75,
                        "beginnerScoreBreakdown": {
                            "score": 0.82,
                            "factors": [
                                {"name": "Stability", "weight": 0.3, "value": 0.85, "contrib": 0.255, "detail": "Dominant market position"},
                                {"name": "Growth", "weight": 0.25, "value": 0.75, "contrib": 0.1875, "detail": "Cloud business growth"},
                                {"name": "Dividend", "weight": 0.2, "value": 0.8, "contrib": 0.16, "detail": "Growing dividend yield"},
                                {"name": "Volatility", "weight": 0.25, "value": 0.8, "contrib": 0.20, "detail": "Stable price movement"}
                            ],
                            "notes": ["Strong cloud business and enterprise focus make it beginner-friendly"]
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
                        "beginnerFriendlyScore": 88,
                        "currentPrice": 165.50,
                        "beginnerScoreBreakdown": {
                            "score": 0.88,
                            "factors": [
                                {"name": "Stability", "weight": 0.3, "value": 0.95, "contrib": 0.285, "detail": "Defensive healthcare stock"},
                                {"name": "Growth", "weight": 0.25, "value": 0.7, "contrib": 0.175, "detail": "Steady long-term growth"},
                                {"name": "Dividend", "weight": 0.2, "value": 0.95, "contrib": 0.19, "detail": "High dividend yield"},
                                {"name": "Volatility", "weight": 0.25, "value": 0.9, "contrib": 0.225, "detail": "Low volatility"}
                            ],
                            "notes": ["Excellent defensive stock with high dividend yield"]
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
                        "unrealizedPL": 1025.00,
                        "unrealizedPLPercent": 7.33,
                        "currentPrice": 150.25,
                        "side": "long"
                    },
                    {
                        "id": "2",
                        "symbol": "MSFT",
                        "quantity": 50,
                        "marketValue": 17537.50,
                        "costBasis": 17000.00,
                        "unrealizedPL": 537.50,
                        "unrealizedPLPercent": 3.16,
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
    
    # Mock option orders
    if "optionOrders" in query:
        return {
            "data": {
                "optionOrders": [
                    {
                        "id": "1",
                        "symbol": "AAPL",
                        "optionType": "call",
                        "strike": 150.0,
                        "expiration": "2024-02-16",
                        "side": "buy",
                        "quantity": 1,
                        "orderType": "limit",
                        "limitPrice": 5.25,
                        "timeInForce": "GTC",
                        "status": "filled",
                        "filledPrice": 5.20,
                        "notes": "AAPL 150C 2/16/24",
                        "createdAt": "2024-01-15T10:30:00Z"
                    },
                    {
                        "id": "2",
                        "symbol": "TSLA",
                        "optionType": "put",
                        "strike": 200.0,
                        "expiration": "2024-03-15",
                        "side": "sell",
                        "quantity": 2,
                        "orderType": "market",
                        "limitPrice": None,
                        "timeInForce": "DAY",
                        "status": "pending",
                        "filledPrice": None,
                        "notes": "TSLA 200P 3/15/24",
                        "createdAt": "2024-01-15T11:15:00Z"
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
                    "beginnerFriendlyScore": 85,
                    "currentPrice": 150.25,
                    "beginnerScoreBreakdown": {
                        "score": 0.85,
                        "factors": [
                            {"name": "Stability", "weight": 0.3, "value": 0.9, "contrib": 0.27, "detail": "Large cap, stable business"},
                            {"name": "Growth", "weight": 0.25, "value": 0.8, "contrib": 0.2, "detail": "Consistent revenue growth"},
                            {"name": "Dividend", "weight": 0.2, "value": 0.7, "contrib": 0.14, "detail": "Regular dividend payments"},
                            {"name": "Volatility", "weight": 0.25, "value": 0.8, "contrib": 0.2, "detail": "Moderate price volatility"}
                        ],
                        "notes": ["Excellent choice for beginners due to strong fundamentals and market position"]
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
                        "notes": ["Strong cloud business and enterprise focus make it beginner-friendly"]
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
                    "beginnerFriendlyScore": 78,
                    "currentPrice": 142.50,
                    "beginnerScoreBreakdown": {
                        "score": 0.78,
                        "factors": [
                            {"name": "Stability", "weight": 0.3, "value": 0.8, "contrib": 0.24, "detail": "Search dominance"},
                            {"name": "Growth", "weight": 0.25, "value": 0.85, "contrib": 0.2125, "detail": "Strong revenue growth"},
                            {"name": "Dividend", "weight": 0.2, "value": 0.0, "contrib": 0.0, "detail": "No dividend"},
                            {"name": "Volatility", "weight": 0.25, "value": 0.7, "contrib": 0.175, "detail": "Higher volatility"}
                        ],
                        "notes": ["Growth stock with no dividend, suitable for growth-focused investors"]
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
                    "beginnerFriendlyScore": 65,
                    "currentPrice": 250.80,
                    "beginnerScoreBreakdown": {
                        "score": 0.65,
                        "factors": [
                            {"name": "Stability", "weight": 0.3, "value": 0.6, "contrib": 0.18, "detail": "Volatile stock"},
                            {"name": "Growth", "weight": 0.25, "value": 0.9, "contrib": 0.225, "detail": "High growth potential"},
                            {"name": "Dividend", "weight": 0.2, "value": 0.0, "contrib": 0.0, "detail": "No dividend"},
                            {"name": "Volatility", "weight": 0.25, "value": 0.5, "contrib": 0.125, "detail": "High volatility"}
                        ],
                        "notes": ["High-risk, high-reward growth stock"]
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
                    "beginnerFriendlyScore": 72,
                    "currentPrice": 155.40,
                    "beginnerScoreBreakdown": {
                        "score": 0.72,
                        "factors": [
                            {"name": "Stability", "weight": 0.3, "value": 0.75, "contrib": 0.225, "detail": "E-commerce leader"},
                            {"name": "Growth", "weight": 0.25, "value": 0.8, "contrib": 0.2, "detail": "Cloud and retail growth"},
                            {"name": "Dividend", "weight": 0.2, "value": 0.0, "contrib": 0.0, "detail": "No dividend"},
                            {"name": "Volatility", "weight": 0.25, "value": 0.7, "contrib": 0.175, "detail": "Moderate volatility"}
                        ],
                        "notes": ["Diversified business model with strong growth prospects"]
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
    
    # Mock day trading picks
    if "dayTradingPicks" in query:
        mode = body.get("variables", {}).get("mode", "SAFE")
        return {
            "data": {
                "dayTradingPicks": {
                    "as_of": "2024-01-15T10:30:00Z",
                    "mode": mode,
                    "picks": [
                        {
                            "symbol": "AAPL",
                            "side": "BUY" if mode == "AGGRESSIVE" else "HOLD",
                            "score": 85,
                            "features": {
                                "momentum_15m": 0.15,
                                "rvol_10m": 1.2,
                                "vwap_dist": 0.02,
                                "breakout_pct": 0.05,
                                "spread_bps": 2.5,
                                "catalyst_score": 0.8
                            },
                            "risk": {
                                "atr_5m": 2.5,
                                "size_shares": 100,
                                "stop": 145.00,
                                "targets": [155.00, 158.50],
                                "time_stop_min": 30
                            },
                            "notes": "Strong technical indicators with momentum"
                        },
                        {
                            "symbol": "MSFT",
                            "side": "BUY",
                            "score": 78,
                            "features": {
                                "momentum_15m": 0.12,
                                "rvol_10m": 1.1,
                                "vwap_dist": 0.01,
                                "breakout_pct": 0.03,
                                "spread_bps": 1.8,
                                "catalyst_score": 0.7
                            },
                            "risk": {
                                "atr_5m": 3.2,
                                "size_shares": 80,
                                "stop": 340.00,
                                "targets": [365.00, 370.00],
                                "time_stop_min": 45
                            },
                            "notes": "Cloud growth momentum with strong fundamentals"
                        }
                    ],
                    "universe_size": 500,
                    "quality_threshold": 0.7
                }
            }
        }
    
    # Mock risk management data
    if "riskSummary" in query:
        return {
            "data": {
                "riskSummary": {
                    "account_value": 10000.0,
                    "daily_pnl": 125.50,
                    "daily_pnl_pct": 1.26,
                    "daily_trades": 3,
                    "active_positions": 2,
                    "total_exposure": 2500.0,
                    "exposure_pct": 25.0,
                    "sector_exposure": {
                        "Technology": 60.0,
                        "Healthcare": 25.0,
                        "Finance": 15.0
                    },
                    "risk_level": "MODERATE",
                    "risk_limits": {
                        "max_position_size": 1000.0,
                        "max_daily_loss": 200.0,
                        "max_concurrent_trades": 5,
                        "max_sector_exposure": 50.0
                    }
                }
            }
        }
    
    # Mock active positions data
    if "getActivePositions" in query:
        return {
            "data": {
                "getActivePositions": [
                    {
                        "symbol": "AAPL",
                        "side": "LONG",
                        "entryPrice": 150.25,
                        "quantity": 10,
                        "entryTime": "2024-01-15T09:30:00Z",
                        "stopLossPrice": 145.00,
                        "takeProfitPrice": 160.00,
                        "maxHoldUntil": "2024-01-15T16:00:00Z",
                        "atrStopPrice": 144.50,
                        "currentPnl": 25.50,
                        "timeRemainingMinutes": 180
                    },
                    {
                        "symbol": "MSFT",
                        "side": "LONG",
                        "entryPrice": 350.75,
                        "quantity": 5,
                        "entryTime": "2024-01-15T10:15:00Z",
                        "stopLossPrice": 340.00,
                        "takeProfitPrice": 370.00,
                        "maxHoldUntil": "2024-01-15T16:00:00Z",
                        "atrStopPrice": 338.25,
                        "currentPnl": 12.25,
                        "timeRemainingMinutes": 165
                    }
                ]
            }
        }
    
    # Mock watchlist data
    if "myWatchlist" in query:
        return {
            "data": {
                "myWatchlist": [
                    {
                        "id": "1",
                        "addedAt": "2024-01-15T10:30:00Z",
                        "notes": "Strong fundamentals and growth potential",
                        "targetPrice": 165.00,
                        "stock": {
                            "id": "1",
                            "symbol": "AAPL",
                            "companyName": "Apple Inc.",
                            "sector": "Technology",
                            "currentPrice": 150.25,
                            "change": 2.15,
                            "changePercent": 1.45,
                            "beginnerFriendlyScore": 85
                        }
                    },
                    {
                        "id": "2",
                        "addedAt": "2024-01-14T15:20:00Z",
                        "notes": "Cloud business momentum",
                        "targetPrice": 375.00,
                        "stock": {
                            "id": "2",
                            "symbol": "MSFT",
                            "companyName": "Microsoft Corporation",
                            "sector": "Technology",
                            "currentPrice": 350.75,
                            "change": 5.30,
                            "changePercent": 1.53,
                            "beginnerFriendlyScore": 82
                        }
                    }
                ]
            }
        }
    
    # Mock portfolio data
    if "myPortfolios" in query:
        return {
            "data": {
                "myPortfolios": {
                    "totalPortfolios": 2,
                    "totalValue": 5621.90,
                    "portfolios": [
                        {
                            "name": "Growth Portfolio",
                            "totalValue": 3500.00,
                            "holdingsCount": 2,
                            "holdings": [
                                {
                                    "id": "1",
                                    "stock": {
                                        "id": "1",
                                        "symbol": "AAPL",
                                        "companyName": "Apple Inc."
                                    },
                                    "shares": 20,
                                    "averagePrice": 140.00,
                                    "currentPrice": 150.25,
                                    "totalValue": 3005.00,
                                    "notes": "Strong growth potential",
                                    "createdAt": "2024-01-15T10:30:00Z",
                                    "updatedAt": "2024-01-15T10:30:00Z"
                                },
                                {
                                    "id": "2",
                                    "stock": {
                                        "id": "2",
                                        "symbol": "MSFT",
                                        "companyName": "Microsoft Corporation"
                                    },
                                    "shares": 5,
                                    "averagePrice": 340.00,
                                    "currentPrice": 350.75,
                                    "totalValue": 1753.75,
                                    "notes": "Cloud business growth",
                                    "createdAt": "2024-01-15T10:30:00Z",
                                    "updatedAt": "2024-01-15T10:30:00Z"
                                }
                            ]
                        },
                        {
                            "name": "Conservative Portfolio",
                            "totalValue": 2121.90,
                            "holdingsCount": 2,
                            "holdings": [
                                {
                                    "id": "3",
                                    "stock": {
                                        "id": "3",
                                        "symbol": "JNJ",
                                        "companyName": "Johnson & Johnson"
                                    },
                                    "shares": 10,
                                    "averagePrice": 160.00,
                                    "currentPrice": 165.50,
                                    "totalValue": 1655.00,
                                    "notes": "Stable dividend stock",
                                    "createdAt": "2024-01-15T10:30:00Z",
                                    "updatedAt": "2024-01-15T10:30:00Z"
                                },
                                {
                                    "id": "4",
                                    "stock": {
                                        "id": "4",
                                        "symbol": "VTI",
                                        "companyName": "Vanguard Total Stock Market ETF"
                                    },
                                    "shares": 5,
                                    "averagePrice": 90.00,
                                    "currentPrice": 93.38,
                                    "totalValue": 466.90,
                                    "notes": "Broad market exposure",
                                    "createdAt": "2024-01-15T10:30:00Z",
                                    "updatedAt": "2024-01-15T10:30:00Z"
                                }
                            ]
                        }
                    ],
                    "marketOutlook": {
                        "overallSentiment": "Bullish",
                        "confidence": 0.78,
                        "keyFactors": [
                            "Strong earnings growth",
                            "Low interest rates",
                            "Technology sector momentum",
                            "Consumer spending resilience"
                        ]
                    }
                }
            }
        }
    
    # Mock stock discussions
    if "stockDiscussions" in query:
        print(f"🎯 DEBUG: Matched stockDiscussions query: {query[:100]}...")
        return {
            "data": {
                "stockDiscussions": [
                    {
                        "id": "1",
                        "title": "AAPL Earnings Discussion",
                        "content": "What do you think about Apple's latest earnings?",
                        "createdAt": "2024-01-15T10:30:00Z",
                        "score": 15,
                        "commentCount": 8,
                        "user": {
                            "id": "1",
                            "name": "Test User",
                            "email": "test@example.com"
                        },
                        "stock": {
                            "symbol": "AAPL",
                            "companyName": "Apple Inc."
                        },
                        "comments": [
                            {
                                "id": "1",
                                "content": "Great results!",
                                "createdAt": "2024-01-15T11:00:00Z",
                                "user": {
                                    "name": "Investor123"
                                }
                            }
                        ]
                    },
                    {
                        "id": "2",
                        "title": "MSFT Cloud Growth",
                        "content": "Microsoft's cloud business continues to impress",
                        "createdAt": "2024-01-15T09:15:00Z",
                        "score": 12,
                        "commentCount": 5,
                        "user": {
                            "id": "2",
                            "name": "CloudExpert",
                            "email": "cloud@example.com"
                        },
                        "stock": {
                            "symbol": "MSFT",
                            "companyName": "Microsoft Corporation"
                        },
                        "comments": [
                            {
                                "id": "2",
                                "content": "Azure is killing it!",
                                "createdAt": "2024-01-15T09:30:00Z",
                                "user": {
                                    "name": "TechAnalyst"
                                }
                            }
                        ]
                    }
                ]
            }
        }
    
    # Mock available benchmarks
    if "availableBenchmarks" in query:
        return {
            "data": {
                "availableBenchmarks": ["SPY", "QQQ", "DIA", "VTI", "IWM"]
            }
        }
    
    # Mock benchmark series data
    if "benchmarkSeries" in query:
        symbol = body.get("variables", {}).get("symbol", "SPY")
        timeframe = body.get("variables", {}).get("timeframe", "3M")
        
        # Generate mock benchmark data
        base_price = {"SPY": 450.00, "QQQ": 380.00, "DIA": 350.00, "VTI": 240.00, "IWM": 200.00}.get(symbol, 450.00)
        
        # Generate benchmark names
        benchmark_names = {
            "SPY": "SPDR S&P 500 ETF Trust",
            "QQQ": "Invesco QQQ Trust",
            "DIA": "SPDR Dow Jones Industrial Average ETF",
            "VTI": "Vanguard Total Stock Market ETF",
            "IWM": "iShares Russell 2000 ETF"
        }
        
        return {
            "data": {
                "benchmarkSeries": {
                    "symbol": symbol,
                    "name": benchmark_names.get(symbol, f"{symbol} Benchmark"),
                    "timeframe": timeframe,
                    "totalReturn": base_price * 0.05,  # 5% total return
                    "totalReturnPercent": 5.0,
                    "volatility": 0.18,
                    "startValue": base_price * 0.95,  # Starting value
                    "endValue": base_price,  # Ending value
                    "data": [
                        {"timestamp": "2024-01-15T16:00:00Z", "value": base_price, "return": 0.0, "returnPercent": 0.0},
                        {"timestamp": "2024-01-14T16:00:00Z", "value": base_price * 0.99, "return": -base_price * 0.01, "returnPercent": -1.0},
                        {"timestamp": "2024-01-13T16:00:00Z", "value": base_price * 1.01, "return": base_price * 0.01, "returnPercent": 1.0}
                    ],
                    "dataPoints": [
                        {"timestamp": "2024-01-15T16:00:00Z", "value": base_price, "change": 0.0, "changePercent": 0.0},
                        {"timestamp": "2024-01-14T16:00:00Z", "value": base_price * 0.99, "change": -base_price * 0.01, "changePercent": -1.0},
                        {"timestamp": "2024-01-13T16:00:00Z", "value": base_price * 1.01, "change": base_price * 0.01, "changePercent": 1.0},
                        {"timestamp": "2024-01-12T16:00:00Z", "value": base_price * 0.98, "change": -base_price * 0.02, "changePercent": -2.0},
                        {"timestamp": "2024-01-11T16:00:00Z", "value": base_price * 1.02, "change": base_price * 0.02, "changePercent": 2.0}
                    ]
                }
            }
        }
    
    # Mock advanced stock screening
    if "advancedStockScreening" in query:
        return {
            "data": {
                "advancedStockScreening": [
                    {
                        "symbol": "AAPL",
                        "companyName": "Apple Inc.",
                        "sector": "Technology",
                        "peRatio": 28.5,
                        "dividendYield": 0.44,
                        "marketCap": 3000000000000,
                        "mlScore": 0.85,
                        "technicalScore": 0.78,
                        "fundamentalScore": 0.92,
                        "sentimentScore": 0.75,
                        "beginnerFriendlyScore": 85,
                        "volatility": 0.22,
                        "debtRatio": 0.15,
                        "score": 0.85,
                        "reasoning": "Strong fundamentals with excellent brand value and consistent growth",
                        "currentPrice": 150.25,
                        "change": 2.15,
                        "changePercent": 1.45
                    },
                    {
                        "symbol": "MSFT",
                        "companyName": "Microsoft Corporation",
                        "sector": "Technology",
                        "peRatio": 32.1,
                        "dividendYield": 0.68,
                        "marketCap": 2800000000000,
                        "mlScore": 0.82,
                        "technicalScore": 0.85,
                        "fundamentalScore": 0.88,
                        "sentimentScore": 0.80,
                        "beginnerFriendlyScore": 82,
                        "volatility": 0.18,
                        "debtRatio": 0.12,
                        "score": 0.82,
                        "reasoning": "Cloud business dominance with strong enterprise focus",
                        "currentPrice": 350.75,
                        "change": 5.30,
                        "changePercent": 1.53
                    },
                    {
                        "symbol": "GOOGL",
                        "companyName": "Alphabet Inc.",
                        "sector": "Technology",
                        "peRatio": 25.8,
                        "dividendYield": 0.0,
                        "marketCap": 1800000000000,
                        "mlScore": 0.78,
                        "technicalScore": 0.72,
                        "fundamentalScore": 0.85,
                        "sentimentScore": 0.70,
                        "beginnerFriendlyScore": 78,
                        "volatility": 0.25,
                        "debtRatio": 0.08,
                        "score": 0.78,
                        "reasoning": "Search dominance with strong AI and cloud growth potential",
                        "currentPrice": 142.50,
                        "change": -1.25,
                        "changePercent": -0.87
                    }
                ]
            }
        }
    
    # Mock Rust stock analysis
    if "rustStockAnalysis" in query:
        symbol = body.get("variables", {}).get("symbol", "AAPL")
        return {
            "data": {
                "rustStockAnalysis": {
                    "symbol": symbol,
                    "beginnerFriendlyScore": 85,
                    "riskLevel": "MODERATE",
                    "recommendation": "BUY",
                    "technicalIndicators": {
                        "rsi": 58.5,
                        "macd": 1.25,
                        "macdSignal": 1.15,
                        "macdHistogram": 0.10,
                        "bollingerPosition": 0.65,
                        "bollingerUpper": 160.0,
                        "bollingerLower": 140.0,
                        "bollingerMiddle": 150.0,
                        "sma20": 148.5,
                        "sma50": 145.0,
                        "ema12": 149.0,
                        "ema26": 147.0,
                        "support": 145.00,
                        "resistance": 155.00,
                        "trend": "Bullish"
                    },
                    "fundamentalAnalysis": {
                        "peRatio": 28.5,
                        "pbRatio": 5.2,
                        "debtToEquity": 0.15,
                        "roe": 0.25,
                        "revenueGrowth": 0.08,
                        "earningsGrowth": 0.12,
                        "debtScore": 85.0,
                        "valuationScore": 78.0,
                        "growthScore": 82.0,
                        "stabilityScore": 88.0,
                        "dividendScore": 72.0
                    },
                    "reasoning": "Strong technical indicators show bullish momentum with RSI in healthy range. Fundamentals are solid with consistent revenue growth and low debt. ML models predict continued upward movement with high confidence.",
                    "analysis": {
                        "technical": {
                            "rsi": 58.5,
                            "macd": 1.25,
                            "bollingerPosition": 0.65,
                            "support": 145.00,
                            "resistance": 155.00,
                            "trend": "Bullish"
                        },
                        "fundamental": {
                            "peRatio": 28.5,
                            "pbRatio": 5.2,
                            "debtToEquity": 0.15,
                            "roe": 0.25,
                            "revenueGrowth": 0.08,
                            "earningsGrowth": 0.12
                        },
                        "sentiment": {
                            "analystRating": "Buy",
                            "priceTarget": 165.00,
                            "upside": 0.098,
                            "newsSentiment": 0.75,
                            "socialSentiment": 0.68
                        },
                        "ml": {
                            "prediction": 158.50,
                            "confidence": 0.82,
                            "volatility": 0.22,
                            "riskScore": 0.35,
                            "recommendation": "BUY"
                        }
                    },
                    "timestamp": "2024-01-15T10:30:00Z"
                }
            }
        }
    
    # Mock crypto ML signal
    if "cryptoMlSignal" in query:
        symbol = body.get("variables", {}).get("symbol", "BTC")
        
        # Generate mock crypto ML signal data
        crypto_signals = {
            "BTC": {
                "probability": 0.75,
                "confidenceLevel": "HIGH",
                "explanation": "Strong bullish momentum with increasing institutional adoption and positive market sentiment",
                "features": ["price_momentum", "volume_spike", "sentiment_positive", "institutional_flow"],
                "modelVersion": "v2.1.3"
            },
            "ETH": {
                "probability": 0.68,
                "confidenceLevel": "MEDIUM",
                "explanation": "Moderate bullish signal with DeFi activity increasing and network upgrades",
                "features": ["defi_activity", "network_upgrades", "gas_fees", "staking_rewards"],
                "modelVersion": "v2.1.3"
            },
            "SOL": {
                "probability": 0.82,
                "confidenceLevel": "HIGH",
                "explanation": "Very strong bullish signal with ecosystem growth and developer activity",
                "features": ["ecosystem_growth", "developer_activity", "nft_volume", "defi_tvl"],
                "modelVersion": "v2.1.3"
            }
        }
        
        signal_data = crypto_signals.get(symbol, {
            "probability": 0.55,
            "confidenceLevel": "LOW",
            "explanation": "Neutral signal with mixed market indicators",
            "features": ["price_volatility", "market_sentiment"],
            "modelVersion": "v2.1.3"
        })
        
        return {
            "data": {
                "cryptoMlSignal": {
                    "symbol": symbol,
                    "probability": signal_data["probability"],
                    "confidenceLevel": signal_data["confidenceLevel"],
                    "explanation": signal_data["explanation"],
                    "features": signal_data["features"],
                    "modelVersion": signal_data["modelVersion"],
                    "timestamp": "2024-01-15T10:30:00Z"
                }
            }
        }
    
    # Mock crypto portfolio
    if "cryptoPortfolio" in query:
        return {
            "data": {
                "cryptoPortfolio": {
                    "id": "1",
                    "totalValueUsd": 12500.00,
                    "totalCostBasis": 10000.00,
                    "totalPnl": 2500.00,
                    "totalPnlPercentage": 25.0,
                    "holdings": [
                        {
                            "id": "1",
                            "cryptocurrency": {
                                "symbol": "BTC",
                                "name": "Bitcoin",
                                "iconUrl": "https://cryptologos.cc/logos/bitcoin-btc-logo.png"
                            },
                            "quantity": 0.5,
                            "valueUsd": 20000.00,
                            "costBasis": 15000.00,
                            "pnl": 5000.00,
                            "pnlPercentage": 33.33
                        },
                        {
                            "id": "2",
                            "cryptocurrency": {
                                "symbol": "ETH",
                                "name": "Ethereum",
                                "iconUrl": "https://cryptologos.cc/logos/ethereum-eth-logo.png"
                            },
                            "quantity": 2.0,
                            "valueUsd": 4000.00,
                            "costBasis": 3500.00,
                            "pnl": 500.00,
                            "pnlPercentage": 14.29
                        },
                        {
                            "id": "3",
                            "cryptocurrency": {
                                "symbol": "SOL",
                                "name": "Solana",
                                "iconUrl": "https://cryptologos.cc/logos/solana-sol-logo.png"
                            },
                            "quantity": 50.0,
                            "valueUsd": 5000.00,
                            "costBasis": 4500.00,
                            "pnl": 500.00,
                            "pnlPercentage": 11.11
                        }
                    ]
                }
            }
        }
    
    # Mock crypto price data
    if "cryptoPrice" in query:
        symbol = body.get("variables", {}).get("symbol", "BTC")
        
        # Generate mock crypto price data based on symbol
        crypto_prices = {
            "BTC": {
                "id": "btc_price",
                "priceUsd": 45000.00,
                "priceBtc": 1.0,
                "volume24h": 25000000000,
                "marketCap": 850000000000,
                "priceChange24h": 1250.00,
                "priceChangePercentage24h": 2.85,
                "rsi14": 65.2,
                "volatility7d": 0.15,
                "volatility30d": 0.28,
                "momentumScore": 0.75,
                "sentimentScore": 0.68,
                "timestamp": "2024-01-15T10:30:00Z"
            },
            "ETH": {
                "id": "eth_price",
                "priceUsd": 2800.00,
                "priceBtc": 0.062,
                "volume24h": 12000000000,
                "marketCap": 340000000000,
                "priceChange24h": -45.00,
                "priceChangePercentage24h": -1.58,
                "rsi14": 42.8,
                "volatility7d": 0.18,
                "volatility30d": 0.32,
                "momentumScore": 0.45,
                "sentimentScore": 0.52,
                "timestamp": "2024-01-15T10:30:00Z"
            },
            "SOL": {
                "id": "sol_price",
                "priceUsd": 95.50,
                "priceBtc": 0.0021,
                "volume24h": 800000000,
                "marketCap": 42000000000,
                "priceChange24h": 3.25,
                "priceChangePercentage24h": 3.52,
                "rsi14": 58.7,
                "volatility7d": 0.22,
                "volatility30d": 0.45,
                "momentumScore": 0.68,
                "sentimentScore": 0.71,
                "timestamp": "2024-01-15T10:30:00Z"
            }
        }
        
        # Default to BTC if symbol not found
        price_data = crypto_prices.get(symbol.upper(), crypto_prices["BTC"])
        
        return {
            "data": {
                "cryptoPrice": price_data
            }
        }
    
    # Mock supported currencies
    if "supportedCurrencies" in query:
        return {
            "data": {
                "supportedCurrencies": [
                    {
                        "symbol": "BTC",
                        "name": "Bitcoin",
                        "iconUrl": "https://cryptologos.cc/logos/bitcoin-btc-logo.png",
                        "decimals": 8,
                        "priceDecimals": 2
                    },
                    {
                        "symbol": "ETH",
                        "name": "Ethereum",
                        "iconUrl": "https://cryptologos.cc/logos/ethereum-eth-logo.png",
                        "decimals": 18,
                        "priceDecimals": 2
                    },
                    {
                        "symbol": "SOL",
                        "name": "Solana",
                        "iconUrl": "https://cryptologos.cc/logos/solana-sol-logo.png",
                        "decimals": 9,
                        "priceDecimals": 2
                    },
                    {
                        "symbol": "ADA",
                        "name": "Cardano",
                        "iconUrl": "https://cryptologos.cc/logos/cardano-ada-logo.png",
                        "decimals": 6,
                        "priceDecimals": 4
                    },
                    {
                        "symbol": "DOT",
                        "name": "Polkadot",
                        "iconUrl": "https://cryptologos.cc/logos/polkadot-new-dot-logo.png",
                        "decimals": 10,
                        "priceDecimals": 2
                    }
                ]
            }
        }
    
    # Mock quotes data
    if "quotes" in query:
        symbols = body.get("variables", {}).get("symbols", ["AAPL", "MSFT"])
        quotes = []
        for symbol in symbols:
            quotes.append({
                "symbol": symbol,
                "last": 150.25 if symbol == "AAPL" else 350.75,
                "change": 2.50 if symbol == "AAPL" else -1.25,
                "changePercent": 1.69 if symbol == "AAPL" else -0.35,
                "changePct": 1.69 if symbol == "AAPL" else -0.35
            })
        return {
            "data": {
                "quotes": quotes
            }
        }
    
    # Mock bank accounts data
    if "bankAccounts" in query:
        return {
            "data": {
                "bankAccounts": [
                    {
                        "id": "1",
                        "bankName": "Chase Bank",
                        "accountType": "CHECKING",
                        "accountNumber": "****1234",
                        "lastFour": "1234",
                        "routingNumber": "021000021",
                        "balance": 5000.00,
                        "isVerified": True,
                        "isPrimary": True,
                        "createdAt": "2024-01-15T10:30:00Z",
                        "linkedAt": "2024-01-15T10:30:00Z"
                    },
                    {
                        "id": "2",
                        "bankName": "Bank of America",
                        "accountType": "SAVINGS",
                        "accountNumber": "****5678",
                        "lastFour": "5678",
                        "routingNumber": "026009593",
                        "balance": 15000.00,
                        "isVerified": True,
                        "isPrimary": False,
                        "createdAt": "2024-01-15T10:30:00Z",
                        "linkedAt": "2024-01-15T10:30:00Z"
                    }
                ]
            }
        }
    
    # Mock funding history data
    if "fundingHistory" in query:
        return {
            "data": {
                "fundingHistory": [
                    {
                        "id": "1",
                        "type": "DEPOSIT",
                        "amount": 1000.00,
                        "status": "COMPLETED",
                        "method": "BANK_TRANSFER",
                        "bankAccountId": "1",
                        "bankAccount": {
                            "bankName": "Chase Bank",
                            "accountNumber": "****1234"
                        },
                        "createdAt": "2024-01-15T10:30:00Z",
                        "initiatedAt": "2024-01-15T10:30:00Z",
                        "completedAt": "2024-01-15T10:35:00Z"
                    },
                    {
                        "id": "2",
                        "type": "WITHDRAWAL",
                        "amount": 500.00,
                        "status": "PENDING",
                        "method": "BANK_TRANSFER",
                        "bankAccountId": "1",
                        "bankAccount": {
                            "bankName": "Chase Bank",
                            "accountNumber": "****1234"
                        },
                        "createdAt": "2024-01-15T11:00:00Z",
                        "initiatedAt": "2024-01-15T11:00:00Z",
                        "completedAt": None
                    }
                ]
            }
        }
    
    # Mock SBLOC offer data
    if "sblocOffer" in query:
        return {
            "data": {
                "sblocOffer": {
                    "id": "1",
                    "availableCredit": 25000.00,
                    "interestRate": 0.035,
                    "apr": 0.035,
                    "maxLoanAmount": 50000.00,
                    "collateralValue": 75000.00,
                    "loanToValueRatio": 0.67,
                    "ltv": 0.67,
                    "minDraw": 1000.00,
                    "maxDrawMultiplier": 0.67,
                    "eligibleEquity": 75000.00,
                    "status": "AVAILABLE",
                    "terms": {
                        "minLoanAmount": 1000.00,
                        "maxLoanAmount": 50000.00,
                        "interestRate": 0.035,
                        "termLength": "OPEN_ENDED",
                        "paymentFrequency": "MONTHLY"
                    },
                    "eligibility": {
                        "isEligible": True,
                        "requirements": [
                            "Minimum portfolio value of $25,000",
                            "Account in good standing",
                            "No recent margin calls"
                        ]
                    },
                    "disclosures": [
                        "Securities-based line of credit involves risk of loss",
                        "Interest rates may vary based on market conditions",
                        "Collateral requirements may change",
                        "Early repayment may incur fees"
                    ],
                    "createdAt": "2024-01-15T10:30:00Z",
                    "updatedAt": "2024-01-15T10:30:00Z",
                    "expiresAt": "2024-02-15T10:30:00Z"
                }
            }
        }
    
    # Mock SBLOC banks data
    if "sblocBanks" in query:
        return {
            "data": {
                "sblocBanks": [
                    {
                        "id": "1",
                        "name": "Chase Bank",
                        "logo": "https://example.com/chase-logo.png",
                        "logoUrl": "https://example.com/chase-logo.png",
                        "interestRate": 0.035,
                        "apr": 0.035,
                        "minApr": 0.030,
                        "maxApr": 0.040,
                        "maxLoanAmount": 50000.00,
                        "minLoanAmount": 1000.00,
                        "minLoanUsd": 1000.00,
                        "loanToValueRatio": 0.67,
                        "ltv": 0.67,
                        "minLtv": 0.50,
                        "maxLtv": 0.75,
                        "minDraw": 1000.00,
                        "maxDrawMultiplier": 0.67,
                        "eligibleEquity": 75000.00,
                        "status": "AVAILABLE",
                        "isEligible": True,
                        "requirements": [
                            "Minimum portfolio value of $25,000",
                            "Account in good standing",
                            "No recent margin calls"
                        ],
                        "disclosures": [
                            "Securities-based line of credit involves risk of loss",
                            "Interest rates may vary based on market conditions",
                            "Collateral requirements may change",
                            "Early repayment may incur fees"
                        ],
                        "notes": [
                            "Competitive rates for qualified borrowers",
                            "Quick approval process",
                            "Flexible repayment options"
                        ],
                        "regions": ["US", "CA"],
                        "createdAt": "2024-01-15T10:30:00Z",
                        "updatedAt": "2024-01-15T10:30:00Z"
                    },
                    {
                        "id": "2",
                        "name": "Bank of America",
                        "logo": "https://example.com/bofa-logo.png",
                        "logoUrl": "https://example.com/bofa-logo.png",
                        "interestRate": 0.038,
                        "apr": 0.038,
                        "minApr": 0.035,
                        "maxApr": 0.045,
                        "maxLoanAmount": 75000.00,
                        "minLoanAmount": 2000.00,
                        "minLoanUsd": 2000.00,
                        "loanToValueRatio": 0.70,
                        "ltv": 0.70,
                        "minLtv": 0.55,
                        "maxLtv": 0.80,
                        "minDraw": 2000.00,
                        "maxDrawMultiplier": 0.70,
                        "eligibleEquity": 100000.00,
                        "status": "AVAILABLE",
                        "isEligible": True,
                        "requirements": [
                            "Minimum portfolio value of $50,000",
                            "Account in good standing",
                            "No recent margin calls",
                            "Minimum credit score of 700"
                        ],
                        "disclosures": [
                            "Securities-based line of credit involves risk of loss",
                            "Interest rates may vary based on market conditions",
                            "Collateral requirements may change",
                            "Early repayment may incur fees"
                        ],
                        "notes": [
                            "Higher loan amounts available",
                            "Premium customer benefits",
                            "Dedicated relationship manager"
                        ],
                        "regions": ["US"],
                        "createdAt": "2024-01-15T10:30:00Z",
                        "updatedAt": "2024-01-15T10:30:00Z"
                    },
                    {
                        "id": "3",
                        "name": "Wells Fargo",
                        "logo": "https://example.com/wells-logo.png",
                        "logoUrl": "https://example.com/wells-logo.png",
                        "interestRate": 0.040,
                        "apr": 0.040,
                        "minApr": 0.038,
                        "maxApr": 0.050,
                        "maxLoanAmount": 100000.00,
                        "minLoanAmount": 5000.00,
                        "minLoanUsd": 5000.00,
                        "loanToValueRatio": 0.65,
                        "ltv": 0.65,
                        "minLtv": 0.50,
                        "maxLtv": 0.70,
                        "minDraw": 5000.00,
                        "maxDrawMultiplier": 0.65,
                        "eligibleEquity": 150000.00,
                        "status": "AVAILABLE",
                        "isEligible": False,
                        "requirements": [
                            "Minimum portfolio value of $100,000",
                            "Account in good standing",
                            "No recent margin calls",
                            "Minimum credit score of 750"
                        ],
                        "disclosures": [
                            "Securities-based line of credit involves risk of loss",
                            "Interest rates may vary based on market conditions",
                            "Collateral requirements may change",
                            "Early repayment may incur fees"
                        ],
                        "notes": [
                            "Premium tier service",
                            "Highest loan amounts available",
                            "Strict eligibility requirements"
                        ],
                        "regions": ["US"],
                        "createdAt": "2024-01-15T10:30:00Z",
                        "updatedAt": "2024-01-15T10:30:00Z"
                    }
                ]
            }
        }
    
    # Mock notifications data
    if "notifications" in query:
        return {
            "data": {
                "notifications": [
                    {
                        "id": "1",
                        "type": "PORTFOLIO_ALERT",
                        "title": "Portfolio Performance Alert",
                        "message": "Your portfolio has gained 5.2% this week",
                        "isRead": False,
                        "priority": "MEDIUM",
                        "createdAt": "2024-01-15T14:30:00Z",
                        "actionUrl": "/portfolio",
                        "data": {
                            "portfolioId": "1",
                            "gainPercent": 5.2,
                            "totalValue": 5621.90,
                            "previousValue": 5340.00
                        },
                        "metadata": {
                            "portfolioId": "1",
                            "gainPercent": 5.2
                        }
                    },
                    {
                        "id": "2",
                        "type": "MARKET_UPDATE",
                        "title": "Market Update",
                        "message": "S&P 500 is up 1.2% today",
                        "isRead": True,
                        "priority": "LOW",
                        "createdAt": "2024-01-15T13:15:00Z",
                        "actionUrl": "/market",
                        "data": {
                            "index": "SPY",
                            "change": 1.2,
                            "currentPrice": 4850.25,
                            "previousPrice": 4792.50
                        },
                        "metadata": {
                            "index": "SPY",
                            "change": 1.2
                        }
                    },
                    {
                        "id": "3",
                        "type": "TRADE_CONFIRMATION",
                        "title": "Trade Executed",
                        "message": "Successfully bought 10 shares of AAPL at $150.25",
                        "isRead": False,
                        "priority": "HIGH",
                        "createdAt": "2024-01-15T12:45:00Z",
                        "actionUrl": "/trades",
                        "data": {
                            "symbol": "AAPL",
                            "shares": 10,
                            "price": 150.25,
                            "orderId": "ORD-12345",
                            "totalValue": 1502.50,
                            "orderType": "BUY"
                        },
                        "metadata": {
                            "symbol": "AAPL",
                            "shares": 10,
                            "price": 150.25,
                            "orderId": "ORD-12345"
                        }
                    },
                    {
                        "id": "4",
                        "type": "AI_RECOMMENDATION",
                        "title": "New AI Recommendation",
                        "message": "AI suggests rebalancing your portfolio",
                        "isRead": False,
                        "priority": "MEDIUM",
                        "createdAt": "2024-01-15T11:20:00Z",
                        "actionUrl": "/ai-recommendations",
                        "data": {
                            "recommendationId": "REC-67890",
                            "action": "REBALANCE",
                            "confidence": 0.85,
                            "expectedImpact": 0.12
                        },
                        "metadata": {
                            "recommendationId": "REC-67890",
                            "action": "REBALANCE"
                        }
                    },
                    {
                        "id": "5",
                        "type": "ACCOUNT_UPDATE",
                        "title": "Account Verification Complete",
                        "message": "Your bank account has been successfully verified",
                        "isRead": True,
                        "priority": "LOW",
                        "createdAt": "2024-01-15T10:00:00Z",
                        "actionUrl": "/banking",
                        "data": {
                            "accountId": "ACC-11111",
                            "bankName": "Chase Bank",
                            "accountType": "CHECKING",
                            "verificationDate": "2024-01-15T10:00:00Z"
                        },
                        "metadata": {
                            "accountId": "ACC-11111",
                            "bankName": "Chase Bank"
                        }
                    }
                ]
            }
        }
    
    # Mock notification settings data
    if "notificationSettings" in query:
        return {
            "data": {
                "notificationSettings": {
                    "id": "1",
                    "userId": "1",
                    "emailNotifications": {
                        "enabled": True,
                        "portfolioAlerts": True,
                        "marketUpdates": True,
                        "tradeConfirmations": True,
                        "aiRecommendations": True,
                        "accountUpdates": True,
                        "weeklyDigest": True,
                        "priceAlerts": True,
                        "orderUpdates": True,
                        "newsUpdates": True,
                        "systemUpdates": True,
                        "frequency": "IMMEDIATE"
                    },
                    "pushNotifications": {
                        "enabled": True,
                        "portfolioAlerts": True,
                        "marketUpdates": False,
                        "tradeConfirmations": True,
                        "aiRecommendations": True,
                        "accountUpdates": False,
                        "priceAlerts": True,
                        "orderUpdates": True,
                        "newsUpdates": False,
                        "systemUpdates": False,
                        "quietHours": {
                            "enabled": True,
                            "startTime": "22:00",
                            "endTime": "08:00",
                            "timezone": "America/New_York"
                        }
                    },
                    "smsNotifications": {
                        "enabled": False,
                        "portfolioAlerts": False,
                        "tradeConfirmations": False,
                        "accountUpdates": False,
                        "priceAlerts": False,
                        "orderUpdates": False,
                        "newsUpdates": False,
                        "systemUpdates": False,
                        "phoneNumber": None
                    },
                    "preferences": {
                        "portfolioThreshold": 5.0,
                        "marketThreshold": 2.0,
                        "aiRecommendationThreshold": "MEDIUM",
                        "language": "en",
                        "timezone": "America/New_York"
                    },
                    "createdAt": "2024-01-15T10:30:00Z",
                    "updatedAt": "2024-01-15T10:30:00Z"
                }
            }
        }
    
    # Mock create income profile mutation
    if "createIncomeProfile" in query:
        variables = body.get("variables", {})
        income_bracket = variables.get("incomeBracket", "Under $30,000")
        age = variables.get("age", 28)
        investment_goals = variables.get("investmentGoals", ["Emergency Fund", "Wealth Building"])
        risk_tolerance = variables.get("riskTolerance", "Moderate")
        investment_horizon = variables.get("investmentHorizon", "5-10 years")
        
        return {
            "data": {
                "createIncomeProfile": {
                    "success": True,
                    "message": f"Income profile created successfully for {age}-year-old with {income_bracket} income, {risk_tolerance} risk tolerance, and {investment_horizon} investment horizon."
                }
            }
        }
    
    # Mock volatility data
    if "volatilityData" in query:
        return {
            "data": {
                "volatilityData": {
                    "vix": 18.5,
                    "vixChange": -1.2,
                    "fearGreedIndex": 65,
                    "putCallRatio": 0.85
                }
            }
        }
    
    # Mock ML system status data
    if "mlSystemStatus" in query:
        return {
            "data": {
                "mlSystemStatus": {
                    "outcome_tracking": {
                        "total_outcomes": 1250,
                        "recent_outcomes": 45
                    },
                    "models": {
                        "safe_model": {
                            "model_id": "safe_v2.1.3",
                            "last_trained": "2024-01-15T08:30:00Z",
                            "performance": {
                                "auc": 0.78,
                                "precision_at_3": 0.65,
                                "hit_rate": 0.72,
                                "avg_return": 0.15,
                                "sharpe_ratio": 1.8,
                                "max_drawdown": 0.12
                            }
                        },
                        "aggressive_model": {
                            "model_id": "aggressive_v2.1.3",
                            "last_trained": "2024-01-15T08:30:00Z",
                            "performance": {
                                "auc": 0.82,
                                "precision_at_3": 0.71,
                                "hit_rate": 0.68,
                                "avg_return": 0.28,
                                "sharpe_ratio": 2.1,
                                "max_drawdown": 0.18
                            }
                        }
                    },
                    "bandit": {
                        "breakout": {
                            "win_rate": 0.68,
                            "confidence": 0.85,
                            "alpha": 12.5,
                            "beta": 5.8
                        },
                        "mean_reversion": {
                            "win_rate": 0.72,
                            "confidence": 0.78,
                            "alpha": 15.2,
                            "beta": 6.1
                        },
                        "momentum": {
                            "win_rate": 0.65,
                            "confidence": 0.82,
                            "alpha": 11.8,
                            "beta": 6.4
                        },
                        "etf_rotation": {
                            "win_rate": 0.75,
                            "confidence": 0.88,
                            "alpha": 18.3,
                            "beta": 6.1
                        }
                    },
                    "last_training": {
                        "SAFE": "2024-01-15T08:30:00Z",
                        "AGGRESSIVE": "2024-01-15T08:30:00Z"
                    },
                    "ml_available": True
                }
            }
        }
    
    # Mock options analysis data
    if "optionsAnalysis" in query:
        return {
            "data": {
                "optionsAnalysis": {
                    "id": "1",
                    "symbol": "AAPL",
                    "underlyingSymbol": "AAPL",
                    "currentPrice": 150.25,
                    "underlyingPrice": 150.25,
                    "analysis": {
                        "impliedVolatility": 0.28,
                        "historicalVolatility": 0.25,
                        "putCallRatio": 0.85,
                        "impliedVolatilityRank": 0.75,
                        "skew": 0.12,
                        "maxPain": 145.00,
                        "supportLevels": [140.00, 135.00, 130.00],
                        "resistanceLevels": [155.00, 160.00, 165.00]
                    },
                    "putCallRatio": 0.85,
                    "impliedVolatilityRank": 0.75,
                    "skew": 0.12,
                    "recommendations": [
                        {
                            "strategy": "COVERED_CALL",
                            "strike": 155.00,
                            "expiration": "2024-02-16",
                            "premium": 2.50,
                            "maxProfit": 7.25,
                            "maxLoss": -42.75,
                            "breakeven": 147.75,
                            "probability": 0.65,
                            "riskLevel": "MODERATE"
                        },
                        {
                            "strategy": "CASH_SECURED_PUT",
                            "strike": 145.00,
                            "expiration": "2024-02-16",
                            "premium": 1.80,
                            "maxProfit": 1.80,
                            "maxLoss": -143.20,
                            "breakeven": 143.20,
                            "probability": 0.70,
                            "riskLevel": "LOW"
                        }
                    ],
                    "greeks": {
                        "delta": 0.55,
                        "gamma": 0.02,
                        "theta": -0.15,
                        "vega": 0.25,
                        "rho": 0.08
                    },
                    "marketSentiment": {
                        "bullish": 0.45,
                        "bearish": 0.30,
                        "neutral": 0.25,
                        "sentiment": "BULLISH",
                        "sentimentDescription": "Market sentiment is moderately bullish with strong institutional support and positive earnings outlook. Recent analyst upgrades and strong technical indicators suggest continued upward momentum.",
                        "putCallRatio": 0.85
                    },
                    "sentimentScore": 0.65,
                    "sentimentDescription": "Market sentiment is moderately bullish with strong institutional support and positive earnings outlook. Recent analyst upgrades and strong technical indicators suggest continued upward momentum.",
                    "expirationDates": ["2024-02-16", "2024-03-15", "2024-04-19", "2024-05-17"],
                    "optionsChain": [
                        {
                            "strike": 140.00,
                            "expirationDates": ["2024-02-16", "2024-03-15", "2024-04-19", "2024-05-17"],
                            "callBid": 12.50,
                            "callAsk": 12.80,
                            "putBid": 2.20,
                            "putAsk": 2.50,
                            "volume": 1250,
                            "openInterest": 8500,
                            "calls": {
                                "symbol": "AAPL",
                                "contractSymbol": "AAPL240216C140",
                                "strike": 140.00,
                                "expirationDate": "2024-02-16",
                                "optionType": "CALL",
                                "bid": 12.50,
                                "ask": 12.80,
                                "lastPrice": 12.65,
                                "volume": 1250,
                                "openInterest": 8500,
                                "impliedVolatility": 0.28,
                                "intrinsicValue": 10.25,
                                "timeValue": 2.40,
                                "daysToExpiration": 32,
                                "delta": 0.85,
                                "gamma": 0.02,
                                "theta": -0.15,
                                "vega": 0.25,
                                "rho": 0.08,
                                "greeks": {
                                    "delta": 0.85,
                                    "gamma": 0.02,
                                    "theta": -0.15,
                                    "vega": 0.25,
                                    "rho": 0.08
                                }
                            },
                            "puts": {
                                "symbol": "AAPL",
                                "contractSymbol": "AAPL240216P140",
                                "strike": 140.00,
                                "expirationDate": "2024-02-16",
                                "optionType": "PUT",
                                "bid": 2.20,
                                "ask": 2.50,
                                "lastPrice": 2.35,
                                "volume": 800,
                                "openInterest": 4200,
                                "impliedVolatility": 0.25,
                                "intrinsicValue": 0.00,
                                "timeValue": 2.35,
                                "daysToExpiration": 32,
                                "delta": -0.15,
                                "gamma": 0.02,
                                "theta": -0.10,
                                "vega": 0.20,
                                "rho": -0.05,
                                "greeks": {
                                    "delta": -0.15,
                                    "gamma": 0.02,
                                    "theta": -0.10,
                                    "vega": 0.20,
                                    "rho": -0.05
                                }
                            },
                            "greeks": {
                                "delta": 0.85,
                                "gamma": 0.02,
                                "theta": -0.15,
                                "vega": 0.25,
                                "rho": 0.08
                            }
                        },
                        {
                            "strike": 145.00,
                            "expirationDates": ["2024-02-16", "2024-03-15", "2024-04-19", "2024-05-17"],
                            "callBid": 8.20,
                            "callAsk": 8.50,
                            "putBid": 3.80,
                            "putAsk": 4.10,
                            "volume": 2100,
                            "openInterest": 12000,
                            "calls": {
                                "symbol": "AAPL",
                                "contractSymbol": "AAPL240216C145",
                                "strike": 145.00,
                                "expirationDate": "2024-02-16",
                                "optionType": "CALL",
                                "bid": 8.20,
                                "ask": 8.50,
                                "lastPrice": 8.35,
                                "volume": 2100,
                                "openInterest": 12000,
                                "impliedVolatility": 0.28,
                                "intrinsicValue": 5.25,
                                "timeValue": 3.10,
                                "daysToExpiration": 32,
                                "delta": 0.70,
                                "gamma": 0.03,
                                "theta": -0.18,
                                "vega": 0.30,
                                "rho": 0.10,
                                "greeks": {
                                    "delta": 0.70,
                                    "gamma": 0.03,
                                    "theta": -0.18,
                                    "vega": 0.30,
                                    "rho": 0.10
                                }
                            },
                            "puts": {
                                "symbol": "AAPL",
                                "contractSymbol": "AAPL240216P145",
                                "strike": 145.00,
                                "expirationDate": "2024-02-16",
                                "optionType": "PUT",
                                "bid": 3.80,
                                "ask": 4.10,
                                "lastPrice": 3.95,
                                "volume": 1200,
                                "openInterest": 6500,
                                "impliedVolatility": 0.25,
                                "intrinsicValue": 0.00,
                                "timeValue": 3.95,
                                "daysToExpiration": 32,
                                "delta": -0.30,
                                "gamma": 0.03,
                                "theta": -0.12,
                                "vega": 0.25,
                                "rho": -0.08,
                                "greeks": {
                                    "delta": -0.30,
                                    "gamma": 0.03,
                                    "theta": -0.12,
                                    "vega": 0.25,
                                    "rho": -0.08
                                }
                            },
                            "greeks": {
                                "delta": 0.70,
                                "gamma": 0.03,
                                "theta": -0.18,
                                "vega": 0.30,
                                "rho": 0.10
                            }
                        },
                        {
                            "strike": 150.00,
                            "expirationDates": ["2024-02-16", "2024-03-15", "2024-04-19", "2024-05-17"],
                            "callBid": 4.50,
                            "callAsk": 4.80,
                            "putBid": 6.20,
                            "putAsk": 6.50,
                            "volume": 3500,
                            "openInterest": 18500,
                            "calls": {
                                "symbol": "AAPL",
                                "contractSymbol": "AAPL240216C150",
                                "strike": 150.00,
                                "expirationDate": "2024-02-16",
                                "optionType": "CALL",
                                "bid": 4.50,
                                "ask": 4.80,
                                "lastPrice": 4.65,
                                "volume": 3500,
                                "openInterest": 18500,
                                "impliedVolatility": 0.28,
                                "intrinsicValue": 0.25,
                                "timeValue": 4.40,
                                "daysToExpiration": 32,
                                "delta": 0.55,
                                "gamma": 0.02,
                                "theta": -0.15,
                                "vega": 0.25,
                                "rho": 0.08,
                                "greeks": {
                                    "delta": 0.55,
                                    "gamma": 0.02,
                                    "theta": -0.15,
                                    "vega": 0.25,
                                    "rho": 0.08
                                }
                            },
                            "puts": {
                                "symbol": "AAPL",
                                "contractSymbol": "AAPL240216P150",
                                "strike": 150.00,
                                "expirationDate": "2024-02-16",
                                "optionType": "PUT",
                                "bid": 6.20,
                                "ask": 6.50,
                                "lastPrice": 6.35,
                                "volume": 2000,
                                "openInterest": 11000,
                                "impliedVolatility": 0.25,
                                "intrinsicValue": 0.00,
                                "timeValue": 6.35,
                                "daysToExpiration": 32,
                                "delta": -0.45,
                                "gamma": 0.02,
                                "theta": -0.10,
                                "vega": 0.20,
                                "rho": -0.06,
                                "greeks": {
                                    "delta": -0.45,
                                    "gamma": 0.02,
                                    "theta": -0.10,
                                    "vega": 0.20,
                                    "rho": -0.06
                                }
                            },
                            "greeks": {
                                "delta": 0.55,
                                "gamma": 0.02,
                                "theta": -0.15,
                                "vega": 0.25,
                                "rho": 0.08
                            }
                        }
                    ],
                    "unusualFlow": [
                        {
                            "type": "CALL_SWEEP",
                            "symbol": "AAPL",
                            "strike": 155.00,
                            "expiration": "2024-02-16",
                            "volume": 5000,
                            "totalVolume": 5000,
                            "unusualVolume": 3500,
                            "unusualVolumePercent": 0.70,
                            "premium": 125000,
                            "timestamp": "2024-01-15T14:30:00Z",
                            "topTrades": [
                                {
                                    "symbol": "AAPL240216C155",
                                    "contractSymbol": "AAPL240216C155",
                                    "optionType": "CALL",
                                    "strike": 155.00,
                                    "expirationDate": "2024-02-16",
                                    "volume": 2500,
                                    "openInterest": 15000,
                                    "impliedVolatility": 0.28,
                                    "premium": 62500,
                                    "unusualActivityScore": 0.85,
                                    "activityType": "SWEEP",
                                    "type": "CALL_SWEEP",
                                    "timestamp": "2024-01-15T14:30:00Z"
                                }
                            ],
                            "sweepTrades": [
                                {
                                    "symbol": "AAPL240216C155",
                                    "contractSymbol": "AAPL240216C155",
                                    "optionType": "CALL",
                                    "strike": 155.00,
                                    "expirationDate": "2024-02-16",
                                    "volume": 1500,
                                    "openInterest": 15000,
                                    "impliedVolatility": 0.28,
                                    "premium": 37500,
                                    "unusualActivityScore": 0.80,
                                    "activityType": "SWEEP",
                                    "type": "CALL_SWEEP",
                                    "timestamp": "2024-01-15T14:25:00Z"
                                }
                            ],
                            "blockTrades": [
                                {
                                    "symbol": "AAPL240216C155",
                                    "contractSymbol": "AAPL240216C155",
                                    "optionType": "CALL",
                                    "strike": 155.00,
                                    "expirationDate": "2024-02-16",
                                    "volume": 1000,
                                    "openInterest": 15000,
                                    "impliedVolatility": 0.28,
                                    "premium": 25000,
                                    "unusualActivityScore": 0.75,
                                    "activityType": "BLOCK",
                                    "type": "CALL_BLOCK",
                                    "timestamp": "2024-01-15T14:20:00Z"
                                }
                            ],
                            "lastUpdated": "2024-01-15T14:30:00Z"
                        },
                        {
                            "type": "PUT_BLOCK",
                            "symbol": "AAPL",
                            "strike": 145.00,
                            "expiration": "2024-02-16",
                            "volume": 3000,
                            "totalVolume": 3000,
                            "unusualVolume": 2500,
                            "unusualVolumePercent": 0.83,
                            "premium": 120000,
                            "timestamp": "2024-01-15T13:45:00Z",
                            "topTrades": [
                                {
                                    "symbol": "AAPL240216P145",
                                    "contractSymbol": "AAPL240216P145",
                                    "optionType": "PUT",
                                    "strike": 145.00,
                                    "expirationDate": "2024-02-16",
                                    "volume": 1500,
                                    "openInterest": 12000,
                                    "impliedVolatility": 0.25,
                                    "premium": 60000,
                                    "unusualActivityScore": 0.90,
                                    "activityType": "BLOCK",
                                    "type": "PUT_BLOCK",
                                    "timestamp": "2024-01-15T13:45:00Z"
                                }
                            ],
                            "sweepTrades": [],
                            "blockTrades": [
                                {
                                    "symbol": "AAPL240216P145",
                                    "contractSymbol": "AAPL240216P145",
                                    "optionType": "PUT",
                                    "strike": 145.00,
                                    "expirationDate": "2024-02-16",
                                    "volume": 1500,
                                    "openInterest": 12000,
                                    "impliedVolatility": 0.25,
                                    "premium": 60000,
                                    "unusualActivityScore": 0.90,
                                    "activityType": "BLOCK",
                                    "type": "PUT_BLOCK",
                                    "timestamp": "2024-01-15T13:45:00Z"
                                }
                            ],
                            "lastUpdated": "2024-01-15T13:45:00Z"
                        }
                    ],
                    "recommendedStrategies": [
                        {
                            "name": "Bull Call Spread",
                            "strategyName": "Bull Call Spread",
                            "strategyType": "VERTICAL_SPREAD",
                            "description": "Buy 150 call, sell 155 call",
                            "maxProfit": 2.50,
                            "maxLoss": 2.50,
                            "breakeven": 152.50,
                            "breakevenPoints": [152.50],
                            "probability": 0.68,
                            "probabilityOfProfit": 0.68,
                            "riskLevel": "MODERATE",
                            "marketOutlook": "BULLISH",
                            "riskRewardRatio": 1.0,
                            "daysToExpiration": 32,
                            "totalCost": 2.50,
                            "totalCredit": 0.00
                        },
                        {
                            "name": "Iron Condor",
                            "strategyName": "Iron Condor",
                            "strategyType": "IRON_CONDOR",
                            "description": "Sell 145/150/155/160 spread",
                            "maxProfit": 1.20,
                            "maxLoss": 3.80,
                            "breakeven": [146.20, 158.80],
                            "breakevenPoints": [146.20, 158.80],
                            "probability": 0.72,
                            "probabilityOfProfit": 0.72,
                            "riskLevel": "MODERATE",
                            "marketOutlook": "NEUTRAL",
                            "riskRewardRatio": 0.32,
                            "daysToExpiration": 32,
                            "totalCost": 0.00,
                            "totalCredit": 1.20
                        }
                    ],
                    "createdAt": "2024-01-15T15:00:00Z",
                    "updatedAt": "2024-01-15T15:00:00Z"
                }
            }
        }
    
    # Mock generate AI recommendations mutation
    if "generateAiRecommendations" in query:
        print(f"🎯 DEBUG: Matched generateAiRecommendations query: {query[:100]}...")
        return {
            "data": {
                "generateAiRecommendations": {
                    "success": True,
                    "message": "AI recommendations generated successfully",
                    "recommendations": [
                        {
                            "id": "1",
                            "riskProfile": "MODERATE",
                            "portfolioAllocation": {
                                "stocks": 0.70,
                                "bonds": 0.20,
                                "cash": 0.10
                            },
                            "recommendedStocks": [
                                {
                                    "symbol": "AAPL",
                                    "allocation": 0.30,
                                    "reason": "Strong fundamentals and market position"
                                },
                                {
                                    "symbol": "MSFT",
                                    "allocation": 0.25,
                                    "reason": "Cloud business growth and dividend yield"
                                },
                                {
                                    "symbol": "GOOGL",
                                    "allocation": 0.20,
                                    "reason": "Search dominance and AI capabilities"
                                },
                                {
                                    "symbol": "TSLA",
                                    "allocation": 0.15,
                                    "reason": "EV market leadership and innovation"
                                },
                                {
                                    "symbol": "AMZN",
                                    "allocation": 0.10,
                                    "reason": "E-commerce and cloud diversification"
                                }
                            ],
                            "expectedPortfolioReturn": 0.12,
                            "riskAssessment": {
                                "volatility": 0.18,
                                "sharpeRatio": 0.67,
                                "maxDrawdown": 0.15,
                                "beta": 1.05
                            }
                        }
                    ]
                }
            }
        }
    
    # Mock AI rebalance portfolio mutation
    if "aiRebalancePortfolio" in query:
        print(f"🎯 DEBUG: Matched aiRebalancePortfolio query: {query[:100]}...")
        return {
            "data": {
                "aiRebalancePortfolio": {
                    "success": True,
                    "message": "Portfolio rebalanced successfully",
                    "rebalanceId": "rebalance_12345",
                    "originalAllocation": {
                        "AAPL": 0.25,
                        "MSFT": 0.20,
                        "GOOGL": 0.15,
                        "TSLA": 0.10,
                        "AMZN": 0.10,
                        "CASH": 0.20
                    },
                    "newAllocation": {
                        "AAPL": 0.22,
                        "MSFT": 0.18,
                        "GOOGL": 0.16,
                        "TSLA": 0.12,
                        "AMZN": 0.12,
                        "CASH": 0.20
                    },
                    "rebalanceActions": [
                        {
                            "action": "SELL",
                            "symbol": "AAPL",
                            "shares": 5,
                            "currentValue": 750.00,
                            "reason": "Reduce overweight position"
                        },
                        {
                            "action": "SELL",
                            "symbol": "MSFT",
                            "shares": 3,
                            "currentValue": 450.00,
                            "reason": "Rebalance to target allocation"
                        },
                        {
                            "action": "BUY",
                            "symbol": "GOOGL",
                            "shares": 2,
                            "currentValue": 300.00,
                            "reason": "Increase underweight position"
                        },
                        {
                            "action": "BUY",
                            "symbol": "TSLA",
                            "shares": 4,
                            "currentValue": 600.00,
                            "reason": "Increase allocation based on momentum"
                        },
                        {
                            "action": "BUY",
                            "symbol": "AMZN",
                            "shares": 3,
                            "currentValue": 450.00,
                            "reason": "Rebalance to target allocation"
                        }
                    ],
                    "expectedImpact": {
                        "riskReduction": 0.02,
                        "expectedReturn": 0.09,
                        "volatilityChange": -0.01,
                        "sharpeRatioImprovement": 0.05
                    },
                    "estimatedCosts": {
                        "tradingFees": 12.50,
                        "taxImpact": 0.00,
                        "totalCost": 12.50
                    },
                    "changesMade": [
                        {
                            "symbol": "AAPL",
                            "action": "REDUCE",
                            "oldAllocation": 0.25,
                            "newAllocation": 0.22,
                            "changeAmount": -0.03,
                            "reason": "Reduce overweight position"
                        },
                        {
                            "symbol": "MSFT",
                            "action": "REDUCE",
                            "oldAllocation": 0.20,
                            "newAllocation": 0.18,
                            "changeAmount": -0.02,
                            "reason": "Rebalance to target allocation"
                        },
                        {
                            "symbol": "GOOGL",
                            "action": "INCREASE",
                            "oldAllocation": 0.15,
                            "newAllocation": 0.16,
                            "changeAmount": 0.01,
                            "reason": "Increase underweight position"
                        },
                        {
                            "symbol": "TSLA",
                            "action": "INCREASE",
                            "oldAllocation": 0.10,
                            "newAllocation": 0.12,
                            "changeAmount": 0.02,
                            "reason": "Increase allocation based on momentum"
                        },
                        {
                            "symbol": "AMZN",
                            "action": "INCREASE",
                            "oldAllocation": 0.10,
                            "newAllocation": 0.12,
                            "changeAmount": 0.02,
                            "reason": "Rebalance to target allocation"
                        }
                    ],
                    "stockTrades": [
                        {
                            "symbol": "AAPL",
                            "action": "SELL",
                            "shares": 5,
                            "price": 150.00,
                            "value": 750.00,
                            "commission": 2.50,
                            "companyName": "Apple Inc.",
                            "totalValue": 750.00,
                            "reason": "Reduce overweight position"
                        },
                        {
                            "symbol": "MSFT",
                            "action": "SELL",
                            "shares": 3,
                            "price": 150.00,
                            "value": 450.00,
                            "commission": 2.50,
                            "companyName": "Microsoft Corporation",
                            "totalValue": 450.00,
                            "reason": "Rebalance to target allocation"
                        },
                        {
                            "symbol": "GOOGL",
                            "action": "BUY",
                            "shares": 2,
                            "price": 150.00,
                            "value": 300.00,
                            "commission": 2.50,
                            "companyName": "Alphabet Inc.",
                            "totalValue": 300.00,
                            "reason": "Increase underweight position"
                        },
                        {
                            "symbol": "TSLA",
                            "action": "BUY",
                            "shares": 4,
                            "price": 150.00,
                            "value": 600.00,
                            "commission": 2.50,
                            "companyName": "Tesla Inc.",
                            "totalValue": 600.00,
                            "reason": "Increase allocation based on momentum"
                        },
                        {
                            "symbol": "AMZN",
                            "action": "BUY",
                            "shares": 3,
                            "price": 150.00,
                            "value": 450.00,
                            "commission": 2.50,
                            "companyName": "Amazon.com Inc.",
                            "totalValue": 450.00,
                            "reason": "Rebalance to target allocation"
                        }
                    ],
                    "newPortfolioValue": 50000.00,
                    "rebalanceCost": 12.50,
                    "estimatedImprovement": {
                        "expectedReturnIncrease": 0.01,
                        "riskReduction": 0.02,
                        "sharpeRatioImprovement": 0.05,
                        "volatilityReduction": 0.01,
                        "maxDrawdownReduction": 0.02,
                        "betaAdjustment": -0.05
                    },
                    "dryRun": True,
                    "executionDate": "2024-01-15T16:00:00Z"
                }
            }
        }
    
    # Mock ticker post created subscription
    if "tickerPostCreated" in query:
        print(f"🎯 DEBUG: Matched tickerPostCreated query: {query[:100]}...")
        return {
            "data": {
                "tickerPostCreated": {
                    "id": "1",
                    "kind": "DISCUSSION",
                    "title": "Market Analysis Update",
                    "tickers": ["AAPL"],
                    "user": {
                        "id": "1",
                        "name": "Test User"
                    },
                    "createdAt": "2024-01-15T10:30:00Z"
                }
            }
        }
    
    # Mock crypto recommendations
    if "cryptoRecommendations" in query:
        limit = body.get("variables", {}).get("limit", 5)
        symbols = body.get("variables", {}).get("symbols", [])
        
        # Generate mock crypto recommendations
        all_recommendations = [
            {
                "symbol": "BTC",
                "score": 0.92,
                "probability": 0.85,
                "confidenceLevel": "HIGH",
                "priceUsd": 45000.00,
                "volatilityTier": "MEDIUM",
                "liquidity24hUsd": 25000000000,
                "rationale": "Strong institutional adoption and store of value narrative",
                "recommendation": "BUY",
                "riskLevel": "MEDIUM"
            },
            {
                "symbol": "ETH",
                "score": 0.88,
                "probability": 0.78,
                "confidenceLevel": "HIGH",
                "priceUsd": 3200.00,
                "volatilityTier": "HIGH",
                "liquidity24hUsd": 15000000000,
                "rationale": "Ethereum 2.0 upgrades and DeFi ecosystem growth",
                "recommendation": "BUY",
                "riskLevel": "HIGH"
            },
            {
                "symbol": "SOL",
                "score": 0.85,
                "probability": 0.82,
                "confidenceLevel": "MEDIUM",
                "priceUsd": 95.00,
                "volatilityTier": "HIGH",
                "liquidity24hUsd": 2000000000,
                "rationale": "High performance blockchain with growing ecosystem",
                "recommendation": "BUY",
                "riskLevel": "HIGH"
            },
            {
                "symbol": "ADA",
                "score": 0.72,
                "probability": 0.65,
                "confidenceLevel": "MEDIUM",
                "priceUsd": 0.45,
                "volatilityTier": "MEDIUM",
                "liquidity24hUsd": 800000000,
                "rationale": "Academic approach to blockchain with smart contracts",
                "recommendation": "HOLD",
                "riskLevel": "MEDIUM"
            },
            {
                "symbol": "DOT",
                "score": 0.68,
                "probability": 0.58,
                "confidenceLevel": "LOW",
                "priceUsd": 6.50,
                "volatilityTier": "HIGH",
                "liquidity24hUsd": 500000000,
                "rationale": "Interoperability focus with parachain ecosystem",
                "recommendation": "HOLD",
                "riskLevel": "HIGH"
            }
        ]
        
        # Filter by symbols if provided
        if symbols:
            filtered_recommendations = [rec for rec in all_recommendations if rec["symbol"] in symbols]
        else:
            filtered_recommendations = all_recommendations
        
        # Apply limit
        recommendations = filtered_recommendations[:limit]
        
        return {
            "data": {
                "cryptoRecommendations": recommendations
            }
        }
    
    # Mock portfolio metrics
    if "portfolioMetrics" in query:
        return {
            "data": {
                "portfolioMetrics": {
                    "totalValue": 50000.00,
                    "totalCost": 45000.00,
                    "totalReturn": 5000.00,
                    "totalReturnPercent": 11.11,
                    "dayChange": 250.00,
                    "dayChangePercent": 0.50,
                    "volatility": 0.18,
                    "sharpeRatio": 1.25,
                    "maxDrawdown": 0.12,
                    "beta": 0.95,
                    "alpha": 0.08,
                    "sectorAllocation": {
                        "Technology": 0.60,
                        "Healthcare": 0.20,
                        "Financial": 0.15,
                        "Consumer": 0.05
                    },
                    "riskMetrics": {
                        "var95": 0.05,
                        "var99": 0.08,
                        "expectedShortfall": 0.06,
                        "trackingError": 0.12,
                        "informationRatio": 0.67,
                        "treynorRatio": 0.11,
                        "jensenAlpha": 0.08
                    },
                    "holdings": [
                        {
                            "symbol": "AAPL",
                            "companyName": "Apple Inc.",
                            "shares": 100,
                            "currentPrice": 150.25,
                            "totalValue": 15025.00,
                            "costBasis": 14000.00,
                            "gain": 1025.00,
                            "gainPercent": 7.32,
                            "returnAmount": 1025.00,
                            "returnPercent": 7.32,
                            "sector": "Technology"
                        },
                        {
                            "symbol": "GOOGL",
                            "companyName": "Alphabet Inc.",
                            "shares": 10,
                            "currentPrice": 2800.50,
                            "totalValue": 28005.00,
                            "costBasis": 27000.00,
                            "gain": 1005.00,
                            "gainPercent": 3.72,
                            "returnAmount": 1005.00,
                            "returnPercent": 3.72,
                            "sector": "Technology"
                        },
                        {
                            "symbol": "MSFT",
                            "companyName": "Microsoft Corporation",
                            "shares": 50,
                            "currentPrice": 350.75,
                            "totalValue": 17537.50,
                            "costBasis": 17000.00,
                            "gain": 537.50,
                            "gainPercent": 3.16,
                            "returnAmount": 537.50,
                            "returnPercent": 3.16,
                            "sector": "Technology"
                        }
                    ]
                }
            }
        }
    
    # Feed By Tickers Handler
    if "feedByTickers" in query:
        print(f"🎯 DEBUG: Matched feedByTickers query: {query[:100]}...")       
        return {
            "data": {
                "feedByTickers": [
                    {
                        "id": "feed_post_1",                                
                        "kind": "post",
                        "title": "AAPL Technical Analysis Update",          
                        "content": "Apple showing strong support at $180 level. RSI oversold, potential bounce expected.",                                  
                        "createdAt": "2024-01-15T10:30:00Z",                
                        "score": 95,
                        "user": {
                            "id": "user_feed_1",                            
                            "name": "Tech Trader",                          
                            "profilePic": "https://example.com/avatar_feed1.jpg"                               
                        },
                        "tickers": ["AAPL"],                                
                        "commentCount": 3                                  
                    },
                    {
                        "id": "feed_post_2",                                
                        "kind": "post",
                        "title": "MSFT Earnings Preview",                   
                        "content": "Microsoft earnings next week. Cloud growth expected to drive strong results.",  
                        "createdAt": "2024-01-15T09:45:00Z",                
                        "score": 88,
                        "user": {
                            "id": "user_feed_2",                            
                            "name": "Earnings Expert",                      
                            "profilePic": "https://example.com/avatar_feed2.jpg"                               
                        },
                        "tickers": ["MSFT"],                                
                        "commentCount": 2                                  
                    },
                    {
                        "id": "feed_post_3",                                
                        "kind": "post",
                        "title": "GOOGL AI Developments",                   
                        "content": "Google's latest AI announcements could impact search revenue growth.",          
                        "createdAt": "2024-01-15T08:20:00Z",                
                        "score": 76,
                        "user": {
                            "id": "user_feed_3",                            
                            "name": "AI Analyst",                           
                            "profilePic": "https://example.com/avatar_feed3.jpg"                               
                        },
                        "tickers": ["GOOGL"],                               
                        "commentCount": 1                                  
                    }
                ]
            }
        }

    # Social Feed GraphQL endpoint
    if "socialFeed" in query:
        print(f"🎯 DEBUG: Matched socialFeed query: {query[:100]}...")
        return {
            "data": {
                "socialFeed": [
                    {
                        "id": "post_1",
                        "title": "AAPL Analysis: Strong Q4 Earnings Expected",
                        "content": "Apple's upcoming earnings report looks promising with strong iPhone sales and services growth. The stock has been consolidating near resistance levels.",
                        "createdAt": "2024-01-15T09:30:00Z",
                        "score": 85,
                        "comments": [
                            {
                                "id": "comment_1",
                                "content": "Great analysis! I'm bullish on AAPL long-term",
                                "author": "TraderMike",
                                "createdAt": "2024-01-15T10:15:00Z",
                                "user": {
                                    "id": "user_comment_1",
                                    "username": "TraderMike",
                                    "name": "Trader Mike",
                                    "email": "tradermike@example.com",
                                    "profilePic": "https://example.com/avatar_comment1.jpg",
                                    "verified": False
                                }
                            },
                            {
                                "id": "comment_2", 
                                "content": "What about the China headwinds?",
                                "author": "MarketWatcher",
                                "createdAt": "2024-01-15T11:00:00Z",
                                "user": {
                                    "id": "user_comment_2",
                                    "username": "MarketWatcher",
                                    "name": "Market Watcher",
                                    "email": "marketwatcher@example.com",
                                    "profilePic": "https://example.com/avatar_comment2.jpg",
                                    "verified": True
                                }
                            }
                        ],
                        "author": {
                            "id": "user_1",
                            "username": "TechAnalyst",
                            "name": "Tech Analyst",
                            "email": "techanalyst@example.com",
                            "profilePic": "https://example.com/avatar1.jpg",
                            "verified": True
                        },
                        "user": {
                            "id": "user_1",
                            "username": "TechAnalyst",
                            "name": "Tech Analyst",
                            "email": "techanalyst@example.com",
                            "profilePic": "https://example.com/avatar1.jpg",
                            "verified": True
                        },
                        "tickers": ["AAPL"],
                        "stock": {
                            "id": "stock_aapl",
                            "symbol": "AAPL",
                            "companyName": "Apple Inc.",
                            "currentPrice": 185.50,
                            "change": 2.15,
                            "changePercent": 1.17
                        },
                        "likes": 42,
                        "shares": 8,
                        "commentCount": 2,
                        "sentiment": "bullish"
                    },
                    {
                        "id": "post_2",
                        "title": "Market Update: Fed Policy Impact on Tech Stocks",
                        "content": "The Federal Reserve's recent comments suggest a more dovish stance, which could benefit growth stocks. TSLA and NVDA showing strong momentum.",
                        "createdAt": "2024-01-15T08:45:00Z",
                        "score": 92,
                        "comments": [
                            {
                                "id": "comment_3",
                                "content": "Agreed, the macro environment is improving",
                                "author": "MacroTrader",
                                "createdAt": "2024-01-15T09:20:00Z",
                                "user": {
                                    "id": "user_comment_3",
                                    "username": "MacroTrader",
                                    "name": "Macro Trader",
                                    "email": "macrotrader@example.com",
                                    "profilePic": "https://example.com/avatar_comment3.jpg",
                                    "verified": True
                                }
                            }
                        ],
                        "author": {
                            "id": "user_2",
                            "username": "MarketGuru",
                            "name": "Market Guru",
                            "email": "marketguru@example.com",
                            "profilePic": "https://example.com/avatar2.jpg",
                            "verified": True
                        },
                        "user": {
                            "id": "user_2",
                            "username": "MarketGuru",
                            "name": "Market Guru",
                            "email": "marketguru@example.com",
                            "profilePic": "https://example.com/avatar2.jpg",
                            "verified": True
                        },
                        "tickers": ["TSLA", "NVDA"],
                        "stock": {
                            "id": "stock_tsla",
                            "symbol": "TSLA",
                            "companyName": "Tesla Inc.",
                            "currentPrice": 245.80,
                            "change": 8.25,
                            "changePercent": 3.47
                        },
                        "likes": 67,
                        "shares": 15,
                        "commentCount": 1,
                        "sentiment": "bullish"
                    },
                    {
                        "id": "post_3",
                        "title": "Options Strategy: Covered Calls on MSFT",
                        "content": "With MSFT trading near all-time highs, selling covered calls could generate additional income while maintaining upside exposure.",
                        "createdAt": "2024-01-15T07:30:00Z",
                        "score": 78,
                        "comments": [
                            {
                                "id": "comment_4",
                                "content": "What strike price are you targeting?",
                                "author": "OptionsTrader",
                                "createdAt": "2024-01-15T08:00:00Z",
                                "user": {
                                    "id": "user_comment_4",
                                    "username": "OptionsTrader",
                                    "name": "Options Trader",
                                    "email": "optionstrader@example.com",
                                    "profilePic": "https://example.com/avatar_comment4.jpg",
                                    "verified": False
                                }
                            },
                            {
                                "id": "comment_5",
                                "content": "I'm looking at the 400 strike for March expiration",
                                "author": "TechAnalyst",
                                "createdAt": "2024-01-15T08:15:00Z",
                                "user": {
                                    "id": "user_comment_5",
                                    "username": "TechAnalyst",
                                    "name": "Tech Analyst",
                                    "email": "techanalyst@example.com",
                                    "profilePic": "https://example.com/avatar_comment5.jpg",
                                    "verified": True
                                }
                            }
                        ],
                        "author": {
                            "id": "user_3",
                            "username": "OptionsExpert",
                            "name": "Options Expert",
                            "email": "optionsexpert@example.com",
                            "profilePic": "https://example.com/avatar3.jpg",
                            "verified": False
                        },
                        "user": {
                            "id": "user_3",
                            "username": "OptionsExpert",
                            "name": "Options Expert",
                            "email": "optionsexpert@example.com",
                            "profilePic": "https://example.com/avatar3.jpg",
                            "verified": False
                        },
                        "tickers": ["MSFT"],
                        "stock": {
                            "id": "stock_msft",
                            "symbol": "MSFT",
                            "companyName": "Microsoft Corporation",
                            "currentPrice": 415.20,
                            "change": -1.80,
                            "changePercent": -0.43
                        },
                        "likes": 34,
                        "shares": 6,
                        "commentCount": 2,
                        "sentiment": "neutral"
                    },
                    {
                        "id": "post_4",
                        "title": "Crypto Corner: Bitcoin ETF Inflows Continue",
                        "content": "Bitcoin ETF inflows have been strong this week, with over $2B in new investments. This could signal renewed institutional interest in crypto.",
                        "createdAt": "2024-01-15T06:15:00Z",
                        "score": 89,
                        "comments": [
                            {
                                "id": "comment_6",
                                "content": "The institutional adoption is accelerating",
                                "author": "CryptoBull",
                                "createdAt": "2024-01-15T07:00:00Z",
                                "user": {
                                    "id": "user_comment_6",
                                    "username": "CryptoBull",
                                    "name": "Crypto Bull",
                                    "email": "cryptobull@example.com",
                                    "profilePic": "https://example.com/avatar_comment6.jpg",
                                    "verified": True
                                }
                            }
                        ],
                        "author": {
                            "id": "user_4",
                            "username": "CryptoAnalyst",
                            "name": "Crypto Analyst",
                            "email": "cryptoanalyst@example.com",
                            "profilePic": "https://example.com/avatar4.jpg",
                            "verified": True
                        },
                        "user": {
                            "id": "user_4",
                            "username": "CryptoAnalyst",
                            "name": "Crypto Analyst",
                            "email": "cryptoanalyst@example.com",
                            "profilePic": "https://example.com/avatar4.jpg",
                            "verified": True
                        },
                        "tickers": ["BTC"],
                        "stock": {
                            "id": "crypto_btc",
                            "symbol": "BTC",
                            "companyName": "Bitcoin",
                            "currentPrice": 43250.00,
                            "change": 1250.00,
                            "changePercent": 2.98
                        },
                        "likes": 156,
                        "shares": 23,
                        "commentCount": 1,
                        "sentiment": "bullish"
                    },
                    {
                        "id": "post_5",
                        "title": "Portfolio Rebalancing: Time to Take Profits?",
                        "content": "With the market at all-time highs, it might be prudent to rebalance portfolios and take some profits off the table. Consider reducing risk exposure.",
                        "createdAt": "2024-01-15T05:00:00Z",
                        "score": 73,
                        "comments": [
                            {
                                "id": "comment_7",
                                "content": "Timing the market is difficult, but diversification is key",
                                "author": "PortfolioManager",
                                "createdAt": "2024-01-15T05:30:00Z",
                                "user": {
                                    "id": "user_comment_7",
                                    "username": "PortfolioManager",
                                    "name": "Portfolio Manager",
                                    "email": "portfoliomanager@example.com",
                                    "profilePic": "https://example.com/avatar_comment7.jpg",
                                    "verified": True
                                }
                            },
                            {
                                "id": "comment_8",
                                "content": "I'm staying fully invested for now",
                                "author": "LongTermInvestor",
                                "createdAt": "2024-01-15T06:00:00Z",
                                "user": {
                                    "id": "user_comment_8",
                                    "username": "LongTermInvestor",
                                    "name": "Long Term Investor",
                                    "email": "longterminvestor@example.com",
                                    "profilePic": "https://example.com/avatar_comment8.jpg",
                                    "verified": False
                                }
                            }
                        ],
                        "author": {
                            "id": "user_5",
                            "username": "RiskManager",
                            "name": "Risk Manager",
                            "email": "riskmanager@example.com",
                            "profilePic": "https://example.com/avatar5.jpg",
                            "verified": True
                        },
                        "user": {
                            "id": "user_5",
                            "username": "RiskManager",
                            "name": "Risk Manager",
                            "email": "riskmanager@example.com",
                            "profilePic": "https://example.com/avatar5.jpg",
                            "verified": True
                        },
                        "tickers": [],
                        "stock": {
                            "id": "market_spy",
                            "symbol": "SPY",
                            "companyName": "SPDR S&P 500 ETF Trust",
                            "currentPrice": 485.75,
                            "change": 3.25,
                            "changePercent": 0.67
                        },
                        "likes": 28,
                        "shares": 4,
                        "commentCount": 2,
                        "sentiment": "neutral"
                    }
                ]
            }
        }

    # AI Options GraphQL endpoint
    if "aiOptionsRecommendations" in query:
        print(f"🎯 DEBUG: Matched aiOptionsRecommendations query: {query[:100]}...")
        return {
            "data": {
                "aiOptionsRecommendations": {
                    "recommendations": [
                        {
                            "strategyName": "Bull Call Spread",
                            "strategyType": "income",
                            "confidenceScore": 0.85,
                            "symbol": "AAPL",
                            "currentPrice": 150.25,
                            "options": [
                                {
                                    "type": "call",
                                    "action": "buy",
                                    "strike": 150,
                                    "expiration": "2024-02-16",
                                    "premium": 2.50,
                                    "quantity": 10
                                }
                            ],
                            "analytics": {
                                "maxProfit": 500,
                                "maxLoss": 250,
                                "probabilityOfProfit": 0.65,
                                "expectedReturn": 0.08,
                                "breakeven": 152.50
                            },
                            "reasoning": {
                                "marketOutlook": "Bullish outlook for AAPL based on technical analysis",
                                "strategyRationale": "This income strategy capitalizes on current market conditions",
                                "riskFactors": ["Market volatility", "Time decay", "Liquidity risk"],
                                "keyBenefits": ["High probability of profit", "Limited downside risk", "Flexible execution"]
                            },
                            "riskScore": 3,
                            "daysToExpiration": 30,
                            "createdAt": "2024-01-15T10:00:00Z"
                        },
                        {
                            "strategyName": "Protective Put",
                            "strategyType": "hedge",
                            "confidenceScore": 0.80,
                            "symbol": "AAPL",
                            "currentPrice": 150.25,
                            "options": [
                                {
                                    "type": "put",
                                    "action": "buy",
                                    "strike": 145,
                                    "expiration": "2024-02-16",
                                    "premium": 1.75,
                                    "quantity": 10
                                }
                            ],
                            "analytics": {
                                "maxProfit": 1000,
                                "maxLoss": 175,
                                "probabilityOfProfit": 0.70,
                                "expectedReturn": 0.12,
                                "breakeven": 151.75
                            },
                            "reasoning": {
                                "marketOutlook": "Bullish outlook for AAPL with downside protection",
                                "strategyRationale": "This hedge strategy provides downside protection while maintaining upside potential",
                                "riskFactors": ["Time decay", "Volatility changes", "Premium cost"],
                                "keyBenefits": ["Downside protection", "Unlimited upside", "Risk management"]
                            },
                            "riskScore": 2,
                            "daysToExpiration": 30,
                            "createdAt": "2024-01-15T10:00:00Z"
                        }
                    ],
                    "marketAnalysis": {
                        "symbol": "AAPL",
                        "currentPrice": 150.25,
                        "volatility": 0.25,
                        "sentiment": "bullish",
                        "technicalIndicators": {
                            "rsi": 65.5,
                            "macd": 1.25,
                            "bollingerPosition": 0.7
                        },
                        "marketOutlook": "Strong bullish momentum for AAPL",
                        "keyLevels": {
                            "support": 145.00,
                            "resistance": 160.00
                        }
                    },
                    "symbol": "AAPL",
                    "riskTolerance": "medium",
                    "portfolioValue": 10000,
                    "timeHorizon": 30,
                    "generatedAt": "2024-01-15T10:00:00Z"
                }
            }
        }

    # Default response
    return {"data": {}}

# AI Options REST API Endpoints
@app.post("/api/ai-options/recommendations")
async def ai_options_recommendations(request: Request):
    """AI Options Recommendations endpoint"""
    print(f"🔍 AI Options Request: {request.method} {request.url}")
    
    try:
        body = await request.json()
        symbol = body.get("symbol", "AAPL").upper()
        user_risk_tolerance = body.get("user_risk_tolerance", "medium")
        portfolio_value = body.get("portfolio_value", 10000)
        time_horizon = body.get("time_horizon", 30)
        max_recommendations = body.get("max_recommendations", 5)
        
        print(f"📊 AI Options Params: {symbol}, {user_risk_tolerance}, ${portfolio_value}, {time_horizon} days")
        
        # Mock AI options recommendations
        recommendations = []
        for i in range(max_recommendations):
            strategy_types = ["income", "hedge", "speculation", "arbitrage"]
            strategy_type = strategy_types[i % len(strategy_types)]
            
            recommendation = {
                "strategy_name": f"{strategy_type.title()} Strategy {i+1}",
                "strategy_type": strategy_type,
                "confidence_score": 0.75 + (i * 0.05),
                "symbol": symbol,
                "current_price": 150.25 + (i * 5),
                "options": [
                    {
                        "type": "call" if i % 2 == 0 else "put",
                        "action": "buy",
                        "strike": 150 + (i * 5),
                        "expiration": "2024-02-16",
                        "premium": 2.50 + (i * 0.5),
                        "quantity": 10
                    }
                ],
                "analytics": {
                    "max_profit": 500 + (i * 100),
                    "max_loss": 250 + (i * 50),
                    "probability_of_profit": 0.65 + (i * 0.05),
                    "expected_return": 0.08 + (i * 0.02),
                    "breakeven": 152.50 + (i * 2.5)
                },
                "reasoning": {
                    "market_outlook": f"Bullish outlook for {symbol} based on technical analysis",
                    "strategy_rationale": f"This {strategy_type} strategy capitalizes on current market conditions",
                    "risk_factors": ["Market volatility", "Time decay", "Liquidity risk"],
                    "key_benefits": ["High probability of profit", "Limited downside risk", "Flexible execution"]
                },
                "risk_score": 3 + i,
                "days_to_expiration": time_horizon,
                "created_at": "2024-01-15T10:00:00Z"
            }
            recommendations.append(recommendation)
        
        market_analysis = {
            "symbol": symbol,
            "current_price": 150.25,
            "volatility": 0.25,
            "sentiment": "bullish",
            "technical_indicators": {
                "rsi": 65.5,
                "macd": 1.25,
                "bollinger_position": 0.7
            },
            "market_outlook": f"Strong bullish momentum for {symbol}",
            "key_levels": {
                "support": 145.00,
                "resistance": 160.00
            }
        }
        
        response = {
            "recommendations": recommendations,
            "market_analysis": market_analysis,
            "symbol": symbol,
            "risk_tolerance": user_risk_tolerance,
            "portfolio_value": portfolio_value,
            "time_horizon": time_horizon,
            "generated_at": "2024-01-15T10:00:00Z"
        }
        
        print(f"✅ AI Options Response: {len(recommendations)} recommendations generated")
        return response
        
    except Exception as e:
        print(f"❌ AI Options Error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/ai-options/optimize-strategy")
async def optimize_strategy(request: Request):
    """Strategy Optimization endpoint"""
    print(f"🔍 Strategy Optimization Request: {request.method} {request.url}")
    
    try:
        body = await request.json()
        print(f"📊 Optimization Params: {body}")
        
        # Mock optimization response
        response = {
            "optimized_strategy": {
                "strategy_name": "Optimized Bull Call Spread",
                "confidence_score": 0.85,
                "expected_return": 0.12,
                "max_risk": 500,
                "probability_of_profit": 0.72
            },
            "optimization_details": {
                "original_return": 0.08,
                "improvement": 0.04,
                "risk_adjustment": "Reduced by 15%",
                "optimization_factors": ["Volatility adjustment", "Time decay optimization", "Risk management"]
            },
            "generated_at": "2024-01-15T10:00:00Z"
        }
        
        print(f"✅ Strategy Optimization Response: Strategy optimized")
        return response
        
    except Exception as e:
        print(f"❌ Strategy Optimization Error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/ai-options/market-analysis")
async def market_analysis(request: Request):
    """Market Analysis endpoint"""
    print(f"🔍 Market Analysis Request: {request.method} {request.url}")
    
    try:
        body = await request.json()
        symbol = body.get("symbol", "AAPL").upper()
        analysis_type = body.get("analysisType", "comprehensive")
        
        print(f"📊 Market Analysis Params: {symbol}, {analysis_type}")
        
        # Mock market analysis response
        response = {
            "symbol": symbol,
            "analysis_type": analysis_type,
            "current_price": 150.25,
            "volatility": 0.25,
            "sentiment": "bullish",
            "technical_analysis": {
                "trend": "uptrend",
                "support_levels": [145.00, 140.00],
                "resistance_levels": [160.00, 165.00],
                "rsi": 65.5,
                "macd": 1.25
            },
            "fundamental_analysis": {
                "pe_ratio": 28.5,
                "market_cap": "2.5T",
                "revenue_growth": 0.08,
                "profit_margin": 0.25
            },
            "options_flow": {
                "put_call_ratio": 0.65,
                "unusual_activity": "High call volume",
                "max_pain": 155.00
            },
            "generated_at": "2024-01-15T10:00:00Z"
        }
        
        print(f"✅ Market Analysis Response: Analysis completed for {symbol}")
        return response
        
    except Exception as e:
        print(f"❌ Market Analysis Error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/ai-options/train-models")
async def train_models(request: Request):
    """Model Training endpoint"""
    print(f"🔍 Model Training Request: {request.method} {request.url}")
    
    try:
        body = await request.json()
        symbol = body.get("symbol", "AAPL").upper()
        
        print(f"📊 Model Training Params: {symbol}")
        
        # Mock training response
        response = {
            "symbol": symbol,
            "training_status": "completed",
            "model_accuracy": 0.87,
            "training_data_points": 10000,
            "model_version": "v2.1.0",
            "training_duration": "45 minutes",
            "generated_at": "2024-01-15T10:00:00Z"
        }
        
        print(f"✅ Model Training Response: Models trained for {symbol}")
        return response
        
    except Exception as e:
        print(f"❌ Model Training Error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/ai-options/model-status/{symbol}")
async def model_status(symbol: str):
    """Model Status endpoint"""
    print(f"🔍 Model Status Request: GET /api/ai-options/model-status/{symbol}")
    
    try:
        symbol = symbol.upper()
        print(f"📊 Model Status Params: {symbol}")
        
        # Mock model status response
        response = {
            "symbol": symbol,
            "model_status": "active",
            "last_trained": "2024-01-15T09:00:00Z",
            "model_accuracy": 0.87,
            "prediction_count": 1250,
            "success_rate": 0.82,
            "generated_at": "2024-01-15T10:00:00Z"
        }
        
        print(f"✅ Model Status Response: Status retrieved for {symbol}")
        return response
        
    except Exception as e:
        print(f"❌ Model Status Error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/ai-options/health")
async def ai_options_health():
    """AI Options Health Check endpoint"""
    print(f"🔍 AI Options Health Check Request")
    
    try:
        response = {
            "status": "healthy",
            "service": "ai-options",
            "version": "1.0.0",
            "uptime": "24 hours",
            "models_loaded": 5,
            "generated_at": "2024-01-15T10:00:00Z"
        }
        
        print(f"✅ AI Options Health Response: Service healthy")
        return response
        
    except Exception as e:
        print(f"❌ AI Options Health Error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    print("🚀 Starting RichesReach Test Server...")
    print("📱 Mobile app can now connect to: http://192.168.1.236:8000")
    print("🔑 Test login: test@example.com / password123")
    print("🌐 Server binding to all interfaces (0.0.0.0:8000)")
    uvicorn.run(app, host="0.0.0.0", port=8000)
