# RichesReach Production Server

A production-grade, institutional-quality portfolio management server built with FastAPI, Graphene, and quantitative finance libraries.

## Architecture

- **FastAPI**: High-performance async web framework
- **Graphene**: Type-safe GraphQL with consistent units
- **Redis**: Caching with provenance and TTL
- **CVXPY**: Convex optimization for portfolio construction
- **Prometheus**: Metrics and observability
- **Quantitative Engine**: Factor models, risk management, transaction cost optimization

## Features

### 🏦 Institutional-Grade Risk Management
- **Income-Aware Policy**: Income drives risk capacity, not alpha signals
- **Emergency Cash Floor**: Hard gate preventing equity purchases below cash threshold
- **Suitability Framework**: Pre-filter universe based on investor profile
- **Transaction Cost Optimization**: Realistic TC-aware portfolio construction

### 📊 Quantitative Engine
- **Factor Models**: Size, Value, Quality, Momentum, Low-Vol factors
- **Z-Score Standardization**: Sector-neutral factor scoring
- **Covariance Shrinkage**: Robust risk estimation
- **Convex Optimization**: Mean-variance with constraints

### 🔒 Production Security
- **Environment Variables**: Secure API key management
- **Rate Limiting**: Per-vendor API rate limits
- **Retry Logic**: Exponential backoff with jitter
- **HTTPS Verification**: Secure external API calls

### 📈 Real-Time Data
- **FinnHub Integration**: Live market data with caching
- **Redis Caching**: 15s quote freshness, 1h profile caching
- **Provenance Tracking**: Data source and timestamp tracking

## Setup

### 1. Install Dependencies
```bash
cd server
pip install -r requirements.txt
```

### 2. Environment Configuration
Create `.env` file:
```bash
ENV=prod
ALPHA_VANTAGE_KEY=your_key_here
FINNHUB_KEY=your_key_here
NEWS_API_KEY=your_key_here
SECRET_KEY=your_secret_key
REDIS_URL=redis://localhost:6379/0
```

### 3. Start Redis
```bash
redis-server
```

### 4. Run Server
```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

## API Endpoints

### GraphQL
- **Endpoint**: `http://localhost:8000/graphql`
- **Playground**: `http://localhost:8000/graphql` (GET request)

### Health & Metrics
- **Health**: `http://localhost:8000/health`
- **Metrics**: `http://localhost:8000/metrics`

## GraphQL Schema

### Core Query
```graphql
query GetAIRecommendations {
  aiRecommendations {
    schemaVersion
    portfolioAnalysis {
      totalValue
      numHoldings
      expectedImpact {
        evPct      # decimal units (0.06 = 6%)
        evAbs
        per10k
      }
      risk {
        volatilityEstimate  # percent units (12.8 = 12.8%)
        maxDrawdownPct
      }
    }
    buyRecommendations {
      symbol
      companyName
      expectedReturn      # decimal units (0.06 = 6%)
      currentPrice
      allocation {
        symbol
        percentage
        reasoning
      }
      factorContrib       # {"momentum": 0.8, "value": 0.3}
      tcPreview          # decimal units (0.001 = 0.1%)
      whyThisSize        # explanation string
    }
    riskAssessment {
      overallRisk
      recommendations
    }
  }
}
```

## Quantitative Features

### Factor Model
- **Size**: Log market cap (smaller = positive exposure)
- **Value**: 1/PE + 1/PB (higher = positive exposure)
- **Quality**: ROE + Gross Margin
- **Momentum**: 12-month - 1-month returns
- **Low-Vol**: Negative volatility (lower vol = positive)

### Portfolio Optimization
- **Objective**: Maximize(expected_return - λ·variance - transaction_costs)
- **Constraints**: 
  - Position caps (per name)
  - Sector caps
  - Turnover budget
  - Cash minimum

### Policy Framework
Income brackets drive policy constraints:
- **Under $30k**: 4% name cap, 25% sector cap, 12% cash floor
- **$30k-$50k**: 5% name cap, 28% sector cap, 10% cash floor
- **Over $150k**: 12% name cap, 36% sector cap, 4% cash floor

## Testing

```bash
# Run quant engine tests
python -m pytest tests/test_quant.py

# Run schema contract tests
python -m pytest tests/test_schema_contract.py
```

## Monitoring

- **Prometheus Metrics**: Request count, latency, error rates
- **Redis Monitoring**: Cache hit rates, memory usage
- **Health Checks**: Automated health endpoint monitoring

## Production Deployment

1. **Environment**: Set `ENV=prod`
2. **Secrets**: Use secure secret management
3. **Redis**: Production Redis cluster
4. **Monitoring**: Prometheus + Grafana
5. **Load Balancing**: Multiple server instances
6. **SSL**: HTTPS termination at load balancer

## Data Flow

1. **User Profile** → **Policy Derivation** → **Suitability Filtering**
2. **Market Data** → **Factor Computation** → **Signal Blending**
3. **Risk Model** → **Optimization** → **Portfolio Construction**
4. **Explainability** → **Factor Exposures** → **Transaction Costs**

This architecture delivers institutional-quality portfolio management with proper risk controls, quantitative rigor, and production reliability.
