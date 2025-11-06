#!/bin/bash

# RichesReach AI - Automated Demo with Screen Recording
# Uses Detox to automate app interactions and records the screen

set -e

cd "$(dirname "$0")"

echo "🎬 RichesReach AI - Automated Demo Recorder"
echo "============================================"
echo ""

# Find the app
APP_PATH=$(find ios -name "RichesReach.app" -type d 2>/dev/null | head -1)
if [ -z "$APP_PATH" ]; then
  echo "❌ App not found. Please build in Xcode first (Product → Build)"
  exit 1
fi
echo "✅ Found app: $APP_PATH"

# Ensure simulator is running
SIMULATOR_BOOTED=$(xcrun simctl list devices | grep -c "Booted" || echo "0")
if [ "$SIMULATOR_BOOTED" -eq "0" ]; then
  echo "📱 Starting iOS Simulator..."
  open -a Simulator
  sleep 5
fi

# Start screen recording
OUTPUT_VIDEO="$HOME/Desktop/RichesReach_AutoDemo_$(date +%Y%m%d_%H%M%S).mov"
echo ""
echo "📹 Starting screen recording..."
echo "   Recording to: $OUTPUT_VIDEO"
xcrun simctl io booted recordVideo --codec=h264 --force "$OUTPUT_VIDEO" &
RECORD_PID=$!
sleep 3

echo ""
echo "🤖 Running automated Detox test..."
echo "   This will interact with your app automatically"
echo ""

# Run Detox test (will try to run, may have issues but will record screen)
npm run test:e2e:ios -- --testNamePattern="Voice Trade" 2>&1 | tee /tmp/detox-demo.log || {
  echo ""
  echo "⚠️  Detox test had issues, but screen was recorded"
}

# Wait a bit for any final animations
sleep 3

# Stop recording
echo ""
echo "⏹️  Stopping recording..."
kill $RECORD_PID 2>/dev/null
sleep 3

# Check if video was created
if [ -f "$OUTPUT_VIDEO" ]; then
  SIZE=$(du -h "$OUTPUT_VIDEO" 2>/dev/null | cut -f1)
  echo ""
  echo "✅ Demo complete!"
  echo "📹 Video saved: $OUTPUT_VIDEO"
  echo "   Size: $SIZE"
  echo ""
  
  # Check if Detox actually ran successfully
  if grep -q "PASS\|✅" /tmp/detox-demo.log 2>/dev/null; then
    echo "🎉 Automated demo ran successfully!"
  else
    echo "⚠️  Detox had issues, but video was recorded"
    echo "   You can manually navigate the app while recording using:"
    echo "   ./record-demo.sh"
  fi
else
  echo "❌ Recording failed"
  exit 1
fi

