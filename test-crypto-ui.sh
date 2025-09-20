#!/bin/bash

echo "🚀 Crypto UI Testing Suite"
echo "=========================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Test functions
test_api() {
    local name="$1"
    local url="$2"
    local expected_field="$3"
    
    echo -n "Testing $name... "
    response=$(curl -s "$url" 2>/dev/null)
    
    if [ $? -eq 0 ] && echo "$response" | grep -q "$expected_field"; then
        echo -e "${GREEN}✅ PASS${NC}"
        return 0
    else
        echo -e "${RED}❌ FAIL${NC}"
        return 1
    fi
}

test_performance() {
    local name="$1"
    local url="$2"
    
    echo -n "Performance test $name... "
    start_time=$(date +%s%3N)
    curl -s "$url" > /dev/null 2>&1
    end_time=$(date +%s%3N)
    duration=$((end_time - start_time))
    
    if [ $duration -lt 100 ]; then
        echo -e "${GREEN}✅ ${duration}ms${NC}"
    else
        echo -e "${YELLOW}⚠️  ${duration}ms${NC}"
    fi
}

# Check if servers are running
echo -e "${BLUE}Checking services...${NC}"
if ! curl -s "http://localhost:8127/api/crypto/currencies" > /dev/null; then
    echo -e "${RED}❌ Crypto API server not running on port 8127${NC}"
    echo "Start it with: python3 backend/mock_crypto_server.py &"
    exit 1
fi

if ! curl -s "http://localhost:8128/api/crypto/loans" > /dev/null; then
    echo -e "${RED}❌ Repay API server not running on port 8128${NC}"
    echo "Start it with: python3 backend/mock_repay_server.py &"
    exit 1
fi

echo -e "${GREEN}✅ All services running${NC}"
echo ""

# API Tests
echo -e "${BLUE}API Endpoint Tests${NC}"
echo "-------------------"
test_api "Currencies API" "http://localhost:8127/api/crypto/currencies" "currencies"
test_api "Portfolio API" "http://localhost:8127/api/crypto/portfolio" "total_value_usd"
test_api "ML Signal API" "http://localhost:8127/api/crypto/ml/signal/BTC" "predictionType"
test_api "SBLOC Loans API" "http://localhost:8128/api/crypto/loans" "loans"
test_api "Repay API" "http://localhost:8128/api/crypto/repay" "success"

echo ""

# Performance Tests
echo -e "${BLUE}Performance Tests${NC}"
echo "------------------"
test_performance "Currencies" "http://localhost:8127/api/crypto/currencies"
test_performance "Portfolio" "http://localhost:8127/api/crypto/portfolio"
test_performance "ML Signal" "http://localhost:8127/api/crypto/ml/signal/BTC"
test_performance "Loans" "http://localhost:8128/api/crypto/loans"

echo ""

# GraphQL Tests
echo -e "${BLUE}GraphQL Tests${NC}"
echo "-------------"
echo -n "Testing GraphQL repay... "
repay_response=$(curl -s -X POST "http://localhost:8128/graphql" \
  -H "Content-Type: application/json" \
  -d '{"query": "mutation { repaySblocLoan(loanId: \"loan_1\", amountUsd: 500.0) { success message newOutstanding interestPaid principalPaid } }"}')

if echo "$repay_response" | grep -q '"success": true'; then
    echo -e "${GREEN}✅ PASS${NC}"
else
    echo -e "${RED}❌ FAIL${NC}"
fi

echo ""

# Data Quality Tests
echo -e "${BLUE}Data Quality Tests${NC}"
echo "-------------------"

# Test portfolio data structure
portfolio_data=$(curl -s "http://localhost:8127/api/crypto/portfolio")
if echo "$portfolio_data" | python3 -c "
import sys, json
data = json.load(sys.stdin)
required_fields = ['total_value_usd', 'total_pnl', 'holdings']
if all(field in data for field in required_fields):
    print('✅ Portfolio data structure valid')
    print(f'   Total Value: \${data[\"total_value_usd\"]:,.2f}')
    print(f'   PnL: {data[\"total_pnl_percentage\"]:+.2f}%')
    print(f'   Holdings: {len(data[\"holdings\"])} assets')
else:
    print('❌ Portfolio data structure invalid')
    sys.exit(1)
"; then
    echo ""
else
    echo -e "${RED}❌ Portfolio data validation failed${NC}"
fi

# Test ML signal data structure
ml_data=$(curl -s "http://localhost:8127/api/crypto/ml/signal/BTC")
if echo "$ml_data" | python3 -c "
import sys, json
data = json.load(sys.stdin)
required_fields = ['symbol', 'predictionType', 'probability', 'confidenceLevel']
if all(field in data for field in required_fields):
    print('✅ ML Signal data structure valid')
    print(f'   {data[\"symbol\"]}: {data[\"predictionType\"]} ({data[\"probability\"]*100:.1f}%)')
    print(f'   Confidence: {data[\"confidenceLevel\"]}')
    print(f'   Sentiment: {data[\"sentiment\"]}')
else:
    print('❌ ML Signal data structure invalid')
    sys.exit(1)
"; then
    echo ""
else
    echo -e "${RED}❌ ML Signal data validation failed${NC}"
fi

echo -e "${GREEN}🎉 Crypto UI Testing Complete!${NC}"
echo ""
echo -e "${BLUE}Next Steps:${NC}"
echo "1. Open your React Native app"
echo "2. Navigate to the Crypto screen"
echo "3. Test all components interactively"
echo "4. Check console for any errors"
echo ""
echo -e "${BLUE}Available Test Data:${NC}"
echo "• Portfolio: \$47,754.25 (-3.33% PnL)"
echo "• Holdings: BTC, ETH, SOL"
echo "• Loans: \$5,000 BTC, \$2,500 ETH"
echo "• ML Signal: BTC BIG_DOWN_DAY (54.4%)"
echo ""
echo -e "${BLUE}API Endpoints:${NC}"
echo "• Crypto API: http://localhost:8127"
echo "• Repay API: http://localhost:8128"
echo "• GraphQL: Both servers support GraphQL"
