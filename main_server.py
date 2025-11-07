#!/usr/bin/env python3

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn
import os
import sys

# Setup Django at module load time (before request handlers)
_django_initialized = False
def _setup_django_once():
    global _django_initialized
    if _django_initialized:
        return
    
    try:
        import django
        if 'DJANGO_SETTINGS_MODULE' not in os.environ:
            # Try deployment_package/backend first (current structure)
            backend_path = os.path.join(os.path.dirname(__file__), 'deployment_package', 'backend')
            backend_path_abs = os.path.abspath(backend_path)
            
            # Fallback to backend/backend for compatibility
            if not os.path.exists(backend_path_abs):
                backend_path = os.path.join(os.path.dirname(__file__), 'backend', 'backend')
                backend_path_abs = os.path.abspath(backend_path)
            
            if os.path.exists(backend_path_abs):
                if backend_path_abs not in sys.path:
                    sys.path.insert(0, backend_path_abs)
                os.chdir(backend_path_abs)
                print(f"📊 Django backend path: {backend_path_abs}")
            
            # Use local PostgreSQL with production schema for demo
            # Priority: 1) Local settings with local DB, 2) Standard settings with local DB, 3) Production settings
            settings_module = os.getenv('DJANGO_SETTINGS_MODULE')
            if not settings_module:
                # Check for core app settings (since we're in deployment_package/backend/core)
                settings_local_path = os.path.join(backend_path_abs, 'richesreach', 'settings_local.py')
                settings_path = os.path.join(backend_path_abs, 'richesreach', 'settings.py')
                settings_prod_path = os.path.join(backend_path_abs, 'richesreach', 'settings_aws.py')
                core_settings_path = os.path.join(backend_path_abs, 'core', 'settings.py')
                
                # Try core settings first (new structure)
                if os.path.exists(core_settings_path):
                    settings_module = 'core.settings'
                    print(f"📊 Using core settings: {settings_module}")
                elif os.path.exists(settings_local_path):
                    settings_module = 'richesreach.settings_local'
                    print(f"📊 Using local settings with local PostgreSQL: {settings_module}")
                elif os.path.exists(settings_path):
                    settings_module = 'richesreach.settings'
                    print(f"📊 Using Django settings with local PostgreSQL: {settings_module}")
                elif os.path.exists(settings_prod_path):
                    settings_module = 'richesreach.settings_aws'
                    print(f"📊 Using production settings: {settings_module}")
                else:
                    # Fallback: try to find any settings file
                    import glob
                    settings_files = glob.glob(os.path.join(backend_path_abs, '**', 'settings*.py'), recursive=True)
                    if settings_files:
                        # Extract module path
                        rel_path = os.path.relpath(settings_files[0], backend_path_abs)
                        settings_module = rel_path.replace('/', '.').replace('.py', '')
                        print(f"📊 Using found settings: {settings_module}")
                    else:
                        # Use core as fallback
                        settings_module = 'core.settings'
                        print(f"📊 Using default core settings: {settings_module}")
            
            # Override database settings to use local PostgreSQL for demo
            os.environ.setdefault('DJANGO_SETTINGS_MODULE', settings_module)
            # Ensure local database is used
            if not os.getenv('DB_NAME'):
                os.environ.setdefault('DB_NAME', 'richesreach')
            if not os.getenv('DB_USER'):
                os.environ.setdefault('DB_USER', os.getenv('USER', 'postgres'))
            if not os.getenv('DB_HOST'):
                os.environ.setdefault('DB_HOST', 'localhost')
            if not os.getenv('DB_PORT'):
                os.environ.setdefault('DB_PORT', '5432')
            print(f"📊 Local PostgreSQL config: DB_NAME={os.getenv('DB_NAME')}, DB_HOST={os.getenv('DB_HOST')}")
        
        django.setup()
        _django_initialized = True
        
        # Verify database connection
        try:
            from django.db import connection
            connection.ensure_connection()
            db_info = connection.get_connection_params()
            db_name = db_info.get('database', 'unknown')
            db_host = db_info.get('host', 'unknown')
            print(f"✅ Django initialized with database: {db_name} on {db_host}")
        except Exception as db_error:
            print(f"⚠️ Database connection check failed: {db_error}")
            print("   GraphQL will use fallback handlers until database is connected")
        
        print("✅ Django initialized at module load time")
    except Exception as e:
        print(f"⚠️ Django setup failed (will retry per-request): {e}")

# Try to initialize Django immediately
_setup_django_once()
import json
import asyncio
from datetime import datetime, timedelta
from typing import List, Optional, Dict

# Load environment variables from .env files (for API keys)
try:
    from dotenv import load_dotenv
    # Try to load from multiple possible locations
    backend_path = os.path.join(os.path.dirname(__file__), 'deployment_package', 'backend')
    env_paths = [
        os.path.join(backend_path, 'env.secrets'),
        os.path.join(backend_path, '.env'),
        os.path.join(backend_path, '.env.local'),
        os.path.join(os.path.dirname(__file__), '.env'),
        os.path.join(os.path.dirname(__file__), '.env.local'),
    ]
    for env_path in env_paths:
        if os.path.exists(env_path):
            load_dotenv(env_path)
            print(f"✅ Loaded environment from {env_path}")
            break
except ImportError:
    print("⚠️ python-dotenv not installed, using system environment variables")
except Exception as e:
    print(f"⚠️ Could not load .env files: {e}")

# Import real market data service
try:
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend', 'backend'))
    from core.simple_market_data_service import SimpleMarketDataService
    _market_data_service = SimpleMarketDataService()
    
    # Check if API keys are available
    has_finnhub = bool(os.getenv('FINNHUB_API_KEY'))
    has_alpha_vantage = bool(os.getenv('ALPHA_VANTAGE_API_KEY'))
    
    if has_finnhub or has_alpha_vantage:
        print(f"✅ Real market data service loaded (Finnhub: {'✅' if has_finnhub else '❌'}, Alpha Vantage: {'✅' if has_alpha_vantage else '❌'})")
    else:
        print("⚠️ Real market data service loaded but no API keys found (using fallback)")
        print("   Set FINNHUB_API_KEY or ALPHA_VANTAGE_API_KEY environment variables")
except Exception as e:
    print(f"⚠️ Could not load real market data service: {e}")
    _market_data_service = None

# In-memory watchlist store (for mock/development)
# Key: symbol (uppercase), Value: watchlist item data
_mock_watchlist_store: Dict[str, Dict] = {}

# In-memory user profile store (for mock/development)
# Key: user_id (default "1"), Value: income profile data
_mock_user_profile_store: Dict[str, Dict] = {
    # Default profile for user "1"
    "1": {
        "incomeBracket": "Under $30,000",
        "age": 28,
        "investmentGoals": ["Emergency Fund", "Wealth Building"],
        "riskTolerance": "Moderate",
        "investmentHorizon": "5-10 years"
    }
}

# Stock metadata (sector, marketCap, peRatio, dividendYield) - fallback data
# In production, this would come from company profile APIs
_STOCK_METADATA = {
    "AAPL": {"companyName": "Apple Inc.", "sector": "Technology", "marketCap": 2900000000000, "peRatio": 28.5, "dividendYield": 0.0044, "beginnerFriendlyScore": 85},
    "MSFT": {"companyName": "Microsoft Corporation", "sector": "Technology", "marketCap": 3200000000000, "peRatio": 32.0, "dividendYield": 0.007, "beginnerFriendlyScore": 88},
    "GOOGL": {"companyName": "Alphabet Inc.", "sector": "Technology", "marketCap": 1800000000000, "peRatio": 24.0, "dividendYield": 0.0, "beginnerFriendlyScore": 82},
    "TSLA": {"companyName": "Tesla Inc.", "sector": "Consumer Cyclical", "marketCap": 780000000000, "peRatio": 65.0, "dividendYield": 0.0, "beginnerFriendlyScore": 72},
    "NVDA": {"companyName": "NVIDIA Corporation", "sector": "Technology", "marketCap": 1200000000000, "peRatio": 45.0, "dividendYield": 0.0003, "beginnerFriendlyScore": 78},
    "AMZN": {"companyName": "Amazon.com Inc.", "sector": "Consumer Cyclical", "marketCap": 1500000000000, "peRatio": 42.0, "dividendYield": 0.0, "beginnerFriendlyScore": 80},
    "META": {"companyName": "Meta Platforms Inc.", "sector": "Technology", "marketCap": 850000000000, "peRatio": 22.0, "dividendYield": 0.0, "beginnerFriendlyScore": 75},
    "JNJ": {"companyName": "Johnson & Johnson", "sector": "Healthcare", "marketCap": 420000000000, "peRatio": 28.0, "dividendYield": 0.026, "beginnerFriendlyScore": 92},
}

app = FastAPI(title="RichesReach Main Server", version="1.0.0")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API routers
try:
    import sys
    import os
    backend_path = os.path.join(os.path.dirname(__file__), 'backend', 'backend')
    if backend_path not in sys.path:
        sys.path.insert(0, backend_path)
    from core.holding_insight_api import router as holding_insight_router
    app.include_router(holding_insight_router)
    print("✅ Holding Insight API router registered")
except ImportError as e:
    print(f"⚠️ Holding Insight API router not available: {e}")
except Exception as e:
    print(f"⚠️ Error registering Holding Insight API router: {e}")

# Register Constellation AI API router
try:
    import sys
    import os
    # Try deployment_package/backend first
    deployment_backend_path = os.path.join(os.path.dirname(__file__), 'deployment_package', 'backend')
    if os.path.exists(deployment_backend_path) and deployment_backend_path not in sys.path:
        sys.path.insert(0, deployment_backend_path)
    
    # Fallback to backend/backend
    backend_path = os.path.join(os.path.dirname(__file__), 'backend', 'backend')
    if backend_path not in sys.path:
        sys.path.insert(0, backend_path)
    
    from core.constellation_ai_api import router as constellation_ai_router
    app.include_router(constellation_ai_router)
    print("✅ Constellation AI API router registered")
except ImportError as e:
    print(f"⚠️ Constellation AI API router not available: {e}")
except Exception as e:
    print(f"⚠️ Error registering Constellation AI API router: {e}")

# Register Family Sharing API router
try:
    import sys
    import os
    deployment_backend_path = os.path.join(os.path.dirname(__file__), 'deployment_package', 'backend')
    if os.path.exists(deployment_backend_path) and deployment_backend_path not in sys.path:
        sys.path.insert(0, deployment_backend_path)
    
    backend_path = os.path.join(os.path.dirname(__file__), 'backend', 'backend')
    if backend_path not in sys.path:
        sys.path.insert(0, backend_path)
    
    from core.family_sharing_api import router as family_sharing_router
    app.include_router(family_sharing_router)
    print("✅ Family Sharing API router registered")
except ImportError as e:
    print(f"⚠️ Family Sharing API router not available: {e}")
except Exception as e:
    print(f"⚠️ Error registering Family Sharing API router: {e}")

# Register Dawn Ritual API router
try:
    import sys
    import os
    deployment_backend_path = os.path.join(os.path.dirname(__file__), 'deployment_package', 'backend')
    if os.path.exists(deployment_backend_path) and deployment_backend_path not in sys.path:
        sys.path.insert(0, deployment_backend_path)
    
    backend_path = os.path.join(os.path.dirname(__file__), 'backend', 'backend')
    if backend_path not in sys.path:
        sys.path.insert(0, backend_path)
    
    from core.dawn_ritual_api import router as dawn_ritual_router
    app.include_router(dawn_ritual_router)
    print("✅ Dawn Ritual API router registered")
