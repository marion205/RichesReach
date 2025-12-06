#!/bin/bash

# Check if xcode-select is set correctly
CURRENT_PATH=$(xcode-select -p)
EXPECTED_PATH="/Volumes/ExternalSSD/Xcode.app/Contents/Developer"

if [ "$CURRENT_PATH" != "$EXPECTED_PATH" ]; then
    echo "⚠️  Xcode path not set correctly"
    echo "Current: $CURRENT_PATH"
    echo "Expected: $EXPECTED_PATH"
    echo ""
    echo "Please run first:"
    echo "  sudo xcode-select --switch /Volumes/ExternalSSD/Xcode.app/Contents/Developer"
    echo ""
    exit 1
fi

echo "✅ Xcode path is set correctly"
echo ""

# List available simulators
echo "📱 Available iOS Simulators:"
/Volumes/ExternalSSD/Xcode.app/Contents/Developer/usr/bin/simctl list devices available | grep "iPhone" | head -5
echo ""

# Start Expo
echo "🚀 Starting Expo..."
cd mobile
npm start
