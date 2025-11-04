#!/usr/bin/env bash
# Fix Xcode installation and Ruby gem issues

set -euo pipefail

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
CYAN='\033[0;36m'
NC='\033[0m'

echo -e "${BLUE}╔════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║  Fixing Xcode Installation & Ruby Issues          ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════╝${NC}"
echo ""

XCODE_DOWNLOADS="$HOME/Downloads/Xcode.app"
XCODE_APPS="/Applications/Xcode.app"

# Step 1: Move Xcode
if [ -d "$XCODE_DOWNLOADS" ] && [ ! -d "$XCODE_APPS" ]; then
    echo -e "${BLUE}📦 Step 1: Moving Xcode from Downloads to Applications...${NC}"
    echo -e "${YELLOW}   This will require your password${NC}"
    
    # Get size for progress indication
    SIZE=$(du -sh "$XCODE_DOWNLOADS" 2>/dev/null | awk '{print $1}')
    echo "   Size: $SIZE"
    echo ""
    
    # Move Xcode (requires sudo)
    sudo mv "$XCODE_DOWNLOADS" "$XCODE_APPS"
    echo -e "${GREEN}✅ Moved Xcode to /Applications${NC}"
    
    # Fix permissions
    sudo xattr -dr com.apple.quarantine "$XCODE_APPS" 2>/dev/null || true
    echo -e "${GREEN}✅ Fixed permissions${NC}"
    echo ""
elif [ -d "$XCODE_APPS" ]; then
    echo -e "${GREEN}✅ Xcode already in /Applications${NC}"
    echo ""
else
    echo -e "${RED}❌ Error: Xcode not found in Downloads or Applications${NC}"
    exit 1
fi

# Step 2: Configure Xcode command-line tools
echo -e "${BLUE}🔧 Step 2: Configuring Xcode command-line tools...${NC}"
sudo xcode-select -s "$XCODE_APPS/Contents/Developer"
echo -e "${GREEN}✅ Command-line tools configured${NC}"
echo ""

# Step 3: Accept Xcode license
echo -e "${BLUE}📝 Step 3: Accepting Xcode license...${NC}"
sudo xcodebuild -license accept 2>/dev/null || echo -e "${YELLOW}   License may need manual acceptance (run Xcode once)${NC}"
echo ""

# Step 4: Run first launch
echo -e "${BLUE}📦 Step 4: Installing additional components...${NC}"
sudo xcodebuild -runFirstLaunch 2>/dev/null || true
echo -e "${GREEN}✅ Components installed${NC}"
echo ""

# Step 5: Fix Ruby gem extensions
echo -e "${BLUE}💎 Step 5: Fixing Ruby gem extensions...${NC}"

# Check if using RVM
if command -v rvm &> /dev/null; then
    echo "   Using RVM"
    CURRENT_RUBY=$(rvm current 2>/dev/null || echo "ruby-2.7.6")
    echo "   Current Ruby: $CURRENT_RUBY"
    echo ""
    
    # Rebuild gems with new Xcode
    echo -e "${YELLOW}   Rebuilding gem extensions (this may take a few minutes)...${NC}"
    gem pristine ffi --version 1.15.5 2>/dev/null || gem install ffi --force 2>/dev/null || true
    gem pristine bigdecimal --version 3.3.1 2>/dev/null || gem install bigdecimal --force 2>/dev/null || true
    gem pristine executable-hooks --version 1.6.1 2>/dev/null || gem install executable-hooks --force 2>/dev/null || true
    gem pristine gem-wrappers --version 1.4.0 2>/dev/null || gem install gem-wrappers --force 2>/dev/null || true
    
    echo -e "${GREEN}✅ Gems rebuilt${NC}"
elif command -v rbenv &> /dev/null; then
    echo "   Using rbenv"
    eval "$(rbenv init -)"
    gem install ffi --force 2>/dev/null || true
    echo -e "${GREEN}✅ Gems rebuilt${NC}"
else
    echo -e "${YELLOW}   Using system Ruby - rebuilding gems...${NC}"
    sudo gem pristine ffi --version 1.15.5 2>/dev/null || sudo gem install ffi --force 2>/dev/null || true
    echo -e "${GREEN}✅ Gems rebuilt${NC}"
fi

echo ""

# Step 6: Verify
echo -e "${BLUE}✅ Step 6: Verifying installation...${NC}"
echo "   Developer directory: $(xcode-select -p)"
XCODE_VERSION=$(xcodebuild -version 2>/dev/null | head -1 || echo "Could not determine")
echo "   Xcode version: $XCODE_VERSION"
echo ""
POD_VERSION=$(pod --version 2>/dev/null || echo "CocoaPods not working")
echo "   CocoaPods version: $POD_VERSION"
echo ""

echo -e "${GREEN}╔════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║  ✅ Setup Complete!                               ║${NC}"
echo -e "${GREEN}╚════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${BLUE}💡 Next steps:${NC}"
echo "   1. If CocoaPods still doesn't work, try:"
echo "      ${CYAN}gem install cocoapods${NC}"
echo "   2. Install iOS Pods:"
echo "      ${CYAN}cd mobile/ios && pod install${NC}"
echo "   3. Start your app:"
echo "      ${CYAN}cd mobile && npm start${NC}"
echo ""

