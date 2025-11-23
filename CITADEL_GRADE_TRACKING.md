# Citadel-Grade Signal Performance Tracking

## Overview

This system tracks every day trading pick, its features, and realized performance over time - giving you "Citadel Board" metrics (Sharpe, win rate, max drawdown, etc.) for your retail trading signals.

## What Was Built

### 1. Database Models (`signal_performance_models.py`)

**DayTradingSignal** - Records every pick:
- Symbol, side, mode (SAFE/AGGRESSIVE)
- Features at time of signal (momentum, RVOL, VWAP, etc.)
- Entry/stop/target prices
- Score and risk parameters

**SignalPerformance** - Tracks outcomes:
- Performance at 30m, 2h, EOD, 1d, 2d horizons
- PnL in dollars and percentage
- Whether stop/targets hit
- Outcome classification (WIN/LOSS/STOP_HIT/TARGET_HIT)

**StrategyPerformance** - Aggregated stats:
- Win rate, Sharpe ratio, Sortino ratio
- Max drawdown and duration
- Equity curve data
- Calculated daily/weekly/monthly/all-time

**UserRiskBudget** - Per-user risk management:
- Daily/weekly risk limits
- Circuit breakers (-3% daily loss = pause trading)
- Position sizing rules
- Volatility-based sizing

### 2. Signal Logger (`signal_logger.py`)

Automatically logs every pick when generated:
- Called from day trading resolver
- Stores all features and parameters
- Ready for performance evaluation

### 3. Evaluation Commands

**`evaluate_signal_performance.py`** - Evaluates signals at different horizons:
```bash
# Evaluate 30-minute performance
python manage.py evaluate_signal_performance --horizon 30m

# Evaluate end-of-day performance
python manage.py evaluate_signal_performance --horizon EOD

# Evaluate all horizons
python manage.py evaluate_signal_performance --all
```

**`calculate_strategy_performance.py`** - Calculates aggregated stats:
```bash
# Daily stats
python manage.py calculate_strategy_performance --period daily

# Weekly stats
python manage.py calculate_strategy_performance --period weekly

# Monthly stats
python manage.py calculate_strategy_performance --period monthly
```

### 4. Risk Management (`risk_management.py`)

Helper functions for position sizing and risk controls:
- `calculate_position_size()` - Safe position sizing based on risk budget
- `record_trade_risk()` - Track risk usage and PnL
- Circuit breaker checks

## Setup

### 1. Create Migrations

```bash
cd deployment_package/backend
python manage.py makemigrations core
python manage.py migrate
```

### 2. Set Up Nightly Jobs

Add to cron or Celery:

```bash
# Every 30 minutes during market hours
*/30 9-16 * * 1-5 python manage.py evaluate_signal_performance --horizon 30m

# Every 2 hours
0 11,13,15 * * 1-5 python manage.py evaluate_signal_performance --horizon 2h

# End of day (4:30 PM ET)
30 16 * * 1-5 python manage.py evaluate_signal_performance --horizon EOD

# Nightly strategy performance calculation
0 2 * * 1-6 python manage.py calculate_strategy_performance --period daily
0 3 * * 1 python manage.py calculate_strategy_performance --period weekly
0 4 1 * * python manage.py calculate_strategy_performance --period monthly
```

### 3. Initialize User Risk Budgets

```python
from core.signal_performance_models import UserRiskBudget
from django.contrib.auth import get_user_model

User = get_user_model()
for user in User.objects.all():
    UserRiskBudget.objects.get_or_create(user=user)
```

## Usage

### Automatic Signal Logging

Signals are automatically logged when the day trading resolver runs. No action needed.

### Query Performance Stats

```python
from core.signal_performance_models import StrategyPerformance

# Get latest daily stats for SAFE mode
safe_stats = StrategyPerformance.objects.filter(
    mode='SAFE',
    period='DAILY'
).order_by('-period_end').first()

print(f"Win Rate: {safe_stats.win_rate}%")
print(f"Sharpe: {safe_stats.sharpe_ratio}")
print(f"Max DD: {safe_stats.max_drawdown}%")
```

### Use Risk Management

```python
from core.risk_management import calculate_position_size

# Calculate safe position size for a trade
result = calculate_position_size(
    user=user,
    symbol='AAPL',
    entry_price=150.00,
    stop_price=147.00,
    mode='SAFE'
)

if result['allowed']:
    print(f"Suggested size: {result['shares']} shares")
    print(f"Risk: ${result['dollars_at_risk']} ({result['risk_pct']:.2f}%)")
else:
    print(f"Not allowed: {result['reason']}")
```

## The "Citadel Board"

Query `StrategyPerformance` to see your metrics:

- **Sharpe Ratio** - Risk-adjusted returns (target: > 1.0)
- **Win Rate** - % of winning trades (target: > 50%)
- **Max Drawdown** - Worst peak-to-trough decline (target: < 10%)
- **Sortino Ratio** - Downside risk-adjusted returns
- **Calmar Ratio** - Return / Max DD
- **Equity Curve** - Full performance history

## Investment Committee

See `docs/features/day-trading/INVESTMENT_COMMITTEE.md` for the full Investment Committee system.

The Investment Committee evaluates strategy health against KPI targets:

- **SAFE Mode**: Sharpe > 1.0, Win Rate > 45%, Max DD < 8%
- **AGGRESSIVE Mode**: Sharpe > 0.8, Win Rate > 40%, Max DD < 15%

Run health checks:
```bash
python manage.py strategy_health_check --all
```

This gives you:
- Strategy status (ACTIVE / WATCH / REVIEW)
- Health score (0-100)
- KPI pass/fail status
- Recommendations for improvement

## Next Steps

1. **Run migrations** to create tables
2. **Set up cron jobs** for nightly evaluation
3. **Run Investment Committee health checks** regularly
4. **Monitor logs** to see signals being tracked
5. **Query stats** after a few days of data
6. **Iterate on features** based on what adds edge

## Example: "RichesReach vs SPY" Panel

```python
# Get all-time SAFE mode performance
safe_perf = StrategyPerformance.objects.filter(
    mode='SAFE',
    period='ALL_TIME'
).first()

# Compare to SPY (you'd fetch SPY returns separately)
spy_return = 0.10  # 10% annual return example
richesreach_return = safe_perf.total_pnl_percent

print(f"RichesReach SAFE: {richesreach_return:.2f}%")
print(f"SPY: {spy_return:.2f}%")
print(f"Alpha: {richesreach_return - spy_return:.2f}%")
```

This is your "we beat X" metric for investors.

