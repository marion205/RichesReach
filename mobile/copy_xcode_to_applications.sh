#!/bin/bash
# Script to copy Xcode from external drive to Applications and set up Command Line Tools

set -e

echo "🚀 Copying Xcode to Applications..."
echo ""
echo "⚠️  WARNING: This will:"
echo "   1. Copy 28GB from external drive to Applications"
echo "   2. Take 10-30 minutes depending on drive speed"
echo "   3. Require sudo password"
echo ""
read -p "Continue? (y/N) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Cancelled."
    exit 1
fi

# Step 1: Copy Xcode
echo ""
echo "📦 Step 1: Copying Xcode to Applications..."
echo "   This will take 10-30 minutes..."
sudo cp -R /Volumes/ExternalSSD/Xcode.app /Applications/Xcode.app

# Step 2: Set Command Line Tools
echo ""
echo "🔧 Step 2: Setting Command Line Tools..."
sudo xcode-select -switch /Applications/Xcode.app/Contents/Developer

# Step 3: Run first launch
echo ""
echo "🚀 Step 3: Running Xcode first launch setup..."
sudo xcodebuild -runFirstLaunch

# Step 4: Accept license
echo ""
echo "📜 Step 4: Accepting Xcode license..."
sudo xcodebuild -license accept

# Step 5: Verify
echo ""
echo "✅ Step 5: Verifying installation..."
xcode-select -p
xcodebuild -version

echo ""
echo "✅ Done! Xcode is now in Applications."
echo ""
echo "📝 Next steps:"
echo "   1. Test Simulator: open -a Simulator"
echo "   2. Try Expo: cd mobile && npx expo start --ios"

