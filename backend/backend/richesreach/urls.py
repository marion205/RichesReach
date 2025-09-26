from django.contrib import admin
from django.urls import path
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from graphene_django.views import GraphQLView
from core.schema import schema
import time
import json

def healthz(_):
    return JsonResponse({"ok": True, "app": "richesreach"}, status=200)

def health(_):
    return JsonResponse({"ok": True}, status=200)

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
                token = f"test-jwt-token-{int(time.time())}"
                return JsonResponse({
                    'data': {
                        'tokenAuth': {
                            'token': token,
                            'user': {
                                'id': '1',
                                'email': email,
                                'username': email.split('@')[0]
                            }
                        }
                    }
                })
            else:
                return JsonResponse({
                    'data': {
                        'tokenAuth': {
                            'token': None,
                            'user': None
                        }
                    }
                })
        except Exception as e:
            return JsonResponse({
                'data': {
                    'tokenAuth': {
                        'token': None,
                        'user': None
                    }
                }
            })
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

urlpatterns = [
    path("", home),  # <-- Root endpoint
    path("admin/", admin.site.urls),
    path("healthz", healthz),  # <-- ALB target health
    path("health/", health),   # <-- Docker health check
    path("prices/", prices_view),  # <-- Prices endpoint for crypto/stocks
    path("user-profile/", user_profile_view),  # <-- User profile endpoint
    path("discussions/", discussions_view),  # <-- Stock discussions endpoint
    # IMPORTANT: keep the trailing slash and csrf_exempt for mobile POSTs
    path("graphql/", csrf_exempt(GraphQLView.as_view(schema=schema, graphiql=False))),
    path("auth/", auth_view),
    path("me/", me_view),
    path("signals/", signals_view),
]