#!/bin/bash

# RichesReach AI - Fixed Demo Screen Recorder
# Uses proper recording format that QuickTime can open

set -e

cd "$(dirname "$0")"

echo "🎬 RichesReach AI - Demo Recorder (Fixed)"
echo "=========================================="
echo ""

# Stop any existing recordings first
pkill -f "recordVideo" 2>/dev/null || true
sleep 1

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

# Start screen recording with proper format
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
echo "   When done, run: ./stop-recording.sh"
echo "   Or press Ctrl+C in this terminal"
echo ""
echo "⏺️  Recording started! Navigate the app now..."
echo ""

# Record simulator screen (simctl creates QuickTime-compatible MOV files)
xcrun simctl io booted recordVideo --codec=h264 --force "$OUTPUT_VIDEO" &
RECORD_PID=$!
echo $RECORD_PID > /tmp/demo_record_pid.txt
sleep 2

# Wait for user to stop
echo "   Recording in progress..."
echo "   To stop: Run './stop-recording.sh' or press Ctrl+C"
echo ""

# Keep script running until stopped
trap "echo ''; echo '⏹️  Stopping recording...'; kill $RECORD_PID 2>/dev/null; sleep 2; rm -f /tmp/demo_record_pid.txt; echo '✅ Recording stopped'; SIZE=\$(du -h \"\$OUTPUT_VIDEO\" 2>/dev/null | cut -f1); echo \"📹 Video saved: \$OUTPUT_VIDEO (\$SIZE)\"; exit 0" INT TERM

while kill -0 $RECORD_PID 2>/dev/null; do
  sleep 1
done

