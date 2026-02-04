#!/usr/bin/env bash
# Run the backend with GraphQL profiling enabled. Resolver timings and db_queries
# are logged; use PERFORMANCE_AUDIT_TEMPLATE.md to record before/after.
# Usage:
#   ./scripts/run_with_profiling.sh              # run backend (stdout/stderr to terminal)
#   ./scripts/run_with_profiling.sh --log FILE   # write stderr to FILE for grepping

set -e
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$BACKEND_DIR"

export GRAPHQL_PROFILING=1
# Optional: enable Django DEBUG to get db_queries per resolver (dev only)
# export DEBUG=true

LOG_FILE=""
while [ $# -gt 0 ]; do
  if [ "$1" = "--log" ] && [ -n "${2:-}" ]; then
    LOG_FILE="$2"
    shift 2
    break
  fi
  shift
done

echo "GRAPHQL_PROFILING=1 — resolver timings will be logged (e.g. GRAPHQL_PROFILING resolver=... duration_ms=... db_queries=...)."
echo "Hit Feed, Portfolio, Trading, or Banking operations, then grep for GRAPHQL_PROFILING to fill docs/PERFORMANCE_AUDIT_TEMPLATE.md."
echo ""

if [ -n "$LOG_FILE" ]; then
  echo "Writing stderr to $LOG_FILE — grep GRAPHQL_PROFILING $LOG_FILE"
  exec python main.py 2>"$LOG_FILE"
else
  exec python main.py
fi
