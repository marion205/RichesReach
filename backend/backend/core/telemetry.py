"""
OpenTelemetry Instrumentation
=============================
Adds distributed tracing for observability.

Enables end-to-end tracing across API → Model → Database layers.
"""

from __future__ import annotations

import os
import logging
from typing import Optional

logger = logging.getLogger(__name__)

# Optional OpenTelemetry imports
try:
    from opentelemetry import trace
    from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
    from opentelemetry.instrumentation.psycopg2 import Psycopg2Instrumentor
    from opentelemetry.instrumentation.redis import RedisInstrumentor
    from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.resources import Resource
    from opentelemetry.sdk.trace.export import BatchSpanProcessor
    OTEL_AVAILABLE = True
except ImportError:
    OTEL_AVAILABLE = False
    logger.warning("OpenTelemetry not installed, tracing disabled")


def setup_otel(app=None):
    """
    Setup OpenTelemetry instrumentation.
    
    Args:
        app: FastAPI app instance (optional, can instrument later)
    """
    if not OTEL_AVAILABLE:
        logger.warning("OpenTelemetry not available, skipping setup")
        return
    
    try:
        # Create resource
        resource = Resource.create({
            "service.name": "richesreach-backend",
            "service.version": os.getenv("APP_VERSION", "unknown")
        })
        
        # Create provider
        provider = TracerProvider(resource=resource)
        
        # Add exporter
        otlp_endpoint = os.getenv(
            "OTEL_EXPORTER_OTLP_ENDPOINT",
            "http://localhost:4318/v1/traces"
        )
        processor = BatchSpanProcessor(
            OTLPSpanExporter(endpoint=otlp_endpoint)
        )
        provider.add_span_processor(processor)
        
        # Set global provider
        trace.set_tracer_provider(provider)
        
        # Instrument FastAPI
        if app is not None:
            FastAPIInstrumentor.instrument_app(app)
            logger.info("✅ FastAPI instrumented with OpenTelemetry")
        
        # Instrument database and Redis
        try:
            Psycopg2Instrumentor().instrument()
            logger.info("✅ PostgreSQL instrumented")
        except Exception as e:
            logger.warning(f"Failed to instrument PostgreSQL: {e}")
        
        try:
            RedisInstrumentor().instrument()
            logger.info("✅ Redis instrumented")
        except Exception as e:
            logger.warning(f"Failed to instrument Redis: {e}")
        
        logger.info("✅ OpenTelemetry setup complete")
        
    except Exception as e:
        logger.error(f"Failed to setup OpenTelemetry: {e}")


def get_tracer(name: str = "richesreach"):
    """
    Get a tracer for manual instrumentation.
    
    Args:
        name: Tracer name
        
    Returns:
        Tracer instance (or no-op if OTEL unavailable)
    """
    if not OTEL_AVAILABLE:
        # Return no-op tracer
        class NoOpTracer:
            def start_span(self, *args, **kwargs):
                return NoOpSpan()
        class NoOpSpan:
            def __enter__(self):
                return self
            def __exit__(self, *args):
                pass
            def set_attribute(self, *args, **kwargs):
                pass
            def add_event(self, *args, **kwargs):
                pass
        return NoOpTracer()
    
    return trace.get_tracer(name)

