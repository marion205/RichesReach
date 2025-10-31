# Performance Optimization Implementation Guide

This guide covers the performance optimizations implemented to achieve:
- **Latency**: p50 ≤ 25ms, p95 ≤ 80ms for API; p95 ≤ 50ms per ML inference
- **Cost**: ≤ $0.01 per coached decision; ≤ $0.05/MAU for LLM
- **Reliability**: 99.9% success rate

## Quick Start

1. **Install dependencies**:
   ```bash
   pip install -r requirements_performance.txt
   ```

2. **Convert models to ONNX** (if using custom models):
   ```bash
   python scripts/convert_sklearn_to_onnx.py
   ```

3. **Quantize models** (for 2-6x speedup):
   ```bash
   python scripts/quantize_onnx.py model.onnx model.int8.onnx
   ```

4. **Update Gunicorn config**:
   The optimized `gunicorn.conf.py` is already configured. Use:
   ```bash
   gunicorn -c backend/gunicorn.conf.py final_complete_server:app
   ```

5. **Enable startup optimizations**:
   Add to your FastAPI app startup:
   ```python
   from core.startup_perf import apply_fastapi_optimizations
   from core.telemetry import setup_otel
   
   app = FastAPI()
   apply_fastapi_optimizations(app)
   setup_otel(app)
   ```

## Components

### 1. ONNX Runtime (`core/onnx_runtime.py`)

High-performance ML inference with quantization support.

**Usage**:
```python
from core.onnx_runtime import get_onnx_session, run_onnx_inference
import numpy as np

# Get session
session = get_onnx_session("models/regime_predictor.onnx", use_quantized=True)

# Run inference
inputs = {"input": np.array([[1.0, 2.0, 3.0]])}
outputs = run_onnx_inference("models/regime_predictor.onnx", inputs)
```

**Benefits**: 2-6x faster inference with INT8 quantization, lower memory usage

### 2. Micro-Batching (`core/batcher.py`)

Groups concurrent inference requests for efficiency.

**Usage**:
```python
from core.batcher import MicroBatcher
import numpy as np

# Create batcher
def run_batch(inputs):
    # Your model inference function
    return [model.predict(x) for x in inputs]

batcher = MicroBatcher(runner=run_batch, max_wait_ms=5, max_batch_size=64)

# Use in async endpoint
async def predict_endpoint(features):
    result = await batcher.infer(features)
    return result
```

**Benefits**: 2-4x throughput improvement, reduced model call overhead

### 3. Feature-Hash Caching (`core/cache_wrapper.py`)

Redis-backed caching for ML inference results.

**Usage**:
```python
from core.cache_wrapper import get_feature_cache

cache = get_feature_cache()

def my_model_inference(features):
    # Your inference logic
    return {"prediction": 0.85, "confidence": 0.92}

# Cached prediction
result = cache.cached_predict(
    model="regime_predictor",
    features={"vix": 15.2, "spy_return": 0.02},
    infer_fn=my_model_inference,
    ttl=300  # 5 minutes
)
```

**Benefits**: 30-70% cache hit rate, instant responses for repeated queries

### 4. LLM Caching (`core/llm_cache.py`)

Caches LLM responses to reduce costs.

**Usage**:
```python
from core.llm_cache import get_llm_cache

cache = get_llm_cache()

def call_openai(model, prompt, **kwargs):
    # Your OpenAI call
    return openai.chat.completions.create(...).choices[0].message.content

# Cached LLM call
response = cache.cached_call(
    model="gpt-4o-mini",
    payload={"prompt": "Explain options trading"},
    caller=call_openai,
    ttl=21600  # 6 hours
)
```

**Benefits**: 30-70% cost reduction on LLM calls, faster responses

### 5. Performance Monitoring (`core/performance_slo.py`)

Tracks latency and reliability against SLO targets.

**Usage**:
```python
from core.performance_slo import get_slo_monitor, SLODecorator

monitor = get_slo_monitor()

# Manual tracking
import time
start = time.perf_counter()
# ... your code ...
monitor.record_api((time.perf_counter() - start) * 1000, success=True)

# Or use decorator
@SLODecorator(operation_type="api")
async def my_endpoint():
    # Your endpoint code
    return {"result": "ok"}

# Check SLO compliance
stats = monitor.get_stats()
if not stats["slo_compliant"]:
    # Trigger alerts or degrade gracefully
    pass
```

### 6. API Contracts (`core/contracts.py`)

Structured response contracts for consistency and caching.

**Usage**:
```python
from core.contracts import Contract, CONTRACT_EXAMPLE

# Validate response matches contract
response = {
    "action": "deposit",
    "confidence": 0.83,
    "reason": {...},
    "limits": {...}
}
contract = Contract(**response)  # Validates structure

# Use in API endpoint
@app.post("/api/coach/recommend")
async def get_recommendation():
    # Your AI logic
    return Contract(**CONTRACT_EXAMPLE)
```

## Integration with Existing Code

### Update ML Service

```python
# In core/ml_service.py
from core.onnx_runtime import get_onnx_session
from core.cache_wrapper import get_feature_cache
from core.batcher import MicroBatcher

class MLService:
    def __init__(self):
        self.regime_model = get_onnx_session("models/regime.onnx")
        self.cache = get_feature_cache()
        self.batcher = MicroBatcher(runner=self._batch_infer)
    
    async def predict_regime(self, features):
        # Use cached batched prediction
        return await self.batcher.infer(features)
    
    def _batch_infer(self, inputs):
        # Batch inference
        outputs = self.regime_model.run(None, {"input": inputs})
        return outputs[0]
```

### Update AI Router

```python
# In core/ai_router.py
from core.llm_cache import get_llm_cache

class AIRouter:
    def __init__(self):
        self.llm_cache = get_llm_cache()
    
    async def route(self, prompt, model="gpt-4o-mini"):
        # Use cached LLM calls
        return self.llm_cache.cached_call(
            model=model,
            payload={"messages": [{"role": "user", "content": prompt}]},
            caller=self._call_llm,
            ttl=21600
        )
```

## Deployment Checklist

- [ ] Install `requirements_performance.txt`
- [ ] Convert ML models to ONNX format
- [ ] Quantize models with `scripts/quantize_onnx.py`
- [ ] Update `gunicorn.conf.py` (already done)
- [ ] Enable Redis caching (configure `REDIS_URL`)
- [ ] Setup PgBouncer (optional but recommended)
- [ ] Enable OpenTelemetry (optional but recommended)
- [ ] Add SLO monitoring endpoints
- [ ] Test with load (target: p95 < 80ms)
- [ ] Monitor cache hit rates (target: >30%)
- [ ] Monitor LLM cost reduction (target: >30%)

## Performance Targets

| Metric | Target | Measurement |
|--------|--------|-------------|
| API p50 | ≤ 25ms | `core/performance_slo.py` |
| API p95 | ≤ 80ms | `core/performance_slo.py` |
| ML p95 | ≤ 50ms | `core/performance_slo.py` |
| Success Rate | ≥ 99.9% | `core/performance_slo.py` |
| Cache Hit Rate | ≥ 30% | Redis monitoring |
| LLM Cost/MAU | ≤ $0.05 | Cost tracking |

## Next Steps

1. **Week 1**: ONNX conversion + caching
2. **Week 2**: Micro-batching + Feast integration
3. **Week 3**: PgBouncer + index optimization
4. **Week 4**: Profiling + final tuning

For detailed implementation, see each module's docstrings and examples.

