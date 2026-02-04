#!/usr/bin/env bash
# Run authenticated Feed/Portfolio/Trading requests and optionally grep the profiling log.
# Requires: backend running with GRAPHQL_PROFILING=1 (e.g. ./scripts/run_with_profiling.sh --log /tmp/graphql-profiling.log)
# Usage:
#   EMAIL=your@email.com PASSWORD=yourpass ./scripts/run_authenticated_profiling.sh
#   EMAIL=... PASSWORD=... LOG_FILE=/tmp/graphql-profiling.log ./scripts/run_authenticated_profiling.sh
#   BASE_URL=http://localhost:8002  # default 8000

set -e
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$BACKEND_DIR"

BASE_URL="${BASE_URL:-http://localhost:8000}"
EMAIL="${EMAIL:-}"
PASSWORD="${PASSWORD:-}"
LOG_FILE="${LOG_FILE:-}"

if [ -z "$EMAIL" ] || [ -z "$PASSWORD" ]; then
  echo "Usage: EMAIL=your@email.com PASSWORD=yourpass [BASE_URL=http://localhost:8000] [LOG_FILE=/path/to/log] $0"
  echo "Get a JWT via tokenAuth, then hit Feed, Portfolio, Trading. If LOG_FILE is set, greps it for GRAPHQL_PROFILING."
  exit 1
fi

echo "Getting JWT from $BASE_URL/graphql/ ..."
RESP=$(curl -s -X POST "$BASE_URL/graphql/" -H "Content-Type: application/json" \
  -d "{\"query\":\"mutation TokenAuth { tokenAuth(email: \\\"$EMAIL\\\", password: \\\"$PASSWORD\\\") { token } }\", \"operationName\":\"TokenAuth\"}")
TOKEN=$(echo "$RESP" | sed -n 's/.*"token":"\([^"]*\)".*/\1/p')
if [ -z "$TOKEN" ]; then
  echo "Failed to get token. Response: $RESP"
  exit 1
fi
echo "Token obtained."

echo "Hitting Feed (wallPosts)..."
curl -s -X POST "$BASE_URL/graphql/" -H "Content-Type: application/json" -H "Authorization: Bearer $TOKEN" \
  -d '{"query":"query Feed { wallPosts { id user { id } } }", "operationName":"Feed"}' > /dev/null
echo "Hitting Portfolio (myPortfolios)..."
curl -s -X POST "$BASE_URL/graphql/" -H "Content-Type: application/json" -H "Authorization: Bearer $TOKEN" \
  -d '{"query":"query Portfolio { myPortfolios { totalPortfolios totalValue } }", "operationName":"Portfolio"}' > /dev/null
echo "Hitting Trading (tradingAccount, brokerPositions)..."
curl -s -X POST "$BASE_URL/graphql/" -H "Content-Type: application/json" -H "Authorization: Bearer $TOKEN" \
  -d '{"query":"query Trading { tradingAccount { id } brokerPositions { id } }", "operationName":"Trading"}' > /dev/null
echo "Done."

if [ -n "$LOG_FILE" ] && [ -f "$LOG_FILE" ]; then
  echo ""
  echo "=== Top resolvers by duration (from $LOG_FILE) ==="
  grep GRAPHQL_PROFILING "$LOG_FILE" 2>/dev/null | sed -n 's/.*resolver=\([^ ]*\).*duration_ms=\([0-9.]*\).*/\2 \1/p' | sort -rn | head -20
  echo ""
  echo "=== Top resolvers by db_queries (when DEBUG=True) ==="
  grep GRAPHQL_PROFILING "$LOG_FILE" 2>/dev/null | sed -n 's/.*resolver=\([^ ]*\).*db_queries=\([0-9]*\).*/\2 \1/p' | sort -rn | head -20
else
  echo "Set LOG_FILE to the profiling log path to grep results (e.g. LOG_FILE=/tmp/graphql-profiling.log)."
fi
