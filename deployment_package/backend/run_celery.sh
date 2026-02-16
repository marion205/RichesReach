#!/usr/bin/env bash
# Run Celery worker and Beat for DeFi Auto-Pilot and Trust-First scheduled tasks.
#
# Option A (single process, good for dev):
#   ./run_celery.sh
#
# Option B (two terminals for production):
#   Terminal 1: .venv/bin/celery -A richesreach worker -l info
#   Terminal 2: .venv/bin/celery -A richesreach beat -l info
#
# Tasks on schedule include:
#   - evaluate_autopilot_repairs (every 10 min)
#   - check_portfolio_drawdowns (every 15 min)
#   - check_repair_outcomes (every 12 h)
#   - fetch_defi_yields, monitor_defi_health_factors, etc.

set -e
cd "$(dirname "$0")"

if [ -z "$VIRTUAL_ENV" ] && [ -d .venv ]; then
  source .venv/bin/activate
fi

# Single process: worker + beat (dev)
exec celery -A richesreach worker --beat -l info
