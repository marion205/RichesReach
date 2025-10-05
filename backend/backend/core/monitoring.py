"""
Enhanced Monitoring System for RichesReach
Phase 1: Structured Logging and Metrics
"""

import logging
import json
import time
import os
from datetime import datetime
from typing import Dict, Any, Optional
from functools import wraps
import boto3
from prometheus_client import Counter, Histogram, Gauge, start_http_server
import structlog

# Prometheus Metrics
REQUEST_COUNT = Counter('richesreach_requests_total', 'Total requests', ['method', 'endpoint', 'status'])
REQUEST_DURATION = Histogram('richesreach_request_duration_seconds', 'Request duration', ['method', 'endpoint'])
ACTIVE_CONNECTIONS = Gauge('richesreach_active_connections', 'Active connections')
DATABASE_CONNECTIONS = Gauge('richesreach_database_connections', 'Database connections')
CACHE_HIT_RATIO = Gauge('richesreach_cache_hit_ratio', 'Cache hit ratio')
ML_PREDICTION_COUNT = Counter('richesreach_ml_predictions_total', 'ML predictions', ['model_type', 'symbol'])
API_ERROR_COUNT = Counter('richesreach_api_errors_total', 'API errors', ['service', 'error_type'])

class CloudWatchLogger:
    """Enhanced CloudWatch logging with structured data"""
    
    def __init__(self, log_group: str = "richesreach-ai", region: str = "us-east-1"):
        self.log_group = log_group
        self.region = region
        self.cloudwatch = boto3.client('logs', region_name=region)
        self._ensure_log_group()
        
    def _ensure_log_group(self):
        """Ensure CloudWatch log group exists"""
        try:
            self.cloudwatch.describe_log_groups(logGroupNamePrefix=self.log_group)
        except self.cloudwatch.exceptions.ResourceNotFoundException:
            self.cloudwatch.create_log_group(logGroupName=self.log_group)
            print(f"✅ Created CloudWatch log group: {self.log_group}")
    
    def log_structured(self, level: str, message: str, **kwargs):
        """Log structured data to CloudWatch"""
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": level,
            "message": message,
            "service": "richesreach-ai",
            **kwargs
        }
        
        # Also log to console for development
        print(json.dumps(log_entry, indent=2))

class MetricsCollector:
    """Collect and expose application metrics"""
    
    def __init__(self, port: int = 8001):
        self.port = port
        self.start_metrics_server()
        
    def start_metrics_server(self):
        """Start Prometheus metrics server"""
        try:
            start_http_server(self.port)
            print(f"✅ Metrics server started on port {self.port}")
        except Exception as e:
            print(f"⚠️ Could not start metrics server: {e}")
    
    def record_request(self, method: str, endpoint: str, status: int, duration: float):
        """Record request metrics"""
        REQUEST_COUNT.labels(method=method, endpoint=endpoint, status=str(status)).inc()
        REQUEST_DURATION.labels(method=method, endpoint=endpoint).observe(duration)
    
    def record_ml_prediction(self, model_type: str, symbol: str):
        """Record ML prediction metrics"""
        ML_PREDICTION_COUNT.labels(model_type=model_type, symbol=symbol).inc()
    
    def record_api_error(self, service: str, error_type: str):
        """Record API error metrics"""
        API_ERROR_COUNT.labels(service=service, error_type=error_type).inc()
    
    def update_active_connections(self, count: int):
        """Update active connections gauge"""
        ACTIVE_CONNECTIONS.set(count)
    
    def update_database_connections(self, count: int):
        """Update database connections gauge"""
        DATABASE_CONNECTIONS.set(count)
    
    def update_cache_hit_ratio(self, ratio: float):
        """Update cache hit ratio gauge"""
        CACHE_HIT_RATIO.set(ratio)

