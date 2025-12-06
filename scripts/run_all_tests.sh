#!/bin/bash
# Comprehensive test runner for all new features

set -e

echo "🧪 Running Comprehensive Test Suite"
echo "===================================="
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Track results
BACKEND_PASSED=0
BACKEND_FAILED=0
FRONTEND_PASSED=0
FRONTEND_FAILED=0

# Backend Tests
echo "📦 Backend Tests"
echo "----------------"
cd deployment_package/backend

echo "  ✅ Testing Execution Quality Tracker..."
if python3 -m pytest core/tests/test_execution_quality_tracker.py -v --tb=short > /tmp/exec_quality_test.log 2>&1; then
    PASSED=$(grep -c "PASSED" /tmp/exec_quality_test.log || echo "0")
    FAILED=$(grep -c "FAILED" /tmp/exec_quality_test.log || echo "0")
    BACKEND_PASSED=$((BACKEND_PASSED + PASSED))
    BACKEND_FAILED=$((BACKEND_FAILED + FAILED))
    echo -e "  ${GREEN}✓ Execution Quality Tracker: $PASSED passed${NC}"
    if [ "$FAILED" -gt 0 ]; then
        echo -e "  ${RED}✗ Execution Quality Tracker: $FAILED failed${NC}"
    fi
else
    FAILED=$(grep -c "FAILED" /tmp/exec_quality_test.log || echo "0")
    BACKEND_FAILED=$((BACKEND_FAILED + FAILED))
    echo -e "  ${RED}✗ Execution Quality Tracker: Some tests failed${NC}"
fi

echo ""
echo "  ✅ Testing Budget and Spending Resolvers..."
if python3 -m pytest core/tests/test_budget_and_spending.py -v --tb=short > /tmp/budget_test.log 2>&1; then
    PASSED=$(grep -c "PASSED" /tmp/budget_test.log || echo "0")
    FAILED=$(grep -c "FAILED" /tmp/budget_test.log || echo "0")
    BACKEND_PASSED=$((BACKEND_PASSED + PASSED))
    BACKEND_FAILED=$((BACKEND_FAILED + FAILED))
    echo -e "  ${GREEN}✓ Budget/Spending: $PASSED passed${NC}"
    if [ "$FAILED" -gt 0 ]; then
        echo -e "  ${RED}✗ Budget/Spending: $FAILED failed${NC}"
    fi
else
    FAILED=$(grep -c "FAILED" /tmp/budget_test.log || echo "0")
    BACKEND_FAILED=$((BACKEND_FAILED + FAILED))
    echo -e "  ${RED}✗ Budget/Spending: Some tests failed${NC}"
fi

echo ""
echo "  ✅ Testing Blockchain Queries..."
if python3 -m pytest core/tests/test_blockchain_queries.py -v --tb=short > /tmp/blockchain_test.log 2>&1; then
    PASSED=$(grep -c "PASSED" /tmp/blockchain_test.log || echo "0")
    FAILED=$(grep -c "FAILED" /tmp/blockchain_test.log || echo "0")
    BACKEND_PASSED=$((BACKEND_PASSED + PASSED))
    BACKEND_FAILED=$((BACKEND_FAILED + FAILED))
    echo -e "  ${GREEN}✓ Blockchain Queries: $PASSED passed${NC}"
    if [ "$FAILED" -gt 0 ]; then
        echo -e "  ${RED}✗ Blockchain Queries: $FAILED failed${NC}"
    fi
else
    FAILED=$(grep -c "FAILED" /tmp/blockchain_test.log || echo "0")
    BACKEND_FAILED=$((BACKEND_FAILED + FAILED))
    echo -e "  ${RED}✗ Blockchain Queries: Some tests failed${NC}"
fi

