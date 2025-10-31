#!/bin/bash

# RichesReach Full Application Startup Script
# This script starts all services needed for comprehensive testing

set -e

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}🚀 Starting RichesReach Full Application for Testing${NC}"
echo "=================================================="
echo ""

# Get the script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Function to check if a port is in use
check_port() {
    if lsof -Pi :$1 -sTCP:LISTEN -t >/dev/null 2>&1 ; then
        return 0  # Port is in use
    else
        return 1  # Port is free
    fi
}

# Function to wait for a service
wait_for_service() {
    local host=$1
    local port=$2
    local service_name=$3
    local max_attempts=30
    local attempt=1
    
    echo -e "${YELLOW}⏳ Waiting for $service_name to be ready...${NC}"
    while [ $attempt -le $max_attempts ]; do
        # Try different methods to check port
        if command -v nc &> /dev/null && nc -z $host $port 2>/dev/null; then
            echo -e "${GREEN}✅ $service_name is ready!${NC}"
            return 0
        elif timeout 1 bash -c "echo > /dev/tcp/$host/$port" 2>/dev/null; then
            echo -e "${GREEN}✅ $service_name is ready!${NC}"
            return 0
        elif curl -s "http://$host:$port" > /dev/null 2>&1; then
            echo -e "${GREEN}✅ $service_name is ready!${NC}"
            return 0
        fi
        sleep 1
        attempt=$((attempt + 1))
    done
    echo -e "${RED}❌ $service_name failed to start after $max_attempts seconds${NC}"
    return 1
}

# Stop any existing services
echo -e "${YELLOW}🔄 Stopping any existing services...${NC}"
pkill -f "manage.py runserver" 2>/dev/null || true
pkill -f "expo start" 2>/dev/null || true
docker-compose down 2>/dev/null || true
sleep 2

# Step 1: Start PostgreSQL Database
echo ""
echo -e "${BLUE}📊 Step 1: Starting PostgreSQL Database${NC}"
if command -v docker-compose &> /dev/null || command -v docker &> /dev/null; then
    echo "Starting PostgreSQL with Docker Compose..."
    docker-compose up -d db 2>&1 | grep -v "Creating network" || true
    
    if wait_for_service localhost 5432 "PostgreSQL"; then
        echo -e "${GREEN}✅ Database is ready!${NC}"
    else
        echo -e "${RED}❌ Failed to start database${NC}"
        exit 1
    fi
else
    echo -e "${YELLOW}⚠️  Docker not found. Assuming PostgreSQL is already running...${NC}"
fi

# Step 2: Check for Redis (optional but recommended)
echo ""
echo -e "${BLUE}🔴 Step 2: Checking Redis${NC}"
if check_port 6379; then
    echo -e "${GREEN}✅ Redis is already running on port 6379${NC}"
else
    echo -e "${YELLOW}⚠️  Redis not running. Starting Redis with Docker...${NC}"
    docker-compose up -d redis 2>/dev/null || echo -e "${YELLOW}⚠️  Redis container not defined, continuing without Redis...${NC}"
fi

# Step 3: Setup Django Backend
echo ""
echo -e "${BLUE}🐍 Step 3: Setting up Django Backend${NC}"
BACKEND_DIR="$SCRIPT_DIR/backend/backend"

if [ ! -d "$BACKEND_DIR" ]; then
    echo -e "${RED}❌ Backend directory not found at $BACKEND_DIR${NC}"
    exit 1
fi

cd "$BACKEND_DIR"

# Check for virtual environment
if [ -d "../venv" ]; then
    echo "Activating virtual environment..."
    source ../venv/bin/activate
elif [ -d "venv" ]; then
    echo "Activating virtual environment..."
    source venv/bin/activate
else
    echo -e "${YELLOW}⚠️  No virtual environment found. Using system Python...${NC}"
fi

# Check if manage.py exists
if [ ! -f "manage.py" ]; then
    echo -e "${RED}❌ manage.py not found in $BACKEND_DIR${NC}"
    exit 1
fi

# Run migrations
echo "Running database migrations..."
python3 manage.py migrate --settings=richesreach.settings_local 2>&1 | tail -5 || {
    echo -e "${YELLOW}⚠️  Migration failed or settings_local not found, trying default settings...${NC}"
    python3 manage.py migrate 2>&1 | tail -5 || true
}

# Step 4: Start Django Server
echo ""
echo -e "${BLUE}🚀 Step 4: Starting Django Backend Server${NC}"
if check_port 8000; then
    echo -e "${YELLOW}⚠️  Port 8000 is already in use${NC}"
    read -p "Kill existing process and continue? (y/n): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        lsof -ti:8000 | xargs kill -9 2>/dev/null || true
        sleep 2
    else
        echo "Skipping Django server startup..."
    fi
fi

# Start Django in background
echo "Starting Django server on http://127.0.0.1:8000..."
if [ -f "richesreach/settings_local.py" ]; then
    DJANGO_SETTINGS_MODULE=richesreach.settings_local python3 manage.py runserver 127.0.0.1:8000 > /tmp/django_server.log 2>&1 &
else
    python3 manage.py runserver 127.0.0.1:8000 > /tmp/django_server.log 2>&1 &
fi

DJANGO_PID=$!
echo "Django server started with PID: $DJANGO_PID"

# Wait for Django to be ready
sleep 3
if wait_for_service localhost 8000 "Django Backend"; then
    echo -e "${GREEN}✅ Django backend is ready at http://127.0.0.1:8000${NC}"
    echo -e "${GREEN}   GraphQL endpoint: http://127.0.0.1:8000/graphql${NC}"
