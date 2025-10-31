#!/usr/bin/env python3
"""
Metrics Export Script
====================
Exports Prometheus metrics endpoint for scraping.

Add to your FastAPI app:
    from prometheus_client import make_asgi_app
    metrics_app = make_asgi_app()
    app.mount("/metrics", metrics_app)
"""

import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from prometheus_client import make_asgi_app, generate_latest
from fastapi import FastAPI
from fastapi.responses import Response

app = FastAPI()

# Create Prometheus metrics app
metrics_app = make_asgi_app()

@app.get("/metrics")
async def metrics():
    """Expose Prometheus metrics."""
    return Response(
        content=generate_latest(),
        media_type="text/plain"
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=9091)

