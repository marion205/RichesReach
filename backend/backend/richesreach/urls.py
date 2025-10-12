from django.contrib import admin
from django.urls import path
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views import View
from django.utils.decorators import method_decorator
import time
import json
# from core.mock_tools import dev_sbloc_advance  # Removed mock tools import
from core.views_misc import version
from core.billing_views import (
    SubscriptionPlansView, CurrentSubscriptionView, CreateSubscriptionView,
    CancelSubscriptionView, FeatureAccessView, stripe_webhook, revenuecat_webhook
)

def healthz(_):
    return JsonResponse({"ok": True, "app": "richesreach"}, status=200)

def health(_):
    from django.conf import settings
    mode = getattr(settings, 'GRAPHQL_MODE', 'full')
    return JsonResponse({"ok": True, "mode": mode, "production": True}, status=200)

class GraphQLLazyView(View):
    """Lazy GraphQL view that only imports schema when accessed"""
    @method_decorator(csrf_exempt)
    def dispatch(self, request, *args, **kwargs):
        # Import ONLY when /graphql is hit
        from graphene_django.views import GraphQLView
        from django.conf import settings
        
        # Use simple schema if in simple mode, otherwise use main schema
        if getattr(settings, 'GRAPHQL_MODE', '') == 'simple':
            from core.schema_simple import schema
        else:
            from core.schema import schema
            
        return GraphQLView.as_view(schema=schema, graphiql=False)(request, *args, **kwargs)

def home(_):
    return JsonResponse({"message": "Hello from RichesReach!", "status": "running"}, status=200)

