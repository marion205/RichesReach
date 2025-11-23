# Day Trading Setup & Verification Guide

## Quick Start Checklist

### 1️⃣ Run Migrations

```bash
cd deployment_package/backend
python manage.py makemigrations core
python manage.py migrate
```

**Expected output**: Should create tables for:
- `day_trading_signals`
- `signal_performance`
- `strategy_performance`
- `user_risk_budgets`

If you see "No changes detected", check that `core/models.py` imports the signal performance models (it should already).

### 2️⃣ Restart Backend

```bash
bash start_backend_now.sh
```

Or however you normally start your Django server.

### 3️⃣ Generate Some Signals

Hit your day trading picks endpoint a few times:

**Via GraphQL Playground** (http://localhost:8000/graphql):
```graphql
query {
  dayTradingPicks(mode: "SAFE") {
    mode
    picks {
      symbol
      side
      score
    }
  }
}

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

**Via Mobile App**: Just navigate to the Day Trading screen and toggle between SAFE/AGGRESSIVE modes.

Each call should:
- ✅ Generate exactly 3 picks per mode
- ✅ Log them to `DayTradingSignal` table
- ✅ Show structured logging with provider counts

### 4️⃣ Verify Signals Are Being Stored

```bash
cd deployment_package/backend
python manage.py shell
```

Then in Python shell:
```python
from core.models import DayTradingSignal

# Check count
print(f"Total signals: {DayTradingSignal.objects.count()}")

# Check latest
last = DayTradingSignal.objects.order_by('-generated_at').first()
if last:
    print(f"Latest: {last.symbol} {last.side} ({last.mode})")
    print(f"  Entry: ${last.entry_price}, Score: {last.score}")
    print(f"  Generated: {last.generated_at}")
    print(f"  Universe Source: {last.universe_source}")
else:
    print("No signals found yet - make sure you've called the endpoint")
```

**Expected**: You should see rows with real values. If empty, check:
- Backend is running
- GraphQL endpoint is accessible
- No errors in logs

### 5️⃣ Run First Evaluation Pass

Once you have some signals (and let some time pass so prices can move):

```bash
# Evaluate 30-minute horizon
python manage.py evaluate_signal_performance --horizon 30m

# Evaluate end-of-day
python manage.py evaluate_signal_performance --horizon EOD

# Or evaluate all horizons
python manage.py evaluate_signal_performance --all
```

Then aggregate strategy stats:
```bash
python manage.py calculate_strategy_performance --period daily
python manage.py calculate_strategy_performance --period ALL_TIME
```

### 6️⃣ Check Strategy Performance Stats

In Python shell:
```python
from core.models import StrategyPerformance

# Get latest stats
stats = StrategyPerformance.objects.order_by('-period_end')[:5]
for s in stats:
    print(f"{s.mode} {s.period}:")
    print(f"  Win Rate: {s.win_rate}%")
    print(f"  Sharpe: {s.sharpe_ratio}")
    print(f"  Max DD: {s.max_drawdown}%")
    print(f"  Signals: {s.signals_evaluated}/{s.total_signals}")
    print()
```

**Expected**: You should start seeing:
- Win rate percentages
- Sharpe ratios (may be None if insufficient data)
- Max drawdown values
- Signal counts

### 7️⃣ Query Stats via GraphQL

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
  }
}
```

## Structured Logging

Check your logs for the new structured logging format:

```
DayTradingPicksSummary mode=SAFE universe_size=50 qualified=12 returned=3 provider_counts={'polygon': 8, 'finnhub': 3, 'alpha_vantage': 1} duration_ms=1234 universe_source=DYNAMIC_MOVERS
```

This gives you:
- How many symbols were considered
- How many qualified after filters
- How many were returned (should be 3)
- Which providers succeeded (Polygon/Finnhub/Alpha Vantage mix)
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
- Make sure you have evaluated signals (`evaluate_signal_performance`)
- Check that signals have been generated and some time has passed

### "Sharpe ratio is None"
- Need at least 2 signals with PnL data
- Run evaluation commands to populate SignalPerformance records
- Then recalculate strategy performance

### Migration errors
- Make sure `core/models.py` imports signal performance models
- Check for conflicting migrations
- Try `python manage.py migrate --fake-initial` if needed

## Next Steps

Once verified:
1. ✅ Set up cron jobs for nightly evaluation
2. ✅ Run Investment Committee health checks
3. ✅ Build dashboard showing stats
4. ✅ Use stats for investor slides

See `INVESTMENT_COMMITTEE.md` for the full governance system.

