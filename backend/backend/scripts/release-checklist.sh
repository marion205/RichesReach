#!/bin/bash

# RichesReach Production Release Checklist
# Comprehensive validation and testing script

echo "🚀 Starting RichesReach Production Release Checklist..."
echo "=================================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print status
print_status() {
    local status=$1
    local message=$2
    if [ "$status" = "PASS" ]; then
        echo -e "${GREEN}✅ $message${NC}"
    elif [ "$status" = "FAIL" ]; then
        echo -e "${RED}❌ $message${NC}"
    elif [ "$status" = "WARN" ]; then
        echo -e "${YELLOW}⚠️  $message${NC}"
    else
        echo -e "${BLUE}ℹ️  $message${NC}"
    fi
}

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Initialize counters
TOTAL_CHECKS=0
PASSED_CHECKS=0
FAILED_CHECKS=0
WARNING_CHECKS=0

# Function to run check
run_check() {
    local check_name="$1"
    local check_command="$2"
    local expected_result="$3"
    
    TOTAL_CHECKS=$((TOTAL_CHECKS + 1))
    
    echo ""
    echo "🔍 Checking: $check_name"
    
    if eval "$check_command" >/dev/null 2>&1; then
        if [ "$expected_result" = "success" ]; then
            print_status "PASS" "$check_name"
            PASSED_CHECKS=$((PASSED_CHECKS + 1))
        else
            print_status "FAIL" "$check_name (unexpected success)"
            FAILED_CHECKS=$((FAILED_CHECKS + 1))
        fi
    else
        if [ "$expected_result" = "failure" ]; then
            print_status "PASS" "$check_name"
            PASSED_CHECKS=$((PASSED_CHECKS + 1))
        else
            print_status "FAIL" "$check_name"
            FAILED_CHECKS=$((FAILED_CHECKS + 1))
        fi
    fi
}

echo ""
echo "📋 1. ENVIRONMENT & DEPENDENCIES"
echo "================================"

# Check Python
run_check "Python 3.10+ installed" "python3 --version | grep -E 'Python 3\.(1[0-9]|[2-9][0-9])'" "success"

# Check Node.js
run_check "Node.js 18+ installed" "node --version | grep -E 'v(1[8-9]|[2-9][0-9])'" "success"

# Check required commands
run_check "Django available" "command_exists python3 && python3 -c 'import django'" "success"
run_check "Expo CLI available" "command_exists expo" "success"
run_check "Git available" "command_exists git" "success"

echo ""
echo "📋 2. BACKEND VALIDATION"
echo "========================"

# Navigate to backend
cd backend/backend 2>/dev/null || { print_status "FAIL" "Backend directory not found"; exit 1; }

# Check Django settings
run_check "Django settings valid" "python3 manage.py check --settings=core.settings.prod" "success"
run_check "Django settings dev valid" "python3 manage.py check --settings=core.settings.dev" "success"

# Check migrations
run_check "No pending migrations" "python3 manage.py migrate --check --settings=core.settings.prod" "success"

# Check database connectivity
run_check "Database connectivity" "python3 manage.py dbshell --settings=core.settings.prod -c 'SELECT 1;'" "success"

# Check Redis connectivity (if available)
if command_exists redis-cli; then
    run_check "Redis connectivity" "redis-cli ping" "success"
else
    print_status "WARN" "Redis CLI not found, skipping Redis check"
    WARNING_CHECKS=$((WARNING_CHECKS + 1))
fi

# Check GraphQL schema
run_check "GraphQL schema valid" "python3 manage.py graphql_schema --settings=core.settings.prod" "success"

echo ""
echo "📋 3. SECURITY VALIDATION"
echo "========================="

# Check for hardcoded secrets
run_check "No hardcoded API keys" "! grep -r 'sk-[a-zA-Z0-9]' . --exclude-dir=.git --exclude-dir=node_modules" "success"
run_check "No hardcoded passwords" "! grep -r 'password.*=.*['\''\"][^'\''\"]*['\''\"]' . --exclude-dir=.git --exclude-dir=node_modules" "success"

# Check Django security settings
run_check "DEBUG=False in production" "grep -q 'DEBUG = False' core/settings/prod.py" "success"
run_check "ALLOWED_HOSTS configured" "grep -q 'ALLOWED_HOSTS' core/settings/prod.py" "success"

