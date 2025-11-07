#!/bin/bash
# RichesReach Mobile - Install Development Client on Simulator
# Usage: ./install-dev-client.sh [path-to-app]

set -e

APP_PATH="$1"

# If no path provided, try to find it
if [ -z "$APP_PATH" ]; then
    echo "🔍 Searching for RichesReach.app..."
    
    # Common locations
    SEARCH_PATHS=(
        "$HOME/Downloads/RichesReach.app"
        "$HOME/Downloads/*.app"
        "./RichesReach.app"
        "./*.app"
    )
    
    for path in "${SEARCH_PATHS[@]}"; do
        if [ -d "$path" ] 2>/dev/null; then
            APP_PATH="$path"
            break
        fi
    done
    
    if [ -z "$APP_PATH" ]; then
        echo "❌ Error: Could not find RichesReach.app"
        echo ""
        echo "Usage: ./install-dev-client.sh /path/to/RichesReach.app"
        echo ""
        echo "Or extract your build first:"
        echo "  tar -xzf path/to/your-build.tar.gz"
        exit 1
    fi
fi

# Verify it's an app bundle
if [ ! -d "$APP_PATH" ] || [ ! -f "$APP_PATH/Info.plist" ]; then
    echo "❌ Error: $APP_PATH is not a valid .app bundle"
    exit 1
fi

echo "📱 Installing RichesReach Development Client"
echo "   App: $APP_PATH"
echo ""

# Check if simulator is running
BOOTED=$(xcrun simctl list devices | grep "Booted" | head -1 | sed 's/.*(\([^)]*\)).*/\1/')

if [ -z "$BOOTED" ]; then
    echo "⚠️  No iOS Simulator is running"
    echo "   Opening Simulator..."
    open -a Simulator
    sleep 5
    BOOTED=$(xcrun simctl list devices | grep "Booted" | head -1 | sed 's/.*(\([^)]*\)).*/\1/')
    
    if [ -z "$BOOTED" ]; then
        echo "❌ Error: Could not start simulator"
        exit 1
    fi
fi

echo "✅ Simulator running: $BOOTED"
echo ""

# Install the app
echo "📦 Installing app..."
xcrun simctl install "$BOOTED" "$APP_PATH"

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Development client installed successfully!"
    echo ""
    echo "Next steps:"
    echo "  1. Start Expo: ./start.sh"
    echo "  2. Press 'i' to launch on iOS Simulator"
    echo "  3. The dev client will connect automatically"
else
    echo ""
    echo "❌ Installation failed"
    exit 1
fi

