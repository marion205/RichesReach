#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"

echo "🚀 Quick Build & Run - Building for simulator and launching..."
echo ""

# Kill any running Metro
pkill -f "expo start" || true
pkill -f "metro" || true

# Ensure simulator is booted
BOOTED=$(xcrun simctl list devices | grep "(Booted)" | head -1 | sed 's/.*(\(.*\)) (Booted).*/\1/' || echo "")
if [ -z "$BOOTED" ]; then
  echo "📱 Booting iPhone 16 Pro..."
  xcrun simctl boot "iPhone 16 Pro" 2>/dev/null || xcrun simctl boot "iPhone 15 Pro" 2>/dev/null || {
    FIRST_IPHONE=$(xcrun simctl list devices available | grep "iPhone" | head -1 | sed 's/.*(\(.*\)) (.*/\1/')
    xcrun simctl boot "$FIRST_IPHONE" 2>/dev/null || true
  }
  open -a Simulator
  sleep 5
fi

echo "✅ Simulator ready"

# Clean DerivedData
echo ""
echo "🧹 Cleaning build cache..."
rm -rf ~/Library/Developer/Xcode/DerivedData/RichesReach-* 2>/dev/null || true
pkill -9 -x xcodebuild || true
pkill -9 -x XCBBuildService || true

# Build and run
echo ""
echo "🔨 Building and running on simulator..."
echo "   (This will take 3-5 minutes on first build)"
echo ""

npx expo run:ios --device "$BOOTED" || {
  echo ""
  echo "⚠️  Build failed. Trying without device flag..."
  npx expo run:ios
}

echo ""
echo "✅ App should be launching on simulator!"
echo "   Metro bundler will start automatically."

