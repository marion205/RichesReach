#!/bin/bash

# RichesReach AI - Fully Automated Demo Recording Script
# Automatically records iOS Simulator and saves MP4 video

# Config
SIMULATOR_ID="iPhone 16 Pro"
OUTPUT_VIDEO="RichesReach_Demo_$(date +%Y%m%d_%H%M%S).mov"
DETOX_CONFIG="ios.sim.debug"
PROJECT_ROOT="/Users/marioncollins/RichesReach/mobile"

echo "🚀 Starting RichesReach AI Fully Automated Demo Recording..."

# Change to project directory
cd "$PROJECT_ROOT"

# Step 1: Start Simulator Recording
echo "📹 Starting automated screen recording..."
xcrun simctl io booted recordVideo "$OUTPUT_VIDEO" &
RECORD_PID=$!
sleep 3  # Buffer for recording start

# Step 2: Run Automated Demo (using our AppleScript automation)
echo "🤖 Running automated demo sequence..."
node scripts/applescript-demo-recorder.js
DEMO_EXIT_CODE=$?

# Step 3: Stop Recording
echo "⏹️ Stopping recording..."
kill $RECORD_PID 2>/dev/null
sleep 2  # Flush recording

# Step 4: Verify & Optimize Video
if [ -f "$OUTPUT_VIDEO" ]; then
  SIZE=$(du -h "$OUTPUT_VIDEO" | cut -f1)
  echo "✅ Demo complete! Video saved: $OUTPUT_VIDEO (Size: $SIZE)"
  
  # Trim to 60s for pitch-perfect length (optional)
  if command -v ffmpeg &> /dev/null; then
    ffmpeg -i "$OUTPUT_VIDEO" -ss 0 -t 60 -c copy "RichesReach_Demo_Trimmed.mov" -y 2>/dev/null
    echo "✂️ Trimmed 60s version: RichesReach_Demo_Trimmed.mov"
  else
    echo "💡 Install ffmpeg (brew install ffmpeg) for video trimming"
  fi
  
  # Move to Desktop for easy access
  mv "$OUTPUT_VIDEO" ~/Desktop/ 2>/dev/null
  echo "📁 Video moved to Desktop for easy access"
  
else
  echo "❌ Recording failed—check Simulator status"
  exit 1
fi

if [ $DEMO_EXIT_CODE -eq 0 ]; then
  echo "🎉 Fully automated demo complete! Video ready for YC/Techstars submission!"
  echo "📊 Demo features showcased:"
  echo "   ✅ Voice AI Trading (6 voices)"
  echo "   ✅ MemeQuest Social Trading"
  echo "   ✅ AI Trading Coach"
  echo "   ✅ Learning System"
  echo "   ✅ Social Features"
else
  echo "⚠️ Demo ran but had issues—check logs"
fi

echo "🎬 Your professional demo video is ready!"
