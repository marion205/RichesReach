#!/bin/bash
# Start Performance Monitoring Script
# Monitors performance and compares to baseline

set -e

BACKEND_DIR="$(cd "$(dirname "$0")" && pwd)"
VENV_PATH="$BACKEND_DIR/venv"
BASELINE_FILE="${1:-baseline_production_*.json}"

echo "📊 Starting Performance Monitoring..."
echo "===================================="

# Activate virtual environment
if [ -d "$VENV_PATH" ]; then
    source "$VENV_PATH/bin/activate"
else
    echo "⚠️  Virtual environment not found. Using system Python."
fi

cd "$BACKEND_DIR"

# Find baseline file
if [ -f "$BASELINE_FILE" ]; then
    BASELINE="$BASELINE_FILE"
else
    # Find most recent baseline
    BASELINE=$(ls -t baseline_*.json 2>/dev/null | head -1)
    if [ -z "$BASELINE" ]; then
        echo "⚠️  No baseline file found. Generating new baseline..."
        TIMESTAMP=$(date +%Y%m%d_%H%M%S)
        python manage.py performance_report --export "baseline_${TIMESTAMP}.json"
        BASELINE="baseline_${TIMESTAMP}.json"
    fi
fi

echo "Baseline: $BASELINE"
echo ""
echo "Monitoring will generate reports every 5 minutes."
echo "Press Ctrl+C to stop."
echo ""

# Run monitoring script
exec ./monitor_performance.sh "$BASELINE"
