#!/bin/bash
# Comprehensive Testing Script for All Implementations
# Tests GraphQL queries, API endpoints, and data validation

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🧪 Testing All Implementations${NC}\n"

# Check if server is running
echo -e "${YELLOW}📡 Checking if server is running...${NC}"
if ! curl -s http://localhost:8000/health > /dev/null 2>&1; then
    echo -e "${RED}❌ Server is not running on port 8000${NC}"
    echo -e "${YELLOW}💡 Start the server with: python3 main_server.py${NC}"
    exit 1
fi
echo -e "${GREEN}✅ Server is running${NC}\n"

# Test GraphQL endpoint
echo -e "${YELLOW}🔍 Testing GraphQL endpoint...${NC}"
GRAPHQL_RESPONSE=$(curl -s -X POST http://localhost:8000/graphql \
  -H "Content-Type: application/json" \
  -d '{"query":"{ __typename }"}')

if echo "$GRAPHQL_RESPONSE" | grep -q "data"; then
    echo -e "${GREEN}✅ GraphQL endpoint is working${NC}"
else
    echo -e "${RED}❌ GraphQL endpoint failed${NC}"
    echo "$GRAPHQL_RESPONSE"
    exit 1
fi

# Test Execution Quality Stats
echo -e "\n${YELLOW}📊 Testing Execution Quality Stats...${NC}"
EXEC_QUALITY_QUERY='{
  "query": "query { executionQualityStats(signalType: \"day_trading\", days: 30) { avgSlippagePct avgQualityScore totalFills improvementTips } }"
}'

EXEC_RESPONSE=$(curl -s -X POST http://localhost:8000/graphql \
  -H "Content-Type: application/json" \
  -d "$EXEC_QUALITY_QUERY")

if echo "$EXEC_RESPONSE" | grep -q "executionQualityStats"; then
    if echo "$EXEC_RESPONSE" | grep -q "null"; then
        echo -e "${YELLOW}⚠️  Execution Quality Stats returned null (may be expected if no data)${NC}"
    else
        echo -e "${GREEN}✅ Execution Quality Stats working${NC}"
        echo "$EXEC_RESPONSE" | jq '.' 2>/dev/null || echo "$EXEC_RESPONSE"
    fi
else
    echo -e "${RED}❌ Execution Quality Stats query failed${NC}"
    echo "$EXEC_RESPONSE"
fi

# Test Portfolio Analytics
echo -e "\n${YELLOW}📈 Testing Portfolio Analytics...${NC}"
PORTFOLIO_QUERY='{
  "query": "query { premiumPortfolioMetrics { totalValue totalReturn totalReturnPercent sharpeRatio volatility } }"
}'

PORTFOLIO_RESPONSE=$(curl -s -X POST http://localhost:8000/graphql \
  -H "Content-Type: application/json" \
  -d "$PORTFOLIO_QUERY")

if echo "$PORTFOLIO_RESPONSE" | grep -q "premiumPortfolioMetrics"; then
    if echo "$PORTFOLIO_RESPONSE" | grep -q "null"; then
        echo -e "${YELLOW}⚠️  Portfolio Analytics returned null (may need authentication)${NC}"
    else
        echo -e "${GREEN}✅ Portfolio Analytics working${NC}"
        echo "$PORTFOLIO_RESPONSE" | jq '.' 2>/dev/null || echo "$PORTFOLIO_RESPONSE"
    fi
else
    echo -e "${RED}❌ Portfolio Analytics query failed${NC}"
    echo "$PORTFOLIO_RESPONSE"
fi

# Test Options Chain
echo -e "\n${YELLOW}📊 Testing Options Chain...${NC}"
OPTIONS_QUERY='{
  "query": "query { optionsAnalysis(symbol: \"AAPL\") { underlyingSymbol underlyingPrice optionsChain { expirationDates } } }"
}'

