"""
Pyroscope Continuous Profiling Configuration
============================================
Enables continuous profiling for performance analysis.

Helps identify CPU/memory hotspots in production.
"""

from __future__ import annotations

import os
import logging

logger = logging.getLogger(__name__)

# Optional Pyroscope import
try:
    import pyroscope
    PYROSCOPE_AVAILABLE = True
except ImportError:
    PYROSCOPE_AVAILABLE = False
    logger.warning("pyroscope not installed, profiling disabled")


def setup_pyroscope(
    app_name: str = "richesreach-backend",
    server_address: str = None,
    tags: dict = None
) -> None:
    """
    Setup Pyroscope continuous profiling.
    
    Args:
        app_name: Application name for profiling
        server_address: Pyroscope server address (defaults to env var)
        tags: Additional tags for profiling
    """
    if not PYROSCOPE_AVAILABLE:
        logger.warning("Pyroscope not available, skipping setup")
        return
    
    try:
        server = server_address or os.getenv(
            "PYROSCOPE_SERVER_ADDRESS",
            "http://pyroscope:4040"
        )
        
        default_tags = {
            "environment": os.getenv("ENVIRONMENT", "development"),
            "service": "backend",
        }
        
        if tags:
            default_tags.update(tags)
        
        pyroscope.configure(
            application_name=app_name,
            server_address=server,
            tags=default_tags,
            # Profile CPU and allocations
            enable_logging=True,
            detect_subprocesses=True,
            oncpu=True,
            native=True,
        )
        
        logger.info(f"✅ Pyroscope profiling enabled: {server}")
        
    except Exception as e:
        logger.error(f"Failed to setup Pyroscope: {e}")


def enable_pyroscope_middleware():
    """
    Enable Pyroscope middleware for FastAPI/Django.
    
    Add to FastAPI app:
        from core.pyroscope_config import enable_pyroscope_middleware
        enable_pyroscope_middleware()
    """
    if not PYROSCOPE_AVAILABLE:
        return
    
    # Pyroscope automatically instruments when configured
    # No explicit middleware needed for FastAPI/Django
    pass

