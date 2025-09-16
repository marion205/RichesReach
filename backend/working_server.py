from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from datetime import datetime, timedelta
import jwt
import hashlib
from typing import Optional
import json

app = FastAPI()

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

@app.post("/graphql/")
async def graphql_endpoint(request_data: dict):
    query = request_data.get("query", "")
    variables = request_data.get("variables", {})
    
    print(f"Received query: {query}")
    print(f"Variables: {variables}")
    
    try:
        # Handle tokenAuth mutation
        if "tokenAuth" in query:
            email = variables.get("email", "")
            password = variables.get("password", "")
            
            print(f"Login attempt: email={email}, password={password}")
            
            if not email or not password:
                return {
                    "errors": [{"message": "Email and password are required"}]
                }
            
            user = users_db.get(email.lower())
            password_hash = hashlib.sha256(password.encode()).hexdigest()
            
            if not user or user["password"] != password_hash:
                return {
                    "errors": [{"message": "Please enter valid credentials"}]
                }
            
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
                return {
                    "errors": [{"message": "Email, name, and password are required"}]
                }
            
            if email.lower() in users_db:
                return {
                    "errors": [{"message": "User already exists"}]
                }
            
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
        
        # Handle GetStocks query
        elif "stocks" in query:
            search_term = variables.get("search", "").lower() if variables.get("search") else ""
            
            all_stocks = [
                {
                    "id": "1",
                    "symbol": "AAPL",
                    "companyName": "Apple Inc.",
                    "sector": "Technology",
                    "marketCap": 2800000000000,
                    "peRatio": 29.5,
                    "dividendYield": 0.5,
                    "beginnerFriendlyScore": 85,
                    "__typename": "Stock"
                },
                {
                    "id": "2",
                    "symbol": "MSFT",
                    "companyName": "Microsoft Corp.",
                    "sector": "Technology",
                    "marketCap": 2500000000000,
                    "peRatio": 32.1,
                    "dividendYield": 0.8,
                    "beginnerFriendlyScore": 88,
                    "__typename": "Stock"
                },
                {
                    "id": "3",
                    "symbol": "GOOGL",
                    "companyName": "Alphabet Inc.",
                    "sector": "Technology",
                    "marketCap": 1800000000000,
                    "peRatio": 25.2,
                    "dividendYield": 0.0,
                    "beginnerFriendlyScore": 82,
                    "__typename": "Stock"
                },
                {
                    "id": "4",
                    "symbol": "AMZN",
                    "companyName": "Amazon.com Inc.",
                    "sector": "Consumer Discretionary",
                    "marketCap": 1500000000000,
                    "peRatio": 45.8,
                    "dividendYield": 0.0,
                    "beginnerFriendlyScore": 75,
                    "__typename": "Stock"
                },
                {
                    "id": "5",
                    "symbol": "TSLA",
                    "companyName": "Tesla Inc.",
                    "sector": "Consumer Discretionary",
                    "marketCap": 800000000000,
                    "peRatio": 60.2,
                    "dividendYield": 0.0,
                    "beginnerFriendlyScore": 70,
                    "__typename": "Stock"
                },
                {
                    "id": "6",
                    "symbol": "GM",
                    "companyName": "General Motors Co.",
                    "sector": "Consumer Discretionary",
                    "marketCap": 50000000000,
                    "peRatio": 5.2,
                    "dividendYield": 1.2,
                    "beginnerFriendlyScore": 78,
                    "__typename": "Stock"
                },
                {
                    "id": "7",
                    "symbol": "GOOG",
                    "companyName": "Alphabet Inc. Class C",
                    "sector": "Technology",
                    "marketCap": 1800000000000,
                    "peRatio": 25.2,
                    "dividendYield": 0.0,
                    "beginnerFriendlyScore": 82,
                    "__typename": "Stock"
                }
            ]
            
            # Filter stocks based on search term
            if search_term:
                filtered_stocks = [
                    stock for stock in all_stocks 
                    if (search_term in stock["symbol"].lower() or 
                        search_term in stock["companyName"].lower())
                ]
            else:
                filtered_stocks = all_stocks
            
            return {
                "data": {
                    "stocks": filtered_stocks
                }
            }
        
        # Handle GetBeginnerFriendlyStocks query
        elif "beginnerFriendlyStocks" in query:
            return {
                "data": {
                    "beginnerFriendlyStocks": [
                        {
                            "id": "1",
                            "symbol": "SPY",
                            "companyName": "SPDR S&P 500 ETF Trust",
                            "sector": "Diversified",
                            "marketCap": 400000000000,
                            "peRatio": 22.0,
                            "dividendYield": 1.5,
                            "beginnerFriendlyScore": 92,
                            "__typename": "Stock"
                        },
                        {
                            "id": "2",
                            "symbol": "VTI",
                            "companyName": "Vanguard Total Stock Market ETF",
                            "sector": "Diversified",
                            "marketCap": 350000000000,
                            "peRatio": 21.0,
                            "dividendYield": 1.3,
                            "beginnerFriendlyScore": 90,
                            "__typename": "Stock"
                        },
                        {
                            "id": "3",
                            "symbol": "QQQ",
                            "companyName": "Invesco QQQ Trust",
                            "sector": "Technology",
                            "marketCap": 200000000000,
                            "peRatio": 24.5,
                            "dividendYield": 0.6,
                            "beginnerFriendlyScore": 88,
                            "__typename": "Stock"
                        },
                        {
                            "id": "4",
                            "symbol": "VXUS",
                            "companyName": "Vanguard Total Intl. Stock ETF",
                            "sector": "Diversified",
                            "marketCap": 180000000000,
                            "peRatio": 19.8,
                            "dividendYield": 2.1,
                            "beginnerFriendlyScore": 87,
                            "__typename": "Stock"
                        },
                        {
                            "id": "5",
                            "symbol": "BND",
                            "companyName": "Vanguard Total Bond Market ETF",
                            "sector": "Fixed Income",
                            "marketCap": 120000000000,
                            "peRatio": 15.2,
                            "dividendYield": 3.2,
                            "beginnerFriendlyScore": 95,
                            "__typename": "Stock"
                        }
                    ]
                }
            }
        
        # Handle GetMyWatchlist query
        elif "myWatchlist" in query:
            return {
                "data": {
                    "myWatchlist": [
                        {
                            "id": "1",
                            "stock": {
                                "id": "1",
                                "symbol": "GOOGL",
                                "companyName": "Alphabet Inc.",
                                "sector": "Technology",
                                "beginnerFriendlyScore": 80,
                                "currentPrice": 140.0,
                                "__typename": "Stock"
                            },
                            "addedAt": "2024-01-01T12:00:00Z",
                            "notes": "Long-term growth",
                            "targetPrice": 150.0,
                            "__typename": "WatchlistItem"
                        }
                    ]
                }
            }
        
        # Handle rustStockAnalysis query
        elif "rustStockAnalysis" in query:
            symbol = variables.get("symbol", "AAPL")
            import random
            
            # Generate technical indicators
            technical_indicators = {
                "rsi": round(random.uniform(20, 80), 2),
                "macd": round(random.uniform(-2, 2), 2),
                "macdSignal": round(random.uniform(-1, 1), 2),
                "macdHistogram": round(random.uniform(-0.5, 0.5), 2),
                "sma20": round(random.uniform(50, 200), 2),
                "sma50": round(random.uniform(45, 210), 2),
                "ema12": round(random.uniform(48, 205), 2),
                "ema26": round(random.uniform(47, 208), 2),
                "bollingerUpper": round(random.uniform(60, 250), 2),
                "bollingerMiddle": round(random.uniform(50, 200), 2),
                "bollingerLower": round(random.uniform(40, 150), 2),
                "__typename": "TechnicalIndicators"
            }
            
            # Generate fundamental analysis scores
            fundamental_analysis = {
                "valuationScore": round(random.uniform(60, 95), 1),
                "growthScore": round(random.uniform(50, 90), 1),
                "stabilityScore": round(random.uniform(70, 95), 1),
                "dividendScore": round(random.uniform(40, 85), 1),
                "debtScore": round(random.uniform(60, 90), 1),
                "__typename": "FundamentalAnalysis"
            }
            
            # Generate recommendation
            recommendation = random.choice(["STRONG BUY", "BUY", "HOLD", "SELL", "STRONG SELL"])
            risk_level = random.choice(["Low", "Medium", "High"])
            beginner_score = random.randint(70, 95)
            
            return {
                "data": {
                    "rustStockAnalysis": {
                        "symbol": symbol,
                        "beginnerFriendlyScore": beginner_score,
                        "riskLevel": risk_level,
                        "recommendation": recommendation,
                        "technicalIndicators": technical_indicators,
                        "fundamentalAnalysis": fundamental_analysis,
                        "reasoning": f"Based on technical analysis, {symbol} shows {risk_level.lower()} risk characteristics with strong fundamentals.",
                        "__typename": "RustStockAnalysis"
                    }
                }
            }
        
        # Handle other queries
        return {
            "data": {
                "__schema": {
                    "types": [{"name": "Query"}, {"name": "Mutation"}]
                }
            }
        }
        
    except Exception as e:
        print(f"Error: {e}")
        return {
            "errors": [{"message": str(e)}]
        }

@app.get("/")
async def root():
    return {"message": "RichesReach Working Server is running"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)