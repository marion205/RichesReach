# core/views_health.py
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.conf import settings
from django.db import connection
import redis
import logging
import time

logger = logging.getLogger(__name__)

@csrf_exempt
@require_http_methods(["GET"])
def health_check(request):
    """Comprehensive health check endpoint for production monitoring"""
    
    health_status = {
        "status": "healthy",
        "timestamp": int(time.time()),
        "version": "1.0.0",
        "environment": "production" if not settings.DEBUG else "development",
        "checks": {}
    }
    
    # Database check
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            health_status["checks"]["database"] = {
                "status": "healthy",
                "response_time_ms": 0
            }
    except Exception as e:
        health_status["checks"]["database"] = {
            "status": "unhealthy",
            "error": str(e)
        }
        health_status["status"] = "unhealthy"
    
    # Redis check
    try:
        redis_client = redis.Redis.from_url(
            getattr(settings, 'REDIS_URL', 'redis://process.env.REDIS_HOST || "localhost:6379"/0'),
            socket_connect_timeout=2,
            socket_timeout=2
        )
        start_time = time.time()
        redis_client.ping()
        response_time = int((time.time() - start_time) * 1000)
        
        health_status["checks"]["redis"] = {
            "status": "healthy",
            "response_time_ms": response_time
        }
    except Exception as e:
        health_status["checks"]["redis"] = {
            "status": "unhealthy",
            "error": str(e)
        }
        health_status["status"] = "unhealthy"
    
    # API Keys check
    api_keys_status = {}
    required_keys = ['POLYGON_API_KEY', 'FINNHUB_API_KEY', 'OPENAI_API_KEY']
    
    for key in required_keys:
        value = getattr(settings, key, None)
        api_keys_status[key] = "configured" if value else "missing"
    
    health_status["checks"]["api_keys"] = api_keys_status
    
    # Market data service check
    try:
        from .market_data_service import MarketDataService
        service = MarketDataService()
        # Quick test with a simple symbol
        test_quote = service.get_quote("AAPL")
        health_status["checks"]["market_data"] = {
            "status": "healthy",
            "provider": test_quote.get("provider", "unknown")
        }
    except Exception as e:
        health_status["checks"]["market_data"] = {
            "status": "unhealthy",
            "error": str(e)
        }
        health_status["status"] = "unhealthy"
    
    # Memory usage
    try:
        import psutil
        process = psutil.Process()
        memory_info = process.memory_info()
        health_status["checks"]["memory"] = {
            "status": "healthy",
            "rss_mb": round(memory_info.rss / 1024 / 1024, 2),
            "vms_mb": round(memory_info.vms / 1024 / 1024, 2)
        }
    except ImportError:
        health_status["checks"]["memory"] = {
            "status": "unknown",
            "note": "psutil not available"
        }
    except Exception as e:
        health_status["checks"]["memory"] = {
            "status": "error",
            "error": str(e)
        }
    
    # Determine overall status
    if health_status["status"] == "healthy":
        return JsonResponse(health_status, status=200)
    else:
        return JsonResponse(health_status, status=503)

@csrf_exempt
@require_http_methods(["GET"])
def readiness_check(request):
    """Kubernetes readiness probe endpoint"""
    try:
        # Check if the application is ready to serve traffic
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        
        return JsonResponse({"status": "ready"}, status=200)
    except Exception as e:
        logger.error(f"Readiness check failed: {e}")
        return JsonResponse({"status": "not_ready", "error": str(e)}, status=503)

@csrf_exempt
@require_http_methods(["GET"])
def liveness_check(request):
    """Kubernetes liveness probe endpoint"""
    return JsonResponse({"status": "alive"}, status=200)
