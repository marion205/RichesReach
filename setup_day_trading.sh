#!/bin/bash
# Day Trading System Setup Script
# Run this from the project root after activating your virtual environment

set -e

echo "🚀 Setting up Day Trading System..."
echo ""

# Step 1: Run migrations
echo "📦 Step 1: Running migrations..."
cd deployment_package/backend
python manage.py makemigrations core
python manage.py migrate
echo "✅ Migrations complete!"
echo ""

# Step 2: Verify models are imported
echo "🔍 Step 2: Verifying models..."
python manage.py shell << EOF
from core.models import DayTradingSignal, StrategyPerformance
print(f"✅ DayTradingSignal model: {DayTradingSignal}")
print(f"✅ StrategyPerformance model: {StrategyPerformance}")
print(f"✅ Models are properly imported!")
EOF
echo ""

# Step 3: Check current signal count
echo "📊 Step 3: Checking current signal count..."
python manage.py shell << EOF
from core.models import DayTradingSignal
count = DayTradingSignal.objects.count()
print(f"Current signals in database: {count}")
if count > 0:
    last = DayTradingSignal.objects.order_by('-generated_at').first()
    print(f"Latest signal: {last.symbol} {last.side} ({last.mode}) at {last.generated_at}")
else:
    print("No signals yet. Generate some by hitting the GraphQL endpoint!")
EOF
echo ""

echo "✅ Setup complete!"
echo ""
echo "Next steps:"
echo "1. Start your backend server"
echo "2. Hit the GraphQL endpoint: dayTradingPicks(mode: \"SAFE\")"
echo "3. Run: python manage.py evaluate_signal_performance --horizon 30m"
echo "4. Run: python manage.py calculate_strategy_performance --period ALL_TIME"
echo "5. Query stats: dayTradingStats(period: \"ALL_TIME\")"

