#!/usr/bin/env python3
"""
Final Complete Server for RichesReach - All GraphQL fields included
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import os
import logging
from datetime import datetime, timedelta
import jwt
import hashlib
import json
import random
import asyncio
import aiohttp
import requests

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="RichesReach Final Complete Server",
    description="Complete server with ALL GraphQL fields",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API Keys
ALPHA_VANTAGE_KEY = "OHYSFF1AE446O7CR"
FINNHUB_KEY = "d2rnitpr01qv11lfegugd2rnitpr01qv11lfegv0"
NEWS_API_KEY = "94a335c7316145f79840edd62f77e11e"

def get_real_buy_recommendations():
    """Get buy recommendations using real FinnHub API data"""
    print("🚀 Starting real buy recommendations generation...")
    
    symbols = ["AAPL", "MSFT", "GOOGL", "AMZN", "TSLA"]
    recommendations = []
    
    for symbol in symbols:
        try:
            # Get real quote data from FinnHub
            quote_url = f"https://finnhub.io/api/v1/quote?symbol={symbol}&token={FINNHUB_KEY}"
            quote_response = requests.get(quote_url, timeout=10)
            
            if quote_response.status_code == 200:
                quote_data = quote_response.json()
                current_price = quote_data.get('c', 0)  # current price
                change_percent = quote_data.get('dp', 0)  # change percent
                
                # Get company profile for better company name
                profile_url = f"https://finnhub.io/api/v1/stock/profile2?symbol={symbol}&token={FINNHUB_KEY}"
                profile_response = requests.get(profile_url, timeout=10)
                
                company_name = f"{symbol} Inc."  # fallback
                if profile_response.status_code == 200:
                    profile_data = profile_response.json()
                    company_name = profile_data.get('name', company_name)
                
                # Generate recommendation based on real data
                if change_percent > 3:
                    recommendation = "STRONG BUY"
                    confidence = 0.9
                    reasoning = f"Strong positive momentum with {change_percent:.1f}% gain"
                elif change_percent > 0:
                    recommendation = "BUY"
                    confidence = 0.75
                    reasoning = f"Positive momentum with {change_percent:.1f}% gain"
                elif change_percent > -2:
                    recommendation = "HOLD"
                    confidence = 0.6
                    reasoning = f"Stable performance with {change_percent:.1f}% change"
                else:
                    recommendation = "WEAK BUY"
                    confidence = 0.4
                    reasoning = f"Potential buying opportunity with {change_percent:.1f}% decline"
                
                target_price = round(current_price * (1 + random.uniform(0.05, 0.15)), 2)
                expected_return = round(random.uniform(5, 15), 1)
                
                recommendations.append({
                    "symbol": symbol,
                    "companyName": company_name,
                    "recommendation": recommendation,
                    "confidence": confidence,
                    "reasoning": reasoning,
                    "targetPrice": target_price,
                    "currentPrice": current_price,
                    "expectedReturn": expected_return,
                    "allocation": [
                        {
                            "symbol": symbol,
                            "percentage": round(random.uniform(8, 20), 1),
                            "reasoning": f"Strategic allocation based on {recommendation.lower()} rating"
                        }
                    ],
                    "__typename": "BuyRecommendation"
                })
                
                print(f"✅ Got real data for {symbol}: ${current_price} ({change_percent:.1f}%)")
                
            else:
                print(f"❌ Failed to get quote for {symbol}: {quote_response.status_code}")
                # Fallback to mock data for this symbol
                current_price = round(random.uniform(50, 500), 2)
                change_percent = round(random.uniform(-5, 8), 2)
                
                if change_percent > 3:
                    recommendation = "STRONG BUY"
                    confidence = 0.9
                elif change_percent > 0:
                    recommendation = "BUY"
                    confidence = 0.75
                elif change_percent > -2:
                    recommendation = "HOLD"
                    confidence = 0.6
                else:
                    recommendation = "WEAK BUY"
                    confidence = 0.4
                
                recommendations.append({
                    "symbol": symbol,
                    "companyName": f"{symbol} Inc.",
                    "recommendation": recommendation,
                    "confidence": confidence,
                    "reasoning": f"Fallback data - {change_percent:.1f}% change",
                    "targetPrice": round(current_price * 1.1, 2),
                    "currentPrice": current_price,
                    "expectedReturn": round(random.uniform(5, 15), 1),
                    "allocation": [
                        {
                            "symbol": symbol,
                            "percentage": round(random.uniform(8, 20), 1),
                            "reasoning": f"Strategic allocation based on {recommendation.lower()} rating"
                        }
                    ],
                    "__typename": "BuyRecommendation"
                })
                
        except Exception as e:
            print(f"❌ Error getting data for {symbol}: {e}")
            # Fallback to mock data
            current_price = round(random.uniform(50, 500), 2)
            change_percent = round(random.uniform(-5, 8), 2)
            
            recommendations.append({
                "symbol": symbol,
                "companyName": f"{symbol} Inc.",
                "recommendation": "BUY",
                "confidence": 0.7,
                "reasoning": f"Error fallback - {change_percent:.1f}% change",
                "targetPrice": round(current_price * 1.1, 2),
                "currentPrice": current_price,
                "expectedReturn": round(random.uniform(5, 15), 1),
                "allocation": [
                    {
                        "symbol": symbol,
                        "percentage": round(random.uniform(8, 20), 1),
                        "reasoning": "Strategic allocation based on buy rating"
                    }
                ],
                "__typename": "BuyRecommendation"
            })
    
    print(f"✅ Generated {len(recommendations)} buy recommendations (mix of real and fallback data)")
    return recommendations

# JWT Configuration
SECRET_KEY = "your-secret-key-change-in-production"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

# Mock user database
users_db = {
    "test@example.com": {
        "id": "user_123",
        "name": "Test User",
        "email": "test@example.com",
        "password": hashlib.sha256("testpass".encode()).hexdigest(),
        "hasPremiumAccess": True,
        "subscriptionTier": "premium"
    }
}

def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

@app.get("/")
async def root():
    return {"message": "RichesReach Final Complete Server", "status": "running"}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

@app.post("/graphql/")
async def graphql_endpoint(request_data: dict):
    query = request_data.get("query", "")
    variables = request_data.get("variables", {})
    
    print(f"=== QUERY DEBUG ===")
    print(f"Raw query: {query}")
    print(f"Variables: {variables}")
    
    try:
        response_data = {}
        
        # Handle mutations first
        if "generateAiRecommendations" in query:
            print("🎯 DETECTED generateAiRecommendations mutation!")
            response_data["generateAiRecommendations"] = {
                "success": True,
                "message": "AI recommendations generated successfully",
                "recommendations": [
                    {
                        "id": "rec_1",
                        "riskProfile": "Moderate",
                        "portfolioAllocation": {
                            "stocks": 60,
                            "bonds": 30,
                            "cash": 10
                        },
                        "recommendedStocks": [
                            {
                                "symbol": "AAPL",
                                "companyName": "Apple Inc.",
                                "allocation": 15.0,
                                "reasoning": "Strong fundamentals and market position"
                            },
                            {
                                "symbol": "MSFT",
                                "companyName": "Microsoft Corporation",
                                "allocation": 12.0,
                                "reasoning": "Cloud leadership and strong cash flow"
                            },
                            {
                                "symbol": "JNJ",
                                "companyName": "Johnson & Johnson",
                                "allocation": 8.0,
                                "reasoning": "Stable healthcare dividend stock"
                            }
                        ],
                        "expectedPortfolioReturn": 12.5,
                        "riskAssessment": {
                            "volatility": 15.2,
                            "maxDrawdown": -8.5,
                            "sharpeRatio": 1.8
                        },
                        "__typename": "AIRecommendation"
                    },
                    {
                        "id": "rec_2",
                        "riskProfile": "Conservative",
                        "portfolioAllocation": {
                            "stocks": 40,
                            "bonds": 50,
                            "cash": 10
                        },
                        "recommendedStocks": [
                            {
                                "symbol": "PG",
                                "companyName": "Procter & Gamble",
                                "allocation": 10.0,
                                "reasoning": "Defensive consumer staples"
                            },
                            {
                                "symbol": "JNJ",
                                "companyName": "Johnson & Johnson",
                                "allocation": 12.0,
                                "reasoning": "Stable healthcare with dividends"
                            }
                        ],
                        "expectedPortfolioReturn": 8.5,
                        "riskAssessment": {
                            "volatility": 10.8,
                            "maxDrawdown": -5.2,
                            "sharpeRatio": 1.2
                        },
                        "__typename": "AIRecommendation"
                    }
                ],
                "__typename": "GenerateAIRecommendationsResponse"
            }
            return {"data": response_data}

        if "createIncomeProfile" in query:
            print("🎯 DETECTED createIncomeProfile mutation!")
            income_bracket = variables.get("incomeBracket", "")
            age = variables.get("age", 0)
            investment_goals = variables.get("investmentGoals", [])
            risk_tolerance = variables.get("riskTolerance", "")
            investment_horizon = variables.get("investmentHorizon", "")
            
            # Validate required fields
            if not income_bracket or not risk_tolerance or not investment_horizon:
                return {"errors": [{"message": "Missing required fields for income profile creation"}]}
            
            # Update user's income profile
            if "test@example.com" in users_db:
                users_db["test@example.com"]["incomeProfile"] = {
                    "id": "profile_1",
                    "incomeBracket": income_bracket,
                    "age": age,
                    "investmentGoals": investment_goals,
                    "riskTolerance": risk_tolerance,
                    "investmentHorizon": investment_horizon,
                    "__typename": "IncomeProfile"
                }
            
            return {
                "data": {
                    "createIncomeProfile": {
                        "success": True,
                        "message": "Income profile created successfully",
                        "__typename": "CreateIncomeProfileResponse"
                    }
                }
            }

        if "tokenAuth" in query:
            email = variables.get("email", "")
            password = variables.get("password", "")
            
            if not email or not password:
                return {"errors": [{"message": "Email and password are required"}]}
            
            user = users_db.get(email.lower())
            if not user or user["password"] != hashlib.sha256(password.encode()).hexdigest():
                return {"errors": [{"message": "Invalid credentials"}]}
            
            access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
            access_token = create_access_token(
                data={"sub": email.lower()}, expires_delta=access_token_expires
            )
            
            return {
                "data": {
                    "tokenAuth": {
                        "token": access_token,
                        "refreshToken": access_token,
                        "user": {
                            "id": user["id"],
                            "email": user["email"],
                            "name": user["name"],
                            "hasPremiumAccess": user["hasPremiumAccess"],
                            "subscriptionTier": user["subscriptionTier"],
                            "__typename": "User"
                        },
                        "__typename": "TokenAuth"
                    }
                }
            }

        # Handle specific queries with explicit detection
        response_data = {}
        
        # Check for beginnerFriendlyStocks query
        if "beginnerFriendlyStocks" in query:
            print("🎯 DETECTED beginnerFriendlyStocks query!")
            response_data["beginnerFriendlyStocks"] = [
                {
                    "id": "1",
                    "symbol": "AAPL",
                    "companyName": "Apple Inc.",
                    "sector": "Technology",
                    "marketCap": 3000000000000,
                    "peRatio": 25.5,
                    "dividendYield": 0.5,
                    "beginnerFriendlyScore": 85,
                    "__typename": "Stock"
                },
                {
                    "id": "2",
                    "symbol": "MSFT",
                    "companyName": "Microsoft Corporation",
                    "sector": "Technology",
                    "marketCap": 2800000000000,
                    "peRatio": 28.0,
                    "dividendYield": 0.7,
                    "beginnerFriendlyScore": 88,
                    "__typename": "Stock"
                },
                {
                    "id": "3",
                    "symbol": "GOOGL",
                    "companyName": "Alphabet Inc.",
                    "sector": "Technology",
                    "marketCap": 1800000000000,
                    "peRatio": 22.5,
                    "dividendYield": 0.0,
                    "beginnerFriendlyScore": 75,
                    "__typename": "Stock"
                },
                {
                    "id": "4",
                    "symbol": "JNJ",
                    "companyName": "Johnson & Johnson",
                    "sector": "Healthcare",
                    "marketCap": 400000000000,
                    "peRatio": 15.2,
                    "dividendYield": 2.8,
                    "beginnerFriendlyScore": 92,
                    "__typename": "Stock"
                },
                {
                    "id": "5",
                    "symbol": "PG",
                    "companyName": "Procter & Gamble",
                    "sector": "Consumer Staples",
                    "marketCap": 350000000000,
                    "peRatio": 24.8,
                    "dividendYield": 2.5,
                    "beginnerFriendlyScore": 90,
                    "__typename": "Stock"
                }
            ]
            return {"data": response_data}

        # Check for myWatchlist query
        if "myWatchlist" in query:
            print("🎯 DETECTED myWatchlist query!")
            response_data["myWatchlist"] = [
                {
                    "id": "watch_1",
                    "stock": {
                        "id": "1",
                        "symbol": "AAPL",
                        "companyName": "Apple Inc.",
                        "sector": "Technology",
                        "beginnerFriendlyScore": 85,
                        "currentPrice": 175.5,
                        "__typename": "Stock"
                    },
                    "addedAt": "2024-01-15T10:00:00Z",
                    "notes": "Core technology holding",
                    "targetPrice": 200.0,
                    "__typename": "WatchlistItem"
                },
                {
                    "id": "watch_2",
                    "stock": {
                        "id": "2",
                        "symbol": "MSFT",
                        "companyName": "Microsoft Corporation",
                        "sector": "Technology",
                        "beginnerFriendlyScore": 88,
                        "currentPrice": 380.25,
                        "__typename": "Stock"
                    },
                    "addedAt": "2024-01-16T14:30:00Z",
                    "notes": "Cloud leadership play",
                    "targetPrice": 400.0,
                    "__typename": "WatchlistItem"
                },
                {
                    "id": "watch_3",
                    "stock": {
                        "id": "3",
                        "symbol": "GOOGL",
                        "companyName": "Alphabet Inc.",
                        "sector": "Technology",
                        "beginnerFriendlyScore": 75,
                        "currentPrice": 140.0,
                        "__typename": "Stock"
                    },
                    "addedAt": "2024-01-17T09:15:00Z",
                    "notes": "AI and search dominance",
                    "targetPrice": 160.0,
                    "__typename": "WatchlistItem"
                }
            ]
            return {"data": response_data}

        # Check for myPortfolios query
        if "myPortfolios" in query:
            print("🎯 DETECTED myPortfolios query!")
            response_data["myPortfolios"] = {
                "totalPortfolios": 2,
                "totalValue": 125000.0,
                "portfolios": [
                    {
                        "name": "Tech Growth Portfolio",
                        "totalValue": 75000.0,
                        "holdingsCount": 5,
                        "holdings": [
                            {
                                "id": "pos_1",
                                "stock": {
                                    "id": "1",
                                    "symbol": "AAPL",
                                    "companyName": "Apple Inc.",
                                    "__typename": "Stock"
                                },
                                "shares": 50,
                                "averagePrice": 150.0,
                                "currentPrice": 175.5,
                                "totalValue": 8775.0,
                                "notes": "Core holding",
                                "createdAt": "2024-01-15T10:00:00Z",
                                "updatedAt": "2024-01-20T14:30:00Z",
                                "__typename": "Position"
                            },
                            {
                                "id": "pos_2",
                                "stock": {
                                    "id": "2",
                                    "symbol": "MSFT",
                                    "companyName": "Microsoft Corporation",
                                    "__typename": "Stock"
                                },
                                "shares": 30,
                                "averagePrice": 350.0,
                                "currentPrice": 380.25,
                                "totalValue": 11407.5,
                                "notes": "Cloud leadership",
                                "createdAt": "2024-01-16T14:30:00Z",
                                "updatedAt": "2024-01-20T14:30:00Z",
                                "__typename": "Position"
                            },
                            {
                                "id": "pos_3",
                                "stock": {
                                    "id": "3",
                                    "symbol": "GOOGL",
                                    "companyName": "Alphabet Inc.",
                                    "__typename": "Stock"
                                },
                                "shares": 25,
                                "averagePrice": 130.0,
                                "currentPrice": 140.0,
                                "totalValue": 3500.0,
                                "notes": "AI growth play",
                                "createdAt": "2024-01-17T09:15:00Z",
                                "updatedAt": "2024-01-20T14:30:00Z",
                                "__typename": "Position"
                            },
                            {
                                "id": "pos_4",
                                "stock": {
                                    "id": "4",
                                    "symbol": "AMZN",
                                    "companyName": "Amazon.com Inc.",
                                    "__typename": "Stock"
                                },
                                "shares": 20,
                                "averagePrice": 3200.0,
                                "currentPrice": 3400.0,
                                "totalValue": 68000.0,
                                "notes": "E-commerce leader",
                                "createdAt": "2024-01-18T11:45:00Z",
                                "updatedAt": "2024-01-20T14:30:00Z",
                                "__typename": "Position"
                            },
                            {
                                "id": "pos_5",
                                "stock": {
                                    "id": "5",
                                    "symbol": "TSLA",
                                    "companyName": "Tesla Inc.",
                                    "__typename": "Stock"
                                },
                                "shares": 10,
                                "averagePrice": 200.0,
                                "currentPrice": 220.0,
                                "totalValue": 2200.0,
                                "notes": "EV innovation",
                                "createdAt": "2024-01-19T16:20:00Z",
                                "updatedAt": "2024-01-20T14:30:00Z",
                                "__typename": "Position"
                            }
                        ],
                        "__typename": "Portfolio"
                    },
                    {
                        "name": "Dividend Income Portfolio",
                        "totalValue": 50000.0,
                        "holdingsCount": 3,
                        "holdings": [
                            {
                                "id": "pos_6",
                                "stock": {
                                    "id": "6",
                                    "symbol": "JNJ",
                                    "companyName": "Johnson & Johnson",
                                    "__typename": "Stock"
                                },
                                "shares": 100,
                                "averagePrice": 160.0,
                                "currentPrice": 165.0,
                                "totalValue": 16500.0,
                                "notes": "Stable dividend",
                                "createdAt": "2024-01-10T08:00:00Z",
                                "updatedAt": "2024-01-20T14:30:00Z",
                                "__typename": "Position"
                            },
                            {
                                "id": "pos_7",
                                "stock": {
                                    "id": "7",
                                    "symbol": "PG",
                                    "companyName": "Procter & Gamble Co.",
                                    "__typename": "Stock"
                                },
                                "shares": 80,
                                "averagePrice": 150.0,
                                "currentPrice": 155.0,
                                "totalValue": 12400.0,
                                "notes": "Consumer staples",
                                "createdAt": "2024-01-12T13:15:00Z",
                                "updatedAt": "2024-01-20T14:30:00Z",
                                "__typename": "Position"
                            },
                            {
                                "id": "pos_8",
                                "stock": {
                                    "id": "8",
                                    "symbol": "KO",
                                    "companyName": "The Coca-Cola Company",
                                    "__typename": "Stock"
                                },
                                "shares": 120,
                                "averagePrice": 60.0,
                                "currentPrice": 62.0,
                                "totalValue": 7440.0,
                                "notes": "Beverage giant",
                                "createdAt": "2024-01-14T10:30:00Z",
                                "updatedAt": "2024-01-20T14:30:00Z",
                                "__typename": "Position"
                            }
                        ],
                        "__typename": "Portfolio"
                    }
                ],
                "__typename": "MyPortfolios"
            }
            return {"data": response_data}

        # Check for portfolioMetrics query
        if "portfolioMetrics" in query:
            print("🎯 DETECTED portfolioMetrics query!")
            
            # Get real data for portfolio holdings
            holdings_data = [
                {"symbol": "AAPL", "shares": 50, "costBasis": 7500.0, "sector": "Technology"},
                {"symbol": "MSFT", "shares": 30, "costBasis": 10000.0, "sector": "Technology"},
                {"symbol": "JNJ", "shares": 25, "costBasis": 3500.0, "sector": "Healthcare"},
                {"symbol": "JPM", "shares": 20, "costBasis": 2800.0, "sector": "Finance"},
                {"symbol": "PG", "shares": 15, "costBasis": 2000.0, "sector": "Consumer"}
            ]
            
            holdings = []
            total_value = 0
            total_cost = 0
            day_change = 0
            
            for holding in holdings_data:
                try:
                    # Get real quote data
                    quote_url = f"https://finnhub.io/api/v1/quote?symbol={holding['symbol']}&token={FINNHUB_KEY}"
                    quote_response = requests.get(quote_url, timeout=10)
                    
                    if quote_response.status_code == 200:
                        quote_data = quote_response.json()
                        current_price = quote_data.get('c', 0)
                        change_percent = quote_data.get('dp', 0)
                        
                        # Get company profile
                        profile_url = f"https://finnhub.io/api/v1/stock/profile2?symbol={holding['symbol']}&token={FINNHUB_KEY}"
                        profile_response = requests.get(profile_url, timeout=10)
                        
                        company_name = f"{holding['symbol']} Inc."
                        if profile_response.status_code == 200:
                            profile_data = profile_response.json()
                            company_name = profile_data.get('name', company_name)
                        
                        total_value_holding = current_price * holding['shares']
                        return_amount = total_value_holding - holding['costBasis']
                        return_percent = (return_amount / holding['costBasis']) * 100
                        day_change_holding = total_value_holding * (change_percent / 100)
                        
                        holdings.append({
                            "symbol": holding['symbol'],
                            "companyName": company_name,
                            "shares": holding['shares'],
                            "currentPrice": current_price,
                            "totalValue": total_value_holding,
                            "costBasis": holding['costBasis'],
                            "returnAmount": return_amount,
                            "returnPercent": return_percent,
                            "sector": holding['sector'],
                            "__typename": "Holding"
                        })
                        
                        total_value += total_value_holding
                        total_cost += holding['costBasis']
                        day_change += day_change_holding
                        
                        print(f"✅ Got real data for {holding['symbol']}: ${current_price} ({change_percent:.1f}%)")
                        
                    else:
                        # Fallback to mock data
                        current_price = round(random.uniform(50, 500), 2)
                        total_value_holding = current_price * holding['shares']
                        return_amount = total_value_holding - holding['costBasis']
                        return_percent = (return_amount / holding['costBasis']) * 100
                        
                        holdings.append({
                            "symbol": holding['symbol'],
                            "companyName": f"{holding['symbol']} Inc.",
                            "shares": holding['shares'],
                            "currentPrice": current_price,
                            "totalValue": total_value_holding,
                            "costBasis": holding['costBasis'],
                            "returnAmount": return_amount,
                            "returnPercent": return_percent,
                            "sector": holding['sector'],
                            "__typename": "Holding"
                        })
                        
                        total_value += total_value_holding
                        total_cost += holding['costBasis']
                        
                except Exception as e:
                    print(f"❌ Error getting data for {holding['symbol']}: {e}")
                    # Fallback to mock data
                    current_price = round(random.uniform(50, 500), 2)
                    total_value_holding = current_price * holding['shares']
                    return_amount = total_value_holding - holding['costBasis']
                    return_percent = (return_amount / holding['costBasis']) * 100
                    
                    holdings.append({
                        "symbol": holding['symbol'],
                        "companyName": f"{holding['symbol']} Inc.",
                        "shares": holding['shares'],
                        "currentPrice": current_price,
                        "totalValue": total_value_holding,
                        "costBasis": holding['costBasis'],
                        "returnAmount": return_amount,
                        "returnPercent": return_percent,
                        "sector": holding['sector'],
                        "__typename": "Holding"
                    })
                    
                    total_value += total_value_holding
                    total_cost += holding['costBasis']
            
            total_return = total_value - total_cost
            total_return_percent = (total_return / total_cost) * 100 if total_cost > 0 else 0
            day_change_percent = (day_change / total_value) * 100 if total_value > 0 else 0
            
            response_data["portfolioMetrics"] = {
                "totalValue": total_value,
                "totalCost": total_cost,
                "totalReturn": total_return,
                "totalReturnPercent": total_return_percent,
                "dayChange": day_change,
                "dayChangePercent": day_change_percent,
                "volatility": 15.2,  # Keep mock for now
                "sharpeRatio": 1.8,  # Keep mock for now
                "maxDrawdown": -8.5,  # Keep mock for now
                "beta": 1.2,  # Keep mock for now
                "alpha": 2.3,  # Keep mock for now
                "sectorAllocation": {
                    "Technology": 40,
                    "Healthcare": 20,
                    "Finance": 15,
                    "Consumer": 15,
                    "Other": 10
                },
                "riskMetrics": {
                    "var95": -5.2,
                    "cvar95": -7.8,
                    "volatility": 15.2
                },
                "holdings": holdings,
                "__typename": "PortfolioMetrics"
            }
            return {"data": response_data}

        # Check for aiRecommendations query (what the app actually uses)
        if "aiRecommendations" in query:
            print("🎯 DETECTED aiRecommendations query!")
            response_data["aiRecommendations"] = {
                "portfolioAnalysis": {
                    "totalValue": 50000,
                    "numHoldings": 5,
                    "sectorBreakdown": {
                        "Technology": 40,
                        "Healthcare": 20,
                        "Finance": 15,
                        "Consumer": 15,
                        "Other": 10
                    },
                    "riskScore": 7.2,
                    "diversificationScore": 8.5,
                    "expectedImpact": {
                        "evPct": 12.5,
                        "evAbs": 6250,
                        "per10k": 1250,
                        "__typename": "ExpectedImpact"
                    },
                    "risk": {
                        "volatilityEstimate": 15.2,
                        "maxDrawdownPct": -8.5,
                        "__typename": "Risk"
                    },
                    "assetAllocation": {
                        "stocks": 60,
                        "bonds": 30,
                        "cash": 10,
                        "__typename": "AssetAllocation"
                    },
                    "__typename": "PortfolioAnalysis"
                },
                "buyRecommendations": get_real_buy_recommendations(),
                "sellRecommendations": [
                    {
                        "symbol": "TSLA",
                        "reasoning": "High volatility and overvaluation concerns",
                        "__typename": "SellRecommendation"
                    }
                ],
                "rebalanceSuggestions": [
                    {
                        "action": "INCREASE",
                        "currentAllocation": 40,
                        "suggestedAllocation": 50,
                        "reasoning": "Technology sector showing strong growth",
                        "priority": "HIGH",
                        "__typename": "RebalanceSuggestion"
                    }
                ],
                "riskAssessment": {
                    "overallRisk": "MODERATE",
                    "volatilityEstimate": 15.2,
                    "recommendations": [
                        "Consider increasing bond allocation for stability",
                        "Monitor technology sector concentration"
                    ],
                    "__typename": "RiskAssessment"
                },
                "marketOutlook": {
                    "overallSentiment": "BULLISH",
                    "confidence": 0.75,
                    "keyFactors": [
                        "Strong corporate earnings",
                        "Federal Reserve policy support",
                        "Technology sector growth"
                    ],
                    "__typename": "MarketOutlook"
                },
                "__typename": "AIRecommendations"
            }
            return {"data": response_data}

        # Check for generateAiRecommendations query
        if "generateAiRecommendations" in query:
            print("🎯 DETECTED generateAiRecommendations query!")
            response_data["generateAiRecommendations"] = [
                {
                    "id": "rec_1",
                    "action": "BUY",
                    "symbol": "AAPL",
                    "companyName": "Apple Inc.",
                    "currentPrice": 175.5,
                    "targetPrice": 185.0,
                    "expectedImpact": "Positive",
                    "risk": "Low",
                    "confidence": 0.85,
                    "reasoning": "Strong fundamentals and positive market sentiment",
                    "timeHorizon": "3-6 months",
                    "assetAllocation": {
                        "stocks": 60,
                        "bonds": 30,
                        "cash": 10
                    },
                    "allocation": [
                        {
                            "symbol": "AAPL",
                            "percentage": 15.0,
                            "reasoning": "Core technology holding"
                        },
                        {
                            "symbol": "MSFT",
                            "percentage": 12.0,
                            "reasoning": "Cloud leadership"
                        }
                    ],
                    "__typename": "AIRecommendation"
                }
            ]
            return {"data": response_data}


        # Check for rustStockAnalysis query
        if "rustStockAnalysis" in query:
            print("🎯 DETECTED rustStockAnalysis query!")
            symbol = variables.get("symbol", "AAPL")
            response_data["rustStockAnalysis"] = {
                "symbol": symbol,
                "beginnerFriendlyScore": random.randint(70, 95),
                "riskLevel": random.choice(["Low", "Medium", "High"]),
                "recommendation": random.choice(["Strong Buy", "Buy", "Hold", "Sell"]),
                "technicalIndicators": {
                    "rsi": round(random.uniform(20, 80), 2),
                    "macd": round(random.uniform(-2, 2), 3),
                    "macdSignal": round(random.uniform(-2, 2), 3),
                    "macdHistogram": round(random.uniform(-1, 1), 3),
                    "sma20": round(random.uniform(100, 200), 2),
                    "sma50": round(random.uniform(100, 200), 2),
                    "ema12": round(random.uniform(100, 200), 2),
                    "ema26": round(random.uniform(100, 200), 2),
                    "bollingerUpper": round(random.uniform(150, 250), 2),
                    "bollingerLower": round(random.uniform(100, 150), 2),
                    "bollingerMiddle": round(random.uniform(120, 180), 2),
                    "__typename": "TechnicalIndicators"
                },
                "fundamentalAnalysis": {
                    "valuationScore": round(random.uniform(1, 10), 1),
                    "growthScore": round(random.uniform(1, 10), 1),
                    "stabilityScore": round(random.uniform(1, 10), 1),
                    "dividendScore": round(random.uniform(1, 10), 1),
                    "debtScore": round(random.uniform(1, 10), 1),
                    "__typename": "FundamentalAnalysis"
                },
                "reasoning": f"Based on technical and fundamental analysis, {symbol} shows strong performance indicators with favorable risk-reward ratio.",
                "__typename": "RustStockAnalysis"
            }
            return {"data": response_data}

        # Check for advancedStockScreening query
        if "advancedStockScreening" in query:
            print("🎯 DETECTED advancedStockScreening query!")
            response_data["advancedStockScreening"] = [
                {
                    "symbol": "AAPL",
                    "companyName": "Apple Inc.",
                    "sector": "Technology",
                    "marketCap": 3000000000000,
                    "peRatio": 25.5,
                    "dividendYield": 0.5,
                    "beginnerFriendlyScore": 85,
                    "currentPrice": 175.5,
                    "volatility": 15.2,
                    "debtRatio": 0.3,
                    "reasoning": "Strong fundamentals and market position",
                    "score": 8.5,
                    "mlScore": 0.85,
                    "__typename": "AdvancedStock"
                },
                {
                    "symbol": "MSFT",
                    "companyName": "Microsoft Corporation",
                    "sector": "Technology",
                    "marketCap": 2800000000000,
                    "peRatio": 28.0,
                    "dividendYield": 0.7,
                    "beginnerFriendlyScore": 88,
                    "currentPrice": 380.25,
                    "volatility": 14.8,
                    "debtRatio": 0.25,
                    "reasoning": "Cloud leadership and strong cash flow",
                    "score": 8.8,
                    "mlScore": 0.88,
                    "__typename": "AdvancedStock"
                },
                {
                    "symbol": "GOOGL",
                    "companyName": "Alphabet Inc.",
                    "sector": "Technology",
                    "marketCap": 1800000000000,
                    "peRatio": 22.5,
                    "dividendYield": 0.0,
                    "beginnerFriendlyScore": 75,
                    "currentPrice": 140.0,
                    "volatility": 18.5,
                    "debtRatio": 0.15,
                    "reasoning": "AI and search dominance with growth potential",
                    "score": 8.2,
                    "mlScore": 0.82,
                    "__typename": "AdvancedStock"
                },
                {
                    "symbol": "JNJ",
                    "companyName": "Johnson & Johnson",
                    "sector": "Healthcare",
                    "marketCap": 400000000000,
                    "peRatio": 15.2,
                    "dividendYield": 2.8,
                    "beginnerFriendlyScore": 92,
                    "currentPrice": 160.0,
                    "volatility": 12.3,
                    "debtRatio": 0.35,
                    "reasoning": "Stable healthcare giant with consistent dividends",
                    "score": 7.8,
                    "mlScore": 0.78,
                    "__typename": "AdvancedStock"
                },
                {
                    "symbol": "PG",
                    "companyName": "Procter & Gamble",
                    "sector": "Consumer Staples",
                    "marketCap": 350000000000,
                    "peRatio": 24.8,
                    "dividendYield": 2.5,
                    "beginnerFriendlyScore": 90,
                    "currentPrice": 145.0,
                    "volatility": 10.8,
                    "debtRatio": 0.28,
                    "reasoning": "Defensive consumer staples with strong brand portfolio",
                    "score": 7.5,
                    "mlScore": 0.75,
                    "__typename": "AdvancedStock"
                }
            ]
            return {"data": response_data}

        # Check for optionsAnalysis query
        if "optionsAnalysis" in query:
            print("🎯 DETECTED optionsAnalysis query!")
            symbol = variables.get("symbol", "AAPL")
            response_data["optionsAnalysis"] = {
                "underlyingSymbol": symbol,
                "underlyingPrice": 175.5,
                "optionsChain": {
                    "expirationDates": ["2024-02-16", "2024-03-15"],
                    "calls": [
                        {
                            "symbol": f"{symbol}240216C00180000",
                            "contractSymbol": f"{symbol}240216C00180000",
                            "strike": 180.0,
                            "expirationDate": "2024-02-16",
                            "optionType": "call",
                            "bid": 2.5,
                            "ask": 2.7,
                            "lastPrice": 2.6,
                            "volume": 1500,
                            "openInterest": 5000,
                            "impliedVolatility": 0.25,
                            "delta": 0.45,
                            "gamma": 0.02,
                            "theta": -0.15,
                            "vega": 0.8,
                            "rho": 0.05,
                            "intrinsicValue": 0.0,
                            "timeValue": 2.6,
                            "daysToExpiration": 30,
                            "__typename": "Option"
                        }
                    ],
                    "puts": [],
                    "greeks": {
                        "delta": 0.45,
                        "gamma": 0.02,
                        "theta": -0.15,
                        "vega": 0.8,
                        "rho": 0.05,
                        "__typename": "Greeks"
                    },
                    "__typename": "OptionsChain"
                },
                "unusualFlow": {
                    "symbol": symbol,
                    "contractSymbol": f"{symbol}240216C00180000",
                    "optionType": "call",
                    "strike": 180.0,
                    "expirationDate": "2024-02-16",
                    "volume": 1500,
                    "openInterest": 5000,
                    "premium": 3900.0,
                    "impliedVolatility": 0.25,
                    "unusualActivityScore": 8.5,
                    "activityType": "bullish",
                    "__typename": "UnusualFlow"
                },
                "recommendedStrategies": [
                    {
                        "strategyName": "Covered Call",
                        "strategyType": "income",
                        "description": "Sell call options against stock holdings",
                        "riskLevel": "low",
                        "marketOutlook": "neutral",
                        "maxProfit": 2.6,
                        "maxLoss": -175.5,
                        "breakevenPoints": [175.5],
                        "probabilityOfProfit": 0.65,
                        "riskRewardRatio": 0.015,
                        "daysToExpiration": 30,
                        "totalCost": 0,
                        "totalCredit": 2.6,
                        "__typename": "Strategy"
                    }
                ],
                "marketSentiment": {
                    "putCallRatio": 0.8,
                    "impliedVolatilityRank": 0.6,
                    "skew": 0.1,
                    "sentimentScore": 0.7,
                    "sentimentDescription": "Bullish",
                    "__typename": "MarketSentiment"
                },
                "__typename": "OptionsAnalysis"
            }
            return {"data": response_data}

        # Check for stocks query
        if "stocks" in query:
            print("🎯 DETECTED stocks query!")
            response_data["stocks"] = [
                {
                    "id": "stock_1",
                    "symbol": "AAPL",
                    "companyName": "Apple Inc.",
                    "sector": "Technology",
                    "marketCap": 3000000000000,
                    "peRatio": 25.5,
                    "dividendYield": 0.5,
                    "beginnerFriendlyScore": 85,
                    "__typename": "Stock"
                },
                {
                    "id": "stock_2",
                    "symbol": "MSFT",
                    "companyName": "Microsoft Corporation",
                    "sector": "Technology",
                    "marketCap": 2800000000000,
                    "peRatio": 28.2,
                    "dividendYield": 0.7,
                    "beginnerFriendlyScore": 88,
                    "__typename": "Stock"
                },
                {
                    "id": "stock_3",
                    "symbol": "GOOGL",
                    "companyName": "Alphabet Inc.",
                    "sector": "Technology",
                    "marketCap": 1800000000000,
                    "peRatio": 22.1,
                    "dividendYield": 0.0,
                    "beginnerFriendlyScore": 82,
                    "__typename": "Stock"
                },
                {
                    "id": "stock_4",
                    "symbol": "TSLA",
                    "companyName": "Tesla Inc.",
                    "sector": "Automotive",
                    "marketCap": 800000000000,
                    "peRatio": 45.3,
                    "dividendYield": 0.0,
                    "beginnerFriendlyScore": 75,
                    "__typename": "Stock"
                },
                {
                    "id": "stock_5",
                    "symbol": "AMZN",
                    "companyName": "Amazon.com Inc.",
                    "sector": "Consumer Discretionary",
                    "marketCap": 1500000000000,
                    "peRatio": 35.8,
                    "dividendYield": 0.0,
                    "beginnerFriendlyScore": 80,
                    "__typename": "Stock"
                },
                {
                    "id": "stock_6",
                    "symbol": "META",
                    "companyName": "Meta Platforms Inc.",
                    "sector": "Technology",
                    "marketCap": 900000000000,
                    "peRatio": 18.5,
                    "dividendYield": 0.0,
                    "beginnerFriendlyScore": 78,
                    "__typename": "Stock"
                },
                {
                    "id": "stock_7",
                    "symbol": "NVDA",
                    "companyName": "NVIDIA Corporation",
                    "sector": "Technology",
                    "marketCap": 1200000000000,
                    "peRatio": 55.2,
                    "dividendYield": 0.1,
                    "beginnerFriendlyScore": 72,
                    "__typename": "Stock"
                },
                {
                    "id": "stock_8",
                    "symbol": "NFLX",
                    "companyName": "Netflix Inc.",
                    "sector": "Communication Services",
                    "marketCap": 200000000000,
                    "peRatio": 42.1,
                    "dividendYield": 0.0,
                    "beginnerFriendlyScore": 70,
                    "__typename": "Stock"
                },
                {
                    "id": "stock_9",
                    "symbol": "JPM",
                    "companyName": "JPMorgan Chase & Co.",
                    "sector": "Financial Services",
                    "marketCap": 450000000000,
                    "peRatio": 12.8,
                    "dividendYield": 2.8,
                    "beginnerFriendlyScore": 90,
                    "__typename": "Stock"
                },
                {
                    "id": "stock_10",
                    "symbol": "JNJ",
                    "companyName": "Johnson & Johnson",
                    "sector": "Healthcare",
                    "marketCap": 420000000000,
                    "peRatio": 15.2,
                    "dividendYield": 2.9,
                    "beginnerFriendlyScore": 92,
                    "__typename": "Stock"
                }
            ]
            return {"data": response_data}

        # Check for quotes query
        if "quotes" in query:
            print("🎯 DETECTED quotes query!")
            symbols = variables.get("symbols", ["AAPL", "MSFT", "GOOGL", "TSLA"])
            quotes = []
            
            for symbol in symbols:
                try:
                    # Get real quote data from FinnHub
                    quote_url = f"https://finnhub.io/api/v1/quote?symbol={symbol}&token={FINNHUB_KEY}"
                    quote_response = requests.get(quote_url, timeout=10)
                    
                    if quote_response.status_code == 200:
                        quote_data = quote_response.json()
                        last_price = quote_data.get('c', 0)  # current price
                        change_pct = quote_data.get('dp', 0)  # change percent
                        
                        quotes.append({
                            "symbol": symbol,
                            "last": last_price,
                            "changePct": change_pct,
                            "__typename": "Quote"
                        })
                        
                        print(f"✅ Got real quote for {symbol}: ${last_price} ({change_pct:.1f}%)")
                        
                    else:
                        print(f"❌ Failed to get quote for {symbol}: {quote_response.status_code}")
                        # Fallback to mock data
                        quotes.append({
                            "symbol": symbol,
                            "last": round(random.uniform(50, 500), 2),
                            "changePct": round(random.uniform(-5, 5), 2),
                            "__typename": "Quote"
                        })
                        
                except Exception as e:
                    print(f"❌ Error getting quote for {symbol}: {e}")
                    # Fallback to mock data
                    quotes.append({
                        "symbol": symbol,
                        "last": round(random.uniform(50, 500), 2),
                        "changePct": round(random.uniform(-5, 5), 2),
                        "__typename": "Quote"
                    })
            
            response_data["quotes"] = quotes
            return {"data": response_data}

        # Check for stockDiscussions query
        if "stockDiscussions" in query:
            print("🎯 DETECTED stockDiscussions query!")
            response_data["stockDiscussions"] = [
                {
                    "id": "discussion_1",
                    "title": "Apple's Q4 Earnings Discussion",
                    "content": "What are your thoughts on Apple's latest earnings report? The iPhone sales numbers were impressive, but I'm concerned about the China market impact.",
                    "createdAt": "2024-01-15T10:30:00Z",
                    "score": 67,
                    "commentCount": 23,
                    "user": {
                        "id": "user_456",
                        "name": "TechAnalyst",
                        "email": "analyst@example.com",
                        "__typename": "User"
                    },
                    "stock": {
                        "symbol": "AAPL",
                        "companyName": "Apple Inc.",
                        "__typename": "Stock"
                    },
                    "comments": [
                        {
                            "id": "comment_1",
                            "content": "The services revenue growth is the real story here. Hardware is becoming less important.",
                            "createdAt": "2024-01-15T11:00:00Z",
                            "user": {
                                "name": "Investor123",
                                "__typename": "User"
                            },
                            "__typename": "Comment"
                        },
                        {
                            "id": "comment_2",
                            "content": "China concerns are valid, but Apple's diversification is helping.",
                            "createdAt": "2024-01-15T11:15:00Z",
                            "user": {
                                "name": "MarketWatcher",
                                "__typename": "User"
                            },
                            "__typename": "Comment"
                        },
                        {
                            "id": "comment_3",
                            "content": "The iPhone 15 Pro sales were stronger than expected. Premium segment is holding up well.",
                            "createdAt": "2024-01-15T11:30:00Z",
                            "user": {
                                "name": "TechEnthusiast",
                                "__typename": "User"
                            },
                            "__typename": "Comment"
                        }
                    ],
                    "__typename": "StockDiscussion"
                },
                {
                    "id": "discussion_2",
                    "title": "Microsoft's AI Strategy Deep Dive",
                    "content": "Microsoft's AI investments are finally paying off. Azure growth is accelerating and the integration with OpenAI is creating new opportunities. What's your take on the long-term impact?",
                    "createdAt": "2024-01-14T14:20:00Z",
                    "score": 89,
                    "commentCount": 31,
                    "user": {
                        "id": "user_789",
                        "name": "AIExpert",
                        "email": "ai@example.com",
                        "__typename": "User"
                    },
                    "stock": {
                        "symbol": "MSFT",
                        "companyName": "Microsoft Corporation",
                        "__typename": "Stock"
                    },
                    "comments": [
                        {
                            "id": "comment_4",
                            "content": "The Azure growth is phenomenal! Cloud computing is the future.",
                            "createdAt": "2024-01-14T15:00:00Z",
                            "user": {
                                "name": "CloudGuru",
                                "__typename": "User"
                            },
                            "__typename": "Comment"
                        },
                        {
                            "id": "comment_5",
                            "content": "OpenAI partnership is a game changer. Microsoft is positioning itself perfectly for the AI era.",
                            "createdAt": "2024-01-14T15:30:00Z",
                            "user": {
                                "name": "FutureTech",
                                "__typename": "User"
                            },
                            "__typename": "Comment"
                        }
                    ],
                    "__typename": "StockDiscussion"
                },
                {
                    "id": "discussion_3",
                    "title": "Tesla's Production and Delivery Numbers",
                    "content": "Tesla delivered record numbers this quarter. The Model Y continues to be a bestseller, and the Cybertruck production is finally ramping up. How do you see the EV market evolving?",
                    "createdAt": "2024-01-13T09:45:00Z",
                    "score": 124,
                    "commentCount": 45,
                    "user": {
                        "id": "user_101",
                        "name": "EVEnthusiast",
                        "email": "ev@example.com",
                        "__typename": "User"
                    },
                    "stock": {
                        "symbol": "TSLA",
                        "companyName": "Tesla Inc.",
                        "__typename": "Stock"
                    },
                    "comments": [
                        {
                            "id": "comment_6",
                            "content": "Cybertruck production is finally happening! This could be a major catalyst.",
                            "createdAt": "2024-01-13T10:30:00Z",
                            "user": {
                                "name": "FutureMobility",
                                "__typename": "User"
                            },
                            "__typename": "Comment"
                        },
                        {
                            "id": "comment_7",
                            "content": "The Model Y demand is incredible worldwide. Tesla's manufacturing efficiency is unmatched.",
                            "createdAt": "2024-01-13T11:00:00Z",
                            "user": {
                                "name": "GlobalInvestor",
                                "__typename": "User"
                            },
                            "__typename": "Comment"
                        },
                        {
                            "id": "comment_8",
                            "content": "Competition is heating up though. BYD and other Chinese manufacturers are gaining ground.",
                            "createdAt": "2024-01-13T11:45:00Z",
                            "user": {
                                "name": "MarketRealist",
                                "__typename": "User"
                            },
                            "__typename": "Comment"
                        }
                    ],
                    "__typename": "StockDiscussion"
                },
                {
                    "id": "discussion_4",
                    "title": "Google's Search Dominance and AI Integration",
                    "content": "Google's search business remains strong, but the AI integration is what's exciting. How do you think Bard and other AI products will impact the company's revenue?",
                    "createdAt": "2024-01-12T16:20:00Z",
                    "score": 56,
                    "commentCount": 18,
                    "user": {
                        "id": "user_202",
                        "name": "SearchExpert",
                        "email": "search@example.com",
                        "__typename": "User"
                    },
                    "stock": {
                        "symbol": "GOOGL",
                        "companyName": "Alphabet Inc.",
                        "__typename": "Stock"
                    },
                    "comments": [
                        {
                            "id": "comment_9",
                            "content": "Search advertising is still the cash cow, but AI could open new revenue streams.",
                            "createdAt": "2024-01-12T17:00:00Z",
                            "user": {
                                "name": "AdTechGuru",
                                "__typename": "User"
                            },
                            "__typename": "Comment"
                        }
                    ],
                    "__typename": "StockDiscussion"
                }
            ]
            return {"data": response_data}

        # Check for socialFeed query
        if "socialFeed" in query:
            print("🎯 DETECTED socialFeed query!")
            response_data["socialFeed"] = [
                {
                    "id": "post_1",
                    "title": "Apple's Q4 Earnings Analysis",
                    "content": "Apple reported strong Q4 earnings with iPhone sales exceeding expectations. The company's services revenue continues to grow, showing diversification beyond hardware.",
                    "createdAt": "2024-01-15T10:30:00Z",
                    "score": 45,
                    "commentCount": 12,
                    "user": {
                        "id": "user_456",
                        "name": "TechAnalyst",
                        "email": "analyst@example.com",
                        "__typename": "User"
                    },
                    "stock": {
                        "symbol": "AAPL",
                        "companyName": "Apple Inc.",
                        "__typename": "Stock"
                    },
                    "comments": [
                        {
                            "id": "comment_1",
                            "content": "Great analysis! The services growth is particularly impressive.",
                            "createdAt": "2024-01-15T11:00:00Z",
                            "user": {
                                "name": "Investor123",
                                "__typename": "User"
                            },
                            "__typename": "Comment"
                        },
                        {
                            "id": "comment_2",
                            "content": "What about the China market impact?",
                            "createdAt": "2024-01-15T11:15:00Z",
                            "user": {
                                "name": "MarketWatcher",
                                "__typename": "User"
                            },
                            "__typename": "Comment"
                        }
                    ],
                    "__typename": "SocialPost"
                },
                {
                    "id": "post_2",
                    "title": "Microsoft's AI Strategy Update",
                    "content": "Microsoft's latest AI investments are paying off. Azure growth is accelerating and the integration with OpenAI is creating new opportunities.",
                    "createdAt": "2024-01-14T14:20:00Z",
                    "score": 38,
                    "commentCount": 8,
                    "user": {
                        "id": "user_789",
                        "name": "AIExpert",
                        "email": "ai@example.com",
                        "__typename": "User"
                    },
                    "stock": {
                        "symbol": "MSFT",
                        "companyName": "Microsoft Corporation",
                        "__typename": "Stock"
                    },
                    "comments": [
                        {
                            "id": "comment_3",
                            "content": "The Azure growth is phenomenal!",
                            "createdAt": "2024-01-14T15:00:00Z",
                            "user": {
                                "name": "CloudGuru",
                                "__typename": "User"
                            },
                            "__typename": "Comment"
                        }
                    ],
                    "__typename": "SocialPost"
                },
                {
                    "id": "post_3",
                    "title": "Tesla's Production Numbers",
                    "content": "Tesla delivered record numbers this quarter. The Model Y continues to be a bestseller, and the Cybertruck production is ramping up.",
                    "createdAt": "2024-01-13T09:45:00Z",
                    "score": 52,
                    "commentCount": 15,
                    "user": {
                        "id": "user_101",
                        "name": "EVEnthusiast",
                        "email": "ev@example.com",
                        "__typename": "User"
                    },
                    "stock": {
                        "symbol": "TSLA",
                        "companyName": "Tesla Inc.",
                        "__typename": "Stock"
                    },
                    "comments": [
                        {
                            "id": "comment_4",
                            "content": "Cybertruck production is finally happening!",
                            "createdAt": "2024-01-13T10:30:00Z",
                            "user": {
                                "name": "FutureMobility",
                                "__typename": "User"
                            },
                            "__typename": "Comment"
                        },
                        {
                            "id": "comment_5",
                            "content": "The Model Y demand is incredible worldwide.",
                            "createdAt": "2024-01-13T11:00:00Z",
                            "user": {
                                "name": "GlobalInvestor",
                                "__typename": "User"
                            },
                            "__typename": "Comment"
                        }
                    ],
                    "__typename": "SocialPost"
                }
            ]
            return {"data": response_data}

        # Check for feedByTickers query
        if "feedByTickers" in query:
            print("🎯 DETECTED feedByTickers query!")
            symbols = variables.get("symbols", ["AAPL", "MSFT", "GOOGL", "TSLA"])
            limit = variables.get("limit", 50)
            
            # Generate feed posts based on the requested symbols
            feed_posts = []
            for i, symbol in enumerate(symbols[:5]):  # Limit to 5 symbols for demo
                feed_posts.append({
                    "id": f"feed_post_{i+1}",
                    "kind": "discussion",
                    "title": f"Real-time Discussion: {symbol} Market Analysis",
                    "content": f"Live discussion about {symbol} performance and market trends. Join the conversation and share your insights!",
                    "tickers": [symbol],
                    "score": random.randint(15, 85),
                    "commentCount": random.randint(3, 25),
                    "user": {
                        "id": f"user_{i+1}",
                        "name": f"Trader{i+1}",
                        "profilePic": f"https://via.placeholder.com/40?text={symbol[0]}",
                        "__typename": "User"
                    },
                    "createdAt": (datetime.now() - timedelta(hours=random.randint(1, 24))).isoformat() + "Z",
                    "__typename": "FeedPost"
                })
            
            # Add some multi-ticker posts
            if len(symbols) >= 2:
                feed_posts.append({
                    "id": "feed_post_multi",
                    "kind": "analysis",
                    "title": f"Tech Sector Analysis: {', '.join(symbols[:3])}",
                    "content": f"Comprehensive analysis of the technology sector focusing on {', '.join(symbols[:3])}. Market trends, earnings outlook, and investment strategies.",
                    "tickers": symbols[:3],
                    "score": 78,
                    "commentCount": 12,
                    "user": {
                        "id": "user_analyst",
                        "name": "TechAnalyst",
                        "profilePic": "https://via.placeholder.com/40?text=TA",
                        "__typename": "User"
                    },
                    "createdAt": (datetime.now() - timedelta(hours=2)).isoformat() + "Z",
                    "__typename": "FeedPost"
                })
            
            response_data["feedByTickers"] = feed_posts[:limit]
            return {"data": response_data}

        # Check for me query specifically (must be exact match, not substring)
        if query.strip().startswith("query") and "me" in query and not "feedByTickers" in query and not "tickerPostCreated" in query and not "myPortfolios" in query and not "myWatchlist" in query:
            print("🎯 DETECTED me query!")
            user = users_db["test@example.com"]
            response_data["me"] = {
                "id": user["id"],
                "name": user["name"],
                "email": user["email"],
                "profilePic": user.get("profilePic", "https://via.placeholder.com/150"),
                "followersCount": user.get("followersCount", 1250),
                "followingCount": user.get("followingCount", 89),
                "isFollowingUser": user.get("isFollowingUser", False),
                "isFollowedByUser": user.get("isFollowedByUser", False),
                "hasPremiumAccess": user["hasPremiumAccess"],
                "subscriptionTier": user["subscriptionTier"],
                "followedTickers": user.get("followedTickers", [
                    {"symbol": "AAPL", "__typename": "FollowedTicker"},
                    {"symbol": "MSFT", "__typename": "FollowedTicker"},
                    {"symbol": "GOOGL", "__typename": "FollowedTicker"},
                    {"symbol": "TSLA", "__typename": "FollowedTicker"}
                ]),
                "incomeProfile": user.get("incomeProfile", {
                    "id": "profile_1",
                    "incomeBracket": "$50,000 - $75,000",
                    "age": 30,
                    "investmentGoals": ["Retirement", "Home Purchase"],
                    "riskTolerance": "Moderate",
                    "investmentHorizon": "10-15 years",
                    "__typename": "IncomeProfile"
                }),
                "__typename": "User"
            }
            return {"data": response_data}

        # Check for tickerPostCreated subscription
        if "tickerPostCreated" in query:
            print("🎯 DETECTED tickerPostCreated subscription!")
            symbols = variables.get("symbols", [])
            response_data["tickerPostCreated"] = {
                "id": "post_1",
                "kind": "discussion",
                "title": "Real-time Market Discussion",
                "tickers": symbols[:3] if symbols else ["AAPL", "MSFT", "GOOGL"],
                "user": {
                    "id": "user_123",
                    "name": "MarketBot",
                    "__typename": "User"
                },
                "createdAt": datetime.now().isoformat() + "Z",
                "__typename": "TickerPost"
            }
            return {"data": response_data}

        # Default comprehensive response for all other queries
        print("📝 Using default comprehensive response")
        user = users_db["test@example.com"]

        if "stocks" in query:
            response_data["stocks"] = [
                {
                    "id": "1",
                    "symbol": "AAPL",
                    "companyName": "Apple Inc.",
                    "sector": "Technology",
                    "marketCap": 3000000000000,
                    "peRatio": 25.5,
                    "dividendYield": 0.5,
                    "beginnerFriendlyScore": 85,
                    "__typename": "Stock"
                },
                {
                    "id": "2",
                    "symbol": "MSFT",
                    "companyName": "Microsoft Corporation",
                    "sector": "Technology",
                    "marketCap": 2800000000000,
                    "peRatio": 28.0,
                    "dividendYield": 0.7,
                    "beginnerFriendlyScore": 88,
                    "__typename": "Stock"
                },
                {
                    "id": "3",
                    "symbol": "GOOGL",
                    "companyName": "Alphabet Inc.",
                    "sector": "Technology",
                    "marketCap": 1800000000000,
                    "peRatio": 22.5,
                    "dividendYield": 0.0,
                    "beginnerFriendlyScore": 75,
                    "__typename": "Stock"
                }
            ]

        if "quotes" in query:
            symbols = variables.get("symbols", ["AAPL"])
            response_data["quotes"] = [
                {
                    "symbol": symbol,
                    "last": round(random.uniform(100, 500), 2),
                    "changePct": round(random.uniform(-5, 5), 2),
                    "__typename": "Quote"
                }
                for symbol in symbols
            ]

        return {"data": response_data}

    except Exception as e:
        logger.error(f"GraphQL error: {e}")
        return {"errors": [{"message": str(e)}]}

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
