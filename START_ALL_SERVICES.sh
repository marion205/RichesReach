#!/bin/bash
# Start all backend services for RichesReach
# - main_server.py (FastAPI + Django WSGI) on port 8000
# - Django ASGI server (async AI endpoints) on port 8001

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}╔══════════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║  🚀 Starting All RichesReach Backend Services              ║${NC}"
echo -e "${GREEN}╚══════════════════════════════════════════════════════════════╝${NC}"
echo ""

# Kill existing processes on ports 8000 and 8001
echo -e "${YELLOW}Cleaning up existing processes...${NC}"
lsof -ti:8000 | xargs kill -9 2>/dev/null || true
lsof -ti:8001 | xargs kill -9 2>/dev/null || true
sleep 2

# Check for virtual environment
if [ -d "venv" ]; then
    source venv/bin/activate
    echo -e "${GREEN}✓ Virtual environment activated${NC}"
elif [ -d ".venv" ]; then
    source .venv/bin/activate
    echo -e "${GREEN}✓ Virtual environment activated${NC}"
fi

# Load OpenAI API key if available
if [ -f ".env.openai" ]; then
    export OPENAI_API_KEY=$(cat .env.openai)
    echo -e "${GREEN}✓ OpenAI API key loaded${NC}"
elif [ -n "$OPENAI_API_KEY" ]; then
    echo -e "${GREEN}✓ OpenAI API key found in environment${NC}"
else
    echo -e "${YELLOW}⚠️  OpenAI API key not found - some features may use fallback${NC}"
fi

echo ""
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}📡 Service 1: Main Server (FastAPI + Django WSGI)${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

# Start main_server.py on port 8000
if [ -f "main_server.py" ]; then
    echo "Starting main_server.py on port 8000..."
    python3 main_server.py > /tmp/main_server.log 2>&1 &
    MAIN_SERVER_PID=$!
    echo "Main server PID: $MAIN_SERVER_PID"
    
    # Wait for server to start
    for i in {1..10}; do
        if curl -s http://127.0.0.1:8000/health > /dev/null 2>&1; then
            echo -e "${GREEN}✓ Main server running at http://127.0.0.1:8000${NC}"
            break
        fi
        sleep 1
    done
else
    echo -e "${RED}❌ main_server.py not found${NC}"
    exit 1
fi

echo ""
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}📡 Service 2: Django ASGI Server (Async AI Endpoints)${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

# Start Django ASGI server on port 8001
if [ -d "deployment_package/backend" ]; then
    cd deployment_package/backend
    
    echo "Starting Django ASGI server on port 8001..."
    uvicorn richesreach.asgi:application --host 0.0.0.0 --port 8001 --workers 1 > /tmp/django_asgi.log 2>&1 &
    ASGI_SERVER_PID=$!
    echo "ASGI server PID: $ASGI_SERVER_PID"
    
    # Wait for server to start
    for i in {1..10}; do
        if curl -s http://127.0.0.1:8001/api/ai/health/ > /dev/null 2>&1; then
            echo -e "${GREEN}✓ ASGI server running at http://127.0.0.1:8001${NC}"
            break
        fi
        sleep 1
    done
    
    cd "$SCRIPT_DIR"
else
    echo -e "${YELLOW}⚠️  Django ASGI server directory not found, skipping${NC}"
fi

echo ""
echo -e "${GREEN}╔══════════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║  ✅ All Services Started!                                  ║${NC}"
echo -e "${GREEN}╚══════════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${GREEN}📡 Main Server (FastAPI + Django WSGI):${NC}"
echo "   http://127.0.0.1:8000"
echo "   • GraphQL: http://127.0.0.1:8000/graphql"
echo "   • Health: http://127.0.0.1:8000/health"
echo ""
echo -e "${GREEN}📡 Django ASGI Server (Async AI):${NC}"
echo "   http://127.0.0.1:8001"
echo "   • Health: http://127.0.0.1:8001/api/ai/health/"
echo "   • Chat: http://127.0.0.1:8001/api/ai/chat/"
echo "   • Stream: http://127.0.0.1:8001/api/ai/chat/stream/"
echo ""
echo -e "${YELLOW}📝 Logs:${NC}"
echo "   Main Server: tail -f /tmp/main_server.log"
echo "   ASGI Server: tail -f /tmp/django_asgi.log"
echo ""
echo -e "${YELLOW}🛑 To stop all services:${NC}"
echo "   pkill -f 'main_server.py|uvicorn richesreach.asgi'"
echo ""