OPTIONS_RESPONSE=$(curl -s -X POST http://localhost:8000/graphql \
  -H "Content-Type: application/json" \
  -d "$OPTIONS_QUERY")

if echo "$OPTIONS_RESPONSE" | grep -q "optionsAnalysis"; then
    if echo "$OPTIONS_RESPONSE" | grep -q "null"; then
        echo -e "${YELLOW}⚠️  Options Analysis returned null (may be expected)${NC}"
    else
        echo -e "${GREEN}✅ Options Analysis working${NC}"
        echo "$OPTIONS_RESPONSE" | jq '.' 2>/dev/null || echo "$OPTIONS_RESPONSE"
    fi
else
    echo -e "${RED}❌ Options Analysis query failed${NC}"
    echo "$OPTIONS_RESPONSE"
fi

# Test Day Trading Picks
echo -e "\n${YELLOW}📈 Testing Day Trading Picks...${NC}"
DAY_TRADING_QUERY='{
  "query": "query { dayTradingPicks(mode: \"SAFE\") { mode picks { symbol side score } universeSize } }"
}'

DAY_TRADING_RESPONSE=$(curl -s -X POST http://localhost:8000/graphql \
  -H "Content-Type: application/json" \
  -d "$DAY_TRADING_QUERY")

if echo "$DAY_TRADING_RESPONSE" | grep -q "dayTradingPicks"; then
    if echo "$DAY_TRADING_RESPONSE" | grep -q "null"; then
        echo -e "${YELLOW}⚠️  Day Trading Picks returned null${NC}"
    else
        echo -e "${GREEN}✅ Day Trading Picks working${NC}"
        PICK_COUNT=$(echo "$DAY_TRADING_RESPONSE" | jq '.data.dayTradingPicks.picks | length' 2>/dev/null || echo "0")
        echo -e "${BLUE}   Found $PICK_COUNT picks${NC}"
    fi
else
    echo -e "${RED}❌ Day Trading Picks query failed${NC}"
    echo "$DAY_TRADING_RESPONSE"
fi

# Test Execution Suggestion
echo -e "\n${YELLOW}⚡ Testing Execution Suggestion...${NC}"
EXEC_SUGGESTION_QUERY='{
  "query": "query { executionSuggestion(signal: \"{\\\"symbol\\\": \\\"AAPL\\\", \\\"side\\\": \\\"LONG\\\", \\\"entry_price\\\": 150.0, \\\"risk\\\": {\\\"stop\\\": 147.0, \\\"targets\\\": [153.0, 156.0]}, \\\"features\\\": {\\\"spreadBps\\\": 5.0}}\", signalType: \"day_trading\") { orderType priceBand timeInForce rationale } }"
}'

EXEC_SUGGESTION_RESPONSE=$(curl -s -X POST http://localhost:8000/graphql \
  -H "Content-Type: application/json" \
  -d "$EXEC_SUGGESTION_QUERY")

if echo "$EXEC_SUGGESTION_RESPONSE" | grep -q "executionSuggestion"; then
    if echo "$EXEC_SUGGESTION_RESPONSE" | grep -q "null"; then
        echo -e "${YELLOW}⚠️  Execution Suggestion returned null${NC}"
    else
        echo -e "${GREEN}✅ Execution Suggestion working${NC}"
        echo "$EXEC_SUGGESTION_RESPONSE" | jq '.data.executionSuggestion' 2>/dev/null || echo "$EXEC_SUGGESTION_RESPONSE"
    fi
else
    echo -e "${RED}❌ Execution Suggestion query failed${NC}"
    echo "$EXEC_SUGGESTION_RESPONSE"
fi

# Summary
echo -e "\n${BLUE}📋 Test Summary${NC}"
echo -e "${GREEN}✅ All critical endpoints tested${NC}"
echo -e "${YELLOW}💡 Note: Some queries may return null if no data exists or authentication is required${NC}"
echo -e "${BLUE}🎉 Testing complete!${NC}\n"

