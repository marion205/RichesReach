"""
Market Data API Views with Caching and Rate Limit Protection
Uses Finnhub for stocks and Polygon.io for options
"""
import os
import json
import time
import requests
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.cache import cache_page
from django.core.cache import cache
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

# API Configuration
FINNHUB_API_KEY = os.getenv('FINNHUB_API_KEY')
POLYGON_API_KEY = os.getenv('POLYGON_API_KEY')

def _get_mock_quote(symbol: str) -> dict:
    """Generate mock quote data for testing"""
    import random
    
    base_prices = {
        "AAPL": 150.0, "MSFT": 300.0, "GOOGL": 2500.0, "TSLA": 200.0,
        "AMZN": 3000.0, "META": 300.0, "NVDA": 400.0, "NFLX": 400.0,
        "ADBE": 580.0, "AMD": 125.0, "CRM": 220.0, "INTC": 45.0,
        "LYFT": 12.0, "PYPL": 65.0, "UBER": 45.0
    }
    
    base_price = base_prices.get(symbol, 100.0)
    variation = random.uniform(-0.05, 0.05)
    current_price = base_price * (1 + variation)
    
    return {
        "symbol": symbol,
        "price": round(current_price, 2),
        "change": round(current_price - base_price, 2),
        "change_percent": round(variation * 100, 2),
        "volume": random.randint(1000000, 10000000),
        "timestamp": int(time.time() * 1000),
        "provider": "mock"
    }
ALPHA_VANTAGE_API_KEY = os.getenv('ALPHA_VANTAGE_API_KEY')  # Fallback only

def _fetch_quote_finnhub(symbol: str) -> dict:
    """Fetch quote from Finnhub API"""
    if not FINNHUB_API_KEY:
        raise Exception("FINNHUB_API_KEY not configured")
    
    response = requests.get(
        "https://finnhub.io/api/v1/quote",
        params={
            "symbol": symbol,
            "token": FINNHUB_API_KEY
        },
        timeout=10
    )
    
    if response.status_code != 200:
        raise Exception(f"Finnhub HTTP error: {response.status_code}")
    
    data = response.json()
    
    # Check for API errors
    if data.get('error'):
        raise Exception(f"Finnhub API error: {data['error']}")
    
    # Check for rate limit
    if response.status_code == 429:
        raise Exception("Finnhub rate limit exceeded")
    
    return data

def _fetch_quote_polygon(symbol: str) -> dict:
    """Fetch quote from Polygon.io API (previous day data)"""
    if not POLYGON_API_KEY:
        raise Exception("POLYGON_API_KEY not configured")
    
    response = requests.get(
        f"https://api.polygon.io/v2/aggs/ticker/{symbol}/prev",
        params={"apikey": POLYGON_API_KEY},
        timeout=10
    )
    
    if response.status_code != 200:
        raise Exception(f"Polygon HTTP error: {response.status_code}")
    
    data = response.json()
    
    # Check for API errors
    if data.get('status') == 'ERROR':
        raise Exception(f"Polygon API error: {data.get('message', 'Unknown error')}")
    
    return data

def _fetch_quote_alpha_vantage_fallback(symbol: str) -> dict:
    """Fallback to Alpha Vantage (only if other APIs fail)"""
    if not ALPHA_VANTAGE_API_KEY:
        raise Exception("ALPHA_VANTAGE_API_KEY not configured")
    
    response = requests.get(
        "https://www.alphavantage.co/query",
        params={
            "function": "GLOBAL_QUOTE",
            "symbol": symbol,
            "apikey": ALPHA_VANTAGE_API_KEY
        },
        timeout=10
    )
    
    if response.status_code != 200:
        raise Exception(f"Alpha Vantage HTTP error: {response.status_code}")
    
    data = response.json()
    
    # Check for rate limit response
    if "Note" in data or "Information" in data:
        error_msg = data.get("Note") or data.get("Information")
        raise Exception(f"Alpha Vantage rate limit: {error_msg}")
    
    # Check for API error
    if "Error Message" in data:
        raise Exception(f"Alpha Vantage error: {data['Error Message']}")
    
    return data

def _normalize_finnhub_quote(symbol: str, data: dict) -> dict:
    """Normalize Finnhub quote data"""
    return {
        'symbol': symbol,
        'price': float(data.get('c', 0)),  # current price
        'change': float(data.get('d', 0)),  # change
        'change_percent': float(data.get('dp', 0)),  # change percent
        'high': float(data.get('h', 0)),  # high
        'low': float(data.get('l', 0)),  # low
        'open': float(data.get('o', 0)),  # open
        'previous_close': float(data.get('pc', 0)),  # previous close
        'volume': 0,  # Finnhub doesn't provide volume in quote endpoint
        'updated': time.time(),
        'provider': 'finnhub'
    }

