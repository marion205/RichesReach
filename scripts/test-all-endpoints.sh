#!/bin/bash
# Test all API endpoints for reachability and no 400/500 errors

set -e

API_BASE="${API_BASE:-http://localhost:8000}"
echo "🧪 Testing API endpoints at $API_BASE..."

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Track results
PASSED=0
FAILED=0
SKIPPED=0

test_endpoint() {
    local method=$1
    local endpoint=$2
    local data=$3
    local expected_status=${4:-200}
    
    local url="${API_BASE}${endpoint}"
    local response
    
    if [ "$method" = "GET" ]; then
        response=$(curl -s -w "\n%{http_code}" "$url" || echo "000")
    else
        response=$(curl -s -w "\n%{http_code}" -X "$method" -H "Content-Type: application/json" -d "$data" "$url" || echo "000")
    fi
    
    local body=$(echo "$response" | head -n -1)
    local status=$(echo "$response" | tail -n 1)
    
    if [ "$status" = "$expected_status" ] || [ "$status" = "200" ] || [ "$status" = "302" ]; then
        echo -e "${GREEN}✅${NC} $method $endpoint -> $status"
        ((PASSED++))
        return 0
    elif [ "$status" = "401" ] || [ "$status" = "403" ]; then
        echo -e "${YELLOW}⚠️${NC} $method $endpoint -> $status (auth required)"
        ((SKIPPED++))
        return 0
    else
        echo -e "${RED}❌${NC} $method $endpoint -> $status"
        echo "   Response: $body"
        ((FAILED++))
        return 1
    fi
}

echo ""
echo "📡 Testing GraphQL endpoint..."
test_endpoint "POST" "/graphql/" '{"query":"{ __typename }"}' 200

echo ""
echo "🔐 Testing OAuth endpoints..."
test_endpoint "GET" "/api/auth/alpaca/initiate" "" 302  # Redirects to Alpaca

echo ""
echo "🏦 Testing Banking endpoints (may require auth)..."
test_endpoint "GET" "/api/yodlee/accounts" "" 401  # Expected: auth required

echo ""
echo "📊 Testing Health/Status endpoints..."
test_endpoint "GET" "/admin/" "" 302  # Redirects to login

echo ""
echo "📈 Summary:"
echo -e "  ${GREEN}Passed: $PASSED${NC}"
echo -e "  ${YELLOW}Skipped (auth required): $SKIPPED${NC}"
echo -e "  ${RED}Failed: $FAILED${NC}"

if [ $FAILED -eq 0 ]; then
    echo ""
    echo -e "${GREEN}✅ All reachable endpoints are working!${NC}"
    exit 0
else
    echo ""
    echo -e "${RED}❌ Some endpoints failed!${NC}"
    exit 1
fi

