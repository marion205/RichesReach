#!/bin/bash

# RichesReach AI - One-Command Automated Demo Recorder
# Just run: ./demo.sh
# That's it! No manual work needed.

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "🎬 RichesReach AI - Automated Demo Recorder"
echo "=========================================="
echo ""

# Check if simulator is running
if ! xcrun simctl list devices | grep -q "Booted"; then
  echo "📱 Starting iOS Simulator..."
  xcrun simctl boot "iPhone 16 Pro" 2>/dev/null || open -a Simulator
  sleep 5
  echo "✅ Simulator ready!"
fi

# Run the automated demo
echo ""
echo "🤖 Starting fully automated demo..."
echo "   (No manual interaction needed - sit back and relax!)"
echo ""

./working-demo-recorder.sh

echo ""
echo "🎉 Done! Your demo video is on your Desktop!"
echo "📹 Look for: RichesReach_Demo_*.mov"

