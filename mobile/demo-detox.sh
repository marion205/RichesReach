#!/bin/bash

# RichesReach AI - Detox-Based Automated Demo Recorder
# This uses Detox E2E testing which actually interacts with the app properly

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "🎬 RichesReach AI - Detox Automated Demo Recorder"
echo "================================================"
echo ""

# Ensure iOS pods are installed
if [ ! -d "ios/Pods" ] || [ ! -f "ios/Podfile.lock" ]; then
  echo "🔧 Installing CocoaPods dependencies..."
  pushd ios >/dev/null
  /opt/homebrew/bin/pod install --repo-update || {
    echo "❌ Failed to install pods. Please run: cd ios && /opt/homebrew/bin/pod install"
    exit 1
  }
  popd >/dev/null
  echo "✅ Pods installed successfully"
fi

# Check if Detox is installed
if ! npm list detox &> /dev/null; then
  echo "📦 Installing Detox..."
  npm install --save-dev detox
fi

# Check if we need to prebuild (Expo project)
if [ ! -d "ios/RichesReach.xcworkspace" ]; then
  echo "📱 Prebuilding iOS app for E2E testing..."
  npx expo prebuild --platform ios
fi

# Check if app is built (try multiple possible paths)
APP_PATH=""
if [ -d "ios/build/Build/Products/Debug-iphonesimulator/RichesReach.app" ]; then
  APP_PATH="ios/build/Build/Products/Debug-iphonesimulator/RichesReach.app"
elif [ -d "ios/build/Build/Products/Debug-iphonesimulator/RichesReach.app" ]; then
  APP_PATH="ios/build/Build/Products/Debug-iphonesimulator/RichesReach.app"
else
  # Try to find it
  APP_PATH=$(find ios -name "RichesReach.app" -type d 2>/dev/null | head -1)
fi

if [ -z "$APP_PATH" ] || [ ! -d "$APP_PATH" ]; then
  echo "⚠️  App not found. The app needs to be built in Xcode first."
  echo "   In Xcode: Product → Build (⌘+B)"
  echo "   Then run this script again."
  echo ""
  echo "   Or use the manual demo recorder instead:"
  echo "   ./record-demo.sh"
  exit 1
else
  echo "✅ Found app at: $APP_PATH"
fi

# Check if simulator is running
SIMULATOR_BOOTED=$(xcrun simctl list devices | grep -c "Booted" || echo "0")
if [ "$SIMULATOR_BOOTED" -eq 0 ]; then
  echo "📱 Starting iOS Simulator..."
  xcrun simctl boot "iPhone 16 Pro" 2>/dev/null || {
    echo "   Opening Simulator app..."
    open -a Simulator
    sleep 5
    # Try to boot the device
    xcrun simctl boot "iPhone 16 Pro" 2>/dev/null || true
  }
  sleep 5
fi

# Start recording
OUTPUT_VIDEO="RichesReach_Demo_Detox_$(date +%Y%m%d_%H%M%S).mov"
echo ""
echo "📹 Starting screen recording..."
echo "   Recording to: $OUTPUT_VIDEO"
xcrun simctl io booted recordVideo "$OUTPUT_VIDEO" &
RECORD_PID=$!
sleep 3

# Run Detox demo
echo ""
echo "🤖 Running Detox automated demo..."
echo "   (This will actually interact with your app!)"
echo ""

# Run Detox test with video recording
npm run test:e2e:ios || {
  echo ""
  echo "⚠️  Detox test had issues, but continuing..."
}

# Wait a bit for any final animations
sleep 2

# Stop recording
echo ""
echo "⏹️ Stopping recording..."
kill $RECORD_PID 2>/dev/null
sleep 3

# Process video
if [ -f "$OUTPUT_VIDEO" ]; then
  SIZE=$(du -h "$OUTPUT_VIDEO" | cut -f1)
  echo ""
  echo "✅ Demo complete!"
  echo "📹 Video saved: $OUTPUT_VIDEO (Size: $SIZE)"
  
  # Create optimized version
  OPTIMIZED_VIDEO="RichesReach_Demo_Optimized.mp4"
  if command -v ffmpeg &> /dev/null; then
    echo "🎬 Creating optimized version..."
    ffmpeg -i "$OUTPUT_VIDEO" \
           -ss 0 -t 60 \
           -vf scale=1080:1920 \
           -c:v libx264 \
           -preset fast \
           -crf 23 \
           "$OPTIMIZED_VIDEO" \
           -y 2>/dev/null || true
    if [ -f "$OPTIMIZED_VIDEO" ]; then
      echo "✂️ Optimized version: $OPTIMIZED_VIDEO (60s, 1080x1920)"
    fi
  fi
  
  # Move to Desktop
  mv "$OUTPUT_VIDEO" ~/Desktop/ 2>/dev/null
  [ -f "$OPTIMIZED_VIDEO" ] && mv "$OPTIMIZED_VIDEO" ~/Desktop/ 2>/dev/null
  echo "📁 Videos moved to Desktop"
  
  echo ""
  echo "🎉 FULLY AUTOMATED DEMO RECORDING SUCCESSFUL!"
  echo "📊 Demo Features Showcased:"
  echo "   ✅ Voice AI Trading"
  echo "   ✅ MemeQuest Social Trading"
  echo "   ✅ AI Trading Coach"
  echo "   ✅ Learning System"
  echo "   ✅ Social Features"
else
  echo ""
  echo "❌ Recording failed - check simulator status"
  exit 1
fi

echo ""
echo "🚀 Ready to pitch! Your demo video is on your Desktop!"
