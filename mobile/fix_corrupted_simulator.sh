#!/bin/bash
# Fix for corrupted iOS Simulator runtime causing "????" error

set -e

echo "🔧 Fixing Corrupted iOS Simulator Runtime"
echo ""

# Step 1: Kill all simulator processes
echo "1️⃣ Killing Simulator processes..."
killall Simulator 2>/dev/null || true
sleep 2

# Step 2: Shutdown all simulators
echo "2️⃣ Shutting down all simulators..."
xcrun simctl shutdown all 2>/dev/null || true

# Step 3: Clear Expo cache
echo "3️⃣ Clearing Expo cache..."
cd "$(dirname "$0")"
rm -rf .expo node_modules/.cache 2>/dev/null || true
echo "✅ Cache cleared"

# Step 4: List runtimes to identify corrupted ones
echo ""
echo "4️⃣ Checking for corrupted runtimes..."
echo ""
xcrun simctl runtime list

echo ""
echo "⚠️  If you see iOS 26.0 or any runtime with '????', you need to:"
echo "   1. Open Xcode → Settings → Platforms"
echo "   2. Delete the corrupted runtime (iOS 26.0)"
echo "   3. Re-download iOS 18.2 or iOS 17.5"
echo ""

# Step 5: Try to delete iOS 26.0 runtime if it exists
echo "5️⃣ Attempting to delete iOS 26.0 runtime (if it exists)..."
xcrun simctl runtime delete "iOS 26.0" 2>&1 || {
  echo "   ⚠️  Could not delete via command line (may need to delete in Xcode)"
  echo "   → Go to Xcode → Settings → Platforms → Delete iOS 26.0"
}

# Step 6: Reset simulator service
echo ""
echo "6️⃣ Resetting CoreSimulator service..."
sudo killall -9 com.apple.CoreSimulator.CoreSimulatorService 2>/dev/null || true
sleep 2

# Step 7: Boot a clean simulator
echo ""
echo "7️⃣ Booting a clean simulator (iOS 17.5 iPhone 15 Pro)..."
xcrun simctl boot "iPhone 15 Pro" 2>/dev/null || {
  echo "   ⚠️  Could not boot iPhone 15 Pro, trying iPhone 15..."
  xcrun simctl boot "iPhone 15" 2>/dev/null || true
}

# Step 8: Open Simulator app
echo "8️⃣ Opening Simulator app..."
open -a Simulator
sleep 3

echo ""
echo "✅ Reset complete!"
echo ""
echo "📝 Next steps:"
echo "   1. If iOS 26.0 still appears, delete it in Xcode → Settings → Platforms"
echo "   2. Re-download iOS 18.2 or iOS 17.5 runtime"
echo "   3. Try: cd mobile && npx expo start --ios"
echo ""

