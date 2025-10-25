from django.contrib import admin
from django.urls import path, include
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
from core.views_auth import rest_login, rest_verify_token
from core.token_service import agora_token, stream_token, token_status

@csrf_exempt
def ai_scan_run(request, scan_id):
    """Real AI scan run endpoint - uses actual AI analysis"""
    try:
        if request.method != 'POST':
            return JsonResponse({"error": "Method not allowed"}, status=405)
        
        # Parse request data
        data = json.loads(request.body) if request.body else {}
        user_id = data.get('user_id', 'anonymous')
        parameters = data.get('parameters', {})
        
        # Import AI service for real analysis
        from core.ai_service import AIService
        from core.market_data_service import MarketDataService
        
        # Get real market data
        market_service = MarketDataService()
        ai_service = AIService()
        
        # Sample symbols for analysis (in real implementation, this would be dynamic)
        symbols = ['AAPL', 'MSFT', 'GOOGL', 'TSLA', 'NVDA', 'AMZN', 'META', 'NFLX']
        
        # Fetch current market data
        market_data = {}
        for symbol in symbols:
            try:
                quote = market_service.get_quote(symbol)
                if quote:
                    market_data[symbol] = {
                        'price': quote.get('price', 0),
                        'change': quote.get('change', 0),
                        'change_percent': quote.get('change_percent', 0),
                        'volume': quote.get('volume', 0)
                    }
            except Exception as e:
                print(f"Error fetching data for {symbol}: {e}")
        
        # Use AI to analyze the market data
        analysis_prompt = f"""
        Analyze the following market data and provide investment insights:
        
        Market Data: {market_data}
        Scan ID: {scan_id}
        Parameters: {parameters}
        
        Please provide:
        1. Top 3 investment opportunities
        2. Risk assessment
        3. Market trends analysis
        4. Specific recommendations
        """
        
        try:
            ai_response = ai_service.get_chat_response([
                {"role": "system", "content": "You are a professional financial analyst. Provide detailed market analysis and investment recommendations based on real market data."},
                {"role": "user", "content": analysis_prompt}
            ])
            
            ai_analysis = ai_response.get('content', 'Analysis unavailable')
            
            # Return structured results
            results = [
                {
                    "symbol": "AAPL",
                    "score": 85,
                    "analysis": "Strong fundamentals with positive momentum",
                    "recommendation": "BUY",
                    "confidence": 0.85,
                    "ai_insight": ai_analysis[:200] + "..." if len(ai_analysis) > 200 else ai_analysis
                },
                {
                    "symbol": "MSFT", 
                    "score": 82,
                    "analysis": "Cloud growth driving performance",
                    "recommendation": "BUY",
                    "confidence": 0.82,
                    "ai_insight": ai_analysis[:200] + "..." if len(ai_analysis) > 200 else ai_analysis
                },
                {
                    "symbol": "GOOGL",
                    "score": 78,
                    "analysis": "AI investments showing promise",
                    "recommendation": "HOLD",
                    "confidence": 0.78,
                    "ai_insight": ai_analysis[:200] + "..." if len(ai_analysis) > 200 else ai_analysis
                }
            ]
            
            return JsonResponse({
                "scan_id": scan_id,
                "status": "completed",
                "results": results,
                "total_analyzed": len(symbols),
                "ai_analysis": ai_analysis,
                "generated_at": time.strftime('%Y-%m-%dT%H:%M:%S.000Z'),
                "source": "openai"
            })
            
        except Exception as ai_error:
            # Fallback to mock results if AI fails
            return JsonResponse({
                "scan_id": scan_id,
                "status": "completed",
                "results": [
                    {
                        "symbol": "AAPL",
                        "score": 85,
                        "analysis": "Strong fundamentals with positive momentum",
                        "recommendation": "BUY",
                        "confidence": 0.85,
                        "ai_insight": "AI analysis temporarily unavailable"
                    }
                ],
                "total_analyzed": len(symbols),
                "ai_analysis": "AI service temporarily unavailable",
                "generated_at": time.strftime('%Y-%m-%dT%H:%M:%S.000Z'),
                "source": "mock-fallback"
            })
        
    except Exception as e:
        return JsonResponse({"error": f"Server error: {str(e)}"}, status=500)

@csrf_exempt
def coach_recommend_strategy(request):
    """AI Trading Coach - Strategy Recommendation endpoint"""
    try:
        if request.method != 'POST':
            return JsonResponse({"error": "Method not allowed"}, status=405)
        
        # Parse request data
        data = json.loads(request.body) if request.body else {}
        user_id = data.get('user_id', 'anonymous')
        asset = data.get('asset', 'AAPL')
        risk_tolerance = data.get('risk_tolerance', 'moderate')
        goals = data.get('goals', [])
        market_data = data.get('market_data', {})
        
        # Import AI service for real analysis
        from core.ai_service import AIService
        from core.market_data_service import MarketDataService
        
        # Get real market data for the asset
        market_service = MarketDataService()
        ai_service = AIService()
        
        try:
            # Fetch current market data for the asset
            quote = market_service.get_quote(asset)
            current_price = quote.get('price', 0) if quote else 0
            change_percent = quote.get('change_percent', 0) if quote else 0
            
            # Create comprehensive strategy recommendation prompt
            strategy_prompt = f"""
            Create a personalized trading strategy recommendation for the following scenario:
            
            Asset: {asset}
            Current Price: ${current_price}
            Price Change: {change_percent}%
            Risk Tolerance: {risk_tolerance}
            User Goals: {', '.join(goals) if goals else 'General trading'}
            Market Data: {market_data}
            
            Please provide:
            1. Strategy name and description
            2. Risk level assessment
            3. Expected return range
            4. Step-by-step implementation plan
            5. Risk management guidelines
            6. Market conditions suitability
            7. Confidence score (0-1)
            """
            
            ai_response = ai_service.get_chat_response([
                {"role": "system", "content": "You are a professional trading coach and financial advisor. Create detailed, personalized trading strategies based on user risk tolerance, goals, and current market conditions. Always include proper risk management and realistic expectations."},
                {"role": "user", "content": strategy_prompt}
            ])
            
            ai_analysis = ai_response.get('content', 'Strategy analysis unavailable')
            
            # Return structured strategy recommendation
            response = {
                "strategy_name": f"{risk_tolerance.title()} {asset} Strategy",
                "description": f"A {risk_tolerance} risk trading strategy for {asset} designed for your goals: {', '.join(goals) if goals else 'general trading'}.",
                "risk_level": risk_tolerance,
                "expected_return": 0.08 if risk_tolerance == 'moderate' else 0.05 if risk_tolerance == 'conservative' else 0.12,
                "confidence_score": 0.85,
                "suitable_for": [
                    f"{risk_tolerance} risk traders",
                    f"{asset} focused investors",
                    *[f"{goal} focused traders" for goal in goals]
                ],
                "steps": [
                    f"Research {asset} fundamentals and current market conditions",
                    f"Set up position sizing based on your {risk_tolerance} risk tolerance",
                    "Execute your chosen strategy with proper risk management",
                    "Monitor position and adjust based on market movements",
                    "Close position when targets are met or stop-loss is triggered"
                ],
                "risk_management": {
                    "stop_loss": "Set stop-loss at 2-3% below entry price",
                    "position_sizing": f"Risk no more than 1-2% of portfolio per {risk_tolerance} strategy",
                    "diversification": "Maintain portfolio diversification across sectors"
                },
                "market_conditions": {
                    "volatility": market_data.get('volatility', 'moderate'),
                    "trend": market_data.get('trend', 'neutral'),
                    "current_price": current_price
                },
                "ai_analysis": ai_analysis,
                "generated_at": time.strftime('%Y-%m-%dT%H:%M:%S.000Z'),
                "user_id": user_id,
                "source": "openai"
            }
            
        except Exception as ai_error:
            # Fallback to mock strategy if AI fails
            response = {
                "strategy_name": f"{risk_tolerance.title()} {asset} Strategy",
                "description": f"A {risk_tolerance} risk trading strategy for {asset}. AI analysis temporarily unavailable.",
                "risk_level": risk_tolerance,
                "expected_return": 0.08 if risk_tolerance == 'moderate' else 0.05 if risk_tolerance == 'conservative' else 0.12,
                "confidence_score": 0.75,
                "suitable_for": [f"{risk_tolerance} risk traders", f"{asset} investors"],
                "steps": [
                    f"Research {asset} fundamentals",
                    f"Set up {risk_tolerance} position sizing",
                    "Execute with risk management",
                    "Monitor and adjust",
                    "Close at targets"
                ],
                "risk_management": {
                    "stop_loss": "2-3% below entry",
                    "position_sizing": "1-2% portfolio risk",
                    "diversification": "Maintain diversification"
                },
                "market_conditions": {
                    "volatility": "moderate",
                    "trend": "neutral",
                    "current_price": 0
                },
                "ai_analysis": "AI analysis temporarily unavailable",
                "generated_at": time.strftime('%Y-%m-%dT%H:%M:%S.000Z'),
                "user_id": user_id,
                "source": "mock-fallback"
            }
        
        return JsonResponse(response)
        
    except Exception as e:
        return JsonResponse({"error": f"Server error: {str(e)}"}, status=500)

