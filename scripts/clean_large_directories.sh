#!/usr/bin/env bash
# Clean large directories that are safe to clean (can be regenerated)

set -euo pipefail

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
CYAN='\033[0;36m'
NC='\033[0m'

echo -e "${RED}╔════════════════════════════════════════════════════╗${NC}"
echo -e "${RED}║  Clean Large Rebuildable Directories             ║${NC}"
echo -e "${RED}╚════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${YELLOW}⚠️  This will remove rebuildable data (caches, old versions)${NC}"
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

# 1. CocoaPods repos (6.2GB) - can be redownloaded
echo -e "${BLUE}🧹 1. Cleaning CocoaPods repos (6.2GB)...${NC}"
COCOAPODS_REPO="$HOME/.cocoapods/repos"
if [ -d "$COCOAPODS_REPO" ]; then
    SIZE=$(get_size "$COCOAPODS_REPO")
    echo "   Found: ${YELLOW}$SIZE${NC}"
    echo -e "   ${YELLOW}⚠️  This will require 'pod repo update' after Xcode install${NC}"
    # Keep master, remove others
    if [ -d "$COCOAPODS_REPO/master" ]; then
        # Remove all non-master repos (usually trunk and other specs repos)
        find "$COCOAPODS_REPO" -mindepth 1 -maxdepth 1 ! -name "master" -exec rm -rf {} \; 2>/dev/null || true
        echo -e "   ${GREEN}✅ Removed non-master CocoaPods repos${NC}"
    else
        # If no master, just clean cache
        rm -rf "$COCOAPODS_REPO/trunk" 2>/dev/null || true
        echo -e "   ${GREEN}✅ Cleaned CocoaPods repos${NC}"
    fi
    echo -e "   ${CYAN}   To restore: pod repo update${NC}"
fi

# 2. NVM old Node versions (11GB) - keep current, remove old
echo ""
echo -e "${BLUE}🧹 2. Cleaning old Node versions in NVM (11GB)...${NC}"
NVM_PATH="$HOME/.nvm"
if [ -d "$NVM_PATH" ]; then
    SIZE=$(get_size "$NVM_PATH")
    echo "   Total NVM: ${YELLOW}$SIZE${NC}"
    
    if [ -d "$NVM_PATH/versions" ]; then
        CURRENT_NODE=$(node -v 2>/dev/null || echo "")
        echo "   Current Node: ${CYAN}$CURRENT_NODE${NC}"
        
        if [ -n "$CURRENT_NODE" ]; then
            # Remove all versions except current
            cd "$NVM_PATH/versions"
            for dir in node/*; do
                if [ -d "$dir" ] && [ "$dir" != "node/$CURRENT_NODE" ]; then
                    VERSION=$(basename "$dir")
                    VERSION_SIZE=$(get_size "$dir")
                    echo "   Removing old version: ${YELLOW}$VERSION${NC} (${YELLOW}$VERSION_SIZE${NC})"
                    rm -rf "$dir" 2>/dev/null || true
                fi
            done
            echo -e "   ${GREEN}✅ Removed old Node versions${NC}"
        else
            # If no current version detected, keep latest and remove others
            LATEST=$(ls -t "$NVM_PATH/versions/node" 2>/dev/null | head -1 || echo "")
            if [ -n "$LATEST" ]; then
                cd "$NVM_PATH/versions/node"
                for dir in */; do
                    if [ "$dir" != "$LATEST/" ]; then
                        VERSION=$(basename "$dir")
                        echo "   Removing: ${YELLOW}$VERSION${NC}"
                        rm -rf "$dir" 2>/dev/null || true
                    fi
                done
                echo -e "   ${GREEN}✅ Kept latest, removed old versions${NC}"
            fi
        fi
    fi
fi

# 3. Colima (Docker) data (7.3GB) - container images and volumes
echo ""
echo -e "${BLUE}🧹 3. Cleaning Colima (Docker alternative) data (7.3GB)...${NC}"
COLIMA_PATH="$HOME/.colima"
if [ -d "$COLIMA_PATH" ]; then
    SIZE=$(get_size "$COLIMA_PATH")
    echo "   Found: ${YELLOW}$SIZE${NC}"
    echo -e "   ${YELLOW}⚠️  This will remove Docker containers and images${NC}"
    
    # Try to stop and remove containers first (if colima is running)
    if command -v colima &> /dev/null; then
        colima stop 2>/dev/null || true
        echo -e "   ${GREEN}✅ Stopped Colima${NC}"
    fi
    
    # Remove data directories (images, volumes)
    if [ -d "$COLIMA_PATH/default" ]; then
        rm -rf "$COLIMA_PATH/default" 2>/dev/null || true
        echo -e "   ${GREEN}✅ Removed Colima data${NC}"
    fi
    
    echo -e "   ${CYAN}   To restore: colima start (will redownload images)${NC}"
fi

# 4. Rustup toolchains (1.2GB) - keep stable, remove old
echo ""
echo -e "${BLUE}🧹 4. Cleaning old Rust toolchains (1.2GB)...${NC}"
RUSTUP_PATH="$HOME/.rustup"
if [ -d "$RUSTUP_PATH" ]; then
    SIZE=$(get_size "$RUSTUP_PATH")
    echo "   Found: ${YELLOW}$SIZE${NC}"
    
    # Remove old toolchains, keep stable
    if [ -d "$RUSTUP_PATH/toolchains" ]; then
        cd "$RUSTUP_PATH/toolchains"
        for dir in */; do
            if [[ ! "$dir" =~ stable ]]; then
                TOOLCHAIN=$(basename "$dir")
                echo "   Removing: ${YELLOW}$TOOLCHAIN${NC}"
                rm -rf "$dir" 2>/dev/null || true
            fi
        done
        echo -e "   ${GREEN}✅ Removed old Rust toolchains${NC}"
    fi
    echo -e "   ${CYAN}   To restore: rustup toolchain install <name>${NC}"
fi

# 5. VS Code extensions cache (855MB)
echo ""
echo -e "${BLUE}🧹 5. Cleaning VS Code extensions cache...${NC}"
VSCODE_EXT_CACHE="$HOME/.vscode/extensions"
if [ -d "$VSCODE_EXT_CACHE" ]; then
    SIZE=$(get_size "$VSCODE_EXT_CACHE")
    echo "   Found: ${YELLOW}$SIZE${NC}"
    # Remove cached extension downloads, keep installed
    find "$VSCODE_EXT_CACHE" -name "*.vsix" -delete 2>/dev/null || true
    echo -e "   ${GREEN}✅ Cleared extension caches${NC}"
fi

# Final check
echo ""
echo -e "${CYAN}╔════════════════════════════════════════════════════╗${NC}"
FINAL_SPACE=$(calculate_space)
echo -e "${GREEN}📊 Final Available Space: $FINAL_SPACE${NC}"
echo -e "${CYAN}╚════════════════════════════════════════════════════╝${NC}"
echo ""

echo -e "${GREEN}✅ Large directory cleanup complete!${NC}"
echo ""
echo -e "${BLUE}💡 Summary:${NC}"
echo "   • CocoaPods repos cleaned (6.2GB → smaller)"
echo "   • Old Node versions removed (kept current)"
echo "   • Colima Docker data removed (7.3GB)"
echo "   • Old Rust toolchains removed"
echo ""
echo -e "${YELLOW}⚠️  After Xcode install, you may need to:${NC}"
echo "   • pod repo update"
echo "   • colima start (if you use Docker)"
echo ""

