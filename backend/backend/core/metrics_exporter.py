"""
SLO Metrics Exporter
====================
Exports SLO metrics to CloudWatch and Prometheus.

Tracks latency, success rate, and cost metrics.
"""

from __future__ import annotations

import logging
import time
from typing import Dict, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

# Optional imports
try:
    import boto3
    from prometheus_client import Counter, Histogram, Gauge
    BOTO3_AVAILABLE = True
    PROMETHEUS_AVAILABLE = True
except ImportError:
    BOTO3_AVAILABLE = False
    PROMETHEUS_AVAILABLE = False
    logger.warning("boto3 or prometheus_client not available, metrics export disabled")


# Prometheus metrics (if available)
if PROMETHEUS_AVAILABLE:
    api_latency = Histogram(
        'api_request_duration_seconds',
        'API request duration in seconds',
        ['method', 'endpoint', 'status']
    )
    
    ml_latency = Histogram(
        'ml_inference_duration_seconds',
        'ML inference duration in seconds',
        ['model']
    )
    
    api_requests = Counter(
        'api_requests_total',
        'Total API requests',
        ['method', 'endpoint', 'status']
    )
    
    cache_hits = Counter(
        'redis_cache_hits_total',
        'Total cache hits',
        ['model']
    )
    
    cache_requests = Counter(
        'redis_cache_requests_total',
        'Total cache requests',
        ['model']
    )
    
    slo_compliant_gauge = Gauge(
        'slo_compliant',
        'SLO compliance status (1 = compliant, 0 = non-compliant)'
    )
    
    llm_cost_per_mau_gauge = Gauge(
        'llm_cost_per_mau',
        'LLM cost per monthly active user'
    )
    
    cost_per_decision_gauge = Gauge(
        'cost_per_decision',
        'Cost per AI decision'
    )
else:
    # Dummy metrics if Prometheus not available
    api_latency = None
    ml_latency = None
    api_requests = None
    cache_hits = None
    cache_requests = None
    slo_compliant_gauge = None
    llm_cost_per_mau_gauge = None
    cost_per_decision_gauge = None


class MetricsExporter:
    """Exports metrics to CloudWatch and Prometheus."""
    
    def __init__(self):
        self.cloudwatch = None
        self.namespace = "RichesReach"
        
        if BOTO3_AVAILABLE:
            try:
                self.cloudwatch = boto3.client('cloudwatch')
            except Exception as e:
                logger.warning(f"Failed to initialize CloudWatch: {e}")
    
    def record_api_latency(
        self,
        method: str,
        endpoint: str,
        latency_ms: float,
        status: int
    ) -> None:
        """Record API latency."""
        # Prometheus
        if PROMETHEUS_AVAILABLE and api_latency and api_requests:
            api_latency.labels(
                method=method,
                endpoint=endpoint,
                status=str(status)
            ).observe(latency_ms / 1000.0)
            
            api_requests.labels(
                method=method,
                endpoint=endpoint,
                status=str(status)
            ).inc()
        
        # CloudWatch
        if self.cloudwatch:
            try:
                self.cloudwatch.put_metric_data(
                    Namespace=self.namespace,
                    MetricData=[
                        {
                            'MetricName': 'API_Latency',
                            'Dimensions': [
                                {'Name': 'Method', 'Value': method},
                                {'Name': 'Endpoint', 'Value': endpoint},
                                {'Name': 'Status', 'Value': str(status)}
                            ],
                            'Value': latency_ms,
                            'Unit': 'Milliseconds',
                            'Timestamp': datetime.now()
                        }
                    ]
                )
            except Exception as e:
                logger.warning(f"Failed to send CloudWatch metric: {e}")
    
    def record_ml_latency(
        self,
        model: str,
        latency_ms: float
    ) -> None:
        """Record ML inference latency."""
        # Prometheus
        if PROMETHEUS_AVAILABLE and ml_latency:
            ml_latency.labels(model=model).observe(latency_ms / 1000.0)
        
        # CloudWatch
        if self.cloudwatch:
            try:
                self.cloudwatch.put_metric_data(
                    Namespace=self.namespace,
                    MetricData=[
                        {
                            'MetricName': 'ML_Inference_Latency',
                            'Dimensions': [
                                {'Name': 'Model', 'Value': model}
                            ],
                            'Value': latency_ms,
                            'Unit': 'Milliseconds',
                            'Timestamp': datetime.now()
                        }
                    ]
                )
            except Exception as e:
                logger.warning(f"Failed to send CloudWatch metric: {e}")
    
    def record_cache_stats(
        self,
        model: str,
        hit: bool
    ) -> None:
        """Record cache statistics."""
        if PROMETHEUS_AVAILABLE and cache_requests:
            cache_requests.labels(model=model).inc()
            if hit and cache_hits:
                cache_hits.labels(model=model).inc()
    
    def record_slo_compliance(
        self,
        compliant: bool
    ) -> None:
        """Record SLO compliance status."""
        if PROMETHEUS_AVAILABLE and slo_compliant_gauge:
            slo_compliant_gauge.set(1.0 if compliant else 0.0)
        
        if self.cloudwatch:
            try:
                self.cloudwatch.put_metric_data(
                    Namespace=self.namespace,
                    MetricData=[
                        {
                            'MetricName': 'SLO_Compliant',
                            'Value': 1.0 if compliant else 0.0,
                            'Unit': 'None',
                            'Timestamp': datetime.now()
                        }
                    ]
                )
            except Exception as e:
                logger.warning(f"Failed to send SLO metric: {e}")
    
    def record_cost_metrics(
        self,
        llm_cost_per_mau: float,
        cost_per_decision: float
    ) -> None:
        """Record cost metrics."""
        if PROMETHEUS_AVAILABLE:
            if llm_cost_per_mau_gauge:
                llm_cost_per_mau_gauge.set(llm_cost_per_mau)
            if cost_per_decision_gauge:
                cost_per_decision_gauge.set(cost_per_decision)
        
        if self.cloudwatch:
            try:
                self.cloudwatch.put_metric_data(
                    Namespace=self.namespace,
                    MetricData=[
                        {
                            'MetricName': 'LLM_Cost_Per_MAU',
                            'Value': llm_cost_per_mau,
                            'Unit': 'None',
                            'Timestamp': datetime.now()
                        },
                        {
                            'MetricName': 'Cost_Per_Decision',
                            'Value': cost_per_decision,
                            'Unit': 'None',
                            'Timestamp': datetime.now()
                        }
                    ]
                )
            except Exception as e:
                logger.warning(f"Failed to send cost metrics: {e}")


# Global metrics exporter
_metrics_exporter: Optional[MetricsExporter] = None


def get_metrics_exporter() -> MetricsExporter:
    """Get global metrics exporter instance."""
    global _metrics_exporter
    if _metrics_exporter is None:
        _metrics_exporter = MetricsExporter()
    return _metrics_exporter

