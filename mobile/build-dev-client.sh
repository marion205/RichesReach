#!/bin/bash
# RichesReach Mobile - Development Client Build Script
# Builds and installs the Expo development client for iOS Simulator

set -e

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Verify we're in the right place
if [ ! -f "package.json" ]; then
    echo "❌ Error: package.json not found!"
    echo "   Current directory: $(pwd)"
    exit 1
fi

if [ ! -f "eas.json" ]; then
    echo "❌ Error: eas.json not found!"
    echo "   Run: eas build:configure"
    exit 1
fi

echo "🚀 Building RichesReach Development Client"
echo "📦 Project: $(grep '"name"' package.json | head -1 | cut -d'"' -f4)"
echo ""

# Check EAS login
if ! eas whoami &>/dev/null; then
    echo "⚠️  Not logged into EAS"
    echo "   Run: eas login"
    exit 1
fi

echo "✅ Logged into EAS as: $(eas whoami)"
echo ""

# Check if simulator is running
if ! xcrun simctl list devices | grep -q "Booted"; then
    echo "⚠️  No iOS Simulator is running"
    echo "   Opening Simulator..."
    open -a Simulator
    sleep 3
fi

# Determine build type
BUILD_TYPE="${1:-simulator}"

if [ "$BUILD_TYPE" == "simulator" ]; then
    echo "📱 Building for iOS Simulator"
    echo ""
    
    # Check for Fastlane (for local builds)
    HAS_FASTLANE=false
    if command -v fastlane &> /dev/null; then
        HAS_FASTLANE=true
        FASTLANE_VERSION=$(fastlane --version 2>/dev/null | head -1 || echo "installed")
    fi
    
    echo "Choose build method:"
    echo "  1) Cloud build (recommended, 5-10 min, no setup needed)"
    if [ "$HAS_FASTLANE" = true ]; then
        echo "  2) Local build (faster, 2-5 min, requires Xcode)"
    else
        echo "  2) Local build (requires Fastlane - not installed)"
    fi
    echo ""
    read -p "Enter choice [1]: " choice
    choice=${choice:-1}
    
    if [ "$choice" == "2" ]; then
        # Check for Fastlane (required for local builds)
        if [ "$HAS_FASTLANE" != true ]; then
            echo ""
            echo "❌ Fastlane is required for local builds but not found"
            echo ""
            echo "Quick install options:"
            echo "  brew install fastlane          (Recommended)"
            echo "  sudo gem install fastlane      (System-wide)"
            echo "  gem install fastlane --user-install  (User install)"
            echo ""
            read -p "Switch to cloud build instead? [Y/n]: " switch
            switch=${switch:-Y}
            if [[ "$switch" =~ ^[Yy]$ ]]; then
                choice=1
            else
                echo ""
                echo "Please install Fastlane and run this script again."
                echo "Or use cloud build: ./build-dev-client.sh simulator"
                exit 1
            fi
        fi
    fi
    
    if [ "$choice" == "2" ]; then
        echo ""
        echo "🔨 Starting local build..."
        echo "   Fastlane: $FASTLANE_VERSION"
        eas build --profile simulator --platform ios --local
    else
        echo ""
        echo "☁️  Starting cloud build..."
        echo "   Monitor progress at: https://expo.dev/accounts/$(eas whoami)/projects/richesreach-ai/builds"
        echo "   This will take 5-10 minutes..."
        eas build --profile simulator --platform ios
    fi
else
    echo "📱 Building for physical device"
    eas build --profile development --platform ios
fi

echo ""
echo "✅ Build complete!"
echo ""
echo "Next steps:"
echo "  1. Download the build from: https://expo.dev/accounts/$(eas whoami)/projects/richesreach-ai/builds"
echo "  2. Extract the .tar.gz file"
echo "  3. Install on simulator:"
echo "     xcrun simctl install booted /path/to/RichesReach.app"
echo ""
echo "Or use the install script: ./install-dev-client.sh <path-to-app>"

