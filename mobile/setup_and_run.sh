#!/bin/bash
# Complete setup and run script - Run this in a NEW terminal

set -e

echo "🚀 Setting up CocoaPods and running Expo iOS"
echo ""

# Step 1: Verify RVM is gone
echo "1️⃣ Checking RVM status..."
if env | grep -q rvm; then
  echo "⚠️  WARNING: RVM environment variables still detected!"
  echo "   Please close this terminal and open a NEW one"
  exit 1
else
  echo "✅ RVM is gone (good!)"
fi

# Step 2: Check Ruby
echo ""
echo "2️⃣ Checking Ruby..."
RUBY_PATH=$(which ruby)
RUBY_VERSION=$(ruby --version)
echo "   Ruby: $RUBY_PATH"
echo "   Version: $RUBY_VERSION"

if [[ "$RUBY_PATH" == *"rvm"* ]]; then
  echo "❌ ERROR: Still using RVM Ruby!"
  echo "   Please close this terminal and open a NEW one"
  exit 1
fi

# Step 3: Install CocoaPods (if not already installed)
echo ""
echo "3️⃣ Checking CocoaPods..."
if command -v pod &> /dev/null; then
  POD_VERSION=$(pod --version 2>&1 | head -1)
  if [[ "$POD_VERSION" == *"1."* ]]; then
    echo "✅ CocoaPods found: $POD_VERSION"
  else
    echo "⚠️  CocoaPods found but version check failed"
    echo "   Installing via system Ruby..."
    sudo gem install cocoapods -n /usr/local/bin
  fi
else
  echo "📦 Installing CocoaPods via system Ruby..."
  sudo gem install cocoapods -n /usr/local/bin
fi

# Step 4: Verify CocoaPods
echo ""
echo "4️⃣ Verifying CocoaPods installation..."
POD_PATH=$(which pod)
POD_VERSION=$(pod --version 2>&1 | head -1)
echo "   Pod: $POD_PATH"
echo "   Version: $POD_VERSION"

if [[ "$POD_VERSION" == *"error"* ]] || [[ "$POD_VERSION" == *"Could not find"* ]]; then
  echo "❌ CocoaPods installation failed!"
  echo "   Try running manually: sudo gem install cocoapods -n /usr/local/bin"
  exit 1
fi

# Step 5: Navigate to project
echo ""
echo "5️⃣ Navigating to project..."
cd "$(dirname "$0")"
echo "   Current directory: $(pwd)"

# Step 6: Boot simulator if needed
echo ""
echo "6️⃣ Checking simulator..."
BOOTED=$(xcrun simctl list devices | grep "(Booted)" | head -1)
if [ -z "$BOOTED" ]; then
  echo "📱 Booting iPhone 15 Pro..."
  xcrun simctl boot "iPhone 15 Pro" 2>/dev/null || xcrun simctl boot "iPhone 16 Pro" 2>/dev/null || true
  sleep 2
fi
echo "✅ Simulator ready"

# Step 7: Run Expo
echo ""
echo "7️⃣ Running Expo iOS build..."
echo "   This will take a few minutes on first build..."
echo ""
npx expo run:ios