else
    echo -e "${RED}❌ Django backend failed to start. Check /tmp/django_server.log for details${NC}"
    tail -20 /tmp/django_server.log
    exit 1
fi

# Step 5: Start Mobile App
echo ""
echo -e "${BLUE}📱 Step 5: Starting React Native Mobile App${NC}"
MOBILE_DIR="$SCRIPT_DIR/mobile"
EXPO_PID=""

if [ -d "$MOBILE_DIR" ]; then
    if check_port 8081; then
        echo -e "${YELLOW}⚠️  Expo Metro bundler already running on port 8081${NC}"
        echo -e "${GREEN}✅ Mobile app server already active${NC}"
    else
        cd "$MOBILE_DIR"
        if [ -f "package.json" ]; then
            # Check if node_modules exists
            if [ ! -d "node_modules" ]; then
                echo -e "${YELLOW}⚠️  node_modules not found. Installing dependencies...${NC}"
                read -p "Install npm dependencies now? (y/n): " -n 1 -r
                echo
                if [[ $REPLY =~ ^[Yy]$ ]]; then
                    echo "Installing dependencies (this may take a few minutes)..."
                    npm install
                    echo -e "${GREEN}✅ Dependencies installed${NC}"
                else
                    echo -e "${YELLOW}⚠️  Skipping mobile app startup. Install dependencies first: cd mobile && npm install${NC}"
                fi
            fi
            
            # Start Expo if dependencies are installed
            if [ -d "node_modules" ]; then
                echo "Starting Expo development server (dev-client mode)..."
                echo -e "${YELLOW}📱 Opening Expo in new terminal window...${NC}"
                echo -e "${YELLOW}   ⚠️  First time? Build dev client: cd mobile && npx expo run:ios${NC}"
                echo -e "${YELLOW}   Then you can press 'i' for iOS simulator${NC}"
                
                # Always try to start in a new terminal window (macOS)
                if [[ "$OSTYPE" == "darwin"* ]] && command -v osascript &> /dev/null; then
                    # Use a more reliable method to open new terminal with Expo
                    osascript -e "tell application \"Terminal\"" -e "activate" -e "do script \"cd '$MOBILE_DIR' && echo '🚀 Starting Expo Metro Bundler...' && npm start\"" -e "end tell" 2>/dev/null
                    
                    # Give it a moment to start
                    sleep 3
                    
                    # Check if it's actually running
                    if check_port 8081; then
                        echo -e "${GREEN}✅ Expo server started in new terminal window${NC}"
                        echo -e "${GREEN}   Look for the terminal window with QR code and Metro bundler interface${NC}"
                        echo -e "${GREEN}   You can press 'i' for iOS simulator or 'a' for Android emulator${NC}"
                    else
                        echo -e "${YELLOW}⚠️  Expo may be starting. Check the new terminal window${NC}"
                        echo -e "${YELLOW}   If no new window appeared, run: cd mobile && npm start${NC}"
                    fi
                else
                    # Fallback: provide clear instructions
                    echo -e "${YELLOW}⚠️  Cannot open new terminal automatically${NC}"
                    echo -e "${BLUE}Please run in a separate terminal:${NC}"
                    echo -e "${BLUE}  cd $MOBILE_DIR${NC}"
                    echo -e "${BLUE}  npm start${NC}"
                    echo ""
                    read -p "Press Enter to continue (you can start Expo manually later)..."
                fi
            fi
        else
            echo -e "${YELLOW}⚠️  package.json not found in mobile directory${NC}"
        fi
    fi
else
    echo -e "${YELLOW}⚠️  Mobile directory not found, skipping mobile app${NC}"
fi

# Summary
echo ""
echo -e "${GREEN}=================================================="
echo "✅ RichesReach Application Started Successfully!"
echo "==================================================${NC}"
echo ""
echo -e "${BLUE}Services Running:${NC}"
echo "  📊 Database:     localhost:5432 (PostgreSQL)"
echo "  🔴 Redis:        localhost:6379 (if started)"
echo "  🐍 Backend:      http://127.0.0.1:8000"
echo "  🔵 GraphQL:      http://127.0.0.1:8000/graphql"
echo "  📱 Mobile:       http://localhost:8081 (Expo Metro Bundler)"
echo ""
echo -e "${BLUE}Useful Commands:${NC}"
echo "  • View Django logs:    tail -f /tmp/django_server.log"
echo "  • View Expo logs:      tail -f /tmp/expo_server.log"
echo "  • Stop Django:         kill $DJANGO_PID"
if [ ! -z "$EXPO_PID" ]; then
    echo "  • Stop Expo:           kill $EXPO_PID"
fi
echo "  • Stop all services:   ./stop_full_app.sh"
echo "  • Test endpoints:      curl http://127.0.0.1:8000/health/"
echo "  • Scan QR code:        Open Expo Go app and scan QR code from terminal"
echo ""
echo -e "${YELLOW}Press Ctrl+C to stop all services${NC}"
echo ""

# Keep script running and handle cleanup on exit
cleanup() {
    echo ''
    echo -e "${YELLOW}🛑 Stopping services...${NC}"
    kill $DJANGO_PID 2>/dev/null || true
    if [ ! -z "$EXPO_PID" ]; then
        kill $EXPO_PID 2>/dev/null || true
    fi
    pkill -f "expo start" 2>/dev/null || true
    docker-compose down 2>/dev/null || true
    exit
}

trap cleanup INT TERM

# Wait for user interrupt
wait $DJANGO_PID 2>/dev/null || sleep infinity