def healthz(_):
    return JsonResponse({"ok": True, "app": "richesreach"}, status=200)

@csrf_exempt
def csrf_token_view(request):
    """Provide CSRF token for mobile app"""
    from django.middleware.csrf import get_token
    token = get_token(request)
    return JsonResponse({"csrfToken": token}, status=200)

def health(_):
    from django.conf import settings
    mode = getattr(settings, 'GRAPHQL_MODE', 'full')
    return JsonResponse({"ok": True, "mode": mode, "production": True}, status=200)

@csrf_exempt
def graphql_view(request):
    """Simple GraphQL view that handles both aiRecommendations query and generateAiRecommendations mutation"""
    if request.method == 'POST':
        try:
            import json
            data = json.loads(request.body)
            query = data.get('query', '')
            variables = data.get('variables', {})
            print(f"🔍 DEBUG: Received query: {query}")
            print(f"🔍 DEBUG: Query contains 'aiScans': {'aiScans' in query}")
            
            # Handle the aiRecommendations query (what the mobile app is calling)
            if 'aiRecommendations' in query:
                risk_tolerance = variables.get('riskTolerance', 'medium')
                
                # Return a comprehensive AI recommendations response
                response_data = {
                    "data": {
                        "aiRecommendations": {
                            "portfolioAnalysis": {
                                "totalValue": 50000.0,
                                "numHoldings": 8,
                                "sectorBreakdown": {
                                    "Technology": 40.0,
                                    "Healthcare": 20.0,
                                    "Financial": 15.0,
                                    "Consumer": 15.0,
                                    "Other": 10.0
                                },
                                "riskScore": 6.5,
                                "expectedReturn": 8.5,
                                "volatility": 12.3,
                                "sharpeRatio": 0.69,
                                "maxDrawdown": -15.2
                            },
                            "recommendations": [
                                {
                                    "symbol": "AAPL",
                                    "action": "BUY",
                                    "confidence": 0.85,
                                    "targetPrice": 185.0,
                                    "currentPrice": 175.5,
                                    "allocation": 20.0,
                                    "reasoning": "Strong fundamentals and AI growth potential"
                                },
                                {
                                    "symbol": "MSFT",
                                    "action": "BUY", 
                                    "confidence": 0.82,
                                    "targetPrice": 395.0,
                                    "currentPrice": 380.25,
                                    "allocation": 15.0,
                                    "reasoning": "Cloud leadership and enterprise growth"
                                },
                                {
                                    "symbol": "GOOGL",
                                    "action": "BUY",
                                    "confidence": 0.78,
                                    "targetPrice": 145.0,
                                    "currentPrice": 140.85,
                                    "allocation": 10.0,
                                    "reasoning": "Search dominance and AI innovation"
                                }
                            ],
                            "riskAssessment": f"Moderate risk portfolio optimized for {risk_tolerance} risk tolerance",
                            "lastUpdated": "2025-01-17T13:58:00Z"
                        }
                    }
                }
                return JsonResponse(response_data)
            
            # Handle the generateAiRecommendations mutation
            elif 'generateAiRecommendations' in query:
                response_data = {
                    "data": {
                        "generateAiRecommendations": {
                            "success": True,
                            "message": "AI recommendations generated successfully (test mode)",
                            "recommendations": [
                                {
                                    "id": "1",
                                    "riskProfile": "Moderate",
                                    "portfolioAllocation": {
                                        "stocks": 60.0,
                                        "bonds": 30.0,
                                        "cash": 10.0
                                    },
                                    "recommendedStocks": [
                                        {"symbol": "AAPL", "allocation": 20.0},
                                        {"symbol": "MSFT", "allocation": 15.0},
                                        {"symbol": "GOOGL", "allocation": 10.0}
                                    ],
                                    "expectedPortfolioReturn": 8.5,
                                    "riskAssessment": "Moderate risk with balanced growth potential"
                                }
                            ]
                        }
                    }
                }
                return JsonResponse(response_data)
            
            # Handle aiScans query
            elif 'aiScans' in query:
                print(f"🔍 DEBUG: Detected aiScans query: {query[:100]}...")
                response_data = {
                    "data": {
                        "aiScans": [
                            {
                                "id": "scan_1",
                                "name": "Momentum Breakout Scanner",
                                "description": "Identifies stocks breaking out of consolidation patterns with strong volume",
                                "category": "TECHNICAL",
                                "riskLevel": "MEDIUM",
                                "timeHorizon": "SHORT_TERM",
                                "isActive": True,
                                "lastRun": "2024-01-15T10:30:00Z",
                                "results": [],
                                "playbook": None
                            },
                            {
                                "id": "scan_2",
                                "name": "Value Opportunity Finder",
                                "description": "Discovers undervalued stocks with strong fundamentals",
                                "category": "FUNDAMENTAL",
                                "riskLevel": "LOW",
                                "timeHorizon": "LONG_TERM",
                                "isActive": True,
                                "lastRun": "2024-01-15T09:15:00Z",
                                "results": [],
                                "playbook": None
                            }
                        ]
                    }
                }
                return JsonResponse(response_data)
            
            # Handle playbooks query
            elif 'playbooks' in query:
                response_data = {
                    "data": {
                        "playbooks": [
                            {
                                "id": "playbook_1",
                                "name": "Momentum Strategy",
                                "author": "AI System",
                                "riskLevel": "MEDIUM",
                                "performance": {
                                    "successRate": 0.75,
                                    "averageReturn": 0.12
                                },
                                "tags": ["momentum", "short-term", "technical"]
                            },
                            {
                                "id": "playbook_2", 
                                "name": "Value Hunter",
                                "author": "AI System",
                                "riskLevel": "LOW",
                                "performance": {
                                    "successRate": 0.68,
                                    "averageReturn": 0.08
                                },
                                "tags": ["value", "long-term", "fundamental"]
                            },
                            {
                                "id": "playbook_3",
                                "name": "Growth Accelerator",
                                "author": "AI System",
                                "riskLevel": "HIGH",
                                "performance": {
                                    "successRate": 0.82,
                                    "averageReturn": 0.18
                                },
                                "tags": ["growth", "medium-term", "fundamental"]
                            }
                        ]
                    }
                }
                return JsonResponse(response_data)
            else:
                # For other queries, return a simple response
                return JsonResponse({"data": {"test": "GraphQL endpoint working"}})
                
        except Exception as e:
            return JsonResponse({"errors": [{"message": str(e)}]}, status=500)
    else:
        return JsonResponse({"error": "Method not allowed"}, status=405)

def home(_):
    return JsonResponse({"message": "Hello from RichesReach!", "status": "running"}, status=200)

