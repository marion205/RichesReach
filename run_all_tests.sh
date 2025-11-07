#!/bin/bash
# Run all tests for Family Sharing and Web/PWA features

echo "🧪 Running All Tests for Family Sharing & Web/PWA"
echo "=================================================="
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Track results
TOTAL_TESTS=0
PASSED_TESTS=0
FAILED_TESTS=0

# Function to run tests and track results
run_test_suite() {
    local suite_name=$1
    local test_path=$2
    
    echo -e "${YELLOW}Running: ${suite_name}${NC}"
    echo "----------------------------------------"
    
    if [ -d "deployment_package/backend/venv" ]; then
        source deployment_package/backend/venv/bin/activate
        result=$(python -m pytest "$test_path" -v --tb=line 2>&1)
        exit_code=$?
        
        # Count tests
        passed=$(echo "$result" | grep -c "PASSED" || echo "0")
        failed=$(echo "$result" | grep -c "FAILED" || echo "0")
        total=$((passed + failed))
        
        TOTAL_TESTS=$((TOTAL_TESTS + total))
        PASSED_TESTS=$((PASSED_TESTS + passed))
        FAILED_TESTS=$((FAILED_TESTS + failed))
        
        if [ $exit_code -eq 0 ]; then
            echo -e "${GREEN}✅ ${suite_name}: ${passed}/${total} passed${NC}"
        else
            echo -e "${RED}❌ ${suite_name}: ${failed} failed${NC}"
            echo "$result" | tail -20
        fi
    else
        echo -e "${RED}⚠️  Virtual environment not found${NC}"
    fi
    
    echo ""
}

# Run all test suites
echo "📦 Backend API Tests"
echo "===================="
run_test_suite "Constellation AI API" "deployment_package/backend/core/tests/test_constellation_ai_api.py"
run_test_suite "Constellation AI Integration" "deployment_package/backend/core/tests/test_constellation_ai_integration.py"
run_test_suite "Family Sharing API" "deployment_package/backend/core/tests/test_family_sharing_api.py"
run_test_suite "Family Sharing Integration" "deployment_package/backend/core/tests/test_family_sharing_integration.py"

# Summary
echo "=================================================="
echo "📊 Test Summary"
echo "=================================================="
echo -e "Total Tests: ${TOTAL_TESTS}"
echo -e "${GREEN}Passed: ${PASSED_TESTS}${NC}"
if [ $FAILED_TESTS -gt 0 ]; then
    echo -e "${RED}Failed: ${FAILED_TESTS}${NC}"
else
    echo -e "Failed: ${FAILED_TESTS}"
fi

if [ $FAILED_TESTS -eq 0 ]; then
    echo ""
    echo -e "${GREEN}🎉 All tests passed!${NC}"
    exit 0
else
    echo ""
    echo -e "${RED}⚠️  Some tests failed${NC}"
    exit 1
fi
