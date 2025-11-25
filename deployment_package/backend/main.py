#!/usr/bin/env python3
"""
RichesReach AI Service - Production Main Application
"""
from fastapi import FastAPI, HTTPException, BackgroundTasks, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response
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
from starlette.middleware.wsgi import WSGIMiddleware
from io import BytesIO
from dotenv import load_dotenv

# Load environment variables from .env file
# This ensures FastAPI can access environment variables even if Django hasn't loaded them yet
env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.env')
load_dotenv(env_path)

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

# Check for reportlab availability
try:
    from reportlab.lib.pagesizes import letter
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
    from reportlab.lib import colors
    from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False
    logger.warning("reportlab not available - PDF export will not work")

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

# Add request logging middleware for debugging
from starlette.middleware.base import BaseHTTPMiddleware

class RequestLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: StarletteRequest, call_next):
        # Log requests to Yodlee endpoints
        if '/api/yodlee' in str(request.url):
            import sys
            auth_header = request.headers.get('authorization') or request.headers.get('Authorization', '')
            print(f"🔵 [FastAPI] {request.method} {request.url.path}", file=sys.stdout, flush=True)
            print(f"🔵 [FastAPI] Authorization header: {'Present' if auth_header else 'MISSING'} ({auth_header[:30] if auth_header else 'None'}...)", file=sys.stdout, flush=True)
            print(f"🔵 [FastAPI] All headers: {dict(request.headers)}", file=sys.stdout, flush=True)
            logger.info(f"🔵 [FastAPI] {request.method} {request.url.path} - Auth: {'Present' if auth_header else 'MISSING'}")
        
        response = await call_next(request)
        return response

app.add_middleware(RequestLoggingMiddleware)

# Include AI Options router
if AI_OPTIONS_AVAILABLE:
    app.include_router(ai_options_router)

# Note: FastAPI routes (defined with @app.get/post/etc) are registered here
# Django will be mounted later, after all FastAPI routes are defined
# This ensures FastAPI routes take precedence

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

@app.get("/api/market/quotes")
async def get_market_quotes(symbols: str = None):
    """
    GET /api/market/quotes?symbols=AAPL,MSFT,GOOGL
    Returns real-time or cached stock quotes
    """
    try:
        if not symbols:
            raise HTTPException(status_code=400, detail="symbols parameter is required")
        
        symbol_list = [s.strip().upper() for s in symbols.split(",") if s.strip()]
        
        if not symbol_list:
            raise HTTPException(status_code=400, detail="No valid symbols provided")
        
        logger.info(f"📊 [Quotes API] Fetching quotes for {len(symbol_list)} symbols: {', '.join(symbol_list)}")
        
        # Try to import market data service
        try:
            from core.market_data_api_service import MarketDataAPIService
            market_data_service = MarketDataAPIService()
            MARKET_DATA_AVAILABLE = True
        except Exception as e:
            logger.warning(f"MarketDataAPIService not available: {e}")
            MARKET_DATA_AVAILABLE = False
            market_data_service = None
        
        quotes = []
        
        # If market data service is available, use it
        if MARKET_DATA_AVAILABLE and market_data_service:
            tasks = [market_data_service.get_stock_quote(symbol) for symbol in symbol_list]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            for symbol, result in zip(symbol_list, results):
                if isinstance(result, Exception):
                    logger.warning(f"Error fetching quote for {symbol}: {result}")
                    quotes.append(_get_mock_quote(symbol))
                    continue
                
                quote_data = result or {}
                if quote_data:
                    quotes.append({
                        "symbol": symbol,
                        "price": quote_data.get("price", 0.0),
                        "change": quote_data.get("change", 0.0),
                        "changePercent": quote_data.get("change_percent", 0.0),
                        "volume": quote_data.get("volume", 0),
                        "high": quote_data.get("high", 0.0),
                        "low": quote_data.get("low", 0.0),
                        "open": quote_data.get("open", 0.0),
                        "previousClose": quote_data.get("previous_close", 0.0),
                        "timestamp": quote_data.get("timestamp", ""),
                    })
                else:
                    quotes.append(_get_mock_quote(symbol))
            
            logger.info(f"✅ [Quotes API] Returning {len(quotes)} quotes")
        else:
            # Fallback to mock data if service unavailable
            logger.warning("⚠️ [Quotes API] MarketDataAPIService unavailable, using mock data")
            quotes = [_get_mock_quote(symbol) for symbol in symbol_list]
        
        return quotes
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ [Quotes API] Error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

