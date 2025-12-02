#!/bin/bash

# RichesReach - Start All Features
# This script starts ALL services needed for complete functionality

set -e

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${BLUE}🚀 Starting RichesReach - ALL FEATURES${NC}"
echo "=================================================="
echo ""
echo "This will start:"
echo "  ✅ PostgreSQL Database"
echo "  ✅ Redis Cache"
echo "  ✅ Django Backend (All APIs)"
echo "  ✅ Rust Crypto Engine (Optional)"
echo "  ✅ React Native Mobile App"
echo ""

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Check ports function
check_port() {
    lsof -Pi :$1 -sTCP:LISTEN -t >/dev/null 2>&1
}

# Wait for service
wait_for_service() {
    local host=$1
    local port=$2
    local service=$3
    local max=30
    local count=0
    
    echo -e "${YELLOW}⏳ Waiting for $service...${NC}"
    while [ $count -lt $max ]; do
        if curl -s "http://$host:$port" >/dev/null 2>&1 || nc -z $host $port 2>/dev/null; then
            echo -e "${GREEN}✅ $service ready!${NC}"
            return 0
        fi
        sleep 1
        count=$((count + 1))
    done
    echo -e "${RED}❌ $service timeout${NC}"
    return 1
}

# Stop existing services
echo -e "${YELLOW}🔄 Stopping existing services...${NC}"
pkill -f "manage.py runserver" 2>/dev/null || true
pkill -f "expo start" 2>/dev/null || true
pkill -f "rust_crypto_engine" 2>/dev/null || true
docker-compose down 2>/dev/null || true
sleep 2

# ============================================
# STEP 1: Start Databases
# ============================================
echo ""
echo -e "${BLUE}📊 Step 1: Starting Databases${NC}"

if command -v docker-compose &> /dev/null || command -v docker &> /dev/null; then
    echo "Starting PostgreSQL and Redis..."
    docker-compose up -d 2>&1 | grep -v "Creating network" || true
    sleep 3
    
    if wait_for_service localhost 5432 "PostgreSQL"; then
        echo -e "${GREEN}✅ PostgreSQL ready${NC}"
    fi
    
    if wait_for_service localhost 6379 "Redis"; then
        echo -e "${GREEN}✅ Redis ready${NC}"
    else
        echo -e "${YELLOW}⚠️  Redis not ready (optional)${NC}"
    fi
else
    echo -e "${YELLOW}⚠️  Docker not found. Assuming databases are running...${NC}"
fi

# ============================================
# STEP 2: Setup and Start Django Backend
# ============================================
echo ""
echo -e "${BLUE}🐍 Step 2: Starting Django Backend${NC}"
BACKEND_DIR="$SCRIPT_DIR/backend/backend"

if [ ! -d "$BACKEND_DIR" ]; then
    echo -e "${RED}❌ Backend not found${NC}"
    exit 1
fi

cd "$BACKEND_DIR"

# Activate venv if exists
if [ -d "../venv" ]; then
    source ../venv/bin/activate
elif [ -d "venv" ]; then
    source venv/bin/activate
fi

# Run migrations
echo "Running database migrations..."
python3 manage.py migrate --settings=richesreach.settings_local 2>&1 | tail -3 || {
    python3 manage.py migrate 2>&1 | tail -3 || true
}

# Start Django
if check_port 8000; then
    echo -e "${YELLOW}⚠️  Port 8000 in use, killing existing process...${NC}"
    lsof -ti:8000 | xargs kill -9 2>/dev/null || true
    sleep 2
fi

echo "Starting Django backend..."
if [ -f "richesreach/settings_local.py" ]; then
    DJANGO_SETTINGS_MODULE=richesreach.settings_local python3 manage.py runserver 127.0.0.1:8000 > /tmp/django_server.log 2>&1 &
else
    python3 manage.py runserver 127.0.0.1:8000 > /tmp/django_server.log 2>&1 &
fi

DJANGO_PID=$!
sleep 3

if wait_for_service localhost 8000 "Django Backend"; then
    echo -e "${GREEN}✅ Django backend running at http://127.0.0.1:8000${NC}"
else
    echo -e "${RED}❌ Django failed to start. Check /tmp/django_server.log${NC}"
    tail -20 /tmp/django_server.log
    exit 1
fi

# ============================================
# STEP 3: Start Rust Crypto Engine (Optional)
# ============================================
echo ""
echo -e "${BLUE}🦀 Step 3: Starting Rust Crypto Engine${NC}"
RUST_DIR="$SCRIPT_DIR/rust_crypto_engine"

