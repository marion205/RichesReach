# observability.py
from prometheus_client import Counter, Histogram
import time
from contextlib import contextmanager

REQUEST_COUNT = Counter("rr_requests_total", "Total requests", ["route", "status"])
REQUEST_LATENCY = Histogram("rr_request_latency_seconds", "Request latency seconds", ["route"])

@contextmanager
def observe(route: str):
    start = time.perf_counter()
    try:
        yield
        REQUEST_COUNT.labels(route=route, status="success").inc()
    except Exception:
        REQUEST_COUNT.labels(route=route, status="error").inc()
        raise
    finally:
        REQUEST_LATENCY.labels(route=route).observe(time.perf_counter() - start)