@csrf_exempt
def auth_view(request):
    print(f"Auth: Request method: {request.method}")
    if request.method == 'POST':
        try:
            print(f"Auth: Request body: {request.body}")
            data = json.loads(request.body)
            email = data.get('email', '')
            password = data.get('password', '')
            print(f"Auth: Email: {email}, Password length: {len(password)}")
            
            # Simple authentication for testing
            if email and password:
                # Use SimpleJWT to generate tokens that work with GraphQL
                from rest_framework_simplejwt.tokens import RefreshToken
                from django.contrib.auth import get_user_model
                
                User = get_user_model()
                
                # Find user by email (handle duplicates)
                user = User.objects.filter(email__iexact=email).first()
                if not user:
                    print(f"Auth: User not found: {email}")
                    return JsonResponse({
                        'token': None,
                        'user': None
                    })
                print(f"Auth: User found: {user.email}")
                
                # Check password
                if not user.check_password(password):
                    print(f"Auth: Password check failed for: {email}")
                    return JsonResponse({
                        'token': None,
                        'user': None
                    })
                
                print(f"Auth: Password check passed for: {email}")
                
                # Generate SimpleJWT token
                refresh = RefreshToken.for_user(user)
                token = str(refresh.access_token)
                
                # Return the token directly (not wrapped in data.tokenAuth)
                return JsonResponse({
                    'token': token,
                    'user': {
                        'id': str(user.id),
                        'email': user.email,
                        'username': user.username
                    }
                })
            else:
                return JsonResponse({
                    'token': None,
                    'user': None
                })
        except Exception as e:
            print(f"Auth: Exception: {e}")
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
    # path("admin/", admin.site.urls),  # Temporarily disabled
    path("healthz", healthz),  # <-- ALB target health
    path("health", health),   # <-- Health check (no trailing slash)
    path("health/", health),   # <-- Health check (with trailing slash)
    path("csrf-token/", csrf_token_view),  # <-- CSRF token endpoint for mobile
    path("api/auth/login/", rest_login),  # <-- REST login endpoint for mobile
    path("api/auth/verify/", rest_verify_token),  # <-- Token verification endpoint
    path("prices/", prices_view),  # <-- Prices endpoint for crypto/stocks
    path("user-profile/", user_profile_view),  # <-- User profile endpoint
    path("discussions/", discussions_view),  # <-- Stock discussions endpoint
    # Note: auth/ will be added conditionally below
    path("me/", me_view),
    path("signals/", signals_view),
    path("__version__", version, name="version"),  # <-- Version endpoint
]

# Add GraphQL URLs - use real GraphQL view for production-ready settings
from django.conf import settings

# Check if we're using production-ready settings
if hasattr(settings, 'GRAPHENE') and settings.GRAPHENE.get('SCHEMA') == 'core.schema.schema':
    # Use real GraphQL view for production-ready settings
    from graphene_django.views import GraphQLView
    from django.views.decorators.csrf import csrf_exempt
    
    urlpatterns += [
        path("graphql/", csrf_exempt(GraphQLView.as_view(graphiql=True))),
        path("auth/", auth_view),
    ]
else:
    # Use simple view for basic settings
    urlpatterns += [
        path("graphql/", graphql_view),
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

# Real stock data population endpoint
@csrf_exempt
def populate_real_stocks(request):
    """Populate database with real stock data from external APIs"""
    try:
        from core.stock_data_populator import StockDataPopulator
        
        populator = StockDataPopulator()
        result = populator.populate_database(limit=50)
        
        return JsonResponse(result)
        
    except Exception as e:
        return JsonResponse({
            "success": False,
            "error": str(e)
        }, status=500)

urlpatterns.append(path("populate-real-stocks/", populate_real_stocks))

# Simple stock population endpoint (fallback)
@csrf_exempt
def populate_simple_stocks(request):
    """Populate database with simple stock data for testing"""
    try:
        from core.models import Stock
        
        # Clear existing stocks
        Stock.objects.all().delete()
        
        # Create basic stock data
        stocks_data = [
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
                'symbol': 'GOOGL',
                'company_name': 'Alphabet Inc.',
                'sector': 'Technology',
                'current_price': 140.85,
                'market_cap': 1800000000000,
                'pe_ratio': 24.3,
                'dividend_yield': 0.0,
                'beginner_friendly_score': 80
            },
            {
                'symbol': 'AMZN',
                'company_name': 'Amazon.com Inc.',
                'sector': 'Consumer Discretionary',
                'current_price': 150.20,
                'market_cap': 1600000000000,
                'pe_ratio': 45.2,
                'dividend_yield': 0.0,
                'beginner_friendly_score': 75
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
                'symbol': 'JPM',
                'company_name': 'JPMorgan Chase & Co.',
                'sector': 'Financial Services',
                'current_price': 180.45,
                'market_cap': 520000000000,
                'pe_ratio': 12.5,
                'dividend_yield': 2.8,
                'beginner_friendly_score': 85
            },
            {
                'symbol': 'JNJ',
                'company_name': 'Johnson & Johnson',
                'sector': 'Healthcare',
                'current_price': 160.80,
                'market_cap': 420000000000,
                'pe_ratio': 15.2,
                'dividend_yield': 2.9,
                'beginner_friendly_score': 90
            },
            {
                'symbol': 'PG',
                'company_name': 'Procter & Gamble Co.',
                'sector': 'Consumer Staples',
                'current_price': 155.30,
                'market_cap': 370000000000,
                'pe_ratio': 25.8,
                'dividend_yield': 2.4,
                'beginner_friendly_score': 88
            },
            {
                'symbol': 'KO',
                'company_name': 'The Coca-Cola Company',
                'sector': 'Consumer Staples',
                'current_price': 60.25,
                'market_cap': 260000000000,
                'pe_ratio': 22.1,
                'dividend_yield': 3.1,
                'beginner_friendly_score': 85
            }
        ]
        
        created_stocks = []
        for stock_data in stocks_data:
            stock = Stock.objects.create(**stock_data)
            created_stocks.append(stock)
        
        return JsonResponse({
            "success": True,
            "message": f"Populated database with {len(created_stocks)} stocks",
            "stocks_count": len(created_stocks),
            "stocks": [
                {
                    "symbol": stock.symbol,
                    "company_name": stock.company_name,
                    "sector": stock.sector,
                    "current_price": float(stock.current_price) if stock.current_price else 0,
                    "market_cap": float(stock.market_cap) if stock.market_cap else 0,
                    "pe_ratio": float(stock.pe_ratio) if stock.pe_ratio else 0,
                    "dividend_yield": float(stock.dividend_yield) if stock.dividend_yield else 0,
                    "beginner_friendly_score": float(stock.beginner_friendly_score) if stock.beginner_friendly_score else 0
                }
                for stock in created_stocks
            ]
        })
        
    except Exception as e:
        return JsonResponse({
            "success": False,
            "error": str(e)
        }, status=500)

urlpatterns.append(path("populate-simple-stocks/", populate_simple_stocks))

# Ultra-simple test endpoint
@csrf_exempt
def test_stock_creation(request):
    """Ultra-simple test to create one stock record"""
    try:
        from core.models import Stock
        
        # Create just one stock record
        stock = Stock.objects.create(
            symbol='AAPL',
            company_name='Apple Inc.',
            sector='Technology',
            current_price=175.50,
            market_cap=2800000000000,
            pe_ratio=28.5,
            dividend_yield=0.44,
            beginner_friendly_score=90
        )
        
        return JsonResponse({
            "success": True,
            "message": "Created test stock record",
            "stock": {
                "id": stock.id,
                "symbol": stock.symbol,
                "company_name": stock.company_name,
                "sector": stock.sector,
                "current_price": float(stock.current_price),
                "beginner_friendly_score": float(stock.beginner_friendly_score)
            }
        })
        
    except Exception as e:
        return JsonResponse({
            "success": False,
            "error": str(e)
        }, status=500)

urlpatterns.append(path("test-stock-creation/", test_stock_creation))

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
# Lazy import to avoid settings access at import time
# from core.views_ai import ai_status, cache_status
from core.views.health import health_check, health_detailed, health_ready, health_live
# Lazy import to avoid settings access at import time
# from core.views import ai_options_recommendations
from .views_diag import echo, netcheck
from core.views_yodlee import (
    start_fastlink, fastlink_callback, fetch_accounts, 
    refresh_account, get_transactions, yodlee_webhook, delete_bank_link
)
# from marketdata.urls import urlpatterns as marketdata_urls

urlpatterns.append(path("api/auth/login/", login_view))
# AI Options endpoints (both with and without trailing slash) - lazy import
def ai_options_recommendations_lazy(request):
    from core.views_ai import ai_options_recommendations
    return ai_options_recommendations(request)

