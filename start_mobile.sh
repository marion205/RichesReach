#!/bin/bash

# Start React Native Mobile App Only
# This script starts just the Expo development server

set -e

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}📱 Starting React Native Mobile App${NC}"
echo "=================================================="
echo ""

# Get the script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
MOBILE_DIR="$SCRIPT_DIR/mobile"

if [ ! -d "$MOBILE_DIR" ]; then
    echo -e "${RED}❌ Mobile directory not found at $MOBILE_DIR${NC}"
    exit 1
fi

cd "$MOBILE_DIR"

# Check for package.json
if [ ! -f "package.json" ]; then
    echo -e "${RED}❌ package.json not found in mobile directory${NC}"
    exit 1
fi

# Check if node_modules exists
if [ ! -d "node_modules" ]; then
    echo -e "${YELLOW}⚠️  node_modules not found${NC}"
    echo "Installing dependencies..."
    npm install
    echo -e "${GREEN}✅ Dependencies installed${NC}"
fi

# Check if port 8081 is already in use
if lsof -Pi :8081 -sTCP:LISTEN -t >/dev/null 2>&1 ; then
    echo -e "${YELLOW}⚠️  Port 8081 is already in use${NC}"
    read -p "Kill existing process and continue? (y/n): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        lsof -ti:8081 | xargs kill -9 2>/dev/null || true
        sleep 2
    else
        echo "Exiting..."
        exit 1
    fi
fi

# Ask user how they want to start Expo
echo ""
echo -e "${BLUE}How would you like to start Expo?${NC}"
echo "  1) In this terminal (foreground - you'll see QR code here)"
echo "  2) In a new terminal window (separate window - recommended)"
echo ""
read -p "Enter choice (1 or 2, default: 2): " choice
choice=${choice:-2}

if [ "$choice" = "2" ]; then
    # Start in new terminal window (macOS)
    if [[ "$OSTYPE" == "darwin"* ]]; then
        echo -e "${GREEN}Opening Expo in new Terminal window...${NC}"
        osascript -e "tell application \"Terminal\"" \
                  -e "activate" \
                  -e "do script \"cd '$MOBILE_DIR' && clear && echo '🚀 Expo Metro Bundler' && echo '===================' && echo '' && npm start\"" \
                  -e "end tell"
        echo ""
        echo -e "${GREEN}✅ Expo is starting in a new Terminal window${NC}"
        echo -e "${YELLOW}Look for the new window with QR code and controls${NC}"
        echo ""
        echo -e "${BLUE}In that window you can:${NC}"
        echo "  • Press 'i' to open in iOS simulator"
        echo "  • Press 'a' to open in Android emulator"
        echo "  • Press 'w' to open in web browser"
        echo "  • Scan QR code with Expo Go app"
        echo "  • Press 'r' to reload"
        echo "  • Press Ctrl+C to stop"
    else
        echo -e "${YELLOW}New terminal option not available on this OS. Starting here...${NC}"
        choice=1
    fi
fi

if [ "$choice" = "1" ]; then
    # Start in current terminal
    echo -e "${GREEN}🚀 Starting Expo development server in this terminal...${NC}"
    echo ""
    echo -e "${BLUE}Tips:${NC}"
    echo "  • Press 'i' to open in iOS simulator"
    echo "  • Press 'a' to open in Android emulator"
    echo "  • Press 'w' to open in web browser"
    echo "  • Scan QR code with Expo Go app on your phone"
    echo "  • Press 'r' to reload the app"
    echo "  • Press Ctrl+C to stop"
    echo ""
    
    npm start
fi

