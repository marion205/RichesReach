"""
Startup Performance Optimizations
==================================
Global performance optimizations applied at application startup.

This module sets up:
- uvloop for faster async I/O
- orjson for faster JSON serialization
- Other global optimizations
"""

from __future__ import annotations

import asyncio
import logging
import json

logger = logging.getLogger(__name__)

# Try to use uvloop for faster async
try:
    import uvloop
    asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())
    logger.info("✅ uvloop enabled for faster async I/O")
except ImportError:
    logger.warning("uvloop not available, using default event loop")

# Try to use orjson for faster JSON
try:
    import orjson
    
    def orjson_dumps(v, *, default=None):
        """Fast JSON dumps using orjson."""
        if default is not None:
            return orjson.dumps(v, default=default).decode()
        return orjson.dumps(v).decode()
    
    ORJSON_AVAILABLE = True
    logger.info("✅ orjson available for faster JSON serialization")
except ImportError:
    ORJSON_AVAILABLE = False
    logger.warning("orjson not available, using standard json")
    
    def orjson_dumps(v, *, default=None):
        """Fallback to standard json."""
        return json.dumps(v, default=default)


def apply_fastapi_optimizations(app):
    """
    Apply optimizations to FastAPI app.
    
    Args:
        app: FastAPI application instance
    """
    # Use orjson response class if available
    if ORJSON_AVAILABLE:
        try:
            from fastapi.responses import ORJSONResponse
            app.default_response_class = ORJSONResponse
            logger.info("✅ FastAPI using ORJSONResponse")
        except Exception as e:
            logger.warning(f"Failed to set ORJSONResponse: {e}")


# For FastAPI integration example:
# from core.startup_perf import apply_fastapi_optimizations
# app = FastAPI()
# apply_fastapi_optimizations(app)

