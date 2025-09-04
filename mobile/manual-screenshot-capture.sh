#!/bin/bash

# Manual Screenshot Capture for RichesReach App Store
echo "📱 Manual Screenshot Capture for RichesReach"
echo "============================================="

# Create organized directories
mkdir -p screenshots/iphone-6.7
mkdir -p screenshots/iphone-6.5  
mkdir -p screenshots/iphone-5.5
mkdir -p screenshots/ipad-12.9
mkdir -p screenshots/ipad-11

echo "📋 Screenshot Capture Instructions:"
echo "=================================="
echo ""
echo "🎯 Required Screenshots (5 total):"
echo "1. AI Portfolio Advisor (Hero Screen)"
echo "2. Real-Time Market Data (Stocks Screen)"
echo "3. Portfolio Tracking (Portfolio Screen)"
echo "4. Social Trading Community (Community Screen)"
echo "5. Risk Assessment & Education (Education Screen)"
echo ""
echo "📱 Required Device Sizes:"
echo "- iPhone 6.7\" (iPhone 14 Pro Max) - 1290 x 2796"
echo "- iPhone 6.5\" (iPhone 11 Pro Max) - 1242 x 2688"
echo "- iPhone 5.5\" (iPhone 8 Plus) - 1242 x 2208"
echo "- iPad 12.9\" (iPad Pro 12.9\") - 2048 x 2732"
echo "- iPad 11\" (iPad Pro 11\") - 1668 x 2388"
echo ""

# Function to capture screenshot for current device
capture_current_screen() {
    local screen_name=$1
    local screen_description=$2
    
    echo "📸 Capturing: $screen_description"
    echo "Current device: $(xcrun simctl list devices | grep Booted | head -1)"
    
    # Capture screenshot
    local timestamp=$(date +"%Y%m%d_%H%M%S")
    local filename="screenshots/${screen_name}_${timestamp}.png"
    
    xcrun simctl io booted screenshot "$filename"
    
    if [ $? -eq 0 ]; then
        echo "✅ Screenshot saved: $filename"
        echo "📏 File size: $(ls -lh "$filename" | awk '{print $5}')"
    else
        echo "❌ Failed to capture screenshot"
    fi
    
    echo ""
}

# Interactive capture process
echo "🚀 Starting Manual Screenshot Capture"
echo "====================================="
echo ""
echo "⚠️  IMPORTANT: Make sure your app is running and you're on the correct screen!"
echo ""

# Capture each required screen
echo "📱 Screen 1/5: AI Portfolio Advisor (Hero Screen)"
echo "Navigate to your AI Portfolio Advisor screen, then press Enter..."
read -p "Press Enter when ready to capture..."
capture_current_screen "01-hero-ai-portfolio" "AI Portfolio Advisor"

echo "📱 Screen 2/5: Real-Time Market Data"
echo "Navigate to your Stocks/Market Data screen, then press Enter..."
read -p "Press Enter when ready to capture..."
capture_current_screen "02-market-data" "Real-Time Market Data"

echo "📱 Screen 3/5: Portfolio Tracking"
echo "Navigate to your Portfolio/My Investments screen, then press Enter..."
read -p "Press Enter when ready to capture..."
capture_current_screen "03-portfolio-tracking" "Portfolio Tracking"

echo "📱 Screen 4/5: Social Trading Community"
echo "Navigate to your Community/Social screen, then press Enter..."
read -p "Press Enter when ready to capture..."
capture_current_screen "04-social-community" "Social Trading Community"

echo "📱 Screen 5/5: Risk Assessment & Education"
echo "Navigate to your Education/Learning screen, then press Enter..."
read -p "Press Enter when ready to capture..."
capture_current_screen "05-risk-education" "Risk Assessment & Education"

echo "🎉 Screenshot capture completed!"
echo "==============================="
echo ""
echo "📁 Check the screenshots/ directory for your captured images."
echo "🎨 Next steps:"
echo "1. Review each screenshot for quality"
echo "2. Remove status bar if needed"
echo "3. Ensure file sizes are under 5MB"
echo "4. Organize by device size for App Store submission"
echo ""
echo "📋 Screenshot Summary:"
ls -la screenshots/*.png 2>/dev/null | while read line; do
    echo "  $line"
done