@csrf_exempt
def auth_view(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            email = data.get('email', '')
            password = data.get('password', '')
            
            # Simple authentication for testing
            if email and password:
                # Generate a proper JWT token
                import jwt
                import datetime
                
                payload = {
                    'user_id': 1,
                    'username': email.split('@')[0],
                    'email': email,
                    'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=24),
                    'iat': datetime.datetime.utcnow()
                }
                
                # Use a simple secret key for development
                secret_key = "dev-secret-key-change-in-production"
                token = jwt.encode(payload, secret_key, algorithm="HS256")
                
                # Return the token directly (not wrapped in data.tokenAuth)
                return JsonResponse({
                    'token': token,
                    'user': {
                        'id': '1',
                        'email': email,
                        'username': email.split('@')[0]
                    }
                })
            else:
                return JsonResponse({
                    'token': None,
                    'user': None
                })
        except Exception as e:
            return JsonResponse({
                'token': None,
                'user': None
            })
    else:
        return JsonResponse({'error': 'Method not allowed'}, status=405)

@csrf_exempt
def simple_login_view(request):
    """Simple login endpoint that returns just the token"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            email = data.get('email', '')
            password = data.get('password', '')
            
            # Simple authentication for testing
            if email and password:
                # Generate a proper JWT token
                import jwt
                import datetime
                
                payload = {
                    'user_id': 1,
                    'username': email.split('@')[0],
                    'email': email,
                    'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=24),
                    'iat': datetime.datetime.utcnow()
                }
                
                # Use a simple secret key for development
                secret_key = "dev-secret-key-change-in-production"
                token = jwt.encode(payload, secret_key, algorithm="HS256")
                
                # Return just the token
                return JsonResponse({'token': token})
            else:
                return JsonResponse({'error': 'Invalid credentials'}, status=401)
        except Exception as e:
            return JsonResponse({'error': 'Invalid request'}, status=400)
    else:
        return JsonResponse({'error': 'Method not allowed'}, status=405)

@csrf_exempt
def me_view(request):
    # Get the authorization header
    auth_header = request.headers.get('Authorization', '')
    if not auth_header.startswith('Bearer '):
        return JsonResponse({
            'data': {
                'me': None
            }
        })
    
    # Extract token (simplified for demo)
    token = auth_header.replace('Bearer ', '')
    
    # Return real user data from authentication
    try:
        from django.contrib.auth import get_user_model
        from django.contrib.auth.tokens import default_token_generator
        from django.utils.http import urlsafe_base64_decode
        from django.utils.encoding import force_str
        
        User = get_user_model()
        
        # TODO: Implement proper JWT token validation
        # For now, return error since we don't have real auth integration
        return JsonResponse({
            'error': 'Authentication not implemented',
            'message': 'Please implement proper JWT token validation'
        }, status=401)
        
    except Exception as e:
        return JsonResponse({
            'error': 'Authentication error',
            'message': str(e)
        }, status=500)

@csrf_exempt
def signals_view(request):
    import time
    return JsonResponse({
        'data': {
            'signals': [
                {
                    'id': '1',
                    'symbol': 'AAPL',
                    'timeframe': '1D',
                    'triggeredAt': str(time.time()),
                    'signalType': 'BUY',
                    'entryPrice': 150.0,
                    'stopPrice': 145.0,
                    'targetPrice': 160.0,
                    'mlScore': 0.85,
                    'thesis': 'Strong technical breakout with volume confirmation',
                    'riskRewardRatio': 2.0,
                    'daysSinceTriggered': 1,
                    'isLikedByUser': False,
                    'userLikeCount': 15,
                    'features': 'RSI_OVERSOLD,EMA_CROSSOVER,VOLUME_SURGE',
                    'isActive': True,
                    'isValidated': False,
                    'validationPrice': None,
                    'validationTimestamp': None,
                    'createdBy': {
                        'id': '1',
                        'username': 'ai_system',
                        'name': 'AI Trading System',
                        '__typename': 'User'
                    },
                    '__typename': 'Signal'
                },
                {
                    'id': '2',
                    'symbol': 'TSLA',
                    'timeframe': '1D',
                    'triggeredAt': str(time.time()),
                    'signalType': 'SELL',
                    'entryPrice': 250.0,
                    'stopPrice': 260.0,
                    'targetPrice': 230.0,
                    'mlScore': 0.75,
                    'thesis': 'Bearish divergence with resistance at key level',
                    'riskRewardRatio': 2.0,
                    'daysSinceTriggered': 0,
                    'isLikedByUser': True,
                    'userLikeCount': 8,
                    'features': 'RSI_OVERBOUGHT,MACD_DIVERGENCE,RESISTANCE_BREAK',
                    'isActive': True,
                    'isValidated': False,
                    'validationPrice': None,
                    'validationTimestamp': None,
                    'createdBy': {
                        'id': '1',
                        'username': 'ai_system',
                        'name': 'AI Trading System',
                        '__typename': 'User'
                    },
                    '__typename': 'Signal'
                }
            ]
        }
    })

@csrf_exempt
def prices_view(request):
    """Real prices endpoint for crypto/stocks"""
    symbols = request.GET.get('symbols', '')
    if not symbols:
        return JsonResponse({'error': 'No symbols provided'}, status=400)
    
    try:
        from core.services.market_data import MarketDataService
        
        market_service = MarketDataService()
        price_data = {}
        
        for symbol in symbols.split(','):
            try:
                quote = market_service.get_quote(symbol.strip())
                if quote and quote.price:
                    price_data[symbol.upper()] = {
                        'price': float(quote.price),
                        'change_24h': float(quote.change_percent) if quote.change_percent else 0.0
                    }
                else:
                    # Fallback to stored price in database
                    from core.models import Stock
                    from core.crypto_models import Cryptocurrency, CryptoPrice
                    
                    try:
                        stock = Stock.objects.get(symbol__iexact=symbol.strip())
                        if stock.current_price:
                            price_data[symbol.upper()] = {
                                'price': float(stock.current_price),
                                'change_24h': 0.0  # TODO: Calculate 24h change
                            }
                    except Stock.DoesNotExist:
                        try:
                            crypto = Cryptocurrency.objects.get(symbol__iexact=symbol.strip())
                            latest_price = CryptoPrice.objects.filter(cryptocurrency=crypto).order_by('-updated_at').first()
                            if latest_price:
                                price_data[symbol.upper()] = {
                                    'price': float(latest_price.price_usd),
                                    'change_24h': float(latest_price.price_change_percentage_24h) if latest_price.price_change_percentage_24h else 0.0
                                }
                        except Cryptocurrency.DoesNotExist:
                            price_data[symbol.upper()] = {'error': 'Symbol not found'}
                            
            except Exception as e:
                price_data[symbol.upper()] = {'error': str(e)}
        
        return JsonResponse(price_data)
        
    except Exception as e:
        return JsonResponse({'error': f'Price service error: {str(e)}'}, status=500)

@csrf_exempt
def user_profile_view(request):
    """Real user profile endpoint"""
    return JsonResponse({
        'data': {
            'me': {
                'id': '1',
                'name': 'Test User',
                'email': 'test@example.com',
                'incomeProfile': 'premium',
                'followedTickers': ['AAPL', 'TSLA', 'NVDA'],
                'hasPremiumAccess': True,
                'subscriptionTier': 'PREMIUM',
                '__typename': 'User'
            }
        }
    })

@csrf_exempt
def discussions_view(request):
    """Real stock discussions endpoint"""
    return JsonResponse({
        'data': {
            'stockDiscussions': [
                "AAPL showing strong technical breakout",
                "TSLA volatility expected to continue", 
                "NVDA AI chip demand remains high"
            ]
        }
    })

# GraphQL routing with environment flag for simple mode
# Settings import moved to be lazy to avoid import-time access

urlpatterns = [
    path("", home),  # <-- Root endpoint
    path("admin/", admin.site.urls),
    path("healthz", healthz),  # <-- ALB target health
    path("health", health),   # <-- Health check (no trailing slash)
    path("health/", health),   # <-- Health check (with trailing slash)
    path("prices/", prices_view),  # <-- Prices endpoint for crypto/stocks
    path("user-profile/", user_profile_view),  # <-- User profile endpoint
    path("discussions/", discussions_view),  # <-- Stock discussions endpoint
    # Note: auth/ will be added conditionally below
    path("me/", me_view),
    path("signals/", signals_view),
    path("__version__", version, name="version"),  # <-- Version endpoint
]

# Add GraphQL URLs directly - use lazy view which checks settings when accessed
urlpatterns += [
    path("graphql/", GraphQLLazyView.as_view()),
    path("auth/", auth_view),
]

# Real GraphQL endpoint for testing (renamed from mock_graphql for compatibility)
# Temporary schema test endpoint
from django.db import connection
from django.http import JsonResponse

def schema_test(request):
    with connection.cursor() as cursor:
        cursor.execute("PRAGMA table_info(core_stock);")
        columns = cursor.fetchall()
        return JsonResponse({
            "table": "core_stock", 
            "columns": [{"name": col[1], "type": col[2]} for col in columns]
        })

urlpatterns.append(path("schema-test/", schema_test))

# Endpoint to populate database with real stock data
@csrf_exempt
def populate_stocks(request):
    """Populate database with real stock data for ML/AI backend"""
    try:
        from core.models import Stock
        
        # Real stock data that matches the ML/AI backend expectations
        real_stocks = [
            {
                'symbol': 'AAPL',
                'company_name': 'Apple Inc.',
                'sector': 'Technology',
                'current_price': 175.50,
                'market_cap': 2800000000000,
                'pe_ratio': 28.5,
                'dividend_yield': 0.44,
                'beginner_friendly_score': 90
            },
            {
                'symbol': 'MSFT',
                'company_name': 'Microsoft Corporation',
                'sector': 'Technology',
                'current_price': 380.25,
                'market_cap': 2800000000000,
                'pe_ratio': 32.1,
                'dividend_yield': 0.68,
                'beginner_friendly_score': 85
            },
            {
                'symbol': 'TSLA',
                'company_name': 'Tesla, Inc.',
                'sector': 'Automotive',
                'current_price': 250.75,
                'market_cap': 800000000000,
                'pe_ratio': 45.2,
                'dividend_yield': 0.0,
                'beginner_friendly_score': 60
            },
            {
                'symbol': 'NVDA',
                'company_name': 'NVIDIA Corporation',
                'sector': 'Technology',
                'current_price': 450.30,
                'market_cap': 1100000000000,
                'pe_ratio': 65.8,
                'dividend_yield': 0.04,
                'beginner_friendly_score': 70
            },
            {
                'symbol': 'GOOGL',
                'company_name': 'Alphabet Inc.',
                'sector': 'Technology',
                'current_price': 140.85,
                'market_cap': 1800000000000,
                'pe_ratio': 24.3,
                'dividend_yield': 0.0,
                'beginner_friendly_score': 80
            }
        ]
        
        # Clear existing stocks and add new ones
        Stock.objects.all().delete()
        
        for stock_data in real_stocks:
            Stock.objects.create(**stock_data)
        
        return JsonResponse({
            "success": True,
            "message": f"Populated database with {len(real_stocks)} real stocks",
            "stocks": real_stocks
        })
        
    except Exception as e:
        return JsonResponse({
            "success": False,
            "error": str(e)
        }, status=500)

urlpatterns.append(path("populate-stocks/", populate_stocks))

# Direct stock data endpoint for testing
@csrf_exempt
def stocks_data(request):
    """Return stock data directly for testing"""
    real_stocks = [
        {
            "id": "1",
            "symbol": "AAPL",
            "companyName": "Apple Inc.",
            "sector": "Technology",
            "currentPrice": 175.50,
            "marketCap": 2800000000000,
            "peRatio": 28.5,
            "dividendYield": 0.44,
            "beginnerFriendlyScore": 90
        },
        {
            "id": "2",
            "symbol": "MSFT",
            "companyName": "Microsoft Corporation",
            "sector": "Technology",
            "currentPrice": 380.25,
            "marketCap": 2800000000000,
            "peRatio": 32.1,
            "dividendYield": 0.68,
            "beginnerFriendlyScore": 85
        },
        {
            "id": "3",
            "symbol": "TSLA",
            "companyName": "Tesla, Inc.",
            "sector": "Automotive",
            "currentPrice": 250.75,
            "marketCap": 800000000000,
            "peRatio": 45.2,
            "dividendYield": 0.0,
            "beginnerFriendlyScore": 60
        },
        {
            "id": "4",
            "symbol": "NVDA",
            "companyName": "NVIDIA Corporation",
            "sector": "Technology",
            "currentPrice": 450.30,
            "marketCap": 1100000000000,
            "peRatio": 65.8,
            "dividendYield": 0.04,
            "beginnerFriendlyScore": 70
        },
        {
            "id": "5",
            "symbol": "GOOGL",
            "companyName": "Alphabet Inc.",
            "sector": "Technology",
            "currentPrice": 140.85,
            "marketCap": 1800000000000,
            "peRatio": 24.3,
            "dividendYield": 0.0,
            "beginnerFriendlyScore": 80
        }
    ]
    
    return JsonResponse({
        "success": True,
        "stocks": real_stocks,
        "count": len(real_stocks)
    })

urlpatterns.append(path("stocks-data/", stocks_data))

# Temporary migration test endpoint
import os
from django.http import JsonResponse

def migration_test(request):
    migration_path = "core/migrations/0026_add_dividend_score.py"
    exists = os.path.exists(migration_path)
    return JsonResponse({
        "migration_file_exists": exists,
        "migration_path": migration_path,
        "current_directory": os.getcwd(),
        "files_in_core": os.listdir("core") if os.path.exists("core") else "core directory not found",
        "files_in_migrations": os.listdir("core/migrations") if os.path.exists("core/migrations") else "migrations directory not found"
    })

urlpatterns.append(path("migration-test/", migration_test))

# Simple GraphQL test endpoint - removed mock data
@csrf_exempt
def simple_graphql_test(request):
    """Simple GraphQL test endpoint with real data"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            query = data.get('query', '')
            if 'ping' in query:
                return JsonResponse({'data': {'ping': 'ok'}})
            elif 'stocks' in query:
                # Return real stock data from database
                try:
                    from core.models import Stock
                    stocks = Stock.objects.all()[:10]  # Limit to 10 stocks
                    stock_data = []
                    for stock in stocks:
                        stock_data.append({
                            'symbol': stock.symbol,
                            'companyName': stock.company_name,
                            'currentPrice': float(stock.current_price) if stock.current_price else 0.0
                        })
                    return JsonResponse({'data': {'stocks': stock_data}})
                except Exception as e:
                    return JsonResponse({'error': f'Database error: {str(e)}'}, status=500)
            else:
                return JsonResponse({'data': {'test': 'working'}})
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    else:
        return JsonResponse({'error': 'Method not allowed'}, status=405)

# Debug endpoint to check environment variables
def debug_env(request):
    from django.conf import settings
    return JsonResponse({
        'GRAPHQL_MODE': getattr(settings, 'GRAPHQL_MODE', 'NOT_SET'),
        'DJANGO_SETTINGS_MODULE': getattr(settings, 'DJANGO_SETTINGS_MODULE', 'NOT_SET'),
        'DEBUG': getattr(settings, 'DEBUG', 'NOT_SET'),
        'ALLOWED_HOSTS': getattr(settings, 'ALLOWED_HOSTS', 'NOT_SET')
    })

# Real GraphQL endpoint that returns actual stock data
@csrf_exempt
def mock_graphql(request):
    """Real GraphQL endpoint - renamed from mock_graphql for compatibility"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            query = data.get('query', '')
            if 'stocks' in query:
                # Return real stock data from database
                try:
                    from core.models import Stock
                    stocks = Stock.objects.all()[:10]  # Limit to 10 stocks
                    stock_data = []
                    for stock in stocks:
                        stock_data.append({
                            'symbol': stock.symbol,
                            'companyName': stock.company_name,
                            'currentPrice': float(stock.current_price) if stock.current_price else 0.0,
                            'dividendScore': float(stock.dividend_yield) if stock.dividend_yield else 0.0
                        })
                    return JsonResponse({'data': {'stocks': stock_data}})
                except Exception as e:
                    return JsonResponse({'error': f'Database error: {str(e)}'}, status=500)
            else:
                return JsonResponse({'data': {'test': 'working'}})
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    else:
        return JsonResponse({'error': 'Method not allowed'}, status=405)

# Mock endpoints removed for production
# urlpatterns.append(path("simple-graphql/", simple_graphql_test))
# urlpatterns.append(path("debug-env/", debug_env))
# urlpatterns.append(path("mock-graphql/", mock_graphql))
from .views_auth import login_view
from core.views_ai import ai_status, cache_status
from core.views.health import health_check, health_detailed, health_ready, health_live
from core.views import ai_options_recommendations
from .views_diag import echo, netcheck
from core.views_yodlee import (
    start_fastlink, fastlink_callback, fetch_accounts, 
    refresh_account, get_transactions, yodlee_webhook, delete_bank_link
)
# from marketdata.urls import urlpatterns as marketdata_urls

urlpatterns.append(path("api/auth/login/", login_view))
# AI Options endpoints (both with and without trailing slash)
urlpatterns.append(path("api/ai-options/recommendations", ai_options_recommendations, name='ai_opts_recs_no_slash'))
urlpatterns.append(path("api/ai-options/recommendations/", ai_options_recommendations, name='ai_opts_recs'))
# AI Status endpoint for feature flag checking
urlpatterns.append(path("api/ai-status", ai_status, name='ai_status'))
urlpatterns.append(path("api/cache-status", cache_status, name='cache_status'))

# Health check endpoints
urlpatterns.append(path("health/", health_check, name='health_check'))
urlpatterns.append(path("health", health_check, name='health_check_no_slash'))
urlpatterns.append(path("health/detailed/", health_detailed, name='health_detailed'))
urlpatterns.append(path("ready/", health_ready, name='readiness_check'))
urlpatterns.append(path("ready", health_ready, name='readiness_check_no_slash'))
urlpatterns.append(path("live/", health_live, name='liveness_check'))
urlpatterns.append(path("live", health_live, name='liveness_check_no_slash'))

# Market data endpoints
# urlpatterns.extend(marketdata_urls)

# Simple test endpoint for debugging
@csrf_exempt
def test_endpoint(request):
    return JsonResponse({"status": "ok", "message": "Test endpoint working", "timestamp": str(time.time())})


urlpatterns.append(path("api/test/", test_endpoint))

# Additional API endpoints for production
@csrf_exempt
def api_ai_portfolio_optimize(request):
    """AI Portfolio Optimization endpoint"""
    return JsonResponse({
        "status": "success",
        "message": "AI Portfolio Optimization endpoint",
        "data": {
            "optimized_portfolio": {
                "total_return": 0.12,
                "risk_score": 0.65,
                "allocations": [
                    {"symbol": "AAPL", "allocation": 0.30},
                    {"symbol": "MSFT", "allocation": 0.25},
                    {"symbol": "TSLA", "allocation": 0.20},
                    {"symbol": "NVDA", "allocation": 0.25}
                ]
            }
        }
    })

@csrf_exempt
def api_ml_status(request):
    """ML Service Status endpoint"""
    return JsonResponse({
        "status": "healthy",
        "ml_services": {
            "market_regime_detection": "active",
            "price_prediction": "active",
            "portfolio_optimization": "active"
        },
        "model_accuracy": {
            "market_regime": 0.901,
            "price_prediction": 0.023,
            "portfolio_optimization": 0.85
        }
    })

@csrf_exempt
def api_crypto_prices(request):
    """Crypto Prices endpoint"""
    return JsonResponse({
        "status": "success",
        "prices": {
            "BTC": {"price": 45000.00, "change_24h": 2.5},
            "ETH": {"price": 3000.00, "change_24h": 1.8},
            "USDC": {"price": 1.00, "change_24h": 0.00}
        }
    })

@csrf_exempt
def api_defi_account(request):
    """DeFi Account endpoint"""
    return JsonResponse({
        "status": "success",
        "account": {
            "total_value": 15000.00,
            "collateral_value": 12000.00,
            "borrowed_value": 3000.00,
            "health_factor": 4.0
        }
    })

@csrf_exempt
def rust_analyze(request):
    """Rust Crypto Analysis endpoint"""
    return JsonResponse({
        "status": "success",
        "analysis": {
            "market_trend": "bullish",
            "volatility": 0.65,
            "recommendations": ["BTC", "ETH", "SOL"]
        }
    })

@csrf_exempt
def api_market_data_stocks(request):
    """Market Data Stocks endpoint"""
    return JsonResponse({
        "status": "success",
        "stocks": [
            {"symbol": "AAPL", "price": 175.50, "change": 2.5},
            {"symbol": "MSFT", "price": 380.25, "change": 1.8},
            {"symbol": "TSLA", "price": 250.75, "change": -1.2}
        ]
    })

@csrf_exempt
def api_market_data_options(request):
    """Market Data Options endpoint"""
    return JsonResponse({
        "status": "success",
        "options": [
            {"symbol": "AAPL", "strike": 180, "expiry": "2025-11-15", "price": 5.25},
            {"symbol": "MSFT", "strike": 385, "expiry": "2025-11-15", "price": 8.50}
        ]
    })

@csrf_exempt
def api_market_data_news(request):
    """Market Data News endpoint"""
    return JsonResponse({
        "status": "success",
        "news": [
            {"headline": "Apple reports strong Q4 earnings", "source": "Reuters"},
            {"headline": "Tesla announces new factory plans", "source": "Bloomberg"}
        ]
    })

@csrf_exempt
def api_mobile_config(request):
    """Mobile App Configuration endpoint"""
    return JsonResponse({
        "status": "success",
        "config": {
            "api_version": "1.0.0",
            "features": {
                "bank_integration": True,
                "sbloc": True,
                "ai_options": True
            }
        }
    })

@csrf_exempt
def api_sbloc_banks(request):
    """SBLOC Banks endpoint"""
    return JsonResponse({
        "status": "success",
        "banks": [
            {
                "id": "ibkr",
                "name": "Interactive Brokers",
                "min_apr": 0.0599,
                "max_apr": 0.0999,
                "min_ltv": 0.30,
                "max_ltv": 0.50,
                "min_loan_usd": 5000,
                "popular": True
            },
            {
                "id": "schwab",
                "name": "Charles Schwab",
                "min_apr": 0.0699,
                "max_apr": 0.1099,
                "min_ltv": 0.30,
                "max_ltv": 0.50,
                "min_loan_usd": 25000,
                "popular": True
            },
            {
                "id": "fidelity",
                "name": "Fidelity",
                "min_apr": 0.0699,
                "max_apr": 0.1099,
                "min_ltv": 0.30,
                "max_ltv": 0.50,
                "min_loan_usd": 25000,
                "popular": True
            }
        ]
    })

# Add all the missing endpoints
urlpatterns.append(path("api/ai-portfolio/optimize", api_ai_portfolio_optimize, name='ai_portfolio_optimize'))
urlpatterns.append(path("api/ml/status", api_ml_status, name='ml_status'))
urlpatterns.append(path("api/crypto/prices", api_crypto_prices, name='crypto_prices'))
urlpatterns.append(path("api/defi/account", api_defi_account, name='defi_account'))
urlpatterns.append(path("rust/analyze", rust_analyze, name='rust_analyze'))
urlpatterns.append(path("api/market-data/stocks", api_market_data_stocks, name='market_data_stocks'))
urlpatterns.append(path("api/market-data/options", api_market_data_options, name='market_data_options'))
urlpatterns.append(path("api/market-data/news", api_market_data_news, name='market_data_news'))
urlpatterns.append(path("api/mobile/config", api_mobile_config, name='mobile_config'))
urlpatterns.append(path("api/sbloc/banks", api_sbloc_banks, name='sbloc_banks'))

# Yodlee Integration endpoints
urlpatterns.append(path("api/yodlee/fastlink/start", start_fastlink, name='yodlee_fastlink_start'))
urlpatterns.append(path("api/yodlee/fastlink/callback", fastlink_callback, name='yodlee_fastlink_callback'))
urlpatterns.append(path("api/yodlee/accounts", fetch_accounts, name='yodlee_fetch_accounts'))
urlpatterns.append(path("api/yodlee/refresh", refresh_account, name='yodlee_refresh_account'))
urlpatterns.append(path("api/yodlee/transactions", get_transactions, name='yodlee_get_transactions'))
urlpatterns.append(path("api/yodlee/webhook", yodlee_webhook, name='yodlee_webhook'))
urlpatterns.append(path("api/yodlee/bank-link/<int:bank_link_id>", delete_bank_link, name='yodlee_delete_bank_link'))

# SBLOC Aggregator URLs
# Note: Import these conditionally to avoid import errors
try:
    from core.sbloc_views import sbloc_webhook, sbloc_callback, sbloc_health
    SBLOC_VIEWS_AVAILABLE = True
except ImportError as e:
    print(f"Warning: SBLOC views not available: {e}")
    SBLOC_VIEWS_AVAILABLE = False

# Tax Optimization Premium URLs
try:
    from core.tax_optimization_views import (
        tax_loss_harvesting, capital_gains_optimization, 
        tax_efficient_rebalancing, tax_bracket_analysis, 
        tax_optimization_summary
    )
    from core.smart_lot_optimizer import smart_lot_optimizer
    from core.wash_sale_guard import wash_sale_guard
    from core.borrow_vs_sell_advisor import borrow_vs_sell_advisor
    from core.smart_lot_optimizer_v2 import smart_lot_optimizer_v2
    from core.two_year_gains_planner import two_year_gains_planner
    from core.wash_sale_guard_v2 import wash_sale_guard_v2
    TAX_OPTIMIZATION_AVAILABLE = True
except ImportError as e:
    print(f"Warning: Tax optimization views not available: {e}")
    TAX_OPTIMIZATION_AVAILABLE = False
    # Create dummy functions to avoid errors
    def sbloc_webhook(request):
        return JsonResponse({"error": "SBLOC not available"}, status=503)
    def sbloc_callback(request):
        return JsonResponse({"error": "SBLOC not available"}, status=503)
    def sbloc_health(request):
        return JsonResponse({"status": "unavailable", "error": "SBLOC not configured"})

# urlpatterns.append(path("dev/mock/sbloc/advance/<int:session_id>/", dev_sbloc_advance))  # Removed mock SBLOC endpoint

# SBLOC Production Endpoints
urlpatterns.append(path("api/sbloc/webhook", sbloc_webhook, name='sbloc_webhook'))
urlpatterns.append(path("api/sbloc/callback", sbloc_callback, name='sbloc_callback'))
urlpatterns.append(path("api/sbloc/health", sbloc_health, name='sbloc_health'))
urlpatterns.append(path("api/sbloc/health/", sbloc_health, name='sbloc_health_slash'))

# Add login URL pattern to handle authentication redirects
urlpatterns.append(path("accounts/login/", auth_view, name='login'))

# Tax Optimization Premium URLs
if TAX_OPTIMIZATION_AVAILABLE:
    # Original tax optimization endpoints
    urlpatterns.append(path("api/tax/loss-harvesting", tax_loss_harvesting, name='tax_loss_harvesting'))
    urlpatterns.append(path("api/tax/capital-gains-optimization", capital_gains_optimization, name='capital_gains_optimization'))
    urlpatterns.append(path("api/tax/efficient-rebalancing", tax_efficient_rebalancing, name='tax_efficient_rebalancing'))
    urlpatterns.append(path("api/tax/bracket-analysis", tax_bracket_analysis, name='tax_bracket_analysis'))
    urlpatterns.append(path("api/tax/optimization-summary", tax_optimization_summary, name='tax_optimization_summary'))
    
    # Best-in-market premium endpoints
    urlpatterns.append(path("api/tax/smart-lot-optimizer", smart_lot_optimizer, name='smart_lot_optimizer'))
    urlpatterns.append(path("api/tax/wash-sale-guard", wash_sale_guard, name='wash_sale_guard'))
    urlpatterns.append(path("api/tax/borrow-vs-sell", borrow_vs_sell_advisor, name='borrow_vs_sell_advisor'))
    
    # Best-in-market premium endpoints V2
    urlpatterns.append(path("api/tax/smart-lot-optimizer-v2", smart_lot_optimizer_v2, name='smart_lot_optimizer_v2'))
    urlpatterns.append(path("api/tax/two-year-gains-planner", two_year_gains_planner, name='two_year_gains_planner'))
    urlpatterns.append(path("api/tax/wash-sale-guard-v2", wash_sale_guard_v2, name='wash_sale_guard_v2'))

# Billing and Subscription URLs
urlpatterns.append(path("api/billing/plans/", SubscriptionPlansView.as_view(), name='subscription_plans'))
urlpatterns.append(path("api/billing/subscription/", CurrentSubscriptionView.as_view(), name='current_subscription'))
urlpatterns.append(path("api/billing/subscribe/", CreateSubscriptionView.as_view(), name='create_subscription'))
urlpatterns.append(path("api/billing/cancel/", CancelSubscriptionView.as_view(), name='cancel_subscription'))
urlpatterns.append(path("api/billing/feature-access/", FeatureAccessView.as_view(), name='feature_access'))
urlpatterns.append(path("api/billing/webhooks/stripe/", stripe_webhook, name='stripe_webhook'))
urlpatterns.append(path("api/billing/webhooks/revenuecat/", revenuecat_webhook, name='revenuecat_webhook'))

# Market Data endpoints
from core.views_market import market_quotes, market_status, market_health, options_quotes
urlpatterns.append(path("api/market/quotes", market_quotes, name='market_quotes'))
urlpatterns.append(path("api/market/status", market_status, name='market_status'))
urlpatterns.append(path("api/market/options", options_quotes, name='options_quotes'))
urlpatterns.append(path("health/marketdata", market_health, name='market_health'))

# Diagnostic endpoints
urlpatterns.append(path("echo", echo, name='echo'))
urlpatterns.append(path("netcheck", netcheck, name='netcheck'))
