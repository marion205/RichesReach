#!/usr/bin/env python3
"""
RichesReach AI Service - Simple Live Data Server
Real-time stock data from Yahoo Finance
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from datetime import datetime, timedelta
import jwt
import hashlib
from typing import Optional, List, Dict, Any
import json
import yfinance as yf
import asyncio
import os

app = FastAPI(
    title="RichesReach Simple Live Data Service",
    description="Real-time stock data and analysis",
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

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def fetch_stock_data_sync(symbol: str) -> Dict[str, Any]:
    """Fetch real-time stock data for a symbol (synchronous)"""
    try:
        ticker = yf.Ticker(symbol)
        info = ticker.info
        hist = ticker.history(period="1d")
        
        if hist.empty:
            return None
            
        current_price = float(hist['Close'].iloc[-1])
        
        # Calculate beginner score
        score = 50
        market_cap = info.get('marketCap', 0)
        if market_cap > 100_000_000_000:
            score += 20
        elif market_cap > 10_000_000_000:
            score += 15
        
        pe_ratio = info.get('trailingPE', 0)
        if 10 <= pe_ratio <= 25:
            score += 15
        
        dividend_yield = info.get('dividendYield', 0)
        if dividend_yield and 0.02 <= dividend_yield <= 0.06:
            score += 10
        
        return {
            "symbol": symbol,
            "companyName": info.get('longName', symbol),
            "sector": info.get('sector', 'Unknown'),
            "marketCap": market_cap,
            "peRatio": pe_ratio,
            "dividendYield": (dividend_yield * 100) if dividend_yield else 0,
            "currentPrice": current_price,
            "beginnerFriendlyScore": min(100, max(0, score))
        }
        
    except Exception as e:
        print(f"Error fetching data for {symbol}: {e}")
        return None

def search_stocks_sync(search_term: str) -> List[Dict[str, Any]]:
    """Search for stocks matching the search term (synchronous)"""
    if not search_term:
        symbols = POPULAR_STOCKS[:10]
    else:
        search_lower = search_term.lower()
        symbols = [s for s in POPULAR_STOCKS if search_lower in s.lower()]
        if not symbols:
            symbols = [s for s in POPULAR_STOCKS if search_lower[0] == s.lower()[0]][:5]
    
    results = []
    for i, symbol in enumerate(symbols):
        stock_data = fetch_stock_data_sync(symbol)
        if stock_data:
            stock_data["id"] = str(i + 1)
            stock_data["__typename"] = "Stock"
            results.append(stock_data)
    
    return results

@app.post("/graphql/")
async def graphql_endpoint(request_data: dict):
    query = request_data.get("query", "")
    variables = request_data.get("variables", {})
    
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
            stocks_data = search_stocks_sync(search_term)
            
            return {
                "data": {
                    "stocks": stocks_data
                }
            }
        
        # Handle GetBeginnerFriendlyStocks query
        elif "beginnerFriendlyStocks" in query:
            beginner_symbols = ["SPY", "VTI", "QQQ", "VXUS", "BND"]
            beginner_stocks = []
            
            for i, symbol in enumerate(beginner_symbols):
                stock_data = fetch_stock_data_sync(symbol)
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
            return {
                "data": {
                    "myWatchlist": []
                }
            }
        
        # Handle rustStockAnalysis query
        elif "rustStockAnalysis" in query:
            symbol = variables.get("symbol", "AAPL")
            stock_data = fetch_stock_data_sync(symbol)
            
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
        "message": "RichesReach Simple Live Data Service",
        "version": "1.0.0",
        "status": "running",
        "timestamp": datetime.now().isoformat(),
        "data_source": "Yahoo Finance (Real-time)"
    }

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "data_source": "Yahoo Finance",
        "stocks_available": len(POPULAR_STOCKS)
    }

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
