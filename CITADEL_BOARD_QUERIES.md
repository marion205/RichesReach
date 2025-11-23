# Citadel Board - Performance Tracking Queries

## Quick Reference: Compare CORE vs DYNAMIC_MOVERS Performance

### Management Command (Recommended)

```bash
# Compare all modes, 30-day lookback, 30-minute horizon
python manage.py compare_universe_performance

# Compare SAFE mode only, 7-day lookback, end-of-day horizon
python manage.py compare_universe_performance --mode SAFE --days 7 --horizon EOD

# Compare AGGRESSIVE mode, 60-day lookback, 2-hour horizon
python manage.py compare_universe_performance --mode AGGRESSIVE --days 60 --horizon 2h
```

### Output Example

```
================================================================================
📊 UNIVERSE PERFORMANCE COMPARISON
================================================================================

Horizon: 30m | Days Back: 30

📈 CORE Universe Signals: 45
📈 DYNAMIC_MOVERS Universe Signals: 38

────────────────────────────────────────────────────────────────────────────────
Metric                          CORE                      DYNAMIC_MOVERS        
────────────────────────────────────────────────────────────────────────────────
Total Signals                   45                        38                     
Signals with Performance Data  42                        35                     
Win Rate                        58.33%                    62.86% ⭐              
Average PnL per Signal         $12.45                    $18.92 ⭐              
Total PnL                      $522.90                   $662.20 ⭐              
Average R:R                    1.85                      2.12 ⭐               
Sharpe Ratio                   0.92                      1.15 ⭐                
Max Drawdown                   $125.30                   $98.50 ⭐               
Best Trade                     $145.20                   $178.50 ⭐              
Worst Trade                    -$85.40                   -$72.30 ⭐             
────────────────────────────────────────────────────────────────────────────────

📊 RECOMMENDATION:
────────────────────────────────────────────────────────────────────────────────
✅ DYNAMIC_MOVERS universe is performing better (5 vs 0 key metrics)
   Dynamic discovery is finding better opportunities!
────────────────────────────────────────────────────────────────────────────────
```

---

## Manual Django Shell Queries

### Basic Comparison

```python
from core.signal_performance_models import DayTradingSignal, SignalPerformance
from django.db.models import Avg, Count, Sum, Q
from django.utils import timezone
from datetime import timedelta

# Get signals from last 30 days
cutoff = timezone.now() - timedelta(days=30)

# CORE universe signals
core_signals = DayTradingSignal.objects.filter(
    universe_source='CORE',
    generated_at__gte=cutoff
)

# DYNAMIC_MOVERS universe signals
dynamic_signals = DayTradingSignal.objects.filter(
    universe_source='DYNAMIC_MOVERS',
    generated_at__gte=cutoff
)

print(f"CORE signals: {core_signals.count()}")
print(f"DYNAMIC_MOVERS signals: {dynamic_signals.count()}")
```

### Win Rate Comparison

```python
from core.signal_performance_models import SignalPerformance

# Get performance data at 30-minute horizon
horizon = '30m'

# CORE win rate
core_perf = SignalPerformance.objects.filter(
    signal__universe_source='CORE',
    signal__generated_at__gte=cutoff,
    horizon=horizon
)
core_wins = core_perf.filter(pnl_dollars__gt=0).count()
core_total = core_perf.count()
core_win_rate = (core_wins / core_total * 100) if core_total > 0 else 0

# DYNAMIC_MOVERS win rate
dynamic_perf = SignalPerformance.objects.filter(
    signal__universe_source='DYNAMIC_MOVERS',
    signal__generated_at__gte=cutoff,
    horizon=horizon
)
dynamic_wins = dynamic_perf.filter(pnl_dollars__gt=0).count()
dynamic_total = dynamic_perf.count()
dynamic_win_rate = (dynamic_wins / dynamic_total * 100) if dynamic_total > 0 else 0

print(f"CORE win rate: {core_win_rate:.2f}%")
print(f"DYNAMIC_MOVERS win rate: {dynamic_win_rate:.2f}%")
```

### Average R:R (Risk:Reward) Comparison

