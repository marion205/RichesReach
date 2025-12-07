#!/bin/bash
# Performance Monitoring Script
# Continuously monitors performance metrics and compares to baseline

set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

BACKEND_DIR="deployment_package/backend"
VENV_PATH="$BACKEND_DIR/venv"
BASELINE_FILE="${1:-baseline_staging_*.json}"

# Activate virtual environment
source "$VENV_PATH/bin/activate"
cd "$BACKEND_DIR"

echo "📊 Performance Monitoring Started"
echo "=================================="
echo "Baseline: $BASELINE_FILE"
echo "Press Ctrl+C to stop"
echo ""

# Function to generate and compare report
generate_report() {
    TIMESTAMP=$(date +%Y%m%d_%H%M%S)
    REPORT_FILE="performance_report_${TIMESTAMP}.json"
    
    echo -e "\n${YELLOW}[$(date +%H:%M:%S)] Generating performance report...${NC}"
    python manage.py performance_report --export "$REPORT_FILE"
    
    if [ -f "$BASELINE_FILE" ]; then
        echo -e "${GREEN}Comparing to baseline...${NC}"
        python -c "
import json
import sys
from pathlib import Path

# Find baseline file
baseline_path = Path('$BASELINE_FILE')
if not baseline_path.exists():
    baseline_files = list(Path('.').glob('baseline_*.json'))
    if baseline_files:
        baseline_path = max(baseline_files, key=lambda p: p.stat().st_mtime)
    else:
        print('No baseline file found')
        sys.exit(0)

with open(baseline_path) as f:
    baseline = json.load(f)
    
with open('$REPORT_FILE') as f:
    current = json.load(f)

baseline_queries = baseline['summary'].get('total_queries', 0)
current_queries = current['summary'].get('total_queries', 0)

baseline_cache = baseline['summary'].get('overall_cache_hit_rate', 0)
current_cache = current['summary'].get('overall_cache_hit_rate', 0)

baseline_avg_time = baseline['summary'].get('avg_query_time_ms', 0)
current_avg_time = current['summary'].get('avg_query_time_ms', 0)

print(f'\n📈 Performance Comparison:')
print(f'  Total Queries: {current_queries} (baseline: {baseline_queries})')
print(f'  Cache Hit Rate: {current_cache:.1f}% (baseline: {baseline_cache:.1f}%)')
print(f'  Avg Query Time: {current_avg_time:.2f}ms (baseline: {baseline_avg_time:.2f}ms)')

if current_cache < baseline_cache * 0.8:
    print('  ⚠️  Cache hit rate is significantly lower than baseline')
if current_avg_time > baseline_avg_time * 1.5:
    print('  ⚠️  Query time is significantly higher than baseline')
"
    fi
    
    echo -e "${GREEN}Report saved: $REPORT_FILE${NC}"
}

# Initial report
generate_report

# Monitor every 5 minutes
while true; do
    sleep 300  # 5 minutes
    generate_report
done

