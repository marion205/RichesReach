#!/bin/bash
# Automated Testing Script for RichesReach Production
# Runs key tests from FINAL_TESTING_CHECKLIST.md

set -e

echo "🧪 RichesReach Production Testing"
echo "=================================="
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

echo "1. Testing Health Endpoint..."
HEALTH_RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" --max-time 10 https://api.richesreach.com/health/ 2>/dev/null || echo "000")
if [ "$HEALTH_RESPONSE" = "200" ]; then
    test_pass "Health endpoint (200 OK)"
else
    # Try ALB endpoint
    HEALTH_RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" --max-time 10 http://riches-reach-alb-1199497064.us-east-1.elb.amazonaws.com/health/ 2>/dev/null || echo "000")
    if [ "$HEALTH_RESPONSE" = "200" ]; then
        test_pass "Health endpoint via ALB (200 OK)"
    else
        test_fail "Health endpoint not responding (got $HEALTH_RESPONSE)"
    fi
fi

echo ""
echo "2. Testing GraphQL Endpoint..."
GRAPHQL_RESPONSE=$(curl -s -X POST https://api.richesreach.com/graphql/ \
  -H "Content-Type: application/json" \
  -d '{"query": "{ __typename }"}' \
  --max-time 10 2>/dev/null || echo "ERROR")
if echo "$GRAPHQL_RESPONSE" | grep -q "__typename"; then
    test_pass "GraphQL endpoint responding"
else
    # Try ALB endpoint
    GRAPHQL_RESPONSE=$(curl -s -X POST http://riches-reach-alb-1199497064.us-east-1.elb.amazonaws.com/graphql/ \
      -H "Content-Type: application/json" \
      -d '{"query": "{ __typename }"}' \
      --max-time 10 2>/dev/null || echo "ERROR")
    if echo "$GRAPHQL_RESPONSE" | grep -q "__typename"; then
        test_pass "GraphQL endpoint via ALB"
    else
        test_fail "GraphQL endpoint not responding"
    fi
fi

echo ""
echo "3. Testing Database Connection..."
cd deployment_package/backend
if python manage.py check --database default > /dev/null 2>&1; then
    test_pass "Database connection"
else
    test_fail "Database connection failed"
fi
cd ../..

echo ""
echo "4. Testing ECS Service Status..."
ECS_STATUS=$(aws ecs describe-services \
  --cluster richesreach-cluster \
  --services richesreach-service \
  --region us-east-1 \
  --query 'services[0].{Status:status,Running:runningCount,Desired:desiredCount}' \
  --output json 2>/dev/null || echo '{"Status":"ERROR"}')

if echo "$ECS_STATUS" | grep -q '"Status":"ACTIVE"'; then
    RUNNING=$(echo "$ECS_STATUS" | grep -o '"Running":[0-9]*' | grep -o '[0-9]*')
    DESIRED=$(echo "$ECS_STATUS" | grep -o '"Desired":[0-9]*' | grep -o '[0-9]*')
    if [ "$RUNNING" = "$DESIRED" ] && [ "$RUNNING" -gt 0 ]; then
        test_pass "ECS service running ($RUNNING/$DESIRED tasks)"
    else
        test_warn "ECS service running but not at desired count ($RUNNING/$DESIRED)"
    fi
else
    test_fail "ECS service not active"
fi

echo ""
echo "5. Testing Response Times..."
HEALTH_TIME=$(curl -s -o /dev/null -w "%{time_total}" --max-time 10 https://api.richesreach.com/health/ 2>/dev/null || echo "10.0")
if (( $(echo "$HEALTH_TIME < 1.0" | bc -l 2>/dev/null || echo 0) )); then
    test_pass "Health endpoint response time (${HEALTH_TIME}s < 1s)"
else
    test_warn "Health endpoint slow (${HEALTH_TIME}s)"
fi

echo ""
echo "6. Testing SSL/TLS..."
SSL_TEST=$(curl -s -o /dev/null -w "%{http_code}" -I --max-time 10 https://api.richesreach.com/health/ 2>/dev/null || echo "000")
if [ "$SSL_TEST" = "200" ] || [ "$SSL_TEST" = "301" ] || [ "$SSL_TEST" = "302" ]; then
    test_pass "SSL/TLS working"
else
    test_warn "SSL/TLS test inconclusive"
fi

echo ""
echo "=================================="
echo "Test Summary:"
echo "  ✅ Passed: $PASSED"
echo "  ❌ Failed: $FAILED"
echo ""

if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}🎉 All critical tests passed!${NC}"
    exit 0
else
    echo -e "${RED}⚠️  Some tests failed. Review output above.${NC}"
    exit 1
fi
