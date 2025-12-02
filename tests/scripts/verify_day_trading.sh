#!/bin/bash
# Day Trading System Verification Script
# Run this to verify everything is working

set -e

echo "🔍 Verifying Day Trading System..."
echo ""

cd deployment_package/backend

# Check signal count
echo "📊 Signal Count:"
python manage.py shell << EOF
from core.models import DayTradingSignal, StrategyPerformance, SignalPerformance
from django.utils import timezone
from datetime import timedelta

signal_count = DayTradingSignal.objects.count()
print(f"Total signals: {signal_count}")

if signal_count > 0:
    last = DayTradingSignal.objects.order_by('-generated_at').first()
    print(f"Latest: {last.symbol} {last.side} ({last.mode})")
    print(f"  Entry: \${last.entry_price}, Score: {last.score}")
    print(f"  Generated: {last.generated_at}")
    print(f"  Universe Source: {last.universe_source}")
    
    # Check recent signals
    recent = DayTradingSignal.objects.filter(
        generated_at__gte=timezone.now() - timedelta(hours=24)
    ).count()
    print(f"Signals in last 24h: {recent}")
else:
    print("⚠️  No signals found. Generate some by calling the GraphQL endpoint!")

# Check performance records
perf_count = SignalPerformance.objects.count()
print(f"\nPerformance records: {perf_count}")

# Check strategy stats
stats_count = StrategyPerformance.objects.count()
print(f"Strategy performance records: {stats_count}")

if stats_count > 0:
    print("\nLatest Strategy Stats:")
    for stat in StrategyPerformance.objects.order_by('-period_end')[:3]:
        print(f"  {stat.mode} {stat.period}:")
        print(f"    Win Rate: {stat.win_rate}%")
        print(f"    Sharpe: {stat.sharpe_ratio}")
        print(f"    Max DD: {stat.max_drawdown}%")
        print(f"    Signals: {stat.signals_evaluated}/{stat.total_signals}")
EOF

echo ""
echo "✅ Verification complete!"

