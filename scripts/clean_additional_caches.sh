#!/usr/bin/env bash
# Clean additional application caches to free more space

set -euo pipefail

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}🧹 Cleaning Additional Application Caches...${NC}"
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

# 1. Google Chrome/Drive Cache (1.8GB)
echo -e "${BLUE}🧹 1. Cleaning Google Application Support cache...${NC}"
GOOGLE_APP_SUPPORT="$HOME/Library/Application Support/Google"
if [ -d "$GOOGLE_APP_SUPPORT" ]; then
    SIZE=$(get_size "$GOOGLE_APP_SUPPORT")
    echo "   Found: ${YELLOW}$SIZE${NC}"
    
    # Chrome cache
    if [ -d "$GOOGLE_APP_SUPPORT/Chrome/Default/Cache" ]; then
        CHROME_SIZE=$(get_size "$GOOGLE_APP_SUPPORT/Chrome/Default/Cache")
        echo "   Chrome Cache: ${YELLOW}$CHROME_SIZE${NC}"
        rm -rf "$GOOGLE_APP_SUPPORT/Chrome/Default/Cache"/* 2>/dev/null || true
        rm -rf "$GOOGLE_APP_SUPPORT/Chrome/Default/Code Cache"/* 2>/dev/null || true
        rm -rf "$GOOGLE_APP_SUPPORT/Chrome/Default/GPUCache"/* 2>/dev/null || true
    fi
    
    # Google Drive cache
    if [ -d "$GOOGLE_APP_SUPPORT/DriveFS" ]; then
        DRIVE_SIZE=$(get_size "$GOOGLE_APP_SUPPORT/DriveFS")
        echo "   DriveFS Cache: ${YELLOW}$DRIVE_SIZE${NC}"
        # Only remove cache, not data
        find "$GOOGLE_APP_SUPPORT/DriveFS" -type d -name "cache" -exec rm -rf {}/* \; 2>/dev/null || true
    fi
    
    echo -e "   ${GREEN}✅ Cleared Google caches${NC}"
fi

# 2. Text-to-Speech Cache (1.7GB)
echo ""
echo -e "${BLUE}🧹 2. Cleaning Text-to-Speech cache...${NC}"
TTS_PATH="$HOME/Library/Application Support/tts"
if [ -d "$TTS_PATH" ]; then
    SIZE=$(get_size "$TTS_PATH")
    echo "   Found: ${YELLOW}$SIZE${NC}"
    # Clean cache but keep config
    find "$TTS_PATH" -type d -name "cache" -exec rm -rf {}/* \; 2>/dev/null || true
    find "$TTS_PATH" -type d -name "Cache" -exec rm -rf {}/* \; 2>/dev/null || true
    # If it's all cache, remove older files
    find "$TTS_PATH" -type f -mtime +30 -delete 2>/dev/null || true
    echo -e "   ${GREEN}✅ Cleared TTS cache${NC}"
fi

# 3. VS Code Cache (956MB)
echo ""
echo -e "${BLUE}🧹 3. Cleaning VS Code cache...${NC}"
VSCODE_CACHE="$HOME/Library/Application Support/Code/Cache"
if [ -d "$VSCODE_CACHE" ]; then
    SIZE=$(get_size "$VSCODE_CACHE")
    echo "   Found: ${YELLOW}$SIZE${NC}"
    rm -rf "$VSCODE_CACHE"/* 2>/dev/null || true
    echo -e "   ${GREEN}✅ Cleared VS Code cache${NC}"
fi

# Also clean Code's other cache directories
VSCODE_CACHED_DATA="$HOME/Library/Application Support/Code/CachedData"
if [ -d "$VSCODE_CACHED_DATA" ]; then
    SIZE=$(get_size "$VSCODE_CACHED_DATA")
    echo "   CachedData: ${YELLOW}$SIZE${NC}"
    # Keep latest, remove older versions
    cd "$VSCODE_CACHED_DATA"
    ls -t | tail -n +2 | xargs rm -rf 2>/dev/null || true
    echo -e "   ${GREEN}✅ Cleared old VS Code CachedData${NC}"
fi

# 4. Visual Studio Cache (821MB)
echo ""
echo -e "${BLUE}🧹 4. Cleaning Visual Studio cache...${NC}"
VS_PATH="$HOME/Library/Application Support/VisualStudio"
if [ -d "$VS_PATH" ]; then
    SIZE=$(get_size "$VS_PATH")
    echo "   Found: ${YELLOW}$SIZE${NC}"
    # Clean cache directories
    find "$VS_PATH" -type d -name "Cache" -exec rm -rf {}/* \; 2>/dev/null || true
    find "$VS_PATH" -type d -name "cache" -exec rm -rf {}/* \; 2>/dev/null || true
    echo -e "   ${GREEN}✅ Cleared Visual Studio cache${NC}"
fi

# 5. WebEx Cache (701MB)
echo ""
echo -e "${BLUE}🧹 5. Cleaning WebEx cache...${NC}"
WEBEX_PATH="$HOME/Library/Application Support/WebEx Folder"
if [ -d "$WEBEX_PATH" ]; then
    SIZE=$(get_size "$WEBEX_PATH")
    echo "   Found: ${YELLOW}$SIZE${NC}"
    find "$WEBEX_PATH" -type d -name "Cache" -exec rm -rf {}/* \; 2>/dev/null || true
    find "$WEBEX_PATH" -type d -name "cache" -exec rm -rf {}/* \; 2>/dev/null || true
    find "$WEBEX_PATH" -type f -name "*.tmp" -delete 2>/dev/null || true
    echo -e "   ${GREEN}✅ Cleared WebEx cache${NC}"
fi

# 6. Zoom Cache (220MB)
echo ""
echo -e "${BLUE}🧹 6. Cleaning Zoom cache...${NC}"
ZOOM_PATH="$HOME/Library/Application Support/zoom.us"
if [ -d "$ZOOM_PATH" ]; then
    SIZE=$(get_size "$ZOOM_PATH")
    echo "   Found: ${YELLOW}$SIZE${NC}"
    rm -rf "$ZOOM_PATH"/*.log 2>/dev/null || true
    find "$ZOOM_PATH" -type d -name "Cache" -exec rm -rf {}/* \; 2>/dev/null || true
    echo -e "   ${GREEN}✅ Cleared Zoom cache${NC}"
fi

# 7. System Caches
echo ""
echo -e "${BLUE}🧹 7. Cleaning system caches...${NC}"
# Homebrew cache (if not already cleaned)
if [ -d "$HOME/Library/Caches/Homebrew" ]; then
    SIZE=$(get_size "$HOME/Library/Caches/Homebrew")
    echo "   Homebrew: ${YELLOW}$SIZE${NC}"
    rm -rf "$HOME/Library/Caches/Homebrew"/* 2>/dev/null || true
fi

# GeoServices cache
if [ -d "$HOME/Library/Caches/GeoServices" ]; then
    SIZE=$(get_size "$HOME/Library/Caches/GeoServices")
    echo "   GeoServices: ${YELLOW}$SIZE${NC}"
    rm -rf "$HOME/Library/Caches/GeoServices"/* 2>/dev/null || true
fi

# 8. Check for other large cache files
echo ""
echo -e "${BLUE}🧹 8. Finding other large cache files...${NC}"
find "$HOME/Library/Caches" -type f -size +100M -exec ls -lh {} \; 2>/dev/null | head -5 | while read -r line; do
    FILE=$(echo "$line" | awk '{print $9}')
    SIZE=$(echo "$line" | awk '{print $5}')
    echo "   Found: ${YELLOW}$(basename "$FILE")${NC} (${YELLOW}$SIZE${NC})"
done

# Final check
echo ""
FINAL_SPACE=$(calculate_space)
echo -e "${BLUE}📊 Final Available Space:${NC} ${GREEN}$FINAL_SPACE${NC}"
echo ""
echo -e "${GREEN}✅ Additional cache cleanup complete!${NC}"
echo ""

