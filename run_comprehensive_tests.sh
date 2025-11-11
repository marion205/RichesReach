#!/bin/bash

# Comprehensive Test Runner for RichesReach - Production Readiness Check
set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Test results
BACKEND_TESTS_PASSED=0
BACKEND_TESTS_FAILED=0
MOBILE_TESTS_PASSED=0
MOBILE_TESTS_FAILED=0
INTEGRATION_TESTS_PASSED=0
INTEGRATION_TESTS_FAILED=0

echo -e "${BLUE}🧪 RichesReach Comprehensive Test Suite${NC}"
echo "=========================================="
echo ""

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# 1. BACKEND TESTS
echo -e "${BLUE}📋 Phase 1: Backend Unit & Integration Tests${NC}"
echo "=============================================="

if [ -d "deployment_package/backend" ]; then
    cd deployment_package/backend
    
    # Activate virtual environment if it exists
    if [ -d "venv" ]; then
        echo -e "${YELLOW}Activating virtual environment...${NC}"
        source venv/bin/activate
    fi
    
    # Check if Django is available
    if python3 -c "import django" 2>/dev/null; then
        echo -e "${GREEN}✅ Django is available${NC}"
        
        # Run Django tests
        echo -e "${YELLOW}Running Django unit tests...${NC}"
        if python3 manage.py test core.tests --verbosity=2 --keepdb 2>&1 | tee /tmp/backend_tests.log; then
            BACKEND_TESTS_PASSED=1
            echo -e "${GREEN}✅ Backend Django tests PASSED${NC}"
        else
            BACKEND_TESTS_FAILED=1
            echo -e "${RED}❌ Backend Django tests FAILED${NC}"
        fi
        
        # Run pytest tests if available
        if command_exists pytest; then
            echo -e "${YELLOW}Running pytest tests...${NC}"
            if python3 -m pytest core/tests/ -v --tb=short --cov=core --cov-report=term-missing 2>&1 | tee /tmp/pytest_tests.log; then
                echo -e "${GREEN}✅ Pytest tests PASSED${NC}"
            else
                echo -e "${RED}❌ Pytest tests FAILED${NC}"
                BACKEND_TESTS_FAILED=1
            fi
        fi
    else
        echo -e "${YELLOW}⚠️  Django not available, skipping Django tests${NC}"
    fi
    
    cd ../..
else
    echo -e "${YELLOW}⚠️  Backend directory not found${NC}"
fi

echo ""

# 2. MOBILE TESTS
echo -e "${BLUE}📋 Phase 2: Mobile Unit Tests${NC}"
echo "=============================================="

if [ -d "mobile" ]; then
    cd mobile
    
    # Check if node_modules exists
    if [ ! -d "node_modules" ]; then
        echo -e "${YELLOW}Installing mobile dependencies...${NC}"
        npm install --silent
    fi
    
    # Run Jest tests
    if command_exists npm; then
        echo -e "${YELLOW}Running Jest unit tests...${NC}"
        if npm test -- --coverage --watchAll=false --verbose 2>&1 | tee /tmp/mobile_tests.log; then
            MOBILE_TESTS_PASSED=1
            echo -e "${GREEN}✅ Mobile tests PASSED${NC}"
        else
            MOBILE_TESTS_FAILED=1
            echo -e "${RED}❌ Mobile tests FAILED${NC}"
        fi
    else
        echo -e "${YELLOW}⚠️  npm not available, skipping mobile tests${NC}"
    fi
    
    cd ..
else
    echo -e "${YELLOW}⚠️  Mobile directory not found${NC}"
fi

echo ""

# 3. INTEGRATION TESTS
echo -e "${BLUE}📋 Phase 3: Integration Tests${NC}"
echo "=============================================="

if [ -d "tests/integration" ]; then
    if command_exists pytest; then
        echo -e "${YELLOW}Running integration tests...${NC}"
        if python3 -m pytest tests/integration/ -v --tb=short 2>&1 | tee /tmp/integration_tests.log; then
            INTEGRATION_TESTS_PASSED=1
            echo -e "${GREEN}✅ Integration tests PASSED${NC}"
        else
            INTEGRATION_TESTS_FAILED=1
            echo -e "${RED}❌ Integration tests FAILED${NC}"
        fi
    else
        echo -e "${YELLOW}⚠️  pytest not available, skipping integration tests${NC}"
    fi
else
    echo -e "${YELLOW}⚠️  Integration tests directory not found${NC}"
fi

echo ""

# 4. COVERAGE REPORT
echo -e "${BLUE}📋 Phase 4: Coverage Report${NC}"
echo "=============================================="

# Backend coverage
if [ -f "/tmp/pytest_tests.log" ]; then
    echo -e "${YELLOW}Backend Coverage:${NC}"
    grep -A 20 "TOTAL" /tmp/pytest_tests.log | tail -5 || echo "Coverage info not found"
fi

# Mobile coverage
if [ -f "mobile/coverage/coverage-summary.json" ]; then
    echo -e "${YELLOW}Mobile Coverage:${NC}"
    cat mobile/coverage/coverage-summary.json | grep -A 5 "total" || echo "Coverage summary not found"
fi

echo ""

# 5. FINAL SUMMARY
echo -e "${BLUE}📊 Test Results Summary${NC}"
echo "=============================================="
echo ""

TOTAL_FAILED=$((BACKEND_TESTS_FAILED + MOBILE_TESTS_FAILED + INTEGRATION_TESTS_FAILED))

if [ $BACKEND_TESTS_PASSED -eq 1 ]; then
    echo -e "${GREEN}✅ Backend Tests: PASSED${NC}"
else
    echo -e "${RED}❌ Backend Tests: FAILED${NC}"
fi

if [ $MOBILE_TESTS_PASSED -eq 1 ]; then
    echo -e "${GREEN}✅ Mobile Tests: PASSED${NC}"
else
    echo -e "${RED}❌ Mobile Tests: FAILED${NC}"
fi

if [ $INTEGRATION_TESTS_PASSED -eq 1 ]; then
    echo -e "${GREEN}✅ Integration Tests: PASSED${NC}"
else
    echo -e "${RED}❌ Integration Tests: FAILED${NC}"
fi

echo ""

if [ $TOTAL_FAILED -eq 0 ]; then
    echo -e "${GREEN}🎉 ALL TESTS PASSED! Production ready! 🚀${NC}"
    exit 0
else
    echo -e "${RED}❌ SOME TESTS FAILED. Review errors above.${NC}"
    echo ""
    echo -e "${YELLOW}Test logs saved to:${NC}"
    echo "  - /tmp/backend_tests.log"
    echo "  - /tmp/pytest_tests.log"
    echo "  - /tmp/mobile_tests.log"
    echo "  - /tmp/integration_tests.log"
    exit 1
fi