except ImportError as e:
    print(f"⚠️ Dawn Ritual API router not available: {e}")
except Exception as e:
    print(f"⚠️ Error registering Dawn Ritual API router: {e}")

# Register Credit Building API router
try:
    import sys
    import os
    deployment_backend_path = os.path.join(os.path.dirname(__file__), 'deployment_package', 'backend')
    if os.path.exists(deployment_backend_path) and deployment_backend_path not in sys.path:
        sys.path.insert(0, deployment_backend_path)
    
    backend_path = os.path.join(os.path.dirname(__file__), 'backend', 'backend')
    if backend_path not in sys.path:
        sys.path.insert(0, backend_path)
    
    from core.credit_api import router as credit_router
    app.include_router(credit_router)
    print("✅ Credit Building API router registered")
except ImportError as e:
    print(f"⚠️ Credit Building API router not available: {e}")
except Exception as e:
    print(f"⚠️ Error registering Credit Building API router: {e}")

@app.get("/health")
async def health():
    return {"status": "ok", "schemaVersion": "1.0.0", "timestamp": datetime.now().isoformat()}

@app.get("/api/market/quotes")
async def get_market_quotes(symbols: str):
    """Get market quotes for multiple symbols using real market data."""
    try:
        symbol_list = [s.strip().upper() for s in symbols.split(',')]
        quotes = []
        
        if _market_data_service:
            # Fetch real market data for each symbol
            for symbol in symbol_list:
                try:
                    print(f"📡 Fetching real data for {symbol}...")
                    quote_data = await _market_data_service.get_stock_quote(symbol)
                    print(f"📡 Result for {symbol}: {'✅ Got data' if quote_data else '❌ No data'}")
                    if quote_data:
                        quotes.append({
                            "symbol": symbol,
                            "price": quote_data.get('price', 0),
                            "change": quote_data.get('change', 0),
                            "changePercent": quote_data.get('change_percent', 0) / 100 if isinstance(quote_data.get('change_percent'), (int, float)) else 0,
                            "volume": quote_data.get('volume', 0),
                            "marketCap": _STOCK_METADATA.get(symbol, {}).get('marketCap', 0),
                            "timestamp": quote_data.get('timestamp', datetime.now().isoformat()),
                            "provider": quote_data.get('provider', 'unknown')
                        })
                    else:
                        # Fallback to mock if API fails
                        print(f"⚠️ No real data for {symbol}, using fallback")
                        quotes.append({
                            "symbol": symbol,
                            "price": 150.0,
                            "change": 0.0,
                            "changePercent": 0.0,
                            "volume": 0,
                            "marketCap": _STOCK_METADATA.get(symbol, {}).get('marketCap', 0),
                            "timestamp": datetime.now().isoformat(),
                            "provider": "fallback"
                        })
                except Exception as e:
                    print(f"⚠️ Error fetching real data for {symbol}: {e}")
                    # Fallback
                    quotes.append({
                        "symbol": symbol,
                        "price": 150.0,
                        "change": 0.0,
                        "changePercent": 0.0,
                        "volume": 0,
                        "marketCap": _STOCK_METADATA.get(symbol, {}).get('marketCap', 0),
                        "timestamp": datetime.now().isoformat(),
                        "provider": "fallback"
                    })
        else:
            # No market data service available, use fallback
            for symbol in symbol_list:
                quotes.append({
                    "symbol": symbol,
                    "price": _STOCK_METADATA.get(symbol, {}).get('currentPrice', 150.0),
                    "change": 0.0,
                    "changePercent": 0.0,
                    "volume": 0,
                    "marketCap": _STOCK_METADATA.get(symbol, {}).get('marketCap', 0),
                    "timestamp": datetime.now().isoformat(),
                    "provider": "fallback"
                })
        
        return {"quotes": quotes}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/pump-fun/launch")
