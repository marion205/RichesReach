#!/usr/bin/env bash

# Local iOS build script with proper PATH setup

set -e

export PATH="/opt/homebrew/bin:$HOME/.local/bin:$PATH"
export LANG=en_US.UTF-8

cd /Users/marioncollins/RichesReach/mobile

echo "🔧 Local iOS Build Script"
echo "========================"
echo ""

# Verify CocoaPods is accessible
if ! command -v pod &> /dev/null; then
  echo "❌ CocoaPods not found in PATH"
  echo "Trying to use: /opt/homebrew/bin/pod"
  if [ -f "/opt/homebrew/bin/pod" ]; then
    echo "✅ Found at /opt/homebrew/bin/pod"
  else
    echo "❌ CocoaPods not found. Please install: brew install cocoapods"
    exit 1
  fi
fi

echo "📱 Building for iPhone 16 Pro..."
echo "This will take 5-10 minutes for the first build"
echo ""

# Build with Expo
npx expo run:ios --device "iPhone 16 Pro"

echo ""
echo "✅ Build complete!"
echo ""
echo "Next: Start Metro with dev client:"
echo "  npx expo start --dev-client"

