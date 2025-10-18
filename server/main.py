# main.py
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from starlette_graphene3 import GraphQLApp, make_graphiql_handler
from settings import settings
from schema import schema
from observability import observe
from prometheus_client import make_asgi_app
from pydantic import BaseModel
from typing import Optional, List
import time
from clients.market import market

app = FastAPI(title="RichesReach", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], allow_methods=["*"], allow_headers=["*"], allow_credentials=True
)

# Pydantic models for API requests/responses
class LoginRequest(BaseModel):
    email: Optional[str] = None
    username: Optional[str] = None
    password: str

class LoginResponse(BaseModel):
    success: bool
    token: str
    user: dict
    message: str

class QuoteResponse(BaseModel):
    symbol: str
    price: float
    change: float
    changePercent: float

# Attach user to context (mock); replace with real auth
@app.middleware("http")
async def attach_user(request: Request, call_next):
    request.state.user = {
        "email": "test@example.com",
        "incomeProfile": {
            "incomeBracket": "Under $30,000",
            "age": 28,
            "investmentGoals": ["Emergency Fund","Wealth Building"],
            "riskTolerance": "Moderate",
            "investmentHorizon": "5-10 years",
        },
        "liquidCashUSD": 1800,   # drives suitability
        "monthlyContributionUSD": 150
    }
    with observe(route=request.url.path):
        response = await call_next(request)
        return response

@app.get("/health")
async def health():
    return {"status":"ok","schemaVersion": settings.SCHEMA_VERSION}

# Authentication endpoint
@app.post("/api/auth/login/", response_model=LoginResponse)
async def login(request: LoginRequest):
    """Handle user login with email or username"""
    try:
        # For demo purposes, accept any email/username with password "password"
        # In production, this would validate against a real database
        if request.password == "password":
            # Create a simple token (not JWT for now)
            email = request.email or request.username or "test@example.com"
            username = request.username or request.email or "testuser"
            token = f"demo_token_{int(time.time())}_{email.replace('@', '_at_')}"
            
            user_data = {
                "id": "1",
                "email": email,
                "username": username,
                "incomeProfile": {
                    "incomeBracket": "Under $30,000",
                    "age": 28,
                    "investmentGoals": ["Emergency Fund", "Wealth Building"],
                    "riskTolerance": "Moderate",
                    "investmentHorizon": "5-10 years",
                },
                "liquidCashUSD": 1800,
                "monthlyContributionUSD": 150
            }
            
            return LoginResponse(
                success=True,
                token=token,
                user=user_data,
                message="Login successful"
            )
        else:
            raise HTTPException(status_code=401, detail="Invalid credentials")
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Market quotes endpoint
@app.get("/api/market/quotes")
async def get_market_quotes(symbols: str):
    """Get market quotes for given symbols"""
    try:
        symbol_list = [s.strip().upper() for s in symbols.split(',')]
        quotes = []
        
        # For demo purposes, return mock data since the market API is failing
        mock_prices = {
            "AAPL": 175.50, "MSFT": 380.25, "GOOGL": 142.80, "AMZN": 155.30,
            "META": 485.20, "NVDA": 875.40, "TSLA": 245.60, "NFLX": 485.20,
            "ADBE": 580.30, "AMD": 125.40, "CRM": 220.80, "INTC": 45.20,
            "LYFT": 12.50, "PYPL": 65.40, "UBER": 45.80
        }
        
        for symbol in symbol_list:
            try:
                # Try to get real data first
                quote_data = await market.finnhub_quote(symbol)
                if quote_data and "value" in quote_data:
                    value = quote_data["value"]
                    current_price = value.get("c", 0)
                    previous_close = value.get("pc", current_price)
                    change = current_price - previous_close
                    change_percent = (change / previous_close * 100) if previous_close != 0 else 0
                    
                    quotes.append({
                        "symbol": symbol,
                        "price": current_price,
                        "change": change,
                        "changePercent": change_percent
                    })
                else:
                    # Use mock data as fallback
                    base_price = mock_prices.get(symbol, 100.0)
                    change = base_price * 0.02  # 2% change
                    quotes.append({
                        "symbol": symbol,
                        "price": base_price,
                        "change": change,
                        "changePercent": 2.0
                    })
            except Exception as e:
                print(f"Error fetching quote for {symbol}: {e}")
                # Use mock data as fallback
                base_price = mock_prices.get(symbol, 100.0)
                change = base_price * 0.01  # 1% change
                quotes.append({
                    "symbol": symbol,
                    "price": base_price,
                    "change": change,
                    "changePercent": 1.0
                })
        
        return {"quotes": quotes}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

app.mount("/metrics", make_asgi_app())

app.add_route(
    "/graphql", GraphQLApp(schema=schema, on_get=make_graphiql_handler())
)
