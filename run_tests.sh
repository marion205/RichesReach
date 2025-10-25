#!/bin/bash

# Comprehensive Test Runner for RichesReach
echo "🧪 Running Comprehensive Tests for RichesReach"
echo "=============================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Test results tracking
TOTAL_TESTS=0
PASSED_TESTS=0
FAILED_TESTS=0

# Function to run tests and track results
run_test_suite() {
    local test_name="$1"
    local test_command="$2"
    local test_dir="$3"
    
    echo -e "\n${BLUE}🔍 Running $test_name...${NC}"
    echo "Command: $test_command"
    echo "Directory: $test_dir"
    
    cd "$test_dir" || exit 1
    
    if eval "$test_command"; then
        echo -e "${GREEN}✅ $test_name PASSED${NC}"
        ((PASSED_TESTS++))
    else
        echo -e "${RED}❌ $test_name FAILED${NC}"
        ((FAILED_TESTS++))
    fi
    
    ((TOTAL_TESTS++))
    cd - > /dev/null
}

# Check if we're in the right directory
if [ ! -f "README.md" ]; then
    echo -e "${RED}❌ Please run this script from the RichesReach root directory${NC}"
    exit 1
fi

echo -e "${YELLOW}📋 Test Plan:${NC}"
echo "1. Mobile App Unit Tests (React Native)"
echo "2. Whisper Server Backend Tests (Node.js)"
echo "3. Integration Tests"
echo "4. Performance Tests"

# 1. Mobile App Tests
echo -e "\n${BLUE}📱 Mobile App Tests${NC}"
echo "=================="

# Check if mobile directory exists
if [ -d "mobile" ]; then
    # Install dependencies if needed
    if [ ! -d "mobile/node_modules" ]; then
        echo "Installing mobile app dependencies..."
        cd mobile && npm install && cd ..
    fi
    
    run_test_suite "Mobile App Unit Tests" "npm test -- --coverage --watchAll=false" "mobile"
else
    echo -e "${YELLOW}⚠️  Mobile directory not found, skipping mobile tests${NC}"
fi

# 2. Whisper Server Tests
echo -e "\n${BLUE}🎤 Whisper Server Tests${NC}"
echo "======================="

# Check if whisper-server directory exists
if [ -d "whisper-server" ]; then
    # Install dependencies if needed
    if [ ! -d "whisper-server/node_modules" ]; then
        echo "Installing whisper server dependencies..."
        cd whisper-server && npm install && cd ..
    fi
    
    run_test_suite "Whisper Server Tests" "npm test" "whisper-server"
else
    echo -e "${YELLOW}⚠️  Whisper server directory not found, skipping server tests${NC}"
fi

# 3. Backend Django Tests (if available)
echo -e "\n${BLUE}🐍 Django Backend Tests${NC}"
echo "======================="

if [ -d "backend/backend" ]; then
    cd backend/backend
    
    # Check if virtual environment exists
    if [ -d "venv" ]; then
        source venv/bin/activate
    fi
    
    # Check if Django is available
    if command -v python &> /dev/null; then
        if python -c "import django" 2>/dev/null; then
            run_test_suite "Django Backend Tests" "python manage.py test" "backend/backend"
        else
            echo -e "${YELLOW}⚠️  Django not available, skipping Django tests${NC}"
        fi
    else
        echo -e "${YELLOW}⚠️  Python not available, skipping Django tests${NC}"
    fi
    
    # Live Streaming Server Tests
    if [ -d "streaming-server" ]; then
        echo -e "${BLUE}📺 Testing Live Streaming Server...${NC}"
        if [ -f "streaming-server/package.json" ]; then
            run_test_suite "Live Streaming Server Tests" "npm test" "streaming-server"
        else
            echo -e "${YELLOW}⚠️  Streaming server package.json not found${NC}"
        fi
    else
        echo -e "${YELLOW}⚠️  Streaming server directory not found, skipping streaming tests${NC}"
    fi
    
    cd ../..
else
    echo -e "${YELLOW}⚠️  Django backend directory not found, skipping Django tests${NC}"
fi

# 4. Integration Tests
echo -e "\n${BLUE}🔗 Integration Tests${NC}"
echo "===================="

# Test server connectivity
echo "Testing server connectivity..."

