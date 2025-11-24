#!/usr/bin/env python3
"""
RichesReach AI Service - Production Main Application
"""
from fastapi import FastAPI, HTTPException, BackgroundTasks, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import uvicorn
import os
import logging
from datetime import datetime
import asyncio
import sys
import django
import json
from asgiref.sync import sync_to_async
from starlette.requests import Request as StarletteRequest
from starlette.responses import Response as StarletteResponse

# Setup Django to access models
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'richesreach.settings')
try:
    django.setup()
    from django.contrib.auth import get_user_model
    from django.contrib.auth.hashers import check_password
    try:
        from graphql_jwt.shortcuts import get_token
        GRAPHQL_JWT_AVAILABLE = True
    except ImportError:
        GRAPHQL_JWT_AVAILABLE = False
    # Import GraphQL schema and view
    try:
        from core.schema import schema
        from core.views import graphql_view
        GRAPHQL_AVAILABLE = True
    except Exception as e:
        logging.warning(f"GraphQL not available: {e}")
        GRAPHQL_AVAILABLE = False
        schema = None
        graphql_view = None
    DJANGO_AVAILABLE = True
except Exception as e:
    logging.warning(f"Django not available: {e}")
    DJANGO_AVAILABLE = False
    GRAPHQL_AVAILABLE = False
    schema = None
    graphql_view = None

# Import our AI services
try:
    from core.optimized_ml_service import OptimizedMLService
    from core.market_data_service import MarketDataService
    from core.advanced_market_data_service import AdvancedMarketDataService
    from core.advanced_ml_algorithms import AdvancedMLAlgorithms
    from core.performance_monitoring_service import ProductionMonitoringService
    ML_SERVICES_AVAILABLE = True
except (ImportError, SyntaxError, IndentationError) as e:
    ML_SERVICES_AVAILABLE = False
    logging.warning(f"ML services not available - running in basic mode: {e}")

# Import AI Options API separately (always available)
try:
    from core.ai_options_api import router as ai_options_router
    AI_OPTIONS_AVAILABLE = True
except ImportError as e:
    AI_OPTIONS_AVAILABLE = False
    logging.warning(f"AI Options API not available: {e}")

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="RichesReach AI Service",
    description="Production AI-powered investment portfolio analysis and market intelligence",
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

# Include AI Options router
if AI_OPTIONS_AVAILABLE:
    app.include_router(ai_options_router)

