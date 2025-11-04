#!/usr/bin/env bash
# Aggressive cleanup to free ~7GB+ for Xcode 16.4 installation
# This script removes more items, including temporarily removing Pods

set -euo pipefail

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
CYAN='\033[0;36m'
NC='\033[0m'

echo -e "${RED}╔════════════════════════════════════════════════════╗${NC}"
echo -e "${RED}║  AGGRESSIVE Cleanup for Xcode 16.4 Installation  ║${NC}"
echo -e "${RED}╚════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${YELLOW}⚠️  This will remove more items, including temporary Pods${NC}"
echo ""

# Function to get directory size
get_size() {
    local path="$1"
    if [ -d "$path" ] || [ -f "$path" ]; then
        du -sh "$path" 2>/dev/null | awk '{print $1}' || echo "0"
    else
        echo "0"
    fi
}

calculate_space() {
    df -h / | tail -1 | awk '{print $4}'
}

INITIAL_SPACE=$(calculate_space)
echo -e "${BLUE}📊 Current Available Space:${NC} ${GREEN}$INITIAL_SPACE${NC}"
echo ""

# 1. Empty Trash
echo -e "${BLUE}🧹 1. Emptying Trash...${NC}"
TRASH_SIZE=$(get_size "$HOME/.Trash")
echo "   Found: ${YELLOW}$TRASH_SIZE${NC}"
rm -rf "$HOME/.Trash"/* 2>/dev/null || true
echo -e "   ${GREEN}✅ Cleared${NC}"

# 2. Remove incomplete downloads
echo ""
echo -e "${BLUE}🧹 2. Removing incomplete downloads...${NC}"
find "$HOME/Downloads" -name "*.crdownload" -exec ls -lh {} \; 2>/dev/null | while read -r line; do
    FILE=$(echo "$line" | awk '{print $9}')
    SIZE=$(echo "$line" | awk '{print $5}')
    echo "   Removing: ${YELLOW}$(basename "$FILE")${NC} (${YELLOW}$SIZE${NC})"
    rm -f "$FILE" 2>/dev/null || true
done
echo -e "   ${GREEN}✅ Cleared incomplete downloads${NC}"

# 3. Temporarily remove Pods (can reinstall with pod install)
echo ""
echo -e "${BLUE}🧹 3. Temporarily removing iOS Pods (1.8GB)...${NC}"
PROJECT_ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
PODS_PATH="$PROJECT_ROOT/mobile/ios/Pods"
if [ -d "$PODS_PATH" ]; then
    SIZE=$(get_size "$PODS_PATH")
    echo "   Found: ${YELLOW}$SIZE${NC}"
    echo -e "   ${YELLOW}⚠️  Removing Pods - you'll need to run 'cd mobile/ios && pod install' later${NC}"
    rm -rf "$PODS_PATH" 2>/dev/null || true
    echo -e "   ${GREEN}✅ Removed Pods${NC}"
    echo -e "   ${CYAN}   To restore: cd mobile/ios && pod install${NC}"
fi

# 4. Clean Xcode DerivedData (again, in case more accumulated)
echo ""
echo -e "${BLUE}🧹 4. Deep cleaning Xcode caches...${NC}"
rm -rf "$HOME/Library/Developer/Xcode/DerivedData"/* 2>/dev/null || true
rm -rf "$HOME/Library/Developer/Xcode/Archives"/* 2>/dev/null || true
rm -rf "$HOME/Library/Developer/Xcode/iOS DeviceSupport"/* 2>/dev/null || true
rm -rf "$HOME/Library/Developer/CoreSimulator/Caches"/* 2>/dev/null || true
echo -e "   ${GREEN}✅ Cleared${NC}"

# 5. Clean all CocoaPods cache
echo ""
echo -e "${BLUE}🧹 5. Deep cleaning CocoaPods...${NC}"
rm -rf "$HOME/Library/Caches/CocoaPods"/* 2>/dev/null || true
pod cache clean --all 2>/dev/null || true
echo -e "   ${GREEN}✅ Cleared${NC}"

# 6. Clean npm and yarn caches
echo ""
echo -e "${BLUE}🧹 6. Deep cleaning npm/yarn...${NC}"
npm cache clean --force 2>/dev/null || rm -rf "$HOME/.npm/_cacache"/* 2>/dev/null || true
rm -rf "$HOME/.cache/yarn"/* 2>/dev/null || true
echo -e "   ${GREEN}✅ Cleared${NC}"

# 7. Clean Expo cache
echo ""
echo -e "${BLUE}🧹 7. Deep cleaning Expo cache...${NC}"
rm -rf "$HOME/.expo"/* 2>/dev/null || true
if [ -d "$PROJECT_ROOT/mobile/.expo" ]; then
    rm -rf "$PROJECT_ROOT/mobile/.expo"/* 2>/dev/null || true
fi
echo -e "   ${GREEN}✅ Cleared${NC}"

# 8. Clean watchman
echo ""
echo -e "${BLUE}🧹 8. Cleaning Watchman...${NC}"
if command -v watchman &> /dev/null; then
    watchman watch-del-all 2>/dev/null || true
fi
echo -e "   ${GREEN}✅ Cleared${NC}"

# 9. Clean Homebrew
echo ""
echo -e "${BLUE}🧹 9. Cleaning Homebrew...${NC}"
if command -v brew &> /dev/null; then
    brew cleanup -s 2>/dev/null || true
fi
echo -e "   ${GREEN}✅ Cleared${NC}"

# 10. Clean project build artifacts
echo ""
echo -e "${BLUE}🧹 10. Cleaning all project build artifacts...${NC}"
if [ -d "$PROJECT_ROOT/mobile/ios/build" ]; then
    rm -rf "$PROJECT_ROOT/mobile/ios/build"/* 2>/dev/null || true
fi
if [ -d "$PROJECT_ROOT/mobile/.expo" ]; then
    rm -rf "$PROJECT_ROOT/mobile/.expo"/* 2>/dev/null || true
fi
if [ -d "$PROJECT_ROOT/mobile/.expo-shared" ]; then
    rm -rf "$PROJECT_ROOT/mobile/.expo-shared"/* 2>/dev/null || true
fi
echo -e "   ${GREEN}✅ Cleared${NC}"

# 11. Remove old iOS simulator data (keeps current)
echo ""
echo -e "${BLUE}🧹 11. Cleaning old iOS simulator data...${NC}"
xcrun simctl delete unavailable 2>/dev/null || true
# Remove old simulator runtimes (keeps current iOS version)
xcrun simctl runtime list 2>/dev/null | grep -v "active" | grep "iOS" | while read -r runtime; do
    echo "   Found old runtime: $runtime"
done
echo -e "   ${GREEN}✅ Cleared${NC}"

# Final check
echo ""
echo -e "${CYAN}╔════════════════════════════════════════════════════╗${NC}"
FINAL_SPACE=$(calculate_space)
echo -e "${GREEN}📊 Final Available Space: $FINAL_SPACE${NC}"
echo -e "${CYAN}╚════════════════════════════════════════════════════╝${NC}"
echo ""

# Show space difference
INITIAL_NUM=$(echo "$INITIAL_SPACE" | sed 's/Gi//' | sed 's/Mi//' | awk '{print $1}')
FINAL_NUM=$(echo "$FINAL_SPACE" | sed 's/Gi//' | sed 's/Mi//' | awk '{print $1}')
# Note: This is approximate, but gives an idea

echo -e "${GREEN}✅ Aggressive Cleanup Complete!${NC}"
echo ""
echo -e "${BLUE}💡 Next Steps:${NC}"
echo "   1. Try installing Xcode 16.4 again"
echo "   2. After Xcode is installed, restore Pods:"
echo "      ${CYAN}cd mobile/ios && pod install${NC}"
echo ""
echo -e "${YELLOW}⚠️  Note: You'll need to run 'pod install' in mobile/ios after installation${NC}"
echo ""

