#!/bin/bash

# Quick automated demo - uses manual recorder with guided instructions
# Since Detox needs additional setup, this provides immediate demo capability

cd "$(dirname "$0")"

echo "🎬 RichesReach AI - Quick Demo Recorder"
echo "========================================"
echo ""
echo "This will record your screen while you navigate the app."
echo "The app is already running in the simulator - just navigate through the tabs!"
echo ""

# Start recording
OUTPUT_VIDEO="$HOME/Desktop/RichesReach_AutoDemo_$(date +%Y%m%d_%H%M%S).mov"
echo "📹 Starting screen recording..."
echo "   Recording to: $OUTPUT_VIDEO"
echo ""

# Record simulator
xcrun simctl io booted recordVideo --codec=h264 --force "$OUTPUT_VIDEO" &
RECORD_PID=$!
echo $RECORD_PID > /tmp/demo_record_pid.txt
sleep 2

echo "⏺️  Recording started!"
echo ""
echo "📋 Navigate through these tabs in order:"
echo "   1. Home Tab (Voice AI Trading) - Show voice features"
echo "   2. Invest Tab (MemeQuest) - Show social trading"
echo "   3. Learn Tab - Show learning system"
echo "   4. Community Tab - Show social features"
echo ""
echo "⏱️  Recording for 60 seconds..."
echo "   (You can navigate at your own pace)"
echo ""

# Record for 60 seconds
sleep 60

# Stop recording
echo ""
echo "⏹️  Stopping recording..."
kill $RECORD_PID 2>/dev/null
rm -f /tmp/demo_record_pid.txt
sleep 3

if [ -f "$OUTPUT_VIDEO" ]; then
  SIZE=$(du -h "$OUTPUT_VIDEO" 2>/dev/null | cut -f1)
  echo ""
  echo "✅ Demo complete!"
  echo "📹 Video saved: $OUTPUT_VIDEO"
  echo "   Size: $SIZE"
  echo ""
  echo "✅ You can now open it with QuickTime Player!"
else
  echo "❌ Recording failed"
  exit 1
fi