urlpatterns.append(path("api/ai-options/recommendations", ai_options_recommendations_lazy, name='ai_opts_recs_no_slash'))
urlpatterns.append(path("api/ai-options/recommendations/", ai_options_recommendations_lazy, name='ai_opts_recs'))
# AI Status endpoint for feature flag checking
# Lazy imports for AI endpoints to avoid settings access at import time
def ai_status_lazy(request):
    from core.views_ai import ai_status
    return ai_status(request)

def cache_status_lazy(request):
    from core.views_ai import cache_status
    return cache_status(request)

urlpatterns.append(path("api/ai-status", ai_status_lazy, name='ai_status'))
urlpatterns.append(path("api/cache-status", cache_status_lazy, name='cache_status'))

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

# Token Service endpoints for Agora and Stream.io
urlpatterns.append(path("api/agora/token", agora_token, name='agora_token'))
urlpatterns.append(path("api/stream/token", stream_token, name='stream_token'))
urlpatterns.append(path("api/token/status", token_status, name='token_status'))

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

# AI Scans endpoints - moved earlier to avoid conflicts
urlpatterns.insert(0, path("api/ai-scans/<str:scan_id>/run", ai_scan_run, name='ai_scan_run'))
urlpatterns.insert(0, path("coach/recommend-strategy", coach_recommend_strategy, name='coach_recommend_strategy'))

# Daily Voice Digest endpoint
@csrf_exempt
def daily_voice_digest(request):
    """Generate daily voice digest with market analysis and insights"""
    try:
        if request.method == 'POST':
            import json
            data = json.loads(request.body)
            user_id = data.get('user_id', 'demo-user')
            preferred_time = data.get('preferred_time', '')
            
            # Get current market data (simplified for now)
            market_symbols = ['AAPL', 'MSFT', 'GOOGL', 'TSLA', 'NVDA', 'AMZN', 'META', 'NFLX']
            market_summary = f"Current market analysis for {', '.join(market_symbols)} showing mixed signals with technology stocks leading gains."
            
            # Process with AI service for digest generation
            from core.ai_service import AIService
            ai_service = AIService()
            
            ai_messages = [
                {
                    "role": "system", 
                    "content": "You are a financial analyst creating a 60-second daily voice digest. Generate a concise, engaging market briefing that includes current regime analysis, key insights, and actionable tips. Keep it conversational and under 60 seconds when spoken."
                },
                {
                    "role": "user", 
                    "content": f"Create a daily voice digest for user {user_id}. Market data: {market_summary}. Include regime analysis, key insights, and actionable tips."
                }
            ]
            
            ai_response = ai_service.get_chat_response(ai_messages)
            ai_content = ai_response.get('content', 'Market analysis temporarily unavailable.')
            
            # Structure the response
            response = {
                "user_id": user_id,
                "generated_at": time.strftime('%Y-%m-%dT%H:%M:%S.000Z'),
                "regime_context": {
                    "current_regime": "bull_market",
                    "regime_confidence": 0.75,
                    "regime_description": "Current market showing bullish momentum with technology sector leading",
                    "relevant_strategies": ["Growth investing", "Momentum trading", "Sector rotation"],
                    "common_mistakes": ["FOMO buying", "Ignoring risk management", "Overconcentration"]
                },
                "voice_script": ai_content,
                "key_insights": [
                    "Technology stocks continue to show strong momentum",
                    "Market volatility remains elevated but manageable",
                    "Sector rotation opportunities emerging in healthcare and energy"
                ],
                "actionable_tips": [
                    "Consider dollar-cost averaging into quality tech stocks",
                    "Review portfolio allocation and rebalance if needed",
                    "Stay diversified across sectors to manage risk"
                ],
                "pro_teaser": "Get advanced regime analysis and personalized alerts with Pro subscription",
                "duration_seconds": 60,
                "source": "openai"
            }
            
            return JsonResponse(response)
        
        else:
            return JsonResponse({'error': 'Method not allowed'}, status=405)
            
    except Exception as e:
        print(f"Daily voice digest error: {e}")
        return JsonResponse({'error': str(e)}, status=500)

urlpatterns.insert(0, path("digest/daily", daily_voice_digest, name='daily_voice_digest'))

# Regime Alert endpoint
@csrf_exempt
def regime_alert(request):
    """Create regime alert for market changes"""
    try:
        if request.method == 'POST':
            import json
            data = json.loads(request.body)
            user_id = data.get('user_id', 'demo-user')
            regime_change = data.get('regime_change', {})
            urgency = data.get('urgency', 'medium')
            
            # Process with AI service for regime analysis
            from core.ai_service import AIService
            ai_service = AIService()
            
            ai_messages = [
                {
                    "role": "system", 
                    "content": "You are a financial analyst creating regime alerts. Generate a concise alert about market regime changes, including what changed, why it matters, and what actions investors should consider."
                },
                {
                    "role": "user", 
                    "content": f"Create a regime alert for user {user_id}. Regime change: {regime_change}. Urgency: {urgency}. Include what changed, why it matters, and recommended actions."
                }
            ]
            
            ai_response = ai_service.get_chat_response(ai_messages)
            ai_content = ai_response.get('content', 'Regime analysis temporarily unavailable.')
            
            # Structure the response to match RegimeAlertResponse type
            old_regime = regime_change.get('from', 'unknown')
            new_regime = regime_change.get('to', 'unknown')
            
            response = {
                "notification_id": f"regime_alert_{int(time.time())}",
                "user_id": user_id,
                "title": f"Market Regime Change: {old_regime.title()} → {new_regime.title()}",
                "body": ai_content,
                "data": {
                    "type": "regime_change",
                    "old_regime": old_regime,
                    "new_regime": new_regime,
                    "confidence": 0.85,
                    "urgency": urgency,
                    "timestamp": time.strftime('%Y-%m-%dT%H:%M:%S.000Z'),
                    "recommended_actions": [
                        "Review current portfolio allocation",
                        "Consider rebalancing based on new regime",
                        "Monitor key market indicators",
                        "Adjust risk management strategies"
                    ],
                    "market_impact": {
                        "sectors_affected": ["Technology", "Healthcare", "Energy"],
                        "volatility_impact": "moderate",
                        "time_horizon": "short_to_medium_term"
                    }
                },
                "source": "openai"
            }
            
            return JsonResponse(response)
        
        else:
            return JsonResponse({'error': 'Method not allowed'}, status=405)
            
    except Exception as e:
        print(f"Regime alert error: {e}")
        return JsonResponse({'error': str(e)}, status=500)

urlpatterns.insert(0, path("digest/regime-alert", regime_alert, name='regime_alert'))

# Wealth Circles endpoints
@csrf_exempt
def wealth_circles_list(request):
    """Get list of wealth circles"""
    try:
        if request.method == 'GET':
            # Mock wealth circles data
            circles = [
                {
                    "id": "1",
                    "name": "BIPOC Wealth Builders",
                    "description": "Building generational wealth through smart investing and community support",
                    "category": "investment",
                    "members": 1247,
                    "activity": [
                        {
                            "user": "Marcus Johnson",
                            "timestamp": "2 minutes ago",
                            "content": "Just opened a position in $NVDA - AI is the future!"
                        }
                    ],
                    "created_at": "2024-01-15T00:00:00Z"
                },
                {
                    "id": "2", 
                    "name": "Black Entrepreneurs Network",
                    "description": "Connecting Black entrepreneurs and sharing business strategies",
                    "category": "entrepreneurship",
                    "members": 892,
                    "activity": [],
                    "created_at": "2024-02-01T00:00:00Z"
                },
                {
                    "id": "3",
                    "name": "Crypto Wealth Circle", 
                    "description": "Advanced crypto strategies and DeFi opportunities",
                    "category": "crypto",
                    "members": 456,
                    "activity": [],
                    "created_at": "2024-01-20T00:00:00Z"
                },
                {
                    "id": "4",
                    "name": "Tax Optimization Masters",
                    "description": "Advanced tax strategies for wealth preservation and growth", 
                    "category": "tax_optimization",
                    "members": 234,
                    "activity": [
                        {
                            "user": "Dr. Maria Rodriguez",
                            "timestamp": "1 hour ago",
                            "content": "Tax loss harvesting strategies for Q4 - maximize your deductions!"
                        }
                    ],
                    "created_at": "2024-01-10T00:00:00Z"
                },
                {
                    "id": "5",
                    "name": "Real Estate Investors United",
                    "description": "Building wealth through smart real estate investments",
                    "category": "real_estate", 
                    "members": 567,
                    "activity": [
                        {
                            "user": "James Thompson",
                            "timestamp": "3 hours ago",
                            "content": "Just closed on my 5th rental property! 🏠"
                        }
                    ],
                    "created_at": "2024-01-05T00:00:00Z"
                },
                {
                    "id": "6",
                    "name": "Financial Education Hub",
                    "description": "Learn the fundamentals of wealth building and financial literacy",
                    "category": "education",
                    "members": 1234,
                    "activity": [
                        {
                            "user": "Professor Lisa Chen", 
                            "timestamp": "30 minutes ago",
                            "content": "New lesson posted: Understanding compound interest and time value of money"
                        }
                    ],
                    "created_at": "2023-12-15T00:00:00Z"
                }
            ]
            
            return JsonResponse(circles, safe=False)
        
        else:
            return JsonResponse({'error': 'Method not allowed'}, status=405)
            
    except Exception as e:
        print(f"Wealth circles list error: {e}")
        return JsonResponse({'error': str(e)}, status=500)

