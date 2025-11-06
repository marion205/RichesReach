#!/bin/bash

# RichesReach AI - Manual Demo Recording Helper
# This script helps you record a demo manually with proper setup

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "🎬 RichesReach AI - Manual Demo Recording Helper"
echo "================================================"
echo ""

# Check if simulator is running
if ! xcrun simctl list devices | grep -q "Booted"; then
  echo "📱 Starting iOS Simulator..."
  xcrun simctl boot "iPhone 16 Pro" 2>/dev/null || open -a Simulator
  sleep 5
fi

# Start the app
echo "🚀 Starting RichesReach app..."
if [ -f "node_modules/.bin/expo" ]; then
  echo "   Starting Expo dev server..."
  npm start &
  EXPO_PID=$!
  sleep 10
  echo "   App should be running in simulator now"
else
  echo "   Please start the app manually: npm start"
fi

# Start recording
OUTPUT_VIDEO="RichesReach_Demo_Manual_$(date +%Y%m%d_%H%M%S).mov"
echo ""
echo "📹 Starting screen recording..."
echo "   Recording to: $OUTPUT_VIDEO"
echo ""
xcrun simctl io booted recordVideo "$OUTPUT_VIDEO" &
RECORD_PID=$!
sleep 2

echo "🎬 RECORDING STARTED!"
echo ""
echo "📋 Demo Flow to Follow:"
echo "   ====================="
echo "   1. 🎤 Voice AI Trading"
echo "      - Tap 'Voice AI' tab"
echo "      - Select 'Nova' voice"
echo "      - Tap voice orb"
echo "      - Execute a trade"
echo ""
echo "   2. 🎭 MemeQuest"
echo "      - Tap 'MemeQuest' tab"
echo "      - Select 'Frog Template'"
echo "      - Tap 'Animate'"
echo "      - Send a tip"
echo ""
echo "   3. 🤖 AI Trading Coach"
echo "      - Tap 'Coach' tab"
echo "      - Select a strategy"
echo "      - Execute trade"
echo ""
echo "   4. 📚 Learning System"
echo "      - Tap 'Learning' tab"
echo "      - Start quiz"
echo "      - Answer questions"
echo ""
echo "   5. 👥 Social Features"
echo "      - Tap 'Community' tab"
echo "      - Join a circle"
echo "      - Send a message"
echo ""
echo "⏸️  When finished, press Ctrl+C to stop recording"
echo ""

# Wait for user to finish
trap "echo ''; echo '⏹️ Stopping recording...'; kill $RECORD_PID 2>/dev/null; sleep 3; [ -f \"$OUTPUT_VIDEO\" ] && mv \"$OUTPUT_VIDEO\" ~/Desktop/ && echo '✅ Video saved to Desktop'; kill $EXPO_PID 2>/dev/null; exit 0" INT

# Keep script running
wait

