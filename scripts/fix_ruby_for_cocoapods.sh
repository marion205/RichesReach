#!/usr/bin/env bash
# Fix Ruby/OpenSSL issues for CocoaPods

set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${BLUE}╔════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║  Fixing Ruby/OpenSSL for CocoaPods                ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════╝${NC}"
echo ""

# Check if using RVM
if command -v rvm &> /dev/null; then
    echo -e "${BLUE}📦 Using RVM - fixing OpenSSL dependency...${NC}"
    
    # Check if openssl@3 is available (newer version)
    if brew list openssl@3 &>/dev/null; then
        echo -e "${GREEN}✅ Found openssl@3${NC}"
        export PKG_CONFIG_PATH="/opt/homebrew/opt/openssl@3/lib/pkgconfig:$PKG_CONFIG_PATH"
        export LDFLAGS="-L/opt/homebrew/opt/openssl@3/lib"
        export CPPFLAGS="-I/opt/homebrew/opt/openssl@3/include"
        echo "   Using openssl@3"
    elif brew list openssl &>/dev/null; then
        echo -e "${GREEN}✅ Found openssl${NC}"
        export PKG_CONFIG_PATH="/opt/homebrew/opt/openssl/lib/pkgconfig:$PKG_CONFIG_PATH"
        export LDFLAGS="-L/opt/homebrew/opt/openssl/lib"
        export CPPFLAGS="-I/opt/homebrew/opt/openssl/include"
        echo "   Using openssl"
    else
        echo -e "${YELLOW}⚠️  Installing openssl@3...${NC}"
        brew install openssl@3 || true
        export PKG_CONFIG_PATH="/opt/homebrew/opt/openssl@3/lib/pkgconfig:$PKG_CONFIG_PATH"
        export LDFLAGS="-L/opt/homebrew/opt/openssl@3/lib"
        export CPPFLAGS="-I/opt/homebrew/opt/openssl@3/include"
    fi
    
    echo ""
    echo -e "${BLUE}💎 Reinstalling Ruby with proper OpenSSL...${NC}"
    CURRENT_RUBY=$(rvm current 2>/dev/null || echo "ruby-2.7.6")
    echo "   Current: $CURRENT_RUBY"
    
    # Install a newer Ruby that works better with modern OpenSSL
    echo ""
    echo -e "${YELLOW}Installing Ruby 3.1.0 (better OpenSSL compatibility)...${NC}"
    rvm install 3.1.0 --with-openssl-dir=/opt/homebrew/opt/openssl@3 2>&1 | tail -5 || \
    rvm install 3.1.0 --with-openssl-dir=/opt/homebrew/opt/openssl 2>&1 | tail -5 || \
    rvm install 3.1.0 2>&1 | tail -5
    
    echo ""
    echo -e "${BLUE}🔄 Switching to Ruby 3.1.0...${NC}"
    rvm use 3.1.0 --default
    
    echo ""
    echo -e "${BLUE}📦 Reinstalling CocoaPods...${NC}"
    gem install cocoapods
    
    echo ""
    echo -e "${GREEN}✅ Ruby and CocoaPods fixed!${NC}"
    echo ""
    echo "Ruby version: $(ruby -v)"
    echo "CocoaPods version: $(pod --version 2>/dev/null || echo 'not installed')"
    echo ""
    
else
    echo -e "${YELLOW}⚠️  Not using RVM. Trying to fix system Ruby gems...${NC}"
    
    # Install OpenSSL if needed
    if ! brew list openssl@3 &>/dev/null && ! brew list openssl &>/dev/null; then
        echo "Installing openssl..."
        brew install openssl@3 || brew install openssl
    fi
    
    # Try to install CocoaPods with bundler or directly
    if [ -f "mobile/Gemfile" ]; then
        echo "Using Bundler..."
        cd mobile
        bundle install
        bundle exec pod --version
    else
        echo "Installing CocoaPods directly..."
        gem install cocoapods
    fi
fi

echo ""
echo -e "${GREEN}╔════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║  ✅ Ruby/CocoaPods Setup Complete!               ║${NC}"
echo -e "${GREEN}╚════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${BLUE}💡 Next steps:${NC}"
echo "   1. cd mobile/ios"
echo "   2. pod install"
echo "   3. cd .. && npm start"
echo ""

