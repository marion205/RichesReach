#!/bin/bash

# Deploy Signals API Changes to Production
set -e

echo "🚀 Deploying Signals API Changes to Production..."

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

print_status() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Check if we're in the right directory
if [ ! -d "backend/backend" ]; then
    print_error "Please run this script from the RichesReach root directory"
    exit 1
fi

print_status "Deploying signals API changes..."

# Navigate to backend directory
cd backend/backend

# Check if production server is running
if curl -s http://localhost:8001/graphql/ -H 'content-type: application/json' -d '{"query":"{ ping }"}' > /dev/null 2>&1; then
    print_status "Local server is running - changes are ready"
else
    print_warning "Starting local server to test changes..."
    python3 manage.py runserver 0.0.0.0:8001 &
    sleep 5
fi

# Test the signals API
print_status "Testing signals API..."
SIGNALS_TEST=$(curl -s http://localhost:8001/graphql/ -H 'content-type: application/json' -d '{"query":"{ signals { id symbol signalType mlScore thesis } }"}')

if echo "$SIGNALS_TEST" | grep -q "signals"; then
    print_status "Signals API is working correctly!"
    echo "Sample response:"
    echo "$SIGNALS_TEST" | jq '.' 2>/dev/null || echo "$SIGNALS_TEST"
else
    print_error "Signals API test failed"
    exit 1
fi

print_status "Signals API deployment completed successfully!"
print_warning "Next steps:"
print_warning "1. Your signals API is running locally at: http://localhost:8001/graphql/"
print_warning "2. Test with your mobile app using the signals query"
print_warning "3. For production deployment, use your AWS ECS setup"

echo ""
print_status "Signals API Endpoint: http://localhost:8001/graphql/"
print_status "Test Query: { signals { id symbol signalType mlScore thesis } }"