def _get_mock_quote(symbol: str) -> dict:
    """Generate mock quote data for a symbol."""
    base_price = 100.0 + (hash(symbol) % 500)
    change = (hash(symbol) % 20) - 10
    return {
        "symbol": symbol,
        "price": base_price,
        "change": change,
        "changePercent": (change / base_price) * 100,
        "volume": (hash(symbol) % 10_000_000) + 1_000_000,
        "high": base_price + 5,
        "low": base_price - 5,
        "open": base_price + 2,
        "previousClose": base_price - 2,
        "timestamp": "",
    }

@app.get("/api/yodlee/accounts")
async def get_yodlee_accounts(request: Request):
    """
    GET /api/yodlee/accounts
    Returns user's linked bank accounts from Yodlee or database.
    """
    if not DJANGO_AVAILABLE:
        # Return empty accounts in dev mode if Django not available
        return {
            "success": True,
            "accounts": [],
            "count": 0,
        }
    
    try:
        # Extract token from Authorization header
        auth_header = request.headers.get("Authorization", "")
        token = None
        if auth_header.startswith("Token "):
            token = auth_header.replace("Token ", "")
        elif auth_header.startswith("Bearer "):
            token = auth_header.replace("Bearer ", "")
        
        # Get user
        User = get_user_model()
        user = None
        
        # Handle dev tokens (dev-token-*)
        if token and token.startswith('dev-token-'):
            # Dev token - get demo user
            try:
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
                logger.warning(f"Error getting demo user: {e}")
        elif token and GRAPHQL_JWT_AVAILABLE:
            # Try JWT token validation
            try:
                from graphql_jwt.shortcuts import get_user_by_token
                user = await sync_to_async(get_user_by_token)(token)
            except Exception as e:
                logger.debug(f"JWT token validation failed: {e}")
        
        # Fallback: get demo user or first user (for unauthenticated dev requests)
        if not user:
            try:
                user = await sync_to_async(User.objects.filter(email='demo@example.com').first)()
                if not user:
                    user = await sync_to_async(User.objects.first)()
            except Exception as e:
                logger.warning(f"Error getting user: {e}")
        
        # In dev mode, allow unauthenticated requests with empty accounts
        # In production, this would require authentication
        if not user:
            logger.debug("No user found, returning empty accounts for dev mode")
            return {
                "success": True,
                "accounts": [],
                "count": 0,
            }
        
        # Check if Yodlee is enabled
        try:
            from core.banking_views import _is_yodlee_enabled
            yodlee_enabled = await sync_to_async(_is_yodlee_enabled)()
            if not yodlee_enabled:
                # Return empty accounts if Yodlee is disabled (common in dev)
                return {
                    "success": True,
                    "accounts": [],
                    "count": 0,
                }
        except Exception as e:
            logger.debug(f"Could not check Yodlee status: {e}")
            # Continue anyway - might be dev mode
        
        # Get accounts from database
        from core.banking_models import BankAccount
        db_accounts = await sync_to_async(list)(
            BankAccount.objects.filter(user=user, is_verified=True)
        )
        
        if db_accounts:
            accounts = []
            for db_account in db_accounts:
                accounts.append({
                    'id': db_account.id,
                    'accountId': str(db_account.yodlee_account_id or db_account.id),
                    'name': db_account.name or f"{db_account.provider} Account",
                    'type': db_account.account_type or 'CHECKING',
                    'mask': db_account.mask or '****',
                    'currency': db_account.currency or 'USD',
                    'balance': float(db_account.balance_current) if db_account.balance_current else 0.0,
                    'availableBalance': float(db_account.balance_available) if db_account.balance_available else 0.0,
                    'institutionName': db_account.provider or 'Unknown',
                    'lastUpdated': db_account.last_updated.isoformat() if db_account.last_updated else None,
                })
            
            return {
                "success": True,
                "accounts": accounts,
                "count": len(accounts),
            }
        
        # If no DB accounts, return empty (Yodlee integration would fetch here)
        return {
            "success": True,
            "accounts": [],
            "count": 0,
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting Yodlee accounts: {e}", exc_info=True)
        # Return empty accounts on error (better UX than 500)
        return {
            "success": True,
            "accounts": [],
            "count": 0,
        }

@app.post("/api/tax/report/pdf")
async def generate_tax_report_pdf(request: Request):
    """
    Generate a PDF tax optimization report.
    Returns a PDF file with comprehensive tax analysis.
    """
    if not DJANGO_AVAILABLE:
        raise HTTPException(status_code=503, detail="Tax optimization service not available")
    
    if not REPORTLAB_AVAILABLE:
        raise HTTPException(status_code=503, detail="PDF generation not available - reportlab not installed")
    
    try:
        # Extract token and request body
        auth_header = request.headers.get("Authorization", "")
        token = None
        if auth_header.startswith("Token "):
            token = auth_header.replace("Token ", "")
        elif auth_header.startswith("Bearer "):
            token = auth_header.replace("Bearer ", "")
        
        body = await request.json()
        year = body.get('year', datetime.now().year)
        filing_status = body.get('filingStatus', 'single')
        state = body.get('state', 'CA')
        income = body.get('income', 0)
        
        # Get user
        User = get_user_model()
        user = None
        
        if token and GRAPHQL_JWT_AVAILABLE:
            try:
                from graphql_jwt.shortcuts import get_user_by_token
                user = await sync_to_async(get_user_by_token)(token)
            except Exception:
                pass
        
        if not user:
            user = await sync_to_async(User.objects.filter(email='demo@example.com').first)()
            if not user:
                user = await sync_to_async(User.objects.first)()
        
        # Get portfolio data
        from core.premium_analytics import PremiumAnalyticsService
        service = PremiumAnalyticsService()
        metrics = await sync_to_async(service.get_portfolio_performance_metrics)(user.id)
        
        holdings = []
        if metrics and metrics.get('holdings'):
            for holding in metrics['holdings']:
                holdings.append({
                    'symbol': holding.get('symbol', ''),
                    'companyName': holding.get('company_name', holding.get('name', '')),
                    'shares': holding.get('shares', 0),
                    'currentPrice': float(holding.get('current_price', 0) or 0),
                    'costBasis': float(holding.get('cost_basis', 0) or 0),
                    'totalValue': float(holding.get('total_value', 0) or 0),
                    'returnAmount': float(holding.get('return_amount', 0) or 0),
                    'returnPercent': float(holding.get('return_percent', 0) or 0),
                })
        
        # Calculate tax metrics
        total_portfolio_value = metrics.get('total_value', 0) if metrics else 0
        total_unrealized_gains = metrics.get('total_return', 0) if metrics else 0
        
        # Generate PDF
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter, topMargin=0.5*inch, bottomMargin=0.5*inch)
        story = []
        styles = getSampleStyleSheet()
        
        # Title
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#2563EB'),
            spaceAfter=30,
            alignment=TA_CENTER,
        )
        story.append(Paragraph(f"Tax Optimization Report {year}", title_style))
        story.append(Spacer(1, 0.2*inch))
        
        # Header info
        header_data = [
            ['Generated:', datetime.now().strftime('%B %d, %Y')],
            ['Filing Status:', filing_status.replace('-', ' ').title()],
            ['State:', state],
            ['Annual Income:', f"${income:,.0f}"],
        ]
        header_table = Table(header_data, colWidths=[2*inch, 4*inch])
        header_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#F3F4F6')),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 11),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
        ]))
        story.append(header_table)
        story.append(Spacer(1, 0.3*inch))
        
        # Tax Summary Section
        story.append(Paragraph("Tax Summary", styles['Heading2']))
        story.append(Spacer(1, 0.1*inch))
        
        # Calculate taxes (simplified)
        federal_tax = income * 0.22  # Simplified calculation
        state_tax = income * 0.10 if state == 'CA' else income * 0.05
        total_tax = federal_tax + state_tax
        effective_rate = (total_tax / income * 100) if income > 0 else 0
        
        tax_data = [
            ['Federal Tax', f"${federal_tax:,.2f}"],
            ['State Tax', f"${state_tax:,.2f}"],
            ['Total Tax', f"${total_tax:,.2f}"],
            ['Effective Rate', f"{effective_rate:.1f}%"],
        ]
        tax_table = Table(tax_data, colWidths=[4*inch, 2*inch])
        tax_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2563EB')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 11),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 1, colors.grey),
        ]))
        story.append(tax_table)
        story.append(Spacer(1, 0.3*inch))
        
        # Portfolio Section
        story.append(Paragraph("Portfolio Overview", styles['Heading2']))
        story.append(Spacer(1, 0.1*inch))
        
        portfolio_data = [
            ['Total Portfolio Value', f"${total_portfolio_value:,.2f}"],
            ['Total Unrealized Gains', f"${total_unrealized_gains:,.2f}"],
        ]
        portfolio_table = Table(portfolio_data, colWidths=[4*inch, 2*inch])
        portfolio_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
            ('FONTSIZE', (0, 0), (-1, -1), 11),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
        ]))
        story.append(portfolio_table)
        story.append(Spacer(1, 0.3*inch))
        
        # Top Holdings Section
        if holdings:
            story.append(Paragraph("Top Holdings (Tax Impact)", styles['Heading2']))
            story.append(Spacer(1, 0.1*inch))
            
            holdings_data = [['Symbol', 'Company', 'Shares', 'Value', 'Gain/Loss']]
            for holding in holdings[:10]:  # Top 10
                gain_loss = f"${holding['returnAmount']:,.2f}"
                holdings_data.append([
                    holding['symbol'],
                    holding['companyName'][:30] if holding['companyName'] else holding['symbol'],
                    f"{holding['shares']:,.0f}",
                    f"${holding['totalValue']:,.2f}",
                    gain_loss,
                ])
            
            holdings_table = Table(holdings_data, colWidths=[0.8*inch, 2.2*inch, 0.8*inch, 1*inch, 1.2*inch])
            holdings_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2563EB')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('ALIGN', (2, 0), (4, -1), 'RIGHT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
                ('TOPPADDING', (0, 0), (-1, -1), 6),
                ('GRID', (0, 0), (-1, -1), 1, colors.grey),
            ]))
            story.append(holdings_table)
            story.append(Spacer(1, 0.3*inch))
        
        # Footer
        story.append(Spacer(1, 0.2*inch))
        footer_style = ParagraphStyle(
            'Footer',
            parent=styles['Normal'],
            fontSize=9,
            textColor=colors.grey,
            alignment=TA_CENTER,
        )
        story.append(Paragraph(
            "This report is for informational purposes only and does not constitute tax advice. "
            "Please consult with a qualified tax professional for personalized advice.",
            footer_style
        ))
        
        # Build PDF
        doc.build(story)
        buffer.seek(0)
        pdf_bytes = buffer.getvalue()
        
        return Response(
            content=pdf_bytes,
            media_type='application/pdf',
            headers={
                'Content-Disposition': f'attachment; filename="tax_report_{year}.pdf"'
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating PDF report: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error generating PDF: {str(e)}")

@app.post("/api/tax/smart-harvest/recommendations")
async def get_smart_harvest_recommendations(request: Request):
    """
    Get smart harvest recommendations with pre-filled trades.
    Returns optimized tax-loss harvesting suggestions.
    """
    if not DJANGO_AVAILABLE:
        raise HTTPException(status_code=503, detail="Tax optimization service not available")
    
    try:
        # Extract token and request body
        auth_header = request.headers.get("Authorization", "")
        token = None
        if auth_header.startswith("Token "):
            token = auth_header.replace("Token ", "")
        elif auth_header.startswith("Bearer "):
            token = auth_header.replace("Bearer ", "")
        
        body = await request.json()
        holdings = body.get('holdings', [])
        
        # Get user
        User = get_user_model()
        user = None
        
        if token and GRAPHQL_JWT_AVAILABLE:
            try:
                from graphql_jwt.shortcuts import get_user_by_token
                user = await sync_to_async(get_user_by_token)(token)
            except Exception:
                pass
        
        if not user:
            user = await sync_to_async(User.objects.filter(email='demo@example.com').first)()
            if not user:
                user = await sync_to_async(User.objects.first)()
        
        # Calculate recommendations
        trades = []
        total_savings = 0
        warnings = []
        
        for holding in holdings:
            unrealized_gain = holding.get('unrealizedGain', 0)
            if unrealized_gain < 0:  # Only losses
                loss_amount = abs(unrealized_gain)
                # Estimate tax savings (assuming 22% marginal rate)
                estimated_savings = loss_amount * 0.22
                total_savings += estimated_savings
                
                trades.append({
                    'symbol': holding.get('symbol', ''),
                    'shares': holding.get('shares', 0),
                    'action': 'sell',
                    'estimatedSavings': round(estimated_savings, 2),
                    'reason': f'Harvest ${loss_amount:,.0f} in losses',
                })
        
        return {
            'trades': trades,
            'totalSavings': round(total_savings, 2),
            'warnings': warnings,
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting smart harvest recommendations: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error getting recommendations: {str(e)}")

@app.post("/api/tax/smart-harvest/execute")
async def execute_smart_harvest(request: Request):
    """
    Execute smart harvest trades.
    In production, this would place actual orders with the broker.
    """
    if not DJANGO_AVAILABLE:
        raise HTTPException(status_code=503, detail="Tax optimization service not available")
    
    try:
        # Extract token and request body
        auth_header = request.headers.get("Authorization", "")
        token = None
        if auth_header.startswith("Token "):
            token = auth_header.replace("Token ", "")
        elif auth_header.startswith("Bearer "):
            token = auth_header.replace("Bearer ", "")
        
        body = await request.json()
        trades = body.get('trades', [])
        
        # Get user
        User = get_user_model()
        user = None
        
        if token and GRAPHQL_JWT_AVAILABLE:
            try:
                from graphql_jwt.shortcuts import get_user_by_token
                user = await sync_to_async(get_user_by_token)(token)
            except Exception:
                pass
        
        if not user:
            user = await sync_to_async(User.objects.filter(email='demo@example.com').first)()
            if not user:
                user = await sync_to_async(User.objects.first)()
        
        # Broker API integration structure
        executed_trades = []
        failed_trades = []
        
        try:
            # Import broker service if available
            from core.broker_mutations import PlaceOrder
            from core.broker_models import BrokerAccount, BrokerOrder
            from core.alpaca_broker_service import AlpacaBrokerService
            
            # Get user's broker account
            broker_account = await sync_to_async(BrokerAccount.objects.filter(user=user).first)()
            
            if broker_account and broker_account.alpaca_account_id:
                # Initialize broker service
                broker_service = AlpacaBrokerService()
                
                for trade in trades:
                    try:
                        symbol = trade.get('symbol', '').upper()
                        shares = int(trade.get('shares', 0))
                        
                        if shares <= 0:
                            failed_trades.append({
                                'symbol': symbol,
                                'error': 'Invalid share quantity',
                            })
                            continue
                        
                        # Place sell order through broker API
                        # In production, this would use the actual broker service
                        order_result = {
                            'symbol': symbol,
                            'shares': shares,
                            'side': 'sell',
                            'order_type': 'MARKET',
                            'status': 'submitted',
                            'order_id': f'TLH_{symbol}_{datetime.now().timestamp()}',
                        }
                        
                        # Log the order (in production, save to BrokerOrder model)
                        executed_trades.append(order_result)
                        
                    except Exception as trade_error:
                        logger.error(f"Error executing trade for {trade.get('symbol')}: {trade_error}")
                        failed_trades.append({
                            'symbol': trade.get('symbol', 'UNKNOWN'),
                            'error': str(trade_error),
                        })
            else:
                # No broker account linked - return mock success for demo
                logger.info("No broker account linked, returning mock execution")
                for trade in trades:
                    executed_trades.append({
                        'symbol': trade.get('symbol', ''),
                        'shares': trade.get('shares', 0),
                        'status': 'simulated',
                        'order_id': f'TLH_{trade.get("symbol", "UNKNOWN")}_{datetime.now().timestamp()}',
                    })
                    
        except ImportError:
            # Broker integration not available - return mock success
            logger.info("Broker integration not available, returning mock execution")
            for trade in trades:
                executed_trades.append({
                    'symbol': trade.get('symbol', ''),
                    'shares': trade.get('shares', 0),
                    'status': 'simulated',
                    'order_id': f'TLH_{trade.get("symbol", "UNKNOWN")}_{datetime.now().timestamp()}',
                })
        except Exception as broker_error:
            logger.error(f"Broker integration error: {broker_error}")
            # Fallback to mock execution
            for trade in trades:
                executed_trades.append({
                    'symbol': trade.get('symbol', ''),
                    'shares': trade.get('shares', 0),
                    'status': 'simulated',
                    'order_id': f'TLH_{trade.get("symbol", "UNKNOWN")}_{datetime.now().timestamp()}',
                })
        
        return {
            'success': len(executed_trades) > 0,
            'tradesExecuted': len(executed_trades),
            'tradesFailed': len(failed_trades),
            'executedTrades': executed_trades,
            'failedTrades': failed_trades,
            'message': f'Smart harvest: {len(executed_trades)} trades executed, {len(failed_trades)} failed',
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error executing smart harvest: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error executing harvest: {str(e)}")

@app.get("/api/tax/projection")
async def get_tax_projection(request: Request):
    """
    Get multi-year tax projections.
    Returns year-by-year tax estimates.
    """
    if not DJANGO_AVAILABLE:
        raise HTTPException(status_code=503, detail="Tax optimization service not available")
    
    try:
        # Extract token and query params
        auth_header = request.headers.get("Authorization", "")
        token = None
        if auth_header.startswith("Token "):
            token = auth_header.replace("Token ", "")
        elif auth_header.startswith("Bearer "):
            token = auth_header.replace("Bearer ", "")
        
        years = int(request.query_params.get('years', 5))
        income = float(request.query_params.get('income', 80000))
        filing_status = request.query_params.get('filingStatus', 'single')
        state = request.query_params.get('state', 'CA')
        
        # Get user
        User = get_user_model()
        user = None
        
        if token and GRAPHQL_JWT_AVAILABLE:
            try:
                from graphql_jwt.shortcuts import get_user_by_token
                user = await sync_to_async(get_user_by_token)(token)
            except Exception:
                pass
        
        if not user:
            user = await sync_to_async(User.objects.filter(email='demo@example.com').first)()
            if not user:
                user = await sync_to_async(User.objects.first)()
        
        # Enhanced projection calculations
        projections = []
        current_year = datetime.now().year
        
        # Tax brackets for more accurate calculations
        INCOME_BRACKETS = {
            'single': [
                {'min': 0, 'max': 11600, 'rate': 0.10},
                {'min': 11601, 'max': 47150, 'rate': 0.12},
                {'min': 47151, 'max': 100525, 'rate': 0.22},
                {'min': 100526, 'max': 191950, 'rate': 0.24},
                {'min': 191951, 'max': 243725, 'rate': 0.32},
                {'min': 243726, 'max': 609350, 'rate': 0.35},
                {'min': 609351, 'max': float('inf'), 'rate': 0.37},
            ],
            'married-joint': [
                {'min': 0, 'max': 23200, 'rate': 0.10},
                {'min': 23201, 'max': 94300, 'rate': 0.12},
                {'min': 94301, 'max': 201050, 'rate': 0.22},
                {'min': 201051, 'max': 383900, 'rate': 0.24},
                {'min': 383901, 'max': 487450, 'rate': 0.32},
                {'min': 487451, 'max': 731200, 'rate': 0.35},
                {'min': 731201, 'max': float('inf'), 'rate': 0.37},
            ],
        }
        
        # State tax rates
        STATE_TAX_RATES = {
            'CA': 0.10, 'NY': 0.09, 'NJ': 0.1075, 'OR': 0.099,
            'TX': 0.0, 'FL': 0.0, 'NV': 0.0, 'WA': 0.0,
        }
        
        def calculate_federal_tax(income, filing_status):
            """Calculate federal tax using actual brackets"""
            brackets = INCOME_BRACKETS.get(filing_status, INCOME_BRACKETS['single'])
            tax = 0
            prev_max = 0
            
            for bracket in brackets:
                if income > prev_max:
                    taxable_in_bracket = min(income, bracket['max']) - prev_max
                    tax += taxable_in_bracket * bracket['rate']
                    prev_max = bracket['max']
            
            return tax
        
        def calculate_state_tax(income, state_code):
            """Calculate state tax"""
            rate = STATE_TAX_RATES.get(state_code, 0.05)
            return income * rate
        
        # Calculate projections with enhanced logic
        for i in range(years + 1):
            year = current_year + i
            # Assume 3% annual income growth (can be made configurable)
            growth_rate = 0.03
            projected_income = income * ((1 + growth_rate) ** i)
            
            # Calculate taxes using actual brackets
            federal_tax = calculate_federal_tax(projected_income, filing_status)
            state_tax = calculate_state_tax(projected_income, state)
            total_tax = federal_tax + state_tax
            effective_rate = (total_tax / projected_income * 100) if projected_income > 0 else 0
            
            # Calculate marginal rate (top bracket rate)
            brackets = INCOME_BRACKETS.get(filing_status, INCOME_BRACKETS['single'])
            marginal_rate = 0.10
            for bracket in brackets:
                if projected_income >= bracket['min']:
                    marginal_rate = bracket['rate']
            
            projections.append({
                'year': year,
                'projectedIncome': round(projected_income, 2),
                'projectedTax': round(total_tax, 2),
                'federalTax': round(federal_tax, 2),
                'stateTax': round(state_tax, 2),
                'effectiveRate': round(effective_rate, 2),
                'marginalRate': round(marginal_rate * 100, 1),
            })
        
        return {
            'projections': projections,
            'currentYear': current_year,
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting tax projection: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error getting projection: {str(e)}")

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
        
        # Add logging for sblocBanks queries
        if 'sblocBanks' in query or 'sbloc_banks' in query:
            logger.info(f"🔵 [GraphQL] Executing sblocBanks query")
            logger.info(f"🔵 [GraphQL] Query: {query[:200]}...")
            logger.info(f"🔵 [GraphQL] Context user: {context.user if hasattr(context, 'user') else 'None'}")
        
        result = await loop.run_in_executor(
            None,
            lambda: schema.execute(
                query,
                variables=variables,
                operation_name=operation_name,
                context_value=context
            )
        )
        
        # Add logging for sblocBanks results
        if 'sblocBanks' in query or 'sbloc_banks' in query:
            logger.info(f"🔵 [GraphQL] sblocBanks result.data type: {type(result.data)}")
            if result.data:
                logger.info(f"🔵 [GraphQL] sblocBanks result.data keys: {result.data.keys() if isinstance(result.data, dict) else 'not a dict'}")
                if 'sblocBanks' in result.data:
                    logger.info(f"🔵 [GraphQL] sblocBanks value: {result.data['sblocBanks']}")
                    logger.info(f"🔵 [GraphQL] sblocBanks length: {len(result.data['sblocBanks']) if isinstance(result.data['sblocBanks'], list) else 'not a list'}")
            if result.errors:
                logger.error(f"🔵 [GraphQL] sblocBanks errors: {result.errors}")
        
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

# Test endpoint to verify SBLOC banks are accessible
@app.get("/api/test/sbloc-banks")
async def test_sbloc_banks():
    """Test endpoint to verify SBLOC banks are in database"""
    if not DJANGO_AVAILABLE:
        return JSONResponse(content={'error': 'Django not available', 'banks': []}, status_code=503)
    
    try:
        from core.sbloc_models import SBLOCBank
        
        # Use sync_to_async for Django ORM calls
        def get_banks():
            banks = SBLOCBank.objects.filter(is_active=True).order_by('priority', 'name')
            banks_data = []
            for bank in banks:
                banks_data.append({
                    'id': str(bank.id),
                    'name': bank.name,
                    'minApr': float(bank.min_apr) if bank.min_apr else None,
                    'maxApr': float(bank.max_apr) if bank.max_apr else None,
                    'minLtv': float(bank.min_ltv) if bank.min_ltv else None,
                    'maxLtv': float(bank.max_ltv) if bank.max_ltv else None,
                    'minLoanUsd': int(bank.min_loan_usd) if bank.min_loan_usd else None,
                    'regions': bank.regions or [],
                })
            return banks_data
        
        banks_data = await sync_to_async(get_banks)()
        return JSONResponse(content={'banks': banks_data, 'count': len(banks_data)}, status_code=200)
    except Exception as e:
        logger.error(f"Error in test_sbloc_banks: {e}", exc_info=True)
        return JSONResponse(content={'error': str(e), 'banks': []}, status_code=500)

# Mount Django URLs at the END - after all FastAPI routes are defined
# This ensures FastAPI routes take precedence, then Django handles remaining paths
if DJANGO_AVAILABLE:
    try:
        from django.core.wsgi import get_wsgi_application
        
        # Get Django WSGI application
        django_wsgi = get_wsgi_application()
        
        # CRITICAL FIX: WSGIMiddleware's build_environ() should convert Authorization to HTTP_AUTHORIZATION
        # But it's not working. We need to patch build_environ to explicitly include it.
        from starlette.middleware.wsgi import build_environ as original_build_environ
        import starlette.middleware.wsgi as wsgi_module
        import sys
        
        def patched_build_environ(scope, body):
            """Patched build_environ that explicitly includes Authorization header"""
            import sys
            # Log all headers in scope for debugging
            if scope.get("type") == "http":
                headers = scope.get("headers", [])
                print(f"🔵 [PATCH] build_environ called for {scope.get('path', 'unknown')}", file=sys.stdout, flush=True)
                print(f"🔵 [PATCH] Headers in ASGI scope: {[(name.decode('latin1'), value.decode('latin1')[:30]) for name, value in headers]}", file=sys.stdout, flush=True)
                
                # Check for Authorization header
                auth_found = False
                for name, value in headers:
                    if name.lower() == b"authorization":
                        auth_found = True
                        auth_value = value.decode("latin1")
                        print(f"🔵 [PATCH] Found Authorization in ASGI scope: {auth_value[:30]}...", file=sys.stdout, flush=True)
                        break
                
                if not auth_found:
                    print(f"❌ [PATCH] Authorization NOT FOUND in ASGI scope headers!", file=sys.stdout, flush=True)
            
            # Call original to get the base environ
            environ = original_build_environ(scope, body)
            
            # Manually extract and add Authorization header if present in ASGI scope
            if scope.get("type") == "http":
                headers = scope.get("headers", [])
                for name, value in headers:
                    if name.lower() == b"authorization":
                        auth_value = value.decode("latin1")
                        environ["HTTP_AUTHORIZATION"] = auth_value
                        print(f"🔵 [PATCH] Injected HTTP_AUTHORIZATION: {auth_value[:30]}...", file=sys.stdout, flush=True)
                        logger.info(f"🔵 [PATCH] Injected HTTP_AUTHORIZATION into WSGI environ")
                        break
            
            return environ
        
        # Monkey-patch the build_environ function
        print(f"🔵 [SETUP] Patching build_environ function...", file=sys.stdout, flush=True)
        original_build_environ_ref = wsgi_module.build_environ
        wsgi_module.build_environ = patched_build_environ
        print(f"🔵 [SETUP] build_environ patched. Original: {original_build_environ_ref}, New: {wsgi_module.build_environ}", file=sys.stdout, flush=True)
        logger.info("🔵 [SETUP] build_environ function patched to include Authorization header")
        
        # Create a wrapper for extra logging
        def django_wsgi_with_auth(environ, start_response):
            """WSGI wrapper with logging"""
            import sys
            print(f"🔵 [WSGI WRAPPER] Called for PATH_INFO={environ.get('PATH_INFO')}", file=sys.stdout, flush=True)
            http_keys = [k for k in environ.keys() if k.startswith('HTTP_')]
            print(f"🔵 [WSGI WRAPPER] HTTP_* keys: {http_keys}", file=sys.stdout, flush=True)
            if 'HTTP_AUTHORIZATION' in environ:
                print(f"🔵 [WSGI WRAPPER] HTTP_AUTHORIZATION={environ['HTTP_AUTHORIZATION'][:30]}...", file=sys.stdout, flush=True)
            else:
                print(f"❌ [WSGI WRAPPER] HTTP_AUTHORIZATION NOT FOUND", file=sys.stdout, flush=True)
                print(f"❌ [WSGI WRAPPER] All environ keys: {list(environ.keys())}", file=sys.stdout, flush=True)
            return django_wsgi(environ, start_response)
        
        # Mount Django at root - all Django URLs will be available
        # FastAPI routes are checked first (defined above), then Django routes handle the rest
        app.mount("/", WSGIMiddleware(django_wsgi_with_auth))
        
        logger.info("✅ Django URLs mounted - all Django views are now available")
        logger.info("   FastAPI routes take precedence, then Django routes handle remaining paths")
    except Exception as e:
        logger.warning(f"Could not mount Django URLs: {e}")
        logger.warning("Django views will not be available through FastAPI")

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
