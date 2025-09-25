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

urlpatterns = [
    path("admin/", admin.site.urls),
    path("healthz", healthz),  # <-- ALB target health
    # IMPORTANT: keep the trailing slash and csrf_exempt for mobile POSTs
    path("graphql/", csrf_exempt(GraphQLView.as_view(schema=schema, graphiql=False))),
    path("auth/", auth_view),
    path("me/", me_view),
    path("signals/", signals_view),
]