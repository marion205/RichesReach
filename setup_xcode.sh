#!/bin/bash
echo "🔧 Setting up Xcode path..."
echo ""
echo "Please enter your password when prompted:"
sudo xcode-select --switch /Volumes/ExternalSSD/Xcode.app/Contents/Developer

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Xcode path set successfully!"
    echo ""
    echo "Current path:"
    xcode-select -p
    echo ""
    echo "📱 Available simulators:"
    xcrun simctl list devices available | head -20
    echo ""
    echo "🚀 Ready to start iOS simulator!"
    echo "Run: cd mobile && npm start"
else
    echo "❌ Failed to set Xcode path"
fi
