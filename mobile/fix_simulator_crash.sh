#!/bin/bash
# Fix for Simulator crash: Library not loaded: SimulatorKit.framework

set -e

echo "🔧 Fixing iOS Simulator Crash Issue"
echo ""

# Step 1: Kill all Simulator processes
echo "1️⃣ Killing all Simulator processes..."
killall Simulator 2>/dev/null || true
killall com.apple.CoreSimulator.CoreSimulatorService 2>/dev/null || true
sleep 2

# Step 2: Verify Xcode installation
echo ""
echo "2️⃣ Checking Xcode installation..."
XCODE_PATH=$(xcode-select -p | sed 's|/Contents/Developer||')
if [ ! -d "$XCODE_PATH" ]; then
    echo "❌ Xcode not found at: $XCODE_PATH"
    echo "   Please run: sudo xcode-select --switch /Applications/Xcode.app/Contents/Developer"
    exit 1
fi

echo "✅ Xcode found at: $XCODE_PATH"

# Step 3: Check for SimulatorKit.framework
SIMULATOR_KIT="$XCODE_PATH/Contents/Developer/Library/PrivateFrameworks/SimulatorKit.framework"
if [ ! -d "$SIMULATOR_KIT" ]; then
    echo "❌ SimulatorKit.framework not found at: $SIMULATOR_KIT"
    echo "   This indicates a corrupted Xcode installation."
    echo "   Please reinstall Xcode or run: xcode-select --switch /Applications/Xcode.app/Contents/Developer"
    exit 1
fi

echo "✅ SimulatorKit.framework found"

# Step 4: Check for Simulator.app
SIMULATOR_APP="$XCODE_PATH/Contents/Developer/Applications/Simulator.app"
if [ ! -d "$SIMULATOR_APP" ]; then
    echo "❌ Simulator.app not found at: $SIMULATOR_APP"
    exit 1
fi

echo "✅ Simulator.app found"

# Step 5: Clear any corrupted Group Container references
echo ""
echo "3️⃣ Cleaning up Group Container references..."
rm -rf ~/Library/Group\ Containers/group.com.apple.xip.PKSignedContainer/PKSignedContainer-UnarchiveOperations/*/Xcode.app 2>/dev/null || true
echo "✅ Cleaned up"

# Step 6: Reset CoreSimulator service
echo ""
echo "4️⃣ Resetting CoreSimulator service..."
killall -9 com.apple.CoreSimulator.CoreSimulatorService 2>/dev/null || true
sleep 2

# Step 7: Launch Simulator from the correct location
echo ""
echo "5️⃣ Launching Simulator from correct location..."
open "$SIMULATOR_APP"
sleep 3

# Step 8: Verify Simulator is running
if pgrep -x Simulator > /dev/null; then
    echo "✅ Simulator is running!"
else
    echo "⚠️  Simulator may not have launched. Try manually:"
    echo "   open \"$SIMULATOR_APP\""
fi

# Step 9: Boot a device if none is booted
echo ""
echo "6️⃣ Checking for booted devices..."
BOOTED=$(xcrun simctl list devices | grep "(Booted)" | head -1)
if [ -z "$BOOTED" ]; then
    echo "📱 Booting iPhone 15 Pro..."
    xcrun simctl boot "iPhone 15 Pro" 2>/dev/null || {
        echo "⚠️  Could not boot iPhone 15 Pro, trying iPhone 15..."
        xcrun simctl boot "iPhone 15" 2>/dev/null || true
    }
    sleep 2
    BOOTED=$(xcrun simctl list devices | grep "(Booted)" | head -1)
    if [ -n "$BOOTED" ]; then
        echo "✅ Device booted: $BOOTED"
    fi
else
    echo "✅ Device already booted: $BOOTED"
fi

echo ""
echo "✅ Fix complete!"
echo ""
echo "📝 Next steps:"
echo "   1. If Simulator still crashes, you may need to:"
echo "      sudo xcode-select --switch /Applications/Xcode.app/Contents/Developer"
echo "   2. Try running your app:"
echo "      cd mobile && npx expo start --ios"
echo ""

