#!/usr/bin/env bash
# Free up disk space for Xcode 16.4 installation
# This script safely removes caches and build artifacts to free ~7GB+

set -euo pipefail

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
CYAN='\033[0;36m'
NC='\033[0m'

echo -e "${CYAN}╔════════════════════════════════════════════════════╗${NC}"
echo -e "${CYAN}║  Xcode 16.4 Installation - Disk Space Cleanup    ║${NC}"
echo -e "${CYAN}╚════════════════════════════════════════════════════╝${NC}"
echo ""

# Function to get directory size
get_size() {
    local path="$1"
    if [ -d "$path" ]; then
        du -sh "$path" 2>/dev/null | awk '{print $1}' || echo "0"
    else
        echo "0"
    fi
}

# Function to calculate space before/after
calculate_space() {
    df -h / | tail -1 | awk '{print $4}'
}

# Initial disk space
INITIAL_SPACE=$(calculate_space)
echo -e "${BLUE}📊 Current Available Space:${NC} ${GREEN}$INITIAL_SPACE${NC}"
echo ""

TOTAL_FREED=0

# 1. Xcode DerivedData (often 5-20GB)
echo -e "${BLUE}🧹 1. Cleaning Xcode DerivedData...${NC}"
DERIVED_PATH="$HOME/Library/Developer/Xcode/DerivedData"
if [ -d "$DERIVED_PATH" ]; then
    SIZE=$(get_size "$DERIVED_PATH")
    echo "   Found: ${YELLOW}$SIZE${NC}"
    rm -rf "$DERIVED_PATH"/* 2>/dev/null || true
    echo -e "   ${GREEN}✅ Cleared${NC}"
fi

# 2. Xcode Archives (often 1-5GB)
echo ""
echo -e "${BLUE}🧹 2. Cleaning Xcode Archives...${NC}"
ARCHIVES_PATH="$HOME/Library/Developer/Xcode/Archives"
if [ -d "$ARCHIVES_PATH" ]; then
    SIZE=$(get_size "$ARCHIVES_PATH")
    echo "   Found: ${YELLOW}$SIZE${NC}"
    rm -rf "$ARCHIVES_PATH"/* 2>/dev/null || true
    echo -e "   ${GREEN}✅ Cleared${NC}"
fi

# 3. iOS DeviceSupport (old iOS versions, often 2-10GB)
echo ""
echo -e "${BLUE}🧹 3. Cleaning old iOS DeviceSupport...${NC}"
DEVICE_SUPPORT_PATH="$HOME/Library/Developer/Xcode/iOS DeviceSupport"
if [ -d "$DEVICE_SUPPORT_PATH" ]; then
    SIZE=$(get_size "$DEVICE_SUPPORT_PATH")
    echo "   Found: ${YELLOW}$SIZE${NC}"
    rm -rf "$DEVICE_SUPPORT_PATH"/* 2>/dev/null || true
    echo -e "   ${GREEN}✅ Cleared${NC}"
fi

# 4. iOS Simulators - Caches (often 1-3GB)
echo ""
echo -e "${BLUE}🧹 4. Cleaning iOS Simulator Caches...${NC}"
SIMULATOR_CACHES="$HOME/Library/Developer/CoreSimulator/Caches"
if [ -d "$SIMULATOR_CACHES" ]; then
    SIZE=$(get_size "$SIMULATOR_CACHES")
    echo "   Found: ${YELLOW}$SIZE${NC}"
    rm -rf "$SIMULATOR_CACHES"/* 2>/dev/null || true
    echo -e "   ${GREEN}✅ Cleared${NC}"
fi

# 5. Remove unavailable simulators
echo ""
echo -e "${BLUE}🧹 5. Removing unavailable iOS simulators...${NC}"
xcrun simctl delete unavailable 2>/dev/null && echo -e "   ${GREEN}✅ Removed unavailable simulators${NC}" || echo -e "   ${YELLOW}⚠️  No unavailable simulators${NC}"

# 6. CocoaPods Cache (often 500MB-2GB)
echo ""
echo -e "${BLUE}🧹 6. Cleaning CocoaPods Cache...${NC}"
COCOAPODS_CACHE="$HOME/Library/Caches/CocoaPods"
if [ -d "$COCOAPODS_CACHE" ]; then
    SIZE=$(get_size "$COCOAPODS_CACHE")
    echo "   Found: ${YELLOW}$SIZE${NC}"
    rm -rf "$COCOAPODS_CACHE"/* 2>/dev/null || true
    echo -e "   ${GREEN}✅ Cleared${NC}"
fi

# 7. npm Cache (often 200MB-1GB)
echo ""
echo -e "${BLUE}🧹 7. Cleaning npm Cache...${NC}"
if [ -d "$HOME/.npm" ]; then
    SIZE=$(get_size "$HOME/.npm")
    echo "   Found: ${YELLOW}$SIZE${NC}"
    npm cache clean --force 2>/dev/null || rm -rf "$HOME/.npm/_cacache"/* 2>/dev/null || true
    echo -e "   ${GREEN}✅ Cleared${NC}"
fi

# 8. Yarn Cache
echo ""
echo -e "${BLUE}🧹 8. Cleaning Yarn Cache...${NC}"
YARN_CACHE="$HOME/.cache/yarn"
if [ -d "$YARN_CACHE" ]; then
    SIZE=$(get_size "$YARN_CACHE")
    echo "   Found: ${YELLOW}$SIZE${NC}"
    rm -rf "$YARN_CACHE"/* 2>/dev/null || true
    echo -e "   ${GREEN}✅ Cleared${NC}"
fi

# 9. Expo Cache (often 500MB-2GB)
echo ""
echo -e "${BLUE}🧹 9. Cleaning Expo Cache...${NC}"
EXPO_CACHE="$HOME/.expo"
if [ -d "$EXPO_CACHE" ]; then
    SIZE=$(get_size "$EXPO_CACHE")
    echo "   Found: ${YELLOW}$SIZE${NC}"
    rm -rf "$EXPO_CACHE"/* 2>/dev/null || true
    echo -e "   ${GREEN}✅ Cleared${NC}"
fi

# 10. Watchman Cache
echo ""
echo -e "${BLUE}🧹 10. Cleaning Watchman Cache...${NC}"
if command -v watchman &> /dev/null; then
    watchman watch-del-all 2>/dev/null && echo -e "   ${GREEN}✅ Cleared${NC}" || echo -e "   ${YELLOW}⚠️  Watchman not active${NC}"
fi

# 11. Homebrew Cache (if installed)
echo ""
echo -e "${BLUE}🧹 11. Cleaning Homebrew Cache...${NC}"
if command -v brew &> /dev/null; then
    brew cleanup -s 2>/dev/null && echo -e "   ${GREEN}✅ Cleared${NC}" || echo -e "   ${YELLOW}⚠️  No brew cache to clean${NC}"
fi

# 12. Pod Cache (CocoaPods)
echo ""
echo -e "${BLUE}🧹 12. Cleaning Pod Cache...${NC}"
if command -v pod &> /dev/null; then
    pod cache clean --all 2>/dev/null && echo -e "   ${GREEN}✅ Cleared${NC}" || echo -e "   ${YELLOW}⚠️  No pod cache to clean${NC}"
fi

# 13. Check for old Xcode versions
echo ""
echo -e "${BLUE}🔍 13. Checking for old Xcode versions...${NC}"
OLD_XCODE=$(ls -d /Applications/Xcode*.app 2>/dev/null | grep -v "^/Applications/Xcode.app$" || true)
if [ -n "$OLD_XCODE" ]; then
    echo "   Found old Xcode versions:"
    for xcode in $OLD_XCODE; do
        SIZE=$(get_size "$xcode")
        echo "   ${YELLOW}$xcode${NC} - ${YELLOW}$SIZE${NC}"
    done
    echo ""
    echo -e "   ${YELLOW}⚠️  You can manually remove old Xcode versions if needed${NC}"
    echo -e "   ${CYAN}   Example: sudo rm -rf /Applications/Xcode-16.1.app${NC}"
else
    echo -e "   ${GREEN}✅ No old Xcode versions found${NC}"
fi

# 14. Clean project-specific build artifacts
echo ""
echo -e "${BLUE}🧹 14. Cleaning project build artifacts...${NC}"
PROJECT_ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"

# Clean iOS build folders
if [ -d "$PROJECT_ROOT/mobile/ios/build" ]; then
    SIZE=$(get_size "$PROJECT_ROOT/mobile/ios/build")
    echo "   Found ios/build: ${YELLOW}$SIZE${NC}"
    rm -rf "$PROJECT_ROOT/mobile/ios/build"/* 2>/dev/null || true
    echo -e "   ${GREEN}✅ Cleared${NC}"
fi

# Clean Pods (will need to reinstall, but saves space temporarily)
if [ -d "$PROJECT_ROOT/mobile/ios/Pods" ]; then
    SIZE=$(get_size "$PROJECT_ROOT/mobile/ios/Pods")
    echo "   Found ios/Pods: ${YELLOW}$SIZE${NC}"
    echo -e "   ${YELLOW}⚠️  Skipping Pods (needed for builds)${NC}"
fi

# Clean .expo folders in project
if [ -d "$PROJECT_ROOT/mobile/.expo" ]; then
    SIZE=$(get_size "$PROJECT_ROOT/mobile/.expo")
    echo "   Found .expo: ${YELLOW}$SIZE${NC}"
    rm -rf "$PROJECT_ROOT/mobile/.expo"/* 2>/dev/null || true
    echo -e "   ${GREEN}✅ Cleared${NC}"
fi

# Clean node_modules in project (optional - comment out if you don't want to remove)
# if [ -d "$PROJECT_ROOT/mobile/node_modules" ]; then
#     SIZE=$(get_size "$PROJECT_ROOT/mobile/node_modules")
#     echo "   Found node_modules: ${YELLOW}$SIZE${NC}"
#     echo -e "   ${YELLOW}⚠️  Skipping node_modules (can run 'npm install' later)${NC}"
# fi

# Final disk space
echo ""
echo -e "${CYAN}╔════════════════════════════════════════════════════╗${NC}"
FINAL_SPACE=$(calculate_space)
echo -e "${GREEN}📊 Final Available Space: $FINAL_SPACE${NC}"
echo -e "${CYAN}╚════════════════════════════════════════════════════╝${NC}"
echo ""

# Summary
echo -e "${GREEN}✅ Cleanup Complete!${NC}"
echo ""
echo -e "${BLUE}💡 Next Steps:${NC}"
echo "   1. Try installing Xcode 16.4 again"
echo "   2. If still not enough space, check:"
echo "      • Trash (empty it: rm -rf ~/.Trash/*)"
echo "      • Downloads folder for large files"
echo "      • Old Xcode versions (shown above)"
echo "      • Docker images (if installed): docker system prune -a"
echo ""

