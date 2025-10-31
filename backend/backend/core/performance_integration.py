"""
Performance Optimization Integration
====================================
Central integration point for all performance optimizations.

Import and call initialize_performance_optimizations() in your FastAPI app.
"""

from __future__ import annotations

import logging
import os
from typing import Optional

logger = logging.getLogger(__name__)


def initialize_performance_optimizations(app) -> None:
    """
    Initialize all performance optimizations for FastAPI app.
    
    This function sets up:
    - Startup performance optimizations (uvloop, orjson)
    - OpenTelemetry tracing
    - Pyroscope profiling
    - Prometheus metrics endpoint
    - SLO monitoring
    
    Args:
        app: FastAPI application instance
    """
    try:
        # 1. Startup performance optimizations
        try:
            from core.startup_perf import apply_fastapi_optimizations
            apply_fastapi_optimizations(app)
            logger.info("✅ Startup performance optimizations applied")
        except Exception as e:
            logger.warning(f"⚠️ Startup optimizations failed: {e}")
        
        # 2. OpenTelemetry tracing
        try:
            from core.telemetry import setup_otel
            setup_otel(app)
            logger.info("✅ OpenTelemetry instrumentation enabled")
        except Exception as e:
            logger.warning(f"⚠️ OpenTelemetry setup failed: {e}")
        
        # 3. Pyroscope profiling
        try:
            from core.pyroscope_config import setup_pyroscope
            pyroscope_server = os.getenv("PYROSCOPE_SERVER_ADDRESS", "http://pyroscope:4040")
            setup_pyroscope(
                app_name="richesreach-backend",
                server_address=pyroscope_server,
                tags={
                    "environment": os.getenv("ENVIRONMENT", "development"),
                    "service": "backend"
                }
            )
            logger.info("✅ Pyroscope profiling enabled")
        except Exception as e:
            logger.warning(f"⚠️ Pyroscope setup failed: {e}")
        
        # 4. Prometheus metrics endpoint (only if not already mounted)
        try:
            from prometheus_client import make_asgi_app
            # Check if /metrics already exists
            metrics_exists = any(route.path == "/metrics" for route in app.routes)
            if not metrics_exists:
                metrics_app = make_asgi_app()
                app.mount("/metrics", metrics_app)
                logger.info("✅ Prometheus metrics endpoint mounted at /metrics")
            else:
                logger.info("✅ Prometheus metrics endpoint already exists")
        except ImportError:
            logger.warning("⚠️ prometheus_client not installed, metrics endpoint not available")
        except Exception as e:
            logger.warning(f"⚠️ Prometheus metrics failed: {e}")
        
        # 5. Initialize SLO monitoring
        try:
            from core.performance_slo import get_slo_monitor
            monitor = get_slo_monitor()
            logger.info("✅ SLO monitoring initialized")
        except Exception as e:
            logger.warning(f"⚠️ SLO monitoring failed: {e}")
        
        # 6. Initialize metrics exporter
        try:
            from core.metrics_exporter import get_metrics_exporter
            exporter = get_metrics_exporter()
            logger.info("✅ Metrics exporter initialized")
        except Exception as e:
            logger.warning(f"⚠️ Metrics exporter failed: {e}")
        
        logger.info("✅ Performance optimizations initialized successfully")
        
    except Exception as e:
        logger.error(f"❌ Failed to initialize performance optimizations: {e}")


def add_performance_middleware(app) -> None:
    """
    Add performance monitoring middleware to FastAPI app.
    
    Args:
        app: FastAPI application instance
    """
    try:
        from starlette.middleware.base import BaseHTTPMiddleware
        from core.performance_slo import get_slo_monitor
        from core.metrics_exporter import get_metrics_exporter
        import time
        
        monitor = get_slo_monitor()
        exporter = get_metrics_exporter()
        
        @app.middleware("http")
        async def performance_middleware(request, call_next):
            """Middleware to track API latency and metrics."""
            start_time = time.perf_counter()
            method = request.method
            path = request.url.path
            
            try:
                response = await call_next(request)
                status = response.status_code
                success = 200 <= status < 400
                
                # Calculate latency
                latency_ms = (time.perf_counter() - start_time) * 1000
                
                # Record metrics
                monitor.record_api(latency_ms, success)
                exporter.record_api_latency(method, path, latency_ms, status)
                
                # Add latency header
                response.headers["X-Response-Time-Ms"] = f"{latency_ms:.2f}"
                
                return response
                
            except Exception as e:
                latency_ms = (time.perf_counter() - start_time) * 1000
                monitor.record_api(latency_ms, success=False)
                exporter.record_api_latency(method, path, latency_ms, 500)
                raise
        
        logger.info("✅ Performance middleware added")
        
    except Exception as e:
        logger.warning(f"⚠️ Performance middleware setup failed: {e}")

