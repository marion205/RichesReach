#!/bin/bash
# Check all RichesReach backend services are running

set -e

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${BLUE}╔══════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║  🔍 Checking RichesReach Backend Services                  ║${NC}"
echo -e "${BLUE}╚══════════════════════════════════════════════════════════════╝${NC}"
echo ""

# Function to check if port is in use
check_port() {
    lsof -Pi :$1 -sTCP:LISTEN -t >/dev/null 2>&1
}

# Function to check HTTP endpoint
check_http() {
    local url=$1
    local service=$2
    local timeout=${3:-5}
    
    if curl -s --max-time $timeout "$url" >/dev/null 2>&1; then
        return 0
    else
        return 1
    fi
}

# Function to check service
check_service() {
    local name=$1
    local port=$2
    local health_url=$3
    local required=${4:-true}
    
    echo -n "Checking $name (port $port)... "
    
    if check_port $port; then
        if [ -n "$health_url" ]; then
            if check_http "$health_url" "$name"; then
                echo -e "${GREEN}✅ RUNNING${NC}"
                return 0
            else
                echo -e "${YELLOW}⚠️  PORT OPEN BUT HEALTH CHECK FAILED${NC}"
                return 1
            fi
        else
            echo -e "${GREEN}✅ RUNNING (port open)${NC}"
            return 0
        fi
    else
        if [ "$required" = "true" ]; then
            echo -e "${RED}❌ NOT RUNNING${NC}"
        else
            echo -e "${YELLOW}⚠️  NOT RUNNING (optional)${NC}"
        fi
        return 1
    fi
}

# Track results
ALL_RUNNING=true
REQUIRED_SERVICES=0
RUNNING_SERVICES=0

echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}📡 Required Services${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

# 1. Main Server (GraphQL endpoint)
REQUIRED_SERVICES=$((REQUIRED_SERVICES + 1))
if check_service "Main Server (GraphQL)" 8000 "http://127.0.0.1:8000/health"; then
    RUNNING_SERVICES=$((RUNNING_SERVICES + 1))
    echo "   GraphQL: http://127.0.0.1:8000/graphql"
else
    ALL_RUNNING=false
    echo "   ${RED}❌ GraphQL endpoint not available${NC}"
fi

# 2. Django ASGI Server (Async AI)
REQUIRED_SERVICES=$((REQUIRED_SERVICES + 1))
if check_service "Django ASGI Server" 8001 "http://127.0.0.1:8001/api/ai/health/"; then
    RUNNING_SERVICES=$((RUNNING_SERVICES + 1))
    echo "   Chat API: http://127.0.0.1:8001/api/ai/chat/"
else
    ALL_RUNNING=false
    echo "   ${YELLOW}⚠️  Async AI features may not work${NC}"
fi

# 3. PostgreSQL Database
REQUIRED_SERVICES=$((REQUIRED_SERVICES + 1))
if check_port 5432; then
    RUNNING_SERVICES=$((RUNNING_SERVICES + 1))
    echo -e "PostgreSQL (port 5432)... ${GREEN}✅ RUNNING${NC}"
else
    ALL_RUNNING=false
    echo -e "PostgreSQL (port 5432)... ${RED}❌ NOT RUNNING${NC}"
    echo "   ${YELLOW}💡 Start with: docker-compose up -d db${NC}"
fi

# 4. Redis Cache
REQUIRED_SERVICES=$((REQUIRED_SERVICES + 1))
if check_port 6379; then
    RUNNING_SERVICES=$((RUNNING_SERVICES + 1))
    echo -e "Redis (port 6379)... ${GREEN}✅ RUNNING${NC}"
else
    ALL_RUNNING=false
    echo -e "Redis (port 6379)... ${RED}❌ NOT RUNNING${NC}"
    echo "   ${YELLOW}💡 Start with: docker-compose up -d redis${NC}"
fi

echo ""
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}🔧 Optional Services${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

# 5. Rust Crypto Engine
check_service "Rust Crypto Engine" 3001 "http://127.0.0.1:3001/health/live" false
if [ $? -eq 0 ]; then
    RUNNING_SERVICES=$((RUNNING_SERVICES + 1))
fi

# 6. TTS Service
check_service "TTS Service" 8002 "http://127.0.0.1:8002/health" false
if [ $? -eq 0 ]; then
    RUNNING_SERVICES=$((RUNNING_SERVICES + 1))
fi

# 7. Whisper Server
check_service "Whisper Server" 3003 "" false
if [ $? -eq 0 ]; then
    RUNNING_SERVICES=$((RUNNING_SERVICES + 1))
fi

echo ""
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}📊 Summary${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

echo "Required services: $RUNNING_SERVICES/$REQUIRED_SERVICES running"

if [ "$ALL_RUNNING" = true ]; then
    echo -e "${GREEN}✅ All required services are running!${NC}"
    echo ""
    echo -e "${GREEN}📡 Service Endpoints:${NC}"
    echo "   • GraphQL: http://127.0.0.1:8000/graphql"
    echo "   • Health: http://127.0.0.1:8000/health"
    echo "   • AI Chat: http://127.0.0.1:8001/api/ai/chat/"
    exit 0
else
    echo -e "${RED}❌ Some required services are not running!${NC}"
    echo ""
    echo -e "${YELLOW}💡 To start all services, run:${NC}"
    echo "   ./start_all_backend_services.sh"
    echo ""
    echo -e "${YELLOW}💡 Or start individual services:${NC}"
    echo "   • Main Server: python3 main_server.py"
    echo "   • ASGI Server: cd deployment_package/backend && uvicorn richesreach.asgi:application --port 8001"
    echo "   • Database: docker-compose up -d db redis"
    exit 1
fi

