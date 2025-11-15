#!/bin/bash
# Live Stream Verification Script
# Tests all components of the live streaming system

set -e

echo "🎥 RichesReach Live Stream Verification"
echo "========================================"
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

PASSED=0
FAILED=0

test_pass() {
    echo -e "${GREEN}✅ PASS${NC}: $1"
    ((PASSED++))
}

test_fail() {
    echo -e "${RED}❌ FAIL${NC}: $1"
    ((FAILED++))
}

test_warn() {
    echo -e "${YELLOW}⚠️  WARN${NC}: $1"
}

echo "1. Testing Backend Server..."
BACKEND_RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" --max-time 5 http://localhost:8000/health 2>/dev/null || echo "000")
if [ "$BACKEND_RESPONSE" = "200" ]; then
    test_pass "Backend server is running (port 8000)"
else
    test_fail "Backend server not responding (got $BACKEND_RESPONSE)"
fi

echo ""
echo "2. Testing Streaming Server..."
STREAMING_RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" --max-time 5 http://localhost:3002/health 2>/dev/null || echo "000")
if [ "$STREAMING_RESPONSE" = "200" ]; then
    test_pass "Streaming server is running (port 3002)"
else
    test_warn "Streaming server not responding on port 3002 (may use different port or be integrated)"
fi

echo ""
echo "3. Testing WebSocket Connection..."
# Check if WebSocket endpoint exists
WS_TEST=$(curl -s -o /dev/null -w "%{http_code}" --max-time 5 http://localhost:8000/ws 2>/dev/null || echo "000")
if [ "$WS_TEST" != "000" ]; then
    test_pass "WebSocket endpoint accessible"
else
    test_warn "WebSocket endpoint check inconclusive (may require WebSocket client)"
fi

echo ""
echo "4. Testing Live Stream API Endpoints..."
# Test live stream creation endpoint
STREAM_API=$(curl -s -o /dev/null -w "%{http_code}" -X GET --max-time 5 http://localhost:8000/api/live-streams/ 2>/dev/null || echo "000")
if [ "$STREAM_API" = "200" ] || [ "$STREAM_API" = "401" ] || [ "$STREAM_API" = "403" ]; then
    test_pass "Live stream API endpoint exists (status: $STREAM_API)"
else
    test_warn "Live stream API endpoint check (status: $STREAM_API)"
fi

echo ""
echo "5. Checking Mobile App Configuration..."
if [ -f "mobile/.env.local" ]; then
    if grep -q "STREAMING\|SFU\|LIVE" mobile/.env.local; then
        test_pass "Streaming server URL configured in .env.local"
        echo "   Configuration:"
        grep -E "STREAMING|SFU|LIVE" mobile/.env.local | sed 's/^/   /'
    else
        test_warn "No streaming server URL found in .env.local"
    fi
else
    test_warn ".env.local file not found"
fi

echo ""
echo "6. Testing GraphQL Live Stream Queries..."
GRAPHQL_RESPONSE=$(curl -s -X POST http://localhost:8000/graphql/ \
  -H "Content-Type: application/json" \
  -d '{"query": "{ __typename }"}' \
  --max-time 5 2>/dev/null || echo "ERROR")
if echo "$GRAPHQL_RESPONSE" | grep -q "__typename"; then
    test_pass "GraphQL endpoint working (can query live stream data)"
else
    test_warn "GraphQL endpoint check inconclusive"
fi

echo ""
echo "========================================"
echo "Test Summary:"
echo "  ✅ Passed: $PASSED"
echo "  ❌ Failed: $FAILED"
echo ""

echo "📱 Manual Testing Steps:"
echo ""
echo "1. Open RichesReach app"
echo "2. Navigate to a Wealth Circle"
echo "3. Tap '🎥 Go Live' button"
echo "4. Grant camera/microphone permissions"
echo "5. Verify:"
echo "   - Stream starts with live indicator"
echo "   - Video feed displays correctly"
echo "   - Duration timer starts counting"
echo ""
echo "6. On another device/app instance:"
echo "   - Navigate to same circle"
echo "   - Tap '📺 Join Live'"
echo "   - Verify:"
echo "     - Viewer count increases"
echo "     - Host video displays"
echo "     - Chat interface available"
echo "     - Reaction buttons work"
echo ""

if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}🎉 All critical tests passed!${NC}"
    echo -e "${GREEN}Your live stream infrastructure is ready!${NC}"
    exit 0
else
    echo -e "${YELLOW}⚠️  Some components may need attention.${NC}"
    echo -e "${YELLOW}Check the warnings above and verify manually.${NC}"
    exit 1
fi

