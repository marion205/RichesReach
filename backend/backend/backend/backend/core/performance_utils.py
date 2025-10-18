"""
Performance instrumentation utilities for GraphQL resolvers
Provides timing and monitoring for query performance
"""
import time
import logging
from functools import wraps
from typing import Callable, Any

logger = logging.getLogger("perf")

def timeit(name: str, fn: Callable, *args, **kwargs) -> Any:
    """Time a function execution and log the result"""
    t0 = time.perf_counter()
    try:
        result = fn(*args, **kwargs)
        return result
    finally:
        elapsed_ms = (time.perf_counter() - t0) * 1000
        logger.info(f"{name}={elapsed_ms:.1f}ms")

def resolver_timer(resolver_name: str):
    """Decorator to time GraphQL resolvers"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            return timeit(f"resolver:{resolver_name}", func, *args, **kwargs)
        return wrapper
    return decorator

def cache_hit_timer(cache_key: str):
    """Time cache operations"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            return timeit(f"cache:{cache_key}", func, *args, **kwargs)
        return wrapper
    return decorator

def slow_query_monitor(threshold_ms: float = 1000.0):
    """Monitor for slow queries and log warnings"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            t0 = time.perf_counter()
            try:
                result = func(*args, **kwargs)
                return result
            finally:
                elapsed_ms = (time.perf_counter() - t0) * 1000
                if elapsed_ms > threshold_ms:
                    logger.warning(f"SLOW QUERY: {func.__name__} took {elapsed_ms:.1f}ms (threshold: {threshold_ms}ms)")
                else:
                    logger.info(f"query:{func.__name__}={elapsed_ms:.1f}ms")
        return wrapper
    return decorator
