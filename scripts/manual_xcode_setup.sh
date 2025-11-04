#!/usr/bin/env bash
# Manual steps for Xcode setup - run these commands one by one

set -e

echo "=== Manual Xcode Setup Steps ==="
echo ""
echo "Step 1: Move Xcode (enter your password when prompted)"
echo "  sudo mv ~/Downloads/Xcode.app /Applications/Xcode.app"
echo ""
echo "Step 2: Fix permissions"
echo "  sudo xattr -dr com.apple.quarantine /Applications/Xcode.app"
echo ""
echo "Step 3: Configure command-line tools"
echo "  sudo xcode-select -s /Applications/Xcode.app/Contents/Developer"
echo ""
echo "Step 4: Accept license"
echo "  sudo xcodebuild -license accept"
echo ""
echo "Step 5: First launch"
echo "  sudo xcodebuild -runFirstLaunch"
echo ""
echo "Step 6: Fix Ruby gems"
echo "  gem pristine ffi --version 1.15.5 || gem install ffi --force"
echo ""
echo "Step 7: Verify"
echo "  xcode-select -p"
echo "  xcodebuild -version"
echo ""

# Check if user wants to proceed
read -p "Do you want to run all steps now? (y/n): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo ""
    echo "Step 1: Moving Xcode..."
    sudo mv ~/Downloads/Xcode.app /Applications/Xcode.app
    
    echo ""
    echo "Step 2: Fixing permissions..."
    sudo xattr -dr com.apple.quarantine /Applications/Xcode.app
    
    echo ""
    echo "Step 3: Configuring command-line tools..."
    sudo xcode-select -s /Applications/Xcode.app/Contents/Developer
    
    echo ""
    echo "Step 4: Accepting license..."
    sudo xcodebuild -license accept 2>/dev/null || echo "License may need manual acceptance"
    
    echo ""
    echo "Step 5: Running first launch..."
    sudo xcodebuild -runFirstLaunch 2>/dev/null || true
    
    echo ""
    echo "Step 6: Fixing Ruby gems..."
    gem pristine ffi --version 1.15.5 2>/dev/null || gem install ffi --force 2>/dev/null || true
    gem pristine bigdecimal --version 3.3.1 2>/dev/null || gem install bigdecimal --force 2>/dev/null || true
    
    echo ""
    echo "Step 7: Verifying..."
    echo "Developer directory: $(xcode-select -p)"
    echo "Xcode version: $(xcodebuild -version 2>/dev/null | head -1 || echo 'Could not determine')"
    
    echo ""
    echo "✅ Setup complete!"
else
    echo "Run the commands manually as shown above."
fi