async def pump_fun_launch(request: Request):
    """Pump.fun meme launch endpoint."""
    try:
        body = await request.json()
        
        # Validate required fields
        required_fields = ["name", "symbol", "description", "template", "culturalTheme"]
        missing_fields = [field for field in required_fields if not body.get(field)]
        
        if missing_fields:
            raise HTTPException(
                status_code=400, 
                detail=f"Missing required fields: {', '.join(missing_fields)}"
            )
        
        return {
            "success": True,
            "message": "Meme launched successfully!",
            "contractAddress": "0x" + "".join([f"{ord(c):02x}" for c in body["name"]])[:40],
            "symbol": body["symbol"],
            "name": body["name"]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/trading/quote/{symbol}")
async def trading_quote(symbol: str):
    """Trading quote endpoint."""
    return {
        "symbol": symbol,
        "bid": 149.50,
        "ask": 150.00,
        "bidSize": 100,
        "askSize": 200,
        "timestamp": datetime.now().isoformat()
    }

@app.get("/api/portfolio/recommendations")
async def portfolio_recommendations():
    """Portfolio recommendations endpoint."""
    return {
        "recommendations": [
            {
                "symbol": "AAPL",
                "action": "buy",
                "confidence": 0.85,
                "reason": "Strong earnings growth"
            },
            {
                "symbol": "TSLA",
                "action": "hold",
                "confidence": 0.70,
                "reason": "Volatile but trending up"
            }
        ]
    }

@app.post("/api/kyc/workflow")
async def kyc_workflow(request: Request):
    """KYC workflow endpoint."""
    return {
        "success": True,
        "workflowId": "KYC-12345",
        "status": "pending",
        "nextStep": "document_upload"
    }

@app.post("/api/alpaca/account")
async def alpaca_account(request: Request):
    """Alpaca account creation endpoint."""
    return {
        "success": True,
        "accountId": "ALP-67890",
        "status": "pending_approval"
    }

@app.post("/digest/daily")
async def generate_daily_digest(request: Request):
    """Generate daily voice digest for user."""
    print(f"📢 Daily Voice Digest endpoint called at {datetime.now().isoformat()}")
    try:
        body = await request.json()
        user_id = body.get("user_id", "demo-user")
        preferred_time = body.get("preferred_time")
        
        print(f"📢 Generating digest for user: {user_id}")
        
        # Generate digest with regime context and insights
        digest_id = f"digest-{user_id}-{int(datetime.now().timestamp())}"
        
        # Mock regime detection (in production, use real ML model)
        current_regime = "bull_market"  # Could be: bull_market, bear_market, sideways, choppy
        regime_confidence = 0.82
        
        # Generate voice script with market insights
        voice_script = f"""Good morning! Today's market outlook is {current_regime.replace('_', ' ')} with {regime_confidence * 100:.0f}% confidence. 
        Key highlights: Technology stocks are showing strong momentum, with AI and cloud services leading the way.
        Your portfolio is positioned well for current conditions. Consider rebalancing if you haven't done so in the last quarter.
        Remember, stay disciplined and stick to your investment plan. That's your daily digest for today."""
        
        response = {
            "digest_id": digest_id,
            "user_id": user_id,
            "regime_context": {
                "current_regime": current_regime,
                "regime_confidence": regime_confidence,
                "regime_description": f"Current market conditions indicate a {current_regime.replace('_', ' ')} environment",
                "relevant_strategies": [
                    "Momentum trading",
                    "Sector rotation",
                    "Quality stock selection"
                ],
                "common_mistakes": [
                    "Overtrading in volatile conditions",
                    "Ignoring risk management",
                    "Chasing short-term trends"
                ]
            },
            "voice_script": voice_script,
            "key_insights": [
                "Technology sector showing strong momentum",
                "AI and cloud services leading growth",
                "Portfolio well-positioned for current regime"
            ],
            "actionable_tips": [
                "Consider rebalancing if needed",
                "Review positions monthly",
                "Stay disciplined with investment plan"
            ],
            "pro_teaser": "Upgrade to Pro for advanced regime analysis and personalized strategies",
            "generated_at": datetime.now().isoformat(),
            "scheduled_for": preferred_time or (datetime.now() + timedelta(hours=24)).isoformat()
        }
        
        print(f"✅ Successfully generated digest: {digest_id}")
        return response
        
    except json.JSONDecodeError as e:
        print(f"❌ JSON decode error in daily digest: {e}")
        raise HTTPException(status_code=400, detail=f"Invalid JSON in request body: {str(e)}")
    except Exception as e:
        print(f"❌ Error generating daily digest: {e}")
        import traceback
        traceback.print_exc()
        # Return a valid error response instead of raising
        raise HTTPException(status_code=500, detail=f"Failed to generate daily digest: {str(e)}")

@app.post("/digest/regime-alert")
async def create_regime_alert(request: Request):
    """Create regime change alert."""
    try:
        body = await request.json()
        user_id = body.get("user_id", "demo-user")
        regime_change = body.get("regime_change", {})
        urgency = body.get("urgency", "medium")
        
        alert_id = f"alert-{user_id}-{int(datetime.now().timestamp())}"
        
        return {
            "notification_id": alert_id,
            "user_id": user_id,
            "regime_change": {
                "old_regime": regime_change.get("old_regime", "bull_market"),
                "new_regime": regime_change.get("new_regime", "bear_market"),
                "confidence": regime_change.get("confidence", 0.75),
                "urgency": urgency,
                "type": "regime_change"
            },
            "scheduled_for": datetime.now().isoformat(),
            "type": "regime_alert"
        }
    except Exception as e:
        print(f"Error creating regime alert: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to create regime alert: {str(e)}")

# Yodlee Banking Integration Endpoints
@app.get("/api/yodlee/fastlink/start")
async def yodlee_fastlink_start(request: Request):
    """Create FastLink session for bank account linking"""
    try:
        _setup_django_once()
        from deployment_package.backend.core.banking_views import StartFastlinkView
        view = StartFastlinkView()
        # Convert FastAPI request to Django request
        from django.http import HttpRequest
        django_request = HttpRequest()
        django_request.method = 'GET'
        django_request.user = request.state.user if hasattr(request.state, 'user') else None
        django_request.META = dict(request.headers)
        response = view.get(django_request)
        return JSONResponse(content=json.loads(response.content), status_code=response.status_code)
    except Exception as e:
        print(f"Error in Yodlee FastLink start: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/yodlee/fastlink/callback")
async def yodlee_callback(request: Request):
    """Handle FastLink callback"""
    try:
        _setup_django_once()
        from deployment_package.backend.core.banking_views import YodleeCallbackView
        view = YodleeCallbackView()
        from django.http import HttpRequest
        django_request = HttpRequest()
        django_request.method = 'POST'
        django_request.user = request.state.user if hasattr(request.state, 'user') else None
        body = await request.body()
        django_request._body = body
        django_request.META = dict(request.headers)
        response = view.post(django_request)
        return JSONResponse(content=json.loads(response.content), status_code=response.status_code)
    except Exception as e:
        print(f"Error in Yodlee callback: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/yodlee/accounts")
async def yodlee_accounts(request: Request):
    """Get user's bank accounts"""
    try:
        _setup_django_once()
        from deployment_package.backend.core.banking_views import AccountsView
        view = AccountsView()
        from django.http import HttpRequest
        django_request = HttpRequest()
        django_request.method = 'GET'
        django_request.user = request.state.user if hasattr(request.state, 'user') else None
        django_request.META = dict(request.headers)
        response = view.get(django_request)
        return JSONResponse(content=json.loads(response.content), status_code=response.status_code)
    except Exception as e:
        print(f"Error getting Yodlee accounts: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/yodlee/transactions")
async def yodlee_transactions(request: Request):
    """Get bank transactions"""
    try:
        _setup_django_once()
        from deployment_package.backend.core.banking_views import TransactionsView
        view = TransactionsView()
        from django.http import HttpRequest
        django_request = HttpRequest()
        django_request.method = 'GET'
        django_request.GET = request.query_params
        django_request.user = request.state.user if hasattr(request.state, 'user') else None
        django_request.META = dict(request.headers)
        response = view.get(django_request)
        return JSONResponse(content=json.loads(response.content), status_code=response.status_code)
    except Exception as e:
        print(f"Error getting Yodlee transactions: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/yodlee/refresh")
async def yodlee_refresh(request: Request):
    """Refresh bank account data"""
    try:
        _setup_django_once()
        from deployment_package.backend.core.banking_views import RefreshAccountView
        view = RefreshAccountView()
        from django.http import HttpRequest
        django_request = HttpRequest()
        django_request.method = 'POST'
        django_request.user = request.state.user if hasattr(request.state, 'user') else None
        body = await request.body()
        django_request._body = body
        django_request.META = dict(request.headers)
        response = view.post(django_request)
        return JSONResponse(content=json.loads(response.content), status_code=response.status_code)
    except Exception as e:
        print(f"Error refreshing Yodlee account: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/yodlee/bank-link/{bank_link_id}")
async def yodlee_delete_bank_link(request: Request, bank_link_id: int):
    """Delete bank link"""
    try:
        _setup_django_once()
        from deployment_package.backend.core.banking_views import DeleteBankLinkView
        view = DeleteBankLinkView()
        from django.http import HttpRequest
        django_request = HttpRequest()
        django_request.method = 'DELETE'
        django_request.user = request.state.user if hasattr(request.state, 'user') else None
        django_request.META = dict(request.headers)
        response = view.delete(django_request, bank_link_id)
        return JSONResponse(content=json.loads(response.content), status_code=response.status_code)
    except Exception as e:
        print(f"Error deleting Yodlee bank link: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/yodlee/webhook")
async def yodlee_webhook(request: Request):
    """Handle Yodlee webhook events"""
    try:
        _setup_django_once()
        from deployment_package.backend.core.banking_views import WebhookView
        view = WebhookView()
        from django.http import HttpRequest
        django_request = HttpRequest()
        django_request.method = 'POST'
        body = await request.body()
        django_request._body = body
        django_request.META = dict(request.headers)
        response = view.post(django_request)
        return JSONResponse(content=json.loads(response.content), status_code=response.status_code)
    except Exception as e:
        print(f"Error processing Yodlee webhook: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/money/snapshot")
async def money_snapshot(request: Request):
    """
    Returns unified financial snapshot:
    - Net worth (bank balances + portfolio)
    - Cash flow (30-day in/out/delta)
    - Portfolio positions
    - Shield alerts
    """
    try:
        _setup_django_once()
        from django.http import HttpRequest
        from django.utils import timezone
        from datetime import timedelta
        from decimal import Decimal
        
        # Get user from request (same pattern as Yodlee endpoints)
        user = request.state.user if hasattr(request.state, 'user') else None
        
        # Dev mode: Return mock data if not authenticated (for testing)
        # Only require auth in production
        is_production = os.getenv('ENVIRONMENT') == 'production' or os.getenv('ENV') == 'production'
        print(f"[DEBUG] money_snapshot: user={user}, is_production={is_production}, has_user={hasattr(request.state, 'user')}")
        if not user and not is_production:
            print("[DEBUG] Returning mock data (dev mode)")
            print("⚠️ [DEV MODE] Returning mock money snapshot (no auth)")
            return JSONResponse(content={
                'netWorth': 12500.50,
                'cashflow': {
                    'period': '30d',
                    'in': 3820.40,
                    'out': 3600.10,
                    'delta': 220.30,
                },
                'positions': [
                    {'symbol': 'NVDA', 'value': 1200.00, 'shares': 10},
                    {'symbol': 'TSLA', 'value': 1250.00, 'shares': 5},
                ],
                'shield': [
                    {
                        'type': 'LOW_BALANCE',
                        'inDays': None,
                        'suggestion': 'PAUSE_RISKY_ORDER',
                        'message': 'Low balance detected ($500.00). Consider pausing high-risk trades.'
                    }
                ],
                'breakdown': {
                    'bankBalance': 10000.50,
                    'portfolioValue': 2450.00,
                    'bankAccountsCount': 2,
                }
            })
        
        if not user:
            raise HTTPException(status_code=401, detail="Authentication required")
        
        # Import models
        from deployment_package.backend.core.banking_models import BankAccount, BankTransaction
        from deployment_package.backend.core.models import Portfolio
        
        # Calculate date range (last 30 days)
        to_date = timezone.now().date()
        from_date = to_date - timedelta(days=30)
        
        # 1. Get bank accounts and calculate total bank balance
        bank_accounts = BankAccount.objects.filter(
            user=user,
            is_verified=True
        )
        
        total_bank_balance = Decimal('0.00')
        bank_accounts_list = []
        for account in bank_accounts:
            balance = account.balance_current or Decimal('0.00')
            total_bank_balance += balance
            bank_accounts_list.append({
                'id': account.id,
                'name': account.name,
                'type': account.account_type,
                'balance': float(balance),
            })
        
        # 2. Get portfolio positions
        portfolio_holdings = Portfolio.objects.filter(user=user).select_related('stock')
        
        total_portfolio_value = Decimal('0.00')
        positions = []
        for holding in portfolio_holdings:
            # Use total_value if available, otherwise calculate
            value = holding.total_value if holding.total_value else (
                (holding.current_price or holding.average_price or Decimal('0')) * holding.shares
            )
            total_portfolio_value += value
            
            positions.append({
                'symbol': holding.stock.symbol if holding.stock else 'UNKNOWN',
                'value': float(value),
                'shares': holding.shares,
            })
        
        # 3. Calculate cash flow from transactions (last 30 days)
        transactions = BankTransaction.objects.filter(
            user=user,
            posted_date__gte=from_date,
            posted_date__lte=to_date,
        )
        
        inflow = Decimal('0.00')
        outflow = Decimal('0.00')
        
        for txn in transactions:
            if txn.transaction_type == 'CREDIT':
                inflow += txn.amount
            elif txn.transaction_type == 'DEBIT':
                outflow += abs(txn.amount)  # Outflows are negative, make positive
        
        cashflow_delta = inflow - outflow
        
        # 4. Calculate net worth
        net_worth = total_bank_balance + total_portfolio_value
        
        # 5. Generate shield alerts (simple logic)
        shield_alerts = []
        
        # Low balance alert
        if total_bank_balance < Decimal('500.00'):
            shield_alerts.append({
                'type': 'LOW_BALANCE',
                'inDays': None,
                'suggestion': 'PAUSE_RISKY_ORDER',
                'message': f'Low balance detected (${total_bank_balance:.2f}). Consider pausing high-risk trades.'
            })
        
        # Check for large outflows (potential bills)
        large_outflows = transactions.filter(
            transaction_type='DEBIT',
            amount__lt=-Decimal('100.00')  # Large negative amounts
        ).order_by('posted_date')
        
        if large_outflows.exists():
            # Check if any large outflow is due soon (within 3 days)
            for txn in large_outflows[:3]:  # Check top 3
                days_until = (txn.posted_date - to_date).days
                if 0 <= days_until <= 3:
                    shield_alerts.append({
                        'type': 'BILL_DUE',
                        'inDays': days_until,
                        'suggestion': 'PAUSE_RISKY_ORDER',
                        'message': f'Large payment due in {days_until} days (${abs(txn.amount):.2f})'
                    })
        
        # 6. Return unified snapshot
        return JSONResponse(content={
            'netWorth': float(net_worth),
            'cashflow': {
                'period': '30d',
                'in': float(inflow),
                'out': float(outflow),
                'delta': float(cashflow_delta),
            },
            'positions': positions,
            'shield': shield_alerts,
            'breakdown': {
                'bankBalance': float(total_bank_balance),
                'portfolioValue': float(total_portfolio_value),
                'bankAccountsCount': len(bank_accounts_list),
            }
        })
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error getting money snapshot: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/graphql/")
async def graphql_endpoint(request: Request):
    """GraphQL endpoint for Apollo Client - Uses Django Graphene schema with PostgreSQL."""
    try:
        # Ensure Django is initialized
        _setup_django_once()
        
        # Import Django GraphQL schema
        try:
            from core.schema import schema as graphene_schema
            print("✅ Using Django Graphene schema with PostgreSQL")
        except ImportError as e:
            print(f"⚠️ Could not import Django schema, using fallback: {e}")
            # Fallback to custom handlers if schema not available
            graphene_schema = None
        
        body = await request.json()
        query_str = body.get("query", "")
        variables = body.get("variables", {})
        operation_name = body.get("operationName", "")
        
        # Enhanced debug logging
        print(f"DEBUG: GraphQL operation={operation_name}, query_preview={query_str[:150]}...")
        
        # If Django schema is available, use it (production mode with PostgreSQL)
        if graphene_schema:
            try:
                # Run in thread pool since graphene.execute is synchronous
                # but we're in an async FastAPI endpoint
                loop = asyncio.get_event_loop()
                result = await loop.run_in_executor(
                    None,
                    lambda: graphene_schema.execute(
                        query_str,
                        variables=variables,
                        operation_name=operation_name,
                        context={'request': request}
                    )
                )
                
                if result.errors:
                    print(f"⚠️ GraphQL errors: {result.errors}")
                    error_messages = []
                    for error in result.errors:
                        if hasattr(error, 'message'):
                            error_messages.append({"message": str(error.message)})
                        else:
                            error_messages.append({"message": str(error)})
                    return {
                        "data": result.data or {},
                        "errors": error_messages
                    }
                
                print(f"✅ GraphQL query executed successfully via Django schema (PostgreSQL)")
                return {
                    "data": result.data or {},
                    "errors": []
                }
            except Exception as schema_error:
                print(f"⚠️ Django schema execution failed: {schema_error}")
                import traceback
                traceback.print_exc()
                # Fall through to custom handlers as fallback
        
        # Fallback to custom handlers if Django schema not available
        print("⚠️ Using custom GraphQL handlers (fallback mode)")
        
        # More precise matching: check operationName first, then query string
        is_my_watchlist_query = (
            operation_name == "GetMyWatchlist" or 
            ("myWatchlist" in query_str and ("query" in query_str.lower() or query_str.strip().startswith("{")))
        )
        is_add_to_watchlist_mutation = (
            operation_name == "AddToWatchlist" or
            ("addToWatchlist" in query_str and "mutation" in query_str.lower())
        )
        is_remove_from_watchlist_mutation = (
            operation_name == "RemoveFromWatchlist" or
            ("removeFromWatchlist" in query_str and "mutation" in query_str.lower())
        )
        is_me_query = (
            operation_name in ["GetMe", "GetUserProfile", "Me"] or
            (not is_my_watchlist_query and not is_add_to_watchlist_mutation and not is_remove_from_watchlist_mutation and "me" in query_str and "{ me" in query_str and "myWatchlist" not in query_str and "createIncomeProfile" not in query_str)
        )
        is_research_hub_query = (
            operation_name == "Research" or
            "researchHub" in query_str
        )
        is_stock_chart_data_query = (
            operation_name == "Chart" or
            "stockChartData" in query_str
        )
        is_crypto_portfolio_query = (
            operation_name == "GetCryptoPortfolio" or
            "cryptoPortfolio" in query_str
        )
        is_crypto_analytics_query = (
            operation_name == "GetCryptoAnalytics" or
            "cryptoAnalytics" in query_str
        )
        is_crypto_ml_signal_query = (
            operation_name == "GetCryptoMLSignal" or
            "cryptoMlSignal" in query_str
        )
        is_generate_ml_prediction_mutation = (
            operation_name == "GenerateMLPrediction" or
            ("generateMlPrediction" in query_str and "mutation" in query_str.lower())
        )
        is_crypto_recommendations_query = (
            operation_name == "GetCryptoRecommendations" or
            "cryptoRecommendations" in query_str
        )
        is_supported_currencies_query = (
            operation_name == "GetSupportedCurrencies" or
            "supportedCurrencies" in query_str
        )
        is_ai_recommendations_query = (
            operation_name == "GetAIRecommendations" or
            "aiRecommendations" in query_str
        )
        
        print(f"🔍 Handler detection: myWatchlist={is_my_watchlist_query}, addToWatchlist={is_add_to_watchlist_mutation}, removeFromWatchlist={is_remove_from_watchlist_mutation}, me={is_me_query}, researchHub={is_research_hub_query}, stockChartData={is_stock_chart_data_query}, cryptoPortfolio={is_crypto_portfolio_query}, cryptoAnalytics={is_crypto_analytics_query}, cryptoMlSignal={is_crypto_ml_signal_query}, generateMlPrediction={is_generate_ml_prediction_mutation}, cryptoRecommendations={is_crypto_recommendations_query}, supportedCurrencies={is_supported_currencies_query}, aiRecommendations={is_ai_recommendations_query}")
        
        # Handle common GraphQL queries
        # IMPORTANT: Order matters! More specific handlers should come first
        
        # Handle generateAiRecommendations mutation (must come before aiRecommendations query)
        is_generate_ai_recommendations_mutation = (
            operation_name == "GenerateAIRecommendations" or
            ("generateAiRecommendations" in query_str and "mutation" in query_str.lower())
        )
        
        if is_generate_ai_recommendations_mutation:
            print(f"🚀 GenerateAIRecommendations mutation received")
            user_id = "1"
            stored_profile = _mock_user_profile_store.get(user_id, {})
            
            # Generate recommendations (reuse the same logic as query)
            # For now, just return success - the query will handle the actual data
            return {
                "data": {
                    "generateAiRecommendations": {
                        "success": True,
                        "message": "AI recommendations generated successfully",
                        "recommendations": {}  # Data will be fetched via query
                    }
                }
            }
        
        # Handle createIncomeProfile mutation (must come before other queries)
        if "createIncomeProfile" in query_str and "mutation" in query_str.lower():
            print(f"💾 CreateIncomeProfile mutation received")
            user_id = "1"  # Default user ID
            
            # Extract variables
            income_bracket = variables.get("incomeBracket", "")
            age = variables.get("age", 0)
            investment_goals = variables.get("investmentGoals", [])
            risk_tolerance = variables.get("riskTolerance", "")
            investment_horizon = variables.get("investmentHorizon", "")
            
            # Validate required fields
            if not income_bracket or not age or not investment_goals or not risk_tolerance or not investment_horizon:
                return {
                    "data": {
                        "createIncomeProfile": {
                            "success": False,
                            "message": "Missing required fields"
                        }
                    }
                }
            
            # Store the profile in memory
            _mock_user_profile_store[user_id] = {
                "incomeBracket": income_bracket,
                "age": age,
                "investmentGoals": investment_goals,
                "riskTolerance": risk_tolerance,
                "investmentHorizon": investment_horizon
            }
            
            print(f"✅ Profile saved for user {user_id}: {income_bracket}, age {age}, {len(investment_goals)} goals")
            
            return {
                "data": {
                    "createIncomeProfile": {
                        "success": True,
                        "message": "Profile created successfully"
                    }
                }
            }
        
        elif "placeStockOrder" in query_str:
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
        
        # Handle removeFromWatchlist mutation FIRST (before queries)
        if is_remove_from_watchlist_mutation:
            symbol = variables.get("symbol", "").upper()
            print(f"🗑️ MOCK RemoveFromWatchlist mutation: symbol={symbol}")
            
            if not symbol:
                return {
                    "data": {
                        "removeFromWatchlist": {
                            "success": False,
                            "message": "Symbol is required",
                            "__typename": "RemoveFromWatchlist"
                        }
                    }
                }
            
            # Remove from in-memory store
            if symbol in _mock_watchlist_store:
                del _mock_watchlist_store[symbol]
                print(f"✅ MOCK: Removed {symbol} from watchlist (remaining items: {len(_mock_watchlist_store)})")
                return {
                    "data": {
                        "removeFromWatchlist": {
                            "success": True,
                            "message": f"Successfully removed {symbol} from watchlist",
                            "__typename": "RemoveFromWatchlist"
                        }
                    }
                }
            else:
                print(f"⚠️ MOCK: {symbol} not found in watchlist")
                return {
                    "data": {
                        "removeFromWatchlist": {
                            "success": False,
                            "message": f"{symbol} is not in your watchlist",
                            "__typename": "RemoveFromWatchlist"
                        }
                    }
                }
        
        # Handle watchlist queries (before other mutations)
        elif is_my_watchlist_query:
            # Return all items from the in-memory store
            watchlist_items = list(_mock_watchlist_store.values())
            print(f"📋 myWatchlist query received. Store size: {len(_mock_watchlist_store)}, Items: {list(_mock_watchlist_store.keys())}")
            print(f"📋 Returning {len(watchlist_items)} watchlist items from mock store")
            return {
                "data": {
                    "myWatchlist": watchlist_items
                }
            }
        
        # Handle addToWatchlist mutation (must come before "me" to prevent conflicts)
        elif is_add_to_watchlist_mutation:
            import re
            import django
            
            # Ensure Django is initialized (only once at module load)
            _setup_django_once()
            
            # MOCK HANDLER: Bypass Django for now to test full success flow
            # TODO: Replace with Django model logic once dependencies are installed
            symbol = variables.get("symbol", "").upper()
            company_name = variables.get("company_name") or variables.get("companyName") or f"{symbol} Inc."
            notes = variables.get("notes", "")
            
            print(f"🎯 MOCK AddToWatchlist mutation: symbol={symbol}, company_name={company_name}, notes={notes}")
            
            if not symbol:
                return {
                    "data": {
                        "addToWatchlist": {
                            "success": False,
                            "message": "Symbol is required",
                            "__typename": "AddToWatchlist"
                        }
                    }
                }
            
            # MOCK: Store the watchlist item in memory
            # If item already exists, update it (don't create duplicate)
            if symbol in _mock_watchlist_store:
                # Update existing item (e.g., if notes changed)
                existing_item = _mock_watchlist_store[symbol]
                existing_item["notes"] = notes or existing_item.get("notes", "")
                existing_item["stock"]["companyName"] = company_name or existing_item["stock"].get("companyName", f"{symbol} Inc.")
                watchlist_item = existing_item
                print(f"📝 MOCK: Updated existing watchlist item for {symbol}")
            else:
                # Create new item
                item_id = f"mock-{symbol}-{len(_mock_watchlist_store) + 1}"
                # Mock price data - in real app, this would come from market data service
                mock_prices = {
                    "AAPL": {"price": 189.0, "change": 9.0, "changePercent": 0.05},
                    "TSLA": {"price": 245.0, "change": -12.0, "changePercent": -0.047},
                    "MSFT": {"price": 420.0, "change": 15.0, "changePercent": 0.037},
                    "GOOGL": {"price": 145.0, "change": 2.5, "changePercent": 0.018},
                    "NVDA": {"price": 495.0, "change": 25.0, "changePercent": 0.053},
                }
                price_data = mock_prices.get(symbol, {"price": 150.0, "change": 0.0, "changePercent": 0.0})
                
                watchlist_item = {
                    "id": item_id,
                    "stock": {
                        "symbol": symbol,
                        "companyName": company_name,
                        "currentPrice": price_data["price"],
                        "change": price_data["change"],
                        "changePercent": price_data["changePercent"],
                        "__typename": "Stock"
                    },
                    "addedAt": datetime.now().isoformat(),
                    "notes": notes or "",
                    "targetPrice": None,
                    "__typename": "WatchlistItem"
                }
            
            # Store in memory (keyed by symbol for easy lookup/duplicate prevention)
            _mock_watchlist_store[symbol] = watchlist_item
            
            success = True
            message = f"Mock: Successfully added {symbol} ({company_name}) to watchlist"
            if notes:
                message += f" with notes: {notes}"
            
            print(f"✅ MOCK: Stored {symbol} in watchlist (total items: {len(_mock_watchlist_store)})")
            
            return {
                "data": {
                    "addToWatchlist": {
                        "success": success,
                        "message": message,
                        "__typename": "AddToWatchlist"
                    }
                }
            }
            
            # ========================================
            # TODO: REAL DJANGO HANDLER (uncomment when deps installed)
            # ========================================
            # # Check if Django apps are ready (don't call setup() again - it's not reentrant)
            # try:
            #     import django.apps
            #     if not django.apps.apps.ready:
            #         return {
            #             "data": {
            #                 "addToWatchlist": {
            #                     "success": False,
            #                     "message": "Django apps not initialized. Please check server logs.",
            #                     "__typename": "AddToWatchlist"
            #                 }
            #             }
            #     }
            # except:
            #     pass
            # 
            # try:
            #     from core.models import Stock, Watchlist, WatchlistItem
            #     from django.contrib.auth import get_user_model
            #     User = get_user_model()
            #     # ... rest of Django logic ...
            # except Exception as e:
            #     print(f"❌ Error in addToWatchlist: {e}")
            #     error_symbol = variables.get("symbol", "unknown")
            #     return {
            #         "data": {
            #             "addToWatchlist": {
            #                 "success": False,
            #                 "message": f"Failed to add {error_symbol} to watchlist: {str(e)}",
            #                 "__typename": "AddToWatchlist"
            #             }
            #         }
            #     }
        
        # Handle researchHub query (comprehensive research data)
        elif is_research_hub_query:
            symbol = variables.get("s") or variables.get("symbol", "AAPL").upper()
            print(f"📊 ResearchHub query for {symbol}")
            
            # Get real market data
            quote_data = None
            if _market_data_service:
                try:
                    quote_data = await _market_data_service.get_stock_quote(symbol)
                except Exception as e:
                    print(f"⚠️ Error fetching real data for researchHub {symbol}: {e}")
            
            # Get stock metadata
            metadata = _STOCK_METADATA.get(symbol, {
                "companyName": f"{symbol} Inc.",
                "sector": "Unknown",
                "marketCap": 0,
                "peRatio": 0,
                "dividendYield": 0,
                "beginnerFriendlyScore": 50
            })
            
            # Build quote data
            current_price = quote_data.get("price", 150.0) if quote_data else 150.0
            change = quote_data.get("change", 0.0) if quote_data else 0.0
            change_percent = quote_data.get("changePercent", 0.0) if quote_data else 0.0
            
            # Calculate support/resistance (simple mock - in real app, use technical analysis)
            support_level = current_price * 0.95
            resistance_level = current_price * 1.05
            
            # Mock technical indicators
            rsi = 55.0  # Neutral RSI
            macd = 0.5
            macd_histogram = 0.1
            
            # Calculate simple moving averages (mock)
            moving_avg_50 = current_price * 0.98
            moving_avg_200 = current_price * 0.95
            
            # Mock sentiment
            sentiment_score = 0.6  # Slightly positive
            
            # Mock peers
            tech_peers = ["MSFT", "GOOGL", "AMZN", "NVDA", "META"]
            finance_peers = ["JPM", "BAC", "WFC", "GS", "MS"]
            peers_list = tech_peers if metadata.get("sector") == "Technology" else finance_peers[:3]
            if symbol in peers_list:
                peers_list = [p for p in peers_list if p != symbol]
            
            # Build technical data object (used by alias technicals: technical)
            technical_data = {
                "rsi": rsi,
                "macd": macd,
                "macdhistogram": macd_histogram,
                "movingAverage50": moving_avg_50,
                "movingAverage200": moving_avg_200,
                "supportLevel": support_level,
                "resistanceLevel": resistance_level,
                "impliedVolatility": 0.25
            }
            
            # Build sentiment data with all field name variations
            sentiment_data = {
                "label": "Positive" if sentiment_score > 0.5 else "Neutral",
                "sentiment_label": "Positive" if sentiment_score > 0.5 else "Neutral",
                "score": sentiment_score,
                "sentiment_score": sentiment_score,
                "article_count": 42,
                "articleCount": 42,
                "confidence": 0.75
            }
            
            research_response = {
                "symbol": symbol,
                "snapshot": {
                    "name": metadata.get("companyName", f"{symbol} Inc."),
                    "sector": metadata.get("sector", "Unknown"),
                    "marketCap": metadata.get("marketCap", 0),
                    "country": "USA",
                    "website": f"https://www.{symbol.lower()}.com"
                },
                "quote": {
                    "price": current_price,
                    "chg": change,
                    "chgPct": change_percent,
                    "high": current_price * 1.02,
                    "low": current_price * 0.98,
                    "volume": 10000000
                },
                # CRITICAL: GraphQL alias "technicals: technical" means response should have "technicals"
                # Apollo Client maps the alias to the response, so we need the ALIAS name
                "technicals": technical_data,  # Use alias name for GraphQL response
                "sentiment": sentiment_data,
                "macro": {
                    "vix": 18.5,  # Mock VIX
                    "marketSentiment": "Bullish",
                    "riskAppetite": "Moderate"
                },
                "marketRegime": {
                    "market_regime": "Bull Market",
                    "confidence": 0.7,
                    "recommended_strategy": "momentum_trading"
                },
                "peers": peers_list[:5],
                "updatedAt": datetime.now().isoformat()
            }
            
            return {"data": {"researchHub": research_response}}
        
        # Handle stockChartData query (chart with technical indicators)
        elif is_stock_chart_data_query:
            symbol = variables.get("symbol") or variables.get("s", "AAPL").upper()
            interval = variables.get("interval") or variables.get("iv", "1D")
            limit = variables.get("limit", 180)
            indicators = variables.get("indicators") or variables.get("inds", [])
            
            print(f"📈 stockChartData query for {symbol}, interval={interval}, limit={limit}")
            
            # Get real market data
            quote_data = None
            if _market_data_service:
                try:
                    quote_data = await _market_data_service.get_stock_quote(symbol)
                except Exception as e:
                    print(f"⚠️ Error fetching real data for chart {symbol}: {e}")
            
            current_price = quote_data.get("price", 150.0) if quote_data else 150.0
            change = quote_data.get("change", 0.0) if quote_data else 0.0
            change_percent = quote_data.get("changePercent", 0.0) if quote_data else 0.0
            
            # Generate mock chart data points (candles)
            import random
            
            base_time = datetime.now()
            chart_data = []
            
            # Generate price data with some variation
            price_variation = current_price * 0.05  # 5% variation
            
            for i in range(limit):
                timestamp = base_time - timedelta(days=limit - i - 1)
                # Simple random walk for price simulation
                open_price = current_price + random.uniform(-price_variation, price_variation)
                high_price = open_price * (1 + random.uniform(0, 0.02))
                low_price = open_price * (1 - random.uniform(0, 0.02))
                close_price = open_price + random.uniform(-price_variation * 0.5, price_variation * 0.5)
                volume = random.randint(1000000, 10000000)
                
                chart_data.append({
                    "timestamp": timestamp.isoformat(),
                    "open": round(open_price, 2),
                    "high": round(high_price, 2),
                    "low": round(low_price, 2),
                    "close": round(close_price, 2),
                    "volume": volume
                })
            
            # Calculate simple technical indicators
            closes = [d["close"] for d in chart_data[-50:]]
            sma_20 = sum(closes[-20:]) / 20 if len(closes) >= 20 else current_price
            sma_50 = sum(closes[-50:]) / 50 if len(closes) >= 50 else current_price
            
            # Simple EMA calculation (exponential moving average)
            ema_12 = sum(closes[-12:]) / 12 if len(closes) >= 12 else current_price
            ema_26 = sum(closes[-26:]) / 26 if len(closes) >= 26 else current_price
            
            # Simple Bollinger Bands
            std_dev = sum((c - current_price) ** 2 for c in closes[-20:]) / 20 if len(closes) >= 20 else price_variation
            bb_middle = sma_20
            bb_upper = bb_middle + (2 * std_dev ** 0.5)
            bb_lower = bb_middle - (2 * std_dev ** 0.5)
            
            # Mock RSI (should be 0-100)
            rsi_14 = 55.0  # Neutral
            
            # Mock MACD
            macd = ema_12 - ema_26
            macd_signal = macd * 0.9
            macd_hist = macd - macd_signal
            
            indicators_obj = {}
            if "SMA20" in indicators or "SMA" in str(indicators):
                indicators_obj["SMA20"] = round(sma_20, 2)
            if "SMA50" in indicators or "SMA" in str(indicators):
                indicators_obj["SMA50"] = round(sma_50, 2)
            if "EMA12" in indicators or "EMA" in str(indicators):
                indicators_obj["EMA12"] = round(ema_12, 2)
            if "EMA26" in indicators or "EMA" in str(indicators):
                indicators_obj["EMA26"] = round(ema_26, 2)
            if "BB" in str(indicators) or "Bollinger" in str(indicators):
                indicators_obj["BBUpper"] = round(bb_upper, 2)
                indicators_obj["BBMiddle"] = round(bb_middle, 2)
                indicators_obj["BBLower"] = round(bb_lower, 2)
            if "RSI" in str(indicators):
                indicators_obj["RSI14"] = round(rsi_14, 2)
            if "MACD" in str(indicators):
                indicators_obj["MACD"] = round(macd, 2)
                indicators_obj["MACDSignal"] = round(macd_signal, 2)
                indicators_obj["MACDHist"] = round(macd_hist, 2)
            
            chart_response = {
                "symbol": symbol,
                "interval": interval,
                "limit": limit,
                "currentPrice": current_price,
                "change": change,
                "changePercent": change_percent,
                "data": chart_data,
                "indicators": indicators_obj
            }
            
            return {"data": {"stockChartData": chart_response}}
        
        # Handle crypto portfolio query
        elif is_crypto_portfolio_query:
            print(f"💰 CryptoPortfolio query received")
            # Mock crypto portfolio data
            crypto_portfolio_response = {
                "id": "crypto-portfolio-1",
                "totalValueUsd": 125000.0,
                "totalCostBasis": 100000.0,
                "totalPnl": 25000.0,
                "totalPnlPercentage": 25.0,
                "portfolioVolatility": 0.35,
                "sharpeRatio": 1.2,
                "maxDrawdown": -0.15,
                "diversificationScore": 0.75,
                "topHoldingPercentage": 0.35,
                "createdAt": datetime.now().isoformat(),
                "updatedAt": datetime.now().isoformat(),
                "holdings": [
                    {
                        "id": "holding-btc-1",
                        "quantity": 0.5,
                        "averageCost": 45000.0,
                        "currentPrice": 55000.0,
                        "currentValue": 27500.0,
                        "unrealizedPnl": 5000.0,
                        "unrealizedPnlPercentage": 22.2,
                        "stakedQuantity": 0.0,
                        "stakingRewards": 0.0,
                        "stakingApy": 0.0,
                        "isCollateralized": False,
                        "collateralValue": 0.0,
                        "loanAmount": 0.0,
                        "createdAt": datetime.now().isoformat(),
                        "updatedAt": datetime.now().isoformat(),
                        "cryptocurrency": {
                            "id": "btc",
                            "symbol": "BTC",
                            "name": "Bitcoin",
                            "volatilityTier": "High"
                        }
                    },
                    {
                        "id": "holding-eth-1",
                        "quantity": 10.0,
                        "averageCost": 2500.0,
                        "currentPrice": 3200.0,
                        "currentValue": 32000.0,
                        "unrealizedPnl": 7000.0,
                        "unrealizedPnlPercentage": 28.0,
                        "stakedQuantity": 5.0,
                        "stakingRewards": 320.0,
                        "stakingApy": 4.5,
                        "isCollateralized": False,
                        "collateralValue": 0.0,
                        "loanAmount": 0.0,
                        "createdAt": datetime.now().isoformat(),
                        "updatedAt": datetime.now().isoformat(),
                        "cryptocurrency": {
                            "id": "eth",
                            "symbol": "ETH",
                            "name": "Ethereum",
                            "volatilityTier": "High"
                        }
                    },
                    {
                        "id": "holding-sol-1",
                        "quantity": 100.0,
                        "averageCost": 150.0,
                        "currentPrice": 180.0,
                        "currentValue": 18000.0,
                        "unrealizedPnl": 3000.0,
                        "unrealizedPnlPercentage": 20.0,
                        "stakedQuantity": 50.0,
                        "stakingRewards": 900.0,
                        "stakingApy": 6.2,
                        "isCollateralized": False,
                        "collateralValue": 0.0,
                        "loanAmount": 0.0,
                        "createdAt": datetime.now().isoformat(),
                        "updatedAt": datetime.now().isoformat(),
                        "cryptocurrency": {
                            "id": "sol",
                            "symbol": "SOL",
                            "name": "Solana",
                            "volatilityTier": "Very High"
                        }
                    }
                ]
            }
            return {"data": {"cryptoPortfolio": crypto_portfolio_response}}
        
        # Handle crypto analytics query
        elif is_crypto_analytics_query:
            print(f"📊 CryptoAnalytics query received")
            # Mock crypto analytics data
            crypto_analytics_response = {
                "totalValueUsd": 125000.0,
                "totalCostBasis": 100000.0,
                "totalPnl": 25000.0,
                "totalPnlPercentage": 25.0,
                "portfolioVolatility": 0.35,
                "sharpeRatio": 1.2,
                "maxDrawdown": -0.15,
                "diversificationScore": 0.75,
                "topHoldingPercentage": 0.35,
                "sectorAllocation": {
                    "Bitcoin": 0.22,
                    "Ethereum": 0.256,
                    "Solana": 0.144,
                    "Other": 0.38
                },
                "bestPerformer": {
                    "symbol": "ETH",
                    "returnPercent": 28.0
                },
                "worstPerformer": {
                    "symbol": "BTC",
                    "returnPercent": 22.2
                },
                "lastUpdated": datetime.now().isoformat()
            }
            return {"data": {"cryptoAnalytics": crypto_analytics_response}}
        
        # Handle crypto ML signal query
        elif is_crypto_ml_signal_query:
            symbol = variables.get("symbol", "BTC").upper()
            print(f"📊 CryptoMLSignal query for {symbol}")
            
            # Mock ML signal data
            confidence_value = 0.85
            # Convert numeric confidence to string level (frontend expects string)
            if confidence_value >= 0.8:
                confidence_level = "HIGH"
            elif confidence_value >= 0.5:
                confidence_level = "MEDIUM"
            else:
                confidence_level = "LOW"
            
            crypto_signal_response = {
                "symbol": symbol,
                "predictionType": "BULLISH",  # BULLISH, BEARISH, NEUTRAL
                "probability": 0.72,
                "confidenceLevel": confidence_level,  # Frontend expects string: "HIGH", "MEDIUM", "LOW"
                "explanation": f"Based on technical analysis, {symbol} shows strong upward momentum with RSI at 58, MACD crossing above signal line, and increasing volume. Market sentiment is positive with 65% bullish indicators.",
                "featuresUsed": ["RSI", "MACD", "Volume", "Price Momentum", "Market Sentiment", "Social Media Activity"],
                "createdAt": datetime.now().isoformat(),
                "expiresAt": (datetime.now() + timedelta(hours=24)).isoformat()
            }
            return {"data": {"cryptoMlSignal": crypto_signal_response}}
        
        # Handle generate ML prediction mutation
        elif is_generate_ml_prediction_mutation:
            symbol = variables.get("symbol", "BTC").upper()
            print(f"🤖 GenerateMLPrediction mutation for {symbol}")
            
            # Mock prediction generation
            prediction_response = {
                "success": True,
                "predictionId": f"pred-{symbol}-{int(datetime.now().timestamp())}",
                "probability": 0.68,  # Probability of price increase
                "confidenceLevel": "HIGH",  # Frontend may also use this in prediction display
                "explanation": f"AI model predicts {symbol} has a 68% probability of price increase over the next 24 hours. Key factors: Positive RSI trend, bullish MACD crossover, strong volume support, and favorable market sentiment.",
                "message": f"Prediction generated successfully for {symbol}"
            }
            return {"data": {"generateMlPrediction": prediction_response}}
        
        # Handle crypto recommendations query
        elif is_crypto_recommendations_query:
            limit = variables.get("limit", 6)
            symbols = variables.get("symbols", [])
            print(f"💡 CryptoRecommendations query: limit={limit}, symbols={symbols}")
            
            # Mock recommendations based on popular cryptocurrencies
            all_cryptos = ["BTC", "ETH", "SOL", "ADA", "DOT", "AVAX", "MATIC", "LINK", "UNI", "ATOM"]
            recommended_symbols = symbols if symbols else all_cryptos[:limit]
            
            recommendations_response = [{
                "symbol": s,
                "score": 0.75 if s in ["BTC", "ETH", "SOL"] else 0.65,
                "probability": 0.72 if s in ["BTC", "ETH", "SOL"] else 0.58,
                # Frontend expects confidenceLevel as string: "HIGH", "MEDIUM", "LOW"
                "confidenceLevel": "HIGH" if s in ["BTC", "ETH", "SOL"] else "MEDIUM",
                "priceUsd": 55000.0 if s == "BTC" else (3200.0 if s == "ETH" else (180.0 if s == "SOL" else 100.0)),
                "volatilityTier": "High",
                "liquidity24hUsd": 5000000000.0 if s == "BTC" else 2000000000.0,
                "rationale": f"Strong technical indicators and positive market momentum for {s}",
                "recommendation": "BUY" if s in ["BTC", "ETH", "SOL"] else "HOLD",
                "riskLevel": "Medium" if s in ["BTC", "ETH"] else "High"
            } for s in recommended_symbols[:limit]]
            
            return {"data": {"cryptoRecommendations": recommendations_response}}
        
        # Handle supported currencies query
        elif is_supported_currencies_query:
            print(f"💰 SupportedCurrencies query received")
            
            # Mock supported cryptocurrencies
            supported_currencies_response = [
                {"id": "btc", "symbol": "BTC", "name": "Bitcoin", "isStakingAvailable": False, "volatilityTier": "High"},
                {"id": "eth", "symbol": "ETH", "name": "Ethereum", "isStakingAvailable": True, "volatilityTier": "High"},
                {"id": "sol", "symbol": "SOL", "name": "Solana", "isStakingAvailable": True, "volatilityTier": "Very High"},
                {"id": "ada", "symbol": "ADA", "name": "Cardano", "isStakingAvailable": True, "volatilityTier": "High"},
                {"id": "dot", "symbol": "DOT", "name": "Polkadot", "isStakingAvailable": True, "volatilityTier": "High"},
                {"id": "avax", "symbol": "AVAX", "name": "Avalanche", "isStakingAvailable": True, "volatilityTier": "High"},
                {"id": "matic", "symbol": "MATIC", "name": "Polygon", "isStakingAvailable": True, "volatilityTier": "Medium"},
                {"id": "link", "symbol": "LINK", "name": "Chainlink", "isStakingAvailable": False, "volatilityTier": "High"},
            ]
            
            return {"data": {"supportedCurrencies": supported_currencies_response}}
        
        # Handle user profile queries (only if not a watchlist query)
        elif is_me_query:
            user_id = "1"  # Default user ID
            
            # Get stored profile or use default
            stored_profile = _mock_user_profile_store.get(user_id, {
                "incomeBracket": "Under $30,000",
                "age": 28,
                "investmentGoals": ["Emergency Fund", "Wealth Building"],
                "riskTolerance": "Moderate",
                "investmentHorizon": "5-10 years"
            })
            
            print(f"👤 Me query - returning profile for user {user_id}: {stored_profile.get('incomeBracket')}, age {stored_profile.get('age')}")
            
            return {
                "data": {
                    "me": {
                        "id": user_id,
                        "name": "Test User",
                        "email": "test@example.com",
                        "hasPremiumAccess": True,
                        "subscriptionTier": "premium",
                        "incomeProfile": stored_profile
                    }
                }
            }
        
        # Handle stock queries
        elif "stocks" in query_str:
            # Fetch real stock data for popular stocks
            popular_symbols = ["AAPL", "MSFT", "GOOGL", "TSLA", "NVDA", "AMZN", "META", "JNJ"]
            stocks_data = []
            
            if _market_data_service:
                # Fetch real prices for all symbols concurrently
                async def fetch_stock_data(symbol: str):
                    try:
                        quote_data = await _market_data_service.get_stock_quote(symbol)
                        metadata = _STOCK_METADATA.get(symbol, {})
                        
                        if quote_data:
                            return {
                                "id": symbol,
                                "symbol": symbol,
                                "companyName": metadata.get("companyName", f"{symbol} Inc."),
                                "sector": metadata.get("sector", "Technology"),
                                "marketCap": metadata.get("marketCap", 1000000000000),
                                "peRatio": metadata.get("peRatio", 25.0),
                                "dividendYield": metadata.get("dividendYield", 0.0),
                                "beginnerFriendlyScore": metadata.get("beginnerFriendlyScore", 75),
                                "currentPrice": quote_data.get('price', 150.0),
                                "change": quote_data.get('change', 0.0),
                                "changePercent": quote_data.get('change_percent', 0.0) / 100 if isinstance(quote_data.get('change_percent'), (int, float)) else 0.0,
                                "__typename": "Stock"
                            }
                        else:
                            # Fallback if API fails
                            return {
                                "id": symbol,
                                "symbol": symbol,
                                "companyName": metadata.get("companyName", f"{symbol} Inc."),
                                "sector": metadata.get("sector", "Technology"),
                                "marketCap": metadata.get("marketCap", 1000000000000),
                                "peRatio": metadata.get("peRatio", 25.0),
                                "dividendYield": metadata.get("dividendYield", 0.0),
                                "beginnerFriendlyScore": metadata.get("beginnerFriendlyScore", 75),
                                "currentPrice": metadata.get("currentPrice", 150.0),
                                "change": 0.0,
                                "changePercent": 0.0,
                                "__typename": "Stock"
                            }
                    except Exception as e:
                        print(f"⚠️ Error fetching real data for {symbol}: {e}")
                        # Return fallback data
                        metadata = _STOCK_METADATA.get(symbol, {})
                        return {
                            "id": symbol,
                            "symbol": symbol,
                            "companyName": metadata.get("companyName", f"{symbol} Inc."),
                            "sector": metadata.get("sector", "Technology"),
                            "marketCap": metadata.get("marketCap", 1000000000000),
                            "peRatio": metadata.get("peRatio", 25.0),
                            "dividendYield": metadata.get("dividendYield", 0.0),
                            "beginnerFriendlyScore": metadata.get("beginnerFriendlyScore", 75),
                            "currentPrice": metadata.get("currentPrice", 150.0),
                            "change": 0.0,
                            "changePercent": 0.0,
                            "__typename": "Stock"
                        }
                
                # Fetch all stocks concurrently
                tasks = [fetch_stock_data(symbol) for symbol in popular_symbols]
                stocks_data = await asyncio.gather(*tasks)
            else:
                # Fallback to static data if service not available
                stocks_data = [
                {
                    "id": "AAPL",
                    "symbol": "AAPL",
                    "companyName": "Apple Inc.",
                    "sector": "Technology",
                    "marketCap": 2900000000000,
                    "peRatio": 28.5,
                    "dividendYield": 0.0044,
                    "beginnerFriendlyScore": 85,
                    "currentPrice": 189.0,
                    "change": 9.0,
                    "changePercent": 0.05,
                    "__typename": "Stock"
                },
                {
                    "id": "MSFT",
                    "symbol": "MSFT",
                    "companyName": "Microsoft Corporation",
                    "sector": "Technology",
                    "marketCap": 3200000000000,
                    "peRatio": 32.0,
                    "dividendYield": 0.007,
                    "beginnerFriendlyScore": 88,
                    "currentPrice": 420.0,
                    "change": 15.0,
                    "changePercent": 0.037,
                    "__typename": "Stock"
                },
                {
                    "id": "GOOGL",
                    "symbol": "GOOGL",
                    "companyName": "Alphabet Inc.",
                    "sector": "Technology",
                    "marketCap": 1800000000000,
                    "peRatio": 24.0,
                    "dividendYield": 0.0,
                    "beginnerFriendlyScore": 82,
                    "currentPrice": 145.0,
                    "change": 2.5,
                    "changePercent": 0.018,
                    "__typename": "Stock"
                },
                {
                    "id": "TSLA",
                    "symbol": "TSLA",
                    "companyName": "Tesla Inc.",
                    "sector": "Consumer Cyclical",
                    "marketCap": 780000000000,
                    "peRatio": 65.0,
                    "dividendYield": 0.0,
                    "beginnerFriendlyScore": 72,
                    "currentPrice": 245.0,
                    "change": -12.0,
                    "changePercent": -0.047,
                    "__typename": "Stock"
                },
                {
                    "id": "NVDA",
                    "symbol": "NVDA",
                    "companyName": "NVIDIA Corporation",
                    "sector": "Technology",
                    "marketCap": 1200000000000,
                    "peRatio": 45.0,
                    "dividendYield": 0.0003,
                    "beginnerFriendlyScore": 78,
                    "currentPrice": 495.0,
                    "change": 25.0,
                    "changePercent": 0.053,
                    "__typename": "Stock"
                },
                {
                    "id": "AMZN",
                    "symbol": "AMZN",
                    "companyName": "Amazon.com Inc.",
                    "sector": "Consumer Cyclical",
                    "marketCap": 1500000000000,
                    "peRatio": 42.0,
                    "dividendYield": 0.0,
                    "beginnerFriendlyScore": 80,
                    "currentPrice": 150.0,
                    "change": 3.0,
                    "changePercent": 0.02,
                    "__typename": "Stock"
                },
                {
                    "id": "META",
                    "symbol": "META",
                    "companyName": "Meta Platforms Inc.",
                    "sector": "Technology",
                    "marketCap": 850000000000,
                    "peRatio": 22.0,
                    "dividendYield": 0.0,
                    "beginnerFriendlyScore": 75,
                    "currentPrice": 340.0,
                    "change": 8.0,
                    "changePercent": 0.024,
                    "__typename": "Stock"
                },
                    {
                        "id": "JNJ",
                        "symbol": "JNJ",
                        "companyName": "Johnson & Johnson",
                        "sector": "Healthcare",
                        "marketCap": 420000000000,
                        "peRatio": 28.0,
                        "dividendYield": 0.026,
                        "beginnerFriendlyScore": 92,
                        "currentPrice": 165.0,
                        "change": 1.5,
                        "changePercent": 0.009,
                        "__typename": "Stock"
                    }
                ]
            
            print(f"📊 Returning {len(stocks_data)} stocks ({'REAL DATA' if _market_data_service else 'FALLBACK DATA'})")
            return {
                "data": {
                    "stocks": stocks_data
                }
            }
        
        # Handle aiRecommendations query (comprehensive portfolio analysis)
        # Must come before other queries but after mutations
        elif is_ai_recommendations_query:
            print(f"🤖 AIRecommendations query received - Using REAL ML Implementation")
            
            # Get profile from variables or fallback to stored profile
            profile_var = variables.get("profile", {})
            using_defaults = variables.get("usingDefaults", False)
            
            # Get user profile to personalize recommendations
            user_id = "1"
            stored_profile = _mock_user_profile_store.get(user_id, {})
            
            # Use variables if provided, otherwise use stored profile, otherwise use defaults
            risk_tolerance = (
                profile_var.get("riskTolerance") or 
                stored_profile.get("riskTolerance") or 
                "Moderate"
            )
            investment_horizon_str = (
                stored_profile.get("investmentHorizon") or 
                "5-10 years"
            )
            
            # Map investment horizon years back to string for display (if needed)
            horizon_years = profile_var.get("investmentHorizonYears") or 5
            if not stored_profile.get("investmentHorizon"):
                # Map years to string format
                if horizon_years >= 12:
                    investment_horizon_str = "10+ years"
                elif horizon_years >= 8:
                    investment_horizon_str = "5-10 years"
                elif horizon_years >= 4:
                    investment_horizon_str = "3-5 years"
                elif horizon_years >= 2:
                    investment_horizon_str = "1-3 years"
                else:
                    investment_horizon_str = "1-3 years"
            
            print(f"   Profile from variables: {bool(profile_var)}, usingDefaults: {using_defaults}, risk: {risk_tolerance}, horizon: {investment_horizon_str}")
            
            # Use REAL ML implementation instead of mock data
            try:
                # Import the real ML services
                import sys
                import os
                sys.path.append(os.path.join(os.path.dirname(__file__), 'backend', 'backend'))
                
                # Set up Django environment for ML services
                os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'richesreach.settings')
                import django
                django.setup()
                
                from backend.core.ml_stock_recommender import MLStockRecommender
                from backend.core.models import User, IncomeProfile
                
                # Get or create a user for ML recommendations
                user, created = User.objects.get_or_create(
                    id=1,
                    defaults={
                        'username': 'mobile_user',
                        'email': 'mobile@richesreach.com',
                        'first_name': 'Mobile',
                        'last_name': 'User'
                    }
                )
                
                # Get or create income profile
                income_profile, profile_created = IncomeProfile.objects.get_or_create(
                    user=user,
                    defaults={
                        'age': profile_var.get("age", 30),
                        'income_bracket': profile_var.get("incomeBracket", "Unknown"),
                        'investment_goals': profile_var.get("investmentGoals", []),
                        'risk_tolerance': risk_tolerance,
                        'investment_horizon': investment_horizon_str
                    }
                )
                
                # Update profile if variables provided
                if profile_var:
                    income_profile.age = profile_var.get("age", income_profile.age)
                    income_profile.income_bracket = profile_var.get("incomeBracket", income_profile.income_bracket)
                    income_profile.investment_goals = profile_var.get("investmentGoals", income_profile.investment_goals)
                    income_profile.risk_tolerance = risk_tolerance
                    income_profile.investment_horizon = investment_horizon_str
                    income_profile.save()
                
                print(f"   Using ML recommender for user: {user.username}, profile: {income_profile.risk_tolerance}")
                
                # Generate REAL ML recommendations
                ml_recommender = MLStockRecommender()
                ml_recommendations = ml_recommender.generate_ml_recommendations(user, limit=8)
                
                # Convert ML recommendations to GraphQL format
                buy_recommendations = []
                for rec in ml_recommendations:
                    buy_recommendations.append({
                        "symbol": rec.stock.symbol,
                        "companyName": rec.stock.company_name,
                        "recommendation": "BUY",
                        "confidence": rec.confidence,
                        "reasoning": rec.reasoning,
                        "targetPrice": round(rec.target_price, 2),
                        "currentPrice": round(rec.current_price, 2),
                        "expectedReturn": rec.expected_return,
                        "allocation": 12.5  # Equal allocation for now
                    })
                
                print(f"   Generated {len(buy_recommendations)} REAL ML recommendations")
                
            except Exception as e:
                print(f"   ⚠️ ML implementation failed: {e}")
                print(f"   Falling back to enhanced mock data...")
                
                # Fallback to enhanced mock data with real prices
                popular_symbols = ["AAPL", "MSFT", "GOOGL", "JNJ", "V", "MA", "PG", "DIS"]
                buy_recommendations = []
            
            async def fetch_stock_for_recommendation(symbol: str):
                try:
                    quote_data = None
                    if _market_data_service:
                        quote_data = await _market_data_service.get_stock_quote(symbol)
                    
                    metadata = _STOCK_METADATA.get(symbol, {})
                    current_price = quote_data.get("price", metadata.get("currentPrice", 150.0)) if quote_data else metadata.get("currentPrice", 150.0)
                    target_price = current_price * 1.15  # 15% upside target
                    expected_return = 0.15
                    
                    # Adjust confidence based on risk tolerance and stock characteristics
                    base_confidence = 0.75
                    if risk_tolerance == "Conservative":
                        # Prefer dividend-paying, stable stocks
                        if metadata.get("dividendYield", 0) > 0.01:
                            base_confidence = 0.85
                    elif risk_tolerance == "Aggressive":
                        # Favor growth stocks
                        if metadata.get("peRatio", 0) > 40:
                            base_confidence = 0.80
                    
                    return {
                        "symbol": symbol,
                        "companyName": metadata.get("companyName", f"{symbol} Inc."),
                        "recommendation": "BUY",
                        "confidence": base_confidence,
                        "reasoning": f"Strong fundamentals, favorable sector trends, and alignment with {risk_tolerance.lower()} risk profile.",
                        "targetPrice": round(target_price, 2),
                        "currentPrice": round(current_price, 2),
                        "expectedReturn": expected_return,
                        "allocation": 12.5  # Equal allocation for demo
                    }
                except Exception as e:
                    print(f"⚠️ Error fetching {symbol} for recommendation: {e}")
                    return None
            
            # Fetch stock data concurrently
            stock_tasks = [fetch_stock_for_recommendation(s) for s in popular_symbols[:8]]
            stock_results = await asyncio.gather(*stock_tasks)
            buy_recommendations = [r for r in stock_results if r is not None]
            
            # If no real data available, use fallback
            if not buy_recommendations:
                buy_recommendations = [
                    {
                        "symbol": "AAPL",
                        "companyName": "Apple Inc.",
                        "recommendation": "BUY",
                        "confidence": 0.85,
                        "reasoning": "Strong earnings growth and market leadership in technology",
                        "targetPrice": 190.0,
                        "currentPrice": 268.64,
                        "expectedReturn": 0.15,
                        "allocation": 15.0
                    },
                    {
                        "symbol": "MSFT",
                        "companyName": "Microsoft Corporation",
                        "recommendation": "BUY",
                        "confidence": 0.82,
                        "reasoning": "Cloud services growth and AI integration",
                        "targetPrice": 450.0,
                        "currentPrice": 538.73,
                        "expectedReturn": 0.12,
                        "allocation": 12.0
                    },
                    {
                        "symbol": "JNJ",
                        "companyName": "Johnson & Johnson",
                        "recommendation": "BUY",
                        "confidence": 0.90,
                        "reasoning": "Stable dividend yield and healthcare diversification",
                        "targetPrice": 175.0,
                        "currentPrice": 165.0,
                        "expectedReturn": 0.08,
                        "allocation": 10.0
                    },
                    {
                        "symbol": "V",
                        "companyName": "Visa Inc.",
                        "recommendation": "BUY",
                        "confidence": 0.88,
                        "reasoning": "Payment processing growth and global expansion",
                        "targetPrice": 320.0,
                        "currentPrice": 280.0,
                        "expectedReturn": 0.14,
                        "allocation": 11.0
                    },
                    {
                        "symbol": "PG",
                        "companyName": "Procter & Gamble",
                        "recommendation": "BUY",
                        "confidence": 0.83,
                        "reasoning": "Consumer staples stability and dividend growth",
                        "targetPrice": 170.0,
                        "currentPrice": 155.0,
                        "expectedReturn": 0.09,
                        "allocation": 8.0
                    }
                ]
            
            # Calculate total portfolio value
            total_value = sum(rec.get("currentPrice", 0) * 100 * (rec.get("allocation", 0) / 100) for rec in buy_recommendations) * 10
            
            ai_recommendations_response = {
                "portfolioAnalysis": {
                    "totalValue": total_value,
                    "numHoldings": len(buy_recommendations),
                    "sectorBreakdown": {
                        "Technology": 0.40,
                        "Healthcare": 0.20,
                        "Financials": 0.15,
                        "Consumer Staples": 0.15,
                        "Other": 0.10
                    },
                    "riskScore": 0.65 if risk_tolerance == "Moderate" else (0.45 if risk_tolerance == "Conservative" else 0.80),
                    "diversificationScore": 0.75,
                    "expectedImpact": {
                        "evPct": 12.5,  # Expected value percentage
                        "evAbs": total_value * 0.125,  # Expected value absolute
                        "per10k": 1250.0  # Per 10k investment
                    },
                    "risk": {
                        "volatilityEstimate": 15.0 if risk_tolerance == "Moderate" else (10.0 if risk_tolerance == "Conservative" else 20.0),
                        "maxDrawdownPct": -25.0
                    },
                    "assetAllocation": {
                        "stocks": 0.90,
                        "bonds": 0.08,
                        "cash": 0.02
                    }
                },
                "buyRecommendations": buy_recommendations,
                "sellRecommendations": [
                    {
                        "symbol": "TSLA",
                        "reasoning": "High volatility may not align with current risk profile"
                    }
                ],
                "rebalanceSuggestions": [
                    {
                        "action": "REDUCE",
                        "currentAllocation": 0.25,
                        "suggestedAllocation": 0.15,
                        "reasoning": "Reduce single-stock concentration",
                        "priority": "HIGH"
                    }
                ],
                "riskAssessment": {
                    "overallRisk": "Moderate" if risk_tolerance == "Moderate" else ("Low" if risk_tolerance == "Conservative" else "High"),
                    "volatilityEstimate": 15.0,
                    "recommendations": [
                        "Maintain diversified portfolio across sectors",
                        "Rebalance quarterly to maintain target allocation",
                        "Consider adding bonds for risk reduction if conservative"
                    ]
                },
                "marketOutlook": {
                    "overallSentiment": "Bullish",
                    "confidence": 0.72,
                    "keyFactors": [
                        "Positive earnings trends in technology sector",
                        "Strong consumer spending indicators",
                        "Moderate inflation expectations",
                        "Stable interest rate environment"
                    ]
                }
            }
            
            print(f"✅ Returning {len(buy_recommendations)} buy recommendations")
            return {"data": {"aiRecommendations": ai_recommendations_response}}
        
        # Handle portfolioMetrics query
        is_portfolio_metrics_query = (
            operation_name == "GetPortfolioMetrics" or
            "portfolioMetrics" in query_str
        )
        
        if is_portfolio_metrics_query:
            print(f"📊 PortfolioMetrics query received")
            # Try to fetch real portfolio data from Django
            try:
                _setup_django_once()
                from core.models import Portfolio, PortfolioPosition, Stock
                from django.contrib.auth import get_user_model
                User = get_user_model()
                
                # Get default user
                user, _ = User.objects.get_or_create(
                    id=1,
                    defaults={'username': 'mobile_user', 'email': 'mobile@richesreach.com'}
                )
                
                # Get all portfolios for user
                portfolios = Portfolio.objects.filter(user=user)
                total_value = 0
                total_cost = 0
                holdings_list = []
                
                for portfolio in portfolios:
                    positions = PortfolioPosition.objects.filter(portfolio=portfolio)
                    for position in positions:
                        stock = position.stock
                        current_price = stock.current_price or 150.0
                        shares = position.shares or 0
                        cost_basis = position.average_price or current_price
                        
                        position_value = current_price * shares
                        position_cost = cost_basis * shares
                        return_amount = position_value - position_cost
                        return_percent = (return_amount / position_cost * 100) if position_cost > 0 else 0
                        
                        total_value += position_value
                        total_cost += position_cost
                        
                        holdings_list.append({
                            "symbol": stock.symbol,
                            "companyName": stock.company_name or f"{stock.symbol} Inc.",
                            "shares": shares,
                            "currentPrice": round(current_price, 2),
                            "totalValue": round(position_value, 2),
                            "costBasis": round(position_cost, 2),
                            "returnAmount": round(return_amount, 2),
                            "returnPercent": round(return_percent, 2),
                            "sector": getattr(stock, 'sector', 'Technology')
                        })
                
                total_return = total_value - total_cost
                total_return_percent = (total_return / total_cost * 100) if total_cost > 0 else 0
                
                portfolio_metrics_response = {
                    "totalValue": round(total_value, 2),
                    "totalCost": round(total_cost, 2),
                    "totalReturn": round(total_return, 2),
                    "totalReturnPercent": round(total_return_percent, 2),
                    "dayChange": 0.0,  # Would need to calculate from previous day
                    "dayChangePercent": 0.0,
                    "volatility": 15.0,  # Would need to calculate
                    "sharpeRatio": 1.2,  # Would need to calculate
                    "maxDrawdown": -5.0,  # Would need to calculate
                    "beta": 1.0,  # Would need to calculate
                    "alpha": 0.0,  # Would need to calculate
                    "sectorAllocation": {},  # Would need to calculate
                    "riskMetrics": {},  # Would need to calculate
                    "holdings": holdings_list
                }
                
                print(f"✅ Returning portfolio metrics with {len(holdings_list)} holdings")
                return {"data": {"portfolioMetrics": portfolio_metrics_response}}
                
            except Exception as e:
                print(f"⚠️ Error fetching real portfolio data: {e}")
                # Fallback to mock data
                portfolio_metrics_response = {
                    "totalValue": 14303.52,
                    "totalCost": 12000.0,
                    "totalReturn": 2303.52,
                    "totalReturnPercent": 19.2,
                    "dayChange": 125.50,
                    "dayChangePercent": 0.88,
                    "volatility": 15.8,
                    "sharpeRatio": 1.4,
                    "maxDrawdown": -5.2,
                    "beta": 1.0,
                    "alpha": 2.5,
                    "sectorAllocation": {"Technology": 0.6, "Healthcare": 0.3, "Finance": 0.1},
                    "riskMetrics": {"overallRisk": "Moderate"},
                    "holdings": [
                        {
                            "symbol": "AAPL",
                            "companyName": "Apple Inc.",
                            "shares": 10,
                            "currentPrice": 180.0,
                            "totalValue": 1800.0,
                            "costBasis": 1500.0,
                            "returnAmount": 300.0,
                            "returnPercent": 20.0,
                            "sector": "Technology"
                        },
                        {
                            "symbol": "MSFT",
                            "companyName": "Microsoft Corporation",
                            "shares": 8,
                            "currentPrice": 320.0,
                            "totalValue": 2560.0,
                            "costBasis": 2400.0,
                            "returnAmount": 160.0,
                            "returnPercent": 6.67,
                            "sector": "Technology"
                        },
                        {
                            "symbol": "SPY",
                            "companyName": "SPDR S&P 500 ETF",
                            "shares": 15,
                            "currentPrice": 420.0,
                            "totalValue": 6300.0,
                            "costBasis": 6000.0,
                            "returnAmount": 300.0,
                            "returnPercent": 5.0,
                            "sector": "Finance"
                        }
                    ]
                }
                return {"data": {"portfolioMetrics": portfolio_metrics_response}}
        
        # Handle myPortfolios query
        is_my_portfolios_query = (
            operation_name == "GetMyPortfolios" or
            "myPortfolios" in query_str
        )
        
        if is_my_portfolios_query:
            print(f"📊 MyPortfolios query received")
            # Try to fetch real portfolio data from Django
            try:
                _setup_django_once()
                from core.models import Portfolio, PortfolioPosition, Stock
                from django.contrib.auth import get_user_model
                User = get_user_model()
                
                # Get default user
                user, _ = User.objects.get_or_create(
                    id=1,
                    defaults={'username': 'mobile_user', 'email': 'mobile@richesreach.com'}
                )
                
                # Get all portfolios for user
                portfolios = Portfolio.objects.filter(user=user)
                portfolios_list = []
                total_value = 0
                
                for portfolio in portfolios:
                    positions = PortfolioPosition.objects.filter(portfolio=portfolio)
                    holdings_list = []
                    portfolio_value = 0
                    
                    for position in positions:
                        stock = position.stock
                        current_price = stock.current_price or 150.0
                        shares = position.shares or 0
                        position_value = current_price * shares
                        portfolio_value += position_value
                        
                        holdings_list.append({
                            "id": str(position.id),
                            "stock": {
                                "symbol": stock.symbol
                            },
                            "shares": shares,
                            "averagePrice": round(position.average_price or current_price, 2),
                            "currentPrice": round(current_price, 2),
                            "totalValue": round(position_value, 2)
                        })
                    
                    total_value += portfolio_value
                    portfolios_list.append({
                        "name": portfolio.name,
                        "totalValue": round(portfolio_value, 2),
                        "holdingsCount": len(holdings_list),
                        "holdings": holdings_list
                    })
                
                my_portfolios_response = {
                    "totalPortfolios": len(portfolios_list),
                    "totalValue": round(total_value, 2),
                    "portfolios": portfolios_list
                }
                
                print(f"✅ Returning {len(portfolios_list)} portfolios with total value {total_value}")
                return {"data": {"myPortfolios": my_portfolios_response}}
                
            except Exception as e:
                print(f"⚠️ Error fetching real portfolio data: {e}")
                # Fallback to mock data
                my_portfolios_response = {
                    "totalPortfolios": 1,
                    "totalValue": 14303.52,
                    "portfolios": [
                        {
                            "name": "Main Portfolio",
                            "totalValue": 14303.52,
                            "holdingsCount": 3,
                            "holdings": [
                                {
                                    "id": "1",
                                    "stock": {"symbol": "AAPL"},
                                    "shares": 10,
                                    "averagePrice": 150.0,
                                    "currentPrice": 180.0,
                                    "totalValue": 1800.0
                                },
                                {
                                    "id": "2",
                                    "stock": {"symbol": "MSFT"},
                                    "shares": 8,
                                    "averagePrice": 230.0,
                                    "currentPrice": 320.0,
                                    "totalValue": 2560.0
                                },
                                {
                                    "id": "3",
                                    "stock": {"symbol": "SPY"},
                                    "shares": 15,
                                    "averagePrice": 380.0,
                                    "currentPrice": 420.0,
                                    "totalValue": 6300.0
                                }
                            ]
                        }
                    ]
                }
                return {"data": {"myPortfolios": my_portfolios_response}}
        
        # Default response for any other GraphQL query
        return {
            "data": {},
            "errors": []
        }
        
    except Exception as e:
        print(f"GraphQL Error: {e}")
        # Return empty data object instead of null to prevent UI errors
        return {
            "data": {},
            "errors": [{"message": str(e)}]
        }

if __name__ == "__main__":
    print("🚀 Starting RichesReach Main Server...")
    print("📡 Available endpoints:")
    print("   • GET /health - Health check")
    print("   • GET /api/market/quotes - Market quotes")
    print("   • POST /api/pump-fun/launch - Meme launch")
    print("   • GET /api/trading/quote/{symbol} - Trading quotes")
    print("   • GET /api/portfolio/recommendations - Portfolio recommendations")
    print("   • POST /api/kyc/workflow - KYC workflow")
    print("   • POST /api/alpaca/account - Alpaca account")
    print("   • POST /digest/daily - Daily Voice Digest")
    print("   • POST /digest/regime-alert - Regime Change Alert")
    print("   • POST /graphql/ - GraphQL endpoint")
    print("")
    print("🌐 Server running on http://localhost:8000")
    print("📊 GraphQL Playground: http://localhost:8000/graphql")
    print("❤️  Health Check: http://localhost:8000/health")
    print("")
    print("Press Ctrl+C to stop the server")
    
    uvicorn.run(app, host="0.0.0.0", port=8000)
