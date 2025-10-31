# Monitoring Setup Guide

This directory contains monitoring infrastructure for RichesReach.

## Services

1. **Pyroscope** - Continuous profiling (http://localhost:4040)
2. **Grafana** - Dashboards (http://localhost:3000, admin/admin)
3. **Prometheus** - Metrics collection (http://localhost:9090)

## Quick Start

```bash
# Start all monitoring services
docker-compose -f docker-compose.yml -f docker-compose.monitoring.yml up -d

# Access dashboards
open http://localhost:3000  # Grafana
open http://localhost:4040  # Pyroscope
open http://localhost:9090   # Prometheus
```

## Grafana Dashboards

1. **SLO Dashboard** - Performance and reliability metrics
   - Location: `grafana/dashboards/slo-dashboard.json`
   - Metrics: Latency, success rate, cache hits, costs

## CloudWatch Dashboard

For AWS production, deploy the CloudWatch dashboard:

```bash
aws cloudwatch put-dashboard \
  --dashboard-name "RichesReach-SLO" \
  --dashboard-body file://cloudwatch/slo-dashboard.json
```

## Configuration

- **Datasources**: `grafana/datasources/datasources.yml`
- **Prometheus Config**: `prometheus/prometheus.yml`
- **Dashboards**: `grafana/dashboards/*.json`

## Integration

Add to your FastAPI app:

```python
# Enable profiling
from core.pyroscope_config import setup_pyroscope
setup_pyroscope("richesreach-backend")

# Export metrics
from prometheus_client import make_asgi_app
metrics_app = make_asgi_app()
app.mount("/metrics", metrics_app)

# Track metrics
from core.metrics_exporter import get_metrics_exporter
exporter = get_metrics_exporter()
exporter.record_api_latency("GET", "/health", 25.5, 200)
```