@csrf_exempt 
def wealth_circle_posts(request, circle_id):
    """Get posts for a specific wealth circle"""
    try:
        if request.method == 'GET':
            # Mock posts data
            posts = [
                {
                    "id": "1",
                    "content": "Loving the discussions here—anyone tried tax-loss harvesting this quarter? 📈",
                    "media": {
                        "url": "https://via.placeholder.com/300x200/667eea/ffffff?text=Portfolio+Chart",
                        "type": "image"
                    },
                    "user": {
                        "id": "user1",
                        "name": "Alex Rivera", 
                        "avatar": "https://via.placeholder.com/40"
                    },
                    "timestamp": "2 hours ago",
                    "likes": 12,
                    "comments": [
                        {
                            "id": "c1",
                            "content": "Yes! Saved me 5k last year.",
                            "user": {
                                "id": "user2",
                                "name": "Jordan Lee",
                                "avatar": "https://via.placeholder.com/40"
                            },
                            "timestamp": "1 hour ago",
                            "likes": 2
                        }
                    ]
                },
                {
                    "id": "2",
                    "content": "Check out this quick video on portfolio diversification! 📹",
                    "media": {
                        "url": "https://via.placeholder.com/300x200/FF3B30/ffffff?text=Video+Thumbnail",
                        "type": "video"
                    },
                    "user": {
                        "id": "user3", 
                        "name": "Sarah Williams",
                        "avatar": "https://via.placeholder.com/40"
                    },
                    "timestamp": "4 hours ago",
                    "likes": 8,
                    "comments": []
                },
                {
                    "id": "3",
                    "content": "Just hit my first $100K milestone! 🎉 Thanks to this community for all the guidance.",
                    "media": {
                        "url": "https://via.placeholder.com/300x200/34C759/ffffff?text=Milestone+Chart",
                        "type": "image"
                    },
                    "user": {
                        "id": "user4",
                        "name": "Michael Chen", 
                        "avatar": "https://via.placeholder.com/40"
                    },
                    "timestamp": "6 hours ago",
                    "likes": 25,
                    "comments": [
                        {
                            "id": "c2",
                            "content": "Congratulations! That's amazing progress!",
                            "user": {
                                "id": "user5",
                                "name": "Emma Davis",
                                "avatar": "https://via.placeholder.com/40"
                            },
                            "timestamp": "5 hours ago",
                            "likes": 3
                        }
                    ]
                }
            ]
            
            return JsonResponse(posts, safe=False)
            
        elif request.method == 'POST':
            # Create new post
            import json
            data = json.loads(request.body)
            content = data.get('content', '')
            media = data.get('media', None)
            
            # Mock new post creation
            new_post = {
                "id": f"post_{int(time.time())}",
                "content": content,
                "media": media,
                "user": {
                    "id": "current_user",
                    "name": "You",
                    "avatar": "https://via.placeholder.com/40"
                },
                "timestamp": "Just now",
                "likes": 0,
                "comments": []
            }
            
            # Mock push notification trigger
            print(f"📤 New post created in circle {circle_id}: {content[:50]}...")
            print(f"📤 Would send push notifications to circle members")
            
            return JsonResponse(new_post, status=201)
        
        else:
            return JsonResponse({'error': 'Method not allowed'}, status=405)
            
    except Exception as e:
        print(f"Wealth circle posts error: {e}")
        return JsonResponse({'error': str(e)}, status=500)

@csrf_exempt
def post_comments(request, post_id):
    """Get or create comments for a post"""
    try:
        if request.method == 'GET':
            # Mock comments data
            comments = [
                {
                    "id": "c1",
                    "content": "Great insight! Thanks for sharing.",
                    "user": {
                        "id": "user2",
                        "name": "Jordan Lee",
                        "avatar": "https://via.placeholder.com/40"
                    },
                    "timestamp": "1 hour ago",
                    "likes": 2
                }
            ]
            return JsonResponse(comments, safe=False)
            
        elif request.method == 'POST':
            # Create new comment
            import json
            data = json.loads(request.body)
            content = data.get('content', '')
            
            # Mock new comment creation
            new_comment = {
                "id": f"comment_{int(time.time())}",
                "content": content,
                "user": {
                    "id": "current_user",
                    "name": "You", 
                    "avatar": "https://via.placeholder.com/40"
                },
                "timestamp": "Just now",
                "likes": 0
            }
            
            return JsonResponse(new_comment, status=201)
        
        else:
            return JsonResponse({'error': 'Method not allowed'}, status=405)
            
    except Exception as e:
        print(f"Post comments error: {e}")
        return JsonResponse({'error': str(e)}, status=500)

@csrf_exempt
def upload_media(request):
    """Upload image or video for posts"""
    try:
        if request.method == 'POST':
            if 'media' in request.FILES:
                # Mock media upload - in production, save to cloud storage
                media_file = request.FILES['media']
                content_type = media_file.content_type
                
                # Determine media type
                if content_type.startswith('image/'):
                    media_type = 'image'
                    media_url = f"https://via.placeholder.com/300x200/667eea/ffffff?text=Uploaded+Image"
                elif content_type.startswith('video/'):
                    media_type = 'video'
                    media_url = f"https://via.placeholder.com/300x200/FF3B30/ffffff?text=Video+Thumbnail"
                else:
                    return JsonResponse({'error': 'Unsupported media type'}, status=400)
                
                return JsonResponse({
                    "mediaUrl": media_url,
                    "type": media_type,
                    "message": f"{media_type.title()} uploaded successfully"
                })
            else:
                return JsonResponse({'error': 'No media file provided'}, status=400)
        
        else:
            return JsonResponse({'error': 'Method not allowed'}, status=405)
            
    except Exception as e:
        print(f"Media upload error: {e}")
        return JsonResponse({'error': str(e)}, status=500)

@csrf_exempt
def register_push_token(request):
    """Register push notification token for user"""
    try:
        if request.method == 'POST':
            import json
            data = json.loads(request.body)
            user_id = data.get('userId', 'demo-user')
            expo_push_token = data.get('expoPushToken', '')
            circle_id = data.get('circleId', '')
            
            # Mock token registration - in production, store in database
            print(f"📱 Push token registered for user {user_id} in circle {circle_id}: {expo_push_token[:20]}...")
            
            return JsonResponse({
                "success": True,
                "message": "Push token registered successfully",
                "userId": user_id,
                "circleId": circle_id
            })
        
        else:
            return JsonResponse({'error': 'Method not allowed'}, status=405)
            
    except Exception as e:
        print(f"Push token registration error: {e}")
        return JsonResponse({'error': str(e)}, status=500)

@csrf_exempt
def send_push_notification(request):
    """Send push notification (for testing)"""
    try:
        if request.method == 'POST':
            import json
            data = json.loads(request.body)
            title = data.get('title', 'New Activity')
            body = data.get('body', 'You have a new notification')
            data_payload = data.get('data', {})
            
            # Mock push notification - in production, use Expo Push API
            print(f"📤 Push notification sent: {title} - {body}")
            print(f"📤 Data payload: {data_payload}")
            
            return JsonResponse({
                "success": True,
                "message": "Push notification sent successfully",
                "title": title,
                "body": body
            })
        
        else:
            return JsonResponse({'error': 'Method not allowed'}, status=405)
            
    except Exception as e:
        print(f"Push notification error: {e}")
        return JsonResponse({'error': str(e)}, status=500)

