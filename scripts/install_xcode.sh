#!/usr/bin/env bash
# Move Xcode from Downloads to Applications and configure it

set -euo pipefail

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${BLUE}╔════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║  Installing Xcode 16.4                            ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════╝${NC}"
echo ""

XCODE_DOWNLOADS="$HOME/Downloads/Xcode.app"
XCODE_APPS="/Applications/Xcode.app"

# Check if Xcode exists in Downloads
if [ ! -d "$XCODE_DOWNLOADS" ]; then
    echo -e "${RED}❌ Error: Xcode.app not found in ~/Downloads${NC}"
    echo "   Please extract the Xcode_16.4.xip file first"
    exit 1
fi

echo -e "${BLUE}📦 Found Xcode in Downloads${NC}"
echo "   Size: $(du -sh "$XCODE_DOWNLOADS" 2>/dev/null | awk '{print $1}')"
echo ""

# Check if there's already an Xcode in Applications
if [ -d "$XCODE_APPS" ]; then
    echo -e "${YELLOW}⚠️  Xcode already exists in /Applications${NC}"
    echo "   Current version: $(/usr/libexec/PlistBuddy -c "Print :CFBundleShortVersionString" "$XCODE_APPS/Contents/version.plist" 2>/dev/null || echo "unknown")"
    echo ""
    read -p "   Replace it? (y/n): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "   Cancelled."
        exit 0
    fi
    echo ""
    echo -e "${BLUE}🗑️  Removing old Xcode...${NC}"
    sudo rm -rf "$XCODE_APPS"
    echo -e "${GREEN}✅ Removed${NC}"
fi

# Move Xcode to Applications (requires sudo)
echo ""
echo -e "${BLUE}📦 Moving Xcode to /Applications...${NC}"
echo -e "${YELLOW}   This will require your password${NC}"
echo ""

# First, quit any running Xcode instances
pkill -9 Xcode 2>/dev/null || true
sleep 2

# Move Xcode (requires sudo for /Applications)
sudo mv "$XCODE_DOWNLOADS" "$XCODE_APPS"
echo -e "${GREEN}✅ Moved Xcode to /Applications${NC}"

# Fix permissions
echo ""
echo -e "${BLUE}🔧 Fixing permissions...${NC}"
sudo xattr -dr com.apple.quarantine "$XCODE_APPS" 2>/dev/null || true
sudo chown -R root:wheel "$XCODE_APPS" 2>/dev/null || true
echo -e "${GREEN}✅ Permissions fixed${NC}"

# Set Xcode as active developer directory
echo ""
echo -e "${BLUE}🔧 Setting up command line tools...${NC}"
sudo xcode-select -s "$XCODE_APPS/Contents/Developer"
echo -e "${GREEN}✅ Command line tools configured${NC}"

# Accept license agreement
echo ""
echo -e "${BLUE}📝 Accepting Xcode license...${NC}"
sudo xcodebuild -license accept 2>/dev/null || echo -e "${YELLOW}   License may need manual acceptance${NC}"

# Install additional components
echo ""
echo -e "${BLUE}📦 Installing additional components...${NC}"
sudo xcodebuild -runFirstLaunch 2>/dev/null || true
echo -e "${GREEN}✅ Components installed${NC}"

# Verify installation
echo ""
echo -e "${BLUE}✅ Verifying installation...${NC}"
echo "   Developer directory: $(xcode-select -p)"
echo "   Xcode version: $(xcodebuild -version 2>/dev/null | head -1 || echo "Could not determine")"
echo ""

echo -e "${GREEN}╔════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║  ✅ Xcode Installation Complete!                 ║${NC}"
echo -e "${GREEN}╚════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${BLUE}💡 Next steps:${NC}"
echo "   1. Open Xcode once to complete setup"
echo "   2. Run: cd mobile/ios && pod install"
echo "   3. Then you can run: npm start"
echo ""

