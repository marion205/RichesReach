#!/bin/bash

# RichesReach App Store Screenshots Capture Script
echo "📱 RichesReach App Store Screenshots Capture"
echo "=============================================="

# Create screenshots directory structure
echo "📁 Creating screenshot directories..."
mkdir -p screenshots/iphone-6.7
mkdir -p screenshots/iphone-6.5
mkdir -p screenshots/iphone-5.5
mkdir -p screenshots/ipad-12.9
mkdir -p screenshots/ipad-11

# Check if iOS Simulator is available
if ! command -v xcrun &> /dev/null; then
    echo "❌ Xcode not found. Please install Xcode from the App Store."
    exit 1
fi

echo "🔍 Available iOS Simulators:"
xcrun simctl list devices available | grep "iPhone\|iPad"

echo ""
echo "📋 Screenshot Capture Instructions:"
echo "=================================="
echo ""
echo "1. 🚀 Start your app in iOS Simulator:"
echo "   npm run ios"
echo ""
echo "2. 📱 Navigate to each screen you want to capture:"
echo "   - AI Portfolio Advisor (Hero screen)"
echo "   - Real-Time Market Data"
echo "   - Portfolio Tracking"
echo "   - Social Trading Community"
echo "   - Risk Assessment & Education"
echo ""
echo "3. 📸 Capture screenshots using:"
echo "   - Cmd+S in iOS Simulator"
echo "   - Or use: xcrun simctl io booted screenshot"
echo ""
echo "4. 📏 Required sizes:"
echo "   - iPhone 6.7\": 1290 x 2796 pixels"
echo "   - iPhone 6.5\": 1242 x 2688 pixels"
echo "   - iPhone 5.5\": 1242 x 2208 pixels"
echo "   - iPad 12.9\": 2048 x 2732 pixels"
echo "   - iPad 11\": 1668 x 2388 pixels"
echo ""
echo "5. 🎨 Post-processing:"
echo "   - Remove status bar"
echo "   - Ensure file size < 5MB"
echo "   - Use PNG or JPEG format"
echo ""

# Function to capture screenshot for specific device
capture_for_device() {
    local device_name=$1
    local screenshot_name=$2
    
    echo "📸 Capturing $screenshot_name for $device_name..."
    
    # Boot the simulator if not already running
    xcrun simctl boot "$device_name" 2>/dev/null || true
    
    # Wait a moment for simulator to be ready
    sleep 3
    
    # Capture screenshot
    xcrun simctl io booted screenshot "screenshots/$device_name/$screenshot_name.png"
    
    if [ $? -eq 0 ]; then
        echo "✅ Screenshot captured: screenshots/$device_name/$screenshot_name.png"
    else
        echo "❌ Failed to capture screenshot for $device_name"
    fi
}

# Interactive screenshot capture
echo "🎯 Interactive Screenshot Capture"
echo "================================"
echo ""
echo "Choose an option:"
echo "1) Capture all required screenshots automatically"
echo "2) Capture specific device size"
echo "3) Manual capture instructions only"
echo "4) Open iOS Simulator"
echo ""
read -p "Enter your choice (1-4): " choice

case $choice in
    1)
        echo "🚀 Starting automatic screenshot capture..."
        echo "⚠️  Make sure your app is running in the simulator first!"
        echo ""
        read -p "Press Enter when your app is ready in the simulator..."
        
        # List of devices to capture
        devices=("iPhone 14 Pro Max" "iPhone 11 Pro Max" "iPhone 8 Plus" "iPad Pro (12.9-inch)" "iPad Pro (11-inch)")
        
        for device in "${devices[@]}"; do
            echo "📱 Setting up $device..."
            capture_for_device "$device" "01-hero-ai-portfolio"
            capture_for_device "$device" "02-market-data"
            capture_for_device "$device" "03-portfolio-tracking"
            capture_for_device "$device" "04-social-community"
            capture_for_device "$device" "05-risk-education"
        done
        ;;
    2)
        echo "📱 Available devices:"
        echo "1) iPhone 14 Pro Max (6.7\")"
        echo "2) iPhone 11 Pro Max (6.5\")"
        echo "3) iPhone 8 Plus (5.5\")"
        echo "4) iPad Pro 12.9-inch"
        echo "5) iPad Pro 11-inch"
        read -p "Select device (1-5): " device_choice
        
        case $device_choice in
            1) device="iPhone 14 Pro Max" ;;
            2) device="iPhone 11 Pro Max" ;;
            3) device="iPhone 8 Plus" ;;
            4) device="iPad Pro (12.9-inch)" ;;
            5) device="iPad Pro (11-inch)" ;;
            *) echo "❌ Invalid choice"; exit 1 ;;
        esac
        
        echo "📸 Capturing screenshots for $device..."
        echo "⚠️  Make sure your app is running in the simulator first!"
        read -p "Press Enter when ready..."
        
        capture_for_device "$device" "01-hero-ai-portfolio"
        capture_for_device "$device" "02-market-data"
        capture_for_device "$device" "03-portfolio-tracking"
        capture_for_device "$device" "04-social-community"
        capture_for_device "$device" "05-risk-education"
        ;;
    3)
        echo "📋 Manual Capture Instructions:"
        echo "=============================="
        echo ""
        echo "1. Open iOS Simulator:"
        echo "   xcrun simctl list devices available"
        echo "   xcrun simctl boot 'iPhone 14 Pro Max'"
        echo ""
        echo "2. Run your app:"
        echo "   npm run ios"
        echo ""
        echo "3. Navigate to each screen and capture:"
        echo "   Cmd+S in simulator"
        echo ""
        echo "4. Save to screenshots/ directory with proper naming"
        ;;
    4)
        echo "🚀 Opening iOS Simulator..."
        open -a Simulator
        echo "✅ iOS Simulator opened. You can now run your app with: npm run ios"
        ;;
    *)
        echo "❌ Invalid choice"
        exit 1
        ;;
esac

echo ""
echo "✅ Screenshot capture process completed!"
echo "📁 Check the screenshots/ directory for your captured images."
echo "🎨 Remember to post-process them according to the guide."