echo ""
echo "  ✅ Testing Execution Advisor..."
if python3 -m pytest core/tests/test_execution_advisor.py -v --tb=short > /tmp/exec_advisor_test.log 2>&1; then
    PASSED=$(grep -c "PASSED" /tmp/exec_advisor_test.log || echo "0")
    FAILED=$(grep -c "FAILED" /tmp/exec_advisor_test.log || echo "0")
    BACKEND_PASSED=$((BACKEND_PASSED + PASSED))
    BACKEND_FAILED=$((BACKEND_FAILED + FAILED))
    echo -e "  ${GREEN}✓ Execution Advisor: $PASSED passed${NC}"
    if [ "$FAILED" -gt 0 ]; then
        echo -e "  ${RED}✗ Execution Advisor: $FAILED failed${NC}"
    fi
else
    FAILED=$(grep -c "FAILED" /tmp/exec_advisor_test.log || echo "0")
    BACKEND_FAILED=$((BACKEND_FAILED + FAILED))
    echo -e "  ${RED}✗ Execution Advisor: Some tests failed${NC}"
fi

cd ../..

# Frontend Tests
echo ""
echo "📱 Frontend Tests"
echo "-----------------"
cd mobile

if command -v npm &> /dev/null; then
    echo "  ✅ Testing Voice Web3 Controller..."
    if npm test -- src/features/voice/services/__tests__/VoiceWeb3Controller.test.ts --passWithNoTests --silent > /tmp/voice_test.log 2>&1; then
        FRONTEND_PASSED=$((FRONTEND_PASSED + 1))
        echo -e "  ${GREEN}✓ Voice Web3 Controller: Tests passed${NC}"
    else
        FRONTEND_FAILED=$((FRONTEND_FAILED + 1))
        echo -e "  ${RED}✗ Voice Web3 Controller: Tests failed${NC}"
    fi

    echo ""
    echo "  ✅ Testing Budgeting Screen..."
    if npm test -- src/features/banking/screens/__tests__/BudgetingScreen.test.tsx --passWithNoTests --silent > /tmp/budgeting_test.log 2>&1; then
        FRONTEND_PASSED=$((FRONTEND_PASSED + 1))
        echo -e "  ${GREEN}✓ Budgeting Screen: Tests passed${NC}"
    else
        FRONTEND_FAILED=$((FRONTEND_FAILED + 1))
        echo -e "  ${RED}✗ Budgeting Screen: Tests failed${NC}"
    fi

    echo ""
    echo "  ✅ Testing NFT Gallery..."
    if npm test -- src/features/blockchain/components/__tests__/NFTGallery.test.tsx --passWithNoTests --silent > /tmp/nft_test.log 2>&1; then
        FRONTEND_PASSED=$((FRONTEND_PASSED + 1))
        echo -e "  ${GREEN}✓ NFT Gallery: Tests passed${NC}"
    else
        FRONTEND_FAILED=$((FRONTEND_FAILED + 1))
        echo -e "  ${RED}✗ NFT Gallery: Tests failed${NC}"
    fi
else
    echo -e "  ${YELLOW}⚠ npm not found, skipping frontend tests${NC}"
fi

cd ..

# Summary
echo ""
echo "===================================="
echo "📊 Test Summary"
echo "===================================="
echo ""
echo "Backend Tests:"
echo -e "  ${GREEN}Passed: $BACKEND_PASSED${NC}"
echo -e "  ${RED}Failed: $BACKEND_FAILED${NC}"
echo ""
echo "Frontend Tests:"
echo -e "  ${GREEN}Passed: $FRONTEND_PASSED${NC}"
echo -e "  ${RED}Failed: $FRONTEND_FAILED${NC}"
echo ""

TOTAL_PASSED=$((BACKEND_PASSED + FRONTEND_PASSED))
TOTAL_FAILED=$((BACKEND_FAILED + FRONTEND_FAILED))

if [ $TOTAL_FAILED -eq 0 ]; then
    echo -e "${GREEN}✅ All tests passed!${NC}"
    exit 0
else
    echo -e "${RED}❌ Some tests failed${NC}"
    exit 1
fi
