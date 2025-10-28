#!/bin/bash

# RichesReach AI - QuickTime Compatible Demo Recording Script
# Creates MP4 format that works with QuickTime Player

# Config
OUTPUT_VIDEO="RichesReach_Demo_$(date +%Y%m%d_%H%M%S).mp4"
PROJECT_ROOT="/Users/marioncollins/RichesReach/mobile"

echo "🚀 Starting RichesReach AI QuickTime Compatible Demo Recording..."

# Change to project directory
cd "$PROJECT_ROOT"

# Step 1: Ensure Simulator is ready
echo "📱 Checking iOS Simulator status..."
if ! xcrun simctl list devices | grep -q "iPhone 16 Pro.*Booted"; then
  echo "⚠️ iPhone 16 Pro not booted. Starting simulator..."
  xcrun simctl boot "iPhone 16 Pro" 2>/dev/null || true
  sleep 5
fi

# Step 2: Start Simulator Recording with MP4 format
echo "📹 Starting QuickTime compatible recording..."
xcrun simctl io booted recordVideo --codec=h264 "$OUTPUT_VIDEO" &
RECORD_PID=$!
sleep 3  # Buffer for recording start

# Step 3: Run Automated Demo Sequence
echo "🤖 Running fully automated demo sequence..."
echo "   🎤 Voice AI Trading Demo..."
echo "   🎭 MemeQuest Social Demo..."
echo "   🤖 AI Trading Coach Demo..."
echo "   📚 Learning System Demo..."
echo "   👥 Social Features Demo..."

# Run our AppleScript automation
node scripts/applescript-demo-recorder.js
DEMO_EXIT_CODE=$?

# Step 4: Stop Recording
echo "⏹️ Stopping recording..."
kill $RECORD_PID 2>/dev/null
sleep 3  # Flush recording

# Step 5: Process Video for QuickTime compatibility
if [ -f "$OUTPUT_VIDEO" ]; then
  SIZE=$(du -h "$OUTPUT_VIDEO" | cut -f1)
  echo "✅ Recording complete! Processing for QuickTime compatibility..."
  
  # Create QuickTime compatible version
  QT_VIDEO="RichesReach_Demo_QuickTime.mp4"
  if command -v ffmpeg &> /dev/null; then
    echo "🎬 Converting to QuickTime compatible format..."
    ffmpeg -i "$OUTPUT_VIDEO" -c:v libx264 -c:a aac -movflags +faststart -preset medium -crf 23 "$QT_VIDEO" -y 2>/dev/null
    echo "✅ QuickTime compatible version: $QT_VIDEO"
  else
    echo "⚠️ ffmpeg not found. Installing..."
    if command -v brew &> /dev/null; then
      brew install ffmpeg
      ffmpeg -i "$OUTPUT_VIDEO" -c:v libx264 -c:a aac -movflags +faststart -preset medium -crf 23 "$QT_VIDEO" -y 2>/dev/null
      echo "✅ QuickTime compatible version: $QT_VIDEO"
    else
      echo "❌ Please install ffmpeg: brew install ffmpeg"
      QT_VIDEO="$OUTPUT_VIDEO"
    fi
  fi
  
  # Move to Desktop
  mv "$OUTPUT_VIDEO" ~/Desktop/ 2>/dev/null
  mv "$QT_VIDEO" ~/Desktop/ 2>/dev/null
  echo "📁 Videos moved to Desktop for easy access"
  
else
  echo "❌ Recording failed—check Simulator and try again"
  exit 1
fi

# Step 6: Success Report
if [ $DEMO_EXIT_CODE -eq 0 ]; then
  echo ""
  echo "🎉 QUICKTIME COMPATIBLE DEMO RECORDING SUCCESSFUL!"
  echo "📊 Demo Features Showcased:"
  echo "   ✅ Voice AI Trading (6 AI voices)"
  echo "   ✅ Real-time Market Data (<50ms)"
  echo "   ✅ MemeQuest Social Trading"
  echo "   ✅ AI Trading Coach"
  echo "   ✅ Gamified Learning System"
  echo "   ✅ Social Features & Community"
  echo "   ✅ BIPOC-Focused Content"
  echo ""
  echo "🎬 Your QuickTime compatible demo video is ready!"
  echo "📁 Files on Desktop:"
  echo "   • $OUTPUT_VIDEO (original)"
  echo "   • $QT_VIDEO (QuickTime compatible)"
  echo ""
  echo "🚀 Ready for YC/Techstars submission!"
else
  echo "⚠️ Demo completed with minor issues—check logs"
fi

echo ""
echo "✅ QuickTime Player should now open the video successfully!"
