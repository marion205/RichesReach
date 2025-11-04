#!/usr/bin/env bash
# Build iOS app using Expo (handles CocoaPods automatically)

set -e

cd /Users/marioncollins/RichesReach/mobile

echo "🚀 Building iOS development client..."
echo ""
echo "This will:"
echo "  1. Handle CocoaPods automatically"
echo "  2. Build the iOS app"
echo "  3. Install it on the simulator"
echo ""

# Set locale
export LANG=en_US.UTF-8
export LC_ALL=en_US.UTF-8

# Build and run
npx expo run:ios

echo ""
echo "✅ Build complete!"