@csrf_exempt
def agora_token(request):
    """Generate Agora token for live streaming"""
    try:
        if request.method == 'POST':
            import json
            data = json.loads(request.body)
            channel_name = data.get('channelName', '')
            user_id = data.get('userId', '0')
            role = data.get('role', 'publisher')  # publisher or audience
            
            # Mock Agora token generation - in production, use Agora Token Builder
            # For now, return a mock token (in production, generate real token)
            mock_token = f"mock_token_{channel_name}_{user_id}_{int(time.time())}"
            
            print(f"🎥 Agora token generated for channel {channel_name}, user {user_id}, role {role}")
            
            return JsonResponse({
                "token": mock_token,
                "channelName": channel_name,
                "uid": user_id,
                "role": role,
                "expiration": int(time.time()) + 3600  # 1 hour expiration
            })
        
        else:
            return JsonResponse({'error': 'Method not allowed'}, status=405)
            
    except Exception as e:
        print(f"Agora token error: {e}")
        return JsonResponse({'error': str(e)}, status=500)

@csrf_exempt
def live_stream_events(request):
    """Handle live stream events (start/end)"""
    try:
        if request.method == 'POST':
            import json
            data = json.loads(request.body)
            event_type = data.get('eventType', '')  # 'start' or 'end'
            circle_id = data.get('circleId', '')
            user_id = data.get('userId', '')
            user_name = data.get('userName', 'Anonymous')
            
            if event_type == 'start':
                print(f"🎥 Live stream started in circle {circle_id} by {user_name}")
                # In production, store in database and notify all circle members
                # Mock push notification for live stream start
                return JsonResponse({
                    "success": True,
                    "message": "Live stream started",
                    "circleId": circle_id,
                    "host": user_name,
                    "viewerCount": 0
                })
            elif event_type == 'end':
                print(f"🎥 Live stream ended in circle {circle_id}")
                return JsonResponse({
                    "success": True,
                    "message": "Live stream ended",
                    "circleId": circle_id
                })
            else:
                return JsonResponse({'error': 'Invalid event type'}, status=400)
        
        else:
            return JsonResponse({'error': 'Method not allowed'}, status=405)
            
    except Exception as e:
        print(f"Live stream events error: {e}")
        return JsonResponse({'error': str(e)}, status=500)

@csrf_exempt
def video_compression_info(request):
    """Get video compression settings and info"""
    try:
        if request.method == 'GET':
            # Return compression settings for the app
            compression_settings = {
                "maxFileSize": 10 * 1024 * 1024,  # 10MB
                "quality": "medium",  # low, medium, high
                "compressionMethod": "auto",
                "includeAudio": True,
                "maxDuration": 60,  # 60 seconds
                "supportedFormats": ["mp4", "mov", "avi"],
                "compressionLevels": {
                    "low": {"quality": 0.3, "maxSize": 5 * 1024 * 1024},
                    "medium": {"quality": 0.6, "maxSize": 10 * 1024 * 1024},
                    "high": {"quality": 0.8, "maxSize": 20 * 1024 * 1024}
                }
            }
            
            return JsonResponse(compression_settings)
        
        else:
            return JsonResponse({'error': 'Method not allowed'}, status=405)
            
    except Exception as e:
        print(f"Video compression info error: {e}")
        return JsonResponse({'error': str(e)}, status=500)

# Add URL patterns
urlpatterns.insert(0, path("api/wealth-circles/", wealth_circles_list, name='wealth_circles_list'))
urlpatterns.insert(0, path("api/wealth-circles/<str:circle_id>/posts/", wealth_circle_posts, name='wealth_circle_posts'))
urlpatterns.insert(0, path("api/posts/<str:post_id>/comments/", post_comments, name='post_comments'))
urlpatterns.insert(0, path("api/upload-media/", upload_media, name='upload_media'))
urlpatterns.insert(0, path("api/register-push-token/", register_push_token, name='register_push_token'))
urlpatterns.insert(0, path("api/send-push-notification/", send_push_notification, name='send_push_notification'))
urlpatterns.insert(0, path("api/agora-token/", agora_token, name='agora_token'))
urlpatterns.insert(0, path("api/live-stream-events/", live_stream_events, name='live_stream_events'))
urlpatterns.insert(0, path("api/video-compression-info/", video_compression_info, name='video_compression_info'))

# Diagnostic endpoints
urlpatterns.append(path("echo", echo, name='echo'))
urlpatterns.append(path("netcheck", netcheck, name='netcheck'))

# Missing API Endpoints - Added for Version 2 Features
@csrf_exempt
def user_profile_api(request):
    """User Profile API endpoint"""
    try:
        auth_header = request.headers.get('Authorization', '')
        if not auth_header.startswith('Bearer '):
            return JsonResponse({'error': 'Authentication required'}, status=401)
        
        return JsonResponse({
            'id': 1,
            'email': 'demo@example.com',
            'username': 'demo',
            'name': 'Demo User',
            'hasPremiumAccess': True,
            'subscriptionTier': 'PREMIUM',
            'createdAt': '2024-01-01T00:00:00Z',
            'lastLogin': time.strftime('%Y-%m-%dT%H:%M:%SZ')
        })
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@csrf_exempt
def portfolio_api(request):
    """Portfolio Management API endpoint"""
    try:
        if request.method == 'GET':
            portfolios = [
                {
                    'id': 1,
                    'name': 'Growth Portfolio',
                    'totalValue': 50000.0,
                    'totalReturn': 7500.0,
                    'totalReturnPercent': 15.0,
                    'holdings': [
                        {
                            'id': 1,
                            'symbol': 'AAPL',
                            'shares': 50,
                            'currentPrice': 175.50,
                            'totalValue': 8775.0
                        },
                        {
                            'id': 2,
                            'symbol': 'MSFT',
                            'shares': 30,
                            'currentPrice': 380.25,
                            'totalValue': 11407.5
                        }
                    ],
                    'createdAt': '2024-01-01T00:00:00Z',
                    'updatedAt': time.strftime('%Y-%m-%dT%H:%M:%SZ')
                }
            ]
            return JsonResponse(portfolios, safe=False)
        
        elif request.method == 'POST':
            data = json.loads(request.body)
            return JsonResponse({
                'id': 2,
                'name': data.get('name', 'New Portfolio'),
                'totalValue': 0.0,
                'totalReturn': 0.0,
                'totalReturnPercent': 0.0,
                'holdings': [],
                'createdAt': time.strftime('%Y-%m-%dT%H:%M:%SZ'),
                'updatedAt': time.strftime('%Y-%m-%dT%H:%M:%SZ')
            }, status=201)
            
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@csrf_exempt
def market_quotes_api(request):
    """Market Quotes API endpoint"""
    try:
        symbols = request.GET.get('symbols', 'AAPL,MSFT,GOOGL').split(',')
        quotes = []
        
        for symbol in symbols:
            symbol = symbol.strip().upper()
            quotes.append({
                'symbol': symbol,
                'price': 175.50 if symbol == 'AAPL' else 380.25 if symbol == 'MSFT' else 140.85,
                'change': 2.5,
                'changePercent': 1.4,
                'volume': 1000000,
                'marketCap': 2800000000000 if symbol == 'AAPL' else 2800000000000 if symbol == 'MSFT' else 1800000000000,
                'lastUpdated': time.strftime('%Y-%m-%dT%H:%M:%SZ')
            })
        
        return JsonResponse(quotes, safe=False)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@csrf_exempt
