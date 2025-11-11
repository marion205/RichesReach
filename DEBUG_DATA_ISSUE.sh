#!/bin/bash
# Comprehensive Debug Script for "No Usable Data Found" Issue

echo "🔍 RichesReach Data Loading Debug Script"
echo "=========================================="
echo ""

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${YELLOW}Step 1: Checking Environment Configuration${NC}"
echo "----------------------------------------"
cd /Users/marioncollins/RichesReach/mobile
if [ -f .env.local ]; then
    echo -e "${GREEN}✅ .env.local found:${NC}"
    cat .env.local
elif [ -f .env ]; then
    echo -e "${GREEN}✅ .env found:${NC}"
    cat .env
else
    echo -e "${RED}❌ No .env file found${NC}"
fi
echo ""

echo -e "${YELLOW}Step 2: Testing Backend Connectivity${NC}"
echo "----------------------------------------"
echo "Testing health endpoint..."
HEALTH_RESPONSE=$(curl -s http://192.168.1.240:8000/health/ --max-time 5)
if [ -n "$HEALTH_RESPONSE" ]; then
    echo -e "${GREEN}✅ Health endpoint responding:${NC}"
    echo "$HEALTH_RESPONSE"
else
    echo -e "${RED}❌ Health endpoint not responding${NC}"
fi
echo ""

echo "Testing GraphQL endpoint (no auth)..."
GQL_RESPONSE=$(curl -s -X POST http://192.168.1.240:8000/graphql/ \
  -H "Content-Type: application/json" \
  -d '{"query": "{ __typename }"}' --max-time 5)
if [ -n "$GQL_RESPONSE" ]; then
    echo -e "${GREEN}✅ GraphQL endpoint responding:${NC}"
    echo "$GQL_RESPONSE"
else
    echo -e "${RED}❌ GraphQL endpoint not responding${NC}"
fi
echo ""

echo "Testing GraphQL with GetMe query (no auth)..."
GQL_ME_RESPONSE=$(curl -s -X POST http://192.168.1.240:8000/graphql/ \
  -H "Content-Type: application/json" \
  -d '{"query": "{ me { id email name } }"}' --max-time 5)
if [ -n "$GQL_ME_RESPONSE" ]; then
    echo -e "${GREEN}✅ GetMe query response:${NC}"
    echo "$GQL_ME_RESPONSE"
else
    echo -e "${RED}❌ GetMe query failed${NC}"
fi
echo ""

echo -e "${YELLOW}Step 3: Checking Server Status${NC}"
echo "----------------------------------------"
if pgrep -f "main_server.py" > /dev/null; then
    echo -e "${GREEN}✅ Backend server is running${NC}"
    SERVER_PID=$(pgrep -f "main_server.py" | head -1)
    echo "   Process ID: $SERVER_PID"
else
    echo -e "${RED}❌ Backend server is NOT running${NC}"
fi
echo ""

if pgrep -f "expo start" > /dev/null; then
    echo -e "${GREEN}✅ Expo is running${NC}"
else
    echo -e "${YELLOW}⚠️  Expo is NOT running${NC}"
fi
echo ""

echo -e "${YELLOW}Step 4: Recent Server Logs${NC}"
echo "----------------------------------------"
if [ -f /tmp/richesreach_server.log ]; then
    echo "Last 10 lines from server log:"
    tail -10 /tmp/richesreach_server.log | grep -E "GET|POST|graphql|GraphQL|error|Error|192.168" || echo "No relevant logs found"
else
    echo -e "${YELLOW}⚠️  Server log file not found${NC}"
fi
echo ""

echo -e "${YELLOW}Step 5: Network Configuration${NC}"
echo "----------------------------------------"
echo "Mac IP Address:"
ifconfig | grep "inet " | grep -v 127.0.0.1 | head -1
echo ""

echo -e "${YELLOW}Step 6: Database Check${NC}"
echo "----------------------------------------"
cd /Users/marioncollins/RichesReach/deployment_package/backend
if [ -f db.sqlite3 ]; then
    USER_COUNT=$(sqlite3 db.sqlite3 "SELECT COUNT(*) FROM core_user;" 2>/dev/null)
    if [ -n "$USER_COUNT" ]; then
        echo -e "${GREEN}✅ Users in database: $USER_COUNT${NC}"
        echo "Sample users:"
        sqlite3 db.sqlite3 "SELECT email, name FROM core_user LIMIT 3;" 2>/dev/null || echo "Could not query users"
    else
        echo -e "${YELLOW}⚠️  Could not query database${NC}"
    fi
else
    echo -e "${YELLOW}⚠️  SQLite database not found${NC}"
fi
echo ""

echo -e "${YELLOW}Step 7: Next Steps${NC}"
echo "----------------------------------------"
echo "1. Scan QR code in Expo terminal"
echo "2. Watch Expo terminal for logs (especially [API_BASE], [GQL], 🔐)"
echo "3. Test from phone browser: http://192.168.1.240:8000/health/"
echo "4. Check if login screen appears in app"
echo "5. If logged in, check for token in AsyncStorage"
echo ""
echo -e "${GREEN}✅ Debug check complete!${NC}"
echo ""
echo "📋 Share the following with me:"
echo "   - Expo terminal logs after app loads"
echo "   - Phone browser test result"
echo "   - Whether login screen appears"
echo "   - Any error messages in app"