# Tax Optimization endpoints
@app.get("/api/tax/optimization-summary")
async def get_tax_optimization_summary(request: Request):
    """
    Get tax optimization summary with portfolio holdings for tax analysis.
    Returns holdings data needed for tax loss harvesting, capital gains analysis, etc.
    """
    if not DJANGO_AVAILABLE:
        raise HTTPException(status_code=503, detail="Tax optimization service not available")
    
    try:
        # Extract token from Authorization header (supports both Token and Bearer)
        auth_header = request.headers.get("Authorization", "")
        token = None
        if auth_header.startswith("Token "):
            token = auth_header.replace("Token ", "")
        elif auth_header.startswith("Bearer "):
            token = auth_header.replace("Bearer ", "")
        
        # Get user - try to validate JWT token if available, otherwise use demo user
        User = get_user_model()
        user = None
        
        if token and GRAPHQL_JWT_AVAILABLE:
            try:
                from graphql_jwt.shortcuts import get_user_by_token
                # Try to get user from JWT token
                user = await sync_to_async(get_user_by_token)(token)
            except Exception as e:
                logger.debug(f"JWT token validation failed: {e}")
        
        # Fallback: get user from email or use demo user
        if not user:
            try:
                # Try to get demo user or first user
                user = await sync_to_async(User.objects.filter(email='demo@example.com').first)()
                if not user:
                    user = await sync_to_async(User.objects.first)()
                if not user:
                    # Create demo user if none exists
                    user, _ = await sync_to_async(User.objects.get_or_create)(
                        email='demo@example.com',
                        defaults={'name': 'Demo User'}
                    )
            except Exception as e:
                logger.warning(f"Error getting user: {e}")
                raise HTTPException(status_code=401, detail="Invalid authentication")
        
        # Get portfolio holdings using PremiumAnalyticsService
        from core.premium_analytics import PremiumAnalyticsService
        service = PremiumAnalyticsService()
        metrics = await sync_to_async(service.get_portfolio_performance_metrics)(user.id)
        
        # Format holdings for tax optimization
        holdings = []
        if metrics and metrics.get('holdings'):
            for holding in metrics['holdings']:
                holdings.append({
                    'symbol': holding.get('symbol', ''),
                    'companyName': holding.get('company_name', holding.get('name', '')),
                    'shares': holding.get('shares', 0),
                    'currentPrice': float(holding.get('current_price', 0) or 0),
                    'costBasis': float(holding.get('cost_basis', holding.get('average_price', 0)) or 0),
                    'totalValue': float(holding.get('total_value', 0) or 0),
                    'returnAmount': float(holding.get('return_amount', 0) or 0),
                    'returnPercent': float(holding.get('return_percent', 0) or 0),
                    'sector': holding.get('sector', 'Unknown'),
                })
        
        # If no holdings from metrics, try to get from Portfolio model directly
        if not holdings:
            from core.models import Portfolio, Stock
            portfolio_holdings = await sync_to_async(list)(
                Portfolio.objects.filter(user=user).select_related('stock')[:20]
            )
            
            for ph in portfolio_holdings:
                stock = ph.stock
                current_price = float(ph.current_price or (stock.current_price if stock else 0) or 0)
                cost_basis = float(ph.average_price or 0)
                shares = ph.shares or 0
                total_value = float(ph.total_value or (current_price * shares) if current_price and shares else 0)
                return_amount = float((current_price - cost_basis) * shares if current_price and cost_basis and shares else 0)
                return_percent = float(((current_price - cost_basis) / cost_basis * 100) if cost_basis and current_price else 0)
                
                holdings.append({
                    'symbol': stock.symbol if stock else '',
                    'companyName': stock.company_name if stock else '',
                    'shares': shares,
                    'currentPrice': current_price,
                    'costBasis': cost_basis,
                    'totalValue': total_value,
                    'returnAmount': return_amount,
                    'returnPercent': return_percent,
                    'sector': stock.sector if stock else 'Unknown',
                })
        
        return {
            'holdings': holdings,
            'totalPortfolioValue': metrics.get('total_value', 0) if metrics else 0,
            'totalUnrealizedGains': metrics.get('total_return', 0) if metrics else 0,
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in tax optimization summary: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error fetching tax optimization data: {str(e)}")

# Initialize services
if ML_SERVICES_AVAILABLE:
    try:
        ml_service = OptimizedMLService()
        market_data_service = AdvancedMarketDataService()
        advanced_ml = AdvancedMLAlgorithms()
        monitoring_service = ProductionMonitoringService()
        logger.info("All ML services initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize ML services: {e}")
        ML_SERVICES_AVAILABLE = False

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "RichesReach AI Service",
        "version": "1.0.0",
        "status": "running",
        "timestamp": datetime.now().isoformat(),
        "ml_services": ML_SERVICES_AVAILABLE
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    health_status = {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "services": {
            "ml_services": ML_SERVICES_AVAILABLE,
            "market_data": ML_SERVICES_AVAILABLE,
            "monitoring": ML_SERVICES_AVAILABLE
        }
    }
    if ML_SERVICES_AVAILABLE:
        try:
            # Test ML service health
            ml_health = ml_service.check_health()
            health_status["services"]["ml_health"] = ml_health
            # Test market data service
            market_health = market_data_service.check_health()
            health_status["services"]["market_health"] = market_health
        except Exception as e:
            health_status["status"] = "degraded"
            health_status["error"] = str(e)
    return health_status

@app.post("/api/portfolio/analyze")
async def analyze_portfolio(background_tasks: BackgroundTasks):
    """Analyze investment portfolio using AI"""
    if not ML_SERVICES_AVAILABLE:
        raise HTTPException(status_code=503, detail="ML services not available")
    try:
        # Record metric
        if 'monitoring_service' in locals():
            monitoring_service.record_metric(
                "portfolio_analysis_requests", 1, "count"
            )
        # Run portfolio analysis in background
        background_tasks.add_task(run_portfolio_analysis)
        return {
            "message": "Portfolio analysis started",
            "status": "processing",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Portfolio analysis error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/market/regime")
async def predict_market_regime(background_tasks: BackgroundTasks):
    """Predict current market regime using AI"""
    if not ML_SERVICES_AVAILABLE:
        raise HTTPException(status_code=503, detail="ML services not available")
    try:
        # Record metric
        if 'monitoring_service' in locals():
            monitoring_service.record_metric(
                "market_regime_requests", 1, "count"
            )
        # Run market regime prediction in background
        background_tasks.add_task(run_market_regime_prediction)
        return {
            "message": "Market regime prediction started",
            "status": "processing",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Market regime prediction error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/status")
async def get_service_status():
    """Get comprehensive service status"""
    status = {
        "service": "RichesReach AI",
        "version": "1.0.0",
        "status": "running",
        "timestamp": datetime.now().isoformat(),
        "environment": os.getenv("ENVIRONMENT", "production"),
        "ml_services": ML_SERVICES_AVAILABLE
    }
    if ML_SERVICES_AVAILABLE:
        try:
            # Get ML model status
            ml_status = ml_service.get_status()
            status["ml_status"] = ml_status
            # Get market data status
            market_status = market_data_service.get_status()
            status["market_status"] = market_status
        except Exception as e:
            status["error"] = str(e)
    return status

# Authentication models
class LoginRequest(BaseModel):
    email: str = None
    username: str = None
    password: str
    
    class Config:
        # Allow both email and username fields
        extra = "allow"

def _authenticate_user_sync(email: str, password: str):
    """Synchronous Django authentication helper"""
    User = get_user_model()
    user = None
    
    # Method 1: Try Django's authenticate
    try:
        from django.contrib.auth import authenticate
        user = authenticate(username=email, password=password)
    except Exception as e:
        logger.warning(f"Authenticate failed: {e}")
    
    # Method 2: Manual authentication if Django auth fails
    if not user:
        try:
            user = User.objects.get(email=email)
            logger.info(f"Found user: {user.email}, checking password...")
            if not user.check_password(password):
                logger.warning(f"Invalid password for {email}")
                user = None
            else:
                logger.info(f"Manual authentication successful for {email}")
        except User.DoesNotExist:
            logger.warning(f"User not found: {email}")
            user = None
        except Exception as e:
            logger.error(f"Error during manual auth: {e}", exc_info=True)
            user = None
    
    # Method 3: Development fallback - create/get demo user
    if not user:
        logger.info("Authentication failed, checking for demo user...")
        try:
            if email.lower() == 'demo@example.com':
                user, created = User.objects.get_or_create(
                    email='demo@example.com',
                    defaults={'name': 'Demo User'}
                )
                if created:
                    user.set_password('demo123')
                    user.save()
                    logger.info("Created demo user for development")
                else:
                    if not user.check_password('demo123'):
                        user.set_password('demo123')
                        user.save()
                        logger.info("Reset demo user password")
                logger.info("Using demo user for development (dev mode)")
            else:
                user = None
        except Exception as e:
            logger.error(f"Error creating demo user: {e}")
            user = None
    
    return user

@app.post("/api/auth/login/")
async def login(request: LoginRequest):
    """REST API Login Endpoint
    
    Accepts either email or username in the request body:
    {
        "email": "user@example.com",
        "password": "password123"
    }
    or
    {
        "username": "user@example.com",
        "password": "password123"
    }
    """
    if not DJANGO_AVAILABLE:
        raise HTTPException(status_code=503, detail="Authentication service not available")
    
    try:
        # Handle both email and username fields
        email = (request.email or request.username or "").strip()
        password = request.password
        
        if not email or not password:
            raise HTTPException(status_code=400, detail="Email/username and password are required")
        
        logger.info(f"Login attempt for email: {email}")
        
        # Run Django operations in sync context
        user = await sync_to_async(_authenticate_user_sync)(email, password)
        
        if not user:
            raise HTTPException(status_code=401, detail="Invalid email or password")
        
        # Generate token (also needs to be sync)
        def _generate_token_sync(user):
            token = None
            if GRAPHQL_JWT_AVAILABLE:
                try:
                    token = get_token(user)
                    logger.info(f"Generated JWT token for {email}")
                except Exception as e:
                    logger.warning(f"Failed to generate JWT token: {e}")
            
            # Fallback to dev token if JWT not available
            if not token:
                import time
                token = f"dev-token-{int(time.time())}"
                logger.info(f"Using dev token for {email}")
            return token
        
        token = await sync_to_async(_generate_token_sync)(user)
        
        # Prepare user data
        user_data = {
            'id': str(user.id),
            'email': user.email,
            'name': getattr(user, 'name', ''),
        }
        
        # Add optional fields if they exist
        if hasattr(user, 'profile_pic') and user.profile_pic:
            user_data['profile_pic'] = user.profile_pic
        
        response_data = {
            'access_token': token,
            'token': token,  # Alias for compatibility
            'user': user_data,
        }
        
        logger.info(f"✅ Login successful for {email}")
        return response_data
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in login: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

# GraphQL endpoint
@app.post("/graphql/")
@app.get("/graphql/")
async def graphql_endpoint(request: Request):
    """GraphQL endpoint for Apollo Client"""
    if not GRAPHQL_AVAILABLE:
        raise HTTPException(status_code=503, detail="GraphQL service not available")
    
    try:
        from core.schema import schema
        from core.authentication import get_user_from_token
        
        # Get request body
        body = await request.body()
        body_str = body.decode('utf-8') if isinstance(body, bytes) else body
        
        # Parse JSON body
        try:
            request_data = json.loads(body_str)
        except json.JSONDecodeError:
            raise HTTPException(status_code=400, detail="Invalid JSON in request body")
        
        query = request_data.get('query', '')
        variables = request_data.get('variables', {})
        operation_name = request_data.get('operationName')
        
        # Get user from token
        auth_header = request.headers.get('authorization', '')
        user = None
        if auth_header:
            token = auth_header.replace('Bearer ', '').replace('JWT ', '')
            try:
                user = await sync_to_async(get_user_from_token)(token)
            except Exception as e:
                logger.warning(f"Token validation failed: {e}")
        
        # Create GraphQL context using SimpleContext (supports both object and dict access)
        from core.graphql_context import SimpleContext
        context = SimpleContext(
            user=user if user else None,
            request=request
        )
        
        # Execute GraphQL query in a thread pool to avoid blocking
        import asyncio
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            None,
            lambda: schema.execute(
                query,
                variables=variables,
                operation_name=operation_name,
                context_value=context
            )
        )
        
        # Check for errors
        if result.errors:
            logger.error(f"GraphQL errors: {result.errors}")
            error_messages = []
            for error in result.errors:
                if hasattr(error, 'message'):
                    error_messages.append(str(error.message))
                else:
                    error_messages.append(str(error))
            return JSONResponse(
                content={'errors': error_messages, 'data': result.data},
                status_code=400
            )
        
        return JSONResponse(content={'data': result.data}, status_code=200)
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"GraphQL error: {e}", exc_info=True)
        import traceback
        logger.error(f"GraphQL traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"GraphQL error: {str(e)}")

async def run_portfolio_analysis():
    """Background task for portfolio analysis"""
    try:
        logger.info("Running portfolio analysis...")
        # This would call your actual portfolio analysis logic
        await asyncio.sleep(5)  # Simulate processing
        logger.info("Portfolio analysis completed")
    except Exception as e:
        logger.error(f"Portfolio analysis background task error: {e}")

async def run_market_regime_prediction():
    """Background task for market regime prediction"""
    try:
        logger.info("Running market regime prediction...")
        # This would call your actual market regime logic
        await asyncio.sleep(3)  # Simulate processing
        logger.info("Market regime prediction completed")
    except Exception as e:
        logger.error(f"Market regime prediction background task error: {e}")

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
