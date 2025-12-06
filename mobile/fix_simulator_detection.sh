#!/bin/bash
# Fix for "Simulator is installed but is identified as '????'" error

echo "🔧 Fixing iOS Simulator Detection Issue"
echo ""

# Set proper locale to avoid encoding issues
export LC_ALL=en_US.UTF-8
export LANG=en_US.UTF-8

# Boot a specific simulator if none is booted
BOOTED=$(xcrun simctl list devices | grep "(Booted)" | head -1)
if [ -z "$BOOTED" ]; then
  echo "📱 Booting iPhone 15 Pro..."
  xcrun simctl boot "iPhone 15 Pro" 2>/dev/null || {
    echo "⚠️  Could not boot iPhone 15 Pro, trying iPhone 15..."
    xcrun simctl boot "iPhone 15" 2>/dev/null || {
      echo "⚠️  Could not boot iPhone 15, trying first available iPhone..."
      FIRST_IPHONE=$(xcrun simctl list devices available | grep "iPhone" | head -1 | sed 's/.*iPhone \([^(]*\).*/\1/' | xargs)
      if [ -n "$FIRST_IPHONE" ]; then
        xcrun simctl boot "iPhone $FIRST_IPHONE" 2>/dev/null || true
      fi
    }
  }
  open -a Simulator
  sleep 3
fi

# Verify simulator is booted
BOOTED=$(xcrun simctl list devices | grep "(Booted)" | head -1)
if [ -n "$BOOTED" ]; then
  echo "✅ Simulator is booted: $BOOTED"
else
  echo "❌ Could not boot simulator. Please boot manually:"
  echo "   open -a Simulator"
  exit 1
fi

# Now start Expo with explicit device selection
echo ""
echo "🚀 Starting Expo..."
echo "   (If you still see the '????' error, try: npx expo run:ios)"
echo ""

cd "$(dirname "$0")"
npx expo start --ios

