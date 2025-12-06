#!/bin/bash

# RAHA End-to-End Test Script
# Tests all GraphQL queries and mutations

echo "🧪 RAHA End-to-End Testing"
echo "=========================="
echo ""

BASE_URL="http://127.0.0.1:8000/graphql/"
AUTH_HEADER="Authorization: Bearer dev-token-test"

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

test_query() {
    local name=$1
    local query=$2
    
    echo -n "Testing $name... "
    
    # Create temp file with proper JSON
    temp_file=$(mktemp)
    echo "{\"query\": \"$query\"}" > "$temp_file"
    
    response=$(curl -s -X POST "$BASE_URL" \
        -H "Content-Type: application/json" \
        -H "$AUTH_HEADER" \
        -d "@$temp_file")
    
    rm "$temp_file"
    
    if echo "$response" | grep -q "\"errors\""; then
        echo -e "${RED}FAIL${NC}"
        echo "$response" | python -m json.tool 2>/dev/null | head -20
        return 1
    elif echo "$response" | grep -q "\"data\""; then
        echo -e "${GREEN}PASS${NC}"
        return 0
    else
        echo -e "${YELLOW}UNKNOWN${NC}"
        echo "$response" | head -5
        return 2
    fi
}

# Test 1: Get Strategies
test_query "Get Strategies" "query { strategies { id name slug description category } }"

# Test 2: Get User Strategy Settings
test_query "Get User Strategy Settings" "query { userStrategySettings { id enabled parameters strategyVersion { id strategy { name } } } }"

# Test 3: Get RAHA Signals
test_query "Get RAHA Signals" "query { rahaSignals(symbol: \"AAPL\", timeframe: \"5m\", limit: 5) { id signalType price stopLoss takeProfit confidenceScore } }"

# Test 4: Get Stock Chart Data
test_query "Get Stock Chart Data" "query { stockChartData(symbol: \"AAPL\", timeframe: \"1H\") { symbol data { timestamp open close } } }"

# Test 5: Get User Backtests (metrics is JSONString, no subfields)
test_query "Get User Backtests" "query { userBacktests(limit: 5) { id status createdAt metrics } }"

echo ""
echo "✅ Basic GraphQL tests complete!"
echo ""
echo "Next steps:"
echo "1. Test in mobile app: Enable/disable strategies"
echo "2. Test signal generation from Strategy Detail"
echo "3. Test The Whisper screen with real signals"
echo "4. Test backtest execution"
echo "5. Test navigation flows"

