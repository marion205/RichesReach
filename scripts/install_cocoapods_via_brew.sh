#!/usr/bin/env bash
# Install CocoaPods via Homebrew to bypass Ruby issues

set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}Installing CocoaPods via Homebrew...${NC}"
echo ""

# Check if CocoaPods is already installed via brew
if brew list cocoapods &>/dev/null; then
    echo -e "${GREEN}✅ CocoaPods already installed via Homebrew${NC}"
else
    echo -e "${BLUE}📦 Installing CocoaPods...${NC}"
    brew install cocoapods
    echo -e "${GREEN}✅ CocoaPods installed${NC}"
fi

echo ""
echo "CocoaPods version: $(pod --version 2>/dev/null || echo 'not working')"
echo ""
echo -e "${GREEN}✅ Ready to run 'pod install'${NC}"
echo ""

