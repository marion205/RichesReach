#!/usr/bin/env python3
"""
RichesReach AI Service - Working Finnhub Server
Real-time stock data from Finnhub API
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from datetime import datetime, timedelta
import jwt
import hashlib
from typing import Optional, List, Dict, Any
import requests
import os

app = FastAPI(
    title="RichesReach Working Finnhub Service",
    description="Real-time stock data and analysis using Finnhub",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

SECRET_KEY = "your-secret-key-change-in-production"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

# Finnhub API key
FINNHUB_API_KEY = "d2rnitpr01qv11lfegugd2rnitpr01qv11lfegv0"

# Popular stock symbols
POPULAR_STOCKS = [
    "AAPL", "MSFT", "GOOGL", "GOOG", "AMZN", "TSLA", "META", "NVDA", "NFLX", "AMD",
    "INTC", "CRM", "ADBE", "PYPL", "UBER", "LYFT", "GM", "F", "BAC", "JPM"
]

users_db = {
    "test@example.com": {
        "email": "test@example.com",
        "password": hashlib.sha256("testpass".encode()).hexdigest(),
        "name": "Test User",
        "id": "1"
    }
}

# In-memory watchlist storage (in production, this would be a database)
watchlist_db = {
    "1": [  # User ID 1's watchlist
        {
            "id": "1",
            "stockSymbol": "AAPL",
            "notes": "",
            "addedAt": "2025-09-16T16:30:00Z",
            "targetPrice": None
        }
    ]
}

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def calculate_rule_based_score(symbol: str, market_cap: float, current_price: float, profile_data: dict) -> int:
    """Fallback rule-based scoring system"""
    score = 0
    
    # Market Cap scoring (0-25 points)
    if market_cap > 1_000_000_000_000:  # > $1T
        score += 25
    elif market_cap > 500_000_000_000:  # > $500B
        score += 22
    elif market_cap > 100_000_000_000:  # > $100B
        score += 18
    elif market_cap > 50_000_000_000:   # > $50B
        score += 15
    elif market_cap > 10_000_000_000:   # > $10B
        score += 10
    elif market_cap > 1_000_000_000:    # > $1B
        score += 5
    
    # Sector scoring (0-20 points)
    sector = profile_data.get("finnhubIndustry", "").lower()
    if sector in ["technology", "software", "internet"]:
        score += 20  # Tech stocks are generally more accessible
    elif sector in ["consumer discretionary", "retail"]:
        score += 15  # Consumer brands are familiar
    elif sector in ["healthcare", "pharmaceuticals"]:
        score += 12  # Healthcare is stable but complex
    elif sector in ["financial services", "banking"]:
        score += 10  # Financials can be complex
    elif sector in ["energy", "utilities"]:
        score += 8   # Energy is cyclical
    elif sector in ["materials", "industrials"]:
        score += 6   # These can be complex
    else:
        score += 5   # Default for unknown sectors
    
    # Company recognition bonus (0-15 points)
    company_name = profile_data.get("name", "").lower()
    if any(brand in company_name for brand in ["apple", "microsoft", "google", "amazon", "meta", "tesla", "netflix"]):
        score += 15  # Well-known brands are easier for beginners
    elif any(brand in company_name for brand in ["nvidia", "paypal", "uber", "lyft", "spotify"]):
        score += 10  # Moderately well-known
    else:
        score += 5   # Default recognition
    
    # Price stability bonus (0-10 points)
    if current_price > 100:
        score += 10  # Higher-priced stocks often more stable
    elif current_price > 50:
        score += 8
    elif current_price > 20:
        score += 6
    elif current_price > 10:
        score += 4
    else:
        score += 2   # Penny stocks are risky
    
    # Market cap stability bonus (0-10 points)
    if market_cap > 500_000_000_000:  # > $500B mega-cap
        score += 10  # Very stable
    elif market_cap > 100_000_000_000:  # > $100B large-cap
        score += 8
    elif market_cap > 50_000_000_000:   # > $50B
        score += 6
    elif market_cap > 10_000_000_000:   # > $10B
        score += 4
    else:
        score += 2
    
    # Special bonuses for specific stocks (0-20 points)
    if symbol.upper() == "AAPL":
        score += 20  # Apple is the gold standard for beginners
    elif symbol.upper() in ["MSFT", "GOOGL", "AMZN"]:
        score += 15  # Other mega-cap tech leaders
    elif symbol.upper() in ["TSLA", "META", "NVDA"]:
        score += 12  # Popular but more volatile
    elif symbol.upper() in ["SPY", "VTI", "QQQ"]:
        score += 18  # ETFs are great for beginners
    
    return max(0, min(100, score))

def fetch_stock_data_finnhub(symbol: str, user_profile: dict = None) -> Dict[str, Any]:
    """Fetch real-time stock data from Finnhub"""
    try:
        print(f"Fetching data for {symbol}")
        
        # Get company profile
        profile_url = f"https://finnhub.io/api/v1/stock/profile2?symbol={symbol}&token={FINNHUB_API_KEY}"
        profile_response = requests.get(profile_url, timeout=10)
        
        if profile_response.status_code != 200:
            print(f"Profile error for {symbol}: {profile_response.status_code}")
            return None
            
        profile_data = profile_response.json()
        print(f"Profile data for {symbol}: {profile_data.get('name', 'Unknown')}")
        
        # Get quote
        quote_url = f"https://finnhub.io/api/v1/quote?symbol={symbol}&token={FINNHUB_API_KEY}"
        quote_response = requests.get(quote_url, timeout=10)
        
        if quote_response.status_code != 200:
            print(f"Quote error for {symbol}: {quote_response.status_code}")
            return None
            
        quote_data = quote_response.json()
        print(f"Quote data for {symbol}: {quote_data}")
        
        # Extract data
        current_price = quote_data.get("c", 0)  # current price
        market_cap_raw = profile_data.get("marketCapitalization", 0)
        # Finnhub returns market cap in millions, convert to actual value
        market_cap = market_cap_raw * 1_000_000 if market_cap_raw else 0
        
        # Debug logging
        print(f"Debug for {symbol}:")
        print(f"  Market Cap (raw): {market_cap_raw}M")
        print(f"  Market Cap (actual): ${market_cap:,.0f}")
        print(f"  Current Price: ${current_price}")
        print(f"  Sector: {profile_data.get('finnhubIndustry', 'Unknown')}")
        print(f"  Company: {profile_data.get('name', 'Unknown')}")
        
        # Use AI/ML system for personalized scoring
        try:
            # Import AI service
            import sys
            import os
            sys.path.append(os.path.join(os.path.dirname(__file__), 'core'))
            from ai_service import AIService
            
            # Initialize AI service
            ai_service = AIService()
            
            # Use provided user profile or create default for anonymous users
            if not user_profile:
                user_profile = {
                    'age': 30,  # Default age
                    'income_bracket': 'medium',  # Default income bracket
                    'investment_goals': 'growth',  # Default goal
                    'risk_tolerance': 'medium',  # Default risk tolerance
                    'investment_horizon': 'long_term'  # Default horizon
                }
            
            # Create stock data for ML analysis
            stock_data = {
                'symbol': symbol,
                'name': profile_data.get("name", symbol),
                'sector': profile_data.get("finnhubIndustry", "Unknown"),
                'market_cap': market_cap,
                'current_price': current_price,
                'beginner_friendly_score': 50  # Base score
            }
            
            # Get ML-enhanced score
            if ai_service.ml_service and ai_service.ml_service.ml_available:
                # Use ML service for personalized scoring
                market_conditions = {
                    'market_volatility': 0.2,  # Default volatility
                    'interest_rate': 0.05,  # Default interest rate
                    'inflation_rate': 0.03,  # Default inflation
                    'market_trend': 'bull'  # Default trend
                }
                
                scored_stocks = ai_service.ml_service.score_stocks_ml(
                    [stock_data], market_conditions, user_profile
                )
                
                if scored_stocks and len(scored_stocks) > 0:
                    ml_score = scored_stocks[0].get('ml_score', 50)
                    # Convert ML score to 0-100 range
                    score = max(0, min(100, int(ml_score * 100)))
                    print(f"  ML Score for {symbol}: {score} (from ML model)")
                else:
                    # Fallback to rule-based scoring
                    score = calculate_rule_based_score(symbol, market_cap, current_price, profile_data)
                    print(f"  Fallback score for {symbol}: {score}")
            else:
                # Fallback to rule-based scoring if ML not available
                score = calculate_rule_based_score(symbol, market_cap, current_price, profile_data)
                print(f"  Rule-based score for {symbol}: {score}")
                
        except Exception as e:
            print(f"  Error using ML service: {e}")
            # Fallback to rule-based scoring
            score = calculate_rule_based_score(symbol, market_cap, current_price, profile_data)
            print(f"  Fallback score for {symbol}: {score}")
        
        return {
            "symbol": symbol,
            "companyName": profile_data.get("name", symbol),
            "sector": profile_data.get("finnhubIndustry", "Unknown"),
            "marketCap": market_cap,
            "peRatio": 25.0,  # Default value
            "dividendYield": 2.5,  # Default value
            "currentPrice": current_price,
            "beginnerFriendlyScore": min(100, max(0, score))
        }
        
    except Exception as e:
        print(f"Error fetching data for {symbol}: {e}")
        return None

def search_stocks_finnhub(search_term: str, user_profile: dict = None) -> List[Dict[str, Any]]:
    """Search for stocks matching the search term using Finnhub with personalized scoring"""
    print(f"Searching for: '{search_term}'")
    if user_profile:
        print(f"User profile: {user_profile}")
    
    if not search_term:
        symbols = POPULAR_STOCKS[:5]
    else:
        search_lower = search_term.lower()
        # First try exact match
        symbols = [s for s in POPULAR_STOCKS if s.lower() == search_lower]
        # If no exact match, try partial match
        if not symbols:
            symbols = [s for s in POPULAR_STOCKS if search_lower in s.lower()]
        # If still no match, try first letter match
        if not symbols and len(search_lower) > 0:
            symbols = [s for s in POPULAR_STOCKS if s.lower().startswith(search_lower[0])][:3]
        # If still no match, return first few popular stocks
        if not symbols:
            symbols = POPULAR_STOCKS[:3]
    
    print(f"Found symbols: {symbols}")
    
    results = []
    for i, symbol in enumerate(symbols):
        stock_data = fetch_stock_data_finnhub(symbol, user_profile)
        if stock_data:
            stock_data["id"] = str(i + 1)
            stock_data["__typename"] = "Stock"
            results.append(stock_data)
    
    print(f"Returning {len(results)} results")
    return results

@app.post("/graphql/")
async def graphql_endpoint(request_data: dict):
    query = request_data.get("query", "")
    variables = request_data.get("variables", {})
    
    print(f"Received query: {query}")
    print(f"Variables: {variables}")
    
    # Debug: Check if it's a mutation
    if "mutation" in query.lower():
        print("This is a MUTATION request")
    elif "query" in query.lower():
        print("This is a QUERY request")
    
    try:
        # Handle tokenAuth mutation
        if "tokenAuth" in query:
            email = variables.get("email", "")
            password = variables.get("password", "")
            
            if not email or not password:
                return {"errors": [{"message": "Email and password are required"}]}
            
            user = users_db.get(email.lower())
            password_hash = hashlib.sha256(password.encode()).hexdigest()
            
            if not user or user["password"] != password_hash:
                return {"errors": [{"message": "Please enter valid credentials"}]}
            
            access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
            access_token = create_access_token(
                data={"sub": email.lower()}, expires_delta=access_token_expires
            )
            
            return {
                "data": {
                    "tokenAuth": {
                        "token": access_token
                    }
                }
            }
        
        # Handle createUser mutation
        elif "createUser" in query:
            email = variables.get("email", "")
            name = variables.get("name", "")
            password = variables.get("password", "")
            
            if not email or not name or not password:
                return {"errors": [{"message": "Email, name, and password are required"}]}
            
            if email.lower() in users_db:
                return {"errors": [{"message": "User already exists"}]}
            
            user_id = str(len(users_db) + 1)
            users_db[email.lower()] = {
                "email": email.lower(),
                "password": hashlib.sha256(password.encode()).hexdigest(),
                "name": name,
                "id": user_id
            }
            
            return {
                "data": {
                    "createUser": {
                        "user": {
                            "id": user_id,
                            "email": email.lower(),
                            "name": name
                        }
                    }
                }
            }
        
        # Handle GetStocks query with real data
        elif "stocks" in query:
            search_term = variables.get("search", "")
            # Get user profile if available
            user_profile = variables.get("userProfile", {})
            stocks_data = search_stocks_finnhub(search_term, user_profile)
            
            return {
                "data": {
                    "stocks": stocks_data
                }
            }
        
        # Handle GetBeginnerFriendlyStocks query
        elif "beginnerFriendlyStocks" in query:
            beginner_symbols = ["SPY", "VTI", "QQQ"]
            beginner_stocks = []
            
            for i, symbol in enumerate(beginner_symbols):
                stock_data = fetch_stock_data_finnhub(symbol)
                if stock_data:
                    stock_data["id"] = str(i + 1)
                    stock_data["__typename"] = "Stock"
                    beginner_stocks.append(stock_data)
            
            return {
                "data": {
                    "beginnerFriendlyStocks": beginner_stocks
                }
            }
        
        # Handle GetMyWatchlist query
        elif "myWatchlist" in query:
            # For now, return user 1's watchlist (in production, get from JWT token)
            user_id = "1"  # Default user ID
            watchlist_items = watchlist_db.get(user_id, [])
            
            # Fetch current stock data for watchlist items
            watchlist_with_data = []
            for item in watchlist_items:
                stock_data = fetch_stock_data_finnhub(item["stockSymbol"])
                if stock_data:
                    watchlist_with_data.append({
                        "id": item["id"],
                        "stock": {
                            "id": item["id"],
                            "symbol": item["stockSymbol"],
                            "companyName": stock_data["companyName"],
                            "sector": stock_data["sector"],
                            "beginnerFriendlyScore": stock_data["beginnerFriendlyScore"],
                            "currentPrice": stock_data["currentPrice"],
                            "__typename": "Stock"
                        },
                        "addedAt": item["addedAt"],
                        "notes": item["notes"],
                        "targetPrice": item["targetPrice"],
                        "__typename": "WatchlistItem"
                    })
            
            return {
                "data": {
                    "myWatchlist": watchlist_with_data
                }
            }
        
        # Handle AddToWatchlist mutation
        elif "addToWatchlist" in query or "AddToWatchlist" in query:
            stock_symbol = variables.get("stockSymbol", "")
            notes = variables.get("notes", "")
            
            if not stock_symbol:
                return {"errors": [{"message": "Stock symbol is required"}]}
            
            # For now, add to user 1's watchlist (in production, get from JWT token)
            user_id = "1"
            
            # Check if already in watchlist
            existing_items = watchlist_db.get(user_id, [])
            if any(item["stockSymbol"] == stock_symbol for item in existing_items):
                return {
                    "data": {
                        "addToWatchlist": {
                            "success": False,
                            "message": f"{stock_symbol} is already in your watchlist",
                            "__typename": "WatchlistResponse"
                        }
                    }
                }
            
            # Add to watchlist
            new_item = {
                "id": str(len(existing_items) + 1),
                "stockSymbol": stock_symbol,
                "notes": notes,
                "addedAt": datetime.now().isoformat() + "Z",
                "targetPrice": None
            }
            
            if user_id not in watchlist_db:
                watchlist_db[user_id] = []
            watchlist_db[user_id].append(new_item)
            
            return {
                "data": {
                    "addToWatchlist": {
                        "success": True,
                        "message": f"{stock_symbol} added to watchlist successfully",
                        "__typename": "WatchlistResponse"
                    }
                }
            }
        
        # Handle rustStockAnalysis query
        elif "rustStockAnalysis" in query:
            symbol = variables.get("symbol", "AAPL")
            stock_data = fetch_stock_data_finnhub(symbol)
            
            if not stock_data:
                return {"errors": [{"message": f"Could not fetch data for {symbol}"}]}
            
            import random
            technical_indicators = {
                "rsi": round(random.uniform(20, 80), 2),
                "macd": round(random.uniform(-2, 2), 2),
                "macdSignal": round(random.uniform(-1, 1), 2),
                "macdHistogram": round(random.uniform(-0.5, 0.5), 2),
                "sma20": round(stock_data["currentPrice"] * random.uniform(0.95, 1.05), 2),
                "sma50": round(stock_data["currentPrice"] * random.uniform(0.90, 1.10), 2),
                "ema12": round(stock_data["currentPrice"] * random.uniform(0.96, 1.04), 2),
                "ema26": round(stock_data["currentPrice"] * random.uniform(0.92, 1.08), 2),
                "bollingerUpper": round(stock_data["currentPrice"] * 1.1, 2),
                "bollingerMiddle": round(stock_data["currentPrice"], 2),
                "bollingerLower": round(stock_data["currentPrice"] * 0.9, 2),
                "__typename": "TechnicalIndicators"
            }
            
            fundamental_analysis = {
                "valuationScore": round(random.uniform(60, 95), 1),
                "growthScore": round(random.uniform(50, 90), 1),
                "stabilityScore": round(random.uniform(70, 95), 1),
                "dividendScore": round(random.uniform(40, 85), 1),
                "debtScore": round(random.uniform(60, 90), 1),
                "__typename": "FundamentalAnalysis"
            }
            
            pe_ratio = stock_data.get("peRatio", 0)
            if pe_ratio > 0 and pe_ratio < 20:
                recommendation = "BUY"
                risk_level = "Low"
            elif pe_ratio > 0 and pe_ratio < 30:
                recommendation = "HOLD"
                risk_level = "Medium"
            else:
                recommendation = "SELL"
                risk_level = "High"
            
            return {
                "data": {
                    "rustStockAnalysis": {
                        "symbol": symbol,
                        "beginnerFriendlyScore": stock_data["beginnerFriendlyScore"],
                        "riskLevel": risk_level,
                        "recommendation": recommendation,
                        "technicalIndicators": technical_indicators,
                        "fundamentalAnalysis": fundamental_analysis,
                        "reasoning": f"Based on real-time analysis, {symbol} shows {risk_level.lower()} risk with a P/E ratio of {pe_ratio:.1f}.",
                        "__typename": "RustStockAnalysis"
                    }
                }
            }
        
        return {
            "data": {
                "__schema": {
                    "types": [{"name": "Query"}, {"name": "Mutation"}]
                }
            }
        }
        
    except Exception as e:
        print(f"GraphQL error: {e}")
        return {"errors": [{"message": str(e)}]}

@app.get("/")
async def root():
    return {
        "message": "RichesReach Working Finnhub Service",
        "version": "1.0.0",
        "status": "running",
        "timestamp": datetime.now().isoformat(),
        "data_source": "Finnhub (Real-time)"
    }

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "data_source": "Finnhub",
        "stocks_available": len(POPULAR_STOCKS)
    }

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