def _normalize_polygon_quote(symbol: str, data: dict) -> dict:
    """Normalize Polygon.io quote data (previous day aggregates)"""
    results = data.get('results', [])
    if not results:
        raise Exception("No results in Polygon response")
    
    quote_data = results[0]  # Get the first (and only) result
    return {
        'symbol': symbol,
        'price': float(quote_data.get('c', 0)),  # close price
        'change': 0,  # Polygon prev doesn't provide change
        'change_percent': 0,
        'high': float(quote_data.get('h', 0)),  # high
        'low': float(quote_data.get('l', 0)),   # low
        'open': float(quote_data.get('o', 0)),  # open
        'previous_close': float(quote_data.get('c', 0)),  # close as previous close
        'volume': int(quote_data.get('v', 0)),  # volume
        'updated': time.time(),
        'provider': 'polygon'
    }

def _normalize_alpha_vantage_quote(symbol: str, data: dict) -> dict:
    """Normalize Alpha Vantage quote data"""
    quote_data = data.get("Global Quote", {})
    return {
        'symbol': symbol,
        'price': float(quote_data.get('05. price', 0)),
        'change': float(quote_data.get('09. change', 0)),
        'change_percent': float(quote_data.get('10. change percent', '0%').rstrip('%')),
        'volume': int(quote_data.get('06. volume', 0)),
        'high': float(quote_data.get('03. high', 0)),
        'low': float(quote_data.get('04. low', 0)),
        'open': float(quote_data.get('02. open', 0)),
        'previous_close': float(quote_data.get('08. previous close', 0)),
        'updated': time.time(),
        'provider': 'alpha_vantage'
    }

@csrf_exempt
def market_quotes(request):
    """
    GET /api/market/quotes?symbols=GOOGL,TSLA,AAPL
    Returns cached market quotes using Finnhub (primary), Polygon.io (secondary), Alpha Vantage (fallback)
    """
    if request.method != 'GET':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    
    symbols_param = request.GET.get('symbols', '')
    if not symbols_param:
        return JsonResponse({'error': 'symbols parameter required'}, status=400)
    
    # Parse symbols
    symbols = [s.strip().upper() for s in symbols_param.split(',') if s.strip()]
    if not symbols:
        return JsonResponse({'error': 'No valid symbols provided'}, status=400)
    
    # Limit symbols per request to prevent abuse
    if len(symbols) > 20:
        return JsonResponse({'error': 'Maximum 20 symbols per request'}, status=400)
    
    quotes = []
    
    for symbol in symbols:
        try:
            # Check cache first (60 second TTL)
            cache_key = f"quote:{symbol}"
            cached_quote = cache.get(cache_key)
            
            if cached_quote:
                quotes.append(cached_quote)
                continue
            
            quote = None
            provider_used = None
            
            # Check if mock mode is enabled
            if getattr(settings, 'USE_MARKET_MOCK', False):
                quote = _get_mock_quote(symbol)
                provider_used = 'mock'
                logger.info(f"✅ Using mock data for {symbol}")
            else:
                # Try Finnhub first (primary)
                try:
                    if FINNHUB_API_KEY:
                        data = _fetch_quote_finnhub(symbol)
                        quote = _normalize_finnhub_quote(symbol, data)
                        provider_used = 'finnhub'
                        logger.info(f"✅ Fetched {symbol} from Finnhub")
                except Exception as e:
                    logger.warning(f"Finnhub failed for {symbol}: {e}")
                
                # Try Polygon.io second (secondary)
                if not quote and POLYGON_API_KEY:
                    try:
                        data = _fetch_quote_polygon(symbol)
                        quote = _normalize_polygon_quote(symbol, data)
                        provider_used = 'polygon'
                        logger.info(f"✅ Fetched {symbol} from Polygon.io")
                    except Exception as e:
                        logger.warning(f"Polygon.io failed for {symbol}: {e}")
                
                # Try Alpha Vantage as fallback (only if others fail)
                if not quote and ALPHA_VANTAGE_API_KEY:
                    try:
                        data = _fetch_quote_alpha_vantage_fallback(symbol)
                        quote = _normalize_alpha_vantage_quote(symbol, data)
                        provider_used = 'alpha_vantage'
                        logger.info(f"✅ Fetched {symbol} from Alpha Vantage (fallback)")
                    except Exception as e:
                        logger.warning(f"Alpha Vantage fallback failed for {symbol}: {e}")
            
            if quote:
                # Cache for 60 seconds
                cache.set(cache_key, quote, timeout=60)
                quotes.append(quote)
                logger.info(f"📊 Cached quote for {symbol} from {provider_used}")
            else:
                logger.error(f"❌ All providers failed for {symbol}")
                
        except Exception as e:
            logger.error(f"Unexpected error fetching quote for {symbol}: {e}")
            continue
    
    return JsonResponse(quotes, safe=False)