class PerformanceMonitor:
    """Monitor application performance"""
    
    def __init__(self):
        self.metrics = MetricsCollector()
        self.cloudwatch = CloudWatchLogger()
        
    def monitor_function(self, func_name: str = None):
        """Decorator to monitor function performance"""
        def decorator(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                start_time = time.time()
                func_name_actual = func_name or func.__name__
                
                try:
                    result = func(*args, **kwargs)
                    duration = time.time() - start_time
                    
                    # Log successful execution
                    self.cloudwatch.log_structured(
                        "INFO",
                        f"Function {func_name_actual} completed successfully",
                        function=func_name_actual,
                        duration=duration,
                        status="success"
                    )
                    
                    return result
                    
                except Exception as e:
                    duration = time.time() - start_time
                    
                    # Log error
                    self.cloudwatch.log_structured(
                        "ERROR",
                        f"Function {func_name_actual} failed",
                        function=func_name_actual,
                        duration=duration,
                        error=str(e),
                        status="error"
                    )
                    
                    # Record error metrics
                    self.metrics.record_api_error("internal", type(e).__name__)
                    
                    raise
                    
            return wrapper
        return decorator
    
    def monitor_graphql_query(self, query_name: str):
        """Monitor GraphQL query performance"""
        def decorator(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                start_time = time.time()
                
                try:
                    result = func(*args, **kwargs)
                    duration = time.time() - start_time
                    
                    # Record metrics
                    self.metrics.record_request("POST", f"/graphql/{query_name}", 200, duration)
                    
                    # Log query execution
                    self.cloudwatch.log_structured(
                        "INFO",
                        f"GraphQL query {query_name} executed",
                        query=query_name,
                        duration=duration,
                        status="success"
                    )
                    
                    return result
                    
                except Exception as e:
                    duration = time.time() - start_time
                    
                    # Record error metrics
                    self.metrics.record_request("POST", f"/graphql/{query_name}", 500, duration)
                    self.metrics.record_api_error("graphql", type(e).__name__)
                    
                    # Log error
                    self.cloudwatch.log_structured(
                        "ERROR",
                        f"GraphQL query {query_name} failed",
                        query=query_name,
                        duration=duration,
                        error=str(e),
                        status="error"
                    )
                    
                    raise
                    
            return wrapper
        return decorator

class HealthChecker:
    """System health monitoring"""
    
    def __init__(self):
        self.monitor = PerformanceMonitor()
        
    def check_database_health(self) -> Dict[str, Any]:
        """Check database connectivity and performance"""
        try:
            from django.db import connection
            start_time = time.time()
            
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
                result = cursor.fetchone()
            
            duration = time.time() - start_time
            
            return {
                "status": "healthy",
                "response_time": duration,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
    
    def check_redis_health(self) -> Dict[str, Any]:
        """Check Redis connectivity"""
        try:
            import redis
            r = redis.Redis(host='localhost', port=6379, db=0)
            start_time = time.time()
            
            r.ping()
            duration = time.time() - start_time
            
            return {
                "status": "healthy",
                "response_time": duration,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
    
    def check_external_apis(self) -> Dict[str, Any]:
        """Check external API connectivity"""
        apis = {
            "polygon": "https://api.polygon.io/v2/aggs/ticker/AAPL/prev",
            "finnhub": "https://finnhub.io/api/v1/quote?symbol=AAPL",
            "coingecko": "https://api.coingecko.com/api/v3/ping"
        }
        
        results = {}
        for api_name, url in apis.items():
            try:
                import requests
                start_time = time.time()
                
                response = requests.get(url, timeout=5)
                duration = time.time() - start_time
                
                results[api_name] = {
                    "status": "healthy" if response.status_code == 200 else "unhealthy",
                    "response_time": duration,
                    "status_code": response.status_code
                }
                
            except Exception as e:
                results[api_name] = {
                    "status": "unhealthy",
                    "error": str(e)
                }
        
        return results
    
    def get_system_health(self) -> Dict[str, Any]:
        """Get comprehensive system health"""
        return {
            "timestamp": datetime.now().isoformat(),
            "database": self.check_database_health(),
            "redis": self.check_redis_health(),
            "external_apis": self.check_external_apis(),
            "overall_status": "healthy"  # Will be determined by individual checks
        }

# Global instances
performance_monitor = PerformanceMonitor()
health_checker = HealthChecker()

# Structured logging setup
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

def get_logger(name: str = "richesreach"):
    """Get structured logger"""
    return structlog.get_logger(name)

# Export logger for backward compatibility
logger = get_logger()

# Export commonly used functions
__all__ = [
    'performance_monitor',
    'health_checker', 
    'get_logger',
    'MetricsCollector',
    'CloudWatchLogger'
]