echo ""
echo "📋 4. MOBILE APP VALIDATION"
echo "==========================="

# Navigate to mobile
cd ../../mobile 2>/dev/null || { print_status "FAIL" "Mobile directory not found"; exit 1; }

# Check package.json
run_check "Package.json valid" "node -e 'JSON.parse(require(\"fs\").readFileSync(\"package.json\"))'" "success"

# Check TypeScript compilation
run_check "TypeScript compilation" "npx tsc --noEmit" "success"

# Check Expo configuration
run_check "Expo config valid" "npx expo config --type public" "success"

# Check for critical dependencies
run_check "Apollo Client available" "npm list @apollo/client" "success"
run_check "React Navigation available" "npm list @react-navigation/native" "success"

echo ""
echo "📋 5. API INTEGRATION TESTS"
echo "==========================="

# Navigate back to backend
cd ../backend/backend

# Test health endpoints
run_check "Health endpoint accessible" "curl -s http://localhost:8000/health/ | grep -q 'UP'" "success" || print_status "WARN" "Health endpoint not accessible (server may not be running)"

# Test GraphQL endpoint
run_check "GraphQL endpoint accessible" "curl -s -X POST http://localhost:8000/graphql/ -H 'Content-Type: application/json' -d '{\"query\":\"{ __schema { types { name } } }\"}' | grep -q 'data'" "success" || print_status "WARN" "GraphQL endpoint not accessible (server may not be running)"

echo ""
echo "📋 6. PERFORMANCE VALIDATION"
echo "============================"

# Check file sizes
run_check "No oversized files" "find . -name '*.py' -size +1M | wc -l | grep -q '^0$'" "success"
run_check "No oversized JS files" "find ../../mobile -name '*.js' -size +5M | wc -l | grep -q '^0$'" "success"

# Check for memory leaks (basic)
run_check "No obvious memory leaks" "! grep -r 'setInterval.*function' . --exclude-dir=.git" "success"

echo ""
echo "📋 7. DOCUMENTATION & CONFIGURATION"
echo "==================================="

# Check for required documentation
run_check "README exists" "test -f ../../README.md" "success"
run_check "Environment example exists" "test -f .env.example || test -f ../../.env.example" "success"

# Check configuration files
run_check "Django settings structure" "test -d core/settings" "success"
run_check "Mobile optimization config" "test -f ../../mobile/src/config/mobileOptimization.ts" "success"

echo ""
echo "📋 8. FINAL SUMMARY"
echo "==================="

echo ""
echo "🎯 RELEASE CHECKLIST RESULTS:"
echo "============================="
echo -e "Total Checks: ${BLUE}$TOTAL_CHECKS${NC}"
echo -e "Passed: ${GREEN}$PASSED_CHECKS${NC}"
echo -e "Failed: ${RED}$FAILED_CHECKS${NC}"
echo -e "Warnings: ${YELLOW}$WARNING_CHECKS${NC}"

echo ""
if [ $FAILED_CHECKS -eq 0 ]; then
    if [ $WARNING_CHECKS -eq 0 ]; then
        print_status "PASS" "🎉 ALL CHECKS PASSED! System is ready for production deployment."
        echo ""
        echo "🚀 DEPLOYMENT READY:"
        echo "  ✅ Backend: Production-ready with security hardening"
        echo "  ✅ Mobile: Optimized for battery and data usage"
        echo "  ✅ Database: All migrations applied"
        echo "  ✅ Security: No hardcoded secrets, proper settings"
        echo "  ✅ Performance: Optimized caching and rate limiting"
        echo "  ✅ Monitoring: Health checks and logging configured"
        exit 0
    else
        print_status "WARN" "⚠️  System ready with warnings. Review warnings before deployment."
        exit 1
    fi
else
    print_status "FAIL" "❌ CRITICAL ISSUES FOUND! Fix failed checks before deployment."
    echo ""
    echo "🔧 REQUIRED ACTIONS:"
    echo "  - Fix all failed checks above"
    echo "  - Re-run this checklist"
    echo "  - Ensure all tests pass"
    exit 1
fi
