"""
RAHA Performance Monitoring
Tracks query performance, cache hit rates, and optimization metrics
"""
import logging
import time
from typing import Dict, Any, Optional
from functools import wraps
from django.core.cache import cache
from django.db import connection
from django.utils import timezone
from collections import defaultdict
import json

logger = logging.getLogger(__name__)


class PerformanceMonitor:
    """Monitor and track performance metrics for RAHA queries"""
    
    def __init__(self):
        self.metrics = defaultdict(lambda: {
            'query_count': 0,
            'total_time': 0.0,
            'min_time': float('inf'),
            'max_time': 0.0,
            'cache_hits': 0,
            'cache_misses': 0,
            'db_queries': 0,
        })
        self._enabled = True
    
    def enable(self):
        """Enable performance monitoring"""
        self._enabled = True
    
    def disable(self):
        """Disable performance monitoring"""
        self._enabled = False
    
    def record_query(
        self,
        query_name: str,
        duration: float,
        cache_hit: bool = False,
        db_query_count: int = 0
    ):
        """Record a query performance metric"""
        if not self._enabled:
            return
        
        metric = self.metrics[query_name]
        metric['query_count'] += 1
        metric['total_time'] += duration
        metric['min_time'] = min(metric['min_time'], duration)
        metric['max_time'] = max(metric['max_time'], duration)
        
        if cache_hit:
            metric['cache_hits'] += 1
        else:
            metric['cache_misses'] += 1
        
        metric['db_queries'] += db_query_count
    
    def get_metrics(self) -> Dict[str, Dict[str, Any]]:
        """Get all performance metrics"""
        result = {}
        for query_name, metric in self.metrics.items():
            avg_time = (
                metric['total_time'] / metric['query_count']
                if metric['query_count'] > 0
                else 0.0
            )
            
            cache_hit_rate = (
                metric['cache_hits'] / (metric['cache_hits'] + metric['cache_misses']) * 100
                if (metric['cache_hits'] + metric['cache_misses']) > 0
                else 0.0
            )
            
            result[query_name] = {
                'query_count': metric['query_count'],
                'avg_time_ms': round(avg_time * 1000, 2),
                'min_time_ms': round(metric['min_time'] * 1000, 2) if metric['min_time'] != float('inf') else 0,
                'max_time_ms': round(metric['max_time'] * 1000, 2),
                'total_time_ms': round(metric['total_time'] * 1000, 2),
                'cache_hit_rate': round(cache_hit_rate, 2),
                'cache_hits': metric['cache_hits'],
                'cache_misses': metric['cache_misses'],
                'avg_db_queries': round(metric['db_queries'] / metric['query_count'], 2) if metric['query_count'] > 0 else 0,
            }
        
        return result
    
    def get_summary(self) -> Dict[str, Any]:
        """Get performance summary"""
        metrics = self.get_metrics()
        
        total_queries = sum(m['query_count'] for m in metrics.values())
        total_cache_hits = sum(m['cache_hits'] for m in metrics.values())
        total_cache_misses = sum(m['cache_misses'] for m in metrics.values())
        
        overall_cache_hit_rate = (
            total_cache_hits / (total_cache_hits + total_cache_misses) * 100
            if (total_cache_hits + total_cache_misses) > 0
            else 0.0
        )
        
        avg_query_time = sum(m['avg_time_ms'] for m in metrics.values()) / len(metrics) if metrics else 0
        
        return {
            'total_queries': total_queries,
            'overall_cache_hit_rate': round(overall_cache_hit_rate, 2),
            'avg_query_time_ms': round(avg_query_time, 2),
            'query_types': len(metrics),
            'metrics': metrics
        }
    
    def reset(self):
        """Reset all metrics"""
        self.metrics.clear()
    
    def export_metrics(self, filepath: Optional[str] = None) -> str:
        """Export metrics to JSON"""
        data = {
            'timestamp': timezone.now().isoformat(),
            'summary': self.get_summary(),
            'detailed_metrics': self.get_metrics()
        }
        
        json_str = json.dumps(data, indent=2)
        
        if filepath:
            with open(filepath, 'w') as f:
                f.write(json_str)
        
        return json_str


# Global performance monitor instance
_performance_monitor = PerformanceMonitor()


def get_performance_monitor() -> PerformanceMonitor:
    """Get the global performance monitor instance"""
    return _performance_monitor


def monitor_query_performance(query_name: str):
    """Decorator to monitor query performance"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            monitor = get_performance_monitor()
            
            # Count DB queries before
            initial_queries = len(connection.queries)
            
            # Check cache (if applicable)
            cache_hit = False
            if hasattr(kwargs.get('info'), 'context'):
                # Try to detect cache hit by checking if result is already available
                pass
            
            # Measure execution time
            start_time = time.time()
            result = func(*args, **kwargs)
            duration = time.time() - start_time
            
            # Count DB queries after
            final_queries = len(connection.queries)
            db_query_count = final_queries - initial_queries
            
            # Record metric
            monitor.record_query(query_name, duration, cache_hit, db_query_count)
            
            # Log if slow
            if duration > 0.1:  # > 100ms
                logger.warning(
                    f"⚠️ Slow query: {query_name} took {duration*1000:.2f}ms "
                    f"({db_query_count} DB queries)"
                )
            
            return result
        return wrapper
    return decorator


def log_performance_metrics():
    """Log current performance metrics"""
    monitor = get_performance_monitor()
    summary = monitor.get_summary()
    
    logger.info("📊 Performance Metrics Summary:")
    logger.info(f"  Total Queries: {summary['total_queries']}")
    logger.info(f"  Overall Cache Hit Rate: {summary['overall_cache_hit_rate']}%")
    logger.info(f"  Avg Query Time: {summary['avg_query_time_ms']}ms")
    logger.info(f"  Query Types: {summary['query_types']}")
    
    # Log top slowest queries
    metrics = summary['metrics']
    if metrics:
        sorted_queries = sorted(
            metrics.items(),
            key=lambda x: x[1]['avg_time_ms'],
            reverse=True
        )[:5]
        
        logger.info("  Top 5 Slowest Queries:")
        for query_name, metric in sorted_queries:
            logger.info(
                f"    {query_name}: {metric['avg_time_ms']}ms avg "
                f"({metric['cache_hit_rate']}% cache hit rate)"
            )


# Middleware for automatic performance monitoring
class PerformanceMonitoringMiddleware:
    """Django middleware to monitor GraphQL query performance"""
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        # Only monitor GraphQL requests
        if request.path == '/graphql/' or request.path.endswith('/graphql'):
            monitor = get_performance_monitor()
            
            # Count initial DB queries
            initial_queries = len(connection.queries)
            
            # Measure request time
            start_time = time.time()
            response = self.get_response(request)
            duration = time.time() - start_time
            
            # Count final DB queries
            final_queries = len(connection.queries)
            db_query_count = final_queries - initial_queries
            
            # Record metric
            monitor.record_query('graphql_request', duration, False, db_query_count)
            
            # Log slow requests
            if duration > 0.5:  # > 500ms
                logger.warning(
                    f"⚠️ Slow GraphQL request: {request.path} took {duration*1000:.2f}ms "
                    f"({db_query_count} DB queries)"
                )
            
            return response
        
        return self.get_response(request)

