#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"

echo "🚀 Quick Test Setup - Getting simulator ready..."
echo ""

# 1. Check Xcode
echo "📱 Checking Xcode..."
if ! command -v xcodebuild &> /dev/null; then
  echo "❌ Xcode not found. Please install Xcode from App Store."
  exit 1
fi
XCODE_VERSION=$(xcodebuild -version | head -1)
echo "✅ $XCODE_VERSION"

# 2. Check if iOS Simulator is available
echo ""
echo "📱 Checking iOS Simulator..."
if ! xcrun simctl list devices available | grep -q "iPhone"; then
  echo "⚠️  No iOS simulators found. Opening Simulator app..."
  open -a Simulator
  sleep 3
fi

# 3. Verify Pods are installed
echo ""
echo "📦 Checking CocoaPods..."
if [ ! -d "ios/Pods" ] || [ ! -f "ios/Podfile.lock" ]; then
  echo "⚠️  Pods not installed. Installing..."
  cd ios
  pod install
  cd ..
else
  echo "✅ Pods already installed"
fi

# 4. Check for booted simulator
echo ""
echo "🔍 Finding booted simulator..."
BOOTED=$(xcrun simctl list devices | grep "(Booted)" | head -1 | sed 's/.*(\(.*\)) (Booted).*/\1/' || echo "")
if [ -z "$BOOTED" ]; then
  echo "⚠️  No booted simulator. Booting iPhone 16 Pro..."
  xcrun simctl boot "iPhone 16 Pro" 2>/dev/null || xcrun simctl boot "iPhone 15 Pro" 2>/dev/null || {
    # Get first available iPhone
    FIRST_IPHONE=$(xcrun simctl list devices available | grep "iPhone" | head -1 | sed 's/.*(\(.*\)) (.*/\1/')
    if [ -n "$FIRST_IPHONE" ]; then
      echo "   Booting $FIRST_IPHONE..."
      xcrun simctl boot "$FIRST_IPHONE"
    fi
  }
  open -a Simulator
  sleep 5
  BOOTED=$(xcrun simctl list devices | grep "(Booted)" | head -1 | sed 's/.*(\(.*\)) (Booted).*/\1/' || echo "")
fi

if [ -z "$BOOTED" ]; then
  echo "❌ Could not boot simulator. Please boot manually: open -a Simulator"
  exit 1
fi
echo "✅ Simulator ready: $BOOTED"

# 5. Check if app is installed
echo ""
echo "🔍 Checking if app is installed..."
BUNDLE_ID="com.richesreach.app"
APP_CONTAINER=$(xcrun simctl get_app_container booted "$BUNDLE_ID" 2>/dev/null || echo "")
if [ -z "$APP_CONTAINER" ]; then
  echo "⚠️  App not installed. You'll need to build it."
  echo ""
  echo "📋 Next steps:"
  echo "   1. Run: npx expo run:ios"
  echo "   2. Or use your EAS dev build"
  echo ""
else
  echo "✅ App is installed"
fi

# 6. Kill any existing Metro bundlers
echo ""
echo "🧹 Cleaning up old Metro processes..."
pkill -f "expo start" || true
pkill -f "metro" || true
sleep 2

# 7. Check Node modules
echo ""
echo "📦 Checking dependencies..."
if [ ! -d "node_modules" ]; then
  echo "⚠️  node_modules not found. Run: npm install"
  exit 1
fi
echo "✅ Dependencies installed"

# 8. Verify Skia is installed
echo ""
echo "🎨 Verifying Skia..."
if ! npm list @shopify/react-native-skia &> /dev/null; then
  echo "⚠️  Skia not installed. Installing..."
  npm install @shopify/react-native-skia
fi
echo "✅ Skia installed"

echo ""
echo "✅ Setup complete!"
echo ""
echo "📋 To start testing:"
echo ""
echo "   Option 1: Build and run locally"
echo "   → npx expo run:ios"
echo ""
echo "   Option 2: Use EAS dev build + Metro"
echo "   → npx expo start --dev-client"
echo "   (Then launch app from simulator)"
echo ""
echo "   Option 3: Install latest EAS build"
echo "   → ./install_latest_eas_sim.sh"
echo "   → npx expo start --dev-client"
echo ""

