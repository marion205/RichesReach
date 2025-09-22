# defi/views_prices.py
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

# Replace with real sources (Coingecko, Chainlink aggregators, etc.)
STATIC_PRICES = { "USDC": 1.0, "USDT": 1.0, "WETH": 2500.0 }

@api_view(['GET'])
@permission_classes([AllowAny])
def prices(request):
    syms = request.GET.get('symbols', '')
    out = {}
    for s in [x.strip().upper() for x in syms.split(',') if x.strip()]:
      out[s] = STATIC_PRICES.get(s)
    return Response(out)
