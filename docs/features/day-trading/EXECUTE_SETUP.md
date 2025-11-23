# Execute Day Trading Setup

## Quick Commands

### Option 1: Use the Setup Script

```bash
# Activate your virtual environment first
source venv/bin/activate  # or .venv/bin/activate

# Run setup script
./setup_day_trading.sh
```

### Option 2: Manual Steps

```bash
# 1. Activate virtual environment
source venv/bin/activate

# 2. Run migrations
cd deployment_package/backend
python manage.py makemigrations core
python manage.py migrate

# 3. Verify models
python manage.py shell
```

In Python shell:
```python
from core.models import DayTradingSignal, StrategyPerformance
print(f"DayTradingSignal: {DayTradingSignal}")
print(f"StrategyPerformance: {StrategyPerformance}")
```

## Generate Signals

### Via GraphQL Playground

1. Start your backend server
2. Go to http://localhost:8000/graphql (or your GraphQL endpoint)
3. Run:

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

Then try AGGRESSIVE mode:
```graphql
query {
  dayTradingPicks(mode: "AGGRESSIVE") {
    mode
    picks {
      symbol
      side
      score
    }
  }
}
```

### Via Mobile App

Just navigate to the Day Trading screen and toggle between SAFE/AGGRESSIVE modes.

## Verify Signals Are Stored

```bash
cd deployment_package/backend
python manage.py shell
```

```python
from core.models import DayTradingSignal

# Check count
count = DayTradingSignal.objects.count()
print(f"Total signals: {count}")

# Check latest
if count > 0:
    last = DayTradingSignal.objects.order_by('-generated_at').first()
    print(f"Latest: {last.symbol} {last.side} ({last.mode})")
    print(f"  Entry: ${last.entry_price}, Score: {last.score}")
    print(f"  Generated: {last.generated_at}")
    print(f"  Universe Source: {last.universe_source}")
```

Or use the verification script:
```bash
./verify_day_trading.sh
```

## Evaluate Performance

Once you have some signals and some time has passed:

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

## Query Stats via GraphQL

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

Filter by mode:
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

## Check Logs for Structured Data

Look for structured logs like:
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

## Troubleshooting

### "No signals found"
- Make sure backend is running
- Check GraphQL endpoint is accessible
- Look for errors in backend logs
- Verify API keys are set (POLYGON_API_KEY, etc.)

### "No strategy performance stats"
- Run `calculate_strategy_performance` command first
- Make sure you've evaluated signals (`evaluate_signal_performance`)
- Check that signals have been generated and some time has passed

### "Sharpe ratio is None"
- Need at least 2 signals with PnL data
- Run evaluation commands to populate SignalPerformance records
- Then recalculate strategy performance

## Next Steps

Once verified:
1. Set up cron jobs for nightly evaluation
2. Run Investment Committee health checks
3. Build dashboard showing stats
4. Use stats for investor slides

