"""
Performance SLO Monitoring
==========================
Tracks and enforces Service Level Objectives for latency and reliability.

Targets:
- p50 ≤ 25 ms for API
- p95 ≤ 80 ms for API  
- p95 ≤ 50 ms per ML inference
- 99.9% success rate
"""

from __future__ import annotations

import time
import logging
from typing import Dict, List, Optional
from dataclasses import dataclass, field
from collections import deque
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


@dataclass
class SLOTargets:
    """SLO targets for different operation types."""
    api_p50_ms: float = 25.0
    api_p95_ms: float = 80.0
    ml_inference_p95_ms: float = 50.0
    success_rate: float = 0.999  # 99.9%


@dataclass
class LatencyMetric:
    """Single latency measurement."""
    operation: str
    latency_ms: float
    timestamp: datetime = field(default_factory=datetime.now)
    success: bool = True


class SLOMonitor:
    """
    Monitors performance against SLO targets.
    
    Tracks latency percentiles and success rates.
    """
    
    def __init__(
        self,
        targets: Optional[SLOTargets] = None,
        window_size: int = 1000
    ):
        """
        Initialize SLO monitor.
        
        Args:
            targets: SLO targets (uses defaults if None)
            window_size: Number of metrics to keep in sliding window
        """
        self.targets = targets or SLOTargets()
        self.window_size = window_size
        
        # Metrics storage
        self.api_metrics: deque = deque(maxlen=window_size)
        self.ml_metrics: deque = deque(maxlen=window_size)
        self.errors: deque = deque(maxlen=window_size)
    
    def record_api(
        self,
        latency_ms: float,
        success: bool = True
    ) -> None:
        """Record an API operation."""
        metric = LatencyMetric(
            operation="api",
            latency_ms=latency_ms,
            success=success
        )
        self.api_metrics.append(metric)
        if not success:
            self.errors.append(metric)
    
    def record_ml(
        self,
        latency_ms: float,
        success: bool = True
    ) -> None:
        """Record an ML inference operation."""
        metric = LatencyMetric(
            operation="ml",
            latency_ms=latency_ms,
            success=success
        )
        self.ml_metrics.append(metric)
        if not success:
            self.errors.append(metric)
    
    def get_percentile(self, metrics: deque, percentile: float) -> Optional[float]:
        """Calculate percentile from metrics."""
        if not metrics:
            return None
        
        sorted_latencies = sorted([m.latency_ms for m in metrics])
        index = int(len(sorted_latencies) * percentile / 100.0)
        index = min(index, len(sorted_latencies) - 1)
        return sorted_latencies[index]
    
    def check_slo_compliance(self) -> Dict[str, bool]:
        """
        Check if current metrics meet SLO targets.
        
        Returns:
            Dictionary of SLO checks (True = compliant)
        """
        checks = {}
        
        # API p50
        api_p50 = self.get_percentile(self.api_metrics, 50)
        checks['api_p50'] = (
            api_p50 is None or api_p50 <= self.targets.api_p50_ms
        )
        
        # API p95
        api_p95 = self.get_percentile(self.api_metrics, 95)
        checks['api_p95'] = (
            api_p95 is None or api_p95 <= self.targets.api_p95_ms
        )
        
        # ML p95
        ml_p95 = self.get_percentile(self.ml_metrics, 95)
        checks['ml_p95'] = (
            ml_p95 is None or ml_p95 <= self.targets.ml_inference_p95_ms
        )
        
        # Success rate
        total_requests = len(self.api_metrics) + len(self.ml_metrics)
        if total_requests > 0:
            success_rate = 1.0 - (len(self.errors) / total_requests)
            checks['success_rate'] = success_rate >= self.targets.success_rate
        else:
            checks['success_rate'] = True  # No data yet
        
        return checks
    
    def get_stats(self) -> Dict[str, Any]:
        """Get current performance statistics."""
        api_p50 = self.get_percentile(self.api_metrics, 50)
        api_p95 = self.get_percentile(self.api_metrics, 95)
        ml_p95 = self.get_percentile(self.ml_metrics, 95)
        
        total = len(self.api_metrics) + len(self.ml_metrics)
        success_rate = (
            1.0 - (len(self.errors) / total) if total > 0 else 1.0
        )
        
        return {
            "api_p50_ms": api_p50,
            "api_p95_ms": api_p95,
            "ml_p95_ms": ml_p95,
            "success_rate": success_rate,
            "total_requests": total,
            "errors": len(self.errors),
            "slo_compliant": all(self.check_slo_compliance().values())
        }


# Global SLO monitor instance
_slo_monitor: Optional[SLOMonitor] = None


def get_slo_monitor() -> SLOMonitor:
    """Get global SLO monitor instance."""
    global _slo_monitor
    if _slo_monitor is None:
        _slo_monitor = SLOMonitor()
    return _slo_monitor


class SLODecorator:
    """Decorator for automatic SLO tracking."""
    
    def __init__(self, operation_type: str = "api"):
        self.operation_type = operation_type
    
    def __call__(self, func):
        """Decorator implementation."""
        async def async_wrapper(*args, **kwargs):
            monitor = get_slo_monitor()
            start = time.perf_counter()
            success = True
            try:
                result = await func(*args, **kwargs)
                return result
            except Exception:
                success = False
                raise
            finally:
                latency_ms = (time.perf_counter() - start) * 1000
                if self.operation_type == "api":
                    monitor.record_api(latency_ms, success)
                else:
                    monitor.record_ml(latency_ms, success)
        
        def sync_wrapper(*args, **kwargs):
            monitor = get_slo_monitor()
            start = time.perf_counter()
            success = True
            try:
                result = func(*args, **kwargs)
                return result
            except Exception:
                success = False
                raise
            finally:
                latency_ms = (time.perf_counter() - start) * 1000
                if self.operation_type == "api":
                    monitor.record_api(latency_ms, success)
                else:
                    monitor.record_ml(latency_ms, success)
        
        import inspect
        if inspect.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper

