#!/bin/bash
# RichesReach Mobile - Expo Start Script
# Ensures we're in the correct directory and starts Expo with cache clear

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Verify we're in the right place
if [ ! -f "package.json" ]; then
    echo "❌ Error: package.json not found!"
    echo "   Current directory: $(pwd)"
    echo "   Expected: mobile/ directory with package.json"
    exit 1
fi

if [ ! -f "app.json" ]; then
    echo "❌ Error: app.json not found!"
    echo "   Current directory: $(pwd)"
    exit 1
fi

echo "✅ Starting Expo from: $(pwd)"
echo "📦 Project: $(grep '"name"' package.json | head -1 | cut -d'"' -f4)"
echo ""

# Check if environment variable is set for physical device
if [ -z "$EXPO_PUBLIC_API_BASE_URL" ]; then
    echo "⚠️  EXPO_PUBLIC_API_BASE_URL not set"
    echo "   For physical devices, set: export EXPO_PUBLIC_API_BASE_URL=http://192.168.1.240:8000"
    echo ""
fi

# Start Expo with cache clear
npx expo start --clear