```python
from django.db.models import Avg

# CORE average R:R
core_wins = core_perf.filter(pnl_dollars__gt=0).aggregate(Avg('pnl_dollars'))['pnl_dollars__avg'] or 0
core_losses = abs(core_perf.filter(pnl_dollars__lt=0).aggregate(Avg('pnl_dollars'))['pnl_dollars__avg'] or 0)
core_rr = (core_wins / core_losses) if core_losses > 0 else 0

# DYNAMIC_MOVERS average R:R
dynamic_wins = dynamic_perf.filter(pnl_dollars__gt=0).aggregate(Avg('pnl_dollars'))['pnl_dollars__avg'] or 0
dynamic_losses = abs(dynamic_perf.filter(pnl_dollars__lt=0).aggregate(Avg('pnl_dollars'))['pnl_dollars__avg'] or 0)
dynamic_rr = (dynamic_wins / dynamic_losses) if dynamic_losses > 0 else 0

print(f"CORE avg R:R: {core_rr:.2f}")
print(f"DYNAMIC_MOVERS avg R:R: {dynamic_rr:.2f}")
```

### Sharpe Ratio Comparison

```python
import math
from django.db.models import StdDev

# CORE Sharpe
core_pnl_values = list(core_perf.values_list('pnl_dollars', flat=True))
if len(core_pnl_values) > 1:
    core_mean = sum(core_pnl_values) / len(core_pnl_values)
    core_std = math.sqrt(sum((x - core_mean) ** 2 for x in core_pnl_values) / len(core_pnl_values))
    core_sharpe = (core_mean / core_std) if core_std > 0 else 0
else:
    core_sharpe = 0

# DYNAMIC_MOVERS Sharpe
dynamic_pnl_values = list(dynamic_perf.values_list('pnl_dollars', flat=True))
if len(dynamic_pnl_values) > 1:
    dynamic_mean = sum(dynamic_pnl_values) / len(dynamic_pnl_values)
    dynamic_std = math.sqrt(sum((x - dynamic_mean) ** 2 for x in dynamic_pnl_values) / len(dynamic_pnl_values))
    dynamic_sharpe = (dynamic_mean / dynamic_std) if dynamic_std > 0 else 0
else:
    dynamic_sharpe = 0

print(f"CORE Sharpe: {core_sharpe:.3f}")
print(f"DYNAMIC_MOVERS Sharpe: {dynamic_sharpe:.3f}")
```

### Mode-Specific Comparison

```python
# Compare SAFE mode only
core_safe = DayTradingSignal.objects.filter(
    universe_source='CORE',
    mode='SAFE',
    generated_at__gte=cutoff
)

dynamic_safe = DayTradingSignal.objects.filter(
    universe_source='DYNAMIC_MOVERS',
    mode='SAFE',
    generated_at__gte=cutoff
)

# Compare AGGRESSIVE mode only
core_agg = DayTradingSignal.objects.filter(
    universe_source='CORE',
    mode='AGGRESSIVE',
    generated_at__gte=cutoff
)

dynamic_agg = DayTradingSignal.objects.filter(
    universe_source='DYNAMIC_MOVERS',
    mode='AGGRESSIVE',
    generated_at__gte=cutoff
)
```

---

## Automated Nightly Comparison

Add to your cron job or Celery task:

```python
# In your nightly evaluation job
from django.core.management import call_command

# After evaluating signals, compare universes
call_command('compare_universe_performance', 
             horizon='EOD', 
             days=30)

# Save results to a log file or database for tracking over time
```

---

## Key Metrics Explained

- **Win Rate**: Percentage of profitable trades
- **Average PnL**: Average profit/loss per signal
- **Total PnL**: Cumulative profit/loss
- **Average R:R**: Average win size / Average loss size (higher is better)
- **Sharpe Ratio**: Risk-adjusted returns (higher is better, >1 is good)
- **Max Drawdown**: Largest peak-to-trough decline
- **Best/Worst Trade**: Best and worst individual trade outcomes

---

## Decision Framework

**Use CORE if:**
- Win rate > 5% higher
- Sharpe ratio > 0.2 higher
- More consistent (lower max drawdown)
- Market is volatile/unpredictable

**Use DYNAMIC_MOVERS if:**
- Win rate > 5% higher
- Average R:R > 0.3 higher
- Better total PnL over 30+ days
- Market is trending/clear direction

**Use Both if:**
- Metrics are within 5% of each other
- Different modes perform differently
- Want to diversify signal sources

