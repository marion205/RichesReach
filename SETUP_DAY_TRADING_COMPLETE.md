# Complete Day Trading Setup Guide

## Prerequisites

Make sure you have the backend dependencies installed:

```bash
# Activate virtual environment
source venv/bin/activate

# Install/update dependencies
cd deployment_package/backend
pip install -r requirements.txt
```

## Step 1: Run Migrations

```bash
# Make sure you're in the backend directory with venv activated
source venv/bin/activate
cd deployment_package/backend

# Create migrations
python manage.py makemigrations core

# Apply migrations
python manage.py migrate
```

**Expected output:**
- Should create/update tables for:
  - `day_trading_signals`
  - `signal_performance`
  - `strategy_performance`
  - `user_risk_budgets`

## Step 2: Generate Signals

You need to hit the GraphQL endpoint to generate signals. Here are your options:

### Option A: GraphQL Playground

1. **Start your backend server** (if not already running):
   ```bash
   # In deployment_package/backend
   python manage.py runserver
   ```

2. **Open GraphQL Playground** at http://localhost:8000/graphql

3. **Run this query:**
   ```graphql
   query {
     dayTradingPicks(mode: "SAFE") {
       mode
       picks {
         symbol
         side
         score
         features {
           momentum15m
           rvol10m
         }
         risk {
           stop
           targets
         }
       }
       universeSource
     }
   }
   ```

4. **Try AGGRESSIVE mode too:**
   ```graphql
   query {
     dayTradingPicks(mode: "AGGRESSIVE") {
       mode
       picks {
         symbol
         side
         score
       }
       universeSource
     }
   }
   ```

### Option B: Mobile App

Navigate to the Day Trading screen in your mobile app and toggle between SAFE/AGGRESSIVE modes.

### Option C: cURL

```bash
curl -X POST http://localhost:8000/graphql \
  -H "Content-Type: application/json" \
  -d '{
    "query": "query { dayTradingPicks(mode: \"SAFE\") { mode picks { symbol side score } universeSource } }"
  }'
```

## Step 3: Verify Signals Are Stored

```bash
cd deployment_package/backend
python manage.py shell
```

Then in Python shell:
```python
from core.models import DayTradingSignal

# Check count
count = DayTradingSignal.objects.count()
print(f"Total signals: {count}")

# Check latest
if count > 0:
    last = DayTradingSignal.objects.order_by('-generated_at').first()
    print(f"Latest signal:")
    print(f"  Symbol: {last.symbol}")
    print(f"  Side: {last.side}")
    print(f"  Mode: {last.mode}")
    print(f"  Entry Price: ${last.entry_price}")
    print(f"  Score: {last.score}")
    print(f"  Generated: {last.generated_at}")
    print(f"  Universe Source: {last.universe_source}")
else:
    print("No signals found yet. Make sure you've called the GraphQL endpoint!")
```

**Or use the verification script:**
```bash
./verify_day_trading.sh
```

## Step 4: Evaluate Performance

Once you have some signals and some time has passed (prices need to move):

```bash
cd deployment_package/backend

# Evaluate 30-minute horizon
python manage.py evaluate_signal_performance --horizon 30m

# Evaluate end-of-day
python manage.py evaluate_signal_performance --horizon EOD

# Or evaluate all horizons
python manage.py evaluate_signal_performance --all
```

Then calculate strategy stats:
```bash
# Daily stats
python manage.py calculate_strategy_performance --period daily

# All-time stats
python manage.py calculate_strategy_performance --period ALL_TIME
```

## Step 5: Query Stats via GraphQL

```graphql
query GetDayTradingStats {
  dayTradingStats(period: "ALL_TIME") {
    mode
    period
    asOf
    winRate
    sharpeRatio
    maxDrawdown
    avgPnlPerSignal
    totalSignals
    signalsEvaluated
    totalPnlPercent
    sortinoRatio
    calmarRatio
  }
}
```

Or filter by mode:
```graphql
query GetSafeModeStats {
  dayTradingStats(mode: "SAFE", period: "ALL_TIME") {
    mode
    winRate
    sharpeRatio
    maxDrawdown
    avgPnlPerSignal
  }
}
```

## Troubleshooting

### "No module named 'django'"
```bash
source venv/bin/activate
cd deployment_package/backend
pip install -r requirements.txt
```

### "No signals found"
- Make sure backend server is running
- Check GraphQL endpoint is accessible (http://localhost:8000/graphql)
- Look for errors in backend logs
- Verify API keys are set (POLYGON_API_KEY, FINNHUB_API_KEY, etc.)

### "No strategy performance stats"
- Run `calculate_strategy_performance` command first
- Make sure you've evaluated signals (`evaluate_signal_performance`)
- Check that signals have been generated and some time has passed

### "Sharpe ratio is None"
- Need at least 2 signals with PnL data
- Run evaluation commands to populate SignalPerformance records
- Then recalculate strategy performance

## Check Structured Logs

Look in your backend logs for entries like:
```
DayTradingPicksSummary mode=SAFE universe_size=50 qualified=12 returned=3 
  provider_counts={'polygon': 8, 'finnhub': 3, 'alpha_vantage': 1} 
  duration_ms=1234 universe_source=DYNAMIC_MOVERS
```

This shows:
- How many symbols were considered
- How many qualified after filters
- Which providers succeeded
- How long it took
- Which universe source was used

## Next Steps

Once everything is working:
1. Set up cron jobs for nightly evaluation
2. Run Investment Committee health checks: `python manage.py strategy_health_check --all`
3. Build dashboard showing stats
4. Use stats for investor slides

