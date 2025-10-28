#!/usr/bin/env python3

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import json
from datetime import datetime

app = FastAPI(title="RichesReach Test Server", version="1.0.0")

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

@app.get("/api/market/quotes")
async def get_market_quotes(symbols: str):
    symbol_list = symbols.split(',')
    quotes = []
    for symbol in symbol_list:
        symbol = symbol.strip().upper()
        quotes.append({
            "symbol": symbol,
            "price": 150.0 + hash(symbol) % 100,
            "change": (hash(symbol) % 20) - 10,
            "changePercent": ((hash(symbol) % 20) - 10) / 100,
            "volume": hash(symbol) % 1000000,
            "timestamp": datetime.now().isoformat()
        })
    return {"quotes": quotes}

@app.post("/api/pump-fun/launch")
async def pump_fun_launch(request: Request):
    body = await request.json()
    required_fields = ["name", "symbol", "description", "template", "culturalTheme"]
    missing_fields = [field for field in required_fields if not body.get(field)]
    
    if missing_fields:
        raise HTTPException(status_code=400, detail=f"Missing required fields: {', '.join(missing_fields)}")
    
    return {
        "success": True,
        "message": "Meme launched successfully!",
        "contractAddress": "0x" + "".join([f"{ord(c):02x}" for c in body["name"]])[:40],
        "symbol": body["symbol"],
        "name": body["name"]
    }

@app.get("/api/trading/quote/{symbol}")
async def trading_quote(symbol: str):
    return {
        "symbol": symbol,
        "bid": 149.50,
        "ask": 150.00,
        "timestamp": datetime.now().isoformat()
    }

@app.get("/api/portfolio/recommendations")
async def portfolio_recommendations():
    return {
        "recommendations": [
            {"symbol": "AAPL", "action": "buy", "confidence": 0.85},
            {"symbol": "TSLA", "action": "hold", "confidence": 0.70}
        ]
    }

@app.post("/api/kyc/workflow")
async def kyc_workflow(request: Request):
    return {"success": True, "workflowId": "KYC-12345", "status": "pending"}

@app.post("/api/alpaca/account")
async def alpaca_account(request: Request):
    return {"success": True, "accountId": "ALP-67890", "status": "pending_approval"}

