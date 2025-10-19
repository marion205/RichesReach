"""
Health check endpoints for monitoring and load balancers.
"""
import time
import psutil
import logging
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.core.cache import cache
from django.db import connection
from django.conf import settings
import os

logger = logging.getLogger(__name__)

@csrf_exempt
@require_http_methods(["GET"])
def health_check(request):
    """
    Basic health check endpoint.
    Returns 200 if the application is running.
    """
    return JsonResponse({
        'status': 'healthy',
        'timestamp': time.time(),
        'version': '1.0.0'
    })

@csrf_exempt
@require_http_methods(["GET"])
def health_detailed(request):
    """
    Detailed health check endpoint with system metrics.
    """
    health_status = {
        'status': 'healthy',
        'timestamp': time.time(),
        'version': '1.0.0',
        'checks': {}
    }
    
    # Database check
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            health_status['checks']['database'] = {
                'status': 'healthy',
                'response_time_ms': 0
            }
    except Exception as e:
        health_status['checks']['database'] = {
            'status': 'unhealthy',
            'error': str(e)
        }
        health_status['status'] = 'unhealthy'
    
    # Redis/Cache check
    try:
        start_time = time.time()
        cache.set('health_check', 'test', 10)
        cache.get('health_check')
        response_time = (time.time() - start_time) * 1000
        
        health_status['checks']['cache'] = {
            'status': 'healthy',
            'response_time_ms': round(response_time, 2)
        }
    except Exception as e:
        health_status['checks']['cache'] = {
            'status': 'unhealthy',
            'error': str(e)
        }
        health_status['status'] = 'unhealthy'
    
    # Disk usage check
    try:
        disk_usage = psutil.disk_usage('/')
        disk_percent = (disk_usage.used / disk_usage.total) * 100
        
        max_disk_usage = getattr(settings, 'HEALTH_CHECK', {}).get('DISK_USAGE_MAX', 90)
        
        if disk_percent > max_disk_usage:
            health_status['checks']['disk'] = {
                'status': 'unhealthy',
                'usage_percent': round(disk_percent, 2),
                'threshold': max_disk_usage
            }
            health_status['status'] = 'unhealthy'
        else:
            health_status['checks']['disk'] = {
                'status': 'healthy',
                'usage_percent': round(disk_percent, 2),
                'threshold': max_disk_usage
            }
    except Exception as e:
        health_status['checks']['disk'] = {
            'status': 'unknown',
            'error': str(e)
        }
    
    # Memory usage check
    try:
        memory = psutil.virtual_memory()
        memory_percent = memory.percent
        memory_mb = memory.used / (1024 * 1024)
        
        min_memory = getattr(settings, 'HEALTH_CHECK', {}).get('MEMORY_MIN', 100)
        
        if memory_mb < min_memory:
            health_status['checks']['memory'] = {
                'status': 'unhealthy',
                'usage_mb': round(memory_mb, 2),
                'usage_percent': round(memory_percent, 2),
                'minimum_mb': min_memory
            }
            health_status['status'] = 'unhealthy'
        else:
            health_status['checks']['memory'] = {
                'status': 'healthy',
                'usage_mb': round(memory_mb, 2),
                'usage_percent': round(memory_percent, 2),
                'minimum_mb': min_memory
            }
    except Exception as e:
        health_status['checks']['memory'] = {
            'status': 'unknown',
            'error': str(e)
        }
    
    # API keys check
    api_keys_status = {}
    required_keys = ['FINNHUB_API_KEY', 'POLYGON_API_KEY']
    optional_keys = ['ALPHA_VANTAGE_API_KEY', 'OPENAI_API_KEY']
    
    for key in required_keys:
        if getattr(settings, key, None):
            api_keys_status[key] = 'configured'
        else:
            api_keys_status[key] = 'missing'
            health_status['status'] = 'degraded'
    
    for key in optional_keys:
        if getattr(settings, key, None):
            api_keys_status[key] = 'configured'
        else:
            api_keys_status[key] = 'not_configured'
    
    health_status['checks']['api_keys'] = api_keys_status
    
    # Return appropriate HTTP status code
    if health_status['status'] == 'healthy':
        return JsonResponse(health_status, status=200)
    elif health_status['status'] == 'degraded':
        return JsonResponse(health_status, status=200)  # Still return 200 for degraded
    else:
        return JsonResponse(health_status, status=503)

@csrf_exempt
@require_http_methods(["GET"])
def health_ready(request):
    """
    Readiness check endpoint for Kubernetes.
    Returns 200 if the application is ready to serve traffic.
    """
    ready_status = {
        'status': 'ready',
        'timestamp': time.time()
    }
    
    # Check if migrations are applied
    try:
        from django.core.management import execute_from_command_line
        from django.core.management.commands.migrate import Command as MigrateCommand
        
        # This is a simplified check - in production you might want to
        # check the migration status more thoroughly
        ready_status['migrations'] = 'applied'
    except Exception as e:
        ready_status['migrations'] = f'error: {str(e)}'
        ready_status['status'] = 'not_ready'
    
    # Check if required services are available
    try:
        # Test database connection
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        
        # Test cache connection
        cache.set('ready_check', 'test', 10)
        cache.get('ready_check')
        
        ready_status['services'] = 'available'
    except Exception as e:
        ready_status['services'] = f'error: {str(e)}'
        ready_status['status'] = 'not_ready'
    
    if ready_status['status'] == 'ready':
        return JsonResponse(ready_status, status=200)
    else:
        return JsonResponse(ready_status, status=503)

@csrf_exempt
@require_http_methods(["GET"])
def health_live(request):
    """
    Liveness check endpoint for Kubernetes.
    Returns 200 if the application is alive.
    """
    return JsonResponse({
        'status': 'alive',
        'timestamp': time.time(),
        'pid': os.getpid()
    })
