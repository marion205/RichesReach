#!/usr/bin/env bash
# Build iOS development client

set -e

echo "🚀 Building iOS development client..."
echo ""
echo "This will:"
echo "  1. Install CocoaPods dependencies (if needed)"
echo "  2. Build the iOS app"
echo "  3. Install it on the simulator"
echo ""
echo "Press Ctrl+C to cancel, or wait 10 seconds..."
sleep 10

cd /Users/marioncollins/RichesReach/mobile

# Build and run on iOS simulator
npx expo run:ios

echo ""
echo "✅ Development client built and installed!"
echo "Now you can run: npm start"