@app.post("/graphql/")
async def graphql_endpoint(request: Request):
    try:
        body = await request.json()
        query_str = body.get("query", "")
        variables = body.get("variables", {})
        
        print(f"🔍 DEBUG: Query received: {query_str[:50]}...")
        
        # Simple query routing based on content - check specific queries first
        if "aiRecommendations" in query_str:
            print("🤖 Returning AI recommendations")
            return {
                "data": {
                    "aiRecommendations": {
                        "portfolioAnalysis": {
                            "totalValue": 125000.0,
                            "numHoldings": 5,
                            "sectorBreakdown": {
                                "Technology": 40.0,
                                "Healthcare": 25.0,
                                "Finance": 20.0,
                                "Consumer": 15.0
                            },
                            "riskScore": 7.2,
                            "diversificationScore": 8.5,
                            "expectedImpact": {
                                "evPct": 12.5,
                                "evAbs": 15625.0,
                                "per10k": 1250.0
                            },
                            "risk": {
                                "volatilityEstimate": 15.8,
                                "maxDrawdownPct": 8.2
                            },
                            "assetAllocation": {
                                "stocks": 85.0,
                                "bonds": 10.0,
                                "cash": 5.0
                            }
                        },
                        "buyRecommendations": [
                            {
                                "symbol": "AAPL",
                                "companyName": "Apple Inc.",
                                "recommendation": "BUY",
                                "confidence": 0.85,
                                "reasoning": "Strong earnings growth and market position",
                                "targetPrice": 160.0,
                                "currentPrice": 150.0,
                                "expectedReturn": 0.067,
                                "allocation": 15.0
                            },
                            {
                                "symbol": "MSFT",
                                "companyName": "Microsoft Corporation",
                                "recommendation": "BUY",
                                "confidence": 0.82,
                                "reasoning": "Cloud growth and AI integration",
                                "targetPrice": 400.0,
                                "currentPrice": 378.0,
                                "expectedReturn": 0.058,
                                "allocation": 12.0
                            }
                        ],
                        "sellRecommendations": [
                            {
                                "symbol": "TSLA",
                                "reasoning": "High volatility and overvaluation concerns"
                            }
                        ],
                        "rebalanceSuggestions": [
                            {
                                "action": "INCREASE",
                                "currentAllocation": 10.0,
                                "suggestedAllocation": 15.0,
                                "reasoning": "Strong fundamentals and growth potential",
                                "priority": "HIGH"
                            }
                        ],
                        "riskAssessment": {
                            "overallRisk": "MODERATE",
                            "volatilityEstimate": 15.8,
                            "recommendations": [
                                "Consider adding more defensive stocks",
                                "Maintain current bond allocation",
                                "Monitor tech sector concentration"
                            ]
                        },
                        "marketOutlook": {
                            "overallSentiment": "BULLISH",
                            "confidence": 0.75,
                            "keyFactors": [
                                "Strong earnings growth",
                                "Fed policy stability",
                                "AI technology adoption"
                            ]
                        }
                    }
                }
            }
        
        elif "tradingPositions" in query_str:
            print("📈 Returning trading positions")
            return {
                "data": {
                    "tradingPositions": [
                        {
                            "id": "pos_001",
                            "symbol": "AAPL",
                            "quantity": 100,
                            "marketValue": 15025.0,
                            "averageCost": 148.5,
                            "unrealizedPL": 175.0,
                            "unrealizedPLPercent": 1.18,
                            "side": "long",
                            "marketPrice": 150.25
                        }
                    ]
                }
            }
        
        elif "tradingOrders" in query_str:
            print("📋 Returning trading orders")
            return {
                "data": {
                    "tradingOrders": [
                        {
                            "id": "order_001",
                            "symbol": "AAPL",
                            "side": "buy",
                            "quantity": 100,
                            "orderType": "market",
                            "status": "filled",
                            "filledQuantity": 100,
                            "averagePrice": 150.25,
                            "createdAt": datetime.now().isoformat()
                        }
                    ]
                }
            }
        
        elif "swingSignals" in query_str:
            print("📡 Returning swing signals")
            return {
                "data": {
                    "swingSignals": [
                        {
                            "id": "signal_001",
                            "symbol": "AAPL",
                            "signalType": "LONG",
                            "entryPrice": 150.25,
                            "targetPrice": 165.5,
                            "stopLoss": 142.0,
                            "mlScore": 0.87,
                            "confidence": 0.92,
                            "reasoning": "Strong momentum with volume spike",
                            "thesis": "Technical breakout with strong volume confirmation"
                        }
                    ]
                }
            }
        
        elif "alpacaAccount" in query_str:
            print("🏦 Returning alpaca account")
            return {
                "data": {
                    "alpacaAccount": {
                        "id": "alpaca_123",
                        "status": "ACTIVE",
                        "buyingPower": 50000.0,
                        "cash": 25000.0,
                        "portfolioValue": 125000.0,
                        "equity": 125000.0,
                        "dayTradeCount": 0
                    }
                }
            }
        
        elif "myPortfolios" in query_str:
            print("💼 Returning portfolios")
            return {
                "data": {
                    "myPortfolios": {
                        "totalPortfolios": 1,
                        "totalValue": 125000.0,
                        "portfolios": [
                            {
                                "name": "Growth Portfolio",
                                "value": 125000.0,
                                "change": 2500.0,
                                "changePercent": 2.04,
                                "holdings": [
                                    {
                                        "symbol": "AAPL",
                                        "shares": 100,
                                        "value": 18592.0,
                                        "weight": 14.87
                                    }
                                ]
                            }
                        ]
                    }
                }
            }
        
        elif "myWatchlist" in query_str:
            print("👀 Returning watchlist")
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
        
        elif "dayTradingPicks" in query_str:
            print("🎯 Returning day trading picks")
            return {
                "data": {
                    "dayTradingPicks": {
                        "asOf": datetime.now().isoformat(),
                        "mode": "SAFE",
                        "picks": [
                            {
                                "symbol": "AAPL",
                                "entryPrice": 150.0,
                                "targetPrice": 155.0,
                                "stopLoss": 145.0,
                                "confidence": 0.85
                            }
                        ]
                    }
                }
            }
        
        elif "advancedStockScreening" in query_str:
            print("🔍 Returning advanced stock screening")
            return {
                "data": {
                    "advancedStockScreening": [
                        {
                            "symbol": "AAPL",
                            "sector": "Technology",
                            "peRatio": 28.5,
                            "dividendYield": 0.0044,
                            "volatility": 0.25,
                            "debtRatio": 0.15,
                            "mlScore": 0.87,
                            "score": 85
                        },
                        {
                            "symbol": "MSFT",
                            "sector": "Technology",
                            "peRatio": 32.1,
                            "dividendYield": 0.0075,
                            "volatility": 0.22,
                            "debtRatio": 0.12,
                            "mlScore": 0.82,
                            "score": 82
                        },
                        {
                            "symbol": "JNJ",
                            "sector": "Healthcare",
                            "peRatio": 24.8,
                            "dividendYield": 0.0295,
                            "volatility": 0.18,
                            "debtRatio": 0.08,
                            "mlScore": 0.75,
                            "score": 78
                        }
                    ]
                }
            }
        
        elif "stocks" in query_str:
            print("📊 Returning stocks data")
            return {
                "data": {
                    "stocks": [
                        {
                            "symbol": "AAPL",
                            "name": "Apple Inc.",
                            "price": 150.0,
                            "change": 2.5,
                            "changePercent": 1.69,
                            "beginnerFriendlyScore": 85,
                            "dividendYield": 0.0044
                        },
                        {
                            "symbol": "TSLA",
                            "name": "Tesla Inc.",
                            "price": 200.0,
                            "change": -5.0,
                            "changePercent": -2.44,
                            "beginnerFriendlyScore": 75,
                            "dividendYield": 0.0
                        }
                    ]
                }
            }
        
        elif "beginnerFriendlyStocks" in query_str:
            print("📚 Returning beginner friendly stocks")
            return {
                "data": {
                    "beginnerFriendlyStocks": [
                        {
                            "id": "stock_001",
                            "symbol": "AAPL",
                            "companyName": "Apple Inc.",
                            "sector": "Technology",
                            "marketCap": 2800000000000,
                            "peRatio": 28.5,
                            "dividendYield": 0.0044,
                            "beginnerFriendlyScore": 85,
                            "currentPrice": 150.0,
                            "beginnerScoreBreakdown": {
                                "score": 85,
                                "factors": [
                                    {
                                        "name": "Market Cap",
                                        "weight": 0.3,
                                        "value": 90,
                                        "contrib": 27,
                                        "detail": "Large cap stock with stable market position"
                                    },
                                    {
                                        "name": "Volatility",
                                        "weight": 0.25,
                                        "value": 80,
                                        "contrib": 20,
                                        "detail": "Moderate volatility suitable for beginners"
                                    },
                                    {
                                        "name": "Dividend",
                                        "weight": 0.2,
                                        "value": 70,
                                        "contrib": 14,
                                        "detail": "Provides steady income stream"
                                    },
                                    {
                                        "name": "Growth",
                                        "weight": 0.25,
                                        "value": 95,
                                        "contrib": 24,
                                        "detail": "Strong growth potential"
                                    }
                                ],
                                "notes": [
                                    "Excellent for beginners due to strong fundamentals",
                                    "Consistent dividend payments",
                                    "Low volatility compared to growth stocks"
                                ]
                            }
                        },
                        {
                            "id": "stock_002",
                            "symbol": "MSFT",
                            "companyName": "Microsoft Corporation",
                            "sector": "Technology",
                            "marketCap": 2800000000000,
                            "peRatio": 32.1,
                            "dividendYield": 0.0075,
                            "beginnerFriendlyScore": 82,
                            "currentPrice": 378.0,
                            "beginnerScoreBreakdown": {
                                "score": 82,
                                "factors": [
                                    {
                                        "name": "Market Cap",
                                        "weight": 0.3,
                                        "value": 95,
                                        "contrib": 28.5,
                                        "detail": "Mega cap with dominant market position"
                                    },
                                    {
                                        "name": "Volatility",
                                        "weight": 0.25,
                                        "value": 75,
                                        "contrib": 18.75,
                                        "detail": "Moderate volatility"
                                    },
                                    {
                                        "name": "Dividend",
                                        "weight": 0.2,
                                        "value": 80,
                                        "contrib": 16,
                                        "detail": "Growing dividend payments"
                                    },
                                    {
                                        "name": "Growth",
                                        "weight": 0.25,
                                        "value": 85,
                                        "contrib": 21.25,
                                        "detail": "Strong cloud and AI growth"
                                    }
                                ],
                                "notes": [
                                    "Great for beginners interested in tech",
                                    "Diversified business model",
                                    "Strong cloud computing presence"
                                ]
                            }
                        },
                        {
                            "id": "stock_003",
                            "symbol": "JNJ",
                            "companyName": "Johnson & Johnson",
                            "sector": "Healthcare",
                            "marketCap": 450000000000,
                            "peRatio": 24.8,
                            "dividendYield": 0.0295,
                            "beginnerFriendlyScore": 88,
                            "currentPrice": 165.0,
                            "beginnerScoreBreakdown": {
                                "score": 88,
                                "factors": [
                                    {
                                        "name": "Market Cap",
                                        "weight": 0.3,
                                        "value": 85,
                                        "contrib": 25.5,
                                        "detail": "Large cap healthcare leader"
                                    },
                                    {
                                        "name": "Volatility",
                                        "weight": 0.25,
                                        "value": 90,
                                        "contrib": 22.5,
                                        "detail": "Low volatility defensive stock"
                                    },
                                    {
                                        "name": "Dividend",
                                        "weight": 0.2,
                                        "value": 95,
                                        "contrib": 19,
                                        "detail": "High dividend yield with long history"
                                    },
                                    {
                                        "name": "Growth",
                                        "weight": 0.25,
                                        "value": 75,
                                        "contrib": 18.75,
                                        "detail": "Steady but moderate growth"
                                    }
                                ],
                                "notes": [
                                    "Perfect for conservative beginners",
                                    "Dividend aristocrat with 60+ years of increases",
                                    "Defensive healthcare sector"
                                ]
                            }
                        }
                    ]
                }
            }
        
        # Handle mutations
        elif "createIncomeProfile" in query_str:
            print("👤 Creating income profile")
            return {
                "data": {
                    "createIncomeProfile": {
                        "success": True,
                        "message": "Profile created successfully"
                    }
                }
            }
        
        elif "placeStockOrder" in query_str:
            print("📊 Placing stock order")
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
            print("🏦 Creating alpaca account")
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
            print("📈 Creating position")
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
        
        # Default: me query (for user profile)
        else:
            print("👤 Returning user profile (default)")
            return {
                "data": {
                    "me": {
                        "id": "demo-user-123",
                        "name": "Demo User",
                        "email": "demo@example.com",
                        "hasPremiumAccess": True,
                        "subscriptionTier": "premium",
                        "incomeProfile": {
                            "incomeBracket": "$75,000 - $100,000",
                            "age": 28,
                            "investmentGoals": ["Wealth Building", "Retirement Savings"],
                            "riskTolerance": "Moderate",
                            "investmentHorizon": "5-10 years"
                        }
                    }
                }
            }
        
    except Exception as e:
        print(f"❌ GraphQL Error: {e}")
        return {
            "data": None,
            "errors": [{"message": str(e)}]
        }

if __name__ == "__main__":
    print("🚀 Starting RichesReach Test Server...")
    print("🌐 Server running on http://localhost:8000")
    print("📊 GraphQL endpoint: http://localhost:8000/graphql/")
    print("❤️  Health Check: http://localhost:8000/health")
    print("")
    print("Press Ctrl+C to stop the server")
    
    uvicorn.run(app, host="0.0.0.0", port=8000)
