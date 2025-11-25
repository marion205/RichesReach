#!/bin/bash
# Pre-Market Scanner Cron Job
# Runs daily at 8:00 AM ET (13:00 UTC, or adjust for DST)
# Add to crontab: 0 13 * * 1-5 /path/to/schedule_pre_market_scanner.sh

# Set working directory
cd /Users/marioncollins/RichesReach/deployment_package/backend

# Activate virtual environment (adjust path as needed)
source ../../venv/bin/activate

# Set environment variables (adjust paths as needed)
export DJANGO_SETTINGS_MODULE=richesreach.settings
export PYTHONPATH=/Users/marioncollins/RichesReach/deployment_package/backend:$PYTHONPATH

# Run pre-market scan with alerts and ML
python manage.py pre_market_scan_with_alerts \
    --mode AGGRESSIVE \
    --limit 20 \
    --send-email \
    --send-push \
    --train-ml

# Log output
echo "$(date): Pre-market scanner completed" >> /tmp/pre_market_scanner.log