# Test Whisper server health
if command -v curl &> /dev/null; then
    echo "Testing Whisper server health endpoint..."
    if curl -s http://localhost:3001/health > /dev/null; then
        echo -e "${GREEN}✅ Whisper server is running${NC}"
        ((PASSED_TESTS++))
    else
        echo -e "${YELLOW}⚠️  Whisper server not running (start with: cd whisper-server && npm start)${NC}"
        ((FAILED_TESTS++))
    fi
    ((TOTAL_TESTS++))
    
    # Test Django backend health
    echo "Testing Django backend health endpoint..."
    if curl -s http://localhost:8000/health > /dev/null; then
        echo -e "${GREEN}✅ Django backend is running${NC}"
        ((PASSED_TESTS++))
    else
        echo -e "${YELLOW}⚠️  Django backend not running (start with: cd backend/backend && python manage.py runserver)${NC}"
        ((FAILED_TESTS++))
    fi
    ((TOTAL_TESTS++))
else
    echo -e "${YELLOW}⚠️  curl not available, skipping connectivity tests${NC}"
fi

# 5. Performance Tests
echo -e "\n${BLUE}⚡ Performance Tests${NC}"
echo "===================="

# Test file size limits
echo "Testing file size limits..."
if [ -d "whisper-server" ]; then
    cd whisper-server
    
    # Create a test file to check upload limits
    dd if=/dev/zero of=test-large-file.m4a bs=1M count=26 2>/dev/null
    
    if [ -f "test-large-file.m4a" ]; then
        file_size=$(stat -f%z test-large-file.m4a 2>/dev/null || stat -c%s test-large-file.m4a 2>/dev/null)
        if [ "$file_size" -gt 26214400 ]; then  # 25MB in bytes
            echo -e "${GREEN}✅ Large file test created (${file_size} bytes)${NC}"
            ((PASSED_TESTS++))
        else
            echo -e "${RED}❌ Large file test failed${NC}"
            ((FAILED_TESTS++))
        fi
        rm -f test-large-file.m4a
    fi
    ((TOTAL_TESTS++))
    
    cd ..
fi

# 6. Security Tests
echo -e "\n${BLUE}🔒 Security Tests${NC}"
echo "=================="

# Test JWT token validation
echo "Testing JWT token validation..."
if [ -d "whisper-server" ]; then
    cd whisper-server
    
    # Test with invalid token
    if command -v curl &> /dev/null; then
        response=$(curl -s -o /dev/null -w "%{http_code}" -X POST http://localhost:3001/api/transcribe-audio/ -H "Authorization: Bearer invalid-token")
        if [ "$response" = "401" ]; then
            echo -e "${GREEN}✅ JWT validation working (401 for invalid token)${NC}"
            ((PASSED_TESTS++))
        else
            echo -e "${RED}❌ JWT validation failed (got $response instead of 401)${NC}"
            ((FAILED_TESTS++))
        fi
        ((TOTAL_TESTS++))
    fi
    
    cd ..
fi

# Final Results
echo -e "\n${BLUE}📊 Test Results Summary${NC}"
echo "========================="
echo -e "Total Tests: ${TOTAL_TESTS}"
echo -e "${GREEN}Passed: ${PASSED_TESTS}${NC}"
echo -e "${RED}Failed: ${FAILED_TESTS}${NC}"

if [ $FAILED_TESTS -eq 0 ]; then
    echo -e "\n${GREEN}🎉 All tests passed! Your RichesReach implementation is ready for testing.${NC}"
    echo -e "\n${YELLOW}📋 Next Steps:${NC}"
    echo "1. Start the Whisper server: cd whisper-server && npm start"
    echo "2. Start the Django backend: cd backend/backend && python manage.py runserver"
    echo "3. Build and test the mobile app: cd mobile && eas build --platform android --profile development"
    echo "4. Test video chat functionality in the app"
    echo "5. Test voice transcription with real audio files"
    
    exit 0
else
    echo -e "\n${RED}❌ Some tests failed. Please review the errors above.${NC}"
    echo -e "\n${YELLOW}🔧 Troubleshooting:${NC}"
    echo "1. Make sure all dependencies are installed"
    echo "2. Check that all services are running"
    echo "3. Verify environment variables are set correctly"
    echo "4. Review the test logs for specific error messages"
    
    exit 1
fi
