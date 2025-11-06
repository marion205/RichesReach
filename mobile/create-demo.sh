#!/bin/bash

# RichesReach AI - Manual Demo Recorder with Screen Recording
# Records your screen while you navigate the app manually

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR/mobile" 2>/dev/null || cd "$SCRIPT_DIR"

echo "🎬 RichesReach AI - Manual Demo Recorder"
echo "=========================================="
echo ""

# Check if simulator is running
SIMULATOR_BOOTED=$(xcrun simctl list devices | grep -c "Booted" || echo "0")
if [ "$SIMULATOR_BOOTED" -eq "0" ]; then
  echo "📱 Starting iOS Simulator..."
  open -a Simulator
  sleep 5
  echo "✅ Simulator started"
fi

# Ensure Metro bundler is running
if ! lsof -Pi :8081 -sTCP:LISTEN -t >/dev/null 2>&1 ; then
  echo "🚀 Starting Metro bundler..."
  cd "$SCRIPT_DIR/mobile" 2>/dev/null || cd "$SCRIPT_DIR"
  npm start > /dev/null 2>&1 &
  METRO_PID=$!
  sleep 5
  echo "✅ Metro bundler started (PID: $METRO_PID)"
fi

# Start screen recording
OUTPUT_VIDEO="$HOME/Desktop/RichesReach_Demo_$(date +%Y%m%d_%H%M%S).mov"
echo ""
echo "📹 Starting screen recording..."
echo "   Recording to: $OUTPUT_VIDEO"
echo ""
echo "📋 Demo Instructions:"
echo "   1. Navigate through the tabs in the simulator:"
echo "      - Home (Voice AI)"
echo "      - Invest (MemeQuest)"
echo "      - Learn (Learning System)"
echo "      - Community (Social Features)"
echo "   2. Show key features in each tab"
echo "   3. Press Ctrl+C when done to stop recording"
echo ""

# Record simulator screen
xcrun simctl io booted recordVideo "$OUTPUT_VIDEO" &
RECORD_PID=$!

echo "⏺️  Recording started! Navigate the app now..."
echo "   Press Ctrl+C to stop recording when done"
echo ""

# Wait for user to stop (Ctrl+C)
trap "echo ''; echo '⏹️  Stopping recording...'; kill $RECORD_PID 2>/dev/null; sleep 2; echo '✅ Recording stopped'; exit 0" INT

# Keep script running until Ctrl+C
while true; do
  sleep 1
done

