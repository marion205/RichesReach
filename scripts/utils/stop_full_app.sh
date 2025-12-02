#!/bin/bash

# RichesReach Full Application Stop Script
# This script stops all running services

set -e

# Colors for output
RED='\033[0;31m'
YELLOW='\033[1;33m'
GREEN='\033[0;32m'
NC='\033[0m' # No Color

echo -e "${YELLOW}🛑 Stopping RichesReach Application Services${NC}"
echo "=================================================="
echo ""

# Stop Django servers
echo -e "${YELLOW}Stopping Django servers...${NC}"
pkill -f "manage.py runserver" 2>/dev/null && echo -e "${GREEN}✅ Django servers stopped${NC}" || echo -e "${YELLOW}⚠️  No Django servers found${NC}"

# Stop Expo/Metro bundler
echo -e "${YELLOW}Stopping Expo/Metro bundler...${NC}"
pkill -f "expo start" 2>/dev/null && echo -e "${GREEN}✅ Expo stopped${NC}" || echo -e "${YELLOW}⚠️  No Expo processes found${NC}"
pkill -f "metro" 2>/dev/null || true

# Stop Docker services
echo -e "${YELLOW}Stopping Docker services...${NC}"
if command -v docker-compose &> /dev/null || command -v docker &> /dev/null; then
    docker-compose down 2>/dev/null && echo -e "${GREEN}✅ Docker services stopped${NC}" || echo -e "${YELLOW}⚠️  No Docker services running${NC}"
else
    echo -e "${YELLOW}⚠️  Docker not installed${NC}"
fi

# Kill processes on specific ports
echo -e "${YELLOW}Cleaning up ports...${NC}"
lsof -ti:8000 | xargs kill -9 2>/dev/null && echo -e "${GREEN}✅ Port 8000 freed${NC}" || true
lsof -ti:8081 | xargs kill -9 2>/dev/null && echo -e "${GREEN}✅ Port 8081 freed${NC}" || true
lsof -ti:5432 | xargs kill -9 2>/dev/null || true
lsof -ti:6379 | xargs kill -9 2>/dev/null || true

echo ""
echo -e "${GREEN}✅ All services stopped!${NC}"

