# Day Trading - Quick Start Guide

## ✅ Setup Complete!

All API keys are configured. Here's how to test:

### 1. Set Environment Variables

**Option A: Use the setup script** (recommended):
```bash
source setup_day_trading_env.sh
```

**Option B: Manual export**:
```bash
export POLYGON_API_KEY="uuKmy9dPAjaSVXVEtCumQPga1dqEPDS2"
export ALPACA_API_KEY="CKVL76T6J6F5BNDADQ322V2BJK"
export ALPACA_SECRET_KEY="6CGQRytfGBWauNSFdVA75jvisv1ctPuMHXU1mwovDXQz"
```

**Option C: Add to Django settings** (for permanent setup):
Add to `deployment_package/backend/richesreach/settings.py`:
```python
import os
os.environ['POLYGON_API_KEY'] = 'uuKmy9dPAjaSVXVEtCumQPga1dqEPDS2'
os.environ['ALPACA_API_KEY'] = 'CKVL76T6J6F5BNDADQ322V2BJK'
os.environ['ALPACA_SECRET_KEY'] = '6CGQRytfGBWauNSFdVA75jvisv1ctPuMHXU1mwovDXQz'
```

### 2. Start Backend Server

```bash
cd deployment_package/backend
python manage.py runserver
```

Or if using FastAPI:
```bash
cd deployment_package/backend
uvicorn main:app --reload --port 8000
```

### 3. Test GraphQL Query

**In a new terminal** (with environment variables set):
```bash
cd /Users/marioncollins/RichesReach
source setup_day_trading_env.sh  # If not already set
python test_day_trading_query.py
```

### 4. Query from Frontend/Postman

**GraphQL Query**:
```graphql
query GetDayTradingPicks($mode: String!) {
  dayTradingPicks(mode: $mode) {
    asOf
    mode
    picks {
      symbol
      side
      score
      features {
        momentum15m
        rvol10m
        vwapDist
        breakoutPct
        spreadBps
        catalystScore
      }
      risk {
        atr5m
        sizeShares
        stop
        targets
        timeStopMin
      }
      notes
    }
    universeSize
    qualityThreshold
  }
}
```

**Variables**:
```json
{
  "mode": "SAFE"
}
```

**Or for AGGRESSIVE mode**:
```json
{
  "mode": "AGGRESSIVE"
}
```

### 5. Expected Response

```json
{
  "data": {
    "dayTradingPicks": {
      "asOf": "2025-01-XX...",
      "mode": "SAFE",
      "picks": [
        {
          "symbol": "AAPL",
          "side": "LONG",
          "score": 2.5,
          "features": {
            "momentum15m": 0.0234,
            "rvol10m": 0.25,
            "vwapDist": 0.01,
            "breakoutPct": 0.05,
            "spreadBps": 5.2,
            "catalystScore": 7.5
          },
          "risk": {
            "atr5m": 1.2,
            "sizeShares": 100,
            "stop": 98.5,
            "targets": [102.0, 103.5, 105.0],
            "timeStopMin": 45
          },
          "notes": "AAPL LONG: Strong trending market, 2.3% momentum, Breakout detected. Score: 2.50"
        }
      ],
      "universeSize": 500,
      "qualityThreshold": 1.5
    }
  }
}
```

---

## 🔍 Troubleshooting

### If GraphQL query fails:

1. **Check backend is running**:
   ```bash
   curl http://localhost:8000/health
   ```

2. **Check GraphQL endpoint**:
   ```bash
   curl -X POST http://localhost:8000/graphql/ \
     -H "Content-Type: application/json" \
     -d '{"query": "{ __schema { queryType { name } } }"}'
   ```

3. **Check environment variables**:
   ```bash
   echo $POLYGON_API_KEY
   echo $ALPACA_API_KEY
   ```

4. **Check logs**:
   - Look for "Generating day trading picks" in backend logs
   - Look for "Got real intraday data from Polygon.io" or "Alpaca"

### If no picks returned:

- **Market hours**: Intraday data only available during market hours (9:30 AM - 4:00 PM ET)
- **API limits**: Check Polygon.io and Alpaca rate limits
- **Database**: Ensure Stock objects exist in database
- **Quality threshold**: Lower scores might be filtered out

---

## 📊 Data Flow

1. **Query received** → `resolve_day_trading_picks()`
2. **Get symbols** → From database (or default list)
3. **Fetch data** → Polygon.io → Alpaca → Historical → Mock
4. **Extract features** → 100+ features from both books
5. **Score** → ML scorer (rule-based or trained model)
6. **Filter** → By quality threshold
7. **Calculate risk** → Stops, targets, position sizing
8. **Return picks** → Top 20 opportunities

---

## ✅ Status

- ✅ All API keys configured
- ✅ Real data integration ready
- ✅ GraphQL endpoint ready
- ✅ Tests ready to run

**You're all set!** 🚀