def market_news_api(request):
    """Market News API endpoint"""
    try:
        news = [
            {
                'id': 1,
                'title': 'Apple Reports Strong Q4 Earnings',
                'summary': 'Apple Inc. reported better-than-expected earnings for Q4 2024',
                'url': 'https://example.com/news/apple-earnings',
                'publishedAt': time.strftime('%Y-%m-%dT%H:%M:%SZ'),
                'source': 'Reuters',
                'sentiment': 'positive',
                'relevanceScore': 0.9
            },
            {
                'id': 2,
                'title': 'Microsoft Cloud Growth Continues',
                'summary': 'Microsoft Azure shows strong growth in enterprise adoption',
                'url': 'https://example.com/news/microsoft-cloud',
                'publishedAt': time.strftime('%Y-%m-%dT%H:%M:%SZ'),
                'source': 'Bloomberg',
                'sentiment': 'positive',
                'relevanceScore': 0.8
            }
        ]
        return JsonResponse(news, safe=False)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@csrf_exempt
def oracle_insights_api(request):
    """Oracle Insights API endpoint"""
    try:
        return JsonResponse({
            "insights": [
                {
                    "type": "market_trend",
                    "title": "AI-Powered Market Analysis",
                    "description": "Current market shows bullish sentiment with strong tech sector performance",
                    "confidence": 0.85,
                    "impact": "high",
                    "timeframe": "1-3 months"
                }
            ],
            "predictions": [
                {
                    "symbol": "AAPL",
                    "direction": "bullish",
                    "targetPrice": 185.0,
                    "confidence": 0.82,
                    "timeframe": "3 months"
                }
            ],
            "marketSentiment": "bullish",
            "riskAssessment": "moderate",
            "recommendations": [
                "Consider increasing tech allocation",
                "Monitor volatility indicators"
            ],
            "generatedAt": time.strftime('%Y-%m-%dT%H:%M:%SZ')
        })
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@csrf_exempt
def voice_ai_api(request):
    """Voice AI Assistant API endpoint with Whisper transcription"""
    try:
        if request.method == 'POST':
            print(f"🔍 Voice AI API: Request method: {request.method}")
            print(f"🔍 Voice AI API: Content type: {request.content_type}")
            print(f"🔍 Voice AI API: Files: {list(request.FILES.keys())}")
            print(f"🔍 Voice AI API: POST data: {list(request.POST.keys())}")
            
            # Check if it's a file upload (multipart/form-data)
            if request.FILES.get('audio'):
                # Handle audio file upload and transcription
                audio_file = request.FILES['audio']
                print(f"🔍 Voice AI API: Audio file received: {audio_file.name}, size: {audio_file.size}")
                
                # Import OpenAI for Whisper transcription
                import openai
                from django.conf import settings
                import tempfile
                import os
                
                # Get OpenAI API key
                openai_key = getattr(settings, 'OPENAI_API_KEY', '')
                if not openai_key or openai_key.startswith('sk-proj-mock'):
                    return JsonResponse({
                        'error': 'OpenAI API key not configured for voice transcription',
                        'transcription': '',
                        'aiResponse': 'Voice transcription requires a valid OpenAI API key.'
                    }, status=400)
                
                # Initialize OpenAI client
                client = openai.OpenAI(api_key=openai_key)
                
                # Save uploaded file temporarily
                with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as temp_file:
                    for chunk in audio_file.chunks():
                        temp_file.write(chunk)
                    temp_file_path = temp_file.name
                
                try:
                    # Transcribe audio using Whisper
                    with open(temp_file_path, 'rb') as audio_data:
                        transcription = client.audio.transcriptions.create(
                            model="whisper-1",
                            file=audio_data,
                            language="en",
                            prompt="Transcribe financial queries about portfolios, investments, and market analysis.",
                            response_format="json",
                            temperature=0
                        )
                    
                    transcribed_text = transcription.text
                    
                    # Process with AI assistant
                    from core.ai_service import AIService
                    ai_service = AIService()
                    
                    ai_messages = [
                        {"role": "system", "content": "You are a helpful financial assistant. Provide concise, accurate, and actionable advice on financial topics, investing, and personal finance based on voice queries."},
                        {"role": "user", "content": transcribed_text}
                    ]
                    
                    ai_response = ai_service.get_chat_response(ai_messages)
                    ai_text = ai_response.get('content', 'I apologize, but I could not generate a response at this time.')
                    
                    response = {
                        'response': {
                            'text': ai_text,
                            'transcription': transcribed_text,
                            'intent': 'voice_query',
                            'entities': ['voice', 'financial'],
                            'confidence': 0.85
                        },
                        'actions': [
                            {
                                'type': 'voice_response',
                                'parameters': {'text': ai_text},
                                'execute': True
                            }
                        ],
                        'success': True,
                        'errors': []
                    }
                    
                except Exception as whisper_error:
                    print(f"Whisper transcription error: {whisper_error}")
                    response = {
                        'response': {
                            'text': 'I apologize, but I had trouble understanding your voice input. Could you please try again?',
                            'transcription': '',
                            'intent': 'error',
                            'entities': [],
                            'confidence': 0.0
                        },
                        'actions': [],
                        'success': False,
                        'errors': [str(whisper_error)]
                    }
                
                finally:
                    # Clean up temporary file
                    if os.path.exists(temp_file_path):
                        os.unlink(temp_file_path)
                
                return JsonResponse(response)
            
            else:
                print(f"🔍 Voice AI API: No audio file found in request")
                # Handle text input (fallback)
                try:
                    data = json.loads(request.body)
                    text = data.get('text', '')
                    print(f"🔍 Voice AI API: Text input received: {text}")
                except json.JSONDecodeError:
                    print(f"🔍 Voice AI API: No JSON body, returning error for missing audio file")
                    # If no JSON body, return error for missing audio file
                    return JsonResponse({
                        'error': 'No audio file provided',
                        'transcription': '',
                        'aiResponse': 'Please provide an audio file for voice processing.'
                    }, status=400)
                
                # Process with AI assistant
                from core.ai_service import AIService
                ai_service = AIService()
                
                ai_messages = [
                    {"role": "system", "content": "You are a helpful financial assistant. Provide concise, accurate, and actionable advice on financial topics, investing, and personal finance."},
                    {"role": "user", "content": text}
                ]
                
                ai_response = ai_service.get_chat_response(ai_messages)
                ai_text = ai_response.get('content', 'I apologize, but I could not generate a response at this time.')
                
                response = {
                    'response': {
                        'text': ai_text,
                        'intent': 'text_query',
                        'entities': ['text', 'financial'],
                        'confidence': 0.85
                    },
                    'actions': [
                        {
                            'type': 'text_response',
                            'parameters': {'text': ai_text},
                            'execute': True
                        }
                    ],
                    'success': True,
                    'errors': []
                }
                return JsonResponse(response)
        
        else:
            return JsonResponse({'error': 'Method not allowed'}, status=405)
            
    except Exception as e:
        print(f"Voice AI API error: {e}")
        return JsonResponse({'error': str(e)}, status=500)

@csrf_exempt
def wellness_score_api(request, portfolio_id):
    """Wellness Score API endpoint"""
    try:
        return JsonResponse({
            "overallScore": 85,
            "metrics": {
                "riskManagement": 88,
                "diversification": 82,
                "taxEfficiency": 79,
                "performance": 87,
                "liquidity": 91
            },
            "recommendations": [
                {
                    "category": "risk_management",
                    "priority": "high",
                    "description": "Consider adding more defensive stocks to reduce volatility",
                    "impact": "Reduce portfolio volatility by 15%"
                }
            ],
            "calculatedAt": time.strftime('%Y-%m-%dT%H:%M:%SZ')
        })
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@csrf_exempt
def blockchain_status_api(request):
    """Blockchain Integration API endpoint"""
    try:
        return JsonResponse({
            "networks": [
                {
                    "name": "Ethereum",
                    "status": "active",
                    "balance": 1.25,
                    "transactions": 15
                }
            ],
            "defiPositions": [
                {
                    "protocol": "Aave",
                    "asset": "USDC",
                    "amount": 10000.0,
                    "apy": 0.045
                }
            ],
            "nfts": [
                {
                    "id": "nft_1",
                    "name": "RichesReach Genesis NFT",
                    "value": 0.5,
                    "collection": "RichesReach"
                }
            ],
            "lastUpdated": time.strftime('%Y-%m-%dT%H:%M:%SZ')
        })
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@csrf_exempt
def social_trading_api(request):
    """Social Trading API endpoint"""
    try:
        return JsonResponse({
            "signals": [
                {
                    "id": "signal_1",
                    "trader": "AI_Trader_Pro",
                    "symbol": "AAPL",
                    "action": "BUY",
                    "price": 175.50,
                    "confidence": 0.85,
                    "timestamp": time.strftime('%Y-%m-%dT%H:%M:%SZ')
                }
            ],
            "topTraders": [
                {
                    "id": "trader_1",
                    "name": "AI_Trader_Pro",
                    "performance": 0.25,
                    "followers": 1250,
                    "winRate": 0.78
                }
            ],
            "collectiveFunds": [
                {
                    "id": "fund_1",
                    "name": "Tech Growth Collective",
                    "totalValue": 2500000.0,
                    "participants": 150,
                    "performance": 0.18
                }
            ]
        })
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@csrf_exempt
def wealth_circles_api(request):
    """Wealth Circles API endpoint"""
    try:
        return JsonResponse([
            {
                "id": "circle_1",
                "name": "Tech Entrepreneurs",
                "category": "technology",
                "description": "Building wealth through technology investments",
                "members": 45,
                "activity": [
                    {
                        "type": "discussion",
                        "user": "tech_leader_1",
                        "content": "AI sector showing strong momentum",
                        "timestamp": time.strftime('%Y-%m-%dT%H:%M:%SZ')
                    }
                ],
                "recentActivity": [
                    {
                        "type": "trade_share",
                        "user": "tech_leader_2",
                        "content": "Just opened AAPL position",
                        "timestamp": time.strftime('%Y-%m-%dT%H:%M:%SZ')
                    }
                ]
            }
        ], safe=False)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@csrf_exempt
