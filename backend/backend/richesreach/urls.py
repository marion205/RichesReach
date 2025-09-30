from django.contrib import admin
from django.urls import path
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from graphene_django.views import GraphQLView
import time
import json

def healthz(_):
    return JsonResponse({"ok": True, "app": "richesreach"}, status=200)

def health(_):
    return JsonResponse({"ok": True, "mode": "simple"}, status=200)

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
    
    # Return mock user data
    return JsonResponse({
        'data': {
            'me': {
                'id': '1',
                'name': 'Test User',
                'email': 'test@example.com',
                'hasPremiumAccess': True,
                'subscriptionTier': 'PREMIUM',
                '__typename': 'User'
            }
        }
    })

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
    """Mock prices endpoint for crypto/stocks"""
    symbols = request.GET.get('symbols', '')
    if not symbols:
        return JsonResponse({'error': 'No symbols provided'}, status=400)
    
    # Mock price data for demo
    price_data = {}
    for symbol in symbols.split(','):
        if symbol.upper() == 'USDC':
            price_data[symbol.upper()] = {'price': 1.00, 'change_24h': 0.00}
        elif symbol.upper() == 'BTC':
            price_data[symbol.upper()] = {'price': 45000.00, 'change_24h': 2.5}
        elif symbol.upper() == 'ETH':
            price_data[symbol.upper()] = {'price': 3000.00, 'change_24h': 1.8}
        else:
            price_data[symbol.upper()] = {'price': 100.00, 'change_24h': 0.5}
    
    return JsonResponse(price_data)

@csrf_exempt
def user_profile_view(request):
    """Mock user profile endpoint"""
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
    """Mock stock discussions endpoint"""
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
from django.conf import settings

urlpatterns = [
    path("", home),  # <-- Root endpoint
    path("admin/", admin.site.urls),
    path("healthz", healthz),  # <-- ALB target health
    path("health/", health),   # <-- Docker health check
    path("prices/", prices_view),  # <-- Prices endpoint for crypto/stocks
    path("user-profile/", user_profile_view),  # <-- User profile endpoint
    path("discussions/", discussions_view),  # <-- Stock discussions endpoint
    # Note: auth/ will be added conditionally below
    path("me/", me_view),
    path("signals/", signals_view),
]

if settings.GRAPHQL_MODE == "simple":
    print("DEBUG: Using SimpleGraphQLView and Mock Auth")
    from core.views_gql_simple import SimpleGraphQLView
    from core.mock_auth import mock_login
    urlpatterns += [
        path("graphql/", SimpleGraphQLView.as_view(), name="graphql"),
        path("auth/", mock_login, name="mock_auth"),  # Override auth with mock JWT
    ]
else:
    print("DEBUG: Using standard GraphQLView")
    # Import schema lazily only in standard mode
    from core.schema import schema
    # Standard GraphQLView (original behavior)
    urlpatterns += [
        path("graphql/", csrf_exempt(GraphQLView.as_view(schema=schema, graphiql=False))),
        path("auth/", auth_view),  # Use original auth view
    ]

# Always add the mock GraphQL endpoint for testing
# (mock_graphql function is defined later in the file)
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

# Simple GraphQL test endpoint
@csrf_exempt
def simple_graphql_test(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            query = data.get('query', '')
            if 'ping' in query:
                return JsonResponse({'data': {'ping': 'ok'}})
            elif 'stocks' in query:
                return JsonResponse({
                    'data': {
                        'stocks': [
                            {'symbol': 'AAPL', 'companyName': 'Apple Inc.', 'currentPrice': 175.50},
                            {'symbol': 'MSFT', 'companyName': 'Microsoft Corp.', 'currentPrice': 380.25}
                        ]
                    }
                })
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

# Simple mock GraphQL endpoint that returns stock data
@csrf_exempt
def mock_graphql(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            query = data.get('query', '')
            if 'stocks' in query:
                return JsonResponse({
                    'data': {
                        'stocks': [
                            {
                                'symbol': 'AAPL',
                                'companyName': 'Apple Inc.',
                                'currentPrice': 175.50,
                                'dividendScore': 0.7
                            },
                            {
                                'symbol': 'MSFT',
                                'companyName': 'Microsoft Corporation',
                                'currentPrice': 380.25,
                                'dividendScore': 0.8
                            },
                            {
                                'symbol': 'TSLA',
                                'companyName': 'Tesla, Inc.',
                                'currentPrice': 250.75,
                                'dividendScore': 0.1
                            }
                        ]
                    }
                })
            else:
                return JsonResponse({'data': {'test': 'working'}})
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    else:
        return JsonResponse({'error': 'Method not allowed'}, status=405)

urlpatterns.append(path("simple-graphql/", simple_graphql_test))
urlpatterns.append(path("debug-env/", debug_env))
urlpatterns.append(path("mock-graphql/", mock_graphql))
from .views_auth import login_view
urlpatterns.append(path("api/auth/login/", login_view))
