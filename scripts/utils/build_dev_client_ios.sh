#!/bin/bash
# Build and install iOS Development Client for RichesReach
# This enables all native features including WebRTC, AR, and voice

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MOBILE_DIR="$SCRIPT_DIR/mobile"

cd "$MOBILE_DIR"

echo "🔨 Building iOS Development Client"
echo "=================================="
echo ""
echo "This will:"
echo "  1. Generate native iOS project files"
echo "  2. Install CocoaPods dependencies"
echo "  3. Build and install the app on iOS simulator"
echo ""
echo "⚠️  This may take 10-15 minutes the first time"
echo ""

# Check if Xcode is installed
if ! command -v xcodebuild &> /dev/null; then
    echo "❌ Xcode not found. Please install Xcode from the App Store."
    exit 1
fi

# Check if simulator is available
if ! xcrun simctl list devices available | grep -q "iPhone"; then
    echo "❌ No iOS simulators found. Please install simulators in Xcode."
    exit 1
fi

# Install dependencies if needed
if [ ! -d "node_modules" ]; then
    echo "📦 Installing npm dependencies..."
    npm install
fi

# Prebuild to generate native files
echo ""
echo "📱 Prebuilding native iOS project..."
npx expo prebuild --platform ios --clean

# Install CocoaPods
if [ -d "ios" ]; then
    cd ios
    echo ""
    echo "📦 Installing CocoaPods dependencies..."
    if [ -f "Podfile" ]; then
        pod install
    else
        echo "❌ Podfile not found. Prebuild may have failed."
        exit 1
    fi
    cd ..
fi

# Build and run on iOS simulator
echo ""
echo "🚀 Building and installing on iOS simulator..."
echo "   This will automatically launch the simulator"
echo ""

npx expo run:ios

echo ""
echo "✅ Development client built and installed!"
echo ""
echo "📱 Next steps:"
echo "   1. The simulator should now be running"
echo "   2. Run: npm start (or ./start_all_features.sh)"
echo "   3. The app will connect to the Metro bundler"
echo "   4. All native features (WebRTC, AR, voice) will work!"
echo ""

