# RichesReach Investment Committee

## Overview

The Investment Committee is your internal governance system that evaluates strategy health the same way Citadel reviews pod performance. It defines KPI targets, monitors performance, and flags strategies that need review or retirement.

**Philosophy**: "We don't just generate signals. We measure them like a hedge fund strategy."

## KPI Targets

### SAFE Mode Targets

| Metric | Minimum | Target | Rationale |
|--------|---------|--------|-----------|
| Sharpe Ratio | 1.0 | 1.5 | Risk-adjusted returns (conservative) |
| Win Rate | 45% | 55% | High-probability setups |
| Max Drawdown | 8% | < 5% | Capital preservation |
| Avg PnL per Signal | 0.3% | 0.5% | Consistent small wins |
| Worst Single Loss | 5% | < 3% | Risk control |
| Calmar Ratio | 0.5 | > 1.0 | Return vs drawdown |
| Min Signals | 50 | - | Statistical significance |

### AGGRESSIVE Mode Targets

| Metric | Minimum | Target | Rationale |
|--------|---------|--------|-----------|
| Sharpe Ratio | 0.8 | 1.2 | More volatile, lower minimum |
| Win Rate | 40% | 50% | Lower win rate acceptable |
| Max Drawdown | 15% | < 10% | Higher drawdown acceptable |
| Avg PnL per Signal | 0.5% | 0.8% | Higher returns expected |
| Worst Single Loss | 8% | < 5% | Higher single loss acceptable |
| Calmar Ratio | 0.3 | > 0.5 | Lower Calmar acceptable |
| Min Signals | 50 | - | Same sample size needed |

## Strategy Status Levels

1. **ACTIVE** (Score: 75-100)
   - Meeting all KPIs
   - Continue as-is
   - Green light for users

2. **WATCH** (Score: 50-74)
   - Below target but above minimum
   - Monitor closely
   - Consider parameter adjustments

3. **REVIEW** (Score: < 50)
   - Below minimum thresholds
   - Requires immediate review
   - Consider: tightening filters, reducing universe, or pausing

4. **PAUSED**
   - Temporarily disabled
   - Under review or being modified

5. **RETIRED**
   - Permanently disabled
   - Failed to meet standards after review period

## Usage

### Run Health Check

```bash
# Check SAFE mode
python manage.py strategy_health_check --mode SAFE

# Check AGGRESSIVE mode
python manage.py strategy_health_check --mode AGGRESSIVE

# Check all modes
python manage.py strategy_health_check --all

# Check specific period
python manage.py strategy_health_check --all --period ALL_TIME
```

### Example Output

```
╔══════════════════════════════════════════════════════════════╗
║  RICHESREACH INVESTMENT COMMITTEE - STRATEGY HEALTH REPORT   ║
╚══════════════════════════════════════════════════════════════╝

Strategy: SAFE Mode
Period: ALL_TIME
Evaluation Date: 2025-01-15 14:30:00

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📊 PERFORMANCE METRICS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Signals Evaluated: 150
Win Rate: 52.0% (Target: 55.0%)
Sharpe Ratio: 1.35 (Target: 1.5)
Max Drawdown: 6.2% (Limit: 8.0%)
Avg PnL per Signal: 0.42% (Target: 0.3%)
Calmar Ratio: 0.68 (Min: 0.5)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🎯 KPI STATUS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

✅ SHARPE: PASS
⚠️ WIN_RATE: WATCH
✅ MAX_DRAWDOWN: PASS
✅ AVG_PNL: PASS
✅ WORST_LOSS: PASS
✅ CALMAR: PASS

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📈 OVERALL STATUS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Status: WATCH
Health Score: 73/100

⚠️ ISSUES FOUND:
  • Win rate 52.0% below target 55.0%

💡 RECOMMENDATIONS:
  • Strategy below target - monitor closely
  • Consider: adjusting parameters or universe selection
  • For SAFE mode, consider focusing on higher-probability setups
```

## Programmatic Usage

```python
from core.strategy_governance import StrategyHealthCheck
from core.signal_performance_models import StrategyPerformance

# Get latest strategy performance
strategy = StrategyPerformance.objects.filter(
    mode='SAFE',
    period='ALL_TIME'
).order_by('-period_end').first()

# Run health check
health_check = StrategyHealthCheck(strategy, 'SAFE')
evaluation = health_check.evaluate()

print(f"Status: {evaluation['status']}")
print(f"Score: {evaluation['score']}/100")
print(f"Issues: {evaluation['issues']}")
print(f"Recommendations: {evaluation['recommendations']}")

# Get formatted report
report = health_check.get_report()
print(report)
```

## Automated Monitoring

Set up cron jobs to run health checks automatically:

```bash
# Daily health check (runs after strategy performance calculation)
0 3 * * 1-6 python manage.py strategy_health_check --all --period DAILY

# Weekly health check
0 4 * * 1 python manage.py strategy_health_check --all --period WEEKLY

# Monthly health check
0 5 1 * * python manage.py strategy_health_check --all --period MONTHLY
```

## Decision Framework

### When Status = REVIEW

1. **Immediate Actions**:
   - Review all failing KPIs
   - Check for data quality issues
   - Verify calculation accuracy

2. **Possible Remedies**:
   - Tighten universe filters (higher market cap, more volume)
   - Adjust scoring weights (favor higher-probability setups)
   - Reduce position sizing
   - Temporarily pause strategy

3. **Timeline**:
   - Review within 24 hours
   - Decision within 7 days
   - Either fix or retire

### When Status = WATCH

1. **Actions**:
   - Monitor daily
   - Track trend (improving or degrading?)
   - Document any market regime changes

2. **Possible Adjustments**:
   - Fine-tune parameters
   - Test alternative universe sources
   - A/B test feature weights

### When Status = ACTIVE

1. **Actions**:
   - Continue monitoring weekly
   - Look for optimization opportunities
   - Document what's working

## Integration with Frontend

The Investment Committee status can be exposed to users (transparently):

```graphql
query GetStrategyHealth {
  strategyHealth(mode: SAFE) {
    status
    score
    kpiStatus {
      sharpe
      winRate
      maxDrawdown
    }
    issues
    recommendations
  }
}
```

This builds trust: "We measure our strategies like a hedge fund."

## Marketing Angle

**"Our AI co-pilot is measured like a hedge fund strategy"**

- Every signal is logged
- Performance is evaluated at multiple horizons
- Strategies are reviewed by an Investment Committee
- Underperforming strategies are retired

This is your differentiator vs:
- Robinhood "Top Movers" (no tracking)
- FinTwit gurus (no accountability)
- $99/month signal services (no transparency)

## Next Steps

1. **Run initial health checks** on existing data
2. **Set up automated monitoring** via cron
3. **Create dashboard** showing strategy health
4. **Document review process** for when strategies hit REVIEW
5. **A/B test** universe sources and parameters
6. **Publish transparency report** showing real performance

## Philosophy

> "We're not trying to beat Citadel at HFT. We're trying to give retail traders Citadel-style rigor and feedback loops, repackaged as an educational co-pilot."

The Investment Committee ensures we:
- Only show strategies that meet minimum standards
- Continuously improve based on data
- Build trust through transparency
- Operate like a professional trading desk

