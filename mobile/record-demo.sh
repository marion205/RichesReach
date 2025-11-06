#!/bin/bash

# RichesReach AI - Manual Demo Screen Recorder
# Records the iOS Simulator while you navigate the app manually

set -e

cd "$(dirname "$0")"

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
else
  echo "✅ Simulator is already running"
fi

# Ensure Metro bundler is running
if ! lsof -Pi :8081 -sTCP:LISTEN -t >/dev/null 2>&1 ; then
  echo "🚀 Starting Metro bundler..."
  npm start > /dev/null 2>&1 &
  METRO_PID=$!
  sleep 5
  echo "✅ Metro bundler started"
fi

# Start screen recording
OUTPUT_VIDEO="$HOME/Desktop/RichesReach_Demo_$(date +%Y%m%d_%H%M%S).mov"
echo ""
echo "📹 Starting screen recording..."
echo "   Recording to: $OUTPUT_VIDEO"
echo ""
echo "📋 Demo Instructions:"
echo "   Navigate through the tabs in the simulator:"
echo "   1. Home Tab (Voice AI Trading)"
echo "   2. Invest Tab (MemeQuest Social Trading)"
echo "   3. Learn Tab (Learning System)"
echo "   4. Community Tab (Social Features)"
echo ""
echo "   Press Ctrl+C when done to stop recording"
echo ""
echo "⏺️  Recording started! Navigate the app now..."
echo ""

# Record simulator screen
xcrun simctl io booted recordVideo "$OUTPUT_VIDEO" &
RECORD_PID=$!
sleep 2

# Wait for user to stop (Ctrl+C)
trap "echo ''; echo '⏹️  Stopping recording...'; kill $RECORD_PID 2>/dev/null; sleep 2; echo '✅ Recording stopped'; echo ''; echo '📹 Video saved: $OUTPUT_VIDEO'; SIZE=\$(du -h \"\$OUTPUT_VIDEO\" 2>/dev/null | cut -f1); echo \"   Size: \$SIZE\"; exit 0" INT

# Keep script running until Ctrl+C
echo "   Recording in progress... (Press Ctrl+C to stop)"
while kill -0 $RECORD_PID 2>/dev/null; do
  sleep 1
done