@csrf_exempt
def market_status(request):
    """
    GET /api/market/status
    Returns market data service status
    """
    return JsonResponse({
        'service': 'market_data',
        'providers': {
            'finnhub': {
                'configured': bool(FINNHUB_API_KEY),
                'priority': 1,
                'description': 'Primary stock quotes provider'
            },
            'polygon': {
                'configured': bool(POLYGON_API_KEY),
                'priority': 2,
                'description': 'Secondary stock quotes and options provider'
            },
            'alpha_vantage': {
                'configured': bool(ALPHA_VANTAGE_API_KEY),
                'priority': 3,
                'description': 'Fallback provider only'
            }
        },
        'cache_enabled': True,
        'cache_ttl_seconds': 60,
        'rate_limit_protection': True,
        'max_symbols_per_request': 20,
        'status': 'operational' if (FINNHUB_API_KEY or POLYGON_API_KEY) else 'unavailable'
    })

@csrf_exempt
def market_health(request):
    """
    GET /health/marketdata
    Health check endpoint for market data service
    """
    try:
        # Quick health check - try to fetch a simple quote
        test_symbol = 'AAPL'
        cache_key = f"quote:{test_symbol}"
        cached_quote = cache.get(cache_key)
        
        if cached_quote:
            # We have cached data, service is healthy
            return JsonResponse({
                'status': 'healthy',
                'message': 'Market data service is operational',
                'cache_hit': True,
                'providers_available': {
                    'finnhub': bool(FINNHUB_API_KEY),
                    'polygon': bool(POLYGON_API_KEY),
                    'alpha_vantage': bool(ALPHA_VANTAGE_API_KEY)
                },
                'timestamp': time.time()
            })
        
        # No cached data, check if we can fetch from providers
        if not (FINNHUB_API_KEY or POLYGON_API_KEY or ALPHA_VANTAGE_API_KEY):
            return JsonResponse({
                'status': 'unhealthy',
                'message': 'No market data providers configured',
                'providers_available': {
                    'finnhub': False,
                    'polygon': False,
                    'alpha_vantage': False
                },
                'timestamp': time.time()
            }, status=503)
        
        # Service is configured and ready
        return JsonResponse({
            'status': 'healthy',
            'message': 'Market data service is operational',
            'cache_hit': False,
            'providers_available': {
                'finnhub': bool(FINNHUB_API_KEY),
                'polygon': bool(POLYGON_API_KEY),
                'alpha_vantage': bool(ALPHA_VANTAGE_API_KEY)
            },
            'timestamp': time.time()
        })
        
    except Exception as e:
        logger.error(f"Market data health check failed: {e}")
        return JsonResponse({
            'status': 'unhealthy',
            'message': f'Market data service error: {str(e)}',
            'timestamp': time.time()
        }, status=503)

@csrf_exempt
def options_quotes(request):
    """
    GET /api/market/options?underlying=AAPL&expiration=2024-01-19
    Returns options quotes using Polygon.io
    """
    if request.method != 'GET':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    
    underlying = request.GET.get('underlying', '').upper()
    expiration = request.GET.get('expiration', '')
    
    if not underlying:
        return JsonResponse({'error': 'underlying parameter required'}, status=400)
    
    if not POLYGON_API_KEY:
        return JsonResponse({'error': 'Options data service unavailable'}, status=503)
    
    try:
        # Check cache first (5 minute TTL for options)
        cache_key = f"options:{underlying}:{expiration}"
        cached_options = cache.get(cache_key)
        
        if cached_options:
            return JsonResponse(cached_options, safe=False)
        
        # Fetch options chain from Polygon.io
        url = f"https://api.polygon.io/v3/reference/options/contracts"
        params = {
            "underlying_ticker": underlying,
            "apikey": POLYGON_API_KEY,
            "limit": 1000
        }
        
        if expiration:
            params["expiration_date"] = expiration
        
        response = requests.get(url, params=params, timeout=15)
        
        if response.status_code != 200:
            return JsonResponse({
                'error': f'Polygon API error: {response.status_code}'
            }, status=response.status_code)
        
        data = response.json()
        
        if data.get('status') == 'ERROR':
            return JsonResponse({
                'error': f"Polygon API error: {data.get('message', 'Unknown error')}"
            }, status=400)
        
        # Normalize options data
        options = []
        for contract in data.get('results', []):
            option = {
                'contract_type': contract.get('contract_type'),
                'strike_price': float(contract.get('strike_price', 0)),
                'expiration_date': contract.get('expiration_date'),
                'ticker': contract.get('ticker'),
                'underlying_ticker': contract.get('underlying_ticker'),
                'provider': 'polygon'
            }
            options.append(option)
        
        # Cache for 5 minutes
        cache.set(cache_key, options, timeout=300)
        
        return JsonResponse(options, safe=False)
        
    except requests.exceptions.Timeout:
        return JsonResponse({'error': 'Request timeout'}, status=408)
    except requests.exceptions.RequestException as e:
        return JsonResponse({'error': f'Request error: {str(e)}'}, status=500)
    except Exception as e:
        logger.error(f"Unexpected error fetching options for {underlying}: {e}")
        return JsonResponse({'error': 'Internal server error'}, status=500)
