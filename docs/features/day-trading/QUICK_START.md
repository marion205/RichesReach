# Day Trading System - Quick Start

## What You Have Now

✅ **Multi-provider intraday scanner** (Polygon → Finnhub → Alpha Vantage)  
✅ **Circuit breakers & caching** (60s cache, timeouts, fallbacks)  
✅ **Signal logging** (every pick logged to database)  
✅ **Performance tracking** (evaluated at 30m, 2h, EOD, 1d, 2d)  
✅ **Strategy stats** (Sharpe, win rate, max DD - the "Citadel Board")  
✅ **Investment Committee** (KPI targets, health checks)  
✅ **GraphQL stats endpoint** (query performance metrics)  
✅ **Structured logging** (provider counts, universe size, duration)

## 5-Minute Setup

### 1. Run Migrations
```bash
cd deployment_package/backend
python manage.py makemigrations core
python manage.py migrate
```

### 2. Generate Signals
Hit the GraphQL endpoint or use the mobile app:
```graphql
query {
  dayTradingPicks(mode: "SAFE") {
    picks { symbol side score }
  }
}
```

### 3. Verify Signals Are Logged
```bash
python manage.py shell
```
```python
from core.models import DayTradingSignal
print(DayTradingSignal.objects.count())
```

### 4. Evaluate Performance
```bash
python manage.py evaluate_signal_performance --horizon 30m
python manage.py calculate_strategy_performance --period ALL_TIME
```

### 5. Query Stats
```graphql
query {
  dayTradingStats(period: "ALL_TIME") {
    mode
    winRate
    sharpeRatio
    maxDrawdown
  }
}
```

## What Gets Logged

Every time you generate picks, the system logs:

**Structured Log** (for monitoring):
```
DayTradingPicksSummary mode=SAFE universe_size=50 qualified=12 returned=3 
  provider_counts={'polygon': 8, 'finnhub': 3, 'alpha_vantage': 1} 
  duration_ms=1234 universe_source=DYNAMIC_MOVERS
```

**Database** (for performance tracking):
- `DayTradingSignal`: Every pick with features, entry/stop/targets
- `SignalPerformance`: Outcomes at different horizons
- `StrategyPerformance`: Aggregated stats (Sharpe, win rate, etc.)

## The "Citadel Board"

Query strategy stats to see:
- **Win Rate**: % of winning trades
- **Sharpe Ratio**: Risk-adjusted returns
- **Max Drawdown**: Worst peak-to-trough decline
- **Avg PnL**: Average return per signal
- **Calmar Ratio**: Return / Max DD

## Investment Committee

Run health checks:
```bash
python manage.py strategy_health_check --all
```

This evaluates strategies against KPI targets and flags any that need review.

## Next Steps

1. **Set up cron jobs** for nightly evaluation
2. **Run health checks** regularly
3. **Build dashboard** showing stats
4. **Use for investor slides** (real performance data, not marketing fluff)

See `SETUP_AND_VERIFICATION.md` for detailed verification steps.

