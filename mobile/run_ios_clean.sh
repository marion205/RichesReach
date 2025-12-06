#!/bin/bash
# Run iOS build with clean RVM-free environment

set -e

cd "$(dirname "$0")"

echo "🧹 Cleaning RVM environment..."
# Remove all RVM variables
unset GEM_PATH GEM_HOME RUBY_VERSION RUBY_ROOT MY_RUBY_HOME IRBRC
unset $(env | grep -o '^rvm_[^=]*' | xargs) 2>/dev/null || true

# Clean PATH - remove RVM, prioritize Homebrew
export PATH=$(echo $PATH | tr ':' '\n' | grep -v rvm | tr '\n' ':' | sed 's/:$//')
export PATH="/opt/homebrew/bin:$PATH"

echo "✅ Environment cleaned"
echo "Ruby: $(which ruby) - $(ruby --version 2>&1 | head -1)"
echo "Pod: $(which pod) - $(pod --version 2>&1 | head -1)"
echo ""

# Boot simulator if not booted
BOOTED=$(xcrun simctl list devices | grep "(Booted)" | head -1)
if [ -z "$BOOTED" ]; then
  echo "📱 Booting iPhone 15 Pro..."
  xcrun simctl boot "iPhone 15 Pro" 2>/dev/null || true
fi

echo "🚀 Running Expo..."
echo ""

# Set environment to prevent Expo from trying to install CocoaPods via gem
export EXPO_NO_COCOAPODS_AUTO_INSTALL=1

# Run Expo
npx expo run:ios