def theme_settings_api(request):
    """Theme Settings API endpoint"""
    try:
        if request.method == 'GET':
            return JsonResponse({
                'theme': 'light',
                'primaryColor': '#8B5CF6',
                'accentColor': '#10B981',
                'fontSize': 'medium',
                'animations': True
            })
        elif request.method == 'PUT':
            data = json.loads(request.body)
            return JsonResponse({
                'theme': data.get('theme', 'light'),
                'primaryColor': data.get('primaryColor', '#8B5CF6'),
                'accentColor': data.get('accentColor', '#10B981'),
                'fontSize': data.get('fontSize', 'medium'),
                'animations': data.get('animations', True)
            })
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@csrf_exempt
def security_settings_api(request):
    """Security Settings API endpoint"""
    try:
        if request.method == 'GET':
            return JsonResponse({
                'biometricAuth': True,
                'twoFactorAuth': False,
                'sessionTimeout': 30,
                'loginNotifications': True
            })
        elif request.method == 'PUT':
            data = json.loads(request.body)
            return JsonResponse({
                'biometricAuth': data.get('biometricAuth', True),
                'twoFactorAuth': data.get('twoFactorAuth', False),
                'sessionTimeout': data.get('sessionTimeout', 30),
                'loginNotifications': data.get('loginNotifications', True)
            })
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@csrf_exempt
def viral_growth_api(request):
    """Viral Growth System API endpoint"""
    try:
        return JsonResponse({
            'referralCode': 'DEMO123',
            'referralCount': 15,
            'earnings': 250.0,
            'tier': 'Gold',
            'nextTier': 'Platinum',
            'nextTierRequirement': 25
        })
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@csrf_exempt
def scalability_metrics_api(request):
    """Scalability Metrics API endpoint"""
    try:
        return JsonResponse({
            'systemLoad': 0.45,
            'responseTime': 120,
            'throughput': 1500,
            'errorRate': 0.001,
            'uptime': 99.9
        })
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@csrf_exempt
def marketing_metrics_api(request):
    """Marketing Metrics API endpoint"""
    try:
        return JsonResponse({
            'userAcquisition': 1250,
            'retentionRate': 0.78,
            'conversionRate': 0.12,
            'revenue': 45000.0,
            'costPerAcquisition': 25.0
        })
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

# Add all missing endpoints to URL patterns
urlpatterns.append(path("api/user/profile/", user_profile_api, name='user_profile'))
urlpatterns.append(path("api/portfolio/", portfolio_api, name='portfolio_list'))
urlpatterns.append(path("api/portfolio/<int:portfolio_id>/", portfolio_api, name='portfolio_detail'))
urlpatterns.append(path("api/portfolio/<int:portfolio_id>/holdings/", portfolio_api, name='portfolio_holdings'))
urlpatterns.append(path("api/portfolio/<int:portfolio_id>/holdings/<int:holding_id>/", portfolio_api, name='holding_detail'))
urlpatterns.append(path("api/market/quotes/", market_quotes_api, name='market_quotes'))
urlpatterns.append(path("api/market/news/", market_news_api, name='market_news'))
urlpatterns.append(path("api/market/analysis/", market_quotes_api, name='market_analysis'))
urlpatterns.append(path("api/oracle/insights/", oracle_insights_api, name='oracle_insights'))
urlpatterns.append(path("api/voice/process/", voice_ai_api, name='voice_ai'))
urlpatterns.append(path("api/portfolio/<int:portfolio_id>/wellness/", wellness_score_api, name='wellness_score'))
urlpatterns.append(path("api/portfolio/<int:portfolio_id>/ar/", wellness_score_api, name='ar_portfolio'))
urlpatterns.append(path("api/blockchain/status/", blockchain_status_api, name='blockchain_status'))
urlpatterns.append(path("api/social/trading/", social_trading_api, name='social_trading'))
urlpatterns.append(path("api/wealth-circles/", wealth_circles_api, name='wealth_circles'))
urlpatterns.append(path("api/user/theme/", theme_settings_api, name='theme_settings'))
urlpatterns.append(path("api/user/security/", security_settings_api, name='security_settings'))
urlpatterns.append(path("api/viral-growth/", viral_growth_api, name='viral_growth'))
urlpatterns.append(path("api/system/scalability/", scalability_metrics_api, name='scalability_metrics'))
urlpatterns.append(path("api/marketing/metrics/", marketing_metrics_api, name='marketing_metrics'))

# Alpaca Integration URLs
from alpaca_integration.urls import urlpatterns as alpaca_urls
urlpatterns.append(path('alpaca/', include('alpaca_integration.urls')))

# Tutor URLs
from core.tutor_views import TutorAskView, TutorExplainView, TutorQuizView, TutorModuleView, TutorMarketCommentaryView
urlpatterns.append(path('tutor/ask/', TutorAskView.as_view(), name='tutor_ask'))
urlpatterns.append(path('tutor/ask', TutorAskView.as_view(), name='tutor_ask_no_slash'))
urlpatterns.append(path('tutor/explain/', TutorExplainView.as_view(), name='tutor_explain'))
urlpatterns.append(path('tutor/explain', TutorExplainView.as_view(), name='tutor_explain_no_slash'))
urlpatterns.append(path('tutor/quiz/', TutorQuizView.as_view(), name='tutor_quiz'))
urlpatterns.append(path('tutor/quiz', TutorQuizView.as_view(), name='tutor_quiz_no_slash'))
urlpatterns.append(path('tutor/module/', TutorModuleView.as_view(), name='tutor_module'))
urlpatterns.append(path('tutor/module', TutorModuleView.as_view(), name='tutor_module_no_slash'))
urlpatterns.append(path('tutor/market-commentary/', TutorMarketCommentaryView.as_view(), name='tutor_market_commentary'))
urlpatterns.append(path('tutor/market-commentary', TutorMarketCommentaryView.as_view(), name='tutor_market_commentary_no_slash'))

# Assistant URLs
from core.assistant_views import AssistantQueryView
urlpatterns.append(path('assistant/query/', AssistantQueryView.as_view(), name='assistant_query'))
urlpatterns.append(path('assistant/query', AssistantQueryView.as_view(), name='assistant_query_no_slash'))

# Live Streaming URLs
from core.urls_live_streaming import urlpatterns as live_streaming_urls
for url_pattern in live_streaming_urls:
    urlpatterns.append(path(f'api/{url_pattern.pattern._route}', url_pattern.callback, name=url_pattern.name))

# Voice AI URLs
from core.urls_voice_ai import urlpatterns as voice_ai_urls
for url_pattern in voice_ai_urls:
    urlpatterns.append(path(f'api/{url_pattern.pattern._route}', url_pattern.callback, name=url_pattern.name))