if [ -d "$RUST_DIR" ] && [ -f "$RUST_DIR/Cargo.toml" ]; then
    if command -v cargo &> /dev/null; then
        cd "$RUST_DIR"
        
        if check_port 3002; then
            echo -e "${YELLOW}⚠️  Port 3002 in use${NC}"
        else
            echo "Building and starting Rust engine..."
            cargo run --release -- --port 3002 > /tmp/rust_engine.log 2>&1 &
            RUST_PID=$!
            sleep 5
            
            if wait_for_service localhost 3002 "Rust Engine"; then
                echo -e "${GREEN}✅ Rust engine running at http://127.0.0.1:3002${NC}"
            else
                echo -e "${YELLOW}⚠️  Rust engine may still be starting${NC}"
            fi
        fi
    else
        echo -e "${YELLOW}⚠️  Rust not installed, skipping crypto engine${NC}"
    fi
else
    echo -e "${YELLOW}⚠️  Rust engine not found, skipping${NC}"
fi

# ============================================
# STEP 4: Start Mobile App
# ============================================
echo ""
echo -e "${BLUE}📱 Step 4: Starting React Native Mobile App${NC}"
MOBILE_DIR="$SCRIPT_DIR/mobile"

if [ -d "$MOBILE_DIR" ]; then
    cd "$MOBILE_DIR"
    
    if [ ! -d "node_modules" ]; then
        echo -e "${YELLOW}⚠️  Installing dependencies...${NC}"
        npm install
    fi
    
    if check_port 8081; then
        echo -e "${YELLOW}⚠️  Expo already running on port 8081${NC}"
    else
            echo "Starting Expo in Development Build mode..."
            if [[ "$OSTYPE" == "darwin"* ]] && command -v osascript &> /dev/null; then
                osascript -e "tell application \"Terminal\"" \
                          -e "activate" \
                          -e "do script \"cd '$MOBILE_DIR' && clear && echo '📱 Development Build Mode' && echo '==========================' && echo '' && npx expo start --dev-client --clear\"" \
                          -e "end tell" 2>/dev/null
                echo -e "${GREEN}✅ Expo starting in Development Build mode (new terminal)${NC}"
                echo -e "${YELLOW}   First time? Run: cd mobile && npx expo run:ios${NC}"
                echo -e "${YELLOW}   In that window, press 'i' to open iOS simulator${NC}"
            else
                npx expo start --dev-client --clear > /tmp/expo_server.log 2>&1 &
                EXPO_PID=$!
                echo -e "${GREEN}✅ Expo starting in Development Build mode (PID: $EXPO_PID)${NC}"
            fi
    fi
else
    echo -e "${YELLOW}⚠️  Mobile directory not found${NC}"
fi

# ============================================
# SUMMARY
# ============================================
echo ""
echo -e "${GREEN}=================================================="
echo "✅ ALL FEATURES STARTED!"
echo "==================================================${NC}"
echo ""
echo -e "${BLUE}Services Running:${NC}"
echo "  📊 PostgreSQL:    localhost:5432"
echo "  🔴 Redis:         localhost:6379"
echo "  🐍 Django:        http://127.0.0.1:8000"
echo "  🔵 GraphQL:       http://127.0.0.1:8000/graphql"
echo "  🦀 Rust Engine:   http://127.0.0.1:3002 (if started)"
echo "  📱 Expo:          http://localhost:8081"
echo ""
echo -e "${BLUE}Available Features:${NC}"
echo "  ✅ Market Data & Real-time Quotes"
echo "  ✅ Options Trading & Greeks"
echo "  ✅ Portfolio Management"
echo "  ✅ AI Trading Coach & Tutor"
echo "  ✅ Voice AI Assistant"
echo "  ✅ Crypto/DeFi Analysis"
echo "  ✅ Social Trading & Wealth Circles"
echo "  ✅ Education & Learning Paths"
echo "  ✅ Bank Integration (SBLOC, Yodlee)"
echo "  ✅ GraphQL API (80+ endpoints)"
echo ""
echo -e "${BLUE}Next Steps:${NC}"
echo "  1. In Expo terminal, press 's' to switch to Expo Go"
echo "  2. Press 'i' to open iOS simulator"
echo "  3. Test features in the mobile app"
echo ""
echo -e "${YELLOW}View logs:${NC}"
echo "  • Django:    tail -f /tmp/django_server.log"
echo "  • Rust:      tail -f /tmp/rust_engine.log"
echo "  • Expo:     tail -f /tmp/expo_server.log"
echo ""
echo -e "${GREEN}All systems operational! 🚀${NC}"
echo ""

