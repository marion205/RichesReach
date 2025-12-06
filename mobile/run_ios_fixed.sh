#!/bin/bash
# Workaround for Expo's iOS 26.0 runtime detection issue

set -e

cd "$(dirname "$0")"

echo "🔧 Bypassing Expo simulator detection issue..."
echo ""

# Ensure simulator is booted
BOOTED=$(xcrun simctl list devices | grep "(Booted)" | head -1)
if [ -z "$BOOTED" ]; then
  echo "📱 Booting iPhone 15 Pro..."
  xcrun simctl boot "iPhone 15 Pro" 2>/dev/null || true
  open -a Simulator
  sleep 3
fi

# Get the booted device UUID
DEVICE_UUID=$(xcrun simctl list devices | grep "(Booted)" | grep -oE '[A-F0-9]{8}-[A-F0-9]{4}-[A-F0-9]{4}-[A-F0-9]{4}-[A-F0-9]{12}' | head -1)

if [ -z "$DEVICE_UUID" ]; then
  echo "❌ No booted simulator found. Please boot one manually:"
  echo "   xcrun simctl boot 'iPhone 15 Pro'"
  echo "   open -a Simulator"
  exit 1
fi

echo "✅ Using device: $DEVICE_UUID"
echo ""

# Use xcodebuild directly to bypass Expo's detection
echo "🔨 Building with Xcode (bypassing Expo detection)..."
echo ""

# Check if ios directory exists
if [ ! -d "ios" ]; then
  echo "❌ iOS directory not found. Generating native projects..."
  npx expo prebuild --platform ios
fi

# Build and run using xcodebuild
cd ios

# Install pods if needed
if [ ! -d "Pods" ]; then
  echo "📦 Installing CocoaPods..."
  pod install
fi

echo "🔨 Building app..."
xcodebuild \
  -workspace RichesReach.xcworkspace \
  -scheme RichesReach \
  -configuration Debug \
  -sdk iphonesimulator \
  -destination "id=$DEVICE_UUID" \
  build \
  2>&1 | grep -E "(error|warning|BUILD)" | head -20

echo ""
echo "📱 Installing app on simulator..."
xcrun simctl install booted ../ios/build/Build/Products/Debug-iphonesimulator/RichesReach.app 2>/dev/null || {
  echo "⚠️  Install failed, trying to find app in DerivedData..."
  APP_PATH=$(find ~/Library/Developer/Xcode/DerivedData -name "RichesReach.app" -type d | head -1)
  if [ -n "$APP_PATH" ]; then
    xcrun simctl install booted "$APP_PATH"
  else
    echo "❌ Could not find built app"
    exit 1
  fi
}

echo "🚀 Launching app..."
xcrun simctl launch booted com.richesreach.app

echo ""
echo "✅ App should be launching!"
echo "   Now start Metro bundler in another terminal:"
echo "   cd mobile && npx expo start"

