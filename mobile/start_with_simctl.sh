#!/bin/bash
# Workaround: Use simctl directly to bypass Simulator app crash

set -e

cd "$(dirname "$0")"

echo "🔧 Starting app using simctl (bypassing Simulator app)"
echo ""

# Step 1: Boot simulator if not already booted
BOOTED=$(xcrun simctl list devices | grep "(Booted)" | head -1)
if [ -z "$BOOTED" ]; then
  echo "📱 Booting iPhone 15 Pro..."
  xcrun simctl boot "iPhone 15 Pro" 2>/dev/null || {
    echo "⚠️  Could not boot iPhone 15 Pro, trying iPhone 15..."
    xcrun simctl boot "iPhone 15" 2>/dev/null || true
  }
  sleep 2
fi

DEVICE_UUID=$(xcrun simctl list devices | grep "(Booted)" | grep -oE '[A-F0-9]{8}-[A-F0-9]{4}-[A-F0-9]{4}-[A-F0-9]{4}-[A-F0-9]{12}' | head -1)

if [ -z "$DEVICE_UUID" ]; then
  echo "❌ No booted simulator found"
  exit 1
fi

echo "✅ Simulator booted: $DEVICE_UUID"
echo ""

# Step 2: Start Expo Metro bundler in background
echo "🚀 Starting Expo Metro bundler..."
npx expo start --no-dev --minify > /tmp/expo-metro.log 2>&1 &
EXPO_PID=$!
echo "   Metro PID: $EXPO_PID"
echo "   Logs: tail -f /tmp/expo-metro.log"
echo ""

# Wait for Metro to start
sleep 5

# Step 3: Get the Metro URL
METRO_URL="http://localhost:8081"

echo "📱 Metro should be running at $METRO_URL"
echo ""
echo "⚠️  Note: Since Simulator app is crashing, you'll need to:"
echo "   1. Use Expo Go app on the simulator (if installed)"
echo "   2. Or build the app and install via simctl"
echo ""
echo "To install Expo Go on simulator:"
echo "   xcrun simctl install booted /path/to/ExpoGo.app"
echo ""
echo "To build and install your app:"
echo "   npx expo run:ios --device $DEVICE_UUID"
echo ""

# Keep script running
echo "Press Ctrl+C to stop Metro..."
wait $EXPO_PID

